"""Language support and configuration for code translation."""

from typing import Dict, List, Set
import re

class LanguageConfig:
    """Configuration for supported programming languages."""
    
    # Language specific tokens and patterns
    LANGUAGE_PATTERNS = {
        'python': {
            'indent': '    ',
            'line_end': '\n',
            'block_start': ':',
            'block_end': None,  # Python uses indentation
            'comment_single': '#',
            'comment_multi_start': '"""',
            'comment_multi_end': '"""',
            'function_def': 'def',
            'class_def': 'class',
            'indent_triggers': {':', 'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except'},
            'dedent_triggers': {'return', 'break', 'continue', 'pass', 'raise'},
            'keywords': {'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'return', 'import', 'from'},
        },
        'java': {
            'indent': '    ',
            'line_end': ';\n',
            'block_start': '{',
            'block_end': '}',
            'comment_single': '//',
            'comment_multi_start': '/*',
            'comment_multi_end': '*/',
            'function_def': 'public|private|protected',
            'class_def': 'class',
            'indent_triggers': {'{'},
            'dedent_triggers': {'}'},
            'keywords': {'public', 'private', 'protected', 'class', 'interface', 'if', 'else', 'for', 'while', 'try', 'catch', 'return', 'import'},
        },
        'cpp': {
            'indent': '    ',
            'line_end': ';\n',
            'block_start': '{',
            'block_end': '}',
            'comment_single': '//',
            'comment_multi_start': '/*',
            'comment_multi_end': '*/',
            'function_def': '',
            'class_def': 'class',
            'indent_triggers': {'{'},
            'dedent_triggers': {'}'},
            'keywords': {'class', 'struct', 'if', 'else', 'for', 'while', 'try', 'catch', 'return', 'include'},
        },
        'javascript': {
            'indent': '    ',
            'line_end': ';\n',
            'block_start': '{',
            'block_end': '}',
            'comment_single': '//',
            'comment_multi_start': '/*',
            'comment_multi_end': '*/',
            'function_def': 'function',
            'class_def': 'class',
            'indent_triggers': {'{'},
            'dedent_triggers': {'}'},
            'keywords': {'function', 'class', 'if', 'else', 'for', 'while', 'try', 'catch', 'return', 'import', 'export'},
        },
        'csharp': {
            'indent': '    ',
            'line_end': ';\n',
            'block_start': '{',
            'block_end': '}',
            'comment_single': '//',
            'comment_multi_start': '/*',
            'comment_multi_end': '*/',
            'function_def': 'public|private|protected',
            'class_def': 'class',
            'indent_triggers': {'{'},
            'dedent_triggers': {'}'},
            'keywords': {'public', 'private', 'protected', 'class', 'interface', 'if', 'else', 'for', 'while', 'try', 'catch', 'return', 'using'},
        }
    }
    
    @classmethod
    def get_supported_languages(cls) -> Set[str]:
        """Get set of supported programming languages."""
        return set(cls.LANGUAGE_PATTERNS.keys())
    
    @classmethod
    def get_language_pattern(cls, language: str) -> Dict:
        """Get patterns for a specific language."""
        if language not in cls.LANGUAGE_PATTERNS:
            raise ValueError(f"Language {language} not supported")
        return cls.LANGUAGE_PATTERNS[language]
    
    @classmethod
    def format_code(cls, code: str, language: str) -> str:
        """Format code according to language conventions."""
        if not code.strip():
            return ""
            
        patterns = cls.get_language_pattern(language)
        
        # Basic formatting
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0
        
        # Split code by braces for C-style languages
        if language in ['java', 'cpp', 'javascript', 'csharp']:
            # Add spaces around braces and split by semicolons
            code = re.sub(r'([{}])', r' \1 ', code)
            code = re.sub(r';', ';\n', code)
            # Split by braces while preserving them
            code = re.sub(r'([{}])', r'\1\n', code)
            lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
                continue
                
            # Handle dedentation
            if language == 'python':
                # Python uses semantic indentation
                if any(stripped.startswith(trigger) for trigger in patterns['dedent_triggers']):
                    indent_level = max(0, indent_level - 1)
            else:
                # Other languages use braces
                if patterns['block_end'] and stripped.startswith(patterns['block_end']):
                    indent_level = max(0, indent_level - 1)
            
            # Add the line with proper indentation
            formatted_lines.append(patterns['indent'] * indent_level + stripped)
            
            # Handle indentation for next line
            if language == 'python':
                # Python uses semantic indentation
                if any(stripped.endswith(trigger) for trigger in patterns['indent_triggers']):
                    indent_level += 1
            else:
                # Other languages use braces
                if patterns['block_start'] and stripped.endswith(patterns['block_start']):
                    indent_level += 1
        
        # Join lines and ensure proper line endings
        result = '\n'.join(formatted_lines)
        
        # Add semicolons for languages that require them
        if patterns['line_end'].strip():
            lines = result.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.endswith(patterns['line_end'].strip()):
                    if not any(stripped.endswith(x) for x in ['{', '}', ':', ';']):
                        lines[i] = line + patterns['line_end'].strip()
            result = '\n'.join(lines)
        
        return result
    
    @classmethod
    def add_language_tokens(cls, code: str, language: str) -> str:
        """Add language-specific tokens to code."""
        return f"<{language}> {code} </{language}>"
    
    @classmethod
    def extract_functions(cls, code: str, language: str) -> List[str]:
        """Extract function definitions from code."""
        patterns = cls.get_language_pattern(language)
        function_pattern = patterns['function_def']
        
        if not function_pattern:
            return []
            
        # Create regex pattern based on language
        if language in ['java', 'csharp']:
            pattern = rf"({function_pattern})\s+[\w<>[\],\s]+\s+(\w+)\s*\([^)]*\)\s*{patterns['block_start']}"
        elif language == 'python':
            pattern = r"def\s+(\w+)\s*\([^)]*\)\s*:"
        elif language == 'javascript':
            pattern = r"(function\s+(\w+)|const\s+(\w+)\s*=\s*function|\(\s*\)\s*=>)\s*{?"
        else:
            pattern = rf"\w+\s+(\w+)\s*\([^)]*\)\s*{patterns['block_start']}"
            
        return re.findall(pattern, code)
