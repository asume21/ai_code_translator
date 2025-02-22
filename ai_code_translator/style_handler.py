"""Style handler for preserving code formatting and conventions during translation."""

import re
from typing import Dict, List, Optional, Tuple, Set
import black
import isort
import autopep8
import jsbeautifier as js_beautify
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class StyleConfig:
    """Configuration for code style preferences."""
    indent_size: int = 4
    max_line_length: int = 80
    quote_style: str = "double"  # 'single' or 'double'
    naming_convention: str = "snake_case"  # 'snake_case', 'camelCase', 'PascalCase'
    bracket_style: str = "same_line"  # 'same_line' or 'new_line'

class StyleHandler:
    """Handles code style preservation during translation."""
    
    def __init__(self, config: Optional[StyleConfig] = None):
        self.config = config or StyleConfig()
    
    def preserve_style(self, source_code: str, target_code: str,
                      source_lang: str, target_lang: str) -> str:
        """Preserve code style during translation."""
        # Extract style characteristics from source code
        source_style = self._extract_style_characteristics(source_code)
        
        # Override with config settings if provided
        if self.config:
            source_style['indent_size'] = self.config.indent_size
            source_style['quote_style'] = self.config.quote_style
            source_style['naming_style'] = self.config.naming_convention
        
        # Format the target code based on the source style
        formatted_code = self._format_code(target_code, target_lang, source_style)
        
        # Apply naming conventions
        formatted_code = self._apply_naming_convention(formatted_code, source_style['naming_style'])
        
        # Apply indentation
        formatted_code = self._apply_indentation(formatted_code, source_style['indent_size'])
        
        # Apply quote style
        formatted_code = self._apply_quote_style(formatted_code, source_style['quote_style'])
        
        return formatted_code
    
    def _extract_style_characteristics(self, code: str) -> Dict[str, any]:
        """Extract style characteristics from code."""
        chars = {
            'indent_size': self._detect_indentation(code),
            'quote_style': self._detect_quote_style(code),
            'naming_style': self._detect_naming_convention(code),
            'max_line_length': self._detect_max_line_length(code),
            'bracket_style': self._detect_bracket_style(code)
        }
        return chars
    
    def _format_code(self, code: str, lang: str, style: Dict[str, any]) -> str:
        """Format code according to style characteristics."""
        if lang.lower() == 'python':
            return self._format_python(code, style)
        elif lang.lower() in ['javascript', 'typescript']:
            return self._format_javascript(code, style)
        else:
            logger.warning(f"No specific formatter for language: {lang}")
            return code
    
    def _format_python(self, code: str, style: Optional[Dict[str, any]] = None) -> str:
        """Format Python code."""
        style = style or {}
        
        # Apply autopep8 for basic formatting
        code = autopep8.fix_code(code, options={
            'max_line_length': style.get('max_line_length', 80)
        })
        
        try:
            # Configure black with the correct line length
            mode = black.FileMode(line_length=style.get('max_line_length', 88))
            code = black.format_str(code, mode=mode)
        except Exception as e:
            logger.warning(f"Black formatting failed: {e}")
        
        # Sort imports
        try:
            code = isort.code(code)
        except Exception as e:
            logger.warning(f"Import sorting failed: {e}")
        
        return code
    
    def _format_javascript(self, code: str, style: Optional[Dict[str, any]] = None) -> str:
        """Format JavaScript code."""
        style = style or {}
        
        opts = {
            'indent_size': style.get('indent_size', 4),
            'max_preserve_newlines': 2,
            'preserve_newlines': True,
            'keep_array_indentation': True,
            'break_chained_methods': False,
            'indent_scripts': 'normal',
            'space_before_conditional': True,
            'unescape_strings': False,
            'jslint_happy': False,
            'end_with_newline': True,
            'wrap_line_length': style.get('max_line_length', 80),
            'indent_inner_html': False,
            'comma_first': False,
            'e4x': False
        }
        
        try:
            return js_beautify.beautify(code, opts)
        except Exception as e:
            logger.warning(f"JavaScript formatting failed: {e}")
            return code
    
    def _detect_indentation(self, code: str) -> int:
        """Detect indentation size from code."""
        lines = code.split('\n')
        indents = []
        
        for line in lines:
            if line.strip():
                # Count leading spaces
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    indents.append(indent)
        
        if not indents:
            return self.config.indent_size
        
        # Return most common indentation
        return max(set(indents), key=indents.count)
    
    def _detect_quote_style(self, code: str) -> str:
        """Detect quote style from code."""
        # Count string literals with single and double quotes
        single_quotes = len(re.findall(r"(?<!\\)'[^'\\]*(?:\\.[^'\\]*)*'", code))
        double_quotes = len(re.findall(r'(?<!\\)"[^"\\]*(?:\\.[^"\\]*)*"', code))
        
        # Check if there are any quotes at all
        if not single_quotes and not double_quotes:
            return self.config.quote_style
        
        return 'single' if single_quotes > double_quotes else 'double'
    
    def _detect_naming_convention(self, code: str) -> str:
        """Detect naming convention from code."""
        # Look for variable and function names
        names = re.findall(r'\b[a-zA-Z_]\w*\b', code)
        
        # Filter out language keywords and built-ins
        keywords = {'def', 'class', 'if', 'else', 'while', 'for', 'try', 'except', 'return', 'import', 'from',
                   'function', 'var', 'let', 'const', 'new', 'this', 'super', 'extends', 'constructor'}
        names = [name for name in names if name not in keywords and not name.startswith('__')]
        
        if not names:
            return self.config.naming_convention
        
        # Count occurrences of each naming convention
        snake_case = 0
        camel_case = 0
        pascal_case = 0
        
        for name in names:
            if '_' in name and name.islower():
                snake_case += 1
            elif name[0].isupper() and not '_' in name:
                pascal_case += 1
            elif name[0].islower() and not '_' in name and any(c.isupper() for c in name[1:]):
                camel_case += 2  # Give extra weight to camelCase in JavaScript
            elif name.islower():
                snake_case += 1
            elif name.isupper():
                snake_case += 1
        
        # Return the most common convention
        counts = {
            'snake_case': snake_case,
            'camelCase': camel_case,
            'PascalCase': pascal_case
        }
        
        return max(counts.items(), key=lambda x: x[1])[0]
    
    def _detect_max_line_length(self, code: str) -> int:
        """Detect maximum line length from code."""
        lines = code.split('\n')
        if not lines:
            return self.config.max_line_length
        
        lengths = [len(line) for line in lines if line.strip()]
        if not lengths:
            return self.config.max_line_length
        
        # Use 90th percentile to avoid outliers
        sorted_lengths = sorted(lengths)
        idx = int(len(sorted_lengths) * 0.9)
        return sorted_lengths[idx]
    
    def _detect_bracket_style(self, code: str) -> str:
        """Detect bracket style from code."""
        # Look for opening braces
        same_line = len(re.findall(r'\)\s*{', code))
        new_line = len(re.findall(r'\)\s*\n\s*{', code))
        
        return 'same_line' if same_line >= new_line else 'new_line'
    
    def _apply_indentation(self, code: str, size: int) -> str:
        """Apply indentation to code."""
        lines = code.split('\n')
        result = []
        
        # First pass: detect base indentation from first non-empty line
        base_indent = None
        for line in lines:
            if line.strip():
                base_indent = len(line) - len(line.lstrip())
                break
        
        if base_indent is None:
            base_indent = 0
        
        # Second pass: apply indentation
        for line in lines:
            if not line.strip():
                result.append(line)
                continue
            
            # Count leading spaces in original line
            original_indent = len(line) - len(line.lstrip())
            
            # Calculate new indentation
            if original_indent >= base_indent:
                # Convert original indentation to new size
                indent_level = (original_indent - base_indent) // 4  # Assume original indent was 4 spaces
                new_indent = ' ' * (base_indent + indent_level * size)
                result.append(new_indent + line.lstrip())
            else:
                # Line has less indentation than base, preserve it
                result.append(' ' * original_indent + line.lstrip())
        
        return '\n'.join(result)
    
    def _apply_naming_convention(self, code: str, convention: str) -> str:
        """Apply naming convention to identifiers."""
        if convention not in ["snake_case", "camelCase", "PascalCase"]:
            return code
        
        def to_snake_case(name):
            # Convert camelCase or PascalCase to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        
        def to_camel_case(name):
            # Convert snake_case or PascalCase to camelCase
            if '_' in name:
                components = name.split('_')
                return components[0].lower() + ''.join(x.title() for x in components[1:])
            else:
                # Handle PascalCase
                if name and name[0].isupper():
                    return name[0].lower() + name[1:]
                return name
        
        def to_pascal_case(name):
            # Convert snake_case or camelCase to PascalCase
            if '_' in name:
                components = name.split('_')
            else:
                # Handle camelCase
                s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
                s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
                components = s2.lower().split('_')
            return ''.join(x.title() for x in components)
        
        # Don't convert class names if they're already in PascalCase
        def should_convert_name(name, match_type):
            if match_type == "class" and name[0].isupper() and any(c.islower() for c in name[1:]):
                return False
            return True
        
        # Convert identifiers based on the target convention
        if convention == "snake_case":
            # Handle class names (keep PascalCase)
            code = re.sub(r'class\s+([A-Za-z][A-Za-z0-9_]*)', 
                         lambda m: f'class {m.group(1)}' if not should_convert_name(m.group(1), "class") 
                         else f'class {to_snake_case(m.group(1))}', code)
            
            # Handle function parameters and variable names
            code = re.sub(r'\b([A-Za-z][A-Za-z0-9_]*)\b(?![({])', 
                         lambda m: to_snake_case(m.group(1)), code)
            
        elif convention == "camelCase":
            # Handle class names (keep PascalCase)
            code = re.sub(r'class\s+([A-Za-z][A-Za-z0-9_]*)', 
                         lambda m: f'class {m.group(1)}' if not should_convert_name(m.group(1), "class")
                         else f'class {to_pascal_case(m.group(1))}', code)
            
            # Handle function parameters and variable names
            code = re.sub(r'\b([A-Za-z][A-Za-z0-9_]*)\b(?![({])', 
                         lambda m: to_camel_case(m.group(1)) if not m.group(1)[0].isupper() 
                         else m.group(1), code)
            
        elif convention == "PascalCase":
            # Convert all identifiers to PascalCase except for function parameters
            code = re.sub(r'\b([A-Za-z][A-Za-z0-9_]*)\b(?=\s*[({])', 
                         lambda m: to_pascal_case(m.group(1)), code)
        
        return code
    
    def _apply_quote_style(self, code: str, quote_style: str) -> str:
        """Apply the specified quote style to string literals."""
        if quote_style not in ["single", "double"]:
            return code
        
        def replace_quotes(match):
            content = match.group(1)
            quote = "'" if quote_style == "single" else '"'
            # Escape any quotes of the same type in the content
            content = content.replace(quote, '\\' + quote)
            # Unescape the other type of quotes
            other_quote = '"' if quote == "'" else "'"
            content = content.replace('\\' + other_quote, other_quote)
            return f"{quote}{content}{quote}"
        
        # Handle string literals
        patterns = [
            r'"([^"\\]*(?:\\.[^"\\]*)*)"',  # Double quoted strings
            r"'([^'\\]*(?:\\.[^'\\]*)*)'",  # Single quoted strings
            r"`([^`\\]*(?:\\.[^`\\]*)*)`",  # Template literals
        ]
        
        # First convert all quotes to the target style
        for pattern in patterns:
            code = re.sub(pattern, replace_quotes, code)
        
        # Handle string literals in comments
        if quote_style == "single":
            code = re.sub(r'//\s*"([^"]*)"', r"// '\1'", code)
            code = re.sub(r'/\*\s*"([^"]*)"', r"/* '\1'", code)
        else:
            code = re.sub(r"//\s*'([^']*)'", r'// "\1"', code)
            code = re.sub(r"/\*\s*'([^']*)'", r'/* "\1"', code)
        
        # Add quotes to strings in comments that don't have them
        code = re.sub(r'(//\s*)([^"\']+)$', 
                     lambda m: f"{m.group(1)}'{m.group(2)}'" if quote_style == "single" else f'{m.group(1)}"{m.group(2)}"', 
                     code, flags=re.MULTILINE)
        
        return code
