"""
Enhanced Voice Agent with Calendar Integration
Production-ready integration with your existing agent
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from google_calendar_integration import GoogleCalendarIntegration

logger = logging.getLogger("enhanced-voice-agent")

class EnhancedVoiceAgent:
    """
    Enhanced voice agent with calendar scheduling capabilities
    """
    
    def __init__(self):
        """Initialize the enhanced voice agent"""
        self.calendar = None
        self.customer_info = {}
        self.conversation_context = {}
        
        # Initialize calendar integration
        self._initialize_calendar()
    
    def _initialize_calendar(self):
        """Initialize Google Calendar integration"""
        try:
            self.calendar = GoogleCalendarIntegration()
            logger.info("✅ Calendar integration initialized successfully")
            print("✅ Calendar integration ready")
        except Exception as e:
            logger.error(f"❌ Failed to initialize calendar: {e}")
            print(f"⚠️  Calendar integration failed: {e}")
            self.calendar = None
    
    def detect_intent(self, user_message: str) -> str:
        """
        Detect user intent from message
        
        Args:
            user_message: User's message
            
        Returns:
            Intent type: 'scheduling', 'support', 'general'
        """
        message_lower = user_message.lower()
        
        # Scheduling intents
        scheduling_keywords = [
            'appointment', 'schedule', 'book', 'booking', 'available',
            'availability', 'time', 'date', 'cancel', 'reschedule',
            'modify', 'change', 'when', 'free'
        ]
        
        if any(keyword in message_lower for keyword in scheduling_keywords):
            return 'scheduling'
        
        # Support intents
        support_keywords = [
            'help', 'problem', 'issue', 'question', 'support',
            'service', 'billing', 'account', 'technical'
        ]
        
        if any(keyword in message_lower for keyword in support_keywords):
            return 'support'
        
        return 'general'
    
    async def handle_scheduling_request(self, user_message: str) -> str:
        """
        Handle scheduling-related requests
        
        Args:
            user_message: User's scheduling request
            
        Returns:
            Response message
        """
        if not self.calendar:
            return ("I apologize, but appointment scheduling is currently unavailable. "
                   "Please try again later or contact us directly.")
        
        message_lower = user_message.lower()
        
        try:
            # Check availability request
            if any(word in message_lower for word in ['available', 'availability', 'free', 'open']):
                return await self._handle_availability_check(user_message)
            
            # Book appointment request
            elif any(word in message_lower for word in ['book', 'schedule', 'appointment']):
                return await self._handle_booking_request(user_message)
            
            # Cancel appointment
            elif any(word in message_lower for word in ['cancel', 'delete']):
                return await self._handle_cancellation_request(user_message)
            
            # Reschedule appointment
            elif any(word in message_lower for word in ['reschedule', 'change', 'modify', 'move']):
                return await self._handle_reschedule_request(user_message)
            
            # General scheduling help
            else:
                return self._get_scheduling_help()
                
        except Exception as e:
            logger.error(f"Error handling scheduling request: {e}")
            return "I encountered an issue while processing your scheduling request. Please try again."
    
    async def _handle_availability_check(self, user_message: str) -> str:
        """Handle availability checking requests"""
        # Extract date preference (simplified - in production use NLP)
        today = datetime.now().date()
        check_date = today
        
        if 'tomorrow' in user_message.lower():
            check_date = today + timedelta(days=1)
        elif 'next week' in user_message.lower():
            check_date = today + timedelta(days=7)
        elif 'monday' in user_message.lower():
            # Find next Monday
            days_ahead = 0 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            check_date = today + timedelta(days=days_ahead)
        
        # Check availability
        slots = self.calendar.check_availability(check_date.strftime('%Y-%m-%d'))
        
        if not slots:
            return f"I don't have any available appointments for {check_date.strftime('%A, %B %d')}. Would you like me to check another date?"
        
        # Format response
        date_str = check_date.strftime('%A, %B %d')
        response = f"I have the following times available on {date_str}:\n"
        
        for i, slot in enumerate(slots[:4], 1):  # Show up to 4 slots
            response += f"{i}. {slot['start_time']}\n"
        
        response += "\nWhich time works best for you?"
        return response
    
    async def _handle_booking_request(self, user_message: str) -> str:
        """Handle appointment booking requests"""
        # Check if we have customer info
        if not self.customer_info.get('name') or not self.customer_info.get('email'):
            return ("I'd be happy to book an appointment for you! "
                   "First, may I get your name and email address?")
        
        # Check if we have a specific time request
        if not self.conversation_context.get('requested_time'):
            return ("What date and time would work best for you? "
                   "I can check our availability and book it right away.")
        
        # If we have all info, proceed with booking
        return await self._process_booking()
    
    async def _process_booking(self) -> str:
        """Process the actual booking"""
        try:
            customer_name = self.customer_info['name']
            customer_email = self.customer_info['email']
            requested_datetime = self.conversation_context['requested_time']
            
            result = self.calendar.book_appointment(
                customer_name=customer_name,
                customer_email=customer_email,
                start_datetime=requested_datetime,
                appointment_type='consultation',
                description=f'Appointment booked via voice agent for {customer_name}'
            )
            
            if result['success']:
                return (f"Perfect! I've successfully booked your appointment for "
                       f"{result['start_time']}. You'll receive a calendar invite "
                       f"at {customer_email} with all the details. "
                       f"Google Calendar will also send you reminder emails. "
                       f"Is there anything else I can help you with?")
            else:
                return (f"I apologize, but I wasn't able to book that appointment. "
                       f"{result['message']} Would you like me to check other available times?")
                
        except Exception as e:
            logger.error(f"Error processing booking: {e}")
            return "I encountered an issue while booking your appointment. Please try again."
    
    async def _handle_cancellation_request(self, user_message: str) -> str:
        """Handle appointment cancellation"""
        return ("I can help you cancel an appointment. "
               "Could you please provide your email address so I can look up your booking?")
    
    async def _handle_reschedule_request(self, user_message: str) -> str:
        """Handle appointment rescheduling"""
        return ("I can help you reschedule your appointment. "
               "Let me first find your existing booking, then we can pick a new time. "
               "What's your email address?")
    
    def _get_scheduling_help(self) -> str:
        """Get general scheduling help"""
        return ("I can help you with appointments! I can:\n"
               "• Check available appointment times\n"
               "• Book new appointments\n"
               "• Reschedule existing appointments\n"
               "• Cancel appointments\n\n"
               "What would you like to do?")
    
    def update_customer_info(self, name: str = None, email: str = None, phone: str = None):
        """Update customer information"""
        if name:
            self.customer_info['name'] = name
        if email:
            self.customer_info['email'] = email
        if phone:
            self.customer_info['phone'] = phone
    
    def set_requested_time(self, datetime_str: str):
        """Set the requested appointment time"""
        self.conversation_context['requested_time'] = datetime_str
    
    async def process_message(self, user_message: str) -> str:
        """
        Main message processing function
        
        Args:
            user_message: User's message
            
        Returns:
            Agent's response
        """
        # Detect intent
        intent = self.detect_intent(user_message)
        
        # Route to appropriate handler
        if intent == 'scheduling':
            return await self.handle_scheduling_request(user_message)
        elif intent == 'support':
            return await self.handle_support_request(user_message)
        else:
            return await self.handle_general_request(user_message)
    
    async def handle_support_request(self, user_message: str) -> str:
        """Handle support requests (integrate with your existing support system)"""
        # This is where you'd integrate with your existing support agent
        return ("I can help you with support questions. "
               "What specific issue are you experiencing?")
    
    async def handle_general_request(self, user_message: str) -> str:
        """Handle general requests"""
        return ("Hello! I'm your CareSetu Healthcare assistant. "
               "I can help you schedule appointments or answer questions about our services. "
               "How can I assist you today?")
    
    def get_business_hours(self) -> str:
        """Get business hours information"""
        if not self.calendar:
            return "Business hours information is currently unavailable."
        
        hours = self.calendar.business_hours
        return (f"Our business hours are {hours['start']} to {hours['end']} "
               f"({hours['timezone']}), Monday through Friday.")

# Example usage and testing
async def test_enhanced_agent():
    """Test the enhanced agent"""
    
    print("🤖 Testing Enhanced Voice Agent with Calendar")
    print("=" * 50)
    
    # Initialize agent
    agent = EnhancedVoiceAgent()
    
    # Test conversation scenarios
    test_scenarios = [
        "Hi, I'd like to book an appointment",
        "What times are available tomorrow?",
        "Can I schedule something for next week?",
        "I need to cancel my appointment",
        "What are your business hours?",
        "I have a technical problem"
    ]
    
    for scenario in test_scenarios:
        print(f"\n👤 Customer: {scenario}")
        response = await agent.process_message(scenario)
        print(f"🤖 Agent: {response}")
    
    print(f"\n✅ Enhanced agent testing completed!")

if __name__ == "__main__":
    asyncio.run(test_enhanced_agent())