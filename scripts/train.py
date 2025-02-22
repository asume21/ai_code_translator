"""
Training script for the code translator model with memory optimizations.
"""

import os
import gc
import torch
from pathlib import Path
from torch.utils.data import random_split
from ai_code_translator.model import CodeTranslator
from ai_code_translator.dataset import CodeTranslationDataset
from ai_code_translator.trainer import Trainer

def setup_memory_optimizations():
    """Setup memory optimizations for training."""
    # Enable garbage collection
    gc.enable()
    
    # Set memory allocation config
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    # Configure PyTorch to be memory efficient
    torch.backends.cudnn.benchmark = True
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def main():
    # Set random seed for reproducibility
    torch.manual_seed(42)
    
    # Apply memory optimizations
    setup_memory_optimizations()
    
    # Initialize paths
    data_dir = Path(__file__).parent.parent / 'data'
    checkpoint_dir = Path(__file__).parent.parent / 'checkpoints'
    
    # Create checkpoint directory
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize model with optimizations
    model = CodeTranslator(
        model_name="Salesforce/codet5-base",
        gradient_checkpointing=False
    )
    
    # Load and prepare datasets
    print("Loading datasets...")
    
    # Define dataset paths
    dataset_paths = [
        data_dir / "apps" / "train.json",
        data_dir / "code_alpaca" / "train.json",
        data_dir / "codesearchnet" / "python" / "train.json",
        data_dir / "codesearchnet" / "java" / "train.json",
        data_dir / "codesearchnet" / "javascript" / "train.json"
    ]
    
    # Create combined dataset with memory-efficient loading
    train_dataset = CodeTranslationDataset.from_paths(
        dataset_paths,
        max_length=384,  # Reduced from 512 to save memory
        tokenizer=model.tokenizer
    )
    
    # Split into train/val
    train_size = int(0.9 * len(train_dataset))
    val_size = len(train_dataset) - train_size
    train_dataset, val_dataset = random_split(train_dataset, [train_size, val_size])
    
    print(f"Training on {len(train_dataset)} examples")
    print(f"Validating on {len(val_dataset)} examples")
    
    # Initialize trainer with memory optimizations
    trainer = Trainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        batch_size=1,  # Minimum batch size
        learning_rate=2e-5,
        num_epochs=10,
        checkpoint_dir=checkpoint_dir,
        use_wandb=False,
        fp16=False,
        gradient_accumulation_steps=32,  # Increased for effective batch size
        warmup_steps=1000,
        max_grad_norm=1.0
    )
    
    try:
        # Start training
        print("Starting training...")
        trainer.train()
        print("Training complete!")
        print(f"Model checkpoints saved to {checkpoint_dir}")
    except RuntimeError as e:
        if "out of memory" in str(e):
            print("WARNING: out of memory")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        raise e
    finally:
        # Cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

if __name__ == "__main__":
    main()
