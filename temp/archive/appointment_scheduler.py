"""
Appointment Scheduler for Voice Agent
Integrates with existing agent framework
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from calendar_agent_actions import CalendarAgentActions

class AppointmentScheduler:
    """
    Main appointment scheduling coordinator
    """
    
    def __init__(self, credentials_file: str = 'credentials.json'):
        """Initialize appointment scheduler"""
        self.calendar_actions = CalendarAgentActions(credentials_file)
        
        # Business configuration
        self.business_config = {
            'name': 'CareSetu Healthcare',
            'timezone': 'America/New_York',
            'business_hours': {
                'monday': {'start': '09:00', 'end': '17:00'},
                'tuesday': {'start': '09:00', 'end': '17:00'},
                'wednesday': {'start': '09:00', 'end': '17:00'},
                'thursday': {'start': '09:00', 'end': '17:00'},
                'friday': {'start': '09:00', 'end': '17:00'},
                'saturday': {'start': '10:00', 'end': '14:00'},
                'sunday': {'start': 'closed', 'end': 'closed'}
            }
        }
        
        # Common scheduling phrases for intent detection
        self.scheduling_intents = [
            'book appointment', 'schedule appointment', 'make appointment',
            'book consultation', 'schedule meeting', 'set up appointment',
            'available times', 'check availability', 'when are you free',
            'cancel appointment', 'reschedule appointment', 'change appointment'
        ]
    
    def detect_scheduling_intent(self, user_message: str) -> bool:
        """
        Detect if user wants to schedule something
        
        Args:
            user_message: User's message
            
        Returns:
            True if scheduling intent detected
        """
        message_lower = user_message.lower()
        return any(intent in message_lower for intent in self.scheduling_intents)
    
    async def handle_scheduling_request(self, user_message: str, customer_info: Dict[str, Any] = None) -> str:
        """
        Handle scheduling-related requests
        
        Args:
            user_message: User's message
            customer_info: Customer information if available
            
        Returns:
            Response message
        """
        message_lower = user_message.lower()
        
        # Check availability request
        if any(phrase in message_lower for phrase in ['available', 'free', 'open']):
            return await self._handle_availability_check(user_message)
        
        # Book appointment request
        elif any(phrase in message_lower for phrase in ['book', 'schedule', 'make']):
            return await self._handle_booking_request(user_message, customer_info)
        
        # Cancel appointment request
        elif any(phrase in message_lower for phrase in ['cancel', 'delete']):
            return await self._handle_cancellation_request(user_message)
        
        # Reschedule request
        elif any(phrase in message_lower for phrase in ['reschedule', 'change', 'move']):
            return await self._handle_reschedule_request(user_message)
        
        # General scheduling help
        else:
            return self._get_scheduling_help()
    
    async def _handle_availability_check(self, user_message: str) -> str:
        """Handle availability checking"""
        # Extract date from message (simplified - in production use NLP)
        today = datetime.now().date()
        
        # Default to today if no specific date mentioned
        check_date = today.strftime('%Y-%m-%d')
        
        # Check for common date references
        if 'tomorrow' in user_message.lower():
            check_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'next week' in user_message.lower():
            check_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        
        return await self.calendar_actions.check_availability(check_date)
    
    async def _handle_booking_request(self, user_message: str, customer_info: Dict[str, Any] = None) -> str:
        """Handle appointment booking"""
        if not customer_info or not customer_info.get('email'):
            return ("To book an appointment, I'll need your name and email address. "
                   "Could you please provide that information?")
        
        # In a real implementation, you'd use NLP to extract:
        # - Preferred date/time
        # - Appointment type
        # - Any special requirements
        
        return ("I'd be happy to help you book an appointment! "
               "What date and time would work best for you? "
               "I can check our availability and book it right away.")
    
    async def _handle_cancellation_request(self, user_message: str) -> str:
        """Handle appointment cancellation"""
        return ("To cancel an appointment, I'll need to look up your existing booking. "
               "Could you provide your email address or the appointment date?")
    
    async def _handle_reschedule_request(self, user_message: str) -> str:
        """Handle appointment rescheduling"""
        return ("I can help you reschedule your appointment. "
               "Let me first find your existing booking, then we can pick a new time.")
    
    def _get_scheduling_help(self) -> str:
        """Get general scheduling help"""
        return (f"I can help you with appointments at {self.business_config['name']}! "
               "I can:\n"
               "• Check available appointment times\n"
               "• Book new appointments\n"
               "• Reschedule existing appointments\n"
               "• Cancel appointments\n\n"
               "What would you like to do?")
    
    def get_business_hours_info(self) -> str:
        """Get formatted business hours information"""
        hours_info = []
        for day, hours in self.business_config['business_hours'].items():
            if hours['start'] == 'closed':
                hours_info.append(f"{day.title()}: Closed")
            else:
                hours_info.append(f"{day.title()}: {hours['start']} - {hours['end']}")
        
        return "Our business hours are:\n" + "\n".join(hours_info)
    
    async def quick_book_appointment(self, 
                                   customer_name: str,
                                   customer_email: str,
                                   preferred_date: str,
                                   preferred_time: str,
                                   appointment_type: str = 'consultation') -> str:
        """
        Quick booking for voice agent
        
        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            preferred_date: Date in YYYY-MM-DD format
            preferred_time: Time in HH:MM format
            appointment_type: Type of appointment
            
        Returns:
            Booking result message
        """
        try:
            # Combine date and time
            datetime_str = f"{preferred_date}T{preferred_time}:00"
            
            # Try to book the appointment
            result = await self.calendar_actions.book_appointment(
                customer_name=customer_name,
                customer_email=customer_email,
                start_datetime=datetime_str,
                appointment_type=appointment_type
            )
            
            return result
            
        except Exception as e:
            return f"Error booking appointment: {str(e)}"
    
    def get_function_contexts(self):
        """Get function contexts for LLM integration"""
        return self.calendar_actions.get_function_contexts()
    
    async def execute_calendar_function(self, function_name: str, **kwargs) -> str:
        """Execute calendar function"""
        return await self.calendar_actions.execute_function(function_name, **kwargs)