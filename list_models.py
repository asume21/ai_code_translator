import os
import google.generativeai as genai

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Please set the GEMINI_API_KEY environment variable")
        return
    
    genai.configure(api_key=api_key)
    
    print("Available models:")
    for model in genai.list_models():
        print(f"Model: {model.name}")
        print(f"Supported methods: {model.supported_generation_methods}")
        print("-")

if __name__ == "__main__":
    main()
