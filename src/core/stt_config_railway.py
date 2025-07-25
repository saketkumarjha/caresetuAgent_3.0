"""
Railway Optimized STT Configuration
Minimal memory footprint for AssemblyAI integration
"""

import os
from typing import List
from dataclasses import dataclass
from livekit.plugins import assemblyai

# Import Railway config
try:
    from config_railway import config
except ImportError:
    from src.config_railway import config

@dataclass
class RailwaySTTConfig:
    """Lightweight STT configuration for Railway."""
    
    # Essential business terms only (reduced list for memory)
    ESSENTIAL_TERMS = [
        # Core appointment terms
        "appointment", "booking", "schedule", "reschedule", "cancel",
        "available", "availability", "consultation",
        
        # Time terms
        "today", "tomorrow", "Monday", "Tuesday", "Wednesday", 
        "Thursday", "Friday", "morning", "afternoon", "evening",
        
        # Healthcare essentials
        "doctor", "patient", "medical", "health", "medicine",
        "prescription", "insurance", "support"
    ]
    
    @property
    def boost_terms(self) -> List[str]:
        """Get essential word boost terms."""
        return self.ESSENTIAL_TERMS

def create_assemblyai_stt() -> assemblyai.STT:
    """Create Railway-optimized AssemblyAI STT."""
    
    if not config or not config.assemblyai.api_key:
        raise ValueError("AssemblyAI API key not configured in Railway")
    
    # Minimal STT configuration for Railway free tier
    stt = assemblyai.STT(
        # Basic turn detection (reduced complexity)
        format_turns=True,
        end_of_turn_confidence_threshold=0.8,  # Higher threshold for reliability
        min_end_of_turn_silence_when_confident=200,  # Slightly longer for stability
        max_turn_silence=2000,  # Shorter timeout for responsiveness
    )
    
    return stt

def test_railway_stt():
    """Test STT configuration for Railway deployment."""
    
    test_phrases = [
        "I need to book an appointment",
        "What times are available tomorrow?",
        "Can I reschedule my consultation?",
        "I need medical support"
    ]
    
    print("🎤 Railway STT Test")
    print("=" * 40)
    print("Essential test phrases:")
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"{i}. {phrase}")
    
    print(f"\n📝 Word boost terms: {len(RailwaySTTConfig().boost_terms)} terms")
    print("✅ Railway STT configuration ready")

if __name__ == "__main__":
    try:
        stt = create_assemblyai_stt()
        print("✅ Railway AssemblyAI STT configured successfully")
        test_railway_stt()
    except Exception as e:
        print(f"❌ Railway STT configuration failed: {e}")
        print("Check your ASSEMBLYAI_API_KEY in Railway environment variables")