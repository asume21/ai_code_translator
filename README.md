# AI Code Translator Advanced

An advanced code translation tool with LLM integration, Astutely chatbot, and security scanning capabilities.

## Features

- **LLM-Enhanced Translation**: Uses Gemini API for high-quality code translations
- **Astutely Chatbot**: Integrated conversational assistant for code-related questions
- **Security Scanner**: Detects vulnerabilities in your code
- **Multiple Language Support**: Translates between various programming languages
- **Syntax Highlighting**: Professional code display with syntax highlighting
- **Multiple Themes**: Choose between Dark, Light, and Classic themes

## Setup

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/asume21/ai_code_translator.git
   cd ai_code_translator
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your credentials:
   - Copy `config/gemini_credentials_template.json` to `config/gemini_credentials.json`
   - Add your Gemini API key to the file
   ```json
   {
     "api_key": "YOUR_GEMINI_API_KEY_HERE",
     "project_id": "your-project-id",
     "model": "models/gemini-1.5-pro-001"
   }
   ```

   Alternatively, you can set the API key as an environment variable:
   ```
   set GEMINI_API_KEY=your_api_key_here
   ```

### Running the Application

Run the application using the provided batch file:
```
run.bat
```

Or directly with Python:
```
python integrated_gui.py
```

## Usage

### Code Translation

1. Select the source and target languages from the dropdowns
2. Enter or paste your code in the input panel
3. Click "Translate" to convert the code

### Chatbot

1. Switch to the Chatbot tab
2. Type your question or code-related query
3. The Astutely chatbot will respond with helpful information

### Security Scanner

1. Switch to the Security tab
2. Enter or paste the code you want to analyze
3. Click "Scan Code" to detect potential vulnerabilities

## Recent Updates

- Added improved vulnerability scanner with pattern detection for multiple languages
- Integrated Gemini API for enhanced translations and chatbot capabilities
- Added syntax highlighting and theme options
- Improved error handling and user experience

## License

MIT License
