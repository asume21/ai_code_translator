"""
Integrated GUI for AI Code Translator with LLM Integration and Premium Features

This module provides a GUI that integrates the chatbot, translator, and vulnerability scanner
into a single, seamless interface powered by the IntegratedTranslatorAI.
"""

import os
import sys
import json
import logging
import platform
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import re
import webbrowser
import time
import subprocess
import traceback
import argparse
import pathlib
from pathlib import Path
import pygments
import jsonschema
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import scrolledtext, messagebox
import tkinter as tk
import asyncio

# AI imports
from integrated_ai import IntegratedTranslatorAI
from ai_code_translator.chatbot_interface import ChatbotInterface
from security.vulnerability_scanner import VulnerabilityScanner
from security.vulnerability_scanner_interface import VulnerabilityScannerInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Theme settings
THEMES = {
    "Dark": "darkly",
    "Light": "cosmo",
    "Classic": "default"
}

class IntegratedTranslatorGUI:
    """Main GUI class for the AI Code Translator."""

    def _on_closing(self):
        """Handle window closing."""
        if Messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

    def _on_theme_changed(self, event):
        """Handle theme changes."""
        new_theme = self.theme_var.get()
        self.style.theme_use(THEMES[new_theme])
        self.current_theme = new_theme
        self.theme_indicator.config(text=f"Theme: {new_theme}")

    def _on_tab_changed(self, event):
        """Handle tab changes."""
        pass  # Add any tab-specific initialization here if needed

    def __init__(self, gemini_api_key=None, gemini_model="models/gemini-1.5-pro-001", enable_premium=False, enable_security=True):
        """Initialize the integrated translator GUI."""
        try:
            # Initialize root window with ttkbootstrap style
            self.style = tb.Style(theme="darkly")
            self.root = self.style.master  # Use the master window from style
            self.root.title("AI Code Translator Advanced")
            self.root.geometry("1200x800")
            
            # Initialize variables
            self.font_size = 10  # Default font size
            self.current_theme = "Dark"  # Default theme
            self.gemini_api_key = gemini_api_key
            self.gemini_model = gemini_model  # Initialize model variable early
            self.enable_premium = enable_premium
            self.enable_security = enable_security
            self.current_file = None
            
            # Initialize theme variable
            self.theme_var = tk.StringVar(value=self.current_theme)
            
            # Initialize AI components
            self.ai_interface = IntegratedTranslatorAI(
                credentials_path="config/gemini_credentials_template.json",
                model_name=gemini_model
            )
            
            # Initialize language settings
            self.source_lang = "Python"
            self.target_lang = "JavaScript"
            self.scan_lang = "Python"
            
            # Initialize status bar variables
            self.status_var = tk.StringVar(value="Ready")
            
            # Initialize file handling methods
            self._add_file_handling_methods()
            
            # Create menu bar
            self._create_menu_bar()
            
            # Create notebook for tabs
            self.notebook = tb.Notebook(self.root)
            self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create tabs and their widgets
            self._create_translator_tab()
            self._create_chatbot_tab()
            self._create_vulnerability_scanner_tab()
            
            # Initialize vulnerability scanner
            try:
                self.vulnerability_scanner = VulnerabilityScanner(
                    credentials_path="credentials.json"
                )
                self.vulnerability_scanner_interface = VulnerabilityScannerInterface(
                    vulnerability_scanner=self.vulnerability_scanner
                )
            except Exception as e:
                logger.error(f"Failed to initialize vulnerability scanner: {e}")
                self.vulnerability_scanner = None
                self.vulnerability_scanner_interface = None
            
            # Initialize chatbot
            if self.ai_interface and self.ai_interface.gemini:
                self.chatbot = ChatbotInterface(self.ai_interface.gemini)
            else:
                self.chatbot = None
            
            # Configure styles after widgets are created
            self._configure_styles()
            
            # Initialize status bar after all widgets are created
            self._create_status_bar()
            
            # Load settings
            self._load_settings()
            
            # Set up keyboard shortcuts
            self._setup_keyboard_shortcuts()
            
            # Bind events
            self.root.bind("<<NotebookTabChanged>>", self._on_tab_changed)
            self.root.bind("<Configure>", self._on_theme_changed)
            
            # Start main loop
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            traceback.print_exc()
            if hasattr(self, 'root'):
                self.root.destroy()
            sys.exit(1)

    def _add_file_handling_methods(self):
        """Add file handling methods to the class."""
        def open_file(self):
            """Open a file for translation."""
            try:
                # Use ttkbootstrap's file dialog
                file_path = tb.filedialog.askopenfilename(
                    title="Open File",
                    filetypes=[
                        ("Python Files", "*.py"),
                        ("JavaScript Files", "*.js"),
                        ("Java Files", "*.java"),
                        ("C++ Files", "*.cpp"),
                        ("C# Files", "*.cs"),
                        ("Go Files", "*.go"),
                        ("Ruby Files", "*.rb"),
                        ("PHP Files", "*.php"),
                        ("Swift Files", "*.swift"),
                        ("Kotlin Files", "*.kt"),
                        ("All Files", "*.*")
                    ]
                )
                
                if file_path:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        code = file.read()
                        
                    # Get language from file extension
                    lang_map = {
                        '.py': 'Python',
                        '.js': 'JavaScript',
                        '.java': 'Java',
                        '.cpp': 'C++',
                        '.cs': 'C#',
                        '.go': 'Go',
                        '.rb': 'Ruby',
                        '.php': 'PHP',
                        '.swift': 'Swift',
                        '.kt': 'Kotlin'
                    }
                    
                    # Set appropriate tab based on language
                    if file_path.lower().endswith('.py'):
                        self.notebook.select(0)  # Translator tab
                        self.source_text.delete(1.0, 'end')
                        self.source_text.insert(1.0, code)
                        self.source_lang_var.set('Python')
                    else:
                        self.notebook.select(2)  # Scanner tab
                        self.scan_text.delete(1.0, 'end')
                        self.scan_text.insert(1.0, code)
                        self.scan_lang_var.set(lang_map.get(os.path.splitext(file_path)[1].lower(), 'Python'))
                        
                    self.current_file = file_path
                    self.root.title(f"AI Code Translator - {os.path.basename(file_path)}")
                    
            except Exception as e:
                self._show_error(f"Error opening file: {str(e)}")

        def save_file(self):
            """Save the current code to a file."""
            try:
                if not self.current_file:
                    # If no file is open, use save as
                    file_path = tb.filedialog.asksaveasfilename(
                        title="Save File",
                        defaultextension=".py",
                        filetypes=[
                            ("Python Files", "*.py"),
                            ("JavaScript Files", "*.js"),
                            ("Java Files", "*.java"),
                            ("C++ Files", "*.cpp"),
                            ("C# Files", "*.cs"),
                            ("Go Files", "*.go"),
                            ("Ruby Files", "*.rb"),
                            ("PHP Files", "*.php"),
                            ("Swift Files", "*.swift"),
                            ("Kotlin Files", "*.kt"),
                            ("All Files", "*.*")
                        ]
                    )
                else:
                    file_path = self.current_file

                if file_path:
                    # Get current code based on active tab
                    if self.notebook.index("current") == 0:  # Translator tab
                        code = self.target_text.get(1.0, 'end')
                    else:  # Scanner tab
                        code = self.scan_text.get(1.0, 'end')

                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(code)
                    
                    self.current_file = file_path
                    self.root.title(f"AI Code Translator - {os.path.basename(file_path)}")
                    
            except Exception as e:
                self._show_error(f"Error saving file: {str(e)}")

        def save_as_file(self):
            """Save the current code to a new file."""
            self.current_file = None
            self.save_file()

        def _select_all(self):
            """Select all text in the current text widget."""
            try:
                widget = self.root.focus_get()
                if isinstance(widget, tk.Text):
                    widget.tag_add(tk.SEL, "1.0", 'end')
                    widget.mark_set(tk.INSERT, "1.0")
                    widget.see(tk.INSERT)
            except:
                pass

        # Add methods to class
        self.open_file = open_file.__get__(self)
        self.save_file = save_file.__get__(self)
        self.save_as_file = save_as_file.__get__(self)
        self._select_all = _select_all.__get__(self)

    def _create_menu_bar(self):
        """Create the menu bar."""
        # Create menubar using ttkbootstrap
        menubar = tb.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.root.quit)
        
        # Edit menu
        edit_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all)
        edit_menu.add_separator()
        edit_menu.add_command(label="Increase Font Size", accelerator="Ctrl++", command=lambda: self._change_font_size(1))
        edit_menu.add_command(label="Decrease Font Size", accelerator="Ctrl+-", command=lambda: self._change_font_size(-1))
        
        # View menu
        view_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Theme", command=self._change_theme)
        
        # Help menu
        help_menu = tb.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", accelerator="F1", command=self._show_about)
        
    def _initialize_ai_components(self):
        """Initialize the AI interface."""
        try:
            if self.ai_interface:
                self.ai_interface.use_gemini_model(self.gemini_model)
                logger.info(f"AI initialized with model: {self.gemini_model}")
            else:
                logger.warning("AI interface not initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI: {e}")

    def _configure_styles(self):
        """Configure ttkbootstrap styles"""
        # Configure main window style
        self.style.configure("TFrame", background=self.style.colors.bg)
        self.style.configure("TLabel", font=("Segoe UI", 10))
        
        # Configure button styles
        self.style.configure("primary.TButton", font=("Segoe UI", 10))
        self.style.configure("secondary.TButton", font=("Segoe UI", 10))
        self.style.configure("success.TButton", font=("Segoe UI", 10))
        self.style.configure("danger.TButton", font=("Segoe UI", 10))
        
        # Configure treeview style
        self.style.configure("Treeview", font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        
        # Configure text widget fonts using tkinter's native styling
        for widget in [self.source_text, self.target_text, self.chat_text, self.scan_text, self.scan_results]:
            widget.configure(font=("Courier New", self.font_size))

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-t>", lambda e: self.translate_code())
        self.root.bind("<F1>", lambda e: self._show_about())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-plus>", lambda e: self._change_font_size(1))
        self.root.bind("<Control-minus>", lambda e: self._change_font_size(-1))
        
    def prompt_for_api_key(self):
        """Prompt the user for their API key."""
        try:
            # Create dialog using ttkbootstrap
            dialog = tb.Toplevel(self.root)
            dialog.title("Gemini API Key Required")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create dialog content
            frame = tb.Frame(dialog)
            frame.pack(padx=20, pady=20, fill=BOTH, expand=True)
            
            tb.Label(frame, text="Enter your Gemini API Key:").pack(pady=(0, 10))
            
            key_entry = tb.Entry(frame, show="*", width=50)
            key_entry.pack(pady=(0, 20))
            key_entry.focus()
            
            # Create buttons
            button_frame = tb.Frame(frame)
            button_frame.pack(pady=(10, 0))
            
            tb.Button(
                button_frame,
                text="Enter API Key",
                command=lambda: self._save_api_key(key_entry.get(), dialog)
            ).pack(side=LEFT, padx=(0, 10))
            
            tb.Button(
                button_frame,
                text="Enter Demo Mode",
                command=lambda: self._enter_demo_mode(dialog)
            ).pack(side=LEFT)
            
            # Wait for dialog
            dialog.wait_window()
            
        except Exception as e:
            logger.error(f"Error in prompt_for_api_key: {str(e)}")
            Messagebox.show_error(f"Error: {str(e)}", title="Error")

    def _enter_demo_mode(self, dialog):
        """Enter demo mode with a mock API key."""
        # This is a mock key for demo purposes only
        mock_key = "DEMO_MODE_NO_REAL_API_ACCESS"
        self._mock_ai_interface()
        dialog.destroy()
        self.status_var.set("Running in demo mode - limited functionality")
        self.api_status.config(text="API: Demo Mode")
        
    def _mock_ai_interface(self):
        """Create a mock AI interface for demo purposes."""
        self.ai_interface = type('MockAI', (), {
            'translate_code': lambda source_code, target_language, use_neural=False, use_llm=False: 
                f"// Translated to {target_language}\n// DEMO MODE - NO ACTUAL TRANSLATION\n\n{source_code}",
            'chat': lambda message: "This is demo mode. Please enter a valid API key for full functionality.",
            'scan_vulnerabilities': lambda code, language: {
                'vulnerabilities': [
                    {
                        'severity': 'high',
                        'type': 'Demo Vulnerability',
                        'description': 'This is a demo vulnerability for testing purposes.',
                        'line': 1,
                        'fix': 'This is demo mode. Please enter a valid API key for actual vulnerability scanning.'
                    }
                ],
                'summary': 'Demo scan completed. Please enter a valid API key for actual vulnerability scanning.'
            }
        })()
        
    def _save_api_key(self, api_key: str, dialog: tb.Toplevel):
        """Save the API key and initialize AI."""
        if not api_key:
            Messagebox.showwarning("Invalid Key", "Please enter a valid API key.")
            return
            
        try:
            # Save API key
            self.gemini_api_key = api_key
            
            # Initialize AI
            self._initialize_ai_components()
            
            if self.ai_interface:
                Messagebox.showinfo("Success", "API key saved successfully!")
                dialog.destroy()
            else:
                Messagebox.showerror("Error", "Failed to initialize AI with the provided key.")
                
        except Exception as e:
            Messagebox.showerror("Error", f"Failed to save API key: {str(e)}")
            
    def _show_error(self, message):
        """Show an error message in a dialog."""
        # Use tkinter's messagebox since ttkbootstrap doesn't have it
        mb = tk.messagebox
        mb.showerror("Error", message)

    def _setup_translator_tab(self):
        """Set up the translator tab UI"""
        main_frame = tb.Frame(self.translator_tab)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Model selection frame
        model_frame = tb.LabelFrame(main_frame, text="Model Selection", padding=10)
        model_frame.pack(fill=X, pady=(0, 15))

        tb.Label(model_frame, text="Model:").pack(side=LEFT, padx=(0, 5))
        self.model_var = "models/gemini-1.5-pro-001"  
        model_combo = tb.Combobox(
            model_frame,
            values=["models/gemini-1.5-pro-001"],
            state="readonly",
            width=15
        )
        model_combo.set(self.model_var)
        model_combo.pack(side=LEFT)
        model_combo.bind('<<ComboboxSelected>>', self.on_model_change)

        # Language selection frame
        lang_frame = tb.LabelFrame(main_frame, text="Languages", padding=10)
        lang_frame.pack(fill=X, pady=(0, 15))

        # Source language
        source_frame = tb.Frame(lang_frame)
        source_frame.pack(side=LEFT, padx=(0, 10))

        tb.Label(source_frame, text="Source:").pack(side=LEFT, padx=(0, 5))
        source_combo = tb.Combobox(
            source_frame,
            values=["Python", "JavaScript", "Java", "C++", "PHP"],
            state="readonly",
            width=15
        )
        source_combo.set("Python")
        source_combo.pack(side=LEFT)

        # Target language
        target_frame = tb.Frame(lang_frame)
        target_frame.pack(side=LEFT)

        tb.Label(target_frame, text="Target:").pack(side=LEFT, padx=(0, 5))
        target_combo = tb.Combobox(
            target_frame,
            values=["Python", "JavaScript", "Java", "C++", "PHP"],
            state="readonly",
            width=15
        )
        target_combo.set("JavaScript")
        target_combo.pack(side=LEFT)

        # Code editors
        editor_frame = tb.Frame(main_frame)
        editor_frame.pack(fill=BOTH, expand=True, pady=(10, 0))

        # Source code editor
        source_frame = tb.LabelFrame(editor_frame, text="Source Code", padding=5)
        source_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        self.source_text = scrolledtext.ScrolledText(source_frame, height=20, width=50, font=("Courier New", self.font_size))
        self.source_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Target code editor
        target_frame = tb.LabelFrame(editor_frame, text="Translated Code", padding=5)
        target_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.target_text = scrolledtext.ScrolledText(target_frame, height=20, width=50, font=("Courier New", self.font_size))
        self.target_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Button frame
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))

        tb.Button(
            button_frame,
            text="Translate",
            bootstyle="primary",
            command=self.translate_code
        ).pack(side=LEFT, padx=5)

        tb.Button(
            button_frame,
            text="Clear",
            bootstyle="secondary",
            command=self.new_file
        ).pack(side=LEFT, padx=5)

    def on_model_change(self, event):
        """Handle model selection changes."""
        new_model = self.model_var.get()
        if new_model != self.gemini_model:
            self.gemini_model = new_model
            self.model_indicator.config(text=f"Model: {new_model}")
            self._initialize_ai_components()
            self.status_var.set(f"Model changed to {new_model}")

    def _create_translator_tab(self):
        """Create the translator tab with text widgets."""
        translator_frame = tb.Frame(self.notebook)
        self.notebook.add(translator_frame, text="Translator")
        
        # Create source text widget
        source_frame = tb.LabelFrame(translator_frame, text="Source Code", padding=5)
        source_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        
        self.source_text = scrolledtext.ScrolledText(source_frame, height=20, width=50)
        self.source_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Create target text widget
        target_frame = tb.LabelFrame(translator_frame, text="Target Code", padding=5)
        target_frame.pack(side=LEFT, fill=BOTH, expand=True)
        
        self.target_text = scrolledtext.ScrolledText(target_frame, height=20, width=50)
        self.target_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Create language selection frame
        lang_frame = tb.Frame(translator_frame)
        lang_frame.pack(fill=X, padx=5, pady=5)
        
        # Source language selection
        source_lang_label = tb.Label(lang_frame, text="Source Language:")
        source_lang_label.pack(side=LEFT, padx=5)
        
        self.source_lang_var = tk.StringVar(value="Python")
        source_lang_menu = tb.Menubutton(
            lang_frame,
            textvariable=self.source_lang_var,
            bootstyle="secondary"
        )
        source_lang_menu.menu = tk.Menu(source_lang_menu, tearoff=0)
        source_lang_menu["menu"] = source_lang_menu.menu
        
        for lang in ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "Swift", "Kotlin"]:
            source_lang_menu.menu.add_radiobutton(
                label=lang,
                variable=self.source_lang_var,
                value=lang
            )
        source_lang_menu.pack(side=LEFT, padx=5)
        
        # Target language selection
        target_lang_label = tb.Label(lang_frame, text="Target Language:")
        target_lang_label.pack(side=LEFT, padx=5)
        
        self.target_lang_var = tk.StringVar(value="JavaScript")
        target_lang_menu = tb.Menubutton(
            lang_frame,
            textvariable=self.target_lang_var,
            bootstyle="secondary"
        )
        target_lang_menu.menu = tk.Menu(target_lang_menu, tearoff=0)
        target_lang_menu["menu"] = target_lang_menu.menu
        
        for lang in ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "Swift", "Kotlin"]:
            target_lang_menu.menu.add_radiobutton(
                label=lang,
                variable=self.target_lang_var,
                value=lang
            )
        target_lang_menu.pack(side=LEFT, padx=5)
        
        # Create translate button
        translate_frame = tb.Frame(translator_frame)
        translate_frame.pack(fill=X, padx=5, pady=5)
        
        self.translate_button = tb.Button(
            translate_frame,
            text="Translate",
            command=self.translate_code,
            bootstyle="primary"
        )
        self.translate_button.pack(side=LEFT, padx=5)

    def translate_code(self):
        """Translate code from source to target language."""
        if not self.ai_interface:
            self._show_error("AI interface not initialized")
            return

        try:
            source_code = self.source_text.get(1.0, tk.END).strip()
            if not source_code:
                self._show_error("No source code to translate")
                return

            source_lang = self.source_lang_var.get()
            target_lang = self.target_lang_var.get()
            
            if source_lang == target_lang:
                self._show_error("Source and target languages must be different")
                return

            self.translate_button.configure(state=tb.DISABLED)
            self.source_text.configure(state='disabled')
            
            try:
                # Translate the code
                translated_code = self.ai_interface.translate_code(
                    source_code,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                
                # Update target text
                self.target_text.delete(1.0, tk.END)
                self.target_text.insert(tk.END, translated_code)
                
            finally:
                # Re-enable widgets
                self.translate_button.configure(state=tb.NORMAL)
                self.source_text.configure(state='normal')

        except Exception as e:
            self._show_error(f"Error translating code: {str(e)}")
            self.translate_button.configure(state=tb.NORMAL)
            self.source_text.configure(state='normal')

    def _setup_chatbot_tab(self):
        """Create the chatbot tab with text widget."""
        chatbot_frame = tb.Frame(self.notebook)
        self.notebook.add(chatbot_frame, text="Chatbot")
        
        # Create chat text widget
        self.chat_text = scrolledtext.ScrolledText(chatbot_frame, height=20, width=50)
        self.chat_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
        self.chat_text.configure(state='disabled')
        
        # Create message entry frame
        message_frame = tb.Frame(chatbot_frame)
        message_frame.pack(fill=X, padx=5, pady=5)
        
        # Create message entry
        self.message_entry = tb.Entry(message_frame, width=50)
        self.message_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        # Create send button
        self.send_button = tb.Button(message_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=LEFT, padx=5)
        
        # Bind Enter key to send message
        self.message_entry.bind('<Return>', self.send_message)

    def _create_chatbot_tab(self):
        """Create the chatbot tab with text widget."""
        chatbot_frame = tb.Frame(self.notebook)
        self.notebook.add(chatbot_frame, text="Chatbot")
        
        # Create chat text widget
        chat_frame = tb.Frame(chatbot_frame)
        chat_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=20, width=50)
        self.chat_text.pack(fill=BOTH, expand=True)
        self.chat_text.configure(state='disabled')
        
        # Create message entry frame
        message_frame = tb.Frame(chatbot_frame)
        message_frame.pack(fill=X, padx=5, pady=5)
        
        # Create message entry
        self.message_entry = tb.Entry(message_frame, width=50)
        self.message_entry.pack(side=LEFT, fill=X, expand=True, padx=5)
        
        # Create send button
        self.send_button = tb.Button(
            message_frame,
            text="Send",
            command=self.send_message,
            bootstyle="primary"
        )
        self.send_button.pack(side=LEFT, padx=5)
        
        # Bind Enter key to send message
        self.message_entry.bind('<Return>', self.send_message)

    def send_message(self, event=None):
        """Handle sending a message to the chatbot."""
        if not self.chatbot:
            self._show_error("Chatbot is not initialized")
            return

        message = self.message_entry.get().strip()
        if not message:
            return

        self.message_entry.delete(0, tk.END)
        
        # Add user message to chat
        self.chat_text.configure(state='normal')
        self.chat_text.insert(tk.END, f"You: {message}\n\n")
        self.chat_text.configure(state='disabled')
        
        try:
            # Get response from chatbot
            response = self.chatbot.send_message(message)
            
            # Add chatbot response
            self.chat_text.configure(state='normal')
            self.chat_text.insert(tk.END, f"Astutely: {response}\n\n")
            self.chat_text.configure(state='disabled')
            
            # Scroll to bottom
            self.chat_text.see(tk.END)
            
        except Exception as e:
            self._show_error(f"Error sending message: {str(e)}")

    async def scan_code_for_vulnerabilities(self):
        """Scan code for security vulnerabilities."""
        print("DEBUG: scan_code_for_vulnerabilities called") # DEBUG
        if not self.vulnerability_scanner_interface:
            self._show_error("Vulnerability scanner is not initialized")
            print("DEBUG: Scanner not initialized, returning") # DEBUG
            return

        try:
            code = self.scan_text.get(1.0, tk.END).strip()
            print(f"DEBUG: Code to scan (first 100 chars): {code[:100]}...") # DEBUG
            if not code:
                self._show_error("No code to scan")
                print("DEBUG: No code to scan, returning") # DEBUG
                return

            print("DEBUG: Disabling widgets") # DEBUG
            self.scan_button.configure(state=tb.DISABLED)
            self.scan_text.configure(state='disabled')
            self.scan_results.configure(state='normal')
            self.scan_results.delete(1.0, tk.END)
            self.scan_results.insert(tk.END, "Scanning code...\n")
            self.scan_results.configure(state='disabled')
            self.root.update_idletasks() # Force GUI update
            
            try:
                # Get the selected language from the dropdown
                language = self.scan_lang_var.get()
                print(f"DEBUG: Selected language: {language}") # DEBUG
                
                # Scan the code
                print("DEBUG: Calling vulnerability_scanner_interface.scan_code") # DEBUG
                results = await self.vulnerability_scanner_interface.scan_code(code, language)
                print(f"DEBUG: Scan results received: {results}") # DEBUG
                
                # Show results
                print("DEBUG: Updating results widget") # DEBUG
                self.scan_results.configure(state='normal')
                self.scan_results.delete(1.0, tk.END)
                self.scan_results.insert(tk.END, results if results else "No vulnerabilities found or scanner returned empty.")
                self.scan_results.configure(state='disabled')
                print("DEBUG: Results widget updated") # DEBUG
                
            finally:
                # Re-enable widgets
                print("DEBUG: Re-enabling widgets in finally block") # DEBUG
                self.scan_button.configure(state=tb.NORMAL)
                self.scan_text.configure(state='normal')

        except Exception as e:
            print(f"DEBUG: Exception caught: {e}") # DEBUG
            self._show_error(f"Error scanning code: {str(e)}")
            # Ensure widgets are re-enabled even on error
            try:
                 self.scan_button.configure(state=tb.NORMAL)
                 self.scan_text.configure(state='normal')
            except tk.TclError:
                 print("DEBUG: Widgets might already be destroyed on error exit")

    def _create_vulnerability_scanner_tab(self):
        """Create the vulnerability scanner tab with text widget."""
        scanner_frame = tb.Frame(self.notebook)
        self.notebook.add(scanner_frame, text="Security")
        
        # Create language selection frame
        lang_frame = tb.Frame(scanner_frame)
        lang_frame.pack(fill=X, padx=5, pady=5)
        
        # Language selection
        lang_label = tb.Label(lang_frame, text="Language:")
        lang_label.pack(side=LEFT, padx=5)
        
        self.scan_lang_var = tk.StringVar(value="Python")
        lang_menu = tb.Menubutton(
            lang_frame,
            textvariable=self.scan_lang_var,
            bootstyle="secondary"
        )
        lang_menu.menu = tk.Menu(lang_menu, tearoff=0)
        lang_menu["menu"] = lang_menu.menu
        
        for lang in ["Python", "JavaScript", "Java", "C++", "C#", "Go", "Ruby", "PHP", "Swift", "Kotlin"]:
            lang_menu.menu.add_radiobutton(
                label=lang,
                variable=self.scan_lang_var,
                value=lang
            )
        lang_menu.pack(side=LEFT, padx=5)
        
        # Create input/output frame
        io_frame = tb.Frame(scanner_frame)
        io_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Create input text widget
        input_frame = tb.LabelFrame(io_frame, text="Input Code", padding=5)
        input_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        self.scan_text = scrolledtext.ScrolledText(input_frame, height=20, width=40)
        self.scan_text.pack(fill=BOTH, expand=True)
        
        # Create output text widget
        output_frame = tb.LabelFrame(io_frame, text="Scan Results", padding=5)
        output_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        self.scan_results = scrolledtext.ScrolledText(output_frame, height=20, width=40)
        self.scan_results.pack(fill=BOTH, expand=True)
        
        # Create button frame
        button_frame = tb.Frame(scanner_frame)
        button_frame.pack(fill=X, padx=5, pady=5)
        
        # Create scan button
        self.scan_button = tb.Button(
            button_frame,
            text="Scan Code",
            command=lambda: asyncio.run(self.scan_code_for_vulnerabilities()),
            bootstyle="primary"
        )
        self.scan_button.pack(side=LEFT, padx=5)

        # Create example code button
        example_button = tb.Button(
            button_frame,
            text="Load Example",
            command=lambda: self.load_example_code(self.scan_lang_var.get()),
            bootstyle="secondary"
        )
        example_button.pack(side=LEFT, padx=5)

    def load_example_code(self, language="Python"):
        """Load example vulnerable code for demonstration."""
        try:
            example_code = """
            // Example vulnerable code in selected language
            """
            
            if language == "Python":
                example_code = """
                def read_file(filename):
                    with open(filename, 'r') as f:
                        return f.read()
                
                def main():
                    data = read_file('secret.txt')
                    print(f"Secret data: {data}")
                
                if __name__ == "__main__":
                    main()
                """
            elif language == "JavaScript":
                example_code = """
                function login(username, password) {
                    if (username === "admin" && password === "admin123") {
                        return true;
                    }
                    return false;
                }
                """
            elif language == "Java":
                example_code = """
                import java.io.FileInputStream;
                import java.io.IOException;
                
                public class FileReader {
                    public static void main(String[] args) {
                        try {
                            FileInputStream fis = new FileInputStream("secret.txt");
                            int content;
                            while ((content = fis.read()) != -1) {
                                System.out.print((char) content);
                            }
                            fis.close();
                        } catch (IOException e) {
                            System.out.println("Error reading file");
                        }
                    }
                }
                """
            elif language == "C++":
                example_code = """
                #include <iostream>
                #include <fstream>
                
                int main() {
                    std::ifstream file("secret.txt");
                    std::string line;
                    while (getline(file, line)) {
                        std::cout << line << std::endl;
                    }
                    return 0;
                }
                """
            elif language == "C#":
                example_code = """
                using System;
                using System.IO;
                
                class Program {
                    static void Main() {
                        string path = "secret.txt";
                        string content = File.ReadAllText(path);
                        Console.WriteLine(content);
                    }
                }
                """
            elif language == "Go":
                example_code = """
                package main
                
                import (
                    "fmt"
                    "os"
                )
                
                func main() {
                    data, err := os.ReadFile("secret.txt")
                    if err != nil {
                        fmt.Println("Error reading file")
                        return
                    }
                    fmt.Println(string(data))
                }
                """
            elif language == "Ruby":
                example_code = """
                def read_secret
                    file = File.open("secret.txt")
                    secret = file.read
                    puts secret
                end
                
                read_secret
                """
            elif language == "PHP":
                example_code = """
                <?php
                $filename = 'secret.txt';
                $content = file_get_contents($filename);
                echo $content;
                ?>
                """
            elif language == "Swift":
                example_code = """
                import Foundation
                
                let path = "secret.txt"
                do {
                    let content = try String(contentsOfFile: path)
                    print(content)
                } catch {
                    print("Error reading file")
                }
                """
            elif language == "Kotlin":
                example_code = """
                fun main() {
                    val path = "secret.txt"
                    val content = File(path).readText()
                    println(content)
                }
                """
            
            self.scan_text.configure(state='normal')
            self.scan_text.delete(1.0, tk.END)
            self.scan_text.insert(tk.END, example_code)
            self.scan_text.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load example code: {str(e)}")

    def show_vulnerability_details(self):
        """Show details for the selected vulnerability."""
        # Get selected item
        selected = self.results_tree.focus()
        if not selected:
            Messagebox.showinfo("No Selection", "Please select a vulnerability first.")
            return
            
        # Get vulnerability info
        values = self.results_tree.item(selected, 'values')
        if not values or len(values) < 4:
            return
            
        line_num, severity, category, description = values
        
        # Create details dialog
        details_dialog = tb.Toplevel(self.root)
        details_dialog.title("Vulnerability Details")
        details_dialog.geometry("600x400")
        details_dialog.resizable(True, True)
        details_dialog.transient(self.root)
        details_dialog.grab_set()
        
        # Center the dialog
        details_dialog.update_idletasks()
        width = details_dialog.winfo_width()
        height = details_dialog.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        details_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create main frame
        content_frame = tb.Frame(details_dialog, padding=20)
        content_frame.pack(fill=BOTH, expand=True)
        
        # Vulnerability info
        tb.Label(
            content_frame, 
            text=f"Severity: {severity}",
            font=("Helvetica", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))
        
        tb.Label(
            content_frame, 
            text=f"Line: {line_num}",
            font=("Helvetica", 11)
        ).pack(anchor=tk.W, pady=(0, 5))
        
        tb.Label(
            content_frame, 
            text="Description:",
            font=("Helvetica", 11, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))
        
        desc_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            width=70,
            height=6,
            font=("Helvetica", 10)
        )
        desc_text.pack(fill=tk.X, pady=(0, 10))
        desc_text.insert(tk.END, description)
        desc_text.configure(state="disabled")
        
        # Code snippet
        tb.Label(
            content_frame, 
            text="Code Snippet:",
            font=("Helvetica", 11, "bold")
        ).pack(anchor=tk.W, pady=(10, 5))
        
        # Get the code around the vulnerability
        code = self.scan_text.get(1.0, 'end').split("\n")
        line_idx = int(line_num) - 1
        
        start_line = max(0, line_idx - 2)
        end_line = min(len(code) - 1, line_idx + 2)
        
        snippet = "\n".join([
            f"{i+1}: {line}" for i, line in enumerate(code[start_line:end_line+1], start=start_line)
        ])
        
        snippet_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            width=70,
            height=6,
            font=("Courier New", 10)
        )
        snippet_text.pack(fill=tk.X, pady=(0, 10))
        snippet_text.insert(tk.END, snippet)
        
        # Highlight the vulnerable line
        snippet_text.tag_configure("highlight", background="#ffe0e0")
        
        # Calculate line position in the snippet
        vuln_line_pos = f"{line_idx+1}: "
        start_pos = snippet.find(vuln_line_pos)
        if start_pos >= 0:
            end_pos = snippet.find("\n", start_pos)
            if end_pos < 0:
                end_pos = len(snippet)
            
            # Convert character positions to Tkinter text positions
            start_idx = "1.0 + %d chars" % start_pos
            end_idx = "1.0 + %d chars" % end_pos
            
            snippet_text.tag_add("highlight", start_idx, end_idx)
        
        snippet_text.configure(state="disabled")
        
        # Action buttons
        button_frame = tb.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        tb.Button(
            button_frame,
            text="Fix This Vulnerability",
            command=lambda: self.fix_vulnerability(selected, details_dialog)
        ).pack(side=tk.LEFT)
        
        tb.Button(
            button_frame,
            text="Close",
            command=details_dialog.destroy
        ).pack(side=tk.RIGHT)
        
        # Make dialog modal
        details_dialog.transient(self.root)
        details_dialog.grab_set()
        
    def fix_selected_vulnerability(self):
        """Fix the selected vulnerability."""
        item = self.results_tree.focus()
        if not item:
            Messagebox.showinfo("No Selection", "Please select a vulnerability to fix.")
            return
            
        self.fix_vulnerability(item)
        
    def fix_vulnerability(self, item, dialog=None):
        """Fix a specific vulnerability."""
        # Get vulnerability info
        values = self.results_tree.item(item, 'values')
        if not values:
            return
            
        line_num, severity, category, description = values
        
        # Get the code
        code = self.scan_text.get(1.0, 'end')
        language = self.scan_lang
        
        # Request fix from AI
        try:
            # Set status
            self.status_var.set("Generating fix recommendation...")
            # Use the AI to generate a fix
            if hasattr(self, 'ai_interface') and self.ai_interface:
                prompt = f"""I have a {language} code with a {severity.lower()} severity vulnerability on line {line_num}. 
                The issue is: {description}
                
                Here's the code:
                ```{language.lower()}
                {code}
                ```
                
                Please provide a fixed version of this specific vulnerability, explaining the security issue and showing the corrected code. 
                Focus only on fixing this one vulnerability.
                """
                
                # Get the fix
                fix_result = self.ai_interface.ask_question(prompt)
                
                # Show the fix dialog
                self.show_fix_dialog(code, fix_result, line_num, severity, description)
                
                # Close the details dialog if it exists
                if dialog:
                    dialog.destroy()
            else:
                Messagebox.showerror("AI Not Available", "AI assistant is not available. Please check your API key.")
                
        except Exception as e:
            Messagebox.showerror("Fix Error", f"Error generating fix: {str(e)}")
            
        finally:
            self.status_var.set("Ready")
            
    def show_fix_dialog(self, original_code, fix_result, line_num, severity, description):
        """Show dialog with the suggested fix."""
        fix_dialog = tb.Toplevel(self.root)
        fix_dialog.title(f"Fix for {severity} Vulnerability")
        fix_dialog.geometry("800x600")
        fix_dialog.resizable(True, True)
        fix_dialog.transient(self.root)
        fix_dialog.grab_set()
        
        # Center the dialog
        fix_dialog.update_idletasks()
        width = fix_dialog.winfo_width()
        height = fix_dialog.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        fix_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create main frame
        main_frame = tb.Frame(fix_dialog, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Header
        header_text = f"Fix Recommendation for {severity} Vulnerability on Line {line_num}"
        header_label = tb.Label(main_frame, text=header_text, font=("Helvetica", 12, "bold"))
        header_label.pack(anchor=tk.W, pady=(0, 5))
        
        tb.Label(
            main_frame,
            text=description,
            wraplength=760
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Fix recommendation
        tb.Label(
            main_frame,
            text="AI Fix Recommendation:",
            font=("Helvetica", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Text widget for fix result
        fix_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=90,
            height=20,
            font=("Courier New", 10)
        )
        fix_text.pack(fill=BOTH, expand=True, pady=(0, 15))
        fix_text.insert(tk.END, fix_result)
        
        # Action buttons
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        tb.Button(
            button_frame, 
            text="Apply Fix",
            command=lambda: self.apply_fix(fix_result, fix_dialog)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tb.Button(
            button_frame, 
            text="Close",
            command=fix_dialog.destroy
        ).pack(side=tk.RIGHT)
        
    def apply_fix(self, fix_result, dialog=None):
        """Apply the suggested fix to the code."""
        try:
            # Extract code blocks from fix result
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', fix_result, re.DOTALL)
            
            if code_blocks:
                # Take the last code block as the fixed code
                fixed_code = code_blocks[-1].strip()
                
                # Apply the fix
                self.scan_text.delete(1.0, 'end')
                self.scan_text.insert(tk.END, fixed_code)
                
                # Close dialog if provided
                if dialog:
                    dialog.destroy()
                    
                # Scan again to verify fixes
                self.scan_code_for_vulnerabilities()
                
                Messagebox.showinfo(
                    "Fix Applied", 
                    "The fix has been applied to the code. Rescanning to verify."
                )
            else:
                Messagebox.showwarning(
                    "No Code Found", 
                    "Could not extract code from the fix result. Please review the recommendation and apply changes manually."
                )
        except Exception as e:
            Messagebox.showerror("Error", f"Error applying fix: {str(e)}")

    def apply_fixes(self):
        """Apply fixes to all vulnerabilities."""
        # Get all vulnerability items
        items = self.results_tree.get_children()
        if not items:
            Messagebox.showinfo("No Vulnerabilities", "No vulnerabilities to fix.")
            return
            
        # Confirm with user
        result = Messagebox.askyesno(
            "Fix All Vulnerabilities",
            f"This will attempt to fix all {len(items)} vulnerabilities one by one. Continue?",
            icon=Messagebox.QUESTION
        )
        
        if not result:
            return
            
        # Fix each vulnerability
        for item in items:
            self.fix_vulnerability(item)
            
    def export_report(self):
        """Export the vulnerability scan report to a file."""
        # Get all vulnerability items
        items = self.results_tree.get_children()
        if not items:
            Messagebox.showinfo("No Vulnerabilities", "No vulnerabilities to export.")
            return
            
        # Ask for file location
        file_path = tb.filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Files", "*.html"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Vulnerability Report"
        )
        
        if not file_path:
            return
            
        try:
            # Generate report
            if file_path.endswith(".html"):
                self.export_html_report(file_path, items)
            else:
                self.export_text_report(file_path, items)
                
            # Open the file
            if Messagebox.askyesno("Report Exported", "Report has been exported. Would you like to open it now?"):
                os.startfile(file_path)
                
        except Exception as e:
            Messagebox.showerror("Export Error", f"Error exporting report: {str(e)}")
            
    def export_html_report(self, file_path, items):
        """Export report in HTML format."""
        # Get code and language
        code = self.scan_text.get(1.0, 'end')
        language = self.scan_lang
        
        # Generate report HTML
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Vulnerability Scan Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .summary { background-color: #f5f5f5; padding: 10px; margin: 10px 0; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .critical { color: #d9534f; }
                .high { color: #f0ad4e; }
                .medium { color: #5bc0de; }
                .low { color: #5cb85c; }
                .info { color: #0000ff; }
                pre { background-color: #f8f8f8; padding: 10px; overflow: auto; }
            </style>
        </head>
        <body>
            <h1>Vulnerability Scan Report</h1>
            <div class="summary">
                <p><strong>Date:</strong> %s</p>
                <p><strong>Language:</strong> %s</p>
                <p><strong>Total Vulnerabilities:</strong> %d</p>
            </div>
            
            <h2>Vulnerabilities</h2>
            <table>
                <tr>
                    <th>Severity</th>
                    <th>Line</th>
                    <th>Description</th>
                </tr>
        """ % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), language, len(items))
        
        # Add vulnerability rows
        for item in items:
            values = self.results_tree.item(item, 'values')
            line_num, severity, category, description = values
            
            html += """
                <tr>
                    <td class="%s">%s</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>
            """ % (severity.lower(), severity, line_num, description)
            
        # Add code section
        html += """
            </table>
            
            <h2>Source Code</h2>
            <pre><code>%s</code></pre>
        </body>
        </html>
        """ % (html.escape(code))
        
        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
            
    def export_text_report(self, file_path, items):
        """Export report in plain text format."""
        # Get code and language
        code = self.scan_text.get(1.0, 'end')
        language = self.scan_lang
        
        # Generate report text
        text = "Vulnerability Scan Report\n"
        text += "=" * 30 + "\n\n"
        text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"Language: {language}\n"
        text += f"Total Vulnerabilities: {len(items)}\n\n"
        
        text += "Vulnerabilities:\n"
        text += "-" * 30 + "\n"
        
        # Add vulnerability rows
        for item in items:
            values = self.results_tree.item(item, 'values')
            line_num, severity, category, description = values
            
            text += f"Severity: {severity}\n"
            text += f"Line: {line_num}\n"
            text += f"Description: {description}\n"
            text += "-" * 30 + "\n"
            
        # Add code section
        text += "\nSource Code:\n"
        text += "-" * 30 + "\n"
        text += code
        
        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

    def run_demo_scan(self):
        """Run a demonstration vulnerability scan."""
        # Load sample code first
        self.load_example_code()
        
        # Then scan it
        self.scan_code_for_vulnerabilities()
        
    def show_fix_dialog(self, original_code, fix_result, line_num, severity, description):
        """Show a dialog with the suggested fix."""
        fix_dialog = tb.Toplevel(self.root)
        fix_dialog.title("Vulnerability Fix")
        fix_dialog.geometry("800x600")
        fix_dialog.resizable(True, True)
        fix_dialog.transient(self.root)
        fix_dialog.grab_set()
        
        # Center the dialog
        fix_dialog.update_idletasks()
        width = fix_dialog.winfo_width()
        height = fix_dialog.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        fix_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create main frame
        main_frame = tb.Frame(fix_dialog, padding=10)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Explanation
        tb.Label(
            main_frame,
            text=f"Fix for {severity.capitalize()} Vulnerability (Line {line_num})",
            font=("Helvetica", 14, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        tb.Label(
            main_frame,
            text=description,
            wraplength=760
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Fix recommendation
        tb.Label(
            main_frame,
            text="AI Fix Recommendation:",
            font=("Helvetica", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Text widget for fix result
        fix_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=90,
            height=20,
            font=("Courier New", 10)
        )
        fix_text.pack(fill=BOTH, expand=True, pady=(0, 15))
        fix_text.insert(tk.END, fix_result)
        
        # Action buttons
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        tb.Button(
            button_frame,
            text="Apply Fix",
            command=lambda: self.apply_fix(fix_result, fix_dialog)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tb.Button(
            button_frame,
            text="Close",
            command=fix_dialog.destroy
        ).pack(side=tk.RIGHT)
        
    def apply_fix(self, fix_result, dialog=None):
        """Apply the suggested fix to the code."""
        try:
            # Extract code blocks from fix result
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', fix_result, re.DOTALL)
            
            if code_blocks:
                # Take the last code block as the fixed code
                fixed_code = code_blocks[-1].strip()
                
                # Apply the fix
                self.scan_text.delete(1.0, 'end')
                self.scan_text.insert(tk.END, fixed_code)
                
                # Close dialog if provided
                if dialog:
                    dialog.destroy()
                    
                # Scan again to verify fixes
                self.scan_code_for_vulnerabilities()
                
                Messagebox.showinfo(
                    "Fix Applied", 
                    "The fix has been applied to the code. Rescanning to verify."
                )
            else:
                Messagebox.showwarning(
                    "No Code Found", 
                    "Could not extract code from the fix result. Please review the recommendation and apply changes manually."
                )
        except Exception as e:
            Messagebox.showerror("Error", f"Error applying fix: {str(e)}")

    def initialize_ai(self):
        """Initialize the AI translator with the current settings."""
        try:
            if self.ai_interface:
                self.ai_interface.use_gemini_model(self.gemini_model)
                logger.info(f"AI initialized with model: {self.gemini_model}")
            else:
                logger.warning("AI interface not initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI: {e}")

    def setup_styles(self, style):
        """Set up custom styles for the application."""
        style = ttk.Style()
        
        # Configure premium frame style
        style.configure(
            "Premium.TFrame",
            background="#f0f8ff"
        )
        
        # Configure premium label style
        style.configure(
            "Premium.TLabel",
            background="#f0f8ff",
            foreground="#007bff"
        )
        
        # Configure tab styles
        style.configure(
            "TNotebook", 
            background="#f0f0f0"
        )
        
        style.configure(
            "TNotebook.Tab",
            padding=[10, 5],
            font=("Helvetica", 10)
        )
        
        # Configure button styles
        style.configure(
            "TButton",
            padding=5
        )

    def new_file(self):
        """Clear both code editors for a new file."""
        if Messagebox.askyesno("New File", "Clear both editors?"):
            self.source_text.delete(1.0, 'end')
            self.target_text.delete(1.0, 'end')

    def _show_settings(self):
        """Show the settings dialog."""
        try:
            # Create dialog using ttkbootstrap
            dialog = tb.Toplevel(self.root)
            dialog.title("Settings")
            dialog.geometry("600x500")
            dialog.minsize(500, 400)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create notebook for settings tabs
            notebook = tb.Notebook(dialog)
            notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
            
            # Create tabs
            appearance_tab = tb.Frame(notebook)
            editor_tab = tb.Frame(notebook)
            api_tab = tb.Frame(notebook)
            
            # Add tabs
            notebook.add(appearance_tab, text="Appearance")
            notebook.add(editor_tab, text="Editor")
            notebook.add(api_tab, text="API")
            
            # Setup tabs
            self._setup_appearance_tab(appearance_tab)
            self._setup_editor_tab(editor_tab)
            self._setup_api_tab(api_tab)
            
            # Add OK/Cancel buttons
            button_frame = tb.Frame(dialog)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            tb.Button(
                button_frame,
                text="Cancel",
                command=dialog.destroy
            ).pack(side=tk.RIGHT, padx=5)
            
            tb.Button(
                button_frame,
                text="OK",
                command=lambda: self._apply_settings(dialog)
            ).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            logger.error(f"Error in _show_settings: {str(e)}")
            self._show_error(f"Error: {str(e)}")
            
    def _setup_appearance_tab(self, parent):
        """Set up the appearance settings tab."""
        # Create frame for content
        content_frame = tb.Frame(parent, padding=20)
        content_frame.pack(fill=BOTH, expand=True)
        
        # Theme section
        tb.Label(
            content_frame,
            text="Theme",
            style="Heading.TLabel"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        theme_frame = tb.Frame(content_frame)
        theme_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Theme radio buttons
        self.settings_theme_var = tb.StringVar(value=self.current_theme)
        for i, theme_name in enumerate(THEMES):
            tb.Radiobutton(
                theme_frame,
                text=theme_name,
                variable=self.settings_theme_var,
                value=theme_name,
                padding=(10, 5)
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=5)
        
        # Font section
        tb.Label(
            content_frame,
            text="Font",
            style="Heading.TLabel"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        font_frame = tb.Frame(content_frame)
        font_frame.pack(fill=tk.X, pady=(0, 20))
        
        tb.Label(
            font_frame,
            text="Font Size:"
        ).pack(side=tk.LEFT, padx=10)
        
        self.settings_font_size = tb.IntVar(value=self.font_size)
        font_spin = tb.Spinbox(
            font_frame,
            from_=8,
            to=24,
            textvariable=self.settings_font_size,
            width=5
        )
        font_spin.pack(side=tk.LEFT, padx=5)
        
        # Interface scaling
        tb.Label(
            content_frame,
            text="UI Scale:",
            style="Heading.TLabel"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        scale_frame = tb.Frame(content_frame)
        scale_frame.pack(fill=tk.X)
        
        self.ui_scale_var = tb.DoubleVar(value=1.0)
        scale = tb.Scale(
            scale_frame,
            variable=self.ui_scale_var,
            from_=0.8,
            to=1.5,
            length=300,
            orient=tk.HORIZONTAL
        )
        scale.pack(side=tk.LEFT, padx=10)
        
        scale_label = tb.Label(scale_frame, text="100%")
        scale_label.pack(side=tk.LEFT, padx=5)
        
        # Update label when scale changes
        def update_scale_label(*args):
            scale_label.config(text=f"{int(self.ui_scale_var.get() * 100)}%")
        
        self.ui_scale_var.trace("w", update_scale_label)
        
    def _setup_editor_tab(self, parent):
        """Set up the editor settings tab."""
        # Create frame for content
        content_frame = tb.Frame(parent, padding=20)
        content_frame.pack(fill=BOTH, expand=True)
        
        # Code editor settings
        tb.Label(
            content_frame,
            text="Code Editor",
            style="Heading.TLabel"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Word wrap
        self.word_wrap_var = tb.BooleanVar(value=False)
        tb.Checkbutton(
            content_frame,
            text="Enable Word Wrap",
            variable=self.word_wrap_var
        ).pack(anchor=tk.W, pady=5)
        
        # Line numbers
        self.line_numbers_var = tb.BooleanVar(value=True)
        tb.Checkbutton(
            content_frame,
            text="Show Line Numbers",
            variable=self.line_numbers_var
        ).pack(anchor=tk.W, pady=5)
        
        # Syntax highlighting
        tb.Label(
            content_frame,
            text="Syntax Highlighting",
            style="Heading.TLabel"
        ).pack(anchor=tk.W, pady=(20, 10))
        
        self.syntax_highlight_var = tb.BooleanVar(value=True)
        tb.Checkbutton(
            content_frame,
            text="Enable Syntax Highlighting",
            variable=self.syntax_highlight_var
        ).pack(anchor=tk.W, pady=5)
        
        # Highlight style
        style_frame = tb.Frame(content_frame)
        style_frame.pack(fill=tk.X, pady=5)
        
        tb.Label(
            style_frame,
            text="Highlight Style:"
        ).pack(side=tk.LEFT, padx=10)
        
        self.highlight_style_var = tb.StringVar(value="monokai")
        styles = ["default", "monokai", "vs", "solarized-dark", "solarized-light"]
        style_combo = tb.Combobox(
            style_frame,
            values=styles,
            textvariable=self.highlight_style_var,
            width=15,
            state="readonly"
        )
        style_combo.pack(side=tk.LEFT, padx=5)
        
        # Auto-indentation
        self.auto_indent_var = tb.BooleanVar(value=True)
        tb.Checkbutton(
            content_frame,
            text="Enable Auto-Indentation",
            variable=self.auto_indent_var
        ).pack(anchor=tk.W, pady=5)
        
    def _setup_api_tab(self, parent):
        """Set up the API settings tab."""
        # Create frame for content
        content_frame = tb.Frame(parent, padding=20)
        content_frame.pack(fill=BOTH, expand=True)
        
        # API Key section
        tb.Label(
            content_frame,
            text="Gemini API Settings",
            style="Heading.TLabel"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        key_frame = tb.Frame(content_frame)
        key_frame.pack(fill=tk.X, pady=5)
        
        tb.Label(
            key_frame,
            text="API Key:"
        ).pack(side=tk.LEFT, padx=10)
        
        self.api_key_var = tb.StringVar(value=self.gemini_api_key or "")
        api_key_entry = tb.Entry(
            key_frame,
            textvariable=self.api_key_var,
            width=40,
            show="*"
        )
        api_key_entry.pack(side=tk.LEFT, padx=5)
        
        # Show/Hide password
        self.show_api_key_var = tb.BooleanVar(value=False)
        tb.Checkbutton(
            content_frame,
            text="Show",
            variable=self.show_api_key_var,
            command=lambda: api_key_entry.config(show="" if self.show_api_key_var.get() else "*")
        ).pack(pady=(0, 10))
        
        # Model selection
        model_frame = tb.Frame(content_frame)
        model_frame.pack(fill=tk.X, pady=10)
        
        tb.Label(
            model_frame,
            text="Gemini Model:"
        ).pack(side=tk.LEFT, padx=10)
        
        self.model_var = tb.StringVar(value=self.gemini_model)
        models = ["models/gemini-1.5-pro-001"]
        model_combo = tb.Combobox(
            model_frame,
            values=models,
            textvariable=self.model_var,
            width=15,
            state="readonly"
        )
        model_combo.pack(side=tk.LEFT, padx=5)
        
        # Help text
        help_text = """To get your API key:
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key"""
        
        help_frame = tb.LabelFrame(content_frame, text="Help", padding=10)
        help_frame.pack(fill=tk.X, pady=15)
        
        tb.Label(
            help_frame,
            text=help_text,
            justify=tk.LEFT,
            wraplength=500
        ).pack(fill=tk.X)
        
        # Test connection button
        tb.Button(
            content_frame,
            text="Test Connection",
            bootstyle="primary",
            command=self._test_api_connection
        ).pack(pady=15)
        
    def _test_api_connection(self):
        """Test the API connection with the provided key."""
        api_key = self.api_key_var.get()
        if not api_key:
            Messagebox.showwarning("API Key Required", "Please enter an API key to test.")
            return
            
        try:
            self.status_var.set("Testing API connection...")
            # Try to initialize a temporary Gemini interface
            from ai_code_translator.gemini_interface import GeminiInterface
            temp_gemini = GeminiInterface(
                api_key=api_key,
                model=self.model_var.get()
            )
            
            # Test the model by sending a simple request
            test_prompt = "Hello, how are you?"
            response = temp_gemini.generate(test_prompt)
            
            if response:
                Messagebox.showinfo("Success", "API connection successful!")
                self.status_var.set("API: Connected")
            else:
                raise Exception("No response from API")
                
        except Exception as e:
            logger.error(f"API test failed: {str(e)}")
            Messagebox.showerror("Connection Failed", f"Failed to connect to API: {str(e)}")
            self.status_var.set("API: Not Connected")
    
    def _apply_settings(self, dialog):
        """Apply the settings from the dialog."""
        # Apply theme
        new_theme = self.settings_theme_var.get()
        if new_theme != self.current_theme:
            self.theme_var.set(new_theme)
            self._change_theme()
            
        # Apply font size
        new_font_size = self.settings_font_size.get()
        if new_font_size != self.font_size:
            delta = new_font_size - self.font_size
            self._change_font_size(delta)
            
        # Apply API settings
        new_api_key = self.api_key_var.get()
        if new_api_key != self.gemini_api_key:
            self.gemini_api_key = new_api_key
            self._initialize_ai_components()
            self.api_status.config(text="API: Connected" if self.gemini_api_key else "API: Not Connected")
            
        # Apply model settings
        new_model = self.model_var.get()
        if new_model != self.gemini_model:
            self.gemini_model = new_model
            self._initialize_ai_components()
            self.model_indicator.config(text=f"Model: {new_model}")
            
        # Apply word wrap
        wrap_mode = tk.WORD if self.word_wrap_var.get() else tk.NONE
        self.source_text.configure(wrap=wrap_mode)
        self.target_text.configure(wrap=wrap_mode)
        
        # Save settings
        self._save_settings()
        
        self.status_var.set("Settings applied successfully")

    def _save_settings(self):
        """Save settings to a configuration file."""
        config = {
            "theme": self.current_theme,
            "font_size": self.font_size,
            "model": self.gemini_model,
            "word_wrap": self.word_wrap_var.get(),
            "line_numbers": self.line_numbers_var.get(),
            "syntax_highlight": self.syntax_highlight_var.get(),
            "highlight_style": self.highlight_style_var.get(),
            "auto_indent": self.auto_indent_var.get(),
            "ui_scale": self.ui_scale_var.get()
        }
        
        config_dir = Path(__file__).parent / "config"
        config_dir.mkdir(exist_ok=True)
        
        try:
            with open(config_dir / "settings.json", "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def _load_settings(self):
        """Load settings from a configuration file."""
        config_path = Path(__file__).parent / "config" / "settings.json"
        
        try:
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                    
                # Apply settings
                if "theme" in config:
                    self.current_theme = config["theme"]
                    self.theme_var.set(self.current_theme)
                    self.style.theme_use(THEMES[self.current_theme])
                    
                if "font_size" in config:
                    self.font_size = config["font_size"]
                    
                if "model" in config:
                    self.gemini_model = config["model"]
                    
                if "word_wrap" in config:
                    wrap_mode = tk.WORD if config["word_wrap"] else tk.NONE
                    self.source_text.configure(wrap=wrap_mode)
                    self.target_text.configure(wrap=wrap_mode)
                    self.word_wrap_var.set(config["word_wrap"])
                    
                if "line_numbers" in config:
                    self.line_numbers_var.set(config["line_numbers"])
                    
                if "syntax_highlight" in config:
                    self.syntax_highlight_var.set(config["syntax_highlight"])
                    
                if "highlight_style" in config:
                    self.highlight_style_var.set(config["highlight_style"])
                    
                if "auto_indent" in config:
                    self.auto_indent_var.set(config["auto_indent"])
                    
                if "ui_scale" in config:
                    self.ui_scale_var.set(config["ui_scale"])
                    
                logger.info("Settings loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    def _change_theme(self):
        """Change the application theme."""
        # Get current theme
        current_theme = self.style.theme_use()
        
        # Get all available themes
        themes = self.style.theme_names()
        
        # Find the next theme in the list
        theme_index = themes.index(current_theme)
        next_theme = themes[(theme_index + 1) % len(themes)]
        
        # Apply new theme
        self.style.theme_use(next_theme)
        self.theme_indicator.config(text=f"Theme: {next_theme}")

    def _create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        status_frame = tb.Frame(self.root)
        status_frame.pack(side=BOTTOM, fill=X)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = tb.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=LEFT, padx=5, pady=2)

        # Theme indicator
        self.theme_indicator = tb.Label(status_frame, text=f"Theme: {self.style.theme_use()}")
        self.theme_indicator.pack(side=LEFT, padx=5, pady=2)

        # API status
        self.api_status = tb.Label(status_frame, text="API: Connected" if self.ai_interface else "API: Not Connected")
        self.api_status.pack(side=LEFT, padx=5, pady=2)

        # Model indicator
        self.model_indicator = tb.Label(status_frame, text=f"Model: {self.gemini_model}")
        self.model_indicator.pack(side=LEFT, padx=5, pady=2)

    def _show_about(self):
        """Show the about dialog."""
        about_text = """
        AI Code Translator
        Version 1.0
        
        A powerful code translation tool with AI integration
        and security scanning capabilities.
        
        Copyright 2025
        
        Features:
        - AI-powered code translation
        - Security vulnerability scanning
        - Multiple programming language support
        - Gemini API integration
        """
        
        # Create dialog
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("About AI Code Translator")
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        # Center the dialog
        about_dialog.update_idletasks()
        width = 400
        height = 300
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        about_dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Create content frame
        content_frame = tb.Frame(about_dialog, padding=20)
        content_frame.pack(fill=BOTH, expand=True)
        
        # Create text widget for about content
        about_text_widget = tk.Text(content_frame, wrap=tk.WORD, height=10, width=50)
        about_text_widget.insert(tk.END, about_text)
        about_text_widget.configure(state='disabled')
        about_text_widget.pack(fill=BOTH, expand=True)
        
        # Create close button
        close_button = tb.Button(
            content_frame,
            text="Close",
            command=about_dialog.destroy
        )
        close_button.pack(pady=10)
        
        # Make dialog modal
        about_dialog.wait_window()

def main():
    """Run the integrated translator GUI."""
    try:
        # Initialize ttkbootstrap style
        style = tb.Style(theme="darkly")
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="AI Code Translator with Gemini Integration")
        parser.add_argument("--model-path", help="Path to the model directory")
        parser.add_argument("--gemini-api-key", help="Google Gemini API key")
        parser.add_argument("--use-neural", action="store_true", help="Use neural translation")
        parser.add_argument("--gemini-model", default="models/gemini-1.5-pro-001", help="Gemini model to use")
        parser.add_argument("--premium", action="store_true", help="Enable premium features")
        parser.add_argument("--security", action="store_true", help="Enable security scanner")

        args = parser.parse_args()

        # Create and run the application
        app = IntegratedTranslatorGUI(
            gemini_api_key=args.gemini_api_key,
            gemini_model=args.gemini_model,
            enable_premium=args.premium,
            enable_security=args.security
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
