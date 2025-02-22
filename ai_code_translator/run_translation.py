import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoConfig,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    set_seed,
)

logger = logging.getLogger(__name__)

@dataclass
class ModelArguments:
    model_name_or_path: str
    config_name: Optional[str] = None
    tokenizer_name: Optional[str] = None
    cache_dir: Optional[str] = None
    use_fast_tokenizer: bool = True
    model_revision: str = "main"

@dataclass
class DataTrainingArguments:
    train_file: str
    validation_file: str
    test_file: str
    source_prefix: Optional[str] = None
    max_source_length: Optional[int] = 1024
    max_target_length: Optional[int] = 1024
    text_column: str = "source"
    summary_column: str = "target"

class CodeTranslationDataset(Dataset):
    def __init__(
        self,
        data_file: str,
        tokenizer: AutoTokenizer,
        max_source_length: int,
        max_target_length: int,
    ):
        with open(data_file, "r", encoding="utf-8") as f:
            self.examples = json.load(f)["examples"]
        self.tokenizer = tokenizer
        self.max_source_length = max_source_length
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, i):
        example = self.examples[i]
        source = example["source"]
        target = example["target"]

        source_ids = self.tokenizer(
            source,
            max_length=self.max_source_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        target_ids = self.tokenizer(
            target,
            max_length=self.max_target_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        return {
            "input_ids": source_ids["input_ids"].squeeze(),
            "attention_mask": source_ids["attention_mask"].squeeze(),
            "labels": target_ids["input_ids"].squeeze(),
        }

def main():
    parser = argparse.ArgumentParser(description="Train code translation model")
    parser.add_argument("--model_name_or_path", required=True)
    parser.add_argument("--do_train", action="store_true")
    parser.add_argument("--do_eval", action="store_true")
    parser.add_argument("--do_predict", action="store_true")
    parser.add_argument("--train_file", required=True)
    parser.add_argument("--validation_file", required=True)
    parser.add_argument("--test_file", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--max_source_length", type=int, default=1024)
    parser.add_argument("--max_target_length", type=int, default=1024)
    parser.add_argument("--per_device_train_batch_size", type=int, default=8)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=5e-5)
    parser.add_argument("--num_train_epochs", type=float, default=3)
    parser.add_argument("--logging_dir", type=str, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--fp16", action="store_true")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO,
    )

    # Set seed
    set_seed(args.seed)

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.model_name_or_path)

    # Add special tokens
    special_tokens = ["<PY2C>", "<C>", "<TF2PD>", "<PADDLE>"]
    tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
    model.resize_token_embeddings(len(tokenizer))

    # Create datasets
    train_dataset = CodeTranslationDataset(
        args.train_file, tokenizer, args.max_source_length, args.max_target_length
    ) if args.do_train else None
    
    eval_dataset = CodeTranslationDataset(
        args.validation_file, tokenizer, args.max_source_length, args.max_target_length
    ) if args.do_eval else None
    
    test_dataset = CodeTranslationDataset(
        args.test_file, tokenizer, args.max_source_length, args.max_target_length
    ) if args.do_predict else None

    # Initialize trainer
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        learning_rate=args.learning_rate,
        num_train_epochs=args.num_train_epochs,
        logging_dir=args.logging_dir,
        logging_steps=100,
        save_steps=1000,
        eval_steps=1000,
        evaluation_strategy="steps",
        fp16=args.fp16,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    )

    # Training
    if args.do_train:
        trainer.train()
        trainer.save_model()
        tokenizer.save_pretrained(args.output_dir)

    # Evaluation
    if args.do_eval:
        logger.info("*** Evaluate ***")
        metrics = trainer.evaluate()
        trainer.log_metrics("eval", metrics)

    # Prediction
    if args.do_predict:
        logger.info("*** Predict ***")
        predictions = trainer.predict(test_dataset)
        
        # Decode predictions
        decoded_preds = []
        for pred in predictions.predictions:
            try:
                decoded = tokenizer.decode(torch.tensor(pred).squeeze(), skip_special_tokens=True)
                decoded_preds.append(decoded)
            except Exception as e:
                logger.warning(f"Error decoding prediction: {e}")
                decoded_preds.append("")
        
        # Save predictions
        test_examples = test_dataset.examples
        predictions_data = []
        for i, (pred, example) in enumerate(zip(decoded_preds, test_examples)):
            predictions_data.append({
                "source": example["source"],
                "target": example["target"],
                "prediction": pred,
                "source_lang": example.get("source_lang", "unknown"),
                "target_lang": example.get("target_lang", "unknown")
            })
        
        with open(os.path.join(args.output_dir, "generated_predictions.json"), "w") as f:
            json.dump(predictions_data, f, indent=2)

if __name__ == "__main__":
    main()
