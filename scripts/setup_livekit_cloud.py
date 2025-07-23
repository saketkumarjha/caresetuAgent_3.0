#!/usr/bin/env python3
"""
LiveKit Cloud Setup Helper Script
This script helps you set up your LiveKit Cloud account and configure your .env file.
"""

import os
import sys
import webbrowser
from pathlib import Path
import dotenv

def main():
    print("=" * 60)
    print("LiveKit Cloud Setup Helper")
    print("=" * 60)
    print("\nThis script will help you set up LiveKit Cloud for your CareSetu Voice Agent.")
    
    # Check if .env file exists
    env_path = Path('.env')
    if not env_path.exists():
        print("\n❌ .env file not found. Creating one from .env.example if available...")
        example_path = Path('.env.example')
        if example_path.exists():
            with open(example_path, 'r') as example_file:
                with open(env_path, 'w') as env_file:
                    env_file.write(example_file.read())
            print("✅ Created .env file from .env.example")
        else:
            with open(env_path, 'w') as env_file:
                env_file.write("# LiveKit Cloud Configuration\n")
                env_file.write("LIVEKIT_URL=\n")
                env_file.write("LIVEKIT_API_KEY=\n")
                env_file.write("LIVEKIT_API_SECRET=\n\n")
            print("✅ Created empty .env file")
    
    # Load current .env file
    dotenv.load_dotenv()
    
    # Check if LiveKit credentials are already set
    livekit_url = os.getenv("LIVEKIT_URL", "")
    livekit_api_key = os.getenv("LIVEKIT_API_KEY", "")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "")
    
    if livekit_url and livekit_api_key and livekit_api_secret:
        print("\n✅ LiveKit credentials already set in .env file:")
        print(f"   URL: {livekit_url}")
        print(f"   API Key: {livekit_api_key[:5]}...{livekit_api_key[-3:] if len(livekit_api_key) > 8 else ''}")
        print(f"   API Secret: {livekit_api_secret[:5]}...{livekit_api_secret[-3:] if len(livekit_api_secret) > 8 else ''}")
        
        update = input("\nDo you want to update these credentials? (y/N): ").lower()
        if update != 'y':
            print("\n✅ Keeping existing LiveKit credentials.")
            return
    
    # Open LiveKit Cloud website
    print("\n🌐 Opening LiveKit Cloud website in your browser...")
    webbrowser.open("https://livekit.io/cloud")
    
    print("\n📋 Follow these steps:")
    print("1. Sign up for LiveKit Cloud (free tier available)")
    print("2. Create a new project")
    print("3. Go to the project settings")
    print("4. Copy the API Key, API Secret, and WebSocket URL")
    
    # Get LiveKit credentials from user
    print("\n⌨️ Enter your LiveKit Cloud credentials:")
    new_livekit_url = input("WebSocket URL (wss://...): ").strip()
    new_livekit_api_key = input("API Key: ").strip()
    new_livekit_api_secret = input("API Secret: ").strip()
    
    # Validate input
    if not new_livekit_url or not new_livekit_api_key or not new_livekit_api_secret:
        print("\n❌ Error: All fields are required. Please try again.")
        return
    
    if not new_livekit_url.startswith("wss://"):
        print("\n⚠️ Warning: WebSocket URL should start with 'wss://'. Please verify.")
    
    # Update .env file
    dotenv_file = dotenv.find_dotenv()
    dotenv.set_key(dotenv_file, "LIVEKIT_URL", new_livekit_url)
    dotenv.set_key(dotenv_file, "LIVEKIT_API_KEY", new_livekit_api_key)
    dotenv.set_key(dotenv_file, "LIVEKIT_API_SECRET", new_livekit_api_secret)
    
    print("\n✅ LiveKit Cloud credentials updated in .env file!")
    print("\n🚀 You're now ready to deploy your CareSetu Voice Agent to LiveKit Cloud!")
    print("   See DEPLOYMENT.md for detailed deployment instructions.")

if __name__ == "__main__":
    main()