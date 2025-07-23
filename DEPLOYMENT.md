# CareSetu Voice Agent Deployment Guide

This guide will help you deploy your CareSetu Voice Agent using LiveKit's free tier.

## Deployment Options

### 1. Local Development

To run the agent locally for development:

```bash
# Run with Docker Compose
docker-compose up --build
```

### 2. LiveKit Cloud (Free Tier)

LiveKit Cloud offers a free tier with 1,000 participant minutes per month.

1. Sign up for LiveKit Cloud at https://livekit.io/
2. Create a new project
3. Get your API key and secret
4. Update your `.env` file with the LiveKit credentials

### 3. Self-Hosted Deployment

#### Using Render.com (Free Tier Available)

1. Sign up for Render.com
2. Create a new Web Service
3. Connect to your GitHub repository
4. Set the following:
   - Build Command: `docker build -t caresetu-agent .`
   - Start Command: `docker run caresetu-agent`
   - Add all environment variables from your `.env` file

#### Using Railway.app (Free Tier Available)

1. Sign up for Railway.app
2. Create a new project
3. Connect to your GitHub repository
4. Add your environment variables from `.env`
5. Deploy

## Environment Variables

Make sure your deployment environment has all the necessary environment variables set:

```
# LiveKit Cloud Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Other API keys as needed
ASSEMBLYAI_API_KEY=your-key
GOOGLE_API_KEY=your-key
CARTESIA_API_KEY=your-key
# etc.
```

## Scaling

For the free tier, you don't need to worry about scaling. If your usage grows beyond the free tier limits, you can:

1. Upgrade to a paid LiveKit Cloud plan
2. Scale your self-hosted deployment by adding more worker instances

## Monitoring

Monitor your usage to stay within the free tier limits:

1. LiveKit Cloud: Check the dashboard for usage metrics
2. Self-hosted: Set up logging and monitoring

## Frontend Integration

After deploying your agent, you can integrate it with your frontend using the LiveKit client SDKs:

- Web: https://docs.livekit.io/client-sdk-js/
- iOS: https://docs.livekit.io/client-sdk-swift/
- Android: https://docs.livekit.io/client-sdk-android/

## Need Help?

- LiveKit Documentation: https://docs.livekit.io/
- LiveKit GitHub: https://github.com/livekit
- LiveKit Discord: https://livekit.io/discord
