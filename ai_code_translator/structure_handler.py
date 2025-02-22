"""Handle code structure analysis and preservation."""

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from .code_analyzer import CodeAnalyzer
import re

@dataclass
class MethodInfo:
    """Information about a method."""
    name: str
    args: List[str]
    returns: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    body: List[str] = field(default_factory=list)

@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    methods: Dict[str, MethodInfo] = field(default_factory=dict)
    bases: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)

@dataclass
class ModuleInfo:
    """Information about a module."""
    name: str
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    functions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    imports: Dict[str, str] = field(default_factory=dict)
    globals: List[str] = field(default_factory=list)
    docstring: Optional[str] = None

class StructureHandler:
    """Handles code structure analysis and preservation."""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
    
    def analyze_module(self, code: str, module_name: str = "__main__") -> ModuleInfo:
        """Analyze a module's structure."""
        # Convert JavaScript to Python syntax if needed
        if self._is_javascript(code):
            code = self._preprocess_javascript(code)
        
        tree = ast.parse(code)
        
        # Add parent references to all nodes
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                setattr(child, 'parent', parent)
        
        classes: Dict[str, ClassInfo] = {}
        functions: Dict[str, Dict[str, Any]] = {}
        globals: List[str] = []
        docstring = ast.get_docstring(tree)
        
        # Analyze imports first
        imports = self.analyzer.analyze_imports(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                classes[class_info.name] = class_info
            elif isinstance(node, ast.FunctionDef):
                parent = getattr(node, 'parent', None)
                if not isinstance(parent, ast.ClassDef):  # Skip methods
                    functions[node.name] = self._analyze_function(node)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                parent = getattr(node, 'parent', None)
                if isinstance(parent, ast.Module):
                    globals.append(node.id)
        
        return ModuleInfo(
            name=module_name,
            classes=classes,
            functions=functions,
            imports=imports,
            globals=globals,
            docstring=docstring
        )
    
    def _is_javascript(self, code: str) -> bool:
        """Check if code is JavaScript."""
        # Look for JavaScript-specific syntax
        js_patterns = [
            r'class\s+\w+\s*{',  # Class definition
            r'constructor\s*\(',  # Constructor
            r'function\s+\w+\s*\(',  # Function definition
            r'let\s+|const\s+|var\s+',  # Variable declarations
            r'}\s*$',  # Closing brace at end of line
            r';\s*$'  # Semicolon at end of line
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, code):
                return True
        return False
    
    def _preprocess_javascript(self, code: str) -> str:
        """Convert JavaScript code to Python syntax for analysis."""
        # Split code into lines
        lines = code.split('\n')
        python_lines = []
        in_class = False
        in_method = False
        current_method = None
        method_body = []
        indentation = 0
        class_has_methods = False
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                python_lines.append(line)
                continue
            
            # Handle class definition
            if re.match(r'\s*class\s+\w+\s*{', line):
                class_name = re.search(r'class\s+(\w+)', line).group(1)
                python_lines.append(f'class {class_name}:')
                in_class = True
                indentation = 4
                # Add pass statement immediately
                python_lines.append('    pass')
                continue
            
            # Handle constructor
            if re.match(r'\s*constructor\s*\(', line):
                args = re.search(r'constructor\s*\((.*?)\)', line).group(1)
                # Replace pass with __init__
                python_lines[-1] = f'    def __init__(self):'
                current_method = '__init__'
                in_method = True
                indentation = 8
                class_has_methods = True
                continue
            
            # Handle method definition
            if re.match(r'\s*\w+\s*\(', line) and in_class and not in_method:
                method_name = re.search(r'\s*(\w+)\s*\(', line).group(1)
                args = re.search(r'\w+\s*\((.*?)\)', line).group(1)
                # Add self parameter
                python_lines.append(f'    def {method_name}(self):')
                current_method = method_name
                in_method = True
                indentation = 8
                class_has_methods = True
                continue
            
            # Handle closing braces
            if line.strip() == '}':
                if in_method:
                    # Add method body if not empty
                    if method_body:
                        python_lines.extend(method_body)
                    else:
                        python_lines.append(' ' * indentation + 'pass')
                    method_body = []
                    current_method = None
                    in_method = False
                    indentation = 4
                    python_lines.append('')  # Add blank line after method
                elif in_class:
                    in_class = False
                    class_has_methods = False
                    indentation = 0
                    python_lines.append('')  # Add blank line after class
                continue
            
            # Handle method body
            if in_method:
                # Remove semicolons and convert this. to self.
                line = line.strip().rstrip(';').replace('this.', 'self.')
                # Remove opening brace
                if line.strip() == '{':
                    continue
                if line:
                    # Store method body lines
                    method_body.append(' ' * indentation + line)
                continue
            
            # Handle other lines
            if not line.strip().startswith(('import', 'class')):
                continue
            python_lines.append(line)
        
        # Add pass statement if class is still open
        if in_class and not class_has_methods:
            python_lines.append('    pass')
        
        return '\n'.join(python_lines)
    
    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition."""
        methods: Dict[str, MethodInfo] = {}
        bases = [base.id if isinstance(base, ast.Name) else base.attr for base in node.bases]
        decorators = [d.id if isinstance(d, ast.Name) else d.attr for d in node.decorator_list]
        
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                method_info = self._analyze_method(child)
                methods[method_info.name] = method_info
        
        return ClassInfo(
            name=node.name,
            methods=methods,
            bases=bases,
            docstring=ast.get_docstring(node),
            decorators=decorators
        )
    
    def _analyze_method(self, node: ast.FunctionDef) -> MethodInfo:
        """Analyze a method definition."""
        args = []
        for arg in node.args.args:
            if arg.arg != 'self':  # Skip self parameter
                args.append(arg.arg)
        
        returns = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                returns = node.returns.id
            elif isinstance(node.returns, ast.Subscript):
                returns = node.returns.value.id
        
        decorators = [d.id if isinstance(d, ast.Name) else d.attr for d in node.decorator_list]
        
        # Get method body without docstring
        body = []
        first_line = True
        for line in ast.unparse(node.body).split('\n'):
            if first_line and line.strip().startswith('"') and line.strip().endswith('"'):
                # Skip docstring
                first_line = False
                continue
            body.append(line.strip())
        
        return MethodInfo(
            name=node.name,
            args=args,
            returns=returns,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            body=body
        )
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze a function definition."""
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        returns = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                returns = node.returns.id
            elif isinstance(node.returns, ast.Subscript):
                returns = node.returns.value.id
        
        decorators = [d.id if isinstance(d, ast.Name) else d.attr for d in node.decorator_list]
        
        body = []
        for line in ast.unparse(node.body).split('\n'):
            body.append(line.strip())
        
        return {
            'name': node.name,
            'args': args,
            'returns': returns,
            'docstring': ast.get_docstring(node),
            'decorators': decorators,
            'body': body
        }
    
    def translate_structure(self, module_info: ModuleInfo, source_lang: str, target_lang: str,
                          translator: Optional[Any] = None) -> str:
        """Translate code structure from source to target language."""
        result = []
        
        # Translate imports
        if module_info.imports:
            result.extend(self._translate_imports(module_info.imports, source_lang, target_lang))
            result.append("")  # Add blank line after imports
        
        # Translate functions
        for func_name, func_info in module_info.functions.items():
            result.extend(self._translate_function(func_name, func_info, source_lang, target_lang))
            result.append("")  # Add blank line between functions
        
        # Translate classes
        for class_name, class_info in module_info.classes.items():
            result.extend(self._translate_class(class_name, class_info, source_lang, target_lang))
            result.append("")  # Add blank line between classes
        
        return "\n".join(result).strip()
    
    def _translate_imports(self, imports: Dict[str, str], source_lang: str, target_lang: str) -> List[str]:
        """Translate import statements."""
        if target_lang == 'javascript':
            # Convert Python imports to JavaScript imports
            js_imports = []
            for module, alias in imports.items():
                if 'from' in module:
                    # from module import name -> import { name } from 'module'
                    parts = module.split('import')
                    module = parts[0].replace('from', '').strip()
                    names = alias
                    js_imports.append(f"import {{ {names} }} from '{module}';")
                else:
                    # import module -> import module from 'module'
                    module = module.replace('import', '').strip()
                    js_imports.append(f"import {module} from '{module}';")
            return js_imports
        else:
            # Keep Python imports as is
            return [f"import {module} as {alias}" for module, alias in imports.items()]
    
    def _translate_function(self, func_name: str, func_info: Dict[str, any],
                          source_lang: str, target_lang: str) -> List[str]:
        """Translate a function definition."""
        result = []
        
        # Add docstring as comment
        if func_info.get('docstring'):
            if target_lang == 'javascript':
                result.append("/**")
                for line in func_info['docstring'].split('\n'):
                    result.append(f" * {line.strip()}")
                result.append(" */")
            else:
                result.append(f'"""{func_info["docstring"]}"""')
        
        # Build function signature
        if target_lang == 'javascript':
            # Convert Python function to JavaScript
            params = func_info.get('params', [])
            param_str = ', '.join(params)
            result.append(f"function {func_name}({param_str}) {{")
        else:
            # Keep Python function as is
            params = func_info.get('params', [])
            param_str = ', '.join(params)
            result.append(f"def {func_name}({param_str}):")
        
        # Add function body
        body = func_info.get('body', ['pass'])
        if target_lang == 'javascript':
            # Convert Python body to JavaScript
            for line in body:
                if line.strip() == 'pass':
                    result.append("    // Empty function")
                else:
                    result.append(f"    {line}")
            result.append("}")
        else:
            # Keep Python body as is
            for line in body:
                result.append(f"    {line}")
        
        return result
    
    def _translate_method(self, method_name: str, method_info: MethodInfo, source_lang: str, target_lang: str) -> List[str]:
        """Translate a method definition."""
        result = []
        
        if target_lang == 'javascript':
            # Handle constructor
            if method_name == '__init__':
                method_def = f'constructor({", ".join(method_info.args)}) {{'
            else:
                method_def = f'{method_name}({", ".join(method_info.args)}) {{'
            result.append(method_def)
            
            # Add method docstring
            if method_info.docstring:
                result.append('    /**')
                for line in method_info.docstring.split('\n'):
                    result.append(f'     * {line}')
                result.append('     */')
            
            # Add method body
            for line in method_info.body:
                if line:  # Skip empty lines
                    # Convert self. to this.
                    line = line.replace('self.', 'this.')
                    # Add semicolon if missing
                    if not line.strip().endswith(';'):
                        line += ';'
                    result.append(f'    {line}')
            result.append('}')
        else:  # Python
            # Handle method signature
            if method_name == '__init__':
                method_def = f'def {method_name}(self'
            else:
                method_def = f'def {method_name}(self'
            
            # Add arguments
            if method_info.args:
                method_def += f', {", ".join(method_info.args)}'
            method_def += '):'
            result.append(method_def)
            
            # Add method docstring
            if method_info.docstring:
                result.append(f'    """{method_info.docstring}"""')
            
            # Add method body
            for line in method_info.body:
                if line:  # Skip empty lines
                    # Convert this. to self.
                    line = line.replace('this.', 'self.')
                    # Remove semicolons
                    if line.strip().endswith(';'):
                        line = line[:-1]
                    result.append(f'    {line}')
            
            # Add empty line after method
            result.append('')
        
        return result
    
    def _translate_class(self, class_name: str, class_info: ClassInfo, source_lang: str, target_lang: str) -> List[str]:
        """Translate a class definition."""
        result = []
        
        # Add class docstring
        if class_info.docstring:
            if target_lang == 'javascript':
                result.append('/**')
                for line in class_info.docstring.split('\n'):
                    result.append(f' * {line}')
                result.append(' */')
            else:
                result.append('"""')
                result.extend(class_info.docstring.split('\n'))
                result.append('"""')
        
        # Add class definition
        if target_lang == 'javascript':
            class_def = f'class {class_name}'
            if class_info.bases:
                class_def += f' extends {", ".join(class_info.bases)}'
            class_def += ' {'
            result.append(class_def)
        else:
            class_def = f'class {class_name}'
            if class_info.bases:
                class_def += f'({", ".join(class_info.bases)})'
            class_def += ':'
            result.append(class_def)
        
        # Add methods
        for method_name, method_info in class_info.methods.items():
            result.extend(self._translate_method(method_name, method_info, source_lang, target_lang))
        
        if target_lang == 'javascript':
            result.append('}')
        
        return result
