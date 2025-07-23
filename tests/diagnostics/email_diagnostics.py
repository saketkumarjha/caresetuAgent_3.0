"""
Email Diagnostics for Google Calendar Integration
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def check_calendar_permissions():
    """Check if we have the right permissions for sending emails"""
    print("🔍 Checking Google Calendar permissions...")
    
    try:
        # Load credentials
        if not os.path.exists('token.json'):
            print("❌ No token.json found. Please run the calendar integration first.")
            return False
        
        creds = Credentials.from_authorized_user_file('token.json')
        service = build('calendar', 'v3', credentials=creds)
        
        # Check calendar access
        calendar_list = service.calendarList().list().execute()
        print(f"✅ Found {len(calendar_list.get('items', []))} calendars")
        
        # Check primary calendar settings
        primary_calendar = service.calendars().get(calendarId='primary').execute()
        print(f"📅 Primary calendar: {primary_calendar.get('summary')}")
        print(f"🌍 Timezone: {primary_calendar.get('timeZone')}")
        
        # Check if we can create events with attendees
        print("\n🧪 Testing event creation permissions...")
        
        # Create a test event (we'll delete it immediately)
        from datetime import datetime, timedelta
        
        test_event = {
            'summary': 'Email Test Event - DELETE ME',
            'description': 'This is a test event to check email permissions',
            'start': {
                'dateTime': (datetime.now() + timedelta(hours=1)).isoformat(),
                'timeZone': primary_calendar.get('timeZone', 'UTC'),
            },
            'end': {
                'dateTime': (datetime.now() + timedelta(hours=2)).isoformat(),
                'timeZone': primary_calendar.get('timeZone', 'UTC'),
            },
            'attendees': [
                {'email': 'test@example.com'}  # Test email
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 60},
                ],
            },
            'sendUpdates': 'all'
        }
        
        # Create the event
        created_event = service.events().insert(
            calendarId='primary',
            body=test_event,
            sendUpdates='all'
        ).execute()
        
        print(f"✅ Test event created: {created_event['id']}")
        
        # Immediately delete the test event
        service.events().delete(
            calendarId='primary',
            eventId=created_event['id'],
            sendUpdates='all'
        ).execute()
        
        print("✅ Test event deleted successfully")
        print("✅ Email permissions are working correctly")
        
        return True
        
    except HttpError as e:
        print(f"❌ Google Calendar API error: {e}")
        if e.resp.status == 403:
            print("🔒 Permission denied. You may need to:")
            print("   1. Re-authorize the application")
            print("   2. Check if the Google Calendar API is enabled")
            print("   3. Verify your OAuth2 credentials")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_email_settings():
    """Check email-related settings"""
    print("\n📧 Checking email settings...")
    
    # Check if credentials file exists
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found")
        
        try:
            with open('credentials.json', 'r') as f:
                creds_data = json.load(f)
            
            if 'installed' in creds_data:
                client_info = creds_data['installed']
                print(f"📱 Client ID: {client_info.get('client_id', 'Not found')[:20]}...")
                print(f"🔑 Project ID: {client_info.get('project_id', 'Not found')}")
            else:
                print("⚠️ Credentials format not recognized")
                
        except Exception as e:
            print(f"❌ Error reading credentials: {e}")
    else:
        print("❌ credentials.json not found")
    
    # Check token file
    if os.path.exists('token.json'):
        print("✅ token.json found")
        
        try:
            with open('token.json', 'r') as f:
                token_data = json.load(f)
            
            scopes = token_data.get('scopes', [])
            print(f"🔐 Scopes: {', '.join(scopes)}")
            
            if 'https://www.googleapis.com/auth/calendar' in scopes:
                print("✅ Calendar scope is present")
            else:
                print("❌ Calendar scope missing")
                
        except Exception as e:
            print(f"❌ Error reading token: {e}")
    else:
        print("❌ token.json not found")

def main():
    """Main diagnostic function"""
    print("🎯 CareSetu Email Diagnostics")
    print("=" * 40)
    
    # Check email settings
    check_email_settings()
    
    # Check calendar permissions
    permissions_ok = check_calendar_permissions()
    
    print("\n" + "=" * 40)
    if permissions_ok:
        print("✅ All diagnostics passed!")
        print("📧 Email notifications should be working")
        print("\n💡 If you're still not receiving emails, check:")
        print("   1. Your spam/junk folder")
        print("   2. The email address you're using for testing")
        print("   3. Google Calendar notification settings in your Google account")
    else:
        print("❌ Some diagnostics failed")
        print("🔧 Please fix the issues above and try again")

if __name__ == "__main__":
    main()