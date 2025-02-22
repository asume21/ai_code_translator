"""Feedback Learner for continuous model improvement based on user corrections."""

import torch
from torch.utils.data import Dataset, DataLoader
import json
from typing import Dict, List, Tuple, Optional, Union
import logging
from pathlib import Path
from datetime import datetime
from .model import CodeTransformer
import torch.nn.functional as F

logger = logging.getLogger(__name__)

class FeedbackDataset(Dataset):
    """Dataset for storing and managing user feedback for translations."""
    
    def __init__(self, feedback_file: str = "data/feedback.json"):
        self.feedback_file = Path(feedback_file)
        self.feedback_data = self._load_feedback()
        
    def _load_feedback(self) -> List[Dict]:
        """Load feedback data from JSON file."""
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_feedback(self):
        """Save feedback data to JSON file."""
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_data, f, indent=2)
    
    def add_feedback(
        self,
        source_code: str,
        original_translation: str,
        corrected_translation: str,
        source_lang: str,
        target_lang: str,
        metadata: Optional[Dict] = None
    ):
        """Add new feedback entry."""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "source_code": source_code,
            "original_translation": original_translation,
            "corrected_translation": corrected_translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "metadata": metadata or {}
        }
        self.feedback_data.append(feedback_entry)
        self.save_feedback()
    
    def __len__(self) -> int:
        return len(self.feedback_data)
    
    def __getitem__(self, idx: int) -> Dict:
        return self.feedback_data[idx]

class IncrementalLearner:
    """Manages incremental learning from user feedback."""
    
    def __init__(
        self,
        model: torch.nn.Module,
        feedback_dataset: FeedbackDataset,
        batch_size: int = 32,
        learning_rate: float = 1e-4,
        device: str = "cpu"
    ):
        """Initialize the incremental learner."""
        self.model = model
        self.feedback_dataset = feedback_dataset
        self.device = device
        self.batch_size = batch_size
        self.optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
        self.criterion = torch.nn.CrossEntropyLoss()  # Use default ignore_index
        
    def _prepare_batch(self, batch: Union[Dict, List[Dict]]) -> Tuple[torch.Tensor, torch.Tensor]:
        """Prepare a batch of feedback data for training."""
        # Convert single item to list
        if isinstance(batch, dict):
            batch = [batch]
        
        source_codes = [item["source_code"] for item in batch]
        corrected_translations = [item["corrected_translation"] for item in batch]
        
        # Convert to tensors
        inputs = torch.tensor([self._encode_text(code) for code in source_codes], dtype=torch.long)
        targets = torch.tensor([self._encode_text(code) for code in corrected_translations], dtype=torch.long)
        
        # Ensure inputs and targets have the same shape
        max_len = max(inputs.size(1), targets.size(1))
        inputs = F.pad(inputs, (0, max_len - inputs.size(1)), value=0)
        targets = F.pad(targets, (0, max_len - targets.size(1)), value=0)
        
        # Reshape inputs to match model's expected shape
        inputs = inputs.view(inputs.size(0), -1)
        targets = targets.view(targets.size(0), -1)
        
        # Move tensors to device
        inputs = inputs.to(self.device)
        targets = targets.to(self.device)
        
        return inputs, targets
    
    def _encode_text(self, text: Union[str, List[str]]) -> List[int]:
        """Encode text into a list of integers."""
        # Convert list to string if needed
        if isinstance(text, list):
            text = '\n'.join(text)
        
        # Simple character-level encoding for now
        # In a real implementation, this would use a proper tokenizer
        encoded = [ord(c) % 1000 for c in text]  # Use modulo to ensure it fits in our vocabulary size
        
        # Pad or truncate to fixed length
        max_length = 1000  # Fixed length for all sequences
        if len(encoded) > max_length:
            return encoded[:max_length]
        else:
            return encoded + [0] * (max_length - len(encoded))
    
    def train_on_feedback(self) -> float:
        """Train the model on feedback data."""
        # Get a batch of feedback data
        batch = self.feedback_dataset
        
        # Prepare the batch
        inputs, targets = self._prepare_batch(batch)
        
        # Zero gradients
        self.optimizer.zero_grad()
        
        # Forward pass
        outputs = self.model(inputs)
        
        # Reshape outputs to match targets
        outputs = outputs.view(-1, outputs.size(-1))
        targets = targets.view(-1)
        
        # Calculate loss
        loss = self.criterion(outputs, targets)
        
        # Backward pass
        loss.backward()
        
        # Update weights
        self.optimizer.step()
        
        return loss.item()
    
    def save_model_checkpoint(self, path: str):
        """Save a checkpoint of the model after incremental learning."""
        checkpoint = {
            "model_state": self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "feedback_size": len(self.feedback_dataset)
        }
        torch.save(checkpoint, path)
        logger.info(f"Saved incremental learning checkpoint to {path}")
    
    def load_model_checkpoint(self, path: str):
        """Load a model checkpoint."""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint["model_state"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state"])
        logger.info(f"Loaded checkpoint from {path} (feedback size: {checkpoint['feedback_size']})")
