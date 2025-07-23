"""
LiveKit Agent Actions for Calendar Integration
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
try:
    from livekit.agents import llm
except ImportError:
    # Fallback for testing without LiveKit
    class MockLLM:
        class FunctionContext:
            def __init__(self, name, description, parameters):
                self.name = name
                self.description = description
                self.parameters = parameters
    llm = MockLLM()

from google_calendar_integration import GoogleCalendarIntegration

class CalendarAgentActions:
    """
    LiveKit agent actions for calendar operations
    """
    
    def __init__(self, credentials_file: str = 'credentials.json'):
        """Initialize calendar actions"""
        self.calendar = GoogleCalendarIntegration(credentials_file)
        
        # Define available actions for the LLM
        self.actions = [
            llm.FunctionContext(
                name="check_availability",
                description="Check available appointment slots for a specific date",
                parameters={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Appointment duration in minutes (default: 60)",
                            "default": 60
                        }
                    },
                    "required": ["date"]
                }
            ),
            
            llm.FunctionContext(
                name="book_appointment",
                description="Book an appointment for a customer",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "Customer's full name"
                        },
                        "customer_email": {
                            "type": "string",
                            "description": "Customer's email address"
                        },
                        "start_datetime": {
                            "type": "string",
                            "description": "Appointment start time in ISO format"
                        },
                        "appointment_type": {
                            "type": "string",
                            "description": "Type of appointment",
                            "enum": ["consultation", "follow_up", "assessment"],
                            "default": "consultation"
                        },
                        "description": {
                            "type": "string",
                            "description": "Additional notes or description",
                            "default": ""
                        }
                    },
                    "required": ["customer_name", "customer_email", "start_datetime"]
                }
            ),
            
            llm.FunctionContext(
                name="modify_appointment",
                description="Modify an existing appointment",
                parameters={
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Google Calendar event ID"
                        },
                        "start_datetime": {
                            "type": "string",
                            "description": "New appointment start time in ISO format"
                        },
                        "description": {
                            "type": "string",
                            "description": "Updated description"
                        }
                    },
                    "required": ["event_id"]
                }
            ),
            
            llm.FunctionContext(
                name="cancel_appointment",
                description="Cancel an appointment",
                parameters={
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "Google Calendar event ID to cancel"
                        }
                    },
                    "required": ["event_id"]
                }
            ),
            
            llm.FunctionContext(
                name="get_upcoming_appointments",
                description="Get upcoming appointments",
                parameters={
                    "type": "object",
                    "properties": {
                        "days_ahead": {
                            "type": "integer",
                            "description": "Number of days to look ahead (default: 7)",
                            "default": 7
                        }
                    }
                }
            )
        ]
    
    async def check_availability(self, date: str, duration: int = 60) -> str:
        """
        Check available appointment slots
        
        Args:
            date: Date in YYYY-MM-DD format
            duration: Duration in minutes
            
        Returns:
            Formatted availability response
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            slots = await loop.run_in_executor(
                None, 
                self.calendar.check_availability, 
                date, 
                duration
            )
            
            if not slots:
                return f"No available slots found for {date}. Please try another date."
            
            # Format response
            slot_list = []
            for slot in slots[:5]:  # Limit to 5 slots
                slot_list.append(f"• {slot['start_time']} - {slot['end_time']}")
            
            return f"Available slots for {date}:\n" + "\n".join(slot_list)
            
        except Exception as e:
            return f"Error checking availability: {str(e)}"
    
    async def book_appointment(self, 
                             customer_name: str,
                             customer_email: str,
                             start_datetime: str,
                             appointment_type: str = "consultation",
                             description: str = "") -> str:
        """
        Book an appointment
        
        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            start_datetime: Start time in ISO format
            appointment_type: Type of appointment
            description: Additional description
            
        Returns:
            Booking confirmation message
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.calendar.book_appointment,
                customer_name,
                customer_email,
                start_datetime,
                appointment_type,
                description
            )
            
            if result['success']:
                return (f"✅ Appointment booked successfully!\n"
                       f"Customer: {customer_name}\n"
                       f"Time: {result['start_time']}\n"
                       f"Type: {appointment_type.title()}\n"
                       f"A calendar invite has been sent to {customer_email}")
            else:
                return f"❌ Failed to book appointment: {result['message']}"
                
        except Exception as e:
            return f"Error booking appointment: {str(e)}"
    
    async def modify_appointment(self, 
                               event_id: str,
                               start_datetime: Optional[str] = None,
                               description: Optional[str] = None) -> str:
        """
        Modify an existing appointment
        
        Args:
            event_id: Google Calendar event ID
            start_datetime: New start time
            description: Updated description
            
        Returns:
            Modification confirmation message
        """
        try:
            updates = {}
            if start_datetime:
                updates['start_datetime'] = start_datetime
            if description:
                updates['description'] = description
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.calendar.modify_appointment,
                event_id,
                **updates
            )
            
            if result['success']:
                return "✅ Appointment updated successfully! Updated calendar invite sent."
            else:
                return f"❌ Failed to update appointment: {result['message']}"
                
        except Exception as e:
            return f"Error updating appointment: {str(e)}"
    
    async def cancel_appointment(self, event_id: str) -> str:
        """
        Cancel an appointment
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Cancellation confirmation message
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.calendar.cancel_appointment,
                event_id
            )
            
            if result['success']:
                return "✅ Appointment cancelled successfully! Cancellation notice sent to all attendees."
            else:
                return f"❌ Failed to cancel appointment: {result['message']}"
                
        except Exception as e:
            return f"Error cancelling appointment: {str(e)}"
    
    async def get_upcoming_appointments(self, days_ahead: int = 7) -> str:
        """
        Get upcoming appointments
        
        Args:
            days_ahead: Days to look ahead
            
        Returns:
            Formatted list of upcoming appointments
        """
        try:
            loop = asyncio.get_event_loop()
            appointments = await loop.run_in_executor(
                None,
                self.calendar.get_upcoming_appointments,
                days_ahead
            )
            
            if not appointments:
                return f"No upcoming appointments in the next {days_ahead} days."
            
            # Format response
            apt_list = []
            for apt in appointments:
                start_time = datetime.fromisoformat(apt['start_time']).strftime('%Y-%m-%d %H:%M')
                apt_list.append(f"• {start_time} - {apt['summary']}")
            
            return f"Upcoming appointments:\n" + "\n".join(apt_list)
            
        except Exception as e:
            return f"Error getting appointments: {str(e)}"
    
    def get_function_contexts(self) -> List[llm.FunctionContext]:
        """Get all function contexts for LLM integration"""
        return self.actions
    
    async def execute_function(self, function_name: str, **kwargs) -> str:
        """
        Execute a calendar function
        
        Args:
            function_name: Name of function to execute
            **kwargs: Function arguments
            
        Returns:
            Function result as string
        """
        if function_name == "check_availability":
            return await self.check_availability(**kwargs)
        elif function_name == "book_appointment":
            return await self.book_appointment(**kwargs)
        elif function_name == "modify_appointment":
            return await self.modify_appointment(**kwargs)
        elif function_name == "cancel_appointment":
            return await self.cancel_appointment(**kwargs)
        elif function_name == "get_upcoming_appointments":
            return await self.get_upcoming_appointments(**kwargs)
        else:
            return f"Unknown function: {function_name}"