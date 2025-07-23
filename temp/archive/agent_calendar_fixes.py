"""
Calendar method fixes for BusinessVoiceAgent
"""

# Calendar Integration Methods
def detect_calendar_intent(self, user_message: str) -> bool:
    """
    Detect if user wants to schedule something
    
    Args:
        user_message: User's message
        
    Returns:
        True if calendar/scheduling intent detected
    """
    message_lower = user_message.lower()
    calendar_keywords = [
        'appointment', 'schedule', 'book', 'booking', 'available',
        'availability', 'time', 'date', 'cancel', 'reschedule',
        'modify', 'change', 'when', 'free', 'slots'
    ]
    return any(keyword in message_lower for keyword in calendar_keywords)

async def handle_calendar_request(self, user_message: str, session_id: str = None) -> str:
    """
    Handle calendar-related requests
    
    Args:
        user_message: User's message
        session_id: Session identifier
        
    Returns:
        Response message
    """
    if not self.calendar:
        return ("I apologize, but appointment scheduling is currently unavailable. "
               "Please try again later or contact us directly at saket@jha.com")
    
    message_lower = user_message.lower()
    
    try:
        # Check availability request
        if any(word in message_lower for word in ['available', 'availability', 'free', 'open', 'slots']):
            return await self._handle_availability_check(user_message)
        
        # Book appointment request
        elif any(word in message_lower for word in ['book', 'schedule', 'appointment', 'make']):
            return await self._handle_booking_request(user_message, session_id)
        
        # Cancel appointment
        elif any(word in message_lower for word in ['cancel', 'delete']):
            return await self._handle_cancellation_request(user_message)
        
        # Reschedule appointment
        elif any(word in message_lower for word in ['reschedule', 'change', 'move']):
            return await self._handle_reschedule_request(user_message)
        
        # General scheduling help
        else:
            return self._get_calendar_help()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling calendar request: {e}")
        return ("I encountered an issue while processing your scheduling request. "
               "Please try again.")

async def _handle_availability_check(self, user_message: str) -> str:
    """Handle availability checking requests"""
    try:
        from datetime import datetime, timedelta
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract date preference (simplified - in production use better NLP)
        today = datetime.now().date()
        check_date = today.strftime('%Y-%m-%d')
        
        # Check for common date references
        message_lower = user_message.lower()
        if 'tomorrow' in message_lower:
            check_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'next week' in message_lower:
            check_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
        elif 'monday' in message_lower:
            days_ahead = (0 - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'tuesday' in message_lower:
            days_ahead = (1 - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'wednesday' in message_lower:
            days_ahead = (2 - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'thursday' in message_lower:
            days_ahead = (3 - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        elif 'friday' in message_lower:
            days_ahead = (4 - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # Check availability
        slots = self.calendar.check_availability(check_date)
        if not slots:
            return f"I don't have any available appointment slots for {check_date}. Would you like me to check a different date?"
        
        # Format available slots
        date_obj = datetime.strptime(check_date, '%Y-%m-%d')
        day_name = date_obj.strftime('%A, %B %d')
        slots_text = []
        for i, slot in enumerate(slots[:5], 1):  # Show first 5 slots
            slots_text.append(f"{slot['start_time']}")
        
        return (f"I have the following appointment times available for {day_name}:\n\n"
               f"{', '.join(slots_text)}\n\n"
               f"Which time works best for you? I can book it right away once you provide your name and email.")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking availability: {e}")
        return "I'm having trouble checking availability right now. Please try again or contact our support team."

async def _handle_booking_request(self, user_message: str, session_id: str = None) -> str:
    """Handle appointment booking requests"""
    try:
        # This is a simplified booking flow - in production you'd use NLP to extract details
        return ("I'd be happy to help you book an appointment! To get started, I'll need:\n\n"
               "1. Your full name\n"
               "2. Your email address\n"
               "3. Your preferred date and time\n\n"
               "What date and time would work best for you? I can check availability and book it immediately.")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling booking request: {e}")
        return "I'm having trouble with the booking system right now. Please try again or contact our support team."

async def _handle_cancellation_request(self, user_message: str) -> str:
    """Handle appointment cancellation requests"""
    try:
        return ("I can help you cancel your appointment. To find your booking, I'll need either:\n\n"
               "• Your email address, or\n"
               "• The appointment date and time\n\n"
               "Could you please provide one of these details?")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling cancellation request: {e}")
        return "I'm having trouble accessing the cancellation system right now. Please try again or contact our support team."

async def _handle_reschedule_request(self, user_message: str) -> str:
    """Handle appointment rescheduling requests"""
    try:
        return ("I can help you reschedule your appointment. First, let me find your existing booking.\n\n"
               "Please provide either:\n"
               "• Your email address, or\n"
               "• Your current appointment date and time\n\n"
               "Then I'll show you available times to reschedule to.")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error handling reschedule request: {e}")
        return "I'm having trouble with the rescheduling system right now. Please try again or contact our support team."

def _get_calendar_help(self) -> str:
    """Get general calendar/scheduling help"""
    return ("I can help you with appointments at CareSetu Healthcare! Here's what I can do:\n\n"
           "• **Check availability** - \"What times are available tomorrow?\"\n"
           "• **Book appointments** - \"I'd like to schedule an appointment\"\n"
           "• **Cancel appointments** - \"I need to cancel my appointment\"\n"
           "• **Reschedule appointments** - \"Can I reschedule my appointment?\"\n\n"
           "Our business hours are Monday to Friday, 9 AM to 6 PM.\n\n"
           "What would you like to do?")

async def quick_book_appointment(self, 
                               customer_name: str,
                               customer_email: str,
                               preferred_date: str,
                               preferred_time: str,
                               appointment_type: str = 'consultation') -> str:
    """
    Quick booking interface for voice agent
    
    Args:
        customer_name: Customer's name
        customer_email: Customer's email
        preferred_date: Date in YYYY-MM-DD format
        preferred_time: Time in HH:MM format
        appointment_type: Type of appointment
        
    Returns:
        Booking result message
    """
    if not self.calendar:
        return "Sorry, appointment booking is not available right now."
    
    try:
        # Combine date and time
        datetime_str = f"{preferred_date}T{preferred_time}:00"
        
        # Try to book the appointment
        result = self.calendar.book_appointment(
            customer_name=customer_name,
            customer_email=customer_email,
            start_datetime=datetime_str,
            appointment_type=appointment_type,
            description=f"Appointment booked via CareSetu voice agent for {customer_name}"
        )
        
        if result['success']:
            return (f"✅ Perfect! I've booked your {appointment_type} appointment for "
                   f"{result['start_time']} on {preferred_date}.\n\n"
                   f"📧 Google Calendar will automatically send you:\n"
                   f"• A calendar invitation to {customer_email}\n"
                   f"• Email reminders 24 hours and 1 hour before your appointment\n\n"
                   f"Your appointment ID is: {result['event_id']}\n\n"
                   f"Is there anything else I can help you with?")
        else:
            return f"I'm sorry, I couldn't book that appointment: {result['message']}. Would you like to try a different time?"
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in quick booking: {e}")
        return f"I encountered an error while booking your appointment: {str(e)}. Please try again or contact our support team."