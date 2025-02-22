"""Code analyzer for handling dependencies and imports."""

import ast
import importlib
import pkg_resources
import re
from typing import Dict, List, Set, Tuple
import logging
from pathlib import Path
import subprocess
import sys

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Analyzes code for dependencies, imports, and structure."""
    
    def __init__(self):
        self.known_packages = {pkg.key for pkg in pkg_resources.working_set}
        
    def analyze_imports(self, code: str) -> Dict[str, List[str]]:
        """Analyze and categorize imports in the code."""
        tree = ast.parse(code)
        
        imports = {
            'standard_lib': [],
            'third_party': [],
            'local': [],
            'unknown': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    self._categorize_import(name.name, imports)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._categorize_import(node.module, imports)
                    
        return imports
    
    def _categorize_import(self, module_name: str, imports: Dict[str, List[str]]):
        """Categorize an import into standard library, third-party, or local."""
        root_module = module_name.split('.')[0]
        
        if root_module in sys.stdlib_module_names:
            imports['standard_lib'].append(module_name)
        elif root_module in self.known_packages:
            imports['third_party'].append(module_name)
        elif Path(f"{root_module}.py").exists():
            imports['local'].append(module_name)
        else:
            imports['unknown'].append(module_name)

    def analyze_dependencies(self, code: str) -> Dict[str, str]:
        """Analyze and determine required package dependencies."""
        imports = self.analyze_imports(code)
        dependencies = {}
        
        for package in imports['third_party']:
            root_package = package.split('.')[0]
            try:
                version = pkg_resources.get_distribution(root_package).version
                dependencies[root_package] = version
            except pkg_resources.DistributionNotFound:
                dependencies[root_package] = 'unknown'
        
        return dependencies

    def analyze_structure(self, code: str) -> Dict:
        """Analyze code structure (classes, functions, etc.)."""
        tree = ast.parse(code)
        
        structure = {
            'classes': [],
            'functions': [],
            'global_vars': [],
            'imports': [],
            'complexity': self._calculate_complexity(tree)
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                structure['classes'].append({
                    'name': node.name,
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                    'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                })
            elif isinstance(node, ast.FunctionDef):
                structure['functions'].append({
                    'name': node.name,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                })
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        structure['global_vars'].append(target.id)
        
        return structure

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def generate_requirements(self, dependencies: Dict[str, str]) -> str:
        """Generate requirements.txt content from dependencies."""
        return '\n'.join([f"{pkg}>={ver}" for pkg, ver in dependencies.items()])

    def fix_imports(self, code: str, target_lang: str) -> str:
        """Fix imports for the target language."""
        if target_lang == 'python':
            return code  # Already Python
            
        import_maps = {
            'javascript': {
                'import ': 'import ',  # ES6 imports
                'from ': 'import ',
                'as ': 'as '
            },
            'java': {
                'import ': 'import ',
                'from ': 'import ',
                'as ': ''  # Java doesn't support import aliases
            },
            'cpp': {
                'import ': '#include ',
                'from ': '#include ',
                'as ': 'namespace '  # C++ namespace alias
            }
        }
        
        if target_lang not in import_maps:
            return code
            
        tree = ast.parse(code)
        import_map = import_maps[target_lang]
        new_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    if target_lang == 'javascript':
                        new_imports.append(f"import {{ {name.name} }} from '{name.name}';")
                    elif target_lang == 'java':
                        new_imports.append(f"import {name.name};")
                    elif target_lang == 'cpp':
                        new_imports.append(f"#include <{name.name}>")
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                for name in node.names:
                    if target_lang == 'javascript':
                        new_imports.append(f"import {{ {name.name} }} from '{module}';")
                    elif target_lang == 'java':
                        new_imports.append(f"import {module}.{name.name};")
                    elif target_lang == 'cpp':
                        new_imports.append(f"#include <{module}/{name.name}.h>")
        
        return '\n'.join(new_imports) + '\n\n' + code

class DependencyManager:
    """Manages project dependencies and virtual environments."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.requirements_file = project_root / 'requirements.txt'
        
    def create_virtual_env(self) -> bool:
        """Create a virtual environment for the project."""
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], 
                         cwd=self.project_root, check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
    
    def install_dependencies(self, dependencies: Dict[str, str]) -> bool:
        """Install required dependencies."""
        try:
            # Write requirements
            with open(self.requirements_file, 'w') as f:
                f.write(CodeAnalyzer().generate_requirements(dependencies))
            
            # Install using pip
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                         cwd=self.project_root, check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def check_compatibility(self, dependencies: Dict[str, str]) -> List[str]:
        """Check for compatibility issues between dependencies."""
        conflicts = []
        installed = pkg_resources.working_set
        
        for pkg, version in dependencies.items():
            if version == 'unknown':
                continue
            
            try:
                pkg_resources.require(f"{pkg}>={version}")
            except pkg_resources.VersionConflict as e:
                conflicts.append(f"Conflict: {e}")
        
        return conflicts
