#!/usr/bin/env python3
"""
Git Hooks Setup Script

This script sets up Git hooks to prevent accidental credential commits.
"""

import os
import sys
import stat
from pathlib import Path

# Pre-commit hook content
PRE_COMMIT_HOOK = """#!/usr/bin/env python3
import re
import sys
import subprocess
from pathlib import Path

# Patterns for identifying potential credential files or content
CREDENTIAL_PATTERNS = [
    r'.*credentials.*\.json',
    r'.*token.*\.json',
    r'.*secret.*\.json',
    r'.*key.*\.json',
    r'.*\.env$',
    r'.*\.pem$',
    r'.*\.key$',
    r'.*\.cert$',
]

# Patterns for identifying credentials in file content
CONTENT_PATTERNS = [
    r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?',
    r'client[_-]?secret["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?',
    r'password["\']?\s*[:=]\s*["\']?[^"\',]+["\']?',
    r'secret["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?',
    r'token["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-.]{16,}["\']?',
    r'access[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}["\']?',
]

def get_staged_files():
    """Get list of files staged for commit."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True, text=True, check=True
    )
    return [file for file in result.stdout.strip().split('\\n') if file]

def check_file_patterns(files):
    """Check if any staged files match credential patterns."""
    for file in files:
        for pattern in CREDENTIAL_PATTERNS:
            if re.match(pattern, file, re.IGNORECASE):
                print(f"ERROR: Potential credential file detected: {file}")
                print("If this is intentional, use --no-verify to bypass this check.")
                return True
    return False

def check_file_content(files):
    """Check if any staged files contain credential patterns."""
    for file in files:
        if not os.path.isfile(file):
            continue
            
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            for pattern in CONTENT_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if matches:
                    print(f"ERROR: Potential credentials found in {file}:")
                    print("If this is intentional, use --no-verify to bypass this check.")
                    return True
        except Exception as e:
            print(f"Warning: Could not check content of {file}: {e}")
    
    return False

def main():
    """Main function to run the pre-commit hook."""
    staged_files = get_staged_files()
    
    if not staged_files:
        return 0
        
    if check_file_patterns(staged_files) or check_file_content(staged_files):
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

def setup_pre_commit_hook():
    """Set up the pre-commit hook."""
    git_dir = Path(".git")
    hooks_dir = git_dir / "hooks"
    
    if not git_dir.exists():
        print("Error: .git directory not found. Are you in a Git repository?")
        return False
        
    if not hooks_dir.exists():
        hooks_dir.mkdir(exist_ok=True)
        
    pre_commit_path = hooks_dir / "pre-commit"
    
    # Write the pre-commit hook
    with open(pre_commit_path, 'w') as f:
        f.write(PRE_COMMIT_HOOK)
        
    # Make the hook executable
    os.chmod(pre_commit_path, os.stat(pre_commit_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    print(f"Pre-commit hook installed at {pre_commit_path}")
    return True

def main():
    """Main function to set up Git hooks."""
    print("Setting up Git hooks for credential protection...")
    
    if setup_pre_commit_hook():
        print("Git hooks setup complete.")
        print("\nThese hooks will help prevent accidental credential commits.")
        print("To bypass the hooks in special cases, use: git commit --no-verify")
    else:
        print("Failed to set up Git hooks.")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())