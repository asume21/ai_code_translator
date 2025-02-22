"""Integration tests for the AI Code Translator."""

import pytest
import torch
from ai_code_translator.model import CodeTransformer, CodeDataset
from ai_code_translator.languages import LanguageConfig
from ai_code_translator.metrics import CodeEvaluator

# Test cases for different languages
TEST_CASES = {
    'python': {
        'code': """def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)""",
        'expected_java': """public int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}""",
    },
    'java': {
        'code': """public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}""",
        'expected_python': """class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b""",
    },
    'javascript': {
        'code': """function greet(name) {
    console.log(`Hello, ${name}!`);
    return true;
}""",
        'expected_python': """def greet(name):
    print(f"Hello, {name}!")
    return True""",
    }
}

@pytest.fixture
def model():
    return CodeTransformer(
        vocab_size=50000,
        d_model=512,
        nhead=8,
        num_encoder_layers=6
    )

def test_language_support():
    """Test that all supported languages are properly configured."""
    languages = LanguageConfig.get_supported_languages()
    required_languages = {'python', 'java', 'cpp', 'javascript', 'csharp'}
    assert required_languages.issubset(languages)
    
    for lang in languages:
        patterns = LanguageConfig.get_language_pattern(lang)
        assert 'indent' in patterns
        assert 'keywords' in patterns
        assert isinstance(patterns['keywords'], set)

def test_code_formatting():
    """Test code formatting for different languages."""
    # Test Python formatting
    python_code = "def test():\nprint('hello')\nreturn None"
    formatted = LanguageConfig.format_code(python_code, 'python')
    assert formatted.count('    ') >= 1  # Check indentation
    
    # Test Java formatting
    java_code = "public class Test{void main(){System.out.println('hello');}}"
    formatted = LanguageConfig.format_code(java_code, 'java')
    assert formatted.count('\n') >= 2  # Check line breaks
    assert formatted.count('{') == formatted.count('}')  # Check brackets

def test_evaluation_metrics():
    """Test evaluation metrics calculation."""
    reference = "def add(a, b):\n    return a + b"
    candidate = "def add(a, b):\n    return a + b"
    
    metrics = CodeEvaluator.evaluate(reference, candidate, 'python')
    assert metrics['bleu_score'] == 1.0  # Perfect match
    assert metrics['structural_similarity'] == 1.0
    assert metrics['syntax_valid'] == 1.0
    assert metrics['overall_score'] == 1.0
    
    # Test with slightly different code
    candidate = "def add(x, y):\n    return x + y"
    metrics = CodeEvaluator.evaluate(reference, candidate, 'python')
    assert 0 < metrics['bleu_score'] < 1.0  # Similar but not perfect
    assert metrics['syntax_valid'] == 1.0  # Still valid syntax

def test_translation_quality(model):
    """Test translation quality for different language pairs."""
    for source_lang, test_case in TEST_CASES.items():
        for target_lang in LanguageConfig.get_supported_languages():
            if source_lang != target_lang:
                translated, metrics = model.translate(
                    test_case['code'],
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                
                assert isinstance(translated, str)
                assert len(translated) > 0
                assert isinstance(metrics, dict)
                assert 0 <= metrics['overall_score'] <= 1
                
                # Verify syntax validity
                assert metrics['syntax_valid'] == 1.0
                
                # If we have expected output, compare structure
                if target_lang in test_case:
                    expected = test_case[f'expected_{target_lang}']
                    similarity = CodeEvaluator.calculate_code_similarity(
                        expected, translated, target_lang
                    )
                    assert similarity > 0.5  # At least 50% structural similarity

def test_special_cases(model):
    """Test handling of special cases and edge cases."""
    # Test empty code
    with pytest.raises(ValueError):
        model.translate("", "python", "java")
    
    # Test invalid language
    with pytest.raises(ValueError):
        model.translate("def test(): pass", "python", "invalid_lang")
    
    # Test very long code
    long_code = "def test(): pass\n" * 1000
    translated, metrics = model.translate(long_code, "python", "java")
    assert isinstance(translated, str)
    assert len(translated) > 0
    
    # Test code with special characters
    special_code = """def test():
    print("Hello 世界!")  # Unicode comment
    return True"""
    translated, metrics = model.translate(special_code, "python", "java")
    assert isinstance(translated, str)
    assert len(translated) > 0

def test_dataset_handling(model):
    """Test dataset creation and processing."""
    source_codes = [test_case['code'] for test_case in TEST_CASES.values()]
    target_codes = [test_case.get('expected_java', test_case['code']) 
                   for test_case in TEST_CASES.values()]
    
    dataset = CodeDataset(
        source_codes=source_codes,
        target_codes=target_codes,
        tokenizer=model.tokenizer,
        source_lang="python",
        target_lang="java"
    )
    
    assert len(dataset) == len(TEST_CASES)
    
    # Test batch processing
    item = dataset[0]
    assert all(key in item for key in ['input_ids', 'attention_mask', 'labels'])
    assert all(isinstance(v, torch.Tensor) for v in item.values())

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
