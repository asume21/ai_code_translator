@echo off
echo Starting AI Code Translator Advanced Version Final...
echo All features enabled by default!

:: Set the working directory
cd /d "%~dp0"

:: Load the API key from environment variable or credentials file
set "GEMINI_API_KEY=%GEMINI_API_KEY%"
if "%GEMINI_API_KEY%"=="" (
    echo Loading API key from config/gemini_credentials_template.json...
    for /f "tokens=2 delims=:= " %%a in ('findstr /i "api_key" config\gemini_credentials_template.json') do (
        set "GEMINI_API_KEY=%%a"
    )
)

:: Run the application
python integrated_gui.py
