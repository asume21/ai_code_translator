"""Validation system for Python-JavaScript translations."""

import ast
import json
import os
from typing import Dict, List, Tuple
import subprocess
import tempfile

class TranslationValidator:
    """Validates Python-JavaScript code translations for correctness."""
    
    def __init__(self):
        self.python_test_template = '''
def test_function({params}):
    {body}
    return result

# Test cases
test_cases = {test_cases}
results = []
for test_case in test_cases:
    try:
        result = test_function(*test_case)
        results.append(result)
    except Exception as e:
        results.append(str(e))
print(json.dumps(results))
'''
        
        self.js_test_template = '''
function testFunction({params}) {{
    {body}
    return result;
}}

// Test cases
const testCases = {test_cases};
const results = [];
for (const testCase of testCases) {{
    try {{
        const result = testFunction(...testCase);
        results.push(result);
    }} catch (e) {{
        results.push(e.toString());
    }}
}}
console.log(JSON.stringify(results));
'''
    
    def generate_test_cases(self, code: str) -> List:
        """Generate test cases based on code analysis."""
        test_cases = []
        try:
            tree = ast.parse(code)
            # Analyze parameters and types
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    num_params = len(node.args.args)
                    # Generate test cases based on parameter count and types
                    if num_params == 1:
                        test_cases.extend([
                            [42],  # Number
                            ["test"],  # String
                            [[1, 2, 3]]  # Array
                        ])
                    elif num_params == 2:
                        test_cases.extend([
                            [10, 20],  # Numbers
                            ["hello", "world"],  # Strings
                            [[1, 2], [3, 4]]  # Arrays
                        ])
                    break
        except:
            # Default test cases if parsing fails
            test_cases = [[1, 2, 3], ["test"], [42]]
        
        return test_cases
    
    def validate_syntax(self, code: str, language: str) -> bool:
        """Validate code syntax."""
        if language == 'python':
            try:
                ast.parse(code)
                return True
            except SyntaxError:
                return False
        else:  # javascript
            with tempfile.NamedTemporaryFile(suffix='.js', delete=False) as f:
                f.write(code.encode())
                js_file = f.name
            
            try:
                result = subprocess.run(['node', '--check', js_file], 
                                     capture_output=True, 
                                     text=True)
                os.unlink(js_file)
                return result.returncode == 0
            except:
                os.unlink(js_file)
                return False
    
    def run_code(self, code: str, language: str, test_cases: List) -> List:
        """Run code with test cases and return results."""
        if language == 'python':
            template = self.python_test_template
            cmd = ['python']
        else:
            template = self.js_test_template
            cmd = ['node']
        
        # Extract function parameters
        try:
            if language == 'python':
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        params = ', '.join(arg.arg for arg in node.args.args)
                        body = '\n    '.join(line for line in code.split('\n')[1:])
                        break
            else:
                # Simple regex for JavaScript (not perfect but works for basic cases)
                import re
                match = re.search(r'function\s+\w+\s*\((.*?)\)\s*{(.*?)}', code, re.DOTALL)
                if match:
                    params = match.group(1)
                    body = match.group(2)
        except:
            params = 'x, y'
            body = code
        
        # Create test file
        test_code = template.format(
            params=params,
            body=body,
            test_cases=json.dumps(test_cases)
        )
        
        with tempfile.NamedTemporaryFile(suffix='.'+language, delete=False) as f:
            f.write(test_code.encode())
            test_file = f.name
        
        try:
            result = subprocess.run(cmd + [test_file], 
                                 capture_output=True, 
                                 text=True,
                                 timeout=5)
            os.unlink(test_file)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except:
            os.unlink(test_file)
            return []
    
    def validate_translation(self, python_code: str, js_code: str) -> Dict:
        """Validate a Python-JavaScript translation pair."""
        results = {
            'python_syntax_valid': False,
            'js_syntax_valid': False,
            'functionally_equivalent': False,
            'test_results': None,
            'errors': []
        }
        
        # Check syntax
        results['python_syntax_valid'] = self.validate_syntax(python_code, 'python')
        results['js_syntax_valid'] = self.validate_syntax(js_code, 'javascript')
        
        if not results['python_syntax_valid']:
            results['errors'].append('Invalid Python syntax')
        if not results['js_syntax_valid']:
            results['errors'].append('Invalid JavaScript syntax')
        
        if results['python_syntax_valid'] and results['js_syntax_valid']:
            # Generate and run test cases
            test_cases = self.generate_test_cases(python_code)
            python_results = self.run_code(python_code, 'python', test_cases)
            js_results = self.run_code(js_code, 'javascript', test_cases)
            
            results['test_results'] = {
                'test_cases': test_cases,
                'python_results': python_results,
                'js_results': js_results
            }
            
            # Check if results match
            if python_results and js_results:
                results['functionally_equivalent'] = python_results == js_results
            else:
                results['errors'].append('Error running test cases')
        
        return results
    
    def validate_dataset(self, dataset_file: str) -> Dict:
        """Validate all translations in a dataset."""
        with open(dataset_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        validation_results = {
            'total_pairs': len(data['pairs']),
            'valid_syntax_pairs': 0,
            'functionally_equivalent_pairs': 0,
            'failed_pairs': [],
            'summary': {}
        }
        
        for i, pair in enumerate(data['pairs']):
            print(f"\rValidating pair {i+1}/{validation_results['total_pairs']}...", end='')
            
            result = self.validate_translation(pair['source'], pair['target'])
            
            if result['python_syntax_valid'] and result['js_syntax_valid']:
                validation_results['valid_syntax_pairs'] += 1
            
            if result['functionally_equivalent']:
                validation_results['functionally_equivalent_pairs'] += 1
            else:
                validation_results['failed_pairs'].append({
                    'pair_index': i,
                    'errors': result['errors'],
                    'test_results': result['test_results']
                })
        
        print("\nGenerating summary...")
        validation_results['summary'] = {
            'success_rate': validation_results['functionally_equivalent_pairs'] / validation_results['total_pairs'],
            'syntax_valid_rate': validation_results['valid_syntax_pairs'] / validation_results['total_pairs'],
            'total_failures': len(validation_results['failed_pairs'])
        }
        
        return validation_results

if __name__ == '__main__':
    # Paths
    project_dir = os.path.dirname(os.path.dirname(__file__))
    dataset_file = os.path.join(project_dir, 'ai_code_translator', 'data', 'cleaned_dataset.json')
    
    # Validate dataset
    validator = TranslationValidator()
    results = validator.validate_dataset(dataset_file)
    
    # Save results
    output_file = os.path.join(project_dir, 'ai_code_translator', 'data', 'validation_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print("\nValidation Results:")
    print(f"Total pairs: {results['total_pairs']}")
    print(f"Valid syntax pairs: {results['valid_syntax_pairs']}")
    print(f"Functionally equivalent pairs: {results['functionally_equivalent_pairs']}")
    print(f"Success rate: {results['summary']['success_rate']*100:.2f}%")
    print(f"Syntax valid rate: {results['summary']['syntax_valid_rate']*100:.2f}%")
    print(f"Failed pairs: {results['summary']['total_failures']}")
    print(f"\nDetailed results saved to: {output_file}")
