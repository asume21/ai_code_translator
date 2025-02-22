import argparse
import json
import re
from typing import List, Dict
from collections import defaultdict
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import torch
from transformers import RobertaTokenizer, RobertaModel

def tokenize_code(code: str, lang: str) -> List[str]:
    """Tokenize code into words and symbols."""
    # Remove comments
    code = re.sub(r'#.*?\n|//.*?\n|/\*.*?\*/', '', code)
    
    # Tokenize based on language syntax
    if lang in ['Python']:
        tokens = re.findall(r'[\w]+|[^\s\w]', code)
    else:  # C-like languages
        tokens = re.findall(r'[\w]+|[^\s\w]', code)
    
    return tokens

def calculate_codebleu(reference: str, candidate: str, lang: str, weights=(0.25, 0.25, 0.25, 0.25)) -> float:
    """Calculate CodeBLEU score."""
    # Tokenize both reference and candidate
    ref_tokens = tokenize_code(reference, lang)
    cand_tokens = tokenize_code(candidate, lang)
    
    # Calculate BLEU score with smoothing
    smooth = SmoothingFunction().method2
    bleu_score = sentence_bleu([ref_tokens], cand_tokens, 
                             weights=weights, 
                             smoothing_function=smooth)
    
    return bleu_score

def load_and_process_predictions(input_file: str) -> Dict:
    """Load and process model predictions."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = defaultdict(list)
    for example in data:
        source_lang = example['source_lang']
        target_lang = example['target_lang']
        reference = example['target']
        prediction = example['prediction']
        
        score = calculate_codebleu(reference, prediction, target_lang)
        results[f"{source_lang}_to_{target_lang}"].append(score)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Calculate CodeBLEU scores for translations")
    parser.add_argument("--input_file", required=True, help="Path to predictions file")
    parser.add_argument("--source_names", required=True, help="Source language names")
    parser.add_argument("--target_names", required=True, help="Target language names")
    parser.add_argument("--codebleu", action="store_true", help="Use CodeBLEU metric")
    
    args = parser.parse_args()
    
    # Process source and target names
    source_names = args.source_names.split(",")
    target_names = args.target_names.split(",")
    
    # Calculate scores
    results = load_and_process_predictions(args.input_file)
    
    # Print results
    print("\nTranslation Results:")
    print("-" * 50)
    for pair, scores in results.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        print(f"{pair}: {avg_score:.4f}")
    print("-" * 50)

if __name__ == "__main__":
    main()
