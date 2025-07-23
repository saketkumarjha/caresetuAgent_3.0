"""
Enhanced LiveKit Calendar Actions for Business Automation Voice Agent
Implements comprehensive scheduling engine with real-time availability and booking workflows
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from google_calendar_integration import GoogleCalendarIntegration

class LiveKitCalendarActions:
    """
    Calendar actions for LiveKit voice agent integration
    Provides real-time scheduling capabilities during voice conversations
    """
    
    def __init__(self):
        """Initialize calendar actions with Google Calendar integration"""
        self.calendar = GoogleCalendarIntegration()
        
    async def check_availability(self, date: str) -> Dict[str, Any]:
        """
        Check availability for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            Dictionary with available slots
        """
        try:
            slots = self.calendar.check_availability(date)
            return {
                "success": True,
                "date": date,
                "available_slots": slots,
                "count": len(slots)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check availability"
            }
    
    async def book_appointment(self, 
                             customer_name: str,
                             customer_email: str,
                             preferred_date: str,
                             preferred_time: str,
                             appointment_type: str = 'consultation') -> Dict[str, Any]:
        """
        Book an appointment
        
        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            preferred_date: Date in YYYY-MM-DD format
            preferred_time: Time in HH:MM format
            appointment_type: Type of appointment
            
        Returns:
            Booking result
        """
        try:
            # Combine date and time
            datetime_str = f"{preferred_date}T{preferred_time}:00"
            
            # Book the appointment
            result = self.calendar.book_appointment(
                customer_name=customer_name,
                customer_email=customer_email,
                start_datetime=datetime_str,
                appointment_type=appointment_type,
                description=f"Appointment booked via CareSetu voice agent for {customer_name}"
            )
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to book appointment"
            }
    
    async def cancel_appointment(self, event_id: str) -> Dict[str, Any]:
        """
        Cancel an appointment
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Cancellation result
        """
        try:
            result = self.calendar.cancel_appointment(event_id)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cancel appointment"
            }
    
    async def get_upcoming_appointments(self, email: str = None) -> Dict[str, Any]:
        """
        Get upcoming appointments
        
        Args:
            email: Optional email to filter by
            
        Returns:
            List of upcoming appointments
        """
        try:
            appointments = self.calendar.get_upcoming_appointments(days_ahead=7)
            
            # Filter by email if provided
            if email:
                appointments = [
                    appt for appt in appointments 
                    if email.lower() in [att.lower() for att in appt.get('attendees', [])]
                ]
            
            return {
                "success": True,
                "appointments": appointments,
                "count": len(appointments)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve appointments"
            }