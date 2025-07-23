#!/usr/bin/env python3
"""
LiveKit Cloud Deployment Helper
This script helps you deploy your agent to LiveKit Cloud Agents Beta.
"""

import os
import sys
import webbrowser
import subprocess
import platform
import dotenv
from pathlib import Path

def main():
    print("=" * 60)
    print("LiveKit Cloud Agents Deployment Helper")
    print("=" * 60)
    
    # Load .env file
    dotenv.load_dotenv()
    
    # Check LiveKit credentials
    livekit_url = os.getenv("LIVEKIT_URL")
    livekit_api_key = os.getenv("LIVEKIT_API_KEY")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not livekit_url or not livekit_api_key or not livekit_api_secret:
        print("\n❌ Error: LiveKit credentials not found in .env file.")
        print("Please run scripts/setup_livekit_cloud.py first.")
        return
    
    print("\n✅ LiveKit credentials found in .env file.")
    print(f"   URL: {livekit_url}")
    print(f"   API Key: {livekit_api_key[:5]}...{livekit_api_key[-3:] if len(livekit_api_key) > 8 else ''}")
    
    # Check if Docker is installed
    print("\n🔍 Checking if Docker is installed...")
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not installed or not in PATH.")
        print("Please install Docker from https://www.docker.com/products/docker-desktop")
        return
    
    # Build Docker image
    print("\n🔨 Building Docker image...")
    try:
        subprocess.run(["docker", "build", "-t", "caresetu-voice-agent", "."], check=True)
        print("✅ Docker image built successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        return
    
    # Open LiveKit Cloud Agents Beta page
    print("\n🌐 Opening LiveKit Cloud Agents Beta signup page...")
    webbrowser.open("https://livekit.io/cloud-agents-beta")
    
    print("\n📋 Follow these steps to deploy your agent to LiveKit Cloud:")
    print("1. Sign up for the LiveKit Cloud Agents Beta if you haven't already")
    print("2. Once approved, log in to your LiveKit Cloud account")
    print("3. Navigate to the Agents section")
    print("4. Click 'Create Agent'")
    print("5. Choose 'Docker Image' as the deployment method")
    print("6. Use the following Docker image: caresetu-voice-agent")
    print("7. Set the environment variables from your .env file")
    print("8. Configure the worker pool size based on your needs")
    print("9. Click 'Deploy'")
    
    # Generate a token for testing
    print("\n🔑 Generating a token for testing...")
    try:
        subprocess.run(["python", "scripts/generate_token.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate token: {e}")
    
    print("\n✅ Your agent is ready to be deployed to LiveKit Cloud!")
    print("\nAfter deployment, you can test your agent using the frontend example:")
    print("1. Update frontend-example/index.html with your token")
    print("2. Open frontend-example/index.html in your browser")

if __name__ == "__main__":
    main()