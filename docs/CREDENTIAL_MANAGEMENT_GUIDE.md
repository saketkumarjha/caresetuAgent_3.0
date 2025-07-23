# Credential Management Guide

This guide explains how to securely manage credentials in this project to prevent exposure of sensitive information in the repository.

## Table of Contents

1. [Introduction](#introduction)
2. [Setting Up Credentials](#setting-up-credentials)
3. [Using Credentials in Code](#using-credentials-in-code)
4. [Rotating Credentials](#rotating-credentials)
5. [Handling Credential Exposure](#handling-credential-exposure)

## Introduction

Proper credential management is essential for application security. This project uses environment variables stored in a `.env` file for local development and secure environment variables for production deployments.

**Important Security Rules:**

- Never commit credentials to the repository
- Always use environment variables for sensitive information
- Regularly rotate credentials
- Use the provided credential management tools

## Setting Up Credentials

### Local Development

1. Copy the `.env.example` file to create a new `.env` file:

   ```
   copy .env.example .env
   ```

2. Edit the `.env` file and add your actual credentials:

   ```
   # Google Calendar API Configuration
   GOOGLE_API_KEY=your_actual_api_key
   GOOGLE_CLIENT_ID=your_actual_client_id
   GOOGLE_CLIENT_SECRET=your_actual_client_secret

   # Other credentials...
   ```

3. The `.env` file is automatically ignored by Git (via `.gitignore`), so your credentials will not be committed.

### Production Deployment

For production environments, set environment variables according to your deployment platform:

- **Heroku**: Use config vars in the dashboard or CLI
- **AWS**: Use AWS Parameter Store or Secrets Manager
- **Docker**: Use environment variables in your docker-compose file or Kubernetes secrets

## Using Credentials in Code

Always use the `CredentialManager` class to access credentials in your code:

```python
from src.utils.credential_manager import credential_manager

# Get a single credential
api_key = credential_manager.get_credential("GOOGLE_API_KEY")

# Get all Google credentials
google_creds = credential_manager.get_google_credentials()
```

This ensures consistent access patterns and proper logging of credential usage.

## Rotating Credentials

When rotating credentials:

1. Update the credential in your service provider (Google, LiveKit, etc.)
2. Update your local `.env` file with the new credential
3. Update the credential in your production environment
4. Verify the application works with the new credential

## Handling Credential Exposure

If credentials are accidentally committed to the repository:

1. Immediately rotate the exposed credentials
2. Run the credential cleanup script to remove them from Git history:
   ```
   python scripts/clean_credentials.py
   ```
3. Force push the cleaned repository:
   ```
   git push --force
   ```
4. Notify all team members to pull the latest changes

## Additional Security Measures

- Use the pre-commit hook to prevent accidental credential commits
- Regularly audit credential access logs
- Limit credential access to only necessary team members
- Consider using a dedicated secret management service for production environments
