"""
Chatbot integration for the AI Code Translator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import re
from typing import List, Dict, Optional
import random

class TranslatorChatbot:
    """Chatbot with personality for the AI Code Translator."""
    
    def __init__(self):
        """Initialize the chatbot with personality and predefined responses."""
        self.context = []
        
        # Chatbot personality
        self.name = "Astutely"
        self.personality = {
            "traits": ["helpful", "knowledgeable", "friendly", "patient"],
            "background": "I was created to help programmers translate Python code to JavaScript and explain the differences between the languages.",
            "interests": ["code translation", "programming languages", "helping developers"],
            "speaking_style": "professional but friendly"
        }
        
        # Expanded responses with personality
        self.responses = {
            # Basic interactions
            r"(?i).*name.*": [
                f"I'm {self.name}, your code translation assistant! How can I help you today?",
                f"My name is {self.name}. I'm here to help with your code translation needs.",
                f"I go by {self.name}. Nice to meet you! What code would you like to translate?"
            ],
            r"(?i).*who.*you.*|(?i).*what.*you.*": [
                f"I'm {self.name}, an AI assistant specialized in translating Python code to JavaScript. I can help you understand the differences between these languages too!",
                f"I'm {self.name}, your friendly code translation companion. I'm designed to help convert Python code to JavaScript and explain the translation process."
            ],
            r"(?i).*how.*you.*": [
                "I'm doing well, thanks for asking! Ready to help with your code translation needs.",
                "I'm operating at optimal efficiency and ready to assist with your code translation tasks!"
            ],
            
            # Translation related
            r"(?i).*translate.*": [
                "I'd be happy to translate your Python code to JavaScript. Please paste the code you want to translate.",
                "Sure thing! Just share the Python code you want converted to JavaScript, and I'll help you translate it."
            ],
            r"(?i).*how.*work.*": [
                "I use a rule-based system to convert Python syntax to JavaScript syntax. I analyze the structure of your Python code and apply transformation rules to generate equivalent JavaScript.",
                "My translation process involves parsing Python code and applying a series of rules to convert it to equivalent JavaScript. I handle functions, loops, conditionals, and more!"
            ],
            
            # Help and features
            r"(?i).*help.*": [
                "I can help you translate Python code to JavaScript, explain translations, or answer questions about the differences between these languages. What would you like to know?",
                "I'm here to assist with code translation! I can convert Python to JavaScript, explain how specific constructs are translated, or answer general questions about the languages."
            ],
            r"(?i).*explain.*": [
                "I'd be happy to explain! What specific part of the translation would you like me to clarify?",
                "Sure thing! Which aspect of the code translation would you like me to explain in more detail?"
            ],
            r"(?i).*feature.*|(?i).*can.*do.*": [
                "I can translate various Python features to JavaScript, including functions, loops, conditionals, variable assignments, and basic data structures. What would you like to translate?",
                "My translation capabilities include handling Python functions, loops, conditionals, variable declarations, and comments. I'm constantly learning to support more complex features!"
            ],
            
            # Pleasantries
            r"(?i).*thank.*": [
                "You're welcome! I'm glad I could help. Is there anything else you'd like to translate or discuss?",
                "Happy to assist! If you have any other code to translate or questions about the process, just let me know."
            ],
            r"(?i).*hello.*|(?i).*hi.*": [
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
    
    def get_response(self, message: str) -> str:
        """Generate a response based on the user's message."""
        # Add message to context
        self.context.append({"role": "user", "content": message})
        
        # Check for code in the message
        if "```" in message or message.count("\n") > 2:
            response = "I see you've shared some code. Would you like me to translate this from Python to JavaScript?"
            self.context.append({"role": "assistant", "content": response})
            return response
        
        # Match against predefined patterns
        for pattern, responses in self.responses.items():
            if pattern != "default" and re.match(pattern, message):
                response = random.choice(responses)
                self.context.append({"role": "assistant", "content": response})
                return response
        
        # Default response
        response = random.choice(self.responses["default"])
        self.context.append({"role": "assistant", "content": response})
        return response


class ChatbotPanel:
    """GUI panel for chatbot interaction."""
    
    def __init__(self, parent, translator_callback=None):
        """Initialize the chatbot panel."""
        self.parent = parent
        self.translator_callback = translator_callback
        self.chatbot = TranslatorChatbot()
        
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
        self.add_message(f"{self.chatbot.name}", f"Hello! I'm {self.chatbot.name}, your AI Code Translator assistant. I can help you translate Python code to JavaScript and explain the differences between these languages. How can I assist you today?")
    
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
        
        # Check for code translation request
        if "translate" in message.lower() and len(message.split()) > 3:
            # Extract code if present
            if self.translator_callback:
                self.translator_callback(message)
                self.add_message(f"{self.chatbot.name}", "I've sent your code to the translator. You can see the results in the Translator tab.")
            else:
                self.add_message(f"{self.chatbot.name}", "Translation feature is not available.")
        else:
            # Get chatbot response
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
