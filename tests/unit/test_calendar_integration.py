"""
Test script for Google Calendar integration
"""

import asyncio
from datetime import datetime, timedelta
from appointment_scheduler import AppointmentScheduler

async def test_calendar_integration():
    """Test the calendar integration functionality"""
    
    print("🔧 Testing Google Calendar Integration...")
    print("=" * 50)
    
    try:
        # Initialize scheduler
        scheduler = AppointmentScheduler()
        print("✅ Scheduler initialized successfully")
        
        # Test 1: Check availability for today
        print("\n📅 Test 1: Checking availability for today...")
        today = datetime.now().strftime('%Y-%m-%d')
        availability = await scheduler.calendar_actions.check_availability(today)
        print(f"Availability result:\n{availability}")
        
        # Test 2: Check availability for tomorrow
        print("\n📅 Test 2: Checking availability for tomorrow...")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        availability_tomorrow = await scheduler.calendar_actions.check_availability(tomorrow)
        print(f"Availability result:\n{availability_tomorrow}")
        
        # Test 3: Intent detection
        print("\n🎯 Test 3: Testing intent detection...")
        test_messages = [
            "I need to book an appointment",
            "What times are available tomorrow?",
            "Can I schedule a consultation?",
            "I want to cancel my appointment",
            "Hello, how are you?"  # Non-scheduling message
        ]
        
        for message in test_messages:
            is_scheduling = scheduler.detect_scheduling_intent(message)
            print(f"Message: '{message}' -> Scheduling intent: {is_scheduling}")
        
        # Test 4: Get business hours
        print("\n🕐 Test 4: Business hours information...")
        hours_info = scheduler.get_business_hours_info()
        print(hours_info)
        
        # Test 5: Handle scheduling requests
        print("\n💬 Test 5: Handling scheduling requests...")
        test_requests = [
            "What times are available tomorrow?",
            "I'd like to book an appointment",
            "Can you help me schedule something?"
        ]
        
        for request in test_requests:
            response = await scheduler.handle_scheduling_request(request)
            print(f"Request: '{request}'")
            print(f"Response: {response}\n")
        
        # Test 6: Get upcoming appointments
        print("\n📋 Test 6: Getting upcoming appointments...")
        upcoming = await scheduler.calendar_actions.get_upcoming_appointments()
        print(f"Upcoming appointments:\n{upcoming}")
        
        print("\n✅ All tests completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please ensure you have set up Google Calendar credentials.")
        print("See GOOGLE_CALENDAR_SETUP.md for instructions.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print("Please check your Google Calendar setup and credentials.")

def test_booking_simulation():
    """Simulate a booking conversation"""
    
    print("\n🎭 Booking Conversation Simulation")
    print("=" * 40)
    
    # Simulate conversation flow
    conversation = [
        ("Customer", "Hi, I'd like to book an appointment"),
        ("Agent", "I'd be happy to help! What date works best for you?"),
        ("Customer", "How about tomorrow at 2 PM?"),
        ("Agent", "Let me check availability for tomorrow..."),
        # This would trigger availability check
        ("Customer", "My name is John Doe and email is john@example.com"),
        ("Agent", "Perfect! I can book that appointment for you."),
        # This would trigger booking
    ]
    
    for speaker, message in conversation:
        print(f"{speaker}: {message}")
    
    print("\n💡 In a real implementation:")
    print("- The agent would check availability in real-time")
    print("- Book the appointment directly in Google Calendar")
    print("- Google Calendar would send the invite automatically")
    print("- Customer receives confirmation email immediately")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_calendar_integration())
    
    # Show booking simulation
    test_booking_simulation()
    
    print("\n🚀 Next Steps:")
    print("1. Set up Google Calendar credentials (see GOOGLE_CALENDAR_SETUP.md)")
    print("2. Test with real calendar booking")
    print("3. Integrate with your existing voice agent")
    print("4. Configure business hours and appointment types")