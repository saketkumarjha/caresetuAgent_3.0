"""
Test script to verify appointment booking and email notifications
"""

import asyncio
from datetime import datetime, timedelta
from google_calendar_integration import GoogleCalendarIntegration

async def test_appointment_booking():
    """Test appointment booking with email notifications"""
    print("🧪 Testing appointment booking with email notifications...")
    
    try:
        # Initialize calendar integration
        calendar = GoogleCalendarIntegration()
        print("✅ Calendar integration initialized")
        
        # Test data
        customer_name = "Test Customer"
        customer_email = "jhasaket99dbg@gmail.com"  # Using your actual email for testing
        
        # Book appointment for tomorrow at 10:00 AM IST
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        tomorrow_ist = datetime.now(ist) + timedelta(days=1)
        appointment_time = tomorrow_ist.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
        
        print(f"📅 Booking test appointment for {customer_name} at {appointment_time}")
        
        # Book the appointment
        result = calendar.book_appointment(
            customer_name=customer_name,
            customer_email=customer_email,
            start_datetime=appointment_time,
            appointment_type='consultation',
            description='Test appointment booked via voice agent test script'
        )
        
        if result['success']:
            print("✅ Appointment booked successfully!")
            print(f"📧 Event ID: {result['event_id']}")
            print(f"🔗 Event Link: {result.get('event_link', 'N/A')}")
            print(f"⏰ Start Time: {result['start_time']}")
            print(f"⏰ End Time: {result['end_time']}")
            print(f"💌 Email invitation should be sent to: {customer_email}")
            
            # Check if we can retrieve the appointment
            print("\n🔍 Checking upcoming appointments...")
            upcoming = calendar.get_upcoming_appointments(days_ahead=2)
            
            if upcoming:
                print(f"📋 Found {len(upcoming)} upcoming appointments:")
                for apt in upcoming:
                    print(f"  - {apt['summary']} at {apt['start_time']}")
            else:
                print("⚠️ No upcoming appointments found")
            
            return result['event_id']
        else:
            print(f"❌ Failed to book appointment: {result['message']}")
            return None
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return None

async def test_email_settings():
    """Test email notification settings"""
    print("\n📧 Testing email notification settings...")
    
    try:
        calendar = GoogleCalendarIntegration()
        
        # Check calendar settings
        print("🔍 Checking calendar service...")
        if calendar.service:
            print("✅ Google Calendar service is connected")
            
            # Get calendar info
            calendar_info = calendar.service.calendars().get(calendarId='primary').execute()
            print(f"📅 Calendar: {calendar_info.get('summary', 'Primary Calendar')}")
            print(f"🌍 Timezone: {calendar_info.get('timeZone', 'Not specified')}")
            
            return True
        else:
            print("❌ Google Calendar service not connected")
            return False
            
    except Exception as e:
        print(f"❌ Error checking email settings: {e}")
        return False

def cleanup_test_appointment(event_id):
    """Clean up test appointment"""
    if not event_id:
        return
        
    try:
        print(f"\n🧹 Cleaning up test appointment: {event_id}")
        calendar = GoogleCalendarIntegration()
        result = calendar.cancel_appointment(event_id)
        
        if result['success']:
            print("✅ Test appointment cleaned up successfully")
        else:
            print(f"⚠️ Could not clean up test appointment: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

async def main():
    """Main test function"""
    print("🎯 CareSetu Appointment Booking & Email Test")
    print("=" * 50)
    
    # Test email settings first
    email_ok = await test_email_settings()
    
    if not email_ok:
        print("❌ Email settings test failed. Please check your Google Calendar setup.")
        return
    
    # Test appointment booking
    event_id = await test_appointment_booking()
    
    if event_id:
        print("\n✅ All tests passed!")
        print("📧 Check your email for the calendar invitation")
        print("📱 The appointment should also appear in your Google Calendar")
        
        # Ask if user wants to clean up
        cleanup = input("\n🧹 Do you want to delete the test appointment? (y/n): ").lower().strip()
        if cleanup == 'y':
            cleanup_test_appointment(event_id)
        else:
            print(f"📝 Test appointment kept. Event ID: {event_id}")
    else:
        print("❌ Appointment booking test failed")

if __name__ == "__main__":
    asyncio.run(main())