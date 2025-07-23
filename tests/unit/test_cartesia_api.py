#!/usr/bin/env python3
"""
Test script to verify Cartesia API is working with the new credentials.
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_cartesia_api():
    """Test the Cartesia API with the new credentials."""
    api_key = os.getenv('CARTESIA_API_KEY')
    
    if not api_key:
        print("❌ CARTESIA_API_KEY not found in environment")
        return False
    
    print(f"🔑 Testing Cartesia API with key: {api_key[:12]}...")
    
    # Test data matching your curl example
    test_data = {
        "model_id": "sonic-turbo",
        "transcript": "Hello, this is a test of the Cartesia text-to-speech service.",
        "voice": {
            "mode": "id",
            "id": "bf0a246a-8642-498a-9950-80c35e9276b5"
        },
        "output_format": {
            "container": "wav",
            "encoding": "pcm_f32le",
            "sample_rate": 44100
        },
        "language": "en"
    }
    
    headers = {
        "Cartesia-Version": "2024-06-10",
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🔄 Making test request to Cartesia API...")
            
            async with session.post(
                "https://api.cartesia.ai/tts/bytes",
                headers=headers,
                json=test_data,
                timeout=30
            ) as response:
                
                print(f"📊 Response status: {response.status}")
                
                if response.status == 200:
                    content_length = response.headers.get('content-length', 'unknown')
                    print(f"✅ SUCCESS! Cartesia API is working correctly")
                    print(f"📁 Audio data received: {content_length} bytes")
                    
                    # Save a small test audio file
                    audio_data = await response.read()
                    with open('test_cartesia_output.wav', 'wb') as f:
                        f.write(audio_data)
                    print(f"🎵 Test audio saved as 'test_cartesia_output.wav'")
                    
                    return True
                    
                elif response.status == 402:
                    print("❌ Payment Required (402) - Check your Cartesia billing")
                    return False
                    
                elif response.status == 401:
                    print("❌ Unauthorized (401) - Invalid API key")
                    return False
                    
                else:
                    error_text = await response.text()
                    print(f"❌ API Error ({response.status}): {error_text}")
                    return False
                    
    except asyncio.TimeoutError:
        print("❌ Request timed out - Check your internet connection")
        return False
        
    except Exception as e:
        print(f"❌ Error testing Cartesia API: {e}")
        return False

async def test_voice_list():
    """Test getting available voices from Cartesia."""
    api_key = os.getenv('CARTESIA_API_KEY')
    
    if not api_key:
        return
    
    headers = {
        "Cartesia-Version": "2024-06-10",
        "X-API-Key": api_key,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("\n🎭 Testing voice list endpoint...")
            
            async with session.get(
                "https://api.cartesia.ai/voices",
                headers=headers,
                timeout=10
            ) as response:
                
                if response.status == 200:
                    voices = await response.json()
                    print(f"✅ Found {len(voices)} available voices")
                    
                    # Show the voice we're using
                    target_voice_id = "bf0a246a-8642-498a-9950-80c35e9276b5"
                    for voice in voices:
                        if voice.get('id') == target_voice_id:
                            print(f"🎤 Using voice: {voice.get('name', 'Unknown')} ({voice.get('language', 'Unknown')})")
                            break
                    else:
                        print(f"⚠️ Voice ID {target_voice_id} not found in available voices")
                        
                else:
                    print(f"❌ Voice list request failed: {response.status}")
                    
    except Exception as e:
        print(f"❌ Error getting voice list: {e}")

async def main():
    """Main test function."""
    print("🚀 Testing Cartesia API Configuration")
    print("=" * 40)
    
    # Test the main TTS endpoint
    tts_success = await test_cartesia_api()
    
    # Test voice list if TTS worked
    if tts_success:
        await test_voice_list()
    
    print("\n" + "=" * 40)
    if tts_success:
        print("✅ Cartesia API is ready for use!")
        print("🎯 You can now run your voice agent with confidence.")
    else:
        print("❌ Cartesia API test failed.")
        print("🔧 Please check your API key and billing status.")

if __name__ == "__main__":
    asyncio.run(main())