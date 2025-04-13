@echo off
echo Please enter your Gemini API key (from Google Cloud Console):
set /p API_KEY="API Key: "

:: Set as environment variable
echo Setting GEMINI_API_KEY environment variable...
setx GEMINI_API_KEY "%API_KEY%"

:: Update credentials.json
echo Updating credentials.json...
echo {"api_key": "%API_KEY%"} > credentials.json

:: Make sure the file has proper UTF-8 encoding
powershell -Command "[IO.File]::WriteAllText('credentials.json', (Get-Content 'credentials.json' -Raw), [System.Text.Encoding]::UTF8)"

echo API key setup complete! You can now run the AI Code Translator.
pause
