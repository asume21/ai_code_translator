"""Fast multi-language dataset builder for code translation."""

import os
import json
import subprocess
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor
import requests
from tqdm import tqdm

class FastDatasetBuilder:
    """Rapidly builds multi-language translation datasets."""
    
    def __init__(self):
        self.supported_languages = {
            'python': ['.py'],
            'javascript': ['.js'],
            'typescript': ['.ts'],
            'java': ['.java'],
            'cpp': ['.cpp', '.hpp', '.cc', '.h'],
            'go': ['.go'],
            'rust': ['.rs'],
            'ruby': ['.rb'],
            'php': ['.php'],
            'csharp': ['.cs']
        }
        
        # Popular repos with multiple language implementations
        self.source_repos = {
            'algorithms': [
                'TheAlgorithms/Python',
                'TheAlgorithms/JavaScript',
                'TheAlgorithms/Java',
                'TheAlgorithms/C-Plus-Plus',
                'TheAlgorithms/Go',
                'TheAlgorithms/Rust'
            ],
            'design_patterns': [
                'faif/python-patterns',
                'fbeline/design-patterns-JS',
                'iluwatar/java-design-patterns',
                'JakubVojvoda/design-patterns-cpp',
                'RefactoringGuru/design-patterns-go'
            ],
            'leetcode': [
                'qiyuangong/leetcode',
                'haoel/leetcode',
                'fishercoder1534/Leetcode'
            ]
        }
        
        # Keywords to identify equivalent implementations
        self.matching_keywords = [
            'sort', 'search', 'tree', 'graph', 'list', 'stack', 'queue',
            'hash', 'binary', 'linked', 'merge', 'quick', 'heap',
            'depth', 'breadth', 'dynamic', 'greedy'
        ]
    
    def clone_repos(self, output_dir: str):
        """Clone all source repositories in parallel."""
        os.makedirs(output_dir, exist_ok=True)
        
        def clone_repo(repo: str):
            repo_dir = os.path.join(output_dir, repo.replace('/', '_'))
            if not os.path.exists(repo_dir):
                subprocess.run(['git', 'clone', f'https://github.com/{repo}.git', repo_dir],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return repo_dir
        
        print("Cloning repositories...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            all_repos = [repo for repos in self.source_repos.values() for repo in repos]
            repo_dirs = list(tqdm(executor.map(clone_repo, all_repos), total=len(all_repos)))
        
        return repo_dirs
    
    def find_matching_files(self, repo_dirs: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """Find matching implementations across languages."""
        
        def get_language(file_path: str) -> str:
            ext = os.path.splitext(file_path)[1]
            for lang, extensions in self.supported_languages.items():
                if ext in extensions:
                    return lang
            return None
        
        def find_files(repo_dir: str) -> List[tuple]:
            matches = []
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    lang = get_language(file_path)
                    if lang:
                        # Get normalized filename without extension
                        name = os.path.splitext(file)[0].lower()
                        # Check if file contains matching keywords
                        if any(kw in name for kw in self.matching_keywords):
                            matches.append((name, lang, file_path))
            return matches
        
        print("\nFinding matching files...")
        all_matches = {}
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            file_matches = list(tqdm(executor.map(find_files, repo_dirs), total=len(repo_dirs)))
        
        # Group matches by name
        for matches in file_matches:
            for name, lang, path in matches:
                if name not in all_matches:
                    all_matches[name] = {}
                if lang not in all_matches[name]:
                    all_matches[name][lang] = []
                all_matches[name][lang].append(path)
        
        return all_matches
    
    def extract_function_pairs(self, matches: Dict[str, Dict[str, List[str]]], min_languages: int = 3) -> List[Dict]:
        """Extract function pairs from matching files."""
        pairs = []
        
        print("\nExtracting function pairs...")
        for name, lang_files in tqdm(matches.items()):
            # Only process files that have implementations in multiple languages
            if len(lang_files) >= min_languages:
                pair_group = {
                    'name': name,
                    'implementations': {}
                }
                
                for lang, files in lang_files.items():
                    # Take the first implementation for now
                    with open(files[0], 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        pair_group['implementations'][lang] = {
                            'code': content,
                            'file': files[0]
                        }
                
                pairs.append(pair_group)
        
        return pairs
    
    def save_dataset(self, pairs: List[Dict], output_file: str):
        """Save the dataset with metadata."""
        dataset = {
            'version': '2.0',
            'statistics': {
                'total_pairs': len(pairs),
                'languages': {},
                'keywords': {}
            },
            'pairs': pairs
        }
        
        # Gather statistics
        for pair in pairs:
            # Count languages
            for lang in pair['implementations'].keys():
                if lang not in dataset['statistics']['languages']:
                    dataset['statistics']['languages'][lang] = 0
                dataset['statistics']['languages'][lang] += 1
            
            # Count keywords
            for kw in self.matching_keywords:
                if kw in pair['name']:
                    if kw not in dataset['statistics']['keywords']:
                        dataset['statistics']['keywords'][kw] = 0
                    dataset['statistics']['keywords'][kw] += 1
        
        print(f"\nSaving dataset to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2)
        
        print("\nDataset Statistics:")
        print(f"Total implementation groups: {len(pairs)}")
        print("\nLanguage distribution:")
        for lang, count in dataset['statistics']['languages'].items():
            print(f"{lang}: {count} implementations")
        print("\nKeyword distribution:")
        for kw, count in dataset['statistics']['keywords'].items():
            print(f"{kw}: {count} occurrences")

def build_fast_dataset():
    """Build the dataset quickly using parallel processing."""
    builder = FastDatasetBuilder()
    
    # Setup paths
    project_dir = os.path.dirname(os.path.dirname(__file__))
    repos_dir = os.path.join(project_dir, 'source_repos')
    output_file = os.path.join(project_dir, 'ai_code_translator', 'data', 'multi_language_dataset.json')
    
    # Build dataset
    print("Starting fast dataset build...")
    repo_dirs = builder.clone_repos(repos_dir)
    matches = builder.find_matching_files(repo_dirs)
    pairs = builder.extract_function_pairs(matches)
    builder.save_dataset(pairs, output_file)
    print("\nDataset build complete!")

if __name__ == '__main__':
    build_fast_dataset()
