# AI Code Translator

A modern GUI application for translating code between different programming languages using AI.

## Features

- Modern, dark-themed GUI with syntax highlighting
- Support for multiple programming languages
- Real-time translation with style preservation
- Memory usage monitoring
- Line number toggling
- Font size controls
- File type detection for automatic language selection
- Enhanced PyTorch model with attention mechanism
- Improved training process with early stopping and validation
- Astutely chatbot integration for interactive assistance

## Chatbot Integration

The AI Code Translator now includes "Astutely", an interactive chatbot that can:

- Answer questions about code translation
- Provide explanations of translation processes
- Accept code directly in the chat for translation
- Guide users through the translation process

The chatbot is integrated into the GUI through a tabbed interface, allowing users to switch between direct translation and conversational interaction.

## Project Structure

```
ai_code_translator/
├── ai_code_translator/         # Main package directory
│   ├── __init__.py            # Package initialization
│   ├── main.py                # GUI application
│   ├── model.py               # Translation model
│   ├── languages.py           # Language definitions
│   ├── style_handler.py       # Code style preservation
│   ├── train_model.py         # Enhanced model training
│   ├── predict.py             # Model prediction script
│   ├── translation_validator.py # Translation validation
│   ├── enhanced_augmentation.py # Data augmentation
│   ├── modern_features.py     # Modern code features
│   ├── config/               # Configuration files
│   │   └── config.yml        # Main configuration
│   ├── data/                 # Data files
│   │   ├── multiwoz/        # MultiWOZ dialogue dataset
│   │   │   └── compiled_dialogues.json  # Processed dialogue data
│   │   ├── train.json       # Training data
│   │   └── val.json         # Validation data
│   └── models/              # Model checkpoints
├── tests/                    # Test files
├── scripts/                  # Utility scripts
├── notebooks/                # Jupyter notebooks
├── requirements.txt          # Project dependencies
├── setup.py                 # Package setup
└── README.md                # Project documentation
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-code-translator.git
cd ai-code-translator
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

## Usage

1. Run the GUI application:
```bash
ai-code-translator
```

2. Train the enhanced model:
```bash
cd ai_code_translator
python train_model.py
```

3. Make predictions with the trained model:
```bash
python predict.py --model-dir models/model_YYYYMMDD_HHMMSS --input "your input text here" --device cuda
```

## Advanced Training Features

The enhanced training process includes:

- **Attention Mechanism**: Improves model's ability to focus on relevant input parts
- **Data Validation Split**: Properly evaluates model performance on unseen data
- **Early Stopping**: Prevents overfitting by stopping training when validation performance stops improving
- **Learning Rate Scheduling**: Automatically adjusts learning rate for better convergence
- **Gradient Clipping**: Prevents exploding gradients during training
- **Comprehensive Logging**: Detailed training logs with visualizations
- **Model Checkpointing**: Saves intermediate models for later resuming or analysis
- **Validation Metrics**: Tracks model performance on validation set

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest tests/
```

3. Format code:
```bash
black ai_code_translator/
isort ai_code_translator/
```

4. Type checking:
```bash
mypy ai_code_translator/
```

## Model Architecture

The `SimpleEncoderDecoder` model architecture includes:

- **Encoder**: LSTM network to process input sequences
- **Attention Layer**: Helps the model focus on relevant parts of the input
- **Decoder**: LSTM network to generate output sequences
- **Dropout**: Prevents overfitting during training
- **Teacher Forcing**: Improves training stability and convergence

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
