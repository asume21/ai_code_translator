"""
Download and prepare datasets for code translation.
"""

import os
import json
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Any
from datasets import load_dataset
from tqdm import tqdm

def clean_huggingface_cache():
    """Clean HuggingFace cache to avoid disk space issues."""
    print("Cleaning HuggingFace cache...")
    cache_dir = Path.home() / ".cache" / "huggingface"
    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)

def download_apps_dataset(data_dir: Path) -> None:
    """Download and prepare Apps dataset."""
    print("Downloading Apps dataset...")
    
    apps_dir = data_dir / "apps"
    apps_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    dataset = load_dataset("codeparrot/apps")
    
    # Prepare train split
    train_data = []
    for item in tqdm(dataset["train"][:5000], desc="Generating train split"):
        train_data.append({
            "source": item["problem"],
            "target": item["solution"],
            "source_lang": "natural",
            "target_lang": "python"
        })
    
    with open(apps_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2)
    
    # Prepare test split
    test_data = []
    for item in tqdm(dataset["test"][:5000], desc="Generating test split"):
        test_data.append({
            "source": item["problem"],
            "target": item["solution"],
            "source_lang": "natural",
            "target_lang": "python"
        })
    
    with open(apps_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2)
    
    print("Successfully downloaded Apps dataset")

def download_codesearchnet_dataset(data_dir: Path) -> None:
    """Download and prepare CodeSearchNet dataset."""
    print("Downloading CodeSearchNet dataset...")
    
    languages = ["python", "java", "javascript"]
    csn_dir = data_dir / "codesearchnet"
    
    for lang in languages:
        clean_huggingface_cache()
        print(f"Successfully downloaded {lang} from CodeSearchNet")
        
        lang_dir = csn_dir / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        dataset = load_dataset("code_search_net", lang)
        
        for split in ["train", "test", "validation"]:
            split_data = []
            
            # Get docstring and code pairs
            for item in tqdm(dataset[split], desc=f"Generating {split} split"):
                if item["docstring"] and item["code"]:
                    split_data.append({
                        "source": item["docstring"],
                        "target": item["code"],
                        "source_lang": "natural",
                        "target_lang": lang
                    })
            
            # Save to file
            output_file = lang_dir / f"{split}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(split_data, f, indent=2)

def download_code_alpaca_dataset(data_dir: Path) -> None:
    """Download and prepare Code Alpaca dataset."""
    print("Downloading Code Alpaca dataset...")
    
    alpaca_dir = data_dir / "code_alpaca"
    alpaca_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    dataset = load_dataset("sahil2801/CodeAlpaca-20k")
    
    # Prepare train data
    train_data = []
    for item in tqdm(dataset["train"], desc="Generating train split"):
        train_data.append({
            "source": item["instruction"] + "\n" + item["input"] if item["input"] else item["instruction"],
            "target": item["output"],
            "source_lang": "natural",
            "target_lang": "code"
        })
    
    # Save to file
    with open(alpaca_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2)
    
    print("Successfully downloaded Code Alpaca dataset")

def copy_codetransocean_dataset(data_dir: Path) -> None:
    """Copy CodeTransOcean dataset from local path."""
    print("Copying CodeTransOcean dataset...")
    
    codetransocean_dir = data_dir / "codetransocean"
    
    # Define subdatasets
    subdatasets = [
        ("multilingualtrans", ["multilingual_train.jsonl", "multilingual_test.jsonl", "multilingual_valid.jsonl"]),
        ("nichetrans", ["niche_train.jsonl", "niche_test.jsonl", "niche_valid.jsonl"]),
        ("dltrans", ["dl_train.jsonl", "dl_test.jsonl", "dl_valid.jsonl"]),
        ("llmtrans", ["LLMTrans.jsonl"])
    ]
    
    for subdir, files in subdatasets:
        target_dir = codetransocean_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each file
        for filename in files:
            source_file = target_dir / filename
            target_file = target_dir / filename.replace(".jsonl", ".json")
            
            if source_file.exists():
                # Read JSONL file line by line
                data = []
                with open(source_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            item = json.loads(line.strip())
                            data.append(item)
                        except json.JSONDecodeError as e:
                            print(f"Error parsing line in {source_file}: {e}")
                            continue
                
                # Write as JSON array
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                
                print(f"Successfully copied {subdir}")
    
    print("Successfully copied all CodeTransOcean datasets")

def count_examples(data_dir: Path) -> None:
    """Count number of examples in each dataset file."""
    total_files = 0
    total_examples = 0
    
    for json_file in data_dir.rglob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    num_examples = len(data)
                    print(f"Dataset {json_file.relative_to(data_dir)}: {num_examples} examples")
                    total_files += 1
                    total_examples += num_examples
        except json.JSONDecodeError as e:
            print(f"Error reading {json_file}: {str(e)}")
            continue
    
    print(f"\nTotal files downloaded: {total_files}")
    print(f"Total examples: {total_examples}")

def main():
    # Set up data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Download/prepare each dataset
    clean_huggingface_cache()
    download_apps_dataset(data_dir)
    
    clean_huggingface_cache()
    download_codesearchnet_dataset(data_dir)
    
    clean_huggingface_cache()
    download_code_alpaca_dataset(data_dir)
    
    clean_huggingface_cache()
    copy_codetransocean_dataset(data_dir)
    
    # Count examples
    count_examples(data_dir)
    
    print(f"\nDataset download complete!")
    print(f"Data directory: {data_dir}")

if __name__ == "__main__":
    main()
