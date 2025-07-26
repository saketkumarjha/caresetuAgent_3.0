"""
Railway Production Configuration
Optimized for Railway's cloud deployment platform
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class RailwayConfig:
    """Railway deployment configuration."""
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
    """Simplified Railway agent configuration."""
    railway: RailwayConfig
    
    # Direct environment variable access for API keys
    @property
    def livekit_url(self) -> str:
        return os.getenv('LIVEKIT_URL', '')
    
    @property
    def livekit_api_key(self) -> str:
        return os.getenv('LIVEKIT_API_KEY', '')
    
    @property
    def livekit_api_secret(self) -> str:
        return os.getenv('LIVEKIT_API_SECRET', '')
    
    @property
    def assemblyai_api_key(self) -> str:
        return os.getenv('ASSEMBLYAI_API_KEY', '')
    
    @property
    def google_api_key(self) -> str:
        return os.getenv('GOOGLE_API_KEY', '')
    
    @classmethod
    def from_env(cls) -> 'AgentConfig':
        """Create config from Railway environment variables."""
        return cls(railway=RailwayConfig.from_env())
    
    def validate(self) -> bool:
        """Validate required environment variables."""
        required_vars = [
            'LIVEKIT_URL',
            'LIVEKIT_API_KEY', 
            'LIVEKIT_API_SECRET',
            'ASSEMBLYAI_API_KEY',
            'GOOGLE_API_KEY'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            print(f"❌ Missing environment variables: {', '.join(missing)}")
            print("Please set these in your Railway dashboard")
            return False
        
        return True

# Global config instance
try:
    config = AgentConfig.from_env()
    if config.validate():
        print("✅ Railway configuration loaded successfully")
        print(f"   Port: {config.railway.port}")
        print(f"   Environment: {config.railway.environment}")
    else:
        config = None
except Exception as e:
    print(f"❌ Railway configuration error: {e}")
    config = None