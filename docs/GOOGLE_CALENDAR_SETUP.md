# Google Calendar Integration Setup Guide

This guide will help you set up Google Calendar integration for your voice agent.

## Prerequisites

- Google account
- Python environment with required packages

## Step 1: Install Required Packages

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pytz
```

## Step 2: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

## Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - Choose "External" for testing
   - Fill in required fields (App name, User support email, Developer contact)
   - Add your email to test users
4. Choose "Desktop application" as application type
5. Download the JSON file and rename it to `credentials.json`
6. Place `credentials.json` in your project root directory

## Step 4: First Time Authentication

When you first run the calendar integration:

1. The system will open a browser window
2. Sign in with your Google account
3. Grant permission to access your calendar
4. The system will save a `token.json` file for future use

## Step 5: Test the Integration

Create a test script:

```python
from google_calendar_integration import GoogleCalendarIntegration

# Initialize calendar integration
calendar = GoogleCalendarIntegration()

# Test availability check
slots = calendar.check_availability('2025-01-25')
print("Available slots:", slots)

# Test booking (replace with real email)
result = calendar.book_appointment(
    customer_name="Test Customer",
    customer_email="test@example.com",
    start_datetime="2025-01-25T14:00:00",
    appointment_type="consultation"
)
print("Booking result:", result)
```

## Configuration Options

### Business Hours

Edit the `business_hours` in `GoogleCalendarIntegration`:

```python
self.business_hours = {
    'start': '09:00',
    'end': '17:00',
    'timezone': 'America/New_York'  # Change to your timezone
}
```

### Appointment Types

Customize appointment types and durations:

```python
self.appointment_types = {
    'consultation': {'duration': 60, 'buffer': 15},
    'follow_up': {'duration': 30, 'buffer': 10},
    'assessment': {'duration': 90, 'buffer': 15}
}
```

## Security Notes

- Keep `credentials.json` and `token.json` secure
- Add them to `.gitignore`
- For production, use service account credentials
- Consider using environment variables for sensitive data

## Troubleshooting

### Common Issues

1. **"File not found" error**

   - Ensure `credentials.json` is in the correct location
   - Check file permissions

2. **Authentication fails**

   - Clear `token.json` and re-authenticate
   - Check OAuth consent screen configuration

3. **API quota exceeded**

   - Check Google Cloud Console for API usage
   - Implement rate limiting if needed

4. **Calendar not found**
   - Ensure you're using the correct calendar ID
   - Check calendar sharing permissions

### Testing Calendar Integration

```python
# Test script
import asyncio
from appointment_scheduler import AppointmentScheduler

async def test_scheduler():
    scheduler = AppointmentScheduler()

    # Test availability
    result = await scheduler.calendar_actions.check_availability('2025-01-25')
    print(result)

    # Test booking
    booking_result = await scheduler.quick_book_appointment(
        customer_name="John Doe",
        customer_email="john@example.com",
        preferred_date="2025-01-25",
        preferred_time="14:00"
    )
    print(booking_result)

# Run test
asyncio.run(test_scheduler())
```

## Integration with Voice Agent

The calendar system integrates with your existing voice agent through:

1. **Intent Detection**: Recognizes scheduling requests
2. **Function Calls**: LLM can call calendar functions
3. **Automatic Notifications**: Google Calendar handles email invites
4. **Real-time Booking**: Appointments booked during conversation

## Next Steps

1. Set up Google Calendar credentials
2. Test basic functionality
3. Integrate with your existing voice agent
4. Configure business hours and appointment types
5. Test end-to-end booking flow

The system is designed to be simple - Google Calendar handles all email notifications automatically, so you don't need to build a separate notification system.
