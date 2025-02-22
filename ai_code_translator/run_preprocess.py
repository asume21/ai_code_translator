import argparse
import json
import os
from typing import List, Dict, Any
from tqdm import tqdm

def clean_code(code: str) -> str:
    """Clean and normalize code."""
    # Remove redundant whitespace
    code = " ".join(code.split())
    # Normalize line endings
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    return code

def process_example(example: Dict[str, Any], source_names: List[str], target_names: List[str]) -> List[Dict[str, Any]]:
    """Process a single example into multiple translation pairs."""
    processed = []
    
    # Handle framework-specific translations (TensorFlow to PaddlePaddle)
    if "tensorflow" in example and "paddle" in example:
        processed.append({
            "source": clean_code(example["tensorflow"]),
            "target": clean_code(example["paddle"]),
            "source_lang": "tensorflow",
            "target_lang": "paddle"
        })
        
    # Handle regular language translations
    for source in source_names:
        if source not in example:
            continue
            
        source_code = clean_code(example[source])
        
        for target in target_names:
            if target == source or target not in example:
                continue
                
            target_code = clean_code(example[target])
            
            processed.append({
                "source": source_code,
                "target": target_code,
                "source_lang": source,
                "target_lang": target
            })
    
    return processed

def preprocess_data(input_file: str, output_file: str, source_names: List[str], target_names: List[str], sub_task: str):
    """Preprocess the data and save to output file."""
    print(f"Processing {input_file}...")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Read input data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process all examples
    processed_examples = []
    for example in tqdm(data["examples"], desc="Processing examples"):
        processed = process_example(example, source_names, target_names)
        processed_examples.extend(processed)
    
    # Add metadata
    output_data = {
        "sub_task": sub_task,
        "source_names": source_names,
        "target_names": target_names,
        "examples": processed_examples
    }
    
    # Save processed data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Processed {len(processed_examples)} translation pairs")
    print(f"Saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Preprocess code translation data")
    parser.add_argument("--input_file", required=True, help="Input JSON file path")
    parser.add_argument("--output_file", required=True, help="Output JSON file path")
    parser.add_argument("--source_names", required=True, help="Comma-separated list of source languages")
    parser.add_argument("--target_names", required=True, help="Comma-separated list of target languages")
    parser.add_argument("--sub_task", required=True, choices=["MultilingualTrans", "RareTrans"], 
                      help="Type of translation task")
    
    args = parser.parse_args()
    
    # Convert comma-separated strings to lists
    source_names = [lang.strip() for lang in args.source_names.split(",")]
    target_names = [lang.strip() for lang in args.target_names.split(",")]
    
    preprocess_data(args.input_file, args.output_file, source_names, target_names, args.sub_task)

if __name__ == "__main__":
    main()
