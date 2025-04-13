"""
Interface for code translation functionality.
"""

from typing import Optional, Dict, Any
from ai_code_translator.gemini_interface import GeminiInterface
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranslatorInterface:
    """Interface for code translation functionality."""
    
    def __init__(self, gemini: GeminiInterface):
        """Initialize the translator interface."""
        self.gemini = gemini
        
    def translate(self, source_code: str, target_language: str) -> Dict[str, Any]:
        """
        Translate source code to target language.
        
        Args:
            source_code: Source code to translate
            target_language: Target language
            
        Returns:
            Dictionary with translation results
        """
        try:
            # Prepare the prompt for translation
            prompt = f"Translate the following code from its original language to {target_language}:\n\n{source_code}\n\nMake sure to maintain the same functionality and style."
            
            # Get the translation from Gemini
            response = self.gemini.chat(prompt)
            
            # Parse the response
            translated_code = response.get('content', '')
            
            return {
                'success': True,
                'translated_code': translated_code,
                'original_code': source_code,
                'target_language': target_language
            }
            
        except Exception as e:
            logger.error(f"Error during translation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
