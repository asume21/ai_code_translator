"""Training script for the Code Transformer model."""

import torch
from torch.utils.data import DataLoader
import torch.optim as optim
from torch.nn import CrossEntropyLoss
from typing import List, Tuple, Optional
import logging
from pathlib import Path
from tqdm import tqdm
import yaml
import json
from .model import CodeTransformer, CodeDataset

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(
        self,
        model: CodeTransformer,
        train_dataset: CodeDataset,
        val_dataset: Optional[CodeDataset] = None,
        batch_size: int = 32,
        learning_rate: float = 1e-4,
        num_epochs: int = 10,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        self.model = model.to(device)
        self.device = device
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        
        # Setup data loaders
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4
        )
        self.val_loader = None
        if val_dataset:
            self.val_loader = DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=4
            )
        
        # Setup optimizer and loss
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = CrossEntropyLoss(ignore_index=model.tokenizer.pad_token_id)
        
        # Setup learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.1,
            patience=2,
            verbose=True
        )

    def train_epoch(self) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        
        for batch in tqdm(self.train_loader, desc="Training"):
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            self.optimizer.zero_grad()
            
            outputs = self.model(
                input_ids,
                src_padding_mask=attention_mask
            )
            
            loss = self.criterion(
                outputs.view(-1, outputs.size(-1)),
                labels.view(-1)
            )
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(self.train_loader)

    def validate(self) -> float:
        """Validate the model."""
        if not self.val_loader:
            return 0.0
            
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Validating"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids,
                    src_padding_mask=attention_mask
                )
                
                loss = self.criterion(
                    outputs.view(-1, outputs.size(-1)),
                    labels.view(-1)
                )
                
                total_loss += loss.item()
        
        return total_loss / len(self.val_loader)

    def train(self, checkpoint_dir: str = 'checkpoints') -> None:
        """Train the model for specified number of epochs."""
        checkpoint_path = Path(checkpoint_dir)
        checkpoint_path.mkdir(exist_ok=True)
        
        best_val_loss = float('inf')
        
        for epoch in range(self.num_epochs):
            logger.info(f"Epoch {epoch+1}/{self.num_epochs}")
            
            train_loss = self.train_epoch()
            logger.info(f"Training Loss: {train_loss:.4f}")
            
            if self.val_loader:
                val_loss = self.validate()
                logger.info(f"Validation Loss: {val_loss:.4f}")
                
                # Update learning rate scheduler
                self.scheduler.step(val_loss)
                
                # Save checkpoint if validation loss improved
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    self.model.save_model(
                        checkpoint_path / f"model_epoch_{epoch+1}_valloss_{val_loss:.4f}.pt"
                    )
            
            # Regular checkpoint
            self.model.save_model(
                checkpoint_path / f"model_epoch_{epoch+1}.pt"
            )

def load_training_data(data_path: str) -> Tuple[List[str], List[str]]:
    """Load training data from JSON file."""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['source_codes'], data['target_codes']

def train_model(config_path: str = 'config.yml') -> None:
    """Train model using configuration from YAML file."""
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize model
    model = CodeTransformer(**config['model'])
    
    # Load training data
    train_source, train_target = load_training_data(config['data']['train_path'])
    val_source, val_target = load_training_data(config['data']['val_path'])
    
    # Create datasets
    train_dataset = CodeDataset(train_source, train_target, model.tokenizer)
    val_dataset = CodeDataset(val_source, val_target, model.tokenizer)
    
    # Initialize trainer
    trainer = ModelTrainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        **config['training']
    )
    
    # Train model
    trainer.train(config['checkpoints']['dir'])

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    train_model()
