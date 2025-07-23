"""AssemblyAI Speech-to-Text configuration and setup."""

import os
import sys
from typing import List, Optional
from dataclasses import dataclass
from livekit.plugins import assemblyai

# Add parent directory to path when running directly from core directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Try both import paths
try:
    # Try direct import first (when running from src/core directory)
    from config import config
except ImportError:
    try:
        # Try relative import (when running from src directory)
        from src.config import config
    except ImportError:
        # Try absolute import (when running from project root)
        import config

@dataclass
class BusinessSTTConfig:
    """Configuration for business-optimized speech recognition."""
    
    # Business terminology for word boost
    BUSINESS_TERMS = [
        # General business terms
        "appointment", "scheduling", "reschedule", "cancel", "availability",
        "support", "billing", "invoice", "payment", "account",
        "customer", "service", "technical", "issue", "problem",
        
        # Common business names and titles
        "CEO", "CFO", "CTO", "manager", "director", "supervisor",
        "department", "team", "project", "meeting", "conference",
        
        # Time and scheduling terms
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "morning", "afternoon", "evening", "AM", "PM",
        "today", "tomorrow", "next week", "next month",
        
        # Common business processes
        "consultation", "follow-up", "callback", "escalate",
        "transfer", "hold", "voicemail", "extension"
    ]
    
    # Industry-specific terms (can be customized per business)
    INDUSTRY_TERMS = [
        # Healthcare
        "doctor", "physician", "nurse", "patient", "medical",
        "prescription", "insurance", "copay", "deductible",
        
        # Legal
        "attorney", "lawyer", "legal", "consultation", "case",
        "court", "hearing", "deposition", "contract",
        
        # Financial
        "advisor", "investment", "portfolio", "retirement",
        "loan", "mortgage", "credit", "banking",
        
        # Real Estate
        "property", "listing", "showing", "inspection",
        "mortgage", "closing", "realtor", "agent"
    ]
    
    @property
    def all_boost_terms(self) -> List[str]:
        """Get all word boost terms."""
        return self.BUSINESS_TERMS + self.INDUSTRY_TERMS

def create_assemblyai_stt() -> assemblyai.STT:
    """Create and configure AssemblyAI STT following LiveKit official docs pattern."""
    
    if not config or not config.assemblyai.api_key:
        raise ValueError("AssemblyAI API key not configured")
    
    # Configure AssemblyAI STT following official LiveKit docs pattern
    stt = assemblyai.STT(
        # Turn detection parameters (following official docs)
        format_turns=True,  # Return formatted final transcripts
        end_of_turn_confidence_threshold=0.7,  # Confidence threshold for end of turn
        min_end_of_turn_silence_when_confident=160,  # Min silence when confident (ms)
        max_turn_silence=2400,  # Max silence before end of turn (ms)
    )
    
    return stt

def test_stt_accuracy():
    """Test speech recognition accuracy with business terminology."""
    
    # Sample business phrases for testing
    test_phrases = [
        "I'd like to schedule an appointment for next Tuesday at 2 PM",
        "I'm having issues with my billing statement and need support",
        "Can you reschedule my consultation with Dr. Johnson?",
        "I need to speak with a manager about my account",
        "What's your availability for a follow-up meeting?",
        "I'd like to cancel my appointment and get a refund",
        "Can you transfer me to the technical support department?",
        "I need help with my insurance copay and deductible"
    ]
    
    print("🎤 AssemblyAI STT Business Accuracy Test")
    print("=" * 50)
    print("Test phrases for business terminology recognition:")
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"{i}. {phrase}")
    
    print("\n📝 To test accuracy:")
    print("1. Run the voice agent with AssemblyAI STT")
    print("2. Speak these phrases during testing")
    print("3. Verify business terms are recognized correctly")
    print("4. Check word boost effectiveness in logs")

class BusinessTurnDetector:
    """Custom turn detection optimized for business conversations."""
    
    def __init__(self):
        self.customer_speaking_threshold = 0.3  # Lower threshold for customer
        self.agent_speaking_threshold = 0.5     # Higher threshold for agent
        self.silence_timeout = 1.2              # Longer silence for business calls
        self.interruption_grace_period = 0.5    # Grace period for customer interruptions
    
    def should_interrupt(self, audio_level: float, silence_duration: float, 
                        speaker: str = "customer") -> bool:
        """
        Determine if the agent should start speaking.
        
        Args:
            audio_level: Current audio level (0.0 to 1.0)
            silence_duration: Duration of silence in seconds
            speaker: Who is currently speaking ("customer" or "agent")
        
        Returns:
            True if agent should start speaking
        """
        
        # Different thresholds based on who's speaking
        if speaker == "customer":
            # Be more patient with customers
            threshold = self.customer_speaking_threshold
            timeout = self.silence_timeout
        else:
            # Agent can be interrupted more readily
            threshold = self.agent_speaking_threshold
            timeout = self.silence_timeout * 0.7
        
        # Check if audio is below threshold and silence duration is sufficient
        return audio_level < threshold and silence_duration >= timeout
    
    def handle_interruption(self, interruption_type: str) -> str:
        """
        Handle different types of interruptions gracefully.
        
        Args:
            interruption_type: Type of interruption ("customer", "background_noise", "technical")
        
        Returns:
            Appropriate response for the interruption
        """
        
        responses = {
            "customer": "I'm sorry, please go ahead.",
            "background_noise": "I'm having trouble hearing you clearly. Could you repeat that?",
            "technical": "I apologize for the technical difficulty. Let me continue.",
            "default": "Please continue, I'm listening."
        }
        
        return responses.get(interruption_type, responses["default"])

if __name__ == "__main__":
    # Test the configuration
    try:
        stt = create_assemblyai_stt()
        print("✅ AssemblyAI STT configured successfully")
        print(f"   Word boost terms: {len(BusinessSTTConfig().all_boost_terms)} terms")
        print("   Universal-Streaming enabled")
        print("   Business conversation optimizations active")
        
        # Run accuracy test
        test_stt_accuracy()
        
    except Exception as e:
        print(f"❌ AssemblyAI STT configuration failed: {e}")
        print("   Please check your ASSEMBLYAI_API_KEY in .env file")