"""Advanced code cleaning and normalization for Python-JavaScript translation."""

import ast
import re
import json
import os
from typing import Dict, List, Optional, Tuple

class CodeCleaner:
    """Advanced code cleaning and normalization."""
    
    def __init__(self):
        self.py_patterns = {
            # Convert Python list operations to JavaScript
            r'(\w+)\.append\((.*?)\)': r'\1.push(\2)',
            r'len\((.*?)\)': r'\1.length',
            r'(\w+)\.extend\((.*?)\)': r'\1.push(...\2)',
            
            # Convert Python dict operations
            r'(\w+)\.keys\(\)': r'Object.keys(\1)',
            r'(\w+)\.values\(\)': r'Object.values(\1)',
            r'(\w+)\.items\(\)': r'Object.entries(\1)',
            
            # Convert Python string operations
            r'(\w+)\.join\((.*?)\)': r'\2.join(\1)',
            r'(\w+)\.strip\(\)': r'\1.trim()',
            r'(\w+)\.lower\(\)': r'\1.toLowerCase()',
            r'(\w+)\.upper\(\)': r'\1.toUpperCase()',
            
            # Convert Python range
            r'range\((\d+)\)': r'Array.from({length: \1}, (_, i) => i)',
            r'range\((.*?),\s*(.*?)\)': r'Array.from({length: \2-\1}, (_, i) => i+\1)',
            
            # Convert Python list comprehensions
            r'\[(.*?) for (.*?) in (.*?)\]': r'\3.map(\2 => \1)',
            r'\[(.*?) for (.*?) in (.*?) if (.*?)\]': r'\3.filter(\2 => \4).map(\2 => \1)',
        }
        
        self.js_patterns = {
            # Convert JavaScript array operations to Python
            r'(\w+)\.push\((.*?)\)': r'\1.append(\2)',
            r'(\w+)\.length': r'len(\1)',
            r'(\w+)\.splice\((.*?)\)': r'\1[\2]',
            
            # Convert JavaScript object operations
            r'Object\.keys\((.*?)\)': r'\1.keys()',
            r'Object\.values\((.*?)\)': r'\1.values()',
            r'Object\.entries\((.*?)\)': r'\1.items()',
            
            # Convert JavaScript string operations
            r'(\w+)\.trim\(\)': r'\1.strip()',
            r'(\w+)\.toLowerCase\(\)': r'\1.lower()',
            r'(\w+)\.toUpperCase\(\)': r'\1.upper()',
            
            # Convert JavaScript array creation
            r'Array\.from\({length:\s*(\d+)}\)': r'[None] * \1',
            r'Array\((.*?)\)\.fill\((.*?)\)': r'[\2] * \1',
            
            # Convert JavaScript arrow functions
            r'\((.*?)\)\s*=>\s*{(.*?)}': r'lambda \1: \2',
        }
    
    def normalize_python(self, code: str) -> str:
        """Normalize Python code with advanced cleaning."""
        try:
            # Parse and unparse to normalize syntax
            tree = ast.parse(code)
            code = ast.unparse(tree)
            
            # Remove comments and docstrings
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
                    node.value.s = ""
            code = ast.unparse(tree)
            
            # Clean up whitespace
            lines = [line for line in code.split('\n') if line.strip()]
            code = '\n'.join(lines)
            
            # Ensure proper function definition
            if not code.startswith('def '):
                if 'return' in code:
                    code = 'def solution():\n    ' + '\n    '.join(code.split('\n'))
                else:
                    code = 'def solution():\n    return ' + code
            
            return code
        except:
            return self._basic_python_cleanup(code)
    
    def normalize_javascript(self, code: str) -> str:
        """Normalize JavaScript code with advanced cleaning."""
        try:
            # Remove comments
            code = re.sub(r'//.*?\n|/\*.*?\*/', '', code, flags=re.DOTALL)
            
            # Normalize function definition
            if not re.search(r'function\s+\w+\s*\(', code):
                if 'return' in code:
                    code = 'function solution() {\n    ' + '\n    '.join(code.split('\n')) + '\n}'
                else:
                    code = 'function solution() {\n    return ' + code + ';\n}'
            
            # Fix common syntax issues
            code = code.replace('elif', 'else if')
            code = code.replace('True', 'true')
            code = code.replace('False', 'false')
            code = code.replace('None', 'null')
            
            # Ensure semicolons
            lines = code.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.endswith('{') and not line.endswith('}') and not line.endswith(';'):
                    lines[i] = line + ';'
            code = '\n'.join(lines)
            
            return code
        except:
            return self._basic_javascript_cleanup(code)
    
    def _basic_python_cleanup(self, code: str) -> str:
        """Basic Python code cleanup for when AST parsing fails."""
        lines = []
        indent = 0
        
        for line in code.split('\n'):
            line = line.strip()
            if line:
                if line.endswith(':'):
                    lines.append('    ' * indent + line)
                    indent += 1
                else:
                    lines.append('    ' * indent + line)
                    if line in ['return', 'break', 'continue', 'pass']:
                        indent = max(0, indent - 1)
        
        code = '\n'.join(lines)
        if not code.startswith('def '):
            code = 'def solution():\n    ' + code
        
        return code
    
    def _basic_javascript_cleanup(self, code: str) -> str:
        """Basic JavaScript code cleanup for when parsing fails."""
        lines = []
        indent = 0
        
        for line in code.split('\n'):
            line = line.strip()
            if line:
                if line.endswith('{'):
                    lines.append('    ' * indent + line)
                    indent += 1
                elif line.startswith('}'):
                    indent = max(0, indent - 1)
                    lines.append('    ' * indent + line)
                else:
                    lines.append('    ' * indent + line)
        
        code = '\n'.join(lines)
        if not re.search(r'function\s+\w+\s*\(', code):
            code = 'function solution() {\n    ' + code + '\n}'
        
        return code
    
    def translate_syntax(self, code: str, source_lang: str) -> str:
        """Translate language-specific syntax patterns."""
        patterns = self.py_patterns if source_lang == 'python' else self.js_patterns
        
        for pattern, replacement in patterns.items():
            code = re.sub(pattern, replacement, code)
        
        return code
    
    def extract_function_info(self, code: str, lang: str) -> Optional[Dict]:
        """Extract function signature and body."""
        try:
            if lang == 'python':
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        return {
                            'name': node.name,
                            'params': [arg.arg for arg in node.args.args],
                            'body': ast.unparse(node.body),
                            'returns': self._get_return_type(node)
                        }
            else:
                # Extract JavaScript function info
                pattern = r'function\s+(\w+)\s*\((.*?)\)\s*{(.*?)}'
                match = re.search(pattern, code, re.DOTALL)
                if match:
                    return {
                        'name': match.group(1),
                        'params': [p.strip() for p in match.group(2).split(',') if p.strip()],
                        'body': match.group(3).strip(),
                        'returns': self._guess_js_return_type(match.group(3))
                    }
        except:
            pass
        return None
    
    def _get_return_type(self, node: ast.FunctionDef) -> str:
        """Get Python function return type."""
        returns = []
        for n in ast.walk(node):
            if isinstance(n, ast.Return):
                if isinstance(n.value, ast.Num):
                    returns.append('number')
                elif isinstance(n.value, ast.Str):
                    returns.append('string')
                elif isinstance(n.value, ast.List):
                    returns.append('array')
                elif isinstance(n.value, ast.Dict):
                    returns.append('object')
                elif isinstance(n.value, ast.Name) and n.value.id in ['True', 'False']:
                    returns.append('boolean')
        return returns[0] if returns else 'any'
    
    def _guess_js_return_type(self, body: str) -> str:
        """Guess JavaScript function return type."""
        if 'return' not in body:
            return 'void'
        
        # Extract return value
        match = re.search(r'return\s+(.*?)[;\n]', body)
        if not match:
            return 'any'
        
        value = match.group(1)
        if value.isdigit() or '.' in value:
            return 'number'
        elif value.startswith('"') or value.startswith("'"):
            return 'string'
        elif value.startswith('['):
            return 'array'
        elif value.startswith('{'):
            return 'object'
        elif value in ['true', 'false']:
            return 'boolean'
        return 'any'

def clean_dataset(input_file: str, output_file: str):
    """Clean and normalize the entire dataset."""
    cleaner = CodeCleaner()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_pairs = []
    stats = {
        'total': len(data['pairs']),
        'cleaned': 0,
        'failed': 0,
        'types': {'number': 0, 'string': 0, 'array': 0, 'object': 0, 'boolean': 0, 'any': 0}
    }
    
    print(f"Cleaning {stats['total']} pairs...")
    
    for i, pair in enumerate(data['pairs']):
        print(f"\rCleaning pair {i+1}/{stats['total']}...", end='')
        
        try:
            # Clean and normalize code
            python_code = cleaner.normalize_python(pair['source'])
            js_code = cleaner.normalize_javascript(pair['target'])
            
            # Extract function info
            py_info = cleaner.extract_function_info(python_code, 'python')
            js_info = cleaner.extract_function_info(js_code, 'javascript')
            
            if py_info and js_info:
                # Update type statistics
                stats['types'][py_info['returns']] = stats['types'].get(py_info['returns'], 0) + 1
                
                cleaned_pairs.append({
                    'source': python_code,
                    'target': js_code,
                    'source_lang': 'python',
                    'target_lang': 'javascript',
                    'metadata': {
                        'python_info': py_info,
                        'javascript_info': js_info,
                        'return_type': py_info['returns'],
                        'complexity': 'medium'  # TODO: Implement complexity analysis
                    }
                })
                stats['cleaned'] += 1
            else:
                stats['failed'] += 1
        except Exception as e:
            stats['failed'] += 1
    
    output_data = {
        'version': '1.2',
        'statistics': stats,
        'pairs': cleaned_pairs
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print("\n\nDataset Cleaning Results:")
    print(f"Total pairs: {stats['total']}")
    print(f"Cleaned pairs: {stats['cleaned']}")
    print(f"Failed pairs: {stats['failed']}")
    print("\nReturn Type Distribution:")
    for type_name, count in stats['types'].items():
        print(f"{type_name}: {count}")
    print(f"\nCleaned dataset saved to: {output_file}")

if __name__ == '__main__':
    # Paths
    project_dir = os.path.dirname(os.path.dirname(__file__))
    input_file = os.path.join(project_dir, 'ai_code_translator', 'data', 'combined_dataset.json')
    output_file = os.path.join(project_dir, 'ai_code_translator', 'data', 'cleaned_dataset.json')
    
    # Clean dataset
    clean_dataset(input_file, output_file)
