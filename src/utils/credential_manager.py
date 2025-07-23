"""
Credential Manager Module

This module provides secure credential management functionality for the application.
It handles loading credentials from environment variables and provides a secure
interface for accessing them throughout the application.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CredentialManager:
    """
    Manages secure access to application credentials.
    
    This class provides methods to securely access credentials from environment
    variables and handles credential rotation and security.
    """
    
    def __init__(self, env_file: str = ".env"):
        """
        Initialize the credential manager.
        
        Args:
            env_file: Path to the .env file containing credentials
        """
        # Load environment variables from .env file
        load_dotenv(env_file)
        self.credentials_cache = {}
        logger.info("Credential manager initialized")
        
    def get_credential(self, key: str, default: Any = None) -> Any:
        """
        Get a credential by key.
        
        Args:
            key: The credential key (environment variable name)
            default: Default value if credential is not found
            
        Returns:
            The credential value or default if not found
        """
        # Check if we've already cached this credential
        if key in self.credentials_cache:
            return self.credentials_cache[key]
            
        # Get from environment variable
        value = os.environ.get(key, default)
        
        # Log access (without the actual value)
        if value is not None and value != default:
            logger.info(f"Credential accessed: {key}")
        else:
            logger.warning(f"Credential not found: {key}")
            
        # Cache for future use
        self.credentials_cache[key] = value
        return value
        
    def get_google_credentials(self) -> Dict[str, str]:
        """
        Get Google API credentials.
        
        Returns:
            Dictionary containing Google API credentials
        """
        return {
            "api_key": self.get_credential("GOOGLE_API_KEY"),
            "client_id": self.get_credential("GOOGLE_CLIENT_ID"),
            "client_secret": self.get_credential("GOOGLE_CLIENT_SECRET")
        }
        
    def get_livekit_credentials(self) -> Dict[str, str]:
        """
        Get LiveKit credentials.
        
        Returns:
            Dictionary containing LiveKit credentials
        """
        return {
            "url": self.get_credential("LIVEKIT_URL"),
            "api_key": self.get_credential("LIVEKIT_API_KEY"),
            "api_secret": self.get_credential("LIVEKIT_API_SECRET")
        }
        
    def create_credentials_file(self, file_path: str, template_data: Dict[str, Any]) -> None:
        """
        Create a credentials file with values from environment variables.
        
        This method is useful for creating credential files required by libraries
        that don't support direct environment variable usage.
        
        Args:
            file_path: Path where the credentials file should be saved
            template_data: Template dictionary with placeholders for credentials
        """
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        # Replace placeholders with actual credentials
        for key, value in template_data.items():
            if isinstance(value, str) and value.startswith("ENV:"):
                env_var = value[4:]  # Remove "ENV:" prefix
                template_data[key] = self.get_credential(env_var, "")
                
        # Write to file
        with open(file_path, 'w') as f:
            json.dump(template_data, f, indent=2)
            
        logger.info(f"Created credentials file: {file_path}")
        
    @staticmethod
    def create_example_env_file(output_path: str = ".env.example") -> None:
        """
        Create an example .env file with placeholder values.
        
        Args:
            output_path: Path where the example .env file should be saved
        """
        example_content = """# Google Calendar API Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# LiveKit Configuration
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Other API Keys
ASSEMBLYAI_API_KEY=your_assemblyai_key
CARTESIA_API_KEY=your_cartesia_key
"""
        with open(output_path, 'w') as f:
            f.write(example_content)
            
        logger.info(f"Created example environment file: {output_path}")


# Singleton instance for global use
credential_manager = CredentialManager()