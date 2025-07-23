"""
Complete Voice Agent Integration with Calendar
Ready for production use with your existing LiveKit setup
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from enhanced_voice_agent import EnhancedVoiceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("complete-agent")

class CompleteVoiceAgent:
    """
    Complete voice agent that integrates calendar with your existing systems
    """
    
    def __init__(self):
        """Initialize the complete agent"""
        self.enhanced_agent = EnhancedVoiceAgent()
        self.conversation_state = {}
        self.customer_session = {}
        
    async def handle_voice_input(self, transcript: str, customer_id: str = None) -> str:
        """
        Handle voice input from LiveKit STT
        
        Args:
            transcript: Speech-to-text transcript
            customer_id: Optional customer identifier
            
        Returns:
            Response text for TTS
        """
        try:
            # Store customer session
            if customer_id:
                self.customer_session['id'] = customer_id
            
            # Extract customer info from conversation if available
            await self._extract_customer_info(transcript)
            
            # Process the message
            response = await self.enhanced_agent.process_message(transcript)
            
            # Log the interaction
            logger.info(f"Customer: {transcript}")
            logger.info(f"Agent: {response}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling voice input: {e}")
            return "I apologize, but I encountered an issue. Could you please repeat that?"
    
    async def _extract_customer_info(self, transcript: str):
        """Extract customer information from conversation"""
        transcript_lower = transcript.lower()
        
        # Simple email extraction (in production, use better NLP)
        if '@' in transcript:
            words = transcript.split()
            for word in words:
                if '@' in word and '.' in word:
                    self.enhanced_agent.update_customer_info(email=word)
                    break
        
        # Simple name extraction (basic implementation)
        if any(phrase in transcript_lower for phrase in ['my name is', "i'm", 'this is']):
            # Extract name after these phrases
            for phrase in ['my name is', "i'm", 'this is']:
                if phrase in transcript_lower:
                    parts = transcript_lower.split(phrase)
                    if len(parts) > 1:
                        potential_name = parts[1].strip().split()[0:2]  # First two words
                        name = ' '.join(potential_name).title()
                        if name and len(name) > 1:
                            self.enhanced_agent.update_customer_info(name=name)
                    break
    
    def get_calendar_status(self) -> Dict[str, Any]:
        """Get calendar integration status"""
        return {
            'calendar_available': self.enhanced_agent.calendar is not None,
            'business_hours': self.enhanced_agent.get_business_hours() if self.enhanced_agent.calendar else None
        }
    
    async def quick_availability_check(self, date_str: str = None) -> str:
        """Quick availability check for specific date"""
        if not date_str:
            from datetime import datetime, timedelta
            date_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        return await self.enhanced_agent._handle_availability_check(f"available {date_str}")
    
    async def emergency_booking(self, customer_name: str, customer_email: str, datetime_str: str) -> Dict[str, Any]:
        """Emergency booking function for urgent appointments"""
        if not self.enhanced_agent.calendar:
            return {'success': False, 'message': 'Calendar not available'}
        
        try:
            result = self.enhanced_agent.calendar.book_appointment(
                customer_name=customer_name,
                customer_email=customer_email,
                start_datetime=datetime_str,
                appointment_type='consultation',
                description='Emergency booking via voice agent'
            )
            return result
        except Exception as e:
            return {'success': False, 'message': str(e)}

# Integration with your existing LiveKit agent
class LiveKitCalendarAgent:
    """
    Integration layer for LiveKit Agents framework
    """
    
    def __init__(self):
        """Initialize LiveKit calendar agent"""
        self.complete_agent = CompleteVoiceAgent()
        
    async def on_speech_recognized(self, transcript: str, participant_id: str = None) -> str:
        """
        Handle speech recognition from LiveKit
        
        Args:
            transcript: STT transcript
            participant_id: LiveKit participant ID
            
        Returns:
            Response for TTS
        """
        return await self.complete_agent.handle_voice_input(transcript, participant_id)
    
    def get_system_prompt(self) -> str:
        """Get system prompt for LLM integration"""
        return """
        You are a professional customer service agent for CareSetu Healthcare.
        
        You have access to real-time calendar scheduling capabilities and can:
        - Check appointment availability
        - Book appointments immediately
        - Handle appointment modifications
        - Provide business hours information
        
        Always be helpful, professional, and efficient. When booking appointments:
        1. Get customer name and email
        2. Confirm preferred date/time
        3. Book the appointment
        4. Confirm details
        
        Google Calendar will automatically send confirmation emails and reminders.
        """

# Testing and demonstration
async def test_complete_integration():
    """Test the complete integration"""
    
    print("🚀 Testing Complete Voice Agent Integration")
    print("=" * 55)
    
    # Initialize complete agent
    agent = CompleteVoiceAgent()
    
    # Test conversation flow
    conversation = [
        "Hi, I need to schedule an appointment",
        "My name is John Doe",
        "My email is john.doe@example.com", 
        "What times are available tomorrow?",
        "2 PM works for me",
        "Yes, please book it"
    ]
    
    print("🎭 Simulating Complete Conversation:")
    print("-" * 40)
    
    for i, message in enumerate(conversation, 1):
        print(f"\n👤 Customer: {message}")
        response = await agent.handle_voice_input(message, f"customer_{i}")
        print(f"🤖 Agent: {response}")
    
    # Test calendar status
    print(f"\n📊 Calendar Status:")
    status = agent.get_calendar_status()
    print(f"   Calendar Available: {status['calendar_available']}")
    if status['business_hours']:
        print(f"   Business Hours: {status['business_hours']}")
    
    # Test quick availability
    print(f"\n⚡ Quick Availability Check:")
    availability = await agent.quick_availability_check()
    print(f"   {availability}")

if __name__ == "__main__":
    asyncio.run(test_complete_integration())