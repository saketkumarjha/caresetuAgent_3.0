"""
Basic test for Google Calendar integration without LiveKit dependencies
"""

import asyncio
from datetime import datetime, timedelta
from google_calendar_integration import GoogleCalendarIntegration

async def test_basic_calendar():
    """Test basic Google Calendar functionality"""
    
    print("🔧 Testing Basic Google Calendar Integration...")
    print("=" * 50)
    
    try:
        # Initialize calendar integration
        print("📅 Initializing Google Calendar...")
        calendar = GoogleCalendarIntegration()
        print("✅ Calendar initialized successfully")
        
        # Test 1: Check availability for today
        print("\n📅 Test 1: Checking availability for today...")
        today = datetime.now().strftime('%Y-%m-%d')
        slots = calendar.check_availability(today)
        
        if slots:
            print(f"✅ Found {len(slots)} available slots:")
            for i, slot in enumerate(slots[:3], 1):  # Show first 3 slots
                print(f"   {i}. {slot['start_time']} - {slot['end_time']}")
        else:
            print("ℹ️  No available slots found for today")
        
        # Test 2: Check availability for tomorrow
        print("\n📅 Test 2: Checking availability for tomorrow...")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        slots_tomorrow = calendar.check_availability(tomorrow)
        
        if slots_tomorrow:
            print(f"✅ Found {len(slots_tomorrow)} available slots for tomorrow:")
            for i, slot in enumerate(slots_tomorrow[:3], 1):
                print(f"   {i}. {slot['start_time']} - {slot['end_time']}")
        else:
            print("ℹ️  No available slots found for tomorrow")
        
        # Test 3: Get upcoming appointments
        print("\n📋 Test 3: Getting upcoming appointments...")
        upcoming = calendar.get_upcoming_appointments(7)
        
        if upcoming:
            print(f"✅ Found {len(upcoming)} upcoming appointments:")
            for apt in upcoming[:3]:  # Show first 3
                start_time = datetime.fromisoformat(apt['start_time']).strftime('%Y-%m-%d %H:%M')
                print(f"   • {start_time} - {apt['summary']}")
        else:
            print("ℹ️  No upcoming appointments found")
        
        # Test 4: Business hours info
        print("\n🕐 Test 4: Business configuration...")
        print(f"Business hours: {calendar.business_hours['start']} - {calendar.business_hours['end']}")
        print(f"Timezone: {calendar.business_hours['timezone']}")
        print("Appointment types:")
        for apt_type, config in calendar.appointment_types.items():
            print(f"   • {apt_type}: {config['duration']} min (buffer: {config['buffer']} min)")
        
        print("\n✅ All basic tests completed successfully!")
        print("\n💡 Your Google Calendar integration is working!")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please ensure credentials.json is properly configured.")
        return False
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print("This might be the first run - you may need to authenticate.")
        print("The system will open a browser window for Google authentication.")
        return False

def test_booking_simulation():
    """Simulate what a booking would look like"""
    
    print("\n🎭 Booking Simulation Example")
    print("=" * 40)
    
    print("Customer: Hi, I'd like to book an appointment")
    print("Agent: I'd be happy to help! What date works best for you?")
    print("Customer: How about tomorrow at 2 PM?")
    print("Agent: Let me check availability for tomorrow...")
    print("        [Checking Google Calendar...]")
    print("Agent: I have 2:00 PM available! May I get your name and email?")
    print("Customer: John Doe, john@example.com")
    print("Agent: Perfect! I'm booking your consultation for tomorrow at 2 PM.")
    print("        [Creating Google Calendar event...]")
    print("Agent: ✅ Done! You'll receive a calendar invite at john@example.com")
    print("        Google Calendar will also send you reminder emails.")
    
    print("\n💡 This is exactly how your voice agent will work!")

if __name__ == "__main__":
    # Run the basic test
    success = asyncio.run(test_basic_calendar())
    
    # Show booking simulation
    test_booking_simulation()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. ✅ Google Calendar integration is working")
        print("2. Test booking an actual appointment")
        print("3. Integrate with your voice agent")
        print("4. Configure business hours if needed")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Google Calendar API is enabled")
        print("2. Check credentials.json is correct")
        print("3. Run authentication if this is first time")
        print("4. See GOOGLE_CALENDAR_SETUP.md for help")