import pytest
import torch
from ai_code_translator.model import CodeTransformer, CodeDataset
from ai_code_translator.languages import LanguageConfig
from ai_code_translator.metrics import CodeEvaluator
from transformers import RobertaTokenizer

@pytest.fixture
def model():
    return CodeTransformer(
        vocab_size=50000,
        d_model=512,
        nhead=8,
        num_encoder_layers=6
    )

@pytest.fixture
def tokenizer():
    return RobertaTokenizer.from_pretrained('microsoft/codebert-base')

def test_model_initialization(model):
    assert isinstance(model, CodeTransformer)
    assert model.d_model == 512
    assert isinstance(model.embedding, torch.nn.Embedding)
    assert isinstance(model.transformer_encoder, torch.nn.TransformerEncoder)

def test_model_forward_pass(model):
    batch_size = 2
    seq_length = 10
    x = torch.randint(0, 1000, (batch_size, seq_length))
    mask = torch.ones((batch_size, seq_length), dtype=torch.bool)
    
    output = model(x, src_padding_mask=mask)
    
    # Check output shape matches model's vocab size
    assert output.shape == (batch_size, seq_length, model.vocab_size)
    assert output.dtype == torch.float32
    assert not torch.isnan(output).any()

def test_model_translation(model):
    python_code = "def add(a, b):\n    return a + b"
    
    with pytest.raises(ValueError, match="Language pair.*not supported"):
        model.translate(python_code, "invalid_lang", "java")
        
    translated, metrics = model.translate(python_code, "python", "java")
    assert isinstance(translated, str)
    assert len(translated) > 0
    assert isinstance(metrics, dict)
    assert 'overall_score' in metrics
    assert 0 <= metrics['overall_score'] <= 1

def test_language_config():
    languages = LanguageConfig.get_supported_languages()
    assert 'python' in languages
    assert 'java' in languages
    
    python_pattern = LanguageConfig.get_language_pattern('python')
    assert 'indent' in python_pattern
    assert python_pattern['indent'] == '    '
    
    with pytest.raises(ValueError):
        LanguageConfig.get_language_pattern('invalid_lang')

def test_code_formatting():
    python_code = "def test():\nprint('hello')\nreturn None"
    formatted = LanguageConfig.format_code(python_code, 'python')
    assert '    print' in formatted
    
    java_code = "public class Test { void main() { System.out.println('hello'); } }"
    formatted = LanguageConfig.format_code(java_code, 'java')
    assert '{' in formatted
    assert '}' in formatted

def test_code_evaluation():
    reference = "def add(a, b):\n    return a + b"
    candidate = "def add(a, b):\n    return a + b"
    metrics = CodeEvaluator.evaluate(reference, candidate, 'python')
    
    assert 'bleu_score' in metrics
    assert 'structural_similarity' in metrics
    assert 'syntax_valid' in metrics
    assert 'overall_score' in metrics
    
    assert metrics['bleu_score'] == 1.0  # Perfect match
    assert metrics['syntax_valid'] == 1.0  # Valid syntax

def test_dataset_initialization(tokenizer):
    source_codes = ["def add(a, b):\n    return a + b"]
    target_codes = ["public int add(int a, int b) {\n    return a + b;\n}"]
    
    dataset = CodeDataset(
        source_codes=source_codes,
        target_codes=target_codes,
        tokenizer=tokenizer,
        source_lang="python",
        target_lang="java"
    )
    
    assert len(dataset) == 1
    
    with pytest.raises(ValueError, match="same length"):
        CodeDataset(source_codes, target_codes + ["extra"], tokenizer)

def test_dataset_item_processing(tokenizer):
    source_codes = ["def add(a, b):\n    return a + b"]
    target_codes = ["public int add(int a, int b) {\n    return a + b;\n}"]
    
    dataset = CodeDataset(
        source_codes=source_codes,
        target_codes=target_codes,
        tokenizer=tokenizer,
        source_lang="python",
        target_lang="java"
    )
    
    item = dataset[0]
    assert "input_ids" in item
    assert "attention_mask" in item
    assert "labels" in item
    assert item["input_ids"].dim() == 1
    assert item["attention_mask"].dim() == 1
    assert item["labels"].dim() == 1
