"""
Preprocess code translation datasets.
"""

import json
import re
import ast
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from ai_code_translator.languages import LanguageConfig

def remove_comments(code: str, language: str) -> str:
    """Remove comments from code based on language."""
    if language == 'python':
        # Remove multi-line docstrings
        code = re.sub(r'"""[\s\S]*?"""', '', code)
        code = re.sub(r"'''[\s\S]*?'''", '', code)
        # Remove single-line comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    else:
        # Remove C-style comments
        code = re.sub(r'/\*[\s\S]*?\*/', '', code)
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
    return code

def normalize_strings(code: str, language: str) -> str:
    """Normalize string quotes based on language conventions."""
    if language == 'python':
        # Use double quotes for strings in Python
        code = re.sub(r"(?<!\\)'([^'\\]*(?:\\.[^'\\]*)*)'", r'"\1"', code)
    elif language in ['javascript', 'typescript']:
        # Use single quotes for strings in JS/TS
        code = re.sub(r'(?<!\\)"([^"\\]*(?:\\.[^"\\]*)*)"', r"'\1'", code)
    return code

def normalize_whitespace(code: str) -> str:
    """Normalize whitespace in code."""
    # Replace tabs with spaces
    code = code.replace('\t', '    ')
    # Remove trailing whitespace
    code = re.sub(r'[ \t]+$', '', code, flags=re.MULTILINE)
    # Normalize line endings
    code = code.replace('\r\n', '\n')
    # Remove multiple blank lines
    code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
    # Ensure single newline at end
    return code.strip() + '\n'

def remove_unused_imports(code: str, language: str) -> str:
    """Remove unused imports based on language."""
    if language == 'python':
        try:
            tree = ast.parse(code)
            imports = []
            used_names = set()
            
            # Collect imports and used names
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)
                elif isinstance(node, ast.Name):
                    used_names.add(node.id)
            
            # Filter out unused imports
            lines = code.split('\n')
            for imp in imports:
                if isinstance(imp, ast.Import):
                    for name in imp.names:
                        if name.asname:
                            if name.asname not in used_names:
                                lines[imp.lineno-1] = ''
                        elif name.name not in used_names:
                            lines[imp.lineno-1] = ''
                            
            return '\n'.join(line for line in lines if line.strip())
        except SyntaxError:
            return code
    return code

def validate_code_pair(source: str, target: str, source_lang: str, target_lang: str) -> bool:
    """Validate that code pairs are suitable for training."""
    # Skip empty code
    if not source.strip() or not target.strip():
        return False
        
    # Skip very short code
    if len(source.split()) < 3 or len(target.split()) < 3:
        return False
        
    # Skip if length ratio is too extreme
    ratio = len(source.split()) / len(target.split())
    if ratio < 0.3 or ratio > 3.0:
        return False
        
    # Skip if code contains unwanted patterns
    unwanted = ['TODO', 'FIXME', 'XXX', '???']
    if any(p in source or p in target for p in unwanted):
        return False
        
    return True

def clean_code(code: str, language: str) -> str:
    """Clean and normalize code."""
    code = remove_comments(code, language)
    code = normalize_strings(code, language)
    code = normalize_whitespace(code)
    code = remove_unused_imports(code, language)
    return code.strip()

def process_file(input_path: str, output_path: str, source_lang: str, target_lang: str):
    """Process a single dataset file."""
    data = load_dataset(input_path)
    processed_data = []
    skipped = 0
    
    for item in data:
        if source_lang in item and target_lang in item:
            source = clean_code(item[source_lang], source_lang)
            target = clean_code(item[target_lang], target_lang)
            
            if validate_code_pair(source, target, source_lang, target_lang):
                processed_data.append({
                    'id': item.get('id', ''),
                    'name': item.get('name', ''),
                    'source': source,
                    'target': target,
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'difficulty': item.get('difficulty', 'medium'),
                    'tags': item.get('tags', [])
                })
            else:
                skipped += 1
    
    print(f"Processed {len(processed_data)} pairs, skipped {skipped} invalid pairs")
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2)

def load_dataset(file_path: str) -> List[Dict]:
    """Load dataset from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='Preprocess code translation datasets')
    parser.add_argument('--input', required=True, help='Input dataset file')
    parser.add_argument('--output', required=True, help='Output processed file')
    parser.add_argument('--source-lang', required=True, help='Source language')
    parser.add_argument('--target-lang', required=True, help='Target language')
    
    args = parser.parse_args()
    process_file(args.input, args.output, args.source_lang, args.target_lang)

if __name__ == '__main__':
    main()
