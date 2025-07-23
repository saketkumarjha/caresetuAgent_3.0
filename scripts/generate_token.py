#!/usr/bin/env python3
"""
LiveKit Token Generator
This script generates a LiveKit token for testing your frontend integration.
"""

import os
import sys
import time
import uuid
import jwt
import dotenv
from pathlib import Path

def main():
    print("=" * 60)
    print("LiveKit Token Generator")
    print("=" * 60)
    
    # Load .env file
    dotenv.load_dotenv()
    
    # Get LiveKit credentials
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not api_key or not api_secret:
        print("\n❌ Error: LiveKit API key and secret not found in .env file.")
        print("Please run scripts/setup_livekit_cloud.py first.")
        return
    
    # Get room name
    room_name = input("\nEnter room name (default: test-room): ").strip() or "test-room"
    
    # Get user identity
    user_identity = input("Enter user identity (default: user-1): ").strip() or "user-1"
    
    # Get user name
    user_name = input("Enter user name (default: Test User): ").strip() or "Test User"
    
    # Generate token
    token = generate_token(api_key, api_secret, room_name, user_identity, user_name)
    
    print("\n✅ Token generated successfully!")
    print("\n" + "=" * 60)
    print("TOKEN:")
    print(token)
    print("=" * 60)
    
    print("\nUse this token in your frontend application.")
    print("It will expire in 24 hours.")

def generate_token(api_key, api_secret, room_name, identity, name):
    """Generate a LiveKit token."""
    now = int(time.time())
    exp = now + (24 * 60 * 60)  # 24 hours
    
    claim = {
        "iss": api_key,
        "nbf": now,
        "exp": exp,
        "sub": identity,
        "video": {
            "room": room_name,
            "room_join": True,
            "can_publish": True,
            "can_subscribe": True,
            "can_publish_data": True,
        },
        "metadata": name
    }
    
    token = jwt.encode(claim, api_secret, algorithm="HS256")
    return token

if __name__ == "__main__":
    main()