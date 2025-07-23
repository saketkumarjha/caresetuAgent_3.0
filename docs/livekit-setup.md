# LiveKit Cloud Setup Guide

## Step 1: Create LiveKit Cloud Account

1. **Visit LiveKit Cloud**

   - Go to [https://cloud.livekit.io](https://cloud.livekit.io)
   - Click "Sign Up" to create a new account
   - Verify your email address

2. **Create a New Project**
   - After logging in, click "Create Project"
   - Choose a project name (e.g., "Voice Agent Development")
   - Select your preferred region (choose closest to your users)

## Step 2: Get API Credentials

1. **Access Project Settings**

   - Click on your project name
   - Navigate to "Settings" → "Keys"

2. **Copy API Credentials**
   - Copy your **API Key**
   - Copy your **API Secret**
   - Note your **WebSocket URL** (format: `wss://your-project.livekit.cloud`)

## Step 3: Configure Environment

1. **Create .env file**

   ```bash
   cp .env.example .env
   ```

2. **Update .env with your credentials**
   ```env
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your-actual-api-key
   LIVEKIT_API_SECRET=your-actual-api-secret
   ```

## Step 4: Set Up Telephony Integration

1. **Enable Telephony**

   - In your LiveKit Cloud project, go to "Telephony"
   - Click "Enable Telephony Integration"
   - Choose your preferred telephony provider (Twilio recommended)

2. **Configure Phone Numbers**

   - Add your business phone numbers
   - Set up call routing to your voice agent
   - Configure webhook endpoints for call events

3. **Test Telephony Setup**
   - Use the provided test phone number
   - Make a test call to verify connectivity
   - Check call logs in the LiveKit dashboard

## Step 5: Verify Setup

Run the connectivity test:

```bash
python test_connectivity.py
```

You should see:

- ✅ LiveKit Cloud connection successful
- Connection to your project confirmed
- Telephony integration ready

## Troubleshooting

### Common Issues

1. **Invalid API Credentials**

   - Double-check your API Key and Secret
   - Ensure no extra spaces or characters
   - Regenerate keys if needed

2. **WebSocket Connection Failed**

   - Verify your LIVEKIT_URL format
   - Check firewall settings
   - Try different network connection

3. **Telephony Not Working**
   - Ensure telephony is enabled in project settings
   - Check phone number configuration
   - Verify webhook URLs are accessible

### Getting Help

- LiveKit Documentation: [https://docs.livekit.io](https://docs.livekit.io)
- LiveKit Discord: [https://livekit.io/join-slack](https://livekit.io/join-slack)
- Support: [https://livekit.io/support](https://livekit.io/support)

## Next Steps

Once LiveKit Cloud is set up:

1. Configure AssemblyAI for speech recognition
2. Set up Google Gemini for LLM processing
3. Configure TTS service (ElevenLabs or Google Cloud)
4. Test the complete voice pipeline
