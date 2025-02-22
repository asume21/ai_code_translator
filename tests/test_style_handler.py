"""Unit tests for the style handler."""

import pytest
from pathlib import Path
import sys

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from ai_code_translator.style_handler import StyleHandler, StyleConfig

# Test data with different styles
SNAKE_CASE_CODE = '''
def calculate_sum(first_number, second_number):
    """Calculate sum of two numbers."""
    result = first_number + second_number
    return result

class number_processor:
    def process_numbers(self, input_list):
        return [num * 2 for num in input_list]
'''

CAMEL_CASE_CODE = '''
function calculateSum(firstNumber, secondNumber) {
    // Calculate sum of two numbers
    let result = firstNumber + secondNumber;
    return result;
}

class NumberProcessor {
    processNumbers(inputList) {
        return inputList.map(num => num * 2);
    }
}
'''

@pytest.fixture
def style_handler():
    return StyleHandler()

def test_style_detection(style_handler):
    """Test style characteristic detection."""
    # Test Python style detection
    chars = style_handler._extract_style_characteristics(SNAKE_CASE_CODE)
    
    assert chars['indent_size'] == 4
    assert chars['naming_style'] == 'snake_case'
    assert chars['quote_style'] in ['single', 'double']
    
    # Test JavaScript style detection
    chars = style_handler._extract_style_characteristics(CAMEL_CASE_CODE)
    assert chars['naming_style'] == 'camelCase'

def test_naming_convention_preservation(style_handler):
    """Test preservation of naming conventions."""
    # Configure for snake_case
    snake_config = StyleConfig(naming_convention='snake_case')
    handler = StyleHandler(snake_config)
    
    result = handler.preserve_style(
        CAMEL_CASE_CODE,
        SNAKE_CASE_CODE,
        'javascript',
        'python'
    )
    
    assert 'calculate_sum' in result
    assert 'first_number' in result
    
    # Configure for camelCase
    camel_config = StyleConfig(naming_convention='camelCase')
    handler = StyleHandler(camel_config)
    
    result = handler.preserve_style(
        SNAKE_CASE_CODE,
        CAMEL_CASE_CODE,
        'python',
        'javascript'
    )
    
    assert 'calculateSum' in result
    assert 'firstNumber' in result

def test_indentation_preservation(style_handler):
    """Test preservation of indentation."""
    # Test with 2-space indentation
    code_2_space = '  def test():\n    pass'
    config = StyleConfig(indent_size=2)
    handler = StyleHandler(config)
    
    result = handler._apply_indentation(code_2_space, 2)
    assert '  def' in result
    
    # Test with 4-space indentation
    code_4_space = '    def test():\n        pass'
    config = StyleConfig(indent_size=4)
    handler = StyleHandler(config)
    
    result = handler._apply_indentation(code_4_space, 4)
    assert '    def' in result

def test_quote_style_preservation(style_handler):
    """Test preservation of quote styles."""
    # Test single quotes
    single_quote_code = "print('test')"
    config = StyleConfig(quote_style='single')
    handler = StyleHandler(config)
    
    result = handler._apply_quote_style(single_quote_code, 'single')
    assert "'" in result
    
    # Test double quotes
    double_quote_code = 'print("test")'
    config = StyleConfig(quote_style='double')
    handler = StyleHandler(config)
    
    result = handler._apply_quote_style(double_quote_code, 'double')
    assert '"' in result

def test_language_specific_formatting(style_handler):
    """Test language-specific formatting."""
    # Test Python formatting
    python_code = 'def test():\n  return True'
    result = style_handler._format_python(python_code)
    assert 'def test():' in result
    
    # Test JavaScript formatting
    js_code = 'function test(){return true}'
    result = style_handler._format_javascript(js_code)
    assert 'function test()' in result
    assert '{' in result

def test_style_config_application(style_handler):
    """Test application of style configuration."""
    config = StyleConfig(
        indent_size=2,
        max_line_length=80,
        quote_style='single',
        naming_convention='camelCase',
        bracket_style='same_line'
    )
    
    handler = StyleHandler(config)
    result = handler.preserve_style(
        SNAKE_CASE_CODE,
        CAMEL_CASE_CODE,
        'python',
        'javascript'
    )
    
    # Check if configuration was applied
    assert '  ' in result  # 2-space indentation
    assert "'" in result  # single quotes
    assert 'function calculateSum' in result  # camelCase
    assert ') {' in result  # same-line brackets

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
