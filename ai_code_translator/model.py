"""
Code translation model implementation with advanced optimizations.
"""

import torch
import torch.nn as nn
from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoTokenizer, T5Config
from torch.utils.data import IterableDataset
import json
import gc
import numpy as np
from typing import Dict, Iterator, Optional, List
import logging

logger = logging.getLogger(__name__)

class CodeTranslator(nn.Module):
    """T5-based code translation model."""
    
    def __init__(self, model_name="Salesforce/codet5-base", max_length=512, device="cuda", config=None):
        """Initialize the model with regularization."""
        super().__init__()
        
        self.model_name = model_name
        self.max_length = max_length
        self.device = device
        self.config = config or {}
        
        # Initialize the tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Initialize the model with configuration
        model_config = T5Config.from_pretrained(model_name)
        if config:
            model_config.dropout_rate = config.get("dropout", 0.1)
            model_config.attention_dropout = config.get("attention_dropout", 0.1)
        
        self.model = T5ForConditionalGeneration.from_pretrained(
            model_name,
            config=model_config
        )
        
        # Initialize label smoothing
        self.label_smoothing = self.config.get("label_smoothing", 0.1)
        self.criterion = nn.CrossEntropyLoss(label_smoothing=self.label_smoothing)
        
        # Add special tokens
        special_tokens = [
            "<python>", "</python>",
            "<javascript>", "</javascript>",
            "<function>", "</function>",
            "<class>", "</class>",
            "<complexity=low>", "<complexity=medium>", "<complexity=high>",
            "<error>", "</error>",
            "<comment>", "</comment>",
            "<imports>", "</imports>"
        ]
        
        # Add special tokens and resize embeddings
        special_tokens_dict = {"additional_special_tokens": special_tokens}
        num_added_toks = self.tokenizer.add_special_tokens(special_tokens_dict)
        self.model.resize_token_embeddings(len(self.tokenizer))
        
        # Initialize new token embeddings
        if num_added_toks > 0:
            input_embeddings = self.model.get_input_embeddings()
            output_embeddings = self.model.get_output_embeddings()
            
            existing_mean = input_embeddings.weight.data[:-num_added_toks].mean()
            existing_std = input_embeddings.weight.data[:-num_added_toks].std()
            
            torch.nn.init.normal_(
                input_embeddings.weight.data[-num_added_toks:],
                mean=existing_mean,
                std=existing_std
            )
            torch.nn.init.normal_(
                output_embeddings.weight.data[-num_added_toks:],
                mean=existing_mean,
                std=existing_std
            )
        
        # Enable gradient checkpointing
        self.model.gradient_checkpointing_enable()
        
        # Move to device
        self.to(self.device)
        
        # Clear GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """Forward pass of the model."""
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
            return_dict=True
        )
        return outputs
    
    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        max_length: Optional[int] = None,
        num_beams: int = 4,
        temperature: float = 1.0,
        top_p: float = 0.9,
        repetition_penalty: float = 1.2,
        length_penalty: float = 1.0,
        **kwargs
    ) -> torch.Tensor:
        """Generate output sequence with improved decoding parameters."""
        return self.model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=max_length or self.max_length,
            num_beams=num_beams,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            length_penalty=length_penalty,
            early_stopping=True,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_hidden_states=True,
            **kwargs
        )
    
    def log_gradients(self) -> None:
        """Log gradient statistics for debugging."""
        for name, param in self.model.named_parameters():
            if param.grad is not None:
                grad_norm = param.grad.norm().item()
                grad_mean = param.grad.mean().item()
                grad_std = param.grad.std().item()
                logger.info(
                    f"Gradient stats - {name}: "
                    f"norm={grad_norm:.4f}, "
                    f"mean={grad_mean:.4f}, "
                    f"std={grad_std:.4f}"
                )
    
    def translate(self, 
                 source_code: str, 
                 source_lang: str, 
                 target_lang: str,
                 max_length: int = 512,
                 num_beams: int = 4,
                 top_p: float = 0.95,
                 temperature: float = 0.7) -> str:
        """Translate code with optimized generation settings."""
        try:
            # Prepare input
            input_text = f"Translate this {source_lang} code to {target_lang}: {source_code}"
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=max_length, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate with optimized settings
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    top_p=top_p,
                    temperature=temperature,
                    early_stopping=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # Decode and return
            translated_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return translated_code
            
        except Exception as e:
            print(f"Error during translation: {str(e)}")
            return ""
    
    def save(self, path: str) -> None:
        """Save model and tokenizer to path."""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

    def load(self, path: str) -> None:
        """Load model and tokenizer from path."""
        self.model = T5ForConditionalGeneration.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model.to(self.device)

class MemoryEfficientDataset(IterableDataset):
    """Memory efficient dataset that loads and processes data in chunks."""
    
    def __init__(self, source_codes, target_codes, tokenizer, max_length=512):
        """Initialize the dataset with source and target code lists."""
        super().__init__()
        self.source_codes = source_codes
        self.target_codes = target_codes
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.total_size = len(source_codes)
        
    def __iter__(self):
        """Iterate over the dataset, yielding tokenized examples."""
        for source, target in zip(self.source_codes, self.target_codes):
            source_tokens = self.tokenizer(
                source,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            
            target_tokens = self.tokenizer(
                target,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt"
            )
            
            yield {
                "input_ids": source_tokens["input_ids"][0],
                "attention_mask": source_tokens["attention_mask"][0],
                "labels": target_tokens["input_ids"][0]
            }
            
    def __len__(self):
        """Return the total size of the dataset."""
        return self.total_size
