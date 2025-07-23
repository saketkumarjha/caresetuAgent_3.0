"""Configuration management for the Voice Agent."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class LiveKitConfig:
    """LiveKit Cloud configuration."""
    url: str
    api_key: str
    api_secret: str
    
    @classmethod
    def from_env(cls) -> 'LiveKitConfig':
        """Create config from environment variables."""
        url = os.getenv('LIVEKIT_URL')
        api_key = os.getenv('LIVEKIT_API_KEY')
        api_secret = os.getenv('LIVEKIT_API_SECRET')
        
        if not all([url, api_key, api_secret]):
            raise ValueError(
                "Missing required LiveKit environment variables. "
                "Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET"
            )
        
        return cls(url=url, api_key=api_key, api_secret=api_secret)

@dataclass
class AssemblyAIConfig:
    """AssemblyAI configuration."""
    api_key: str
    
    @classmethod
    def from_env(cls) -> 'AssemblyAIConfig':
        """Create config from environment variables."""
        api_key = os.getenv('ASSEMBLYAI_API_KEY')
        
        if not api_key:
            raise ValueError("Missing ASSEMBLYAI_API_KEY environment variable")
        
        return cls(api_key=api_key)

@dataclass
class GoogleConfig:
    """Google Gemini configuration."""
    api_key: str
    
    @classmethod
    def from_env(cls) -> 'GoogleConfig':
        """Create config from environment variables."""
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            raise ValueError("Missing GOOGLE_API_KEY environment variable")
        
        return cls(api_key=api_key)

@dataclass
class ElevenLabsConfig:
    """ElevenLabs configuration."""
    api_key: Optional[str]
    
    @classmethod
    def from_env(cls) -> 'ElevenLabsConfig':
        """Create config from environment variables."""
        api_key = os.getenv('ELEVENLABS_API_KEY')
        return cls(api_key=api_key)

@dataclass
class CartesiaConfig:
    """Cartesia TTS configuration."""
    api_key: Optional[str]
    
    @classmethod
    def from_env(cls) -> 'CartesiaConfig':
        """Create config from environment variables."""
        api_key = os.getenv('CARTESIA_API_KEY')
        return cls(api_key=api_key)

@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    redis_url: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables."""
        db_url = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/voice_agent')
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        return cls(url=db_url, redis_url=redis_url)

@dataclass
class CRMConfig:
    """CRM integration configuration."""
    api_url: Optional[str]
    api_key: Optional[str]
    
    @classmethod
    def from_env(cls) -> 'CRMConfig':
        """Create config from environment variables."""
        api_url = os.getenv('CRM_API_URL')
        api_key = os.getenv('CRM_API_KEY')
        
        return cls(api_url=api_url, api_key=api_key)

@dataclass
class AgentConfig:
    """Complete agent configuration."""
    livekit: LiveKitConfig
    assemblyai: AssemblyAIConfig
    google: GoogleConfig
    elevenlabs: ElevenLabsConfig
    cartesia: CartesiaConfig
    database: DatabaseConfig
    crm: CRMConfig
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Create complete config from environment variables."""
        return cls(
            livekit=LiveKitConfig.from_env(),
            assemblyai=AssemblyAIConfig.from_env(),
            google=GoogleConfig.from_env(),
            elevenlabs=ElevenLabsConfig.from_env(),
            cartesia=CartesiaConfig.from_env(),
            database=DatabaseConfig.from_env(),
            crm=CRMConfig.from_env()
        )

# Global config instance
try:
    config = AgentConfig.from_env()
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please copy .env.example to .env and fill in your API keys")
    config = None