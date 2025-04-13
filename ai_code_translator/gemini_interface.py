"""
Google Gemini API interface for code translation and chat.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Union
import re
import json
from google.oauth2 import service_account
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GeminiInterface:
    """Interface for Google's Gemini API."""
    
    def __init__(self, api_key: str = None, model: str = "models/gemini-1.5-pro-001", credentials_path: str = None):
        """Initialize the Gemini interface.
        
        Args:
            api_key: Optional Gemini API key
            model: Model name (default: models/gemini-1.5-pro-001)
            credentials_path: Path to service account credentials JSON file
        """
        self.model_name = model
        self.credentials_path = credentials_path
        self.api_key = api_key
        self.model = None
        self.chat = None
        
        try:
            # Initialize Google Generative AI
            if api_key:
                genai.configure(api_key=api_key)
                logger.info("Configured Gemini with API key")
            elif credentials_path and os.path.exists(credentials_path):
                try:
                    with open(credentials_path, 'r') as f:
                        credentials = json.load(f)
                        
                    # Check if this is a service account credentials file
                    if all(key in credentials for key in ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']):
                        credentials = service_account.Credentials.from_service_account_file(
                            credentials_path,
                            scopes=['https://www.googleapis.com/auth/cloud-platform']
                        )
                        genai.configure(credentials=credentials)
                        logger.info("Configured Gemini with service account credentials")
                    else:
                        # Assume it's a simple API key file
                        api_key = credentials.get("api_key")
                        if api_key:
                            genai.configure(api_key=api_key)
                            logger.info("Configured Gemini with API key from file")
                        else:
                            raise ValueError("No API key found in credentials file")
                except Exception as e:
                    logger.error(f"Failed to load credentials from file: {e}")
                    raise
            else:
                raise ValueError("No valid credentials or API key provided")
            
            # Initialize the model
            try:
                self.model = genai.GenerativeModel(model_name=model)
                self.chat = self.model.start_chat(history=[])
                logger.info(f"Successfully initialized Gemini model: {model}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                raise
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini interface: {e}")
            raise
        
    def chat_response(self, message: str) -> str:
        """Get a response from the chat model."""
        try:
            if not self.model:
                raise ValueError("Gemini model not initialized")
                
            response = self.chat.send_message(message)
            return response.text
            
        except Exception as e:
            logger.error(f"Error getting chat response: {e}")
            raise

    def translate_code(self, source_code: str, source_lang: str, target_lang: str) -> str:
        """Translate code between programming languages."""
        try:
            if not self.model:
                raise ValueError("Gemini model not initialized")
                
            prompt = f"Translate this {source_lang} code to {target_lang}:\n\n{source_code}\n\n" \
                    f"Please provide the translated code in {target_lang} format."
            
            response = self.chat.send_message(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error translating code: {e}")
            raise

    def scan_vulnerabilities(self, code: str, language: str) -> list:
        """Scan code for vulnerabilities."""
        try:
            if not self.model:
                raise ValueError("Gemini model not initialized")
                
            prompt = f"Analyze this {language} code for security vulnerabilities:\n\n{code}\n\n" \
                    f"Please provide a list of vulnerabilities with line numbers, severity levels (low, medium, high)," \
                    f"and suggested fixes. Format the response as JSON with these fields: line, severity, description, fix_suggestion."
            
            response = self.chat.send_message(prompt)
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Error scanning vulnerabilities: {e}")
            raise

    def ask_question(self, question: str) -> str:
        """Ask a question to the model."""
        try:
            if not self.model:
                raise ValueError("Gemini model not initialized")
                
            response = self.chat.send_message(question)
            return response.text
            
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            raise

    def analyze_code(self, code: str, lang: str) -> dict:
        """Analyze code for potential improvements and issues."""
        try:
            prompt = f"""Analyze this {lang} code and provide:
            1. Potential improvements
            2. Security concerns
            3. Performance optimizations
            4. Code style suggestions
            
            Code to analyze:
            ```{lang}
            {code}
            ```
            
            Format the response as JSON with these keys:
            improvements, security_issues, performance_tips, style_suggestions"""
            
            response = self.chat.send_message(
                prompt,
                generation_config={
                    "temperature": 0.1,  # Very low temperature for consistent analysis
                    "top_p": 0.95,
                    "max_output_tokens": 2048,
                }
            )
            
            # Parse JSON response
            try:
                return json.loads(response.text)
            except:
                return {
                    "error": "Failed to parse analysis results",
                    "raw_response": response.text
                }
                
        except Exception as e:
            raise Exception(f"Code analysis failed: {str(e)}")
            
    def chat_response_gui(self, message: str) -> str:
        """Generate a chat response."""
        try:
            print(f"DEBUG - GeminiInterface.chat_response called with: {message}")
            response = self.chat.send_message(
                message,
                generation_config={
                    "temperature": 0.9,
                    "top_p": 0.95,
                    "max_output_tokens": 2048,
                }
            )
            
            print(f"DEBUG - Raw response from Gemini: {response}")
            return response.text
            
        except Exception as e:
            print(f"DEBUG - Error in GeminiInterface.chat_response: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"
