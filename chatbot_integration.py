"""
Chatbot integration for the AI Code Translator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import re
from typing import List, Dict, Optional
import random
import os
import requests
import json

class TranslatorChatbot:
    """A chatbot specialized in code translation."""
    
    def __init__(self, name="Astutely"):
        """Initialize the chatbot with a name and personality."""
        self.name = name
        self.context = []
        
        # Personality traits
        self.personality = {
            "helpful": 0.9,      # Very helpful
            "knowledgeable": 0.8, # Quite knowledgeable about code
            "friendly": 0.9,      # Very friendly
            "patient": 0.9,       # Very patient
            "concise": 0.7        # Moderately concise
        }
        
        # Expanded responses with personality
        self.responses = {
            # Basic interactions
            r".*name.*": [
                f"I'm {self.name}, your code translation assistant! How can I help you today?",
                f"My name is {self.name}. I'm here to help with your code translation needs.",
                f"I go by {self.name}. Nice to meet you! What code would you like to translate?"
            ],
            r".*who.*you.*|.*what.*you.*": [
                f"I'm {self.name}, an AI assistant specialized in translating Python code to JavaScript. I can help you understand the differences between these languages too!",
                f"I'm {self.name}, your friendly code translation companion. I'm designed to help convert Python code to JavaScript and explain the translation process."
            ],
            r".*how.*you.*": [
                "I'm doing well, thanks for asking! Ready to help with your code translation needs.",
                "I'm operating at optimal efficiency and ready to assist with your code translation tasks!"
            ],
            
            # Translation related
            r".*translate.*": [
                "I'd be happy to translate your Python code to JavaScript. Please paste the code you want to translate.",
                "Sure thing! Just share the Python code you want converted to JavaScript, and I'll help you translate it."
            ],
            r".*how.*work.*": [
                "I use a rule-based system to convert Python syntax to JavaScript syntax. I analyze the structure of your Python code and apply transformation rules to generate equivalent JavaScript.",
                "My translation process involves parsing Python code and applying a series of rules to convert it to equivalent JavaScript. I handle functions, loops, conditionals, and more!"
            ],
            
            # Help and features
            r".*help.*": [
                "I can help you translate Python code to JavaScript, explain translations, or answer questions about the differences between these languages. What would you like to know?",
                "I'm here to assist with code translation! I can convert Python to JavaScript, explain how specific constructs are translated, or answer general questions about the languages."
            ],
            r".*explain.*": [
                "I'd be happy to explain! What specific part of the translation would you like me to clarify?",
                "Sure thing! Which aspect of the code translation would you like me to explain in more detail?"
            ],
            r".*feature.*|.*can.*do.*": [
                "I can translate various Python features to JavaScript, including functions, loops, conditionals, variable assignments, and basic data structures. What would you like to translate?",
                "My translation capabilities include handling Python functions, loops, conditionals, variable declarations, and comments. I'm constantly learning to support more complex features!"
            ],
            
            # Pleasantries
            r".*thank.*": [
                "You're welcome! I'm glad I could help. Is there anything else you'd like to translate or discuss?",
                "Happy to assist! If you have any other code to translate or questions about the process, just let me know."
            ],
            r".*hello.*|.*hi.*": [
                f"Hello there! I'm {self.name}, your code translation assistant. How can I help you today?",
                f"Hi! I'm {self.name}. I'm here to help you translate Python code to JavaScript. What would you like to work on?"
            ],
            
            # Default responses
            "default": [
                "I'm not sure I understand. Would you like help translating Python code to JavaScript?",
                "I'm specialized in code translation. Could you clarify what you'd like help with?",
                "I might have missed something. I'm best at helping with Python to JavaScript translation. How can I assist you with that?"
            ]
        }
        
        # Add more sophisticated conversation capabilities
        self.conversation_topics = {
            "python": [
                "Python is a versatile language known for its readability and simplicity. It's great for beginners and experts alike.",
                "Python's indentation-based syntax makes code blocks clear and readable, but it can be a challenge when translating to JavaScript.",
                "Python has a rich ecosystem of libraries and frameworks like Django, Flask, and NumPy that make it powerful for various applications."
            ],
            "javascript": [
                "JavaScript is the language of the web, essential for creating interactive websites and web applications.",
                "JavaScript uses curly braces for code blocks, unlike Python's indentation-based approach.",
                "Modern JavaScript (ES6+) has many features that make it more pleasant to work with, like arrow functions, template literals, and destructuring."
            ],
            "translation": [
                "When translating from Python to JavaScript, we need to handle differences in syntax, data structures, and standard libraries.",
                "One common challenge in translation is converting Python's list comprehensions to JavaScript's array methods.",
                "Python's dictionary operations need to be carefully translated to JavaScript's object manipulation syntax."
            ],
            "programming": [
                "Programming is about solving problems by breaking them down into smaller, manageable pieces.",
                "Good code is not just about functionality, but also readability and maintainability.",
                "Learning multiple programming languages helps you understand different approaches to solving problems."
            ],
            "differences": [
                "Python and JavaScript have several key differences. Python uses indentation for code blocks while JavaScript uses curly braces. Python is often used for backend, data science, and automation, while JavaScript dominates web development. Python has simpler syntax, while JavaScript has more complex event handling and asynchronous features.",
                "The main differences between Python and JavaScript include syntax (indentation vs. braces), typing (Python is strongly typed, JavaScript is loosely typed), and primary use cases (Python for general-purpose programming, data science, and backend; JavaScript for web development).",
                "Python and JavaScript differ in several ways: Python uses indentation for structure while JavaScript uses braces; Python has built-in data structures like tuples and sets that JavaScript lacks; JavaScript has prototypal inheritance while Python uses class-based inheritance; and Python's standard library is more extensive than JavaScript's."
            ]
        }
    
    def get_response(self, message: str) -> str:
        """Generate a response based on the user's message."""
        # Add message to context
        self.context.append({"role": "user", "content": message})
        
        # Check for questions about differences between languages
        difference_patterns = [
            r".*difference.*between.*",
            r".*compare.*",
            r".*versus.*",
            r".*vs\.?.*",
            r".*what.*different.*",
            r".*how.*different.*",
            r".*what.*differences.*"
        ]
        
        for pattern in difference_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                if any(lang in message.lower() for lang in ["python", "javascript", "js"]):
                    response = random.choice(self.conversation_topics["differences"])
                    self.context.append({"role": "assistant", "content": response})
                    return response
        
        # Check for code in the message - only if it has code markers or multiple lines
        if ("```" in message and message.count("\n") > 1) or message.count("\n") > 3:
            response = "I see you've shared some code. Would you like me to translate this from Python to JavaScript?"
            self.context.append({"role": "assistant", "content": response})
            return response
        
        # Check for specific translation request
        if "translate" in message.lower() and len(message.split()) > 5:
            response = "I'd be happy to translate your code. Please share the Python code you want to convert to JavaScript."
            self.context.append({"role": "assistant", "content": response})
            return response
            
        # Handle specific questions about supported languages
        if any(lang in message.lower() for lang in ["java", "c++", "c#", "ruby"]) and "translate" in message.lower():
            response = f"Currently, I'm specialized in translating Python code to JavaScript. I don't support translation to or from other languages like Java, C++, C#, or Ruby yet."
            self.context.append({"role": "assistant", "content": response})
            return response
        
        # Check for conversation topics
        for topic, responses in self.conversation_topics.items():
            if topic in message.lower():
                response = random.choice(responses)
                self.context.append({"role": "assistant", "content": response})
                return response
        
        # Match against predefined patterns
        for pattern, responses in self.responses.items():
            if pattern != "default":
                try:
                    if re.search(pattern, message, re.IGNORECASE):
                        response = random.choice(responses)
                        self.context.append({"role": "assistant", "content": response})
                        return response
                except Exception:
                    # Skip problematic patterns
                    continue
        
        # Check for context and provide a more contextual response
        if len(self.context) >= 4:  # We have at least 2 exchanges
            last_user_msg = self.context[-3]["content"] if len(self.context) >= 3 else ""
            last_bot_msg = self.context[-2]["content"] if len(self.context) >= 2 else ""
            
            # If the last exchange was about translation
            if "translate" in last_user_msg.lower() or "translate" in last_bot_msg.lower():
                response = "To translate Python code to JavaScript, I need to see the code you want to translate. Could you share it with me?"
                self.context.append({"role": "assistant", "content": response})
                return response
            
            # If the last exchange was about how the translator works
            if "how" in last_user_msg.lower() and ("work" in last_user_msg.lower() or "translator" in last_user_msg.lower()):
                response = "My translation process is rule-based. I analyze Python code structure and apply specific rules to convert it to equivalent JavaScript. Would you like to see an example?"
                self.context.append({"role": "assistant", "content": response})
                return response
        
        # Default response
        response = random.choice(self.responses["default"])
        self.context.append({"role": "assistant", "content": response})
        return response
        
    def generate_contextual_response(self, message: str) -> str:
        """Generate a more contextual response based on conversation history."""
        # This would be where a more sophisticated model would analyze the conversation
        # For now, we'll use a simple approach based on keywords and recent context
        
        # Extract recent context (last 3 exchanges)
        recent_context = self.context[-6:] if len(self.context) >= 6 else self.context
        
        # Look for topics in the recent conversation
        topics_mentioned = []
        for entry in recent_context:
            content = entry["content"].lower()
            for topic in self.conversation_topics.keys():
                if topic in content and topic not in topics_mentioned:
                    topics_mentioned.append(topic)
        
        # If we have topics, respond about one of them
        if topics_mentioned:
            topic = random.choice(topics_mentioned)
            return random.choice(self.conversation_topics[topic])
        
        # Fall back to pattern matching
        return None


class AdvancedTranslatorChatbot:
    """A chatbot that uses OpenAI's API for more natural conversations."""
    
    def __init__(self, name="Astutely", api_key=None):
        """Initialize the chatbot with a name and API key."""
        self.name = name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.context = [
            {"role": "system", "content": (
                "You are Astutely, an AI assistant specialized in translating Python code to JavaScript. "
                "You are helpful, knowledgeable, friendly, and patient. "
                "You can explain the differences between Python and JavaScript, "
                "help users understand code translation concepts, "
                "and engage in natural conversations about programming. "
                "When users share code, you can help translate it from Python to JavaScript. "
                "You should only discuss topics related to programming, code translation, "
                "and software development."
            )}
        ]
    
    def get_response(self, message: str) -> str:
        """Generate a response using OpenAI's API."""
        # Add user message to context
        self.context.append({"role": "user", "content": message})
        
        # Check if API key is available
        if not self.api_key:
            response = "I need an API key to access my advanced conversation capabilities. Please set the OPENAI_API_KEY environment variable."
            self.context.append({"role": "assistant", "content": response})
            return response
        
        try:
            # Make API request to OpenAI
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": self.context,
                "max_tokens": 150
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(data)
            )
            
            if response.status_code == 200:
                response_data = response.json()
                assistant_response = response_data["choices"][0]["message"]["content"]
                self.context.append({"role": "assistant", "content": assistant_response})
                return assistant_response
            else:
                # Fallback to basic response if API call fails
                fallback_response = f"I'm having trouble connecting to my knowledge base. Let's stick to basics - I can help translate Python code to JavaScript. Would you like to try that?"
                self.context.append({"role": "assistant", "content": fallback_response})
                return fallback_response
                
        except Exception as e:
            # Fallback to basic response if there's an error
            fallback_response = f"I encountered an error: {str(e)}. I can still help with basic code translation. Would you like to try that?"
            self.context.append({"role": "assistant", "content": fallback_response})
            return fallback_response


class ChatbotPanel:
    """GUI panel for chatbot interaction."""
    
    def __init__(self, parent, translator_callback=None):
        """Initialize the chatbot panel."""
        self.parent = parent
        self.translator_callback = translator_callback
        
        # Try to use the advanced chatbot if API key is available, otherwise use the basic one
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            self.chatbot = AdvancedTranslatorChatbot(api_key=api_key)
            self.using_advanced = True
        else:
            self.chatbot = TranslatorChatbot()
            self.using_advanced = False
        
        # Create the main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        # Create chat display
        self.chat_display = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_display.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
        
        # Create input area
        input_frame = ttk.Frame(self.frame)
        input_frame.grid(row=1, column=0, sticky=tk.EW, padx=5, pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        self.message_input = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=3)
        self.message_input.grid(row=0, column=0, sticky=tk.EW)
        
        # Bind Enter key to send message but allow Shift+Enter for newline
        self.message_input.bind("<Return>", self.on_enter_pressed)
        
        send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_button.grid(row=0, column=1, padx=5)
        
        # Add welcome message
        welcome_message = f"Hello! I'm {self.chatbot.name}, your AI Code Translator assistant. "
        if self.using_advanced:
            welcome_message += "I'm using advanced AI to provide more natural conversations. "
        welcome_message += "I can help you translate Python code to JavaScript and explain the differences between these languages. How can I assist you today?"
        
        self.add_message(f"{self.chatbot.name}", welcome_message)
    
    def add_message(self, sender: str, message: str):
        """Add a message to the chat display."""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def on_enter_pressed(self, event):
        """Handle Enter key press to send message but allow Shift+Enter for newline."""
        # Check if Shift key is pressed
        if event.state & 0x1:  # Shift is pressed
            return  # Allow default behavior (newline)
        
        # Send the message
        self.send_message()
        return "break"  # Prevent default behavior
    
    def send_message(self):
        """Send a message to the chatbot and display the response."""
        message = self.message_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Clear input field
        self.message_input.delete("1.0", tk.END)
        
        # Display user message
        self.add_message("You", message)
        
        # If using advanced chatbot, let it handle all responses
        if self.using_advanced:
            # Check if this is a translation request with code
            has_code = ("```" in message and message.count("\n") > 1) or message.count("\n") > 3
            translation_keywords = ["translate", "convert", "change to javascript", "to js"]
            is_translation_request = any(keyword in message.lower() for keyword in translation_keywords)
            
            if is_translation_request and has_code and self.translator_callback:
                # Extract code between triple backticks if present
                if "```" in message:
                    start = message.find("```") + 3
                    end = message.rfind("```")
                    if start < end:
                        code = message[start:end].strip()
                        self.translator_callback(code)
                        self.add_message(f"{self.chatbot.name}", "I've sent your code to the translator. You can see the results in the Translator tab.")
                        return
                
                # Otherwise use the whole message as potential code
                self.translator_callback(message)
                self.add_message(f"{self.chatbot.name}", "I've sent your message to the translator. You can see the results in the Translator tab.")
                return
            
            # Get response from the advanced chatbot
            response = self.chatbot.get_response(message)
            self.add_message(f"{self.chatbot.name}", response)
            return
        
        # Otherwise, use the original logic for the basic chatbot
        # Check for explicit translation requests
        is_translation_request = False
        
        # Check for keywords that indicate a translation request
        translation_keywords = ["translate", "convert", "change to javascript", "to js"]
        for keyword in translation_keywords:
            if keyword in message.lower():
                is_translation_request = True
                break
        
        # Check for code markers
        has_code = ("```" in message and message.count("\n") > 1) or message.count("\n") > 3
        
        # If it's a translation request with code and we have a callback
        if is_translation_request and has_code and self.translator_callback:
            # Extract code between triple backticks if present
            if "```" in message:
                start = message.find("```") + 3
                end = message.rfind("```")
                if start < end:
                    code = message[start:end].strip()
                    self.translator_callback(code)
                    self.add_message(f"{self.chatbot.name}", "I've sent your code to the translator. You can see the results in the Translator tab.")
                    return
            
            # Otherwise use the whole message as potential code
            self.translator_callback(message)
            self.add_message(f"{self.chatbot.name}", "I've sent your message to the translator. You can see the results in the Translator tab.")
            return
        
        # Handle questions about supported languages
        if any(lang in message.lower() for lang in ["java", "c++", "c#", "ruby"]) and any(word in message.lower() for word in ["translate", "support"]):
            response = "Currently, I'm specialized in translating Python code to JavaScript. I don't support translation to or from other languages like Java, C++, C#, or Ruby yet."
            self.add_message(f"{self.chatbot.name}", response)
            return
            
        # Process general questions about translation
        if "how" in message.lower() and "translator" in message.lower() and "work" in message.lower():
            response = "The translator works by analyzing Python code structure and applying a set of rules to convert it to equivalent JavaScript. It handles functions, loops, conditionals, and basic data structures. Would you like to see an example?"
            self.add_message(f"{self.chatbot.name}", response)
            return
            
        if "do you only translate" in message.lower():
            response = "Yes, currently I only translate from Python to JavaScript. This is my primary function, though I can also explain the differences between these languages and help you understand the translation process."
            self.add_message(f"{self.chatbot.name}", response)
            return
            
        # Handle questions about differences between languages
        difference_patterns = [
            r".*difference.*between.*",
            r".*compare.*",
            r".*versus.*",
            r".*vs\.?.*",
            r".*what.*different.*",
            r".*how.*different.*",
            r".*what.*differences.*"
        ]
        
        for pattern in difference_patterns:
            if re.search(pattern, message, re.IGNORECASE) or (
                message.lower().strip() in ["whats the differences", "what's the differences", "what are the differences"]
            ):
                response = "Python and JavaScript have several key differences:\n\n1. Syntax: Python uses indentation for code blocks while JavaScript uses curly braces {}\n2. Types: Python is strongly typed while JavaScript is loosely typed\n3. Use cases: Python is popular for backend, data science, and automation, while JavaScript dominates web development\n4. Functions: JavaScript has first-class functions and more functional programming features\n5. Concurrency: JavaScript uses event-driven callbacks and promises, while Python has various approaches including async/await\n\nWould you like me to explain any of these differences in more detail?"
                self.add_message(f"{self.chatbot.name}", response)
                return
        
        # Get chatbot response for non-translation requests
        response = self.chatbot.get_response(message)
        self.add_message(f"{self.chatbot.name}", response)
        
        # Make sure the input field is focused and ready for the next message
        self.message_input.focus_set()


def integrate_chatbot(app, root):
    """Integrate the chatbot into the existing application."""
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Add translator tab (existing UI)
    translator_frame = ttk.Frame(notebook)
    notebook.add(translator_frame, text="Translator")
    
    # Move existing UI elements to the translator frame
    for widget in root.winfo_children():
        if widget != notebook:
            widget.pack_forget()
            widget.grid_forget()
            widget.place_forget()
            widget.pack(in_=translator_frame, fill=tk.BOTH, expand=True)
    
    # Add chatbot tab
    chat_frame = ttk.Frame(notebook)
    notebook.add(chat_frame, text="Chatbot")
    
    # Create chatbot panel
    chatbot_panel = ChatbotPanel(chat_frame, translator_callback=app.translate)
    
    return chatbot_panel
