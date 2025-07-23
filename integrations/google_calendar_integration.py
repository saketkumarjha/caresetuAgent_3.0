"""
Google Calendar Integration for Voice Agent
Simplified version - lets Google Calendar handle all notifications
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleCalendarIntegration:
    """
    Simplified Google Calendar integration for appointment scheduling
    """
    
    # Google Calendar API scope
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_file: str = 'config/credentials.json', token_file: str = 'config/token.json'):
        """
        Initialize Google Calendar integration
        
        Args:
            credentials_file: Path to Google OAuth2 credentials file
            token_file: Path to store OAuth2 token
        """
        # Try multiple possible locations for the credentials file
        possible_paths = [
            credentials_file,  # Try direct path first
            os.path.join(os.getcwd(), credentials_file),  # Try from current working directory
            os.path.join(os.path.dirname(os.getcwd()), credentials_file),  # Try from parent directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), credentials_file),  # Try from project root
        ]
        
        # Find the first path that exists
        self.credentials_file = None
        for path in possible_paths:
            if os.path.exists(path):
                self.credentials_file = path
                print(f"Found credentials at: {self.credentials_file}")
                break
        
        if not self.credentials_file:
            raise FileNotFoundError(f"Google credentials file not found. Tried: {possible_paths}")
        
        # Do the same for token file
        possible_token_paths = [
            token_file,  # Try direct path first
            os.path.join(os.getcwd(), token_file),  # Try from current working directory
            os.path.join(os.path.dirname(os.getcwd()), token_file),  # Try from parent directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), token_file),  # Try from project root
        ]
        
        # Find the first path that exists or use the same directory as credentials file
        self.token_file = None
        for path in possible_token_paths:
            if os.path.exists(path) or os.path.exists(os.path.dirname(path)):
                self.token_file = path
                print(f"Using token file at: {self.token_file}")
                break
                
        if not self.token_file:
            # Fallback to same directory as credentials file
            self.token_file = os.path.join(os.path.dirname(self.credentials_file), os.path.basename(token_file))
            print(f"Fallback token file at: {self.token_file}")
        self.service = None
        self.calendar_id = 'primary'  # Use primary calendar by default
        
        # Business configuration
        self.business_hours = {
            'start': '09:00',
            'end': '17:00',
            'timezone': 'Asia/Kolkata'  # Changed to Indian timezone
        }
        
        self.appointment_types = {
            'consultation': {'duration': 60, 'buffer': 15},
            'follow_up': {'duration': 30, 'buffer': 10},
            'assessment': {'duration': 90, 'buffer': 15}
        }
        
        # Email configuration for immediate confirmations
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_address': os.getenv('EMAIL_ADDRESS', ''),
            'email_password': os.getenv('EMAIL_PASSWORD', ''),
            'company_name': 'CareSetu Healthcare',
            'support_email': 'saket@jha.com'
        }
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Google credentials file not found: {self.credentials_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                
                # Try different ports to avoid conflicts
                ports_to_try = [8080, 8081, 8082, 8083, 8084]
                creds = None
                
                for port in ports_to_try:
                    try:
                        print(f"Trying to authenticate on port {port}...")
                        creds = flow.run_local_server(port=port, open_browser=True)
                        print(f"✅ Authentication successful on port {port}")
                        break
                    except OSError as e:
                        if "Address already in use" in str(e) or "10048" in str(e):
                            print(f"Port {port} is busy, trying next port...")
                            continue
                        else:
                            raise e
                
                if not creds:
                    raise Exception("Could not find an available port for authentication")
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def _send_confirmation_email(self, customer_name: str, customer_email: str, 
                               appointment_details: Dict[str, Any]) -> bool:
        """
        Send immediate confirmation email to customer
        
        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            appointment_details: Appointment details
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.email_config['email_address'] or not self.email_config['email_password']:
                print("⚠️ Email credentials not configured, skipping confirmation email")
                return False
            
            # Create email content
            subject = f"✅ Appointment Confirmed - {self.email_config['company_name']}"
            
            # HTML email template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .appointment-details {{ background-color: white; padding: 15px; border-left: 4px solid #4CAF50; margin: 15px 0; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                    .button {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Appointment Confirmed!</h1>
                    </div>
                    
                    <div class="content">
                        <p>Dear {customer_name},</p>
                        
                        <p>Great news! Your appointment has been successfully booked with {self.email_config['company_name']}.</p>
                        
                        <div class="appointment-details">
                            <h3>📅 Appointment Details:</h3>
                            <p><strong>Type:</strong> {appointment_details.get('type', 'Consultation').title()}</p>
                            <p><strong>Date & Time:</strong> {appointment_details.get('start_time', 'TBD')}</p>
                            <p><strong>Duration:</strong> {appointment_details.get('duration', '60')} minutes</p>
                            <p><strong>Appointment ID:</strong> {appointment_details.get('event_id', 'N/A')}</p>
                        </div>
                        
                        <h3>📧 What happens next?</h3>
                        <ul>
                            <li>You'll receive a Google Calendar invitation shortly</li>
                            <li>Email reminders will be sent 24 hours and 1 hour before your appointment</li>
                            <li>The appointment has been added to your calendar automatically</li>
                        </ul>
                        
                        <h3>📞 Need to make changes?</h3>
                        <p>If you need to reschedule or cancel your appointment, please contact us:</p>
                        <ul>
                            <li>Email: {self.email_config['support_email']}</li>
                            <li>Or use our voice assistant for instant changes</li>
                        </ul>
                        
                        <p style="margin-top: 30px;">
                            <a href="mailto:{self.email_config['support_email']}" class="button">Contact Support</a>
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>This confirmation was sent immediately after booking via our AI voice assistant.</p>
                        <p>{self.email_config['company_name']} | {self.email_config['support_email']}</p>
                        <p>Thank you for choosing our healthcare services!</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_body = f"""
            🎉 APPOINTMENT CONFIRMED - {self.email_config['company_name']}
            
            Dear {customer_name},
            
            Great news! Your appointment has been successfully booked.
            
            📅 APPOINTMENT DETAILS:
            Type: {appointment_details.get('type', 'Consultation').title()}
            Date & Time: {appointment_details.get('start_time', 'TBD')}
            Duration: {appointment_details.get('duration', '60')} minutes
            Appointment ID: {appointment_details.get('event_id', 'N/A')}
            
            📧 WHAT HAPPENS NEXT:
            - You'll receive a Google Calendar invitation shortly
            - Email reminders will be sent 24 hours and 1 hour before your appointment
            - The appointment has been added to your calendar automatically
            
            📞 NEED TO MAKE CHANGES?
            If you need to reschedule or cancel, please contact us:
            Email: {self.email_config['support_email']}
            Or use our voice assistant for instant changes
            
            Thank you for choosing {self.email_config['company_name']}!
            
            ---
            This confirmation was sent immediately after booking via our AI voice assistant.
            {self.email_config['company_name']} | {self.email_config['support_email']}
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['email_address']
            msg['To'] = customer_email
            
            # Add both plain text and HTML versions
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['email_address'], self.email_config['email_password'])
                server.send_message(msg)
            
            print(f"✅ Confirmation email sent to {customer_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send confirmation email: {e}")
            return False
    
    def check_availability(self, date: str, duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Check available time slots for a given date
        
        Args:
            date: Date in YYYY-MM-DD format
            duration_minutes: Appointment duration in minutes
            
        Returns:
            List of available time slots
        """
        try:
            # Parse date and set timezone
            tz = pytz.timezone(self.business_hours['timezone'])
            target_date = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=tz)
            
            # Set business hours for the day
            start_time = target_date.replace(
                hour=int(self.business_hours['start'].split(':')[0]),
                minute=int(self.business_hours['start'].split(':')[1])
            )
            end_time = target_date.replace(
                hour=int(self.business_hours['end'].split(':')[0]),
                minute=int(self.business_hours['end'].split(':')[1])
            )
            
            # Get existing events for the day
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Find available slots
            available_slots = []
            current_time = start_time
            
            for event in events:
                event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))
                
                # Check if there's a gap before this event
                if (event_start - current_time).total_seconds() >= duration_minutes * 60:
                    available_slots.append({
                        'start_time': current_time.strftime('%H:%M'),
                        'end_time': (current_time + timedelta(minutes=duration_minutes)).strftime('%H:%M'),
                        'datetime': current_time.isoformat()
                    })
                
                current_time = max(current_time, event_end)
            
            # Check for slot after last event
            if (end_time - current_time).total_seconds() >= duration_minutes * 60:
                available_slots.append({
                    'start_time': current_time.strftime('%H:%M'),
                    'end_time': (current_time + timedelta(minutes=duration_minutes)).strftime('%H:%M'),
                    'datetime': current_time.isoformat()
                })
            
            return available_slots
            
        except Exception as e:
            print(f"Error checking availability: {e}")
            return []
    
    def book_appointment(self, 
                        customer_name: str,
                        customer_email: str,
                        start_datetime: str,
                        appointment_type: str = 'consultation',
                        description: str = '') -> Dict[str, Any]:
        """
        Book an appointment in Google Calendar
        
        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            start_datetime: Start time in ISO format
            appointment_type: Type of appointment
            description: Additional description
            
        Returns:
            Booking result with event details
        """
        try:
            # Get appointment configuration
            config = self.appointment_types.get(appointment_type, self.appointment_types['consultation'])
            duration = config['duration']
            
            # Parse start time
            start_time = datetime.fromisoformat(start_datetime)
            end_time = start_time + timedelta(minutes=duration)
            
            # Create event
            event = {
                'summary': f'{appointment_type.title()} - {customer_name}',
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.business_hours['timezone'],
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.business_hours['timezone'],
                },
                'attendees': [
                    {'email': customer_email, 'displayName': customer_name}
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours
                        {'method': 'email', 'minutes': 60},       # 1 hour
                    ],
                },
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'sendUpdates': 'all'  # Send invites to all attendees
            }
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            # Prepare appointment details for confirmation email
            appointment_details = {
                'type': appointment_type,
                'start_time': start_time.strftime('%A, %B %d, %Y at %I:%M %p'),
                'duration': str(duration),
                'event_id': created_event['id']
            }
            
            # Send immediate confirmation email
            email_sent = self._send_confirmation_email(
                customer_name=customer_name,
                customer_email=customer_email,
                appointment_details=appointment_details
            )
            
            result = {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'start_time': start_time.strftime('%Y-%m-%d %H:%M'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M'),
                'message': f'Appointment booked successfully for {customer_name}',
                'confirmation_email_sent': email_sent
            }
            
            return result
            
        except HttpError as e:
            return {
                'success': False,
                'error': f'Google Calendar API error: {e}',
                'message': 'Failed to book appointment'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to book appointment'
            }
    
    def modify_appointment(self, event_id: str, **updates) -> Dict[str, Any]:
        """
        Modify an existing appointment
        
        Args:
            event_id: Google Calendar event ID
            **updates: Fields to update
            
        Returns:
            Modification result
        """
        try:
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields
            if 'start_datetime' in updates:
                start_time = datetime.fromisoformat(updates['start_datetime'])
                duration_minutes = self.appointment_types.get(
                    updates.get('appointment_type', 'consultation'), 
                    self.appointment_types['consultation']
                )['duration']
                end_time = start_time + timedelta(minutes=duration_minutes)
                
                event['start']['dateTime'] = start_time.isoformat()
                event['end']['dateTime'] = end_time.isoformat()
            
            if 'description' in updates:
                event['description'] = updates['description']
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return {
                'success': True,
                'event_id': updated_event['id'],
                'message': 'Appointment updated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update appointment'
            }
    
    def cancel_appointment(self, event_id: str) -> Dict[str, Any]:
        """
        Cancel an appointment
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            Cancellation result
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return {
                'success': True,
                'message': 'Appointment cancelled successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to cancel appointment'
            }
    
    def get_upcoming_appointments(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming appointments
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming appointments
        """
        try:
            now = datetime.now(pytz.timezone(self.business_hours['timezone']))
            future = now + timedelta(days=days_ahead)
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now.isoformat(),
                timeMax=future.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            appointments = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                appointments.append({
                    'id': event['id'],
                    'summary': event.get('summary', ''),
                    'start_time': start,
                    'description': event.get('description', ''),
                    'attendees': [att.get('email') for att in event.get('attendees', [])]
                })
            
            return appointments
            
        except Exception as e:
            print(f"Error getting appointments: {e}")
            return []