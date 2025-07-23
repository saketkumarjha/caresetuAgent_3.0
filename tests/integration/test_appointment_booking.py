"""
Test actual appointment booking with Google Calendar
"""

import asyncio
from datetime import datetime, timedelta
from google_calendar_integration import GoogleCalendarIntegration

async def test_real_booking():
    """Test booking a real appointment"""
    
    print("🎯 Testing Real Appointment Booking")
    print("=" * 45)
    
    try:
        # Initialize calendar
        calendar = GoogleCalendarIntegration()
        print("✅ Calendar initialized")
        
        # Get tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"\n📅 Checking availability for {tomorrow}...")
        
        # Check availability
        slots = calendar.check_availability(tomorrow)
        
        if not slots:
            print("❌ No available slots found for tomorrow")
            return
        
        print(f"✅ Found {len(slots)} available slots:")
        for i, slot in enumerate(slots[:3], 1):
            print(f"   {i}. {slot['start_time']} - {slot['end_time']}")
        
        # Ask user if they want to book
        print(f"\n🤔 Would you like to book a test appointment?")
        print("This will create a REAL appointment in your Google Calendar!")
        
        choice = input("Enter 'yes' to book a test appointment, or 'no' to skip: ").lower().strip()
        
        if choice != 'yes':
            print("⏭️  Skipping real booking test")
            return
        
        # Get booking details
        print("\n📝 Enter booking details:")
        customer_name = input("Customer name (or press Enter for 'Test Customer'): ").strip()
        if not customer_name:
            customer_name = "Test Customer"
        
        customer_email = input("Customer email (or press Enter for your email): ").strip()
        if not customer_email:
            customer_email = "test@example.com"  # You can change this
        
        # Use first available slot
        first_slot = slots[0]
        booking_datetime = first_slot['datetime']
        
        print(f"\n🔄 Booking appointment...")
        print(f"   Customer: {customer_name}")
        print(f"   Email: {customer_email}")
        print(f"   Time: {first_slot['start_time']} - {first_slot['end_time']}")
        
        # Book the appointment
        result = calendar.book_appointment(
            customer_name=customer_name,
            customer_email=customer_email,
            start_datetime=booking_datetime,
            appointment_type='consultation',
            description='Test appointment booked via voice agent calendar integration'
        )
        
        if result['success']:
            print(f"\n✅ SUCCESS! Appointment booked!")
            print(f"   Event ID: {result['event_id']}")
            print(f"   Time: {result['start_time']} - {result['end_time']}")
            print(f"   Calendar Link: {result.get('event_link', 'N/A')}")
            print(f"\n📧 Google Calendar will automatically send:")
            print(f"   • Calendar invite to {customer_email}")
            print(f"   • Reminder emails (24hr and 1hr before)")
            
            # Ask if they want to cancel the test appointment
            print(f"\n🗑️  This was a test appointment.")
            cancel_choice = input("Would you like to cancel it? (yes/no): ").lower().strip()
            
            if cancel_choice == 'yes':
                cancel_result = calendar.cancel_appointment(result['event_id'])
                if cancel_result['success']:
                    print("✅ Test appointment cancelled successfully")
                else:
                    print(f"❌ Failed to cancel: {cancel_result['message']}")
            else:
                print("📅 Test appointment kept in your calendar")
        else:
            print(f"❌ Booking failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error during booking test: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_booking())