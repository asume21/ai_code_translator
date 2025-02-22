"""Base translator class for code translation."""

import torch
import torch.nn as nn
from typing import Optional

class CodeTranslator(nn.Module):
    """Base class for code translation models."""
    
    def __init__(self):
        super().__init__()
    
    def translate(self, source_code: str, source_lang: str, target_lang: str) -> str:
        """Translate code from source language to target language."""
        raise NotImplementedError("Subclasses must implement translate()")
    
    def train_step(self, source_code: str, target_code: str) -> float:
        """Perform a single training step."""
        raise NotImplementedError("Subclasses must implement train_step()")
    
    def save(self, path: str):
        """Save the model to disk."""
        torch.save(self.state_dict(), path)
    
    def load(self, path: str):
        """Load the model from disk."""
        self.load_state_dict(torch.load(path))
