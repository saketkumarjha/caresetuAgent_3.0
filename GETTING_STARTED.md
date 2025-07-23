# Getting Started with CareSetu Voice Agent

This guide will help you deploy your CareSetu Voice Agent using LiveKit's free tier and set up your frontend integration.

## Step 1: Set Up LiveKit Cloud (Free Tier)

1. **Run the LiveKit setup script**:

   ```bash
   python scripts/setup_livekit_cloud.py
   ```

   This script will:

   - Open the LiveKit Cloud website
   - Guide you through creating an account
   - Help you set up your project
   - Update your `.env` file with your LiveKit credentials

2. **Verify your `.env` file**:

   Make sure your `.env` file has the following LiveKit-related variables:

   ```
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your-api-key
   LIVEKIT_API_SECRET=your-api-secret
   ```

## Step 2: Deploy Your Agent

Choose one of the following deployment options:

### Option 1: Local Deployment with Docker

1. **Build and run with Docker**:

   ```bash
   # Windows
   deploy.bat

   # Linux/Mac
   docker build -t caresetu-voice-agent .
   docker run -p 8081:8081 --env-file .env caresetu-voice-agent
   ```

### Option 2: Deploy with Docker Compose

1. **Run with Docker Compose**:

   ```bash
   docker-compose up --build
   ```

### Option 3: Cloud Deployment

Follow the instructions in [DEPLOYMENT.md](DEPLOYMENT.md) for deploying to:

- LiveKit Cloud Agents Beta
- Render.com
- Railway.app

## Step 3: Set Up Your Frontend

1. **Generate a test token**:

   ```bash
   python scripts/generate_token.py
   ```

2. **Update the frontend example**:

   Open `frontend-example/index.html` and update:

   ```javascript
   const LIVEKIT_URL = "YOUR_LIVEKIT_URL"; // From your .env file
   const TOKEN = "YOUR_TOKEN"; // From the token generator script
   ```

3. **Test the frontend**:

   You can use any web server to serve the frontend. For example:

   ```bash
   # Python 3
   cd frontend-example
   python -m http.server 8000
   ```

   Then open `http://localhost:8000` in your browser.

## Step 4: Integrate with Your Existing Frontend

1. Use the `frontend-example` as a reference for integrating with your existing frontend application.

2. Key integration points:
   - LiveKit client setup
   - Audio track handling
   - Room connection
   - User interface for voice interaction

## Monitoring Usage

To stay within the free tier limits:

1. **Monitor your LiveKit Cloud usage**:

   - Log in to your LiveKit Cloud account
   - Check the dashboard for usage metrics

2. **Optimize your agent**:
   - Limit conversation duration
   - End sessions properly when not in use
   - Use efficient audio codecs

## Need Help?

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions
- Refer to the [LiveKit documentation](https://docs.livekit.io/)
- See `frontend-example/README.md` for frontend integration details
