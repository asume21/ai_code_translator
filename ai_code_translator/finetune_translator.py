import json
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Seq2SeqTrainingArguments, Seq2SeqTrainer
from torch.utils.data import Dataset

class CodeTranslationDataset(Dataset):
    def __init__(self, data, tokenizer, max_length=512):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        source_code = item["Python"]
        target_code = item["C"]

        # Add special tokens to help model distinguish between different types of translations
        if "tensorflow" in item:
            source_code = "<TF2PD>\n" + item["tensorflow"]
            target_code = "<PADDLE>\n" + item["paddle"]
        else:
            source_code = "<PY2C>\n" + source_code
            target_code = "<C>\n" + target_code

        source_tokens = self.tokenizer(source_code, max_length=self.max_length, truncation=True, padding="max_length", return_tensors="pt")
        target_tokens = self.tokenizer(target_code, max_length=self.max_length, truncation=True, padding="max_length", return_tensors="pt")

        return {
            "input_ids": source_tokens["input_ids"].squeeze(),
            "attention_mask": source_tokens["attention_mask"].squeeze(),
            "labels": target_tokens["input_ids"].squeeze()
        }

def main():
    # Load data
    with open("translation_examples.json", "r") as f:
        data = json.load(f)["examples"]

    # Initialize tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
    model = AutoModelForSeq2SeqLM.from_pretrained("Salesforce/codet5-base")

    # Add special tokens
    special_tokens = ["<PY2C>", "<C>", "<TF2PD>", "<PADDLE>"]
    tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
    model.resize_token_embeddings(len(tokenizer))

    # Create dataset
    dataset = CodeTranslationDataset(data, tokenizer)

    # Training arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir="finetuned_translator",
        num_train_epochs=200,  # Increased epochs for better learning
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        warmup_steps=100,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        evaluation_strategy="steps",
        eval_steps=10,
        save_steps=50,
        learning_rate=2e-5,  # Reduced learning rate for stability
        fp16=True,  # Enable mixed precision training
        gradient_accumulation_steps=4,  # Accumulate gradients for larger effective batch size
    )

    # Initialize trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        eval_dataset=dataset,
    )

    # Train model
    trainer.train()
    
    # Save model
    model.save_pretrained("finetuned_translator")
    tokenizer.save_pretrained("finetuned_translator")

if __name__ == "__main__":
    main()
