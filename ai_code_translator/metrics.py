"""Evaluation metrics for code translation."""

from typing import List, Dict, Tuple
import ast
import re
from collections import Counter
from .languages import LanguageConfig
import math

class CodeEvaluator:
    """Evaluates code translation quality using multiple metrics."""
    
    @staticmethod
    def evaluate(source_code: str, translated_code: str, target_lang: str) -> Dict[str, float]:
        """Evaluate the quality of code translation.
        
        Args:
            source_code (str): Original source code
            translated_code (str): Translated code
            target_lang (str): Target programming language
            
        Returns:
            Dict[str, float]: Dictionary containing evaluation metrics
        """
        metrics = {}
        
        # Check syntax validity
        metrics['syntax_valid'] = CodeEvaluator._check_syntax(translated_code, target_lang)
        
        # Calculate BLEU score
        metrics['bleu_score'] = CodeEvaluator._calculate_bleu(source_code, translated_code)
        
        # Calculate structural similarity
        metrics['structural_similarity'] = CodeEvaluator._calculate_structural_similarity(
            source_code, translated_code
        )
        
        # Calculate overall score
        metrics['overall_score'] = (
            metrics['syntax_valid'] * 0.4 +
            metrics['bleu_score'] * 0.3 +
            metrics['structural_similarity'] * 0.3
        )
        
        return metrics
    
    @staticmethod
    def _check_syntax(code: str, language: str) -> float:
        """Check if the code has valid syntax for the given language.
        
        Args:
            code (str): Code to check
            language (str): Programming language
            
        Returns:
            float: 1.0 if syntax is valid, 0.0 otherwise
        """
        try:
            # Get language patterns
            patterns = LanguageConfig.get_language_pattern(language)
            
            # Basic syntax checks
            if not code.strip():
                return 0.0
                
            # Check balanced brackets and parentheses
            brackets = {'(': ')', '[': ']', '{': '}'}
            stack = []
            
            for char in code:
                if char in brackets:
                    stack.append(char)
                elif char in brackets.values():
                    if not stack:
                        return 0.0
                    if brackets[stack[-1]] != char:
                        return 0.0
                    stack.pop()
            
            if stack:
                return 0.0
                
            # Language-specific checks
            if language == 'python':
                # Check indentation consistency
                indent_size = None
                current_indent = 0
                
                for line in code.split('\n'):
                    if not line.strip():
                        continue
                        
                    spaces = len(line) - len(line.lstrip())
                    
                    # First indented line sets the indent size
                    if spaces > 0:
                        if indent_size is None:
                            indent_size = spaces
                        elif spaces % indent_size != 0:
                            return 0.0
                            
                        # Check for sudden large changes in indentation
                        if spaces > current_indent + indent_size:
                            return 0.0
                            
                    current_indent = spaces
                    
            elif language in ['java', 'javascript', 'cpp', 'csharp']:
                # Basic structure checks for C-style languages
                
                # Check class declarations
                if 'class' in code:
                    class_matches = re.findall(r'class\s+(\w+)', code)
                    if not class_matches:
                        return 0.0
                        
                # Check function declarations
                if 'function' in code or ('def' in code and language != 'python'):
                    func_matches = re.findall(r'(?:function|def)\s+(\w+)', code)
                    if not func_matches:
                        return 0.0
                        
                # Check statement termination for non-control lines
                lines = code.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Skip lines that don't need termination
                    if any(line.startswith(x) for x in [
                        'import', 'from', 'class', 'def', 'if', 'else', 'elif',
                        'while', 'for', 'try', 'catch', 'except', 'finally',
                        'package', 'using', '#', '//', '/*', '*', '@', '}'
                    ]):
                        continue
                        
                    # Skip lines that already have valid termination
                    if any(line.endswith(x) for x in ['{', '}', ':', ';', '{']):
                        continue
                        
                    # Skip function/class declarations
                    if re.match(r'^(public|private|protected|static|final)?\s*(class|interface|enum|struct)', line):
                        continue
                    if re.match(r'^(public|private|protected)?\s*(static|final|async)?\s*\w+\s+\w+\s*\([^)]*\)\s*$', line):
                        continue
                    if re.match(r'^(public|private|protected)?\s*(static|final)?\s*\w+\s*\([^)]*\)\s*$', line):
                        continue
                        
                    # Skip lines that are part of a multi-line statement
                    if line.count('(') > line.count(')'):
                        continue
                        
                    # Line needs termination
                    if language in ['java', 'javascript', 'cpp', 'csharp']:
                        if not line.endswith(';'):
                            # Allow lines that end with operators
                            if not any(line.endswith(op) for op in ['+', '-', '*', '/', '&&', '||', '?', ':']):
                                return 0.0
            
            return 1.0
            
        except Exception as e:
            print(f"Syntax check failed: {str(e)}")
            return 0.0
    
    @staticmethod
    def _calculate_bleu(source: str, target: str) -> float:
        """Calculate BLEU score between source and target code.
        
        Args:
            source (str): Source code
            target (str): Target code
            
        Returns:
            float: BLEU score between 0 and 1
        """
        def tokenize(code: str) -> List[str]:
            # Tokenize code into words, operators, and punctuation
            return [t for t in re.findall(r'\w+|[^\w\s]', code) if t.strip()]
        
        # Tokenize source and target
        source_tokens = tokenize(source)
        target_tokens = tokenize(target)
        
        if not source_tokens or not target_tokens:
            return 0.0
        
        # Calculate n-gram matches
        max_n = min(4, len(source_tokens), len(target_tokens))
        if max_n == 0:
            return 0.0
            
        matches = [0] * max_n
        totals = [0] * max_n
        
        for n in range(1, max_n + 1):
            source_ngrams = CodeEvaluator._get_ngrams(source_tokens, n)
            target_ngrams = CodeEvaluator._get_ngrams(target_tokens, n)
            
            matches[n-1] = sum(min(source_ngrams.get(ng, 0), target_ngrams.get(ng, 0))
                             for ng in set(source_ngrams) | set(target_ngrams))
            totals[n-1] = sum(target_ngrams.values())
        
        # Calculate geometric mean of n-gram scores
        if not any(totals):
            return 0.0
            
        scores = []
        for m, t in zip(matches, totals):
            if t == 0:
                scores.append(0.0)
            else:
                scores.append(m/t)
        
        if not any(scores):
            return 0.0
            
        # Use arithmetic mean instead of geometric mean for more intuitive results
        score = sum(scores) / len(scores)
        
        # Apply brevity penalty
        bp = 1.0
        if len(target_tokens) < len(source_tokens):
            bp = math.exp(1 - len(source_tokens)/len(target_tokens))
        
        return bp * score
    
    @staticmethod
    def _get_ngrams(tokens: List[str], n: int) -> Dict[str, int]:
        """Get n-grams from a list of tokens.
        
        Args:
            tokens (List[str]): List of tokens
            n (int): Size of n-grams
            
        Returns:
            Dict[str, int]: Dictionary mapping n-grams to their counts
        """
        ngrams = {}
        for i in range(len(tokens) - n + 1):
            ng = ' '.join(tokens[i:i+n])
            ngrams[ng] = ngrams.get(ng, 0) + 1
        return ngrams
    
    @staticmethod
    def _calculate_structural_similarity(source: str, target: str) -> float:
        """Calculate structural similarity between source and target code.
        
        Args:
            source (str): Source code
            target (str): Target code
            
        Returns:
            float: Similarity score between 0 and 1
        """
        try:
            # Extract structural elements
            source_struct = CodeEvaluator._extract_structure(source)
            target_struct = CodeEvaluator._extract_structure(target)
            
            # Calculate Jaccard similarity
            intersection = len(set(source_struct) & set(target_struct))
            union = len(set(source_struct) | set(target_struct))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0
    
    @staticmethod
    def _extract_structure(code: str) -> List[str]:
        """Extract structural elements from code.
        
        Args:
            code (str): Code to analyze
            
        Returns:
            List[str]: List of structural elements
        """
        # Remove comments and string literals
        code = re.sub(r'#.*$|//.*$|/\*.*?\*/|\'.*?\'|".*?"', '', code, flags=re.M|re.S)
        
        # Extract structural elements
        elements = []
        
        # Function/method definitions
        elements.extend(re.findall(r'(def|function)\s+\w+', code))
        
        # Class definitions
        elements.extend(re.findall(r'class\s+\w+', code))
        
        # Control structures
        elements.extend(re.findall(r'(if|else|elif|for|while|try|catch|except)\s*\(', code))
        
        # Variable declarations
        elements.extend(re.findall(r'(var|let|const|int|float|double|string)\s+\w+', code))
        
        return elements
