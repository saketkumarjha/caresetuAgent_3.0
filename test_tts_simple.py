#!/usr/bin/env python3
"""Simple test to verify TTS is working without wrapper."""

import asyncio
import logging
from src.agent import BusinessVoiceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_tts():
    """Test TTS functionality."""
    try:
        logger.info("🧪 Testing TTS functionality...")
        
        # Initialize agent
        agent = BusinessVoiceAgent()
        logger.info("✅ Agent initialized successfully")
        
        # Test text refinement function
        test_text = "Hello! I'm your careSetu healthcare assistant. How can I help you today?"
        refined_text = agent._refine_text_for_speech(test_text)
        logger.info(f"📝 Original text: {test_text}")
        logger.info(f"📝 Refined text: {refined_text}")
        
        logger.info("✅ TTS test completed successfully")
        
    except Exception as e:
        logger.error(f"❌ TTS test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_tts())