"""
Integrated AI for code translation and chat.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Union
from ai_code_translator.inference import translate_code as rule_based_translate
from ai_code_translator.gemini_interface import GeminiInterface
from ai_code_translator.chatbot_interface import ChatbotInterface
import json
import datetime
import sys
import google.generativeai as genai
from security.vulnerability_scanner import VulnerabilityScanner
from security.vulnerability_scanner_interface import VulnerabilityScannerInterface
from ai_code_translator.translator_interface import TranslatorInterface
import pathlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PremiumManager:
    """Manages premium features and licensing."""
    
    def __init__(self):
        """Initialize the premium manager."""
        self.premium_status = False
        self.license_info = None
        self.license_key = None
        self._load_license()
    
    def is_premium(self) -> bool:
        """Check if premium features are enabled."""
        return self.premium_status and self.license_key is not None
    
    def get_license_info(self) -> dict:
        """Get license information."""
        return self.license_info or {}
    
    def get_license_key(self) -> str:
        """Get the current license key."""
        return self.license_key or ""
    
    def _load_license(self):
        """Load license information from file."""
        try:
            license_file = os.path.join(os.path.dirname(__file__), "license.json")
            if os.path.exists(license_file):
                with open(license_file, "r") as f:
                    data = json.load(f)
                    self.license_info = data
                    self.license_key = data.get("key")
                    self.premium_status = data.get("status", False)
            else:
                logger.warning("No license file found. Running in basic mode.")
        except Exception as e:
            logger.error(f"Error loading license: {str(e)}")
    
    def show_upgrade_dialog(self):
        """Show the upgrade dialog."""
        # Implementation for showing upgrade dialog
        pass
    
    def _activate_premium(self, dialog):
        """Activate premium features."""
        try:
            # Validate and activate license
            if dialog and hasattr(dialog, "license_key"):
                self.license_key = dialog.license_key.get()
                # Save license info
                license_data = {
                    "key": self.license_key,
                    "status": True,
                    "activation_date": datetime.datetime.now().isoformat()
                }
                with open(os.path.join(os.path.dirname(__file__), "license.json"), "w") as f:
                    json.dump(license_data, f)
                self.premium_status = True
                self.license_info = license_data
                logger.info("Premium features activated successfully")
                return True
        except Exception as e:
            logger.error(f"Error activating premium features: {str(e)}")
        return False

class IntegratedTranslatorAI:
    def __init__(self, credentials_path: str = None, model_name: str = "models/gemini-1.5-pro-001"):
        """Initialize the IntegratedTranslatorAI.
        
        Args:
            credentials_path: Path to service account credentials JSON file
            model_name: Gemini model to use
        """
        self.credentials_path = credentials_path
        self.model_name = model_name
        self.gemini = None
        self.vulnerability_scanner = None
        self.vulnerability_scanner_interface = None
        
        try:
            # Initialize Gemini interface
            if credentials_path and os.path.exists(credentials_path):
                with open(credentials_path, 'r') as f:
                    credentials = json.load(f)
                    api_key = credentials.get("api_key")
                    if not api_key:
                        raise ValueError("No API key found in credentials file")
                    
                    self.gemini = GeminiInterface(
                        api_key=api_key,
                        model=model_name,
                        credentials_path=credentials_path
                    )
                    logger.info(f"Successfully initialized Gemini interface with model: {model_name}")
            else:
                raise ValueError("No valid credentials file found")
                
            # Initialize vulnerability scanner
            try:
                self.vulnerability_scanner = VulnerabilityScanner(
                    credentials_path=credentials_path
                )
                self.vulnerability_scanner_interface = VulnerabilityScannerInterface(
                    vulnerability_scanner=self.vulnerability_scanner
                )
                logger.info("Successfully initialized vulnerability scanner")
            except Exception as e:
                logger.warning(f"Failed to initialize vulnerability scanner: {e}")
                self.vulnerability_scanner = None
                self.vulnerability_scanner_interface = None
                
        except Exception as e:
            logger.error(f"Failed to initialize IntegratedTranslatorAI: {e}")
            raise
        
        # Initialize the chatbot
        self.chatbot = ChatbotInterface(self.gemini)
        
        # Initialize the translator
        self.translator = TranslatorInterface(self.gemini)
        
        # Initialize components
        self.rule_based_translator = None
        self.neural_translator = None
        self.llm_interface = None
        
        # Initialize premium manager
        self.premium_manager = PremiumManager()
        
    async def scan_code(self, code: str, language: str) -> List[Dict[str, Any]]:
        """
        Scan code for vulnerabilities.
        
        Args:
            code: Source code to scan
            language: Programming language of the code
            
        Returns:
            List of detected vulnerabilities
        """
        if not self.vulnerability_scanner:
            logger.warning("Vulnerability scanner not initialized")
            return []
            
        try:
            vulnerabilities = await self.vulnerability_scanner.scan_code(code, language)
            return [
                {
                    "line": vuln.line_number,
                    "category": vuln.category,
                    "severity": vuln.severity.value,
                    "description": vuln.description,
                    "code": vuln.code_snippet,
                    "fix": vuln.fix_suggestion,
                    "confidence": vuln.confidence
                }
                for vuln in vulnerabilities
            ]
        except Exception as e:
            logger.error(f"Error scanning code: {str(e)}")
            return []
    
    def use_gemini_model(self, model_name: str = "models/gemini-1.5-pro-001") -> bool:
        """
        Switch to using Gemini model for LLM capabilities.
        
        Args:
            model_name: Name of the Gemini model to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the existing Gemini interface
            self.gemini.model_name = model_name
            
            # Reinitialize the model with new settings
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM",
                },
            ]
            
            # Reinitialize the Gemini model
            self.gemini.model = genai.GenerativeModel(
                model=model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Restart the chat session
            self.gemini.chat = self.gemini.model.start_chat(history=[])
            
            # Update the chatbot with the new model
            self.chatbot = ChatbotInterface(self.gemini)
            
            logger.info(f"Successfully switched to model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to switch model: {str(e)}")
            return False

    def test_api_connection(self):
        """Test the Gemini API connection."""
        try:
            # Test the model by sending a simple request
            test_prompt = "Hello, how are you?"
            response = self.gemini.generate(test_prompt)
            
            if response:
                logger.info("API connection test successful")
                return True
            else:
                raise Exception("No response from API")
                
        except Exception as e:
            logger.error(f"API test failed: {str(e)}")
            return False

    def _initialize_chatbot(self):
        """Initialize or update the chatbot with the current LLM interface."""
        from ai_code_translator.chatbot import Chatbot
        
        # Determine which LLM interface to use
        llm_interface = self.gemini_interface
            
        # Initialize or update the chatbot
        if not hasattr(self, 'chatbot') or self.chatbot is None:
            self.chatbot = Chatbot(
                model_path=None,
                llm_interface=llm_interface
            )
        else:
            # Update the existing chatbot with the new LLM interface
            self.chatbot.llm_interface = llm_interface
    
    def get_current_provider(self) -> str:
        """
        Get the current LLM provider.
        
        Returns:
            "gemini" or "none"
        """
        if self.llm_interface == self.gemini_interface:
            return "gemini"
        else:
            return "none"
    
    def translate_code(self, source_code: str, source_lang: str, target_lang: str) -> str:
        """Translate code between programming languages."""
        try:
            if not self.gemini:
                raise ValueError("Gemini interface not initialized")
                
            prompt = f"Translate this {source_lang} code to {target_lang}:\n\n{source_code}\n\n" \
                    f"Please provide the translated code in {target_lang} format."
            
            response = self.gemini.chat_response(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error translating code: {e}")
            raise

    def chat_response(self, message: str) -> str:
        """Get a response from the chatbot."""
        try:
            if not self.gemini:
                raise ValueError("Gemini interface not initialized")
                
            response = self.gemini.chat_response(message)
            return response
            
        except Exception as e:
            logger.error(f"Error getting chat response: {e}")
            raise

    def scan_vulnerabilities(self, code: str, language: str) -> list:
        """Scan code for vulnerabilities."""
        try:
            if not self.gemini:
                raise ValueError("Gemini interface not initialized")
                
            prompt = f"Analyze this {language} code for security vulnerabilities:\n\n{code}\n\n" \
                    f"Please provide a list of vulnerabilities with line numbers, severity levels (low, medium, high)," \
                    f"and suggested fixes. Format the response as JSON with these fields: line, severity, description, fix_suggestion."
            
            response = self.gemini.chat_response(prompt)
            vulnerabilities = json.loads(response)
            return vulnerabilities
            
        except Exception as e:
            logger.error(f"Error scanning vulnerabilities: {e}")
            raise

    def ask_question(self, question: str) -> str:
        """Ask a question to the AI."""
        try:
            if not self.gemini:
                raise ValueError("Gemini interface not initialized")
                
            response = self.gemini.chat_response(question)
            return response
            
        except Exception as e:
            logger.error(f"Error asking question: {e}")
            raise

    def use_gemini_model(self, model_name: str):
        """Switch to a different Gemini model."""
        try:
            if not self.gemini:
                raise ValueError("Gemini interface not initialized")
                
            self.gemini.model_name = model_name
            self.gemini.model = genai.GenerativeModel(model_name=model_name)
            logger.info(f"Switched to Gemini model: {model_name}")
            
        except Exception as e:
            logger.error(f"Error switching model: {e}")
            raise

    def _validate_translation(
        self,
        source_code: str,
        translated_code: str,
        source_lang: str,
        target_lang: str
    ) -> None:
        """
        Validate the translation result.
        
        Args:
            source_code: Original source code
            translated_code: Translated code
            source_lang: Source language
            target_lang: Target language
        """
        # TO DO: Implement validation logic
        pass
    
    def _code_sanity_check(self, code: str, lang: str) -> bool:
        """
        Perform a basic sanity check on the code.
        
        Args:
            code: Code to check
            lang: Language of the code
            
        Returns:
            True if the code passes the sanity check, False otherwise
        """
        # TO DO: Implement sanity check logic
        return True
    
    def get_translation_feedback(
        self,
        source_code: str,
        translated_code: str,
        source_lang: str = "python",
        target_lang: str = "javascript"
    ) -> str:
        """
        Get feedback on a code translation.
        
        Args:
            source_code: Original source code
            translated_code: Translated code
            source_lang: Source language
            target_lang: Target language
            
        Returns:
            Feedback on the translation
        """
        try:
            if self.gemini_interface:
                # Use Gemini for feedback
                return self.gemini_interface.get_translation_feedback(
                    source_code=source_code,
                    translated_code=translated_code,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
            else:
                return "LLM service not available for translation feedback."
        except Exception as e:
            logger.error(f"Failed to get translation feedback: {e}")
            return f"Failed to get translation feedback: {str(e)}"
    
    def chat(self, message: str) -> str:
        """
        Chat with the AI assistant.
        
        Args:
            message: User message
            
        Returns:
            Assistant's response
        """
        print(f"DEBUG - IntegratedTranslatorAI.chat called with message: {message}")
        
        # Add message to conversation history
        if not hasattr(self, 'conversation_history') or self.conversation_history is None:
            self.conversation_history = []
        self.conversation_history.append({"role": "user", "content": message})
        
        # Simple direct approach to ensure functionality
        try:
            # Use the chat session directly if available
            if hasattr(self, 'chat_session') and self.chat_session:
                print("DEBUG - Using self.chat_session directly")
                response = self.chat_session.send_message(message)
                response_text = response.text
                print(f"DEBUG - Chat session response: {response_text[:100]}...")
            # Fallback to direct model if chat session not available
            elif hasattr(self, 'model') and self.model:
                print("DEBUG - Using self.model directly")
                response = self.model.generate_content(
                    f"""You are Astutely, a helpful and friendly AI code translation assistant.
                    
                    User message: {message}
                    """,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    }
                )
                response_text = response.text
                print(f"DEBUG - Direct model response: {response_text[:100]}...")
            else:
                print("DEBUG - No model available")
                response_text = "I'm sorry, I don't have a language model available to chat with you."
        except Exception as e:
            print(f"DEBUG - Error in chat: {str(e)}")
            response_text = f"I apologize, but I encountered an error: {str(e)}"
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        return response_text
    
    def chat_response(self, message: str) -> str:
        """Generate a response to a chat message."""
        try:
            if self.gemini.model:
                response = self.gemini.model.generate_content(
                    f"""You are Astutely, a helpful and friendly AI code translation assistant.
                    
                    User message: {message}
                    """,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    }
                )
                response_text = response.text
                print(f"DEBUG - Direct model response: {response_text[:100]}...")
            else:
                print("DEBUG - No model available")
                response_text = "I'm sorry, I don't have a language model available to chat with you."
        except Exception as e:
            print(f"DEBUG - Error in chat: {str(e)}")
            response_text = f"I apologize, but I encountered an error: {str(e)}"
        
        return response_text
    
    def clear_conversation_history(self):
        """Clear conversation history."""
        if hasattr(self, 'conversation_history'):
            self.conversation_history = []
        return "Conversation history cleared."


if __name__ == "__main__":
    # Example usage
    credentials_path = os.environ.get("GEMINI_CREDENTIALS_PATH", "credentials.json")
    model_name = "models/gemini-1.5-pro-001"
    
    try:
        ai = IntegratedTranslatorAI(credentials_path=credentials_path, model_name=model_name)
        
        # Example chat
        response = ai.chatbot.chat_response("Translate this Python code to JavaScript:\n\nprint('Hello, World!')")
        print(f"Response: {response}")
        
    except Exception as e:
        logger.error(f"Error running example: {str(e)}")
