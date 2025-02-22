#!/usr/bin/env python3
"""
Script to download large data files from Google Drive.
Requires a valid API key for access.
"""
import os
import sys
import gdown
from pathlib import Path

# Google Drive folder ID (extracted from the sharing URL)
FOLDER_ID = "1RcLRBJ-4gwZ5DSDEgEhgk8eWbz_yGOxk"

# File paths relative to the data directory
FILES = {
    "data/codetransocean/nichetrans/niche_test.json": None,  # Will be filled with file IDs
    "data/codetransocean/nichetrans/niche_train.json": None,
    "data/codetransocean/nichetrans/niche_valid.json": None,
    "data/codetransocean/multilingualtrans/multilingual_train.json": None
}

def ensure_dir(file_path):
    """Create directory if it doesn't exist."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_file(file_id, output_path):
    """Download a single file from Google Drive."""
    url = f"https://drive.google.com/uc?id={file_id}"
    ensure_dir(output_path)
    try:
        gdown.download(url, output_path, quiet=False)
        return True
    except Exception as e:
        print(f"Error downloading {output_path}: {e}")
        return False

def verify_api_key(api_key):
    """Verify if the provided API key is valid."""
    # TODO: Implement your API key verification logic
    if not api_key or api_key == "YOUR_API_KEY":
        print("Error: Valid API key required.")
        print("Please contact [Your Contact Information] to obtain a license and API key.")
        sys.exit(1)
    return True

def main():
    """Main function to download all required files."""
    # Check for API key
    api_key = os.getenv("AI_TRANSLATOR_API_KEY", "")
    verify_api_key(api_key)
    
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    print("Fetching file list from Google Drive folder...")
    folder_url = f"https://drive.google.com/drive/folders/{FOLDER_ID}"
    
    # First, list all files in the folder to get their IDs
    try:
        file_list = gdown.download_folder(folder_url, quiet=True, use_cookies=False)
        if not file_list:
            print("Error: Could not access the Google Drive folder. Please check the URL and your internet connection.")
            sys.exit(1)
    except Exception as e:
        print(f"Error accessing Google Drive folder: {e}")
        sys.exit(1)

    # Download each file
    for file_path in FILES.keys():
        abs_path = project_root / file_path
        print(f"\nDownloading {file_path}...")
        
        # Find the corresponding file in the downloaded list
        file_name = os.path.basename(file_path)
        matching_files = [f for f in file_list if f.endswith(file_name)]
        
        if not matching_files:
            print(f"Warning: Could not find {file_name} in the Google Drive folder")
            continue
            
        source_path = matching_files[0]
        if os.path.exists(source_path):
            # Move the file to its correct location
            ensure_dir(str(abs_path))
            os.replace(source_path, str(abs_path))
            print(f"Successfully downloaded and moved {file_name}")
        else:
            print(f"Error: Download failed for {file_name}")

    print("\nDownload process completed!")

if __name__ == "__main__":
    main()
