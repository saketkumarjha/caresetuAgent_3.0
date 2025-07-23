"""
Quick setup script for Google Calendar integration
"""

import os
import json
from dotenv import load_dotenv

def setup_google_credentials():
    """Setup Google Calendar credentials from environment variables"""
    
    load_dotenv()
    
    # Get credentials from environment
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    api_key = os.getenv('GOOGLE_CALENDAR_API_KEY')
    
    if not client_id:
        print("❌ GOOGLE_CLIENT_ID not found in .env file")
        return False
    
    if not api_key:
        print("❌ GOOGLE_CALENDAR_API_KEY not found in .env file")
        return False
    
    # Create credentials.json file
    credentials = {
        "installed": {
            "client_id": client_id,
            "project_id": "voice-agent-calendar",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "GOCSPX-your_client_secret_here",  # You'll need to get this from Google Cloud Console
            "redirect_uris": ["http://localhost"]
        }
    }
    
    # Write credentials file
    with open('credentials.json', 'w') as f:
        json.dump(credentials, f, indent=2)
    
    print("✅ credentials.json created successfully")
    print("⚠️  Note: You still need to add your client_secret to credentials.json")
    print("   Get it from: https://console.cloud.google.com/apis/credentials")
    
    return True

def check_requirements():
    """Check if required packages are installed"""
    
    required_imports = [
        ('google.auth', 'google-auth'),
        ('google_auth_oauthlib', 'google-auth-oauthlib'), 
        ('google_auth_httplib2', 'google-auth-httplib2'),
        ('googleapiclient', 'google-api-python-client'),
        ('pytz', 'pytz')
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_imports:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required packages are installed")
    return True

def main():
    """Main setup function"""
    
    print("🔧 Google Calendar Integration Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Setup credentials
    if not setup_google_credentials():
        return
    
    print("\n🚀 Next Steps:")
    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    print("2. Enable Google Calendar API")
    print("3. Create OAuth2 credentials (Desktop application)")
    print("4. Download the JSON file and replace credentials.json")
    print("5. Run: python test_calendar_integration.py")
    
    print("\n📚 For detailed instructions, see: GOOGLE_CALENDAR_SETUP.md")

if __name__ == "__main__":
    main()