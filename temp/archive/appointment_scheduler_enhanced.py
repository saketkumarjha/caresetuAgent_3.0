"""
Enhanced Appointment Scheduler for Business Automation Voice Agent
Integrates with Google Calendar and provides real-time scheduling capabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppointmentStatus(Enum):
    """Appointment status enumeration."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class AppointmentType(Enum):
    """Types of appointments available."""
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    DIAGNOSTIC = "diagnostic"
    THERAPY = "therapy"
    EMERGENCY = "emergency"

@dataclass
class TimeSlot:
    """Represents an available time slot."""
    start_time: datetime
    end_time: datetime
    available: bool = True
    appointment_type: Optional[AppointmentType] = None
    provider_id: Optional[str] = None
    
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "available": self.available,
            "appointment_type": self.appointment_type.value if self.appointment_type else None,
            "provider_id": self.provider_id,
            "duration_minutes": self.duration_minutes()
        }

@dataclass
class Appointment:
    """Represents a scheduled appointment."""
    appointment_id: str
    customer_phone: str
    customer_name: str
    appointment_type: AppointmentType
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    provider_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "appointment_id": self.appointment_id,
            "customer_phone": self.customer_phone,
            "customer_name": self.customer_name,
            "appointment_type": self.appointment_type.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
            "provider_id": self.provider_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class BusinessHours:
    """Manages business hours and availability."""
    
    def __init__(self):
        # Default business hours (9 AM to 6 PM, Monday to Friday)
        self.business_hours = {
            0: {"start": "09:00", "end": "18:00"},  # Monday
            1: {"start": "09:00", "end": "18:00"},  # Tuesday
            2: {"start": "09:00", "end": "18:00"},  # Wednesday
            3: {"start": "09:00", "end": "18:00"},  # Thursday
            4: {"start": "09:00", "end": "18:00"},  # Friday
            5: None,  # Saturday - Closed
            6: None,  # Sunday - Closed
        }
        
        # Appointment durations by type (in minutes)
        self.appointment_durations = {
            AppointmentType.CONSULTATION: 30,
            AppointmentType.FOLLOW_UP: 15,
            AppointmentType.DIAGNOSTIC: 45,
            AppointmentType.THERAPY: 60,
            AppointmentType.EMERGENCY: 20,
        }
        
        # Buffer time between appointments (in minutes)
        self.buffer_time = 10
    
    def is_business_day(self, date: datetime) -> bool:
        """Check if the given date is a business day."""
        return self.business_hours.get(date.weekday()) is not None
    
    def get_business_hours(self, date: datetime) -> Optional[Tuple[datetime, datetime]]:
        """Get business hours for a specific date."""
        day_hours = self.business_hours.get(date.weekday())
        if not day_hours:
            return None
        
        start_time = datetime.strptime(day_hours["start"], "%H:%M").time()
        end_time = datetime.strptime(day_hours["end"], "%H:%M").time()
        
        start_datetime = datetime.combine(date.date(), start_time)
        end_datetime = datetime.combine(date.date(), end_time)
        
        return start_datetime, end_datetime
    
    def get_appointment_duration(self, appointment_type: AppointmentType) -> int:
        """Get duration for appointment type in minutes."""
        return self.appointment_durations.get(appointment_type, 30)

class SchedulingEngine:
    """Core scheduling engine for appointment management."""
    
    def __init__(self):
        self.business_hours = BusinessHours()
        self.appointments: Dict[str, Appointment] = {}
        self.calendar_connector = None  # Will be initialized with actual calendar API
        logger.info("✅ Scheduling engine initialized")
    
    async def get_availability(self, 
                             date: datetime, 
                             appointment_type: AppointmentType,
                             duration_minutes: Optional[int] = None) -> List[TimeSlot]:
        """Get available time slots for a specific date and appointment type."""
        
        if not self.business_hours.is_business_day(date):
            logger.info(f"📅 {date.strftime('%A, %B %d')} is not a business day")
            return []
        
        business_hours = self.business_hours.get_business_hours(date)
        if not business_hours:
            return []
        
        start_time, end_time = business_hours
        
        # Get appointment duration
        if duration_minutes is None:
            duration_minutes = self.business_hours.get_appointment_duration(appointment_type)
        
        # Generate time slots
        available_slots = []
        current_time = start_time
        
        while current_time + timedelta(minutes=duration_minutes) <= end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with existing appointments
            if not self._has_conflict(current_time, slot_end):
                slot = TimeSlot(
                    start_time=current_time,
                    end_time=slot_end,
                    available=True,
                    appointment_type=appointment_type
                )
                available_slots.append(slot)
            
            # Move to next slot (including buffer time)
            current_time += timedelta(minutes=duration_minutes + self.business_hours.buffer_time)
        
        logger.info(f"📅 Found {len(available_slots)} available slots for {date.strftime('%A, %B %d')}")
        return available_slots
    
    def _has_conflict(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if the time slot conflicts with existing appointments."""
        for appointment in self.appointments.values():
            if appointment.status in [AppointmentStatus.CANCELLED]:
                continue
            
            # Check for overlap
            if (start_time < appointment.end_time and end_time > appointment.start_time):
                return True
        
        return False
    
    async def book_appointment(self, 
                             customer_phone: str,
                             customer_name: str,
                             appointment_type: AppointmentType,
                             start_time: datetime,
                             notes: Optional[str] = None) -> Tuple[bool, str, Optional[Appointment]]:
        """Book an appointment."""
        
        # Generate appointment ID
        appointment_id = f"apt_{int(datetime.now().timestamp())}_{customer_phone[-4:]}"
        
        # Calculate end time
        duration = self.business_hours.get_appointment_duration(appointment_type)
        end_time = start_time + timedelta(minutes=duration)
        
        # Check availability
        if self._has_conflict(start_time, end_time):
            return False, "Time slot is no longer available", None
        
        # Check business hours
        if not self.business_hours.is_business_day(start_time):
            return False, "Selected date is not a business day", None
        
        business_hours = self.business_hours.get_business_hours(start_time)
        if not business_hours:
            return False, "Selected date is outside business hours", None
        
        bh_start, bh_end = business_hours
        if start_time < bh_start or end_time > bh_end:
            return False, f"Appointment must be between {bh_start.strftime('%I:%M %p')} and {bh_end.strftime('%I:%M %p')}", None
        
        # Create appointment
        appointment = Appointment(
            appointment_id=appointment_id,
            customer_phone=customer_phone,
            customer_name=customer_name,
            appointment_type=appointment_type,
            start_time=start_time,
            end_time=end_time,
            notes=notes
        )
        
        # Store appointment
        self.appointments[appointment_id] = appointment
        
        logger.info(f"✅ Appointment booked: {appointment_id} for {customer_name} on {start_time.strftime('%A, %B %d at %I:%M %p')}")
        
        return True, f"Appointment confirmed for {start_time.strftime('%A, %B %d at %I:%M %p')}", appointment
    
    async def reschedule_appointment(self, 
                                   appointment_id: str,
                                   new_start_time: datetime) -> Tuple[bool, str, Optional[Appointment]]:
        """Reschedule an existing appointment."""
        
        if appointment_id not in self.appointments:
            return False, "Appointment not found", None
        
        appointment = self.appointments[appointment_id]
        
        if appointment.status == AppointmentStatus.CANCELLED:
            return False, "Cannot reschedule a cancelled appointment", None
        
        # Calculate new end time
        duration = self.business_hours.get_appointment_duration(appointment.appointment_type)
        new_end_time = new_start_time + timedelta(minutes=duration)
        
        # Temporarily remove current appointment to check conflicts
        old_start = appointment.start_time
        old_end = appointment.end_time
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        
        # Check for conflicts (excluding this appointment)
        temp_appointments = {k: v for k, v in self.appointments.items() if k != appointment_id}
        has_conflict = False
        for other_apt in temp_appointments.values():
            if other_apt.status in [AppointmentStatus.CANCELLED]:
                continue
            if (new_start_time < other_apt.end_time and new_end_time > other_apt.start_time):
                has_conflict = True
                break
        
        if has_conflict:
            # Restore original times
            appointment.start_time = old_start
            appointment.end_time = old_end
            return False, "New time slot is not available", None
        
        logger.info(f"✅ Appointment rescheduled: {appointment_id} to {new_start_time.strftime('%A, %B %d at %I:%M %p')}")
        
        return True, f"Appointment rescheduled to {new_start_time.strftime('%A, %B %d at %I:%M %p')}", appointment
    
    async def cancel_appointment(self, appointment_id: str) -> Tuple[bool, str, Optional[Appointment]]:
        """Cancel an appointment."""
        
        if appointment_id not in self.appointments:
            return False, "Appointment not found", None
        
        appointment = self.appointments[appointment_id]
        appointment.status = AppointmentStatus.CANCELLED
        
        logger.info(f"❌ Appointment cancelled: {appointment_id}")
        
        return True, "Appointment has been cancelled", appointment
    
    async def get_customer_appointments(self, customer_phone: str) -> List[Appointment]:
        """Get all appointments for a customer."""
        customer_appointments = [
            apt for apt in self.appointments.values()
            if apt.customer_phone == customer_phone and apt.status != AppointmentStatus.CANCELLED
        ]
        
        # Sort by start time
        customer_appointments.sort(key=lambda x: x.start_time)
        
        return customer_appointments
    
    def get_appointment_summary(self, appointment: Appointment) -> str:
        """Get a human-readable summary of an appointment."""
        return f"""
Appointment Details:
- ID: {appointment.appointment_id}
- Type: {appointment.appointment_type.value.title()}
- Date & Time: {appointment.start_time.strftime('%A, %B %d, %Y at %I:%M %p')}
- Duration: {appointment.duration_minutes()} minutes
- Status: {appointment.status.value.title()}
- Customer: {appointment.customer_name}
- Phone: {appointment.customer_phone}
""".strip()

class AppointmentSchedulerAgent:
    """Voice agent integration for appointment scheduling."""
    
    def __init__(self):
        self.scheduling_engine = SchedulingEngine()
        logger.info("✅ Appointment scheduler agent initialized")
    
    async def handle_scheduling_request(self, message: str, context: Dict) -> str:
        """Handle scheduling requests from voice conversations."""
        
        message_lower = message.lower()
        customer_phone = context.get("caller_phone", "unknown")
        customer_name = context.get("customer_name", "Customer")
        
        try:
            # Intent detection
            if any(word in message_lower for word in ["book", "schedule", "appointment", "make"]):
                return await self._handle_booking_request(message, customer_phone, customer_name)
            
            elif any(word in message_lower for word in ["reschedule", "change", "move"]):
                return await self._handle_reschedule_request(message, customer_phone, customer_name)
            
            elif any(word in message_lower for word in ["cancel", "delete"]):
                return await self._handle_cancellation_request(message, customer_phone, customer_name)
            
            elif any(word in message_lower for word in ["availability", "available", "when", "times"]):
                return await self._handle_availability_request(message, customer_phone, customer_name)
            
            elif any(word in message_lower for word in ["my appointments", "upcoming", "scheduled"]):
                return await self._handle_appointment_inquiry(message, customer_phone, customer_name)
            
            else:
                return self._get_scheduling_help_message()
        
        except Exception as e:
            logger.error(f"Error handling scheduling request: {e}")
            return "I'm sorry, I encountered an issue with the scheduling system. Please try again or contact our support team."
    
    async def _handle_booking_request(self, message: str, customer_phone: str, customer_name: str) -> str:
        """Handle appointment booking requests."""
        
        # For now, provide available times for tomorrow (this would be enhanced with NLP)
        tomorrow = datetime.now() + timedelta(days=1)
        
        # Default to consultation type
        appointment_type = AppointmentType.CONSULTATION
        
        # Get availability
        available_slots = await self.scheduling_engine.get_availability(tomorrow, appointment_type)
        
        if not available_slots:
            return f"I don't have any available appointments for {tomorrow.strftime('%A, %B %d')}. Would you like to check a different date?"
        
        # Show first 3 available slots
        slots_text = []
        for i, slot in enumerate(available_slots[:3], 1):
            slots_text.append(f"{i}. {slot.start_time.strftime('%I:%M %p')}")
        
        return f"""I have the following appointment times available for {tomorrow.strftime('%A, %B %d')}:

{chr(10).join(slots_text)}

Which time works best for you? Just say the number or the time."""
    
    async def _handle_availability_request(self, message: str, customer_phone: str, customer_name: str) -> str:
        """Handle availability inquiries."""
        
        # Check availability for the next 3 business days
        available_days = []
        current_date = datetime.now()
        
        for i in range(1, 8):  # Check next 7 days
            check_date = current_date + timedelta(days=i)
            if self.scheduling_engine.business_hours.is_business_day(check_date):
                slots = await self.scheduling_engine.get_availability(check_date, AppointmentType.CONSULTATION)
                if slots:
                    available_days.append(f"• {check_date.strftime('%A, %B %d')}: {len(slots)} slots available")
                
                if len(available_days) >= 3:
                    break
        
        if not available_days:
            return "I don't have any available appointments in the next week. Please contact our office for assistance."
        
        return f"""Here's our availability for the next few days:

{chr(10).join(available_days)}

Would you like to book an appointment on any of these days?"""
    
    async def _handle_appointment_inquiry(self, message: str, customer_phone: str, customer_name: str) -> str:
        """Handle inquiries about existing appointments."""
        
        appointments = await self.scheduling_engine.get_customer_appointments(customer_phone)
        
        if not appointments:
            return "I don't see any upcoming appointments for your number. Would you like to schedule one?"
        
        appointment_list = []
        for apt in appointments:
            appointment_list.append(f"• {apt.appointment_type.value.title()} on {apt.start_time.strftime('%A, %B %d at %I:%M %p')}")
        
        return f"""Here are your upcoming appointments:

{chr(10).join(appointment_list)}

Would you like to reschedule or cancel any of these?"""
    
    async def _handle_reschedule_request(self, message: str, customer_phone: str, customer_name: str) -> str:
        """Handle rescheduling requests."""
        
        appointments = await self.scheduling_engine.get_customer_appointments(customer_phone)
        
        if not appointments:
            return "I don't see any appointments to reschedule. Would you like to book a new appointment?"
        
        if len(appointments) == 1:
            apt = appointments[0]
            return f"""I see you have a {apt.appointment_type.value} appointment on {apt.start_time.strftime('%A, %B %d at %I:%M %p')}.

What day would you like to reschedule it to?"""
        
        else:
            appointment_list = []
            for i, apt in enumerate(appointments, 1):
                appointment_list.append(f"{i}. {apt.appointment_type.value.title()} on {apt.start_time.strftime('%A, %B %d at %I:%M %p')}")
            
            return f"""You have multiple appointments:

{chr(10).join(appointment_list)}

Which appointment would you like to reschedule? Just say the number."""
    
    async def _handle_cancellation_request(self, message: str, customer_phone: str, customer_name: str) -> str:
        """Handle cancellation requests."""
        
        appointments = await self.scheduling_engine.get_customer_appointments(customer_phone)
        
        if not appointments:
            return "I don't see any appointments to cancel."
        
        if len(appointments) == 1:
            apt = appointments[0]
            success, message, _ = await self.scheduling_engine.cancel_appointment(apt.appointment_id)
            
            if success:
                return f"I've cancelled your {apt.appointment_type.value} appointment on {apt.start_time.strftime('%A, %B %d at %I:%M %p')}. Is there anything else I can help you with?"
            else:
                return f"I had trouble cancelling your appointment: {message}"
        
        else:
            appointment_list = []
            for i, apt in enumerate(appointments, 1):
                appointment_list.append(f"{i}. {apt.appointment_type.value.title()} on {apt.start_time.strftime('%A, %B %d at %I:%M %p')}")
            
            return f"""You have multiple appointments:

{chr(10).join(appointment_list)}

Which appointment would you like to cancel? Just say the number."""
    
    def _get_scheduling_help_message(self) -> str:
        """Get help message for scheduling."""
        return """I can help you with appointments! Here's what I can do:

• **Book appointments** - "I'd like to schedule an appointment"
• **Check availability** - "What times are available?"
• **View your appointments** - "What appointments do I have?"
• **Reschedule** - "I need to reschedule my appointment"
• **Cancel** - "I want to cancel my appointment"

Our business hours are Monday to Friday, 9 AM to 6 PM.

What would you like to do?"""

# Example usage and testing
async def test_scheduling_engine():
    """Test the scheduling engine functionality."""
    
    print("🧪 Testing Appointment Scheduling Engine")
    print("=" * 50)
    
    scheduler = AppointmentSchedulerAgent()
    
    # Test context
    test_context = {
        "caller_phone": "+1234567890",
        "customer_name": "John Doe"
    }
    
    # Test scheduling requests
    test_requests = [
        "I'd like to schedule an appointment",
        "What times are available?",
        "What appointments do I have?",
        "I need to reschedule my appointment",
        "I want to cancel my appointment"
    ]
    
    for request in test_requests:
        print(f"\n🗣️ User: '{request}'")
        response = await scheduler.handle_scheduling_request(request, test_context)
        print(f"🤖 Agent: {response}")
    
    print("\n✅ Scheduling engine test completed!")

if __name__ == "__main__":
    asyncio.run(test_scheduling_engine())