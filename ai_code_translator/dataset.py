"""
Dataset module for code translation.
"""

import json
from pathlib import Path
from typing import List, Dict, Union, Optional
import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer

class CodeTranslationDataset(Dataset):
    """Dataset for code translation pairs."""
    
    def __init__(
        self,
        source_codes: List[str],
        target_codes: List[str],
        tokenizer: AutoTokenizer,
        max_length: int = 512,
        source_langs: Optional[List[str]] = None,
        target_langs: Optional[List[str]] = None
    ):
        """Initialize dataset.
        
        Args:
            source_codes: List of source code strings
            target_codes: List of target code strings
            tokenizer: Tokenizer instance
            max_length: Maximum sequence length
            source_langs: Optional list of source languages
            target_langs: Optional list of target languages
        """
        if len(source_codes) != len(target_codes):
            raise ValueError("Source and target lists must have same length")
            
        if source_langs and len(source_langs) != len(source_codes):
            raise ValueError("Source languages list must match code list length")
            
        if target_langs and len(target_langs) != len(target_codes):
            raise ValueError("Target languages list must match code list length")
        
        self.source_codes = source_codes
        self.target_codes = target_codes
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.source_langs = source_langs
        self.target_langs = target_langs
    
    def __len__(self) -> int:
        return len(self.source_codes)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Get a single item from the dataset."""
        source_code = self.source_codes[idx]
        target_code = self.target_codes[idx]
        
        # Add language context if available
        if self.source_langs and self.target_langs:
            source_code = f"Translate {self.source_langs[idx]} to {self.target_langs[idx]}: {source_code}"
        
        # Tokenize source
        source_encoding = self.tokenizer(
            source_code,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        # Tokenize target
        target_encoding = self.tokenizer(
            target_code,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": source_encoding["input_ids"].squeeze(),
            "attention_mask": source_encoding["attention_mask"].squeeze(),
            "labels": target_encoding["input_ids"].squeeze()
        }
    
    @classmethod
    def from_paths(
        cls,
        data_paths: List[Union[str, Path]],
        max_length: int = 512,
        tokenizer: Optional[AutoTokenizer] = None
    ) -> "CodeTranslationDataset":
        """Create dataset from JSON files.
        
        Args:
            data_paths: List of paths to JSON files containing code pairs
            max_length: Maximum sequence length
            tokenizer: Optional tokenizer, will create new one if not provided
        
        Returns:
            CodeTranslationDataset instance
        """
        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
        
        source_codes = []
        target_codes = []
        source_langs = []
        target_langs = []
        
        for path in data_paths:
            path = Path(path)
            if not path.exists():
                print(f"Warning: {path} does not exist, skipping")
                continue
                
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            # Handle different dataset formats
                            
                            # Code Alpaca format
                            if "instruction" in item and "output" in item:
                                source = item["instruction"]
                                if item.get("input"):
                                    source += "\n" + item["input"]
                                source_codes.append(source)
                                target_codes.append(item["output"])
                                source_langs.append("natural")
                                target_langs.append("code")
                                
                            # Apps dataset format
                            elif "question" in item and "solutions" in item:
                                solutions = json.loads(item["solutions"])
                                if solutions:  # Take first solution if multiple
                                    source_codes.append(item["question"])
                                    target_codes.append(solutions[0])
                                    source_langs.append("natural")
                                    target_langs.append("python")
                                    
                            # CodeSearchNet format
                            elif "docstring" in item and "code" in item:
                                if item["docstring"] and item["code"]:
                                    source_codes.append(item["docstring"])
                                    target_codes.append(item["code"])
                                    source_langs.append("natural")
                                    target_langs.append(path.parent.name)  # python/java/javascript
                                    
                            # Standard format
                            elif "source" in item and "target" in item:
                                source_codes.append(item["source"])
                                target_codes.append(item["target"])
                                if "source_lang" in item and "target_lang" in item:
                                    source_langs.append(item["source_lang"])
                                    target_langs.append(item["target_lang"])
                            
            except Exception as e:
                print(f"Error loading {path}: {str(e)}")
                continue
        
        if not source_codes:
            raise ValueError("No valid code pairs found in provided paths")
            
        # Only use language info if we have it for all examples
        if len(source_langs) != len(source_codes):
            source_langs = None
            target_langs = None
        
        return cls(
            source_codes=source_codes,
            target_codes=target_codes,
            tokenizer=tokenizer,
            max_length=max_length,
            source_langs=source_langs,
            target_langs=target_langs
        )
