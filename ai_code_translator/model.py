"""
Code translation model implementation with advanced optimizations.
"""

import torch
from torch import nn
from transformers import T5ForConditionalGeneration, AutoTokenizer
from typing import List, Dict, Optional
import torch.nn.functional as F

# Disable Triton compiler and use eager mode
torch._dynamo.config.suppress_errors = True

class CodeTranslator(nn.Module):
    def __init__(
        self, 
        model_name: str = "Salesforce/codet5-base",
        gradient_checkpointing: bool = False
    ):
        super().__init__()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Initialize model with optimizations
        self.model = T5ForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
        )
        
        # Enable gradient checkpointing if requested
        if gradient_checkpointing and self.device.type == "cuda":
            self.model.gradient_checkpointing_enable()
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Move model to device
        self.model.to(self.device)
    
    def forward(self, 
                input_ids: torch.Tensor, 
                attention_mask: torch.Tensor,
                labels: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass with automatic casting to fp16."""
        
        # Move inputs to device and cast to fp16 if on GPU
        input_ids = input_ids.to(self.device)
        attention_mask = attention_mask.to(self.device)
        if labels is not None:
            labels = labels.to(self.device)
        
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        
        return outputs
    
    @torch.inference_mode()  # Faster than no_grad for inference
    def translate(self, 
                 source_code: str, 
                 source_lang: str, 
                 target_lang: str,
                 max_length: int = 512,
                 num_beams: int = 4,
                 top_p: float = 0.95,
                 temperature: float = 0.7) -> str:
        """Translate code with optimized generation settings."""
        
        # Prepare input text
        input_text = f"Translate this {source_lang} code to {target_lang}: {source_code}"
        
        # Tokenize input
        inputs = self.tokenizer(
            input_text,
            max_length=max_length,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate translation with nucleus sampling
        outputs = self.model.generate(
            **inputs,
            max_length=max_length,
            num_beams=num_beams,
            top_p=top_p,
            temperature=temperature,
            length_penalty=0.6,
            repetition_penalty=1.2,
            early_stopping=True,
            use_cache=True  # Enable cache for inference
        )
        
        # Decode output
        translated_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return translated_code
    
    def save(self, path: str) -> None:
        """Save model and tokenizer to path."""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
    
    def load(self, path: str) -> None:
        """Load model and tokenizer from path."""
        self.model = T5ForConditionalGeneration.from_pretrained(
            path,
            torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
        ).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
