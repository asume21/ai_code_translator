"""
Simple GUI for AI Code Translator that uses only the rule-based translator
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import sys
import os

# Add the parent directory to the path to ensure imports work
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the rule-based translator
from ai_code_translator.final_translator import rule_based_translate
# Import the chatbot integration
from chatbot_integration import ChatbotPanel

class SimpleTranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Code Translator")
        self.root.geometry("1000x700")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create translator tab
        self.translator_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.translator_frame, text="Translator")
        
        # Create chatbot tab
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="Chatbot")
        
        # Initialize the translator UI
        self.init_translator_ui()
        
        # Initialize the chatbot
        self.chatbot = ChatbotPanel(self.chat_frame, translator_callback=self.handle_chat_translation)
    
    def init_translator_ui(self):
        # Create the main frame
        main_frame = ttk.Frame(self.translator_frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the top frame for buttons
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        # Create buttons
        ttk.Button(top_frame, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Save Output", command=self.save_output).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Translate", command=self.translate).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Clear", command=self.clear).pack(side=tk.LEFT, padx=5)
        
        # Create the middle frame for text areas
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Configure grid
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.columnconfigure(1, weight=1)
        middle_frame.rowconfigure(1, weight=1)
        
        # Create labels
        ttk.Label(middle_frame, text="Python Code").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(middle_frame, text="JavaScript Code").grid(row=0, column=1, sticky=tk.W)
        
        # Create text areas
        self.source_text = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD)
        self.source_text.grid(row=1, column=0, sticky=tk.NSEW, padx=5)
        
        self.target_text = scrolledtext.ScrolledText(middle_frame, wrap=tk.WORD)
        self.target_text.grid(row=1, column=1, sticky=tk.NSEW, padx=5)
        
        # Create the status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
    
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    self.source_text.delete(1.0, tk.END)
                    self.source_text.insert(tk.END, file.read())
                self.status_var.set(f"Opened: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def save_output(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".js",
            filetypes=[("JavaScript Files", "*.js"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w') as file:
                    file.write(self.target_text.get(1.0, tk.END))
                self.status_var.set(f"Saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def translate(self):
        source_code = self.source_text.get(1.0, tk.END)
        if not source_code.strip():
            messagebox.showinfo("Info", "Please enter some Python code to translate.")
            return
        
        try:
            self.status_var.set("Translating...")
            self.root.update_idletasks()
            
            # Use the rule-based translator
            translated_code = rule_based_translate(source_code)
            
            self.target_text.delete(1.0, tk.END)
            self.target_text.insert(tk.END, translated_code)
            
            self.status_var.set("Translation complete")
        except Exception as e:
            messagebox.showerror("Error", f"Translation error: {str(e)}")
            self.status_var.set("Translation failed")
    
    def clear(self):
        self.source_text.delete(1.0, tk.END)
        self.target_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
    
    def handle_chat_translation(self, message):
        """Handle translation requests from the chatbot."""
        # Extract code from the message
        code = self.extract_code_from_message(message)
        if code:
            # Switch to translator tab
            self.notebook.select(0)
            
            # Set the code in the source text area
            self.source_text.delete(1.0, tk.END)
            self.source_text.insert(tk.END, code)
            
            # Translate the code
            self.translate()
        else:
            # If no code was found but the message mentions translation
            if "translate" in message.lower():
                # Switch to translator tab anyway
                self.notebook.select(0)
                self.status_var.set("Ready for code translation")
    
    def extract_code_from_message(self, message):
        """Extract code from a chat message."""
        # Look for code blocks with triple backticks
        if "```" in message:
            parts = message.split("```")
            if len(parts) >= 3:
                # Get the content between the first pair of triple backticks
                code = parts[1].strip()
                if code:
                    return code
        
        # If no code blocks with backticks, check if the message itself looks like code
        lines = message.split("\n")
        if len(lines) > 3:
            # Check if it has Python-like syntax
            python_indicators = ["def ", "class ", "import ", "for ", "while ", "if ", "print(", "#", "=", "return "]
            code_line_count = 0
            
            for line in lines:
                if any(indicator in line for indicator in python_indicators):
                    code_line_count += 1
            
            # If at least 30% of lines look like Python code
            if code_line_count >= len(lines) * 0.3:
                return message
        
        return None

def main():
    root = tk.Tk()
    app = SimpleTranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
