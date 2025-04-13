import logging
from google.generativeai import ChatSession

logger = logging.getLogger(__name__)

class ChatbotInterface:
    def __init__(self, gemini_interface, model="models/gemini-1.5-pro-001"):
        """Initialize the ChatbotInterface.
        
        Args:
            gemini_interface: Instance of GeminiInterface containing the API configuration
            model: Model name to use
        """
        self.gemini_interface = gemini_interface
        self.model = model
        self.chat = None
        self._initialize_chat()
        logger.info(f"Successfully initialized ChatbotInterface with model: {model}")

    def _initialize_chat(self):
        """Initialize the chat session."""
        try:
            self.chat = self.gemini_interface.chat
            if self.chat is None:
                raise ValueError("Chat session not initialized in GeminiInterface")
            logger.info("Chat session initialized")
        except Exception as e:
            logger.error(f"Failed to initialize chat session: {str(e)}")
            raise

    def send_message(self, message):
        """Send a message to the chatbot.
        
        Args:
            message: Message to send
            
        Returns:
            Response text from the chatbot
        """
        try:
            response = self.chat.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise

    def clear_history(self):
        """Clear the chat history."""
        try:
            self.chat = self.gemini_interface.chat
            logger.info("Chat history cleared")
        except Exception as e:
            logger.error(f"Failed to clear chat history: {str(e)}")
            raise

    def get_history(self):
        """Get the current chat history.
        
        Returns:
            List of chat messages
        """
        try:
            return self.chat.history
        except Exception as e:
            logger.error(f"Failed to get chat history: {str(e)}")
            raise
