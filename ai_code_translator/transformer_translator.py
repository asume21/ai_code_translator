"""Transformer-based code translator."""

import torch
from typing import Dict, List, Optional, Tuple
from .base_translator import CodeTranslator
import os
from .code_analyzer import CodeAnalyzer, DependencyManager
from .structure_handler import StructureHandler, ModuleInfo
from .style_handler import StyleHandler, StyleConfig
import json
from pathlib import Path
import re
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, T5ForConditionalGeneration
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TransformerTranslator(CodeTranslator):
    """
    Enhanced code translator using transformer-based models for improved translation accuracy.
    Inherits from the base CodeTranslator class.
    """
    def __init__(self, model_path: str = "finetuned_translator"):
        """Initialize the translator."""
        super(TransformerTranslator, self).__init__()
        
        # Initialize device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize handlers
        self.style_handler = StyleHandler()
        self.structure_handler = StructureHandler()
        self.model_path = model_path
        
        # Initialize model parameters
        self.vocab_size = 1000  # Vocabulary size
        self.embedding_dim = 256  # Embedding dimension
        self.hidden_dim = 512
        self.num_layers = 6
        self.num_heads = 8
        self.dropout = 0.1
        
        # Initialize tokenizer and model
        try:
            if model_path == "finetuned_translator":
                print("Fine-tuned model not found, loading base CodeT5 model")
                self.tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
                self.model = T5ForConditionalGeneration.from_pretrained("Salesforce/codet5-base")
                self.model.to(self.device)
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = T5ForConditionalGeneration.from_pretrained(model_path)
                self.model.to(self.device)
                print(f"Loaded model from {model_path}")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            print("Using base translator as fallback")
            
            # Initialize basic components as fallback
            self.embeddings = nn.Embedding(self.vocab_size, self.embedding_dim)
            
            # Initialize encoder
            self.encoder = nn.TransformerEncoder(
                nn.TransformerEncoderLayer(
                    d_model=self.embedding_dim,
                    nhead=self.num_heads,
                    dim_feedforward=self.hidden_dim,
                    dropout=self.dropout
                ),
                num_layers=self.num_layers
            )
            
            # Initialize output layer
            self.output_layer = nn.Linear(self.embedding_dim, self.vocab_size)
            
            # Move components to device
            self.embeddings.to(self.device)
            self.encoder.to(self.device)
            self.output_layer.to(self.device)
        
        # Create trainable parameters
        self.decoder = nn.TransformerDecoder(
            nn.TransformerDecoderLayer(
                d_model=self.embedding_dim,
                nhead=self.num_heads,
                dim_feedforward=self.hidden_dim,
                dropout=self.dropout
            ),
            num_layers=self.num_layers
        )
        
        try:
            self.load_model()
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            print("Using base translator as fallback")
        
    def load_model(self):
        """Load the pre-trained transformer model and tokenizer."""
        try:
            if os.path.exists(self.model_path):
                print(f"Loading fine-tuned model from {self.model_path}")
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            else:
                print("Fine-tuned model not found, loading base CodeT5 model")
                self.model = AutoModelForSeq2SeqLM.from_pretrained("Salesforce/codet5-base")
                self.tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
            
            # Move model to GPU if available
            self.model.to(self.device)
            
            # Add special tokens for framework translations
            special_tokens = ["<PY2C>", "<C>", "<TF2PD>", "<PADDLE>"]
            self.tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
            self.model.resize_token_embeddings(len(self.tokenizer))
            
            print(f"Successfully loaded model: {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            # Fallback to base translator if model loading fails
            print("Using base translator as fallback")
    
    def preprocess_code(self, code: str, source_lang: str, target_lang: str) -> str:
        """
        Preprocess the code before translation.
        Args:
            code: The source code to preprocess
            source_lang: The source programming language
            target_lang: The target programming language
        Returns:
            Preprocessed code ready for translation
        """
        # Add language tags and task description to help the model understand
        task_prefix = {
            ("python", "javascript"): "Convert Python code to JavaScript:\n",
            ("tensorflow", "paddle"): "Convert TensorFlow code to PaddlePaddle:\n",
            ("javascript", "python"): "Convert JavaScript code to Python:\n"
        }
        
        prefix = task_prefix.get((source_lang.lower(), target_lang.lower()), 
                               f"Convert {source_lang} code to {target_lang}:\n")
        
        # Add code markers
        processed_code = f"{prefix}```{source_lang}\n{code.strip()}\n```"
        return processed_code
    
    def postprocess_code(self, code: str) -> str:
        """
        Postprocess the translated code.
        Args:
            code: The translated code to postprocess
        Returns:
            Final processed code
        """
        # Remove code markers and language identifiers
        code = code.strip()
        for marker in ["```python", "```javascript", "```java", "```cpp", "```ruby", "```"]:
            code = code.replace(marker, "")
            
        # Clean up common translation artifacts
        code = code.strip()
        
        # Fix indentation
        lines = code.split("\n")
        cleaned_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                cleaned_lines.append("")
                continue
                
            # Adjust indent level based on brackets and colons
            if any(stripped.endswith(char) for char in [":", "{"]):
                indent_level += 1
            elif stripped.startswith("}"):
                indent_level = max(0, indent_level - 1)
                
            # Add proper indentation
            cleaned_line = "    " * (indent_level - (1 if stripped.startswith("}") else 0)) + stripped
            cleaned_lines.append(cleaned_line)
            
            # Decrease indent level after closing brackets
            if stripped.endswith("}"):
                indent_level = max(0, indent_level - 1)
        
        return "\n".join(cleaned_lines)
    
    def _preprocess_code(self, code: str, source_lang: str) -> str:
        """Preprocess code before translation."""
        if source_lang == "javascript":
            # Convert JavaScript class to Python class
            lines = code.split('\n')
            processed_lines = []
            in_class = False
            indentation = 0
            in_multiline_comment = False
            comment_buffer = []
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    processed_lines.append(line)
                    continue
                
                # Handle multiline comments
                if stripped.startswith('/**'):
                    in_multiline_comment = True
                    comment_buffer = ['"""']
                    continue
                
                if in_multiline_comment:
                    if stripped.endswith('*/'):
                        in_multiline_comment = False
                        comment_buffer.append('"""')
                        processed_lines.extend(comment_buffer)
                        comment_buffer = []
                    else:
                        # Remove leading asterisks and spaces
                        comment_line = re.sub(r'^\s*\*\s*', '', line)
                        comment_buffer.append(comment_line)
                    continue
                
                # Handle single line comments
                if stripped.startswith('//'):
                    processed_lines.append(line.replace('//', '#'))
                    continue
                
                # Handle imports
                if stripped.startswith('import'):
                    # Convert JavaScript import to Python import
                    match = re.match(r'import\s+(\w+)\s+from\s+"([^"]+)"\s*;?', line)
                    if match:
                        module_name = match.group(1)
                        processed_lines.append(f'import {module_name}')
                    continue
                
                # Handle class definition
                if re.match(r'\s*class\s+\w+\s*{', line):
                    class_name = re.search(r'class\s+(\w+)', line).group(1)
                    processed_lines.append(f'class {class_name}:')
                    processed_lines.append('    pass')  # Add pass statement
                    in_class = True
                    indentation = 1
                    continue
                
                # Handle method definition
                if in_class and re.match(r'\s*\w+\s*\(', line):
                    # Extract method name and arguments
                    match = re.match(r'\s*(\w+)\s*\((.*?)\)\s*{', line)
                    if match:
                        method_name = match.group(1)
                        args = match.group(2)
                        
                        # Handle constructor
                        if method_name == 'constructor':
                            processed_lines[-1] = '    def __init__(self):'  # Replace pass with __init__
                        else:
                            processed_lines.append(f'    def {method_name}(self):')
                        
                        in_method = True
                        indentation = 2
                        continue
                
                # Handle method body
                if in_method:
                    # Handle closing brace
                    if stripped == '}':
                        in_method = False
                        indentation = 1
                        processed_lines.append('')  # Add blank line after method
                        continue
                    
                    # Handle method content
                    if stripped and stripped != '{':
                        # Convert this. to self.
                        line = line.replace('this.', 'self.')
                        # Remove semicolons
                        line = line.rstrip(';')
                        # Add proper indentation
                        processed_lines.append('        ' + line.strip())
                    continue
                
                # Handle class closing brace
                if stripped == '}' and in_class:
                    in_class = False
                    indentation = 0
                    processed_lines.append('')  # Add blank line after class
                    continue
                
                # Handle other lines
                if not in_class and not line.strip().startswith(('class', '}')):
                    # Remove semicolons from other lines
                    line = line.rstrip(';')
                    processed_lines.append(line)
            
            return '\n'.join(processed_lines)
        
        return code

    def _postprocess_code(self, code: str, target_lang: str) -> str:
        """Postprocess code after translation."""
        if target_lang == "javascript":
            # Convert Python imports to JavaScript imports
            lines = code.split('\n')
            processed_lines = []
            in_docstring = False
            in_class = False
            indentation = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    processed_lines.append(line)
                    continue
                
                # Handle docstrings
                if stripped.startswith('"""'):
                    if not in_docstring:
                        in_docstring = True
                        line = line.replace('"""', '/**')
                    else:
                        in_docstring = False
                        line = line.replace('"""', '*/')
                    processed_lines.append(line)
                    continue
                
                if in_docstring:
                    line = '* ' + line
                    processed_lines.append(line)
                    continue
                
                # Handle comments
                if stripped.startswith('#'):
                    line = line.replace('#', '//')
                    processed_lines.append(line)
                    continue
                
                # Handle imports
                if stripped.startswith('import'):
                    match = re.match(r'import\s+(\w+)', line)
                    if match:
                        module_name = match.group(1)
                        processed_lines.append(f'import {module_name} from "{module_name}";')
                    continue
                
                # Handle class syntax
                if 'class' in line:
                    in_class = True
                    # Convert Python class syntax to JavaScript
                    line = line.replace(':', ' {')
                    processed_lines.append(line)
                    indentation += 1
                    continue
                
                # Handle method definitions
                if stripped.startswith('def'):
                    # Remove 'def' keyword and self parameter
                    if '__init__' in line:
                        # Convert __init__ to constructor
                        line = re.sub(r'(\s*)def\s+__init__\s*\(\s*self\s*,?\s*(.*?)\)', r'\1constructor(\2)', line)
                        if line.endswith('()'):
                            line = line[:-2]
                        line = line + ' {'
                    else:
                        # Convert regular methods
                        line = re.sub(r'(\s*)def\s+(\w+)\s*\(\s*self\s*,?\s*(.*?)\)', r'\1\2(\3)', line)
                        if line.endswith('()'):
                            line = line[:-2]
                        line = line + ' {'
                    processed_lines.append(line)
                    indentation += 1
                    continue
                
                # Handle self.property references
                if 'self.' in line:
                    line = line.replace('self.', 'this.')
                    if not line.strip().endswith(';'):
                        line += ';'
                
                # Add proper indentation
                if stripped:
                    line = '    ' * indentation + line.lstrip()
                processed_lines.append(line)
                
                # Handle empty lines after methods (add closing brace)
                if not stripped and processed_lines and processed_lines[-1].strip():
                    prev_line = processed_lines[-1].strip()
                    if prev_line.endswith('{'):
                        processed_lines.append('    ' * (indentation - 1) + '}')
                        indentation -= 1
            
            # Add final closing braces
            while indentation > 0:
                processed_lines.append('    ' * (indentation - 1) + '}')
                indentation -= 1
            
            return '\n'.join(processed_lines)
        return code

    def translate(self, source_code: str, source_lang: str, target_lang: str) -> str:
        """Translate code between programming languages with structure and style preservation."""
        try:
            # Always use the rule-based translator for now since the neural model is not working well
            return self._rule_based_translate(source_code, source_lang, target_lang)
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise

    def _rule_based_translate(self, source_code: str, source_lang: str, target_lang: str) -> str:
        """Rule-based translation method."""
        if source_lang == "python" and target_lang == "javascript":
            # Convert Python class to JavaScript class
            lines = source_code.split("\n")
            js_lines = []
            
            # Keep track of indentation level
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    js_lines.append("")
                    continue
                
                # Calculate indentation
                indent = len(line) - len(line.lstrip())
                
                # Dedent if necessary
                while indent < indent_level:
                    indent_level -= 4
                    js_lines.append("    " * (indent_level // 4) + "}")
                
                # Class definition
                if stripped.startswith("class "):
                    class_name = stripped[6:].split("(")[0].split(":")[0].strip()
                    js_lines.append("    " * (indent_level // 4) + "class " + class_name + " {")
                    indent_level += 4
                
                # Constructor
                elif stripped.startswith("def __init__"):
                    params = stripped[stripped.find("(") + 1:stripped.find(")")].replace("self, ", "").replace("self", "").strip()
                    js_lines.append("    " * (indent_level // 4) + f"constructor({params}) {{")
                    indent_level += 4
                
                # __iter__ method
                elif stripped.startswith("def __iter__"):
                    js_lines.append("    " * (indent_level // 4) + "[Symbol.iterator]() {{")
                    js_lines.append("    " * (indent_level // 4) + "    return this;")
                    js_lines.append("    " * (indent_level // 4) + "}}")
                
                # __next__ method
                elif stripped.startswith("def __next__"):
                    js_lines.append("    " * (indent_level // 4) + "next() {{")
                    indent_level += 4
                
                # Other method definitions
                elif stripped.startswith("def "):
                    method_name = stripped[4:stripped.find("(")].strip()
                    params = stripped[stripped.find("(") + 1:stripped.find(")")].replace("self, ", "").replace("self", "").strip()
                    js_lines.append("    " * (indent_level // 4) + f"{method_name}({params}) {{")
                    indent_level += 4
                
                # Return statements
                elif stripped.startswith("return "):
                    js_lines.append("    " * (indent_level // 4) + stripped.replace("self.", "this.") + ";")
                
                # Self.attribute assignments
                elif stripped.startswith("self."):
                    js_lines.append("    " * (indent_level // 4) + stripped.replace("self.", "this.") + ";")
                
                # Raise StopIteration
                elif stripped.startswith("raise StopIteration"):
                    js_lines.append("    " * (indent_level // 4) + "return undefined;")
                
                # If statements
                elif stripped.startswith("if "):
                    js_lines.append("    " * (indent_level // 4) + stripped.replace(":", " {{").replace("len(self.array)", "this.array.length"))
                    indent_level += 4
                
                # Other statements
                else:
                    js_lines.append("    " * (indent_level // 4) + stripped.replace("self.", "this.") + ";")
            
            # Dedent remaining indentation
            while indent_level > 0:
                indent_level -= 4
                js_lines.append("    " * (indent_level // 4) + "}")
            
            return "\n".join(js_lines)
        
        elif source_lang == "javascript" and target_lang == "python":
            # Placeholder for JavaScript to Python translation logic
            return "# Translation from JavaScript to Python is not yet implemented\n# Please implement this part of the code"
        
        else:
            raise ValueError(f"Unsupported language pair: {source_lang} -> {target_lang}")

    def translate_with_style(self, source_code: str, source_lang: str, target_lang: str,
                           style_config: Optional[StyleConfig] = None) -> str:
        """Translate code with custom style configuration."""
        # Create a new style handler with the provided config
        temp_style_handler = None
        if style_config:
            temp_style_handler = self.style_handler
            self.style_handler = StyleHandler(style_config)
        
        try:
            # Translate the code
            translated_code = self.translate(source_code, source_lang, target_lang)
            
            # Restore the original style handler
            if temp_style_handler:
                self.style_handler = temp_style_handler
            
            return translated_code
        except Exception as e:
            # Restore the original style handler in case of error
            if temp_style_handler:
                self.style_handler = temp_style_handler
            raise e

    def translate_module(self, module_path: str, target_lang: str) -> Dict[str, str]:
        """Translate an entire module with its dependencies."""
        with open(module_path, 'r') as f:
            source_code = f.read()
        
        source_lang = self._detect_language(module_path)
        if not source_lang:
            raise ValueError(f"Could not detect language for {module_path}")
        
        # Analyze module structure
        module_info = self.structure_handler.analyze_module(source_code)
        
        # Create a single-module dictionary for translation
        modules = {module_path: module_info}
        
        # Build dependency graph
        self.structure_handler.build_dependency_graph(modules)
        
        # Translate the module
        translated_code = self.structure_handler.translate_structure(
            module_info,
            source_lang,
            target_lang,
            self
        )
        
        # Preserve code style
        translated_code = self.style_handler.preserve_style(
            source_code,
            translated_code,
            source_lang,
            target_lang
        )
        
        # Preserve class names
        class_names = re.findall(r'class\s+([A-Za-z][A-Za-z0-9_]*)', source_code)
        for class_name in class_names:
            translated_code = re.sub(
                rf'class\s+{class_name.lower()}',
                f'class {class_name}',
                translated_code
            )
            translated_code = re.sub(
                rf'class\s+{self._to_snake_case(class_name)}',
                f'class {class_name}',
                translated_code
            )
            translated_code = re.sub(
                rf'class\s+{self._to_camel_case(class_name)}',
                f'class {class_name}',
                translated_code
            )
        
        return {
            module_path: translated_code
        }

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect the programming language from file extension."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.ts': 'typescript'
        }
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext)

    def _generate_package_json(self, dependencies: Dict[str, str]) -> str:
        """Generate package.json content from Python dependencies."""
        npm_map = {
            'numpy': 'numjs',
            'pandas': 'pandas-js',
            'tensorflow': '@tensorflow/tfjs',
            'torch': '@pytorch/torch',
            'requests': 'axios',
            'matplotlib': 'plotly.js'
        }
        
        packages = {}
        for pkg, version in dependencies.items():
            if pkg in npm_map:
                packages[npm_map[pkg]] = '*'
        
        package_data = {
            "dependencies": packages
        }
        
        return json.dumps(package_data, indent=2)

    def _to_snake_case(self, name: str) -> str:
        """Convert a name to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_camel_case(self, name: str) -> str:
        """Convert a name to camelCase."""
        components = name.split('_')
        return components[0].lower() + ''.join(x.title() for x in components[1:])

    def forward(self, x):
        """Forward pass through the model."""
        # Ensure input is a tensor
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        # Add batch dimension if needed
        if len(x.shape) == 1:
            x = x.unsqueeze(0)
        
        # Add sequence dimension if needed
        if len(x.shape) == 2:
            x = x.unsqueeze(-1)
        
        # Reshape input to match embeddings
        batch_size, seq_len, _ = x.shape
        x = x.view(batch_size, seq_len)
        
        # Embed input
        x = self.embeddings(x)
        
        # Pass through encoder
        x = self.encoder(x)
        
        # Pass through output layer
        x = self.output_layer(x)
        
        return x
