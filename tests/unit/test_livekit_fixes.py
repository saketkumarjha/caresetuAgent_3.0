"""
Test script to verify the fixed calendar methods
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the fixed calendar methods
from agent_calendar_fixes import (
    detect_calendar_intent,
    handle_calendar_request,
    _handle_availability_check,
    _handle_booking_request,
    _handle_cancellation_request,
    _handle_reschedule_request,
    _get_calendar_help,
    quick_book_appointment
)

# Mock agent class for testing
class MockAgent:
    def __init__(self):
        self.calendar = None
        logger.info("Mock agent initialized")

# Test calendar intent detection
def test_calendar_intent_detection():
    agent = MockAgent()
    
    # Test cases
    test_messages = [
        "I need to book an appointment",
        "What are your available slots tomorrow?",
        "Can I schedule a consultation?",
        "I want to cancel my appointment",
        "How do I reschedule my visit?",
        "Tell me about your services"  # Non-calendar message
    ]
    
    print("\n=== Testing Calendar Intent Detection ===")
    for message in test_messages:
        result = detect_calendar_intent(agent, message)
        print(f"Message: '{message}' -> Calendar intent: {result}")
    
    print("\nTest completed!")

# Test calendar help function
def test_calendar_help():
    agent = MockAgent()
    
    print("\n=== Testing Calendar Help Function ===")
    help_text = _get_calendar_help(agent)
    print(f"Calendar help text:\n{help_text}")
    
    print("\nTest completed!")

# Main test function
async def run_tests():
    print("\n=== LiveKit Calendar Fixes Test ===")
    
    # Run tests
    test_calendar_intent_detection()
    test_calendar_help()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(run_tests())