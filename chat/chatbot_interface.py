"""
Interface for the chatbot functionality.
"""

import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChatbotInterface:
    """Interface for the chatbot functionality."""
    
    def __init__(self, gemini_interface):
        """Initialize the chatbot interface.
        
        Args:
            gemini_interface: The Gemini interface for chat functionality
        """
        self.gemini = gemini_interface
        self.conversation_history = []
        logger.info("Chatbot interface initialized")
        
        # Set up initial conversation context
        self._setup_initial_context()
        
    def _setup_initial_context(self):
        """Set up the initial conversation context for the chatbot."""
        self.conversation_history.append({
            "role": "system",
            "content": """
            You are Astutely, an AI code translator and assistant. 
            Your main role is to help users translate code between programming languages and answer code-related questions.
            
            Key characteristics:
            - Friendly and helpful personality
            - Expert in multiple programming languages
            - Can translate code while maintaining functionality
            - Provides explanations for code changes
            - Maintains conversation context
            - Can analyze and suggest improvements to code
            
            When translating code:
            1. Maintain the same functionality
            2. Use idiomatic patterns of the target language
            3. Add comments to explain significant changes
            4. Provide explanations for the translation
            
            When answering questions:
            1. Be concise but thorough
            2. Provide code examples when relevant
            3. Explain concepts clearly
            4. Maintain a friendly and professional tone
            """
        })
        logger.info("Chatbot context initialized")
        
    def get_response(self, user_message: str) -> str:
        """
        Get a response from the chatbot.
        
        Args:
            user_message: The user's message
            
        Returns:
            The chatbot's response
        """
        try:
            if not self.gemini:
                raise ValueError("Gemini interface not initialized")
                
            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Get response from Gemini
            response = self.gemini.chat_response(user_message)
            
            # Add AI response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting chat response: {e}")
            raise
            
    def clear_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []
        self._setup_initial_context()
        logger.info("Conversation history cleared")
        
    def get_conversation_history(self) -> list:
        """Get the current conversation history."""
        return self.conversation_history.copy()
        
    def translate_code(self, code: str, source_lang: str, target_lang: str) -> str:
        """
        Translate code using the chatbot.
        
        Args:
            code: The code to translate
            source_lang: The source language
            target_lang: The target language
            
        Returns:
            The translated code
        """
        try:
            prompt = f"""Translate this {source_lang} code to {target_lang}:
            
            {code}
            
            Please provide the translated code in {target_lang} format."""
            
            return self.get_response(prompt)
            
        except Exception as e:
            logger.error(f"Error translating code: {e}")
            raise
            
    def analyze_code(self, code: str, language: str) -> str:
        """
        Analyze code for potential issues and improvements.
        
        Args:
            code: The code to analyze
            language: The programming language
            
        Returns:
            Analysis results and suggestions
        """
        try:
            prompt = f"""Analyze this {language} code for potential issues and improvements:
            
            {code}
            
            Please provide:
            1. Code quality assessment
            2. Potential improvements
            3. Security concerns
            4. Performance suggestions"""
            
            return self.get_response(prompt)
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            raise
            
    def explain_code(self, code: str, language: str) -> str:
        """
        Explain what the code does.
        
        Args:
            code: The code to explain
            language: The programming language
            
        Returns:
            Explanation of the code
        """
        try:
            prompt = f"""Explain what this {language} code does:
            
            {code}
            
            Please provide:
            1. What the code does
            2. How it works
            3. Key concepts used
            4. Common use cases"""
            
            return self.get_response(prompt)
            
        except Exception as e:
            logger.error(f"Error explaining code: {e}")
            raise
