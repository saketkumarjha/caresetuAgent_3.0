"""
OAuth Manager Module

This module provides secure OAuth credential management functionality for the application.
It handles OAuth authentication flow and token storage securely.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OAuthManager:
    """
    Manages OAuth authentication and token storage.
    
    This class provides methods to handle OAuth authentication flow and
    securely store and retrieve tokens.
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize the OAuth manager.
        
        Args:
            env_file: Path to the .env file containing credentials
        """
        # Load environment variables from .env file
        load_dotenv(env_file)
        self.token_dir = Path("temp/tokens")
        self.token_dir.mkdir(parents=True, exist_ok=True)
        logger.info("OAuth manager initialized")
        
    def get_google_credentials(self, scopes: list, token_file: str = "google_token.json") -> Credentials:
        """
        Get Google OAuth credentials.
        
        Args:
            scopes: List of OAuth scopes to request
            token_file: Name of the file to store the token
            
        Returns:
            Google OAuth credentials
        """
        token_path = self.token_dir / token_file
        creds = None
        
        # Load token from file if it exists
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_info(
                    json.loads(token_path.read_text()), scopes)
            except Exception as e:
                logger.error(f"Error loading credentials from token file: {e}")
        
        # If credentials don't exist or are invalid, run the OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            # If still no valid credentials, run the OAuth flow
            if not creds:
                client_id = os.environ.get("GOOGLE_CLIENT_ID")
                client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
                
                if not client_id or not client_secret:
                    raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables")
                
                # Create a credentials.json-like dict from environment variables
                client_config = {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                    }
                }
                
                # Run the OAuth flow
                flow = InstalledAppFlow.from_client_config(client_config, scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials to the token file
            token_path.write_text(creds.to_json())
            logger.info(f"Saved new credentials to {token_path}")
        
        return creds
    
    def clear_token(self, token_file: str) -> None:
        """
        Clear a token file.
        
        Args:
            token_file: Name of the token file to clear
        """
        token_path = self.token_dir / token_file
        if token_path.exists():
            token_path.unlink()
            logger.info(f"Cleared token file: {token_path}")

# Singleton instance for global use
oauth_manager = OAuthManager()