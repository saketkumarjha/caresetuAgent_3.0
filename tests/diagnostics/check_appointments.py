"""
Check appointments and convert to local timezone
"""

from google_calendar_integration import GoogleCalendarIntegration
from datetime import datetime
import pytz

def main():
    print("🗓️ Checking your appointments...")
    
    cal = GoogleCalendarIntegration()
    upcoming = cal.get_upcoming_appointments(days_ahead=2)
    
    print(f"📋 Found {len(upcoming)} upcoming appointments:")
    
    # Convert UTC times to IST
    utc = pytz.UTC
    ist = pytz.timezone('Asia/Kolkata')
    
    for apt in upcoming:
        start_time_str = apt['start_time']
        
        # Parse the UTC time
        if start_time_str.endswith('Z'):
            start_time_utc = datetime.fromisoformat(start_time_str[:-1]).replace(tzinfo=utc)
        else:
            start_time_utc = datetime.fromisoformat(start_time_str).replace(tzinfo=utc)
        
        # Convert to IST
        start_time_ist = start_time_utc.astimezone(ist)
        
        print(f"  📅 {apt['summary']}")
        print(f"     UTC: {start_time_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"     IST: {start_time_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"     ID: {apt['id']}")
        print()

if __name__ == "__main__":
    main()