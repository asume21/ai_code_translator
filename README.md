# AI Code Translator

**PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED**

This is a commercial product. Usage requires a valid license. Contact [Your Contact Information] for licensing inquiries.

A powerful code translation model built on top of CodeT5, capable of translating code between different programming languages.

## Features

- Multi-language code translation support
- Memory-efficient training pipeline
- Support for multiple dataset formats
- Gradient accumulation for training on limited hardware
- Automatic dataset preprocessing

## Requirements

- Python 3.8+
- PyTorch 2.0+
- CUDA compatible GPU (tested on NVIDIA GTX 1050 Ti)
- 8GB+ RAM

## Installation

```bash
git clone https://github.com/yourusername/ai_code_translator.git
cd ai_code_translator
pip install -r requirements.txt
```

## Dataset Setup

The project uses several large dataset files that are stored separately from the code repository. To download the required datasets:

1. Install the project requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the data download script:
   ```bash
   python scripts/download_data.py
   ```

This will automatically download and place the following files in their correct locations:
- `data/codetransocean/nichetrans/niche_test.json`
- `data/codetransocean/nichetrans/niche_train.json`
- `data/codetransocean/nichetrans/niche_valid.json`
- `data/codetransocean/multilingualtrans/multilingual_train.json`

If you encounter any issues with the automatic download, you can manually download the files from [Google Drive](https://drive.google.com/drive/folders/1RcLRBJ-4gwZ5DSDEgEhgk8eWbz_yGOxk?usp=drive_link).

## Usage

### Training

```bash
python scripts/train.py
```

### Translation

```python
from ai_code_translator import CodeTranslator

translator = CodeTranslator()
translated_code = translator.translate(
    source_code="print('Hello World')",
    source_lang="python",
    target_lang="javascript"
)
```

## Datasets

The model is trained on a combination of:
- Apps Dataset
- Code Alpaca
- CodeSearchNet (Python, Java, JavaScript)

## Contributing

We welcome contributions! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Optimizations

The project includes several optimizations for training on consumer-grade hardware:
- Memory-efficient data loading
- Gradient accumulation
- Dynamic batch sizing
- Automatic memory management

## License

MIT License

## Acknowledgments

- Based on Salesforce's CodeT5 model
- Inspired by various code translation projects in the community
