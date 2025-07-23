# Credential Security System

## Overview

This system provides a secure way to manage credentials in the application, addressing the issue of exposed Google OAuth credentials in the repository. It implements a comprehensive approach to credential management, including secure storage, access, and protection against accidental exposure.

## Components

### 1. Credential Manager

The `CredentialManager` class (`src/utils/credential_manager.py`) provides a centralized interface for securely accessing credentials:

- Loads credentials from environment variables
- Provides methods for accessing specific credential sets
- Logs credential access for auditing
- Creates credential files when needed by external libraries

### 2. Credential Cleanup Script

The `clean_credentials.py` script helps identify and remove exposed credentials from Git history:

- Scans for potential credential files
- Removes sensitive files from Git history
- Updates .gitignore with patterns to prevent future exposure

### 3. Git Hooks

The pre-commit hook prevents accidental credential commits by:

- Checking file names against credential patterns
- Scanning file content for potential credentials
- Blocking commits that might expose sensitive information

### 4. Documentation

Comprehensive documentation is provided to guide developers on secure credential management:

- `CREDENTIAL_MANAGEMENT_GUIDE.md`: Detailed guide on managing credentials
- `CREDENTIAL_SECURITY_README.md`: Overview of the credential security system

## Setup Instructions

1. Install required packages:

   ```
   pip install python-dotenv
   ```

2. Set up Git hooks:

   ```
   python scripts/setup_git_hooks.py
   ```

3. Create your `.env` file:

   ```
   copy .env.example .env
   ```

4. Add your actual credentials to the `.env` file

## Usage

Import and use the credential manager in your code:

```python
from src.utils.credential_manager import credential_manager

# Get a single credential
api_key = credential_manager.get_credential("GOOGLE_API_KEY")

# Get all Google credentials
google_creds = credential_manager.get_google_credentials()
```

## Security Best Practices

1. Never commit credentials to the repository
2. Always use environment variables for sensitive information
3. Regularly rotate credentials
4. Use the provided credential management tools
5. Run the credential cleanup script if credentials are accidentally exposed

## Handling Credential Exposure

If credentials are accidentally committed:

1. Immediately rotate the exposed credentials
2. Run the cleanup script: `python scripts/clean_credentials.py`
3. Force push the cleaned repository: `git push --force`
4. Notify all team members to pull the latest changes
