from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

def translate_code(source_code, model_path="finetuned_translator"):
    tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
    
    inputs = tokenizer(source_code, return_tensors="pt", truncation=True, max_length=512)
    outputs = model.generate(**inputs, max_length=512)
    translated_code = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return translated_code

# Test translation
python_code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
"""

translated_c = translate_code(python_code)
print("Original Python code:")
print(python_code)
print("\nTranslated C code:")
print(translated_c)
