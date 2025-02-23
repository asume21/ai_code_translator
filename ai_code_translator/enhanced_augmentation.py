"""Enhanced data augmentation for Python to JavaScript translation."""
import json
import os
import random
from typing import List, Dict, Tuple

class EnhancedCodeAugmenter:
    """Enhanced code augmentation with advanced Python features."""
    
    def __init__(self):
        """Initialize with example patterns."""
        self.python_patterns = self._load_python_patterns()
        
    def _load_python_patterns(self) -> List[Dict[str, str]]:
        """Load Python code patterns for augmentation."""
        return [
            {
                "name": "List Comprehension",
                "python": "    result = [i * 2 for i in range(n) if i > 0]",
                "javascript": "    const result = Array.from({length: n}, (_, i) => i).filter(i => i > 0).map(i => i * 2);"
            },
            {
                "name": "Lambda with Map",
                "python": "    doubled = list(map(lambda x: x * 2, range(n)))",
                "javascript": "    const doubled = Array.from({length: n}, (_, i) => i).map(x => x * 2);"
            },
            {
                "name": "Type Hints",
                "python": "    def helper(x: int) -> int:\n        return x + 1",
                "javascript": "    function helper(x) {\n        return x + 1;\n    }"
            },
            {
                "name": "Class with Methods",
                "python": "    class Calculator:\n        def __init__(self):\n            self.value = n\n        def compute(self):\n            return self.value * 2\n    calc = Calculator()\n    result = calc.compute()",
                "javascript": "    class Calculator {\n        constructor() {\n            this.value = n;\n        }\n        compute() {\n            return this.value * 2;\n        }\n    }\n    const calc = new Calculator();\n    const result = calc.compute();"
            },
            {
                "name": "Dictionary Methods",
                "python": "    cache = {}\n    if n not in cache:\n        cache[n] = n * 2\n    result = cache.get(n, 0)",
                "javascript": "    const cache = {};\n    if (!(n in cache)) {\n        cache[n] = n * 2;\n    }\n    const result = cache[n] ?? 0;"
            },
            {
                "name": "Error Handling",
                "python": "    try:\n        if n < 0:\n            raise ValueError('n must be positive')\n        result = n * 2\n    except ValueError as e:\n        result = 0",
                "javascript": "    try {\n        if (n < 0) {\n            throw new Error('n must be positive');\n        }\n        const result = n * 2;\n    } catch (e) {\n        const result = 0;\n    }"
            },
            {
                "name": "Async/Await",
                "python": "    async def compute():\n        return n * 2\n    result = await compute()",
                "javascript": "    async function compute() {\n        return n * 2;\n    }\n    const result = await compute();"
            },
            {
                "name": "Set Operations",
                "python": "    seen = set()\n    for i in range(n):\n        seen.add(i)\n    result = len(seen)",
                "javascript": "    const seen = new Set();\n    for (let i = 0; i < n; i++) {\n        seen.add(i);\n    }\n    const result = seen.size;"
            }
        ]
    
    def augment_dataset(self, input_file: str, output_file: str, num_augmentations: int = 2):
        """Augment the entire dataset with advanced Python features."""
        # Load existing dataset
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        source_codes = data['source_codes']
        target_codes = data['target_codes']
        
        # Augment each example
        new_sources = []
        new_targets = []
        
        # First add all original examples
        new_sources.extend(source_codes)
        new_targets.extend(target_codes)
        
        # Then create augmented versions
        for source, target in zip(source_codes, target_codes):
            for _ in range(num_augmentations):
                # Randomly select 1-2 patterns
                num_patterns = random.randint(1, 2)
                patterns = random.sample(self.python_patterns, num_patterns)
                
                # Apply each pattern
                aug_source = source
                aug_target = target
                for pattern in patterns:
                    aug_source = self._combine_code(aug_source, pattern['python'])
                    aug_target = self._combine_code(aug_target, pattern['javascript'])
                
                new_sources.append(aug_source)
                new_targets.append(aug_target)
        
        # Save augmented dataset
        augmented_data = {
            'source_codes': new_sources,
            'target_codes': new_targets
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(augmented_data, f, indent=2)
        
        print(f"\nAugmented dataset saved to {output_file}")
        print(f"Original examples: {len(source_codes)}")
        print(f"Total examples after augmentation: {len(new_sources)}")
        
        # Print example transformations
        print("\nExample transformations:")
        for i, (source, target) in enumerate(zip(source_codes, target_codes)):
            print(f"\nOriginal Example {i+1}:")
            print("Python:")
            print(source)
            print("\nJavaScript:")
            print(target)
            
            if i < len(new_sources) - len(source_codes):
                print(f"\nAugmented Version:")
                print("Python:")
                print(new_sources[len(source_codes) + i])
                print("\nJavaScript:")
                print(new_targets[len(source_codes) + i])
            
            if i >= 2:  # Only show first 3 examples
                break
    
    def _combine_code(self, original: str, pattern: str) -> str:
        """Combine original code with a pattern."""
        # Extract function body and find its indentation
        lines = original.split('\n')
        if not lines:
            return original
        
        # Find the indentation of the function body
        body_indent = None
        for line in lines[1:]:  # Skip first line (function definition)
            if line.strip():
                body_indent = len(line) - len(line.lstrip())
                break
        
        if body_indent is None:
            body_indent = 4  # Default indentation
        
        # Find where to insert the pattern (before the return statement)
        insert_idx = -1
        for i, line in enumerate(lines):
            if 'return' in line.strip():
                insert_idx = i
                break
        
        if insert_idx == -1:
            insert_idx = len(lines)  # Insert at the end if no return found
        
        # Adjust pattern indentation
        pattern_lines = pattern.split('\n')
        indented_pattern = []
        for i, line in enumerate(pattern_lines):
            if i == 0:
                # First line uses the body indentation
                indented_pattern.append(' ' * body_indent + line.lstrip())
            else:
                # Subsequent lines maintain relative indentation
                current_indent = len(line) - len(line.lstrip())
                indented_pattern.append(' ' * (body_indent + current_indent) + line.lstrip())
        
        # Insert pattern
        return '\n'.join(lines[:insert_idx] + indented_pattern + lines[insert_idx:])

if __name__ == '__main__':
    # Example usage
    augmenter = EnhancedCodeAugmenter()
    
    # Paths
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai_code_translator', 'data')
    train_file = os.path.join(data_dir, 'train.json')
    augmented_file = os.path.join(data_dir, 'train_augmented.json')
    
    # Augment dataset
    augmenter.augment_dataset(train_file, augmented_file, num_augmentations=2)
