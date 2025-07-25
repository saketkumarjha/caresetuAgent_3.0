"""
Railway Optimized Configuration - Environment Variables Only
Minimal memory footprint configuration for Railway deployment
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables (Railway will inject these)
load_dotenv()

@dataclass
class LiveKitConfig:
    """LiveKit Cloud configuration."""
    url: str
    api_key: str
    api_secret: str
    
    @classmethod
    def from_env(cls) -> 'LiveKitConfig':
        """Create config from Railway environment variables."""
        url = os.getenv('LIVEKIT_URL')
        api_key = os.getenv('LIVEKIT_API_KEY')
        api_secret = os.getenv('LIVEKIT_API_SECRET')
        
        if not all([url, api_key, api_secret]):
            raise ValueError(
                "Missing LiveKit environment variables. "
                "Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in Railway"
            )
        
        return cls(url=url, api_key=api_key, api_secret=api_secret)

@dataclass
class AssemblyAIConfig:
    """AssemblyAI configuration."""
    api_key: str
    
    @classmethod
    def from_env(cls) -> 'AssemblyAIConfig':
        """Create config from Railway environment variables."""
        api_key = os.getenv('ASSEMBLYAI_API_KEY')
        
        if not api_key:
            raise ValueError("Missing ASSEMBLYAI_API_KEY environment variable in Railway")
        
        return cls(api_key=api_key)

@dataclass
class GoogleConfig:
    """Google services configuration."""
    api_key: str
    
    @classmethod
    def from_env(cls) -> 'GoogleConfig':
        """Create config from Railway environment variables."""
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            raise ValueError("Missing GOOGLE_API_KEY environment variable in Railway")
        
        return cls(api_key=api_key)

@dataclass
class RailwayConfig:
    """Railway-specific configuration."""
    port: int
    environment: str
    
    @classmethod
    def from_env(cls) -> 'RailwayConfig':
        """Create Railway config from environment variables."""
        port = int(os.getenv('PORT', 8080))
        environment = os.getenv('RAILWAY_ENVIRONMENT', 'production')
        
        return cls(port=port, environment=environment)

@dataclass
class AgentConfig:
    """Complete Railway-optimized agent configuration."""
    livekit: LiveKitConfig
    assemblyai: AssemblyAIConfig
    google: GoogleConfig
    railway: RailwayConfig
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Create complete config from Railway environment variables."""
        return cls(
            livekit=LiveKitConfig.from_env(),
            assemblyai=AssemblyAIConfig.from_env(),
            google=GoogleConfig.from_env(),
            railway=RailwayConfig.from_env()
        )

# Global config instance for Railway
try:
    config = AgentConfig.from_env()
    print("✅ Railway configuration loaded successfully")
    print(f"   Port: {config.railway.port}")
    print(f"   Environment: {config.railway.environment}")
except ValueError as e:
    print(f"❌ Railway configuration error: {e}")
    print("Please set the required environment variables in Railway dashboard")
    config = None