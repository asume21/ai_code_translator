# AI Code Translator - Advanced Code Translation System
# Author: [Your Name]
# Version: 2.1
# Date: 2025-02-20

import tkinter as tk
from tkinter import scrolledtext, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import platform
import json
import random
import torch
from .transformer_translator import TransformerTranslator
from .feedback_learner import FeedbackDataset, IncrementalLearner
from .style_handler import StyleConfig
import re

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="code_translator.log"
)
logger = logging.getLogger(__name__)

# Initialize the model
model = TransformerTranslator()

# Define the ChatBot
class ChatBot:
    def __init__(self):
        self.model = self.load_conversational_model()

    def load_conversational_model(self):
        """Load a conversational AI model."""
        # Placeholder for a real model (e.g., GPT or a local LLM)
        return lambda prompt: f"AI: I'm sorry, I don't have a conversational model loaded. You said: {prompt}"

    def chat(self, prompt: str) -> str:
        """Respond to user input."""
        response = self.model(prompt)
        return response

# Define platform-specific examples
platform_specific_examples = {
    ("windows", "linux"):
    {
        "C:\\Users\\John\\file.txt": "/home/john/file.txt",
        "os.system('dir')": "os.system('ls')",
        "%APPDATA%": "$HOME/.config",
    },
    ("linux", "windows"):
    {
        "/home/john/file.txt": "C:\\Users\\John\\file.txt",
        "os.system('ls')": "os.system('dir')",
        "$HOME": "%USERPROFILE%",
    }
}

# Define hardware-specific examples
hardware_specific_examples = {
    ("c", "arm_assembly"):
    {
        "int x = 42;": "MOV R0, #42",
        "int y = x + 1;": "ADD R1, R0, #1",
    },
    ("c", "cuda"):
    {
        "for (int i = 0; i < 10; i++) { x[i] = i; }":
        "__global__ void kernel(int *x) {\n    int i = threadIdx.x;\n    if (i < 10) x[i] = i;\n}"
    },
    ("python", "arduino"):
    {
        "print('Hello, World!')": "Serial.println('Hello, World!');",
    }
}

# Define utility functions
def detect_platform() -> str:
    """Detect the current operating system."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"

def translate_platform_specific_code(code: str, source_platform: str, target_platform: str) -> str:
    """Translate platform-specific code."""
    if not source_platform or not target_platform or source_platform == target_platform:
        return code
    
    # Platform-specific translations
    translations = {
        ("windows", "linux"): {
            r'Process.Start\((.*?)\)': r'subprocess.Popen([\1])',
            r'System.IO.File': r'os.path',
            r'\\\\': r'/',
            r'\\': r'/',
        },
        ("linux", "windows"): {
            r'subprocess.Popen\((.*?)\)': r'Process.Start(\1)',
            r'os.path': r'System.IO.File',
            r'/': r'\\',
        }
    }
    
    if (source_platform, target_platform) in translations:
        rules = translations[(source_platform, target_platform)]
        for pattern, replacement in rules.items():
            code = re.sub(pattern, replacement, code)
    
    return code

def translate_hardware_specific_code(code: str, source_lang: str, target_hardware: str) -> str:
    """Translate code for specific hardware."""
    if not target_hardware:
        return code
    
    # Hardware-specific translations
    translations = {
        "cuda": {
            "python": {
                r'torch\.tensor': r'torch.cuda.tensor',
                r'model\.': r'model.cuda().',
                r'\.to\(device\)': r'.cuda()',
            }
        },
        "arm": {
            "cpp": {
                r'#include\s*<x86intrin.h>': r'#include <arm_neon.h>',
                r'__m256': r'float32x4_t',
                r'_mm256_': r'vld1q_f32',
            }
        }
    }
    
    if target_hardware in translations and source_lang in translations[target_hardware]:
        rules = translations[target_hardware][source_lang]
        for pattern, replacement in rules.items():
            code = re.sub(pattern, replacement, code)
    
    return code

def translate_protocol(data: str, source_protocol: str, target_protocol: str) -> str:
    """Translate data between communication protocols."""
    if not source_protocol or not target_protocol or source_protocol == target_protocol:
        return data
    
    if source_protocol == "json" and target_protocol == "binary":
        # Convert JSON to binary format
        try:
            json_data = json.loads(data)
            return str(json_data).encode('utf-8')
        except:
            return data
    
    elif source_protocol == "binary" and target_protocol == "json":
        # Convert binary to JSON format
        try:
            binary_data = data.encode('utf-8') if isinstance(data, str) else data
            return json.dumps(binary_data.decode('utf-8'))
        except:
            return data
    
    return data

def translate_code_full(source_code: str, source_lang: str, target_lang: str,
                       source_platform: str = None, target_platform: str = None,
                       target_hardware: str = None, source_protocol: str = None,
                       target_protocol: str = None) -> str:
    """Translate code with optional platform, hardware, and protocol awareness."""
    try:
        # Basic language translation
        translated_code = model.translate(source_code, source_lang=source_lang, target_lang=target_lang)
        
        # Platform-specific translation
        if source_platform and target_platform:
            translated_code = translate_platform_specific_code(translated_code, source_platform, target_platform)
        
        # Hardware-specific translation
        if target_hardware:
            translated_code = translate_hardware_specific_code(translated_code, target_lang, target_hardware)
        
        # Protocol translation
        if source_protocol and target_protocol:
            translated_code = translate_protocol(translated_code, source_protocol, target_protocol)
        
        return translated_code
    
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise

# Define the GUI
class CodeTranslatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Code Translator")
        self.root.geometry("1200x800")
        self.style = ttk.Style(theme="cyborg")

        # Initialize feedback learner
        self.feedback_dataset = FeedbackDataset()
        self.incremental_learner = IncrementalLearner(model, self.feedback_dataset)
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=BOTH, expand=YES)

        # Input fields
        self.source_code_label = ttk.Label(self.main_frame, text="Source Code:", font=("Helvetica", 12, "bold"))
        self.source_code_label.pack(pady=5, anchor=tk.W)

        self.source_code_input = scrolledtext.ScrolledText(self.main_frame, width=120, height=10, font=("Courier", 10))
        self.source_code_input.pack(pady=10, fill=BOTH, expand=YES)

        # Dropdowns for languages
        self.options_frame = ttk.Frame(self.main_frame)
        self.options_frame.pack(fill=tk.X, pady=10)

        self.source_lang_label = ttk.Label(self.options_frame, text="Source Language:", font=("Helvetica", 10))
        self.source_lang_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_lang_dropdown = ttk.Combobox(self.options_frame, values=["python", "javascript", "java", "cpp", "ruby", "go", "typescript", "tensorflow", "paddle"], font=("Helvetica", 10))
        self.source_lang_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        self.target_lang_label = ttk.Label(self.options_frame, text="Target Language:", font=("Helvetica", 10))
        self.target_lang_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.target_lang_dropdown = ttk.Combobox(self.options_frame, values=["python", "javascript", "java", "cpp", "ruby", "go", "typescript", "tensorflow", "paddle"], font=("Helvetica", 10))
        self.target_lang_dropdown.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

        # Optional fields (platform, hardware, protocol)
        self.optional_frame = ttk.Frame(self.main_frame)
        self.optional_frame.pack(fill=tk.X, pady=10)

        self.source_platform_label = ttk.Label(self.optional_frame, text="Source Platform (optional):")
        self.source_platform_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_platform_dropdown = ttk.Combobox(self.optional_frame, values=["", "windows", "linux", "macos"], font=("Helvetica", 10))
        self.source_platform_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        self.target_platform_label = ttk.Label(self.optional_frame, text="Target Platform (optional):")
        self.target_platform_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.target_platform_dropdown = ttk.Combobox(self.optional_frame, values=["", "windows", "linux", "macos"], font=("Helvetica", 10))
        self.target_platform_dropdown.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

        self.target_hardware_label = ttk.Label(self.optional_frame, text="Target Hardware (optional):")
        self.target_hardware_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.target_hardware_dropdown = ttk.Combobox(self.optional_frame, values=["", "arm", "x86", "cuda", "arduino", "fpga"], font=("Helvetica", 10))
        self.target_hardware_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        self.source_protocol_label = ttk.Label(self.optional_frame, text="Source Protocol (optional):")
        self.source_protocol_label.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.source_protocol_dropdown = ttk.Combobox(self.optional_frame, values=["", "json", "binary"], font=("Helvetica", 10))
        self.source_protocol_dropdown.grid(row=1, column=3, padx=5, pady=5, sticky=tk.EW)

        self.target_protocol_label = ttk.Label(self.optional_frame, text="Target Protocol (optional):")
        self.target_protocol_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.target_protocol_dropdown = ttk.Combobox(self.optional_frame, values=["", "json", "binary"], font=("Helvetica", 10))
        self.target_protocol_dropdown.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        # Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)

        self.translate_button = ttk.Button(self.button_frame, text="Translate", command=self.translate_code, bootstyle=SUCCESS)
        self.translate_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.refresh_button = ttk.Button(self.button_frame, text="Refresh", command=self.refresh_code, bootstyle=INFO)
        self.refresh_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        self.feedback_button = ttk.Button(self.button_frame, text="Submit Correction", command=self.submit_feedback, bootstyle=WARNING)
        self.feedback_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # Output area
        self.output_label = ttk.Label(self.main_frame, text="Output:", font=("Helvetica", 12, "bold"))
        self.output_label.pack(pady=5, anchor=tk.W)

        self.output_area = scrolledtext.ScrolledText(self.main_frame, width=120, height=15, font=("Courier", 10))
        self.output_area.pack(pady=10, fill=BOTH, expand=True)
        self.output_area.tag_configure('bold_underline', font=('Courier', 10, 'bold', 'underline'))

        # Autoscroll configuration
        self.output_area.yview_moveto(1.0)

    def submit_feedback(self):
        """Handle user feedback for translation correction."""
        source_code = self.source_code_input.get("1.0", tk.END).strip()
        source_lang = self.source_lang_dropdown.get()
        target_lang = self.target_lang_dropdown.get()
        
        if not source_code or not source_lang or not target_lang:
            messagebox.showerror("Error", "Please provide source code and select languages.")
            return
        
        # Get the original translation
        original_translation = self.output_area.get("1.0", tk.END).strip()
        
        # Open a dialog for corrected translation
        corrected_translation = tk.simpledialog.askstring(
            "Submit Correction",
            "Please enter the corrected translation:",
            initialvalue=original_translation
        )
        
        if corrected_translation:
            # Add feedback to dataset
            self.feedback_dataset.add_feedback(
                source_code=source_code,
                original_translation=original_translation,
                corrected_translation=corrected_translation,
                source_lang=source_lang,
                target_lang=target_lang
            )
            
            # Train on feedback
            loss = self.incremental_learner.train_on_feedback()
            messagebox.showinfo("Success", f"Thank you for your feedback! Loss: {loss:.4f}")

    def translate_code(self):
        """Handle the translate button click with feedback tracking."""
        source_code = self.source_code_input.get("1.0", tk.END).strip()
        source_lang = self.source_lang_dropdown.get()
        target_lang = self.target_lang_dropdown.get()
        source_platform = self.source_platform_dropdown.get()
        target_platform = self.target_platform_dropdown.get()
        target_hardware = self.target_hardware_dropdown.get()
        source_protocol = self.source_protocol_dropdown.get()
        target_protocol = self.target_protocol_dropdown.get()
        
        if not source_code or not source_lang or not target_lang:
            messagebox.showerror("Error", "Please provide source code and select languages.")
            return
        
        try:
            # Translate code
            translated_code = translate_code_full(
                source_code,
                source_lang,
                target_lang,
                source_platform,
                target_platform,
                target_hardware,
                source_protocol,
                target_protocol
            )
            
            # Display translation
            self.output_area.delete("1.0", tk.END)
            self.output_area.insert(tk.END, translated_code)
            
        except Exception as e:
            messagebox.showerror("Error", f"Translation failed: {str(e)}")

    def refresh_code(self):
        """Clear the source code input area."""
        self.source_code_input.delete("1.0", tk.END)
        self.output_area.delete("1.0", tk.END)

def run_gui():
    """Run the GUI application."""
    root = tk.Tk()
    app = CodeTranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()