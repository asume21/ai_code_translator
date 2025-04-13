from integrated_ai import IntegratedTranslatorAI
import logging
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api():
    try:
        # Initialize the AI with Gemini
        ai = IntegratedTranslatorAI()
        
        # Test the API connection
        logger.info("Testing API connection...")
        if ai.test_api_connection():
            logger.info("API connection successful!")
            
            # Test translation
            logger.info("Testing code translation...")
            result = ai.translate_code("print('Hello World')", "javascript")
            logger.info(f"Translation result: {result}")
            
            # Test chat
            logger.info("Testing chat functionality...")
            response = ai.chat("What is the purpose of this AI Code Translator?")
            logger.info(f"Chat response: {response}")
            
            logger.info("All tests completed successfully!")
            return True
        else:
            logger.error("API connection failed")
            return False
    except Exception as e:
        logger.error(f"Error during API test: {str(e)}")
        return False

if __name__ == "__main__":
    test_api()
