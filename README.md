# AI Code Translator

A powerful open-source code translation model built on top of CodeT5, capable of translating code between different programming languages. Available under both AGPL-3.0 (open-source) and commercial licenses.

## 🌟 Community & Commercial Use

This project is dual-licensed:
- **Open Source**: Free under AGPL-3.0 for open-source projects, research, and personal use
- **Commercial**: Flexible commercial licensing available for business use

## ✨ Features

- Accurate code translation between multiple programming languages
- Preservation of code structure and style
- Built-in code analysis and validation
- Extensible architecture for adding new languages
- Community-driven improvements and extensions

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

## 🤝 Contributing

We welcome contributions! Here's how you can help:
- Report bugs and suggest features
- Submit pull requests
- Improve documentation
- Add support for new programming languages
- Share your success stories

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Optimizations

The project includes several optimizations for training on consumer-grade hardware:
- Memory-efficient data loading
- Gradient accumulation
- Dynamic batch sizing
- Automatic memory management

## 💼 Commercial Support

Need to use this project in a commercial product? Our commercial license includes:
- Priority support
- Additional features
- Custom development
- No AGPL requirements

Contact [Your Contact Information] for details.

## License

AGPL-3.0

## Acknowledgments

- Based on Salesforce's CodeT5 model
- Inspired by various code translation projects in the community
