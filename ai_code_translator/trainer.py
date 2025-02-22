"""
Trainer module for code translation model.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import torch
from torch.cuda.amp import GradScaler, autocast
from torch.nn import Module
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import get_linear_schedule_with_warmup

class Trainer:
    """Trainer for code translation model."""
    
    def __init__(
        self,
        model: Module,
        train_dataset: Dataset,
        val_dataset: Dataset,
        batch_size: int = 8,
        learning_rate: float = 2e-5,
        num_epochs: int = 10,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        use_wandb: bool = False,
        fp16: bool = True,
        gradient_accumulation_steps: int = 1,
        warmup_steps: int = 0,
        max_grad_norm: float = 1.0,
    ):
        """Initialize trainer.
        
        Args:
            model: Model to train
            train_dataset: Training dataset
            val_dataset: Validation dataset
            batch_size: Batch size for training
            learning_rate: Learning rate
            num_epochs: Number of epochs to train
            checkpoint_dir: Directory to save checkpoints
            use_wandb: Whether to use Weights & Biases logging
            fp16: Whether to use mixed precision training
            gradient_accumulation_steps: Number of steps to accumulate gradients
            warmup_steps: Number of warmup steps for learning rate scheduler
            max_grad_norm: Maximum gradient norm for gradient clipping
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        self.model = model.to(self.device)
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        self.use_wandb = use_wandb
        self.fp16 = fp16 and torch.cuda.is_available()
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.warmup_steps = warmup_steps
        self.max_grad_norm = max_grad_norm
        
        # Initialize optimizer
        self.optimizer = AdamW(
            [p for p in self.model.parameters() if p.requires_grad],
            lr=learning_rate,
            weight_decay=0.01,
            eps=1e-8
        )
        
        # Initialize gradient scaler for fp16
        self.scaler = GradScaler() if fp16 else None
        
        # Initialize dataloaders
        self.train_dataloader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0,  # Avoid memory issues
            pin_memory=True
        )
        
        self.val_dataloader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,  # Avoid memory issues
            pin_memory=True
        )
        
        # Initialize learning rate scheduler
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=len(self.train_dataloader) * num_epochs
        )
        
        # Initialize wandb if requested
        if use_wandb:
            import wandb
            wandb.init(project="code-translator")
            
        # Create checkpoint directory
        if self.checkpoint_dir:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, epoch: int, metrics: Dict[str, float]) -> None:
        """Save model checkpoint."""
        if not self.checkpoint_dir:
            return
            
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "metrics": metrics
        }
        
        path = self.checkpoint_dir / f"checkpoint_epoch_{epoch}.pt"
        torch.save(checkpoint, path)
        print(f"Saved checkpoint to {path}")
    
    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        num_batches = len(self.train_dataloader)
        
        progress_bar = tqdm(self.train_dataloader, desc="Training")
        
        for step, batch in enumerate(progress_bar):
            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}
            
            # Forward pass with mixed precision
            if self.fp16:
                with autocast():
                    outputs = self.model(**batch)
                    loss = outputs.loss / self.gradient_accumulation_steps
                    
                # Backward pass with gradient scaling
                self.scaler.scale(loss).backward()
                
                if (step + 1) % self.gradient_accumulation_steps == 0:
                    # Unscale gradients
                    self.scaler.unscale_(self.optimizer)
                    
                    # Clip gradients
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.max_grad_norm
                    )
                    
                    # Optimizer step with gradient scaling
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                    
                    # Scheduler step
                    self.scheduler.step()
                    
                    # Zero gradients
                    self.optimizer.zero_grad()
            else:
                # Regular forward pass
                outputs = self.model(**batch)
                loss = outputs.loss / self.gradient_accumulation_steps
                
                # Regular backward pass
                loss.backward()
                
                if (step + 1) % self.gradient_accumulation_steps == 0:
                    # Clip gradients
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.max_grad_norm
                    )
                    
                    # Optimizer step
                    self.optimizer.step()
                    
                    # Scheduler step
                    self.scheduler.step()
                    
                    # Zero gradients
                    self.optimizer.zero_grad()
            
            total_loss += loss.item() * self.gradient_accumulation_steps
            
            # Update progress bar
            progress_bar.set_postfix({
                "loss": total_loss / (step + 1)
            })
            
        return {"loss": total_loss / num_batches}
    
    @torch.no_grad()
    def evaluate(self) -> Dict[str, float]:
        """Evaluate model on validation set."""
        self.model.eval()
        total_loss = 0
        num_batches = len(self.val_dataloader)
        
        progress_bar = tqdm(self.val_dataloader, desc="Validating")
        
        for batch in progress_bar:
            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}
            
            # Forward pass
            if self.fp16:
                with autocast():
                    outputs = self.model(**batch)
                    loss = outputs.loss
            else:
                outputs = self.model(**batch)
                loss = outputs.loss
            
            total_loss += loss.item()
            
            # Update progress bar
            progress_bar.set_postfix({
                "loss": total_loss / (num_batches)
            })
            
        return {"loss": total_loss / num_batches}
    
    def train(self) -> None:
        """Train model for specified number of epochs."""
        print("Starting training...")
        
        for epoch in range(self.num_epochs):
            print(f"\nEpoch {epoch + 1}/{self.num_epochs}")
            
            # Train
            train_metrics = self.train_epoch()
            print(f"Training loss: {train_metrics['loss']:.4f}")
            
            # Evaluate
            val_metrics = self.evaluate()
            print(f"Validation loss: {val_metrics['loss']:.4f}")
            
            # Log metrics
            if self.use_wandb:
                import wandb
                wandb.log({
                    "epoch": epoch + 1,
                    "train_loss": train_metrics["loss"],
                    "val_loss": val_metrics["loss"]
                })
            
            # Save checkpoint
            metrics = {
                "train_loss": train_metrics["loss"],
                "val_loss": val_metrics["loss"]
            }
            self.save_checkpoint(epoch + 1, metrics)
