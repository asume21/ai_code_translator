"""Training script for the Code Translator model."""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import logging
from pathlib import Path
import yaml
import json
from tqdm import tqdm
import numpy as np
from typing import Dict, List, Optional, Tuple
from .model import CodeTranslator, MemoryEfficientDataset
from .preprocessing import CodePreprocessor
from .data_augmentation import CodeAugmenter
import wandb
from torch import amp  # Import torch.amp
import os  # Import os module
from torch.optim import AdamW
from transformers import get_linear_schedule_with_warmup
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Training configuration."""
    batch_size: int = 16
    num_epochs: int = 10
    learning_rate: float = 2e-5
    mixed_precision: bool = True
    save_steps: int = 500
    continue_on_error: bool = False
    patience: int = 3
    min_delta: float = 0.001
    max_grad_norm: float = 1.0
    gradient_log_steps: int = 100
    weight_decay: float = 0.01
    min_lr: float = 1e-7
    augmentation_prob: float = 0.3
    stochastic_weight_averaging: bool = False
    swa_lr: float = 1e-2
    swa_start_epoch: int = 5
    persistent_workers: bool = True
    num_workers: int = 4

    @classmethod
    def from_dict(cls, config: Dict) -> 'TrainingConfig':
        """Create config from dictionary."""
        training_config = config.get('training', {})
        return cls(**{
            k: v for k, v in training_config.items()
            if k in cls.__dataclass_fields__
        })

class ModelTrainer:
    """Trainer class for the Code Translator model."""
    
    def __init__(
        self,
        model: CodeTranslator,
        train_dataset: MemoryEfficientDataset,
        val_dataset: Optional[MemoryEfficientDataset] = None,
        config: Optional[Dict] = None,
        output_dir: Optional[str] = None,
        use_wandb: bool = False
    ):
        """Initialize the trainer with model and datasets."""
        self.model = model
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.config = TrainingConfig.from_dict(config or {})
        self.use_wandb = use_wandb
        
        # Set device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        # Initialize optimizer
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=float(self.config.learning_rate),
            weight_decay=self.config.weight_decay,
            eps=1e-8
        )

        # Initialize learning rate scheduler
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=0,
            num_training_steps=self.config.num_epochs
        )

        # Initialize data augmenter
        self.augmenter = CodeAugmenter(
            augmentation_prob=self.config.augmentation_prob
        )

        # Initialize mixed precision training
        self.scaler = amp.GradScaler(enabled=self.config.mixed_precision)
        
        # Initialize preprocessor
        self.preprocessor = CodePreprocessor()
        
        # Setup data loaders with correct configuration for IterableDataset
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            num_workers=self.config.num_workers,
            pin_memory=True,
            persistent_workers=self.config.persistent_workers and self.config.num_workers > 0
        )
        
        self.val_loader = DataLoader(
            val_dataset,
            batch_size=self.config.batch_size,
            num_workers=self.config.num_workers,
            pin_memory=True,
            persistent_workers=self.config.persistent_workers and self.config.num_workers > 0
        ) if val_dataset else None
        
        # Calculate steps per epoch based on dataset size and batch size
        self.steps_per_epoch = train_dataset.total_size // self.config.batch_size
        if self.steps_per_epoch == 0:
            self.steps_per_epoch = 1  # Ensure at least one step per epoch
        
        # Initialize SWA if enabled
        self.swa_enabled = self.config.stochastic_weight_averaging
        if self.swa_enabled:
            self.swa_model = torch.optim.swa_utils.AveragedModel(self.model)
            self.swa_scheduler = torch.optim.swa_utils.SWALR(
                self.optimizer,
                swa_lr=self.config.swa_lr
            )
            self.swa_start_epoch = self.config.swa_start_epoch
        
        # Setup output directory
        self.output_dir = Path(output_dir) if output_dir else Path('checkpoints')
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup wandb
        if use_wandb:
            wandb.init(project="code-translator", config=self.config.__dict__)
    
    def preprocess_batch(self, batch: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Preprocess a batch of data."""
        source_texts = self.model.tokenizer.batch_decode(batch['input_ids'], skip_special_tokens=True)
        target_texts = self.model.tokenizer.batch_decode(batch['labels'], skip_special_tokens=True)
        
        # Process source and target code
        processed_source = [
            self.preprocessor.process_python(text) if 'python' in text.lower() 
            else self.preprocessor.process_javascript(text)
            for text in source_texts
        ]
        
        processed_target = [
            self.preprocessor.process_javascript(text) if 'javascript' in text.lower()
            else self.preprocessor.process_python(text)
            for text in target_texts
        ]
        
        # Add special tokens based on code structure
        enhanced_source = []
        enhanced_target = []
        
        for src, tgt in zip(processed_source, processed_target):
            # Add structure markers
            src_enhanced = (
                f"<{src.language}> "
                f"<complexity={src.complexity}> "
                + " ".join(f"<{k}={','.join(v)}>" for k, v in src.special_tokens.items() if v)
                + f" {src.code}"
            )
            
            tgt_enhanced = (
                f"<{tgt.language}> "
                f"<complexity={tgt.complexity}> "
                + " ".join(f"<{k}={','.join(v)}>" for k, v in tgt.special_tokens.items() if v)
                + f" {tgt.code}"
            )
            
            enhanced_source.append(src_enhanced)
            enhanced_target.append(tgt_enhanced)
        
        # Tokenize enhanced code
        enhanced_inputs = self.model.tokenizer(
            enhanced_source,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        
        enhanced_labels = self.model.tokenizer(
            enhanced_target,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        
        return {
            'input_ids': enhanced_inputs['input_ids'].to(self.device),
            'attention_mask': enhanced_inputs['attention_mask'].to(self.device),
            'labels': enhanced_labels['input_ids'].to(self.device)
        }
    
    def train_epoch(self) -> float:
        """Train for one epoch with SWA."""
        self.model.train()
        total_loss = 0.0
        num_batches = 0
        
        # Initialize progress bar
        pbar = tqdm(total=self.steps_per_epoch, desc="Training")
        
        # Training loop
        for batch_idx, batch in enumerate(self.train_loader):
            if batch_idx >= self.steps_per_epoch:
                break
                
            # Move batch to device
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels = batch["labels"].to(self.device)
            
            # Forward pass with mixed precision
            with torch.cuda.amp.autocast(enabled=bool(self.scaler)):
                with amp.autocast(device_type='cuda', enabled=bool(self.scaler)):
                    outputs = self.model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    loss = outputs.loss / 1
            
            # Backward pass with mixed precision
            if self.scaler:
                self.scaler.scale(loss).backward()
                if (batch_idx + 1) % 1 == 0:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                    self.scheduler.step()
                    self.optimizer.zero_grad()
            else:
                loss.backward()
                if (batch_idx + 1) % 1 == 0:
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
                    self.optimizer.step()
                    self.scheduler.step()
                    self.optimizer.zero_grad()
            
            # Update SWA model if enabled
            if self.swa_enabled and self.current_epoch >= self.swa_start_epoch:
                self.swa_model.update_parameters(self.model)
                self.swa_scheduler.step()
            
            # Log gradients periodically
            if (batch_idx + 1) % self.config.gradient_log_steps == 0:
                self.model.log_gradients()
            
            # Update metrics
            total_loss += loss.item() * 1
            num_batches += 1
            
            # Update progress bar
            pbar.set_postfix({"loss": total_loss / num_batches})
            pbar.update(1)
            
            # Log to wandb
            if self.use_wandb:
                wandb.log({
                    "train/loss": loss.item(),
                    "train/learning_rate": self.scheduler.get_last_lr()[0]
                })
        
        pbar.close()
        return total_loss / num_batches if num_batches > 0 else float('inf')
    
    def validate(self) -> float:
        """Validate the model."""
        if not self.val_loader:
            return 0.0
            
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        # Calculate validation steps
        val_steps = self.val_loader.dataset.total_size // self.config.batch_size
        if val_steps == 0:
            val_steps = 1
        
        # Initialize progress bar
        pbar = tqdm(total=val_steps, desc="Validation")
        
        with torch.no_grad():
            for batch_idx, batch in enumerate(self.val_loader):
                if batch_idx >= val_steps:
                    break
                    
                # Preprocess batch
                processed_batch = self.preprocess_batch(batch)
                
                # Move batch to device
                input_ids = processed_batch["input_ids"]
                attention_mask = processed_batch["attention_mask"]
                labels = processed_batch["labels"]
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                loss = outputs.loss
                
                # Update metrics
                total_loss += loss.item()
                num_batches += 1
                
                # Update progress bar
                pbar.set_postfix({"loss": total_loss / num_batches})
                pbar.update(1)
                
                # Log to wandb
                if self.use_wandb:
                    wandb.log({"val/loss": loss.item()})
        
        pbar.close()
        return total_loss / num_batches if num_batches > 0 else float('inf')
    
    def train(self) -> None:
        """Train the model."""
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.config.num_epochs):
            logger.info(f"Starting epoch {epoch + 1}/{self.config.num_epochs}")
            self.current_epoch = epoch
            
            try:
                # Train
                train_loss = self.train_epoch()
                
                # Validate
                val_loss = self.validate()
                
                # Log metrics
                logger.info(f"Epoch {epoch + 1} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
                
                # Early stopping
                if val_loss < best_val_loss - self.config.min_delta:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Save best model
                    self.model.save(str(self.output_dir / "best_model"))
                else:
                    patience_counter += 1
                    if patience_counter >= self.config.patience:
                        logger.info("Early stopping triggered")
                        break
                
            except Exception as e:
                if self.config.continue_on_error:
                    logger.error(f"Error during training: {str(e)}")
                    continue
                else:
                    raise
    
    def save_checkpoint(self, filename: str) -> None:
        """Save a checkpoint."""
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'config': self.config.__dict__
        }
        
        if self.scaler:
            checkpoint['scaler_state_dict'] = self.scaler.state_dict()
        
        if self.swa_enabled:
            checkpoint['swa_model_state_dict'] = self.swa_model.state_dict()
            checkpoint['swa_scheduler_state_dict'] = self.swa_scheduler.state_dict()
        
        torch.save(checkpoint, self.output_dir / filename)
        logger.info(f"Saved checkpoint: {filename}")
    
    def load_checkpoint(self, filename: str) -> None:
        """Load a checkpoint."""
        checkpoint = torch.load(self.output_dir / filename)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        if self.scaler and 'scaler_state_dict' in checkpoint:
            self.scaler.load_state_dict(checkpoint['scaler_state_dict'])
        
        if self.swa_enabled and 'swa_model_state_dict' in checkpoint:
            self.swa_model.load_state_dict(checkpoint['swa_model_state_dict'])
            self.swa_scheduler.load_state_dict(checkpoint['swa_scheduler_state_dict'])
        
        logger.info(f"Loaded checkpoint: {filename}")

def load_training_data(file_path, source_lang='Python', target_lang='JavaScript'):
    """Load training data from JSON file with multiple programming languages.
    
    Args:
        file_path (str): Path to the data file
        source_lang (str): Source programming language
        target_lang (str): Target programming language
        
    Returns:
        tuple: Lists of source and target code strings
    """
    source_codes = []
    target_codes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                # Skip if either source or target language is missing
                if source_lang not in data or target_lang not in data:
                    continue
                source_codes.append(data[source_lang])
                target_codes.append(data[target_lang])
            except json.JSONDecodeError as e:
                logging.warning(f"Skipping invalid JSON line: {e}")
                continue
                
    if not source_codes or not target_codes:
        raise ValueError(f"No valid data found for {source_lang} to {target_lang} translation in {file_path}")
        
    return source_codes, target_codes

def train_model(config_path: str = None) -> None:
    """Train model using configuration from YAML file."""
    if config_path is None:
        # Get the directory where the current script is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'config', 'config.yml')
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Using config path: {config_path}")
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize model
    model = CodeTranslator(**config['model'])
    
    # Load training data
    train_source, train_target = load_training_data(config['data']['train_path'], source_lang=config['data']['source_lang'], target_lang=config['data']['target_lang'])
    val_source, val_target = load_training_data(config['data']['val_path'], source_lang=config['data']['source_lang'], target_lang=config['data']['target_lang'])
    
    # Create datasets
    train_dataset = MemoryEfficientDataset(
        source_codes=train_source,
        target_codes=train_target,
        tokenizer=model.tokenizer,
        max_length=model.max_length
    )
    
    val_dataset = MemoryEfficientDataset(
        source_codes=val_source,
        target_codes=val_target,
        tokenizer=model.tokenizer,
        max_length=model.max_length
    )
    
    # Initialize trainer
    trainer = ModelTrainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        config=config['training'],
        output_dir=config.get('output_dir'),
        use_wandb=config.get('use_wandb', False)
    )
    
    # Train model
    trainer.train()

if __name__ == "__main__":
    train_model()
