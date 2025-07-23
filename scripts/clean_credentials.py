#!/usr/bin/env python3
"""
Credential Cleanup Script

This script helps identify and clean up exposed credentials in the Git repository.
It provides functionality to:
1. Scan for potential credential files
2. Remove sensitive files from Git history
3. Add sensitive files to .gitignore
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Set

# Patterns for identifying potential credential files
CREDENTIAL_PATTERNS = [
    r'.*credentials.*\.json',
    r'.*token.*\.json',
    r'.*secret.*\.json',
    r'.*key.*\.json',
    r'.*\.env',
    r'.*\.pem',
    r'.*\.key',
    r'.*\.cert',
    r'.*password.*',
    r'.*apikey.*',
]

# Files that should always be ignored
DEFAULT_IGNORE_FILES = [
    '.env',
    'credentials.json',
    'token.json',
    '*.pem',
    '*.key',
    '*.cert',
    'service-account.json',
]

def run_command(command: List[str]) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}")
        print(f"Error message: {e.stderr}")
        return ""

def scan_for_credentials() -> Set[str]:
    """Scan the repository for potential credential files."""
    potential_files = set()
    
    # Get all files tracked by Git
    all_files = run_command(['git', 'ls-files']).split('\n')
    
    # Check each file against credential patterns
    for file in all_files:
        if not file:
            continue
            
        for pattern in CREDENTIAL_PATTERNS:
            if re.match(pattern, file, re.IGNORECASE):
                potential_files.add(file)
                break
                
    return potential_files

def update_gitignore(files_to_ignore: List[str]) -> None:
    """Update .gitignore with files that should be ignored."""
    # Read current .gitignore
    gitignore_path = '.gitignore'
    current_ignores = set()
    
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            current_ignores = {line.strip() for line in f if line.strip() and not line.startswith('#')}
    
    # Add new files to ignore
    new_ignores = set(files_to_ignore) - current_ignores
    
    if new_ignores:
        print(f"Adding {len(new_ignores)} entries to .gitignore:")
        for entry in new_ignores:
            print(f"  - {entry}")
            
        with open(gitignore_path, 'a') as f:
            f.write("\n# Added by credential cleanup script\n")
            for entry in sorted(new_ignores):
                f.write(f"{entry}\n")
        
        print("Updated .gitignore successfully.")
    else:
        print("No new entries needed in .gitignore.")

def remove_file_from_git_history(file_path: str) -> bool:
    """Remove a file from Git history using git-filter-repo."""
    try:
        # Check if git-filter-repo is installed
        subprocess.run(['git', 'filter-repo', '--version'], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: git-filter-repo is not installed or not in PATH.")
        print("Please install it with: pip install git-filter-repo")
        return False
    
    try:
        # Remove the file from Git history
        subprocess.run(['git', 'filter-repo', '--path', file_path, '--invert-paths', '--force'],
                      check=True)
        print(f"Successfully removed {file_path} from Git history.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error removing {file_path} from Git history: {e}")
        return False

def main() -> None:
    """Main function to run the credential cleanup process."""
    print("Credential Cleanup Script")
    print("========================\n")
    
    # Scan for potential credential files
    print("Scanning for potential credential files...")
    potential_files = scan_for_credentials()
    
    if not potential_files:
        print("No potential credential files found.")
        
        # Still update .gitignore with default patterns
        print("\nUpdating .gitignore with default credential patterns...")
        update_gitignore(DEFAULT_IGNORE_FILES)
        return
    
    print(f"\nFound {len(potential_files)} potential credential files:")
    for file in sorted(potential_files):
        print(f"  - {file}")
    
    # Ask user which files to clean up
    print("\nDo you want to remove these files from Git history? (y/n)")
    choice = input("> ").strip().lower()
    
    if choice == 'y':
        for file in sorted(potential_files):
            print(f"\nProcessing {file}...")
            remove_file_from_git_history(file)
    
    # Update .gitignore
    print("\nUpdating .gitignore...")
    files_to_ignore = list(DEFAULT_IGNORE_FILES)
    files_to_ignore.extend(potential_files)
    update_gitignore(files_to_ignore)
    
    print("\nCredential cleanup complete.")
    print("\nIMPORTANT: After running this script, you need to force-push your changes:")
    print("  git push --force")
    print("\nWARNING: Force pushing will overwrite the remote repository history.")
    print("Make sure all collaborators are aware of this change.")

if __name__ == "__main__":
    main()