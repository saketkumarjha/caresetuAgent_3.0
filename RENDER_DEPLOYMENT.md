# Deploying CareSetu Voice Agent to Render.com

This guide will walk you through deploying your CareSetu Voice Agent to Render.com using their free tier.

## Prerequisites

1. A [Render.com](https://render.com) account
2. Your LiveKit Cloud credentials (API Key, API Secret, and WebSocket URL)
3. Your project code pushed to a Git repository (GitHub, GitLab, etc.)

## Deployment Steps

### Option 1: One-Click Deployment (Recommended)

1. **Push your code to a Git repository**

   Make sure your code is pushed to GitHub, GitLab, or Bitbucket.

2. **Create a new Web Service on Render**

   - Log in to your [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Web Service"
   - Connect your Git repository
   - Select the repository with your CareSetu Voice Agent code

3. **Configure the Web Service**

   - **Name**: `caresetu-voice-agent` (or any name you prefer)
   - **Environment**: `Docker`
   - **Branch**: `main` (or your default branch)
   - **Plan**: `Free`

4. **Set Environment Variables**

   Add the following environment variables:

   ```
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your-api-key
   LIVEKIT_API_SECRET=your-api-secret
   ASSEMBLYAI_API_KEY=your-assemblyai-key
   GOOGLE_API_KEY=your-google-api-key
   GOOGLE_CALENDAR_API_KEY=your-google-calendar-api-key
   GOOGLE_CLIENT_ID=your-google-client-id
   CARTESIA_API_KEY=your-cartesia-api-key
   ELEVENLABS_API_KEY=your-elevenlabs-api-key
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_ADDRESS=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   ```

5. **Create Disk Storage** (Optional)

   If you need persistent storage:

   - Scroll down to "Disks"
   - Click "Add Disk"
   - Set the mount path to `/app/data`
   - Set the size to 1 GB (minimum for free tier)

6. **Deploy**

   Click "Create Web Service" to deploy your agent.

### Option 2: Using render.yaml (Alternative)

1. **Push your code with the render.yaml file**

   Make sure the `render.yaml` file is in the root of your repository.

2. **Create a new Blueprint on Render**

   - Log in to your [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Blueprint"
   - Connect your Git repository
   - Select the repository with your CareSetu Voice Agent code

3. **Configure Environment Variables**

   You'll be prompted to set values for all the environment variables defined in the `render.yaml` file.

4. **Deploy**

   Click "Apply" to deploy your agent.

## Verifying Deployment

1. **Check the deployment logs**

   After deployment starts, you can view the logs to ensure everything is working correctly.

2. **Test the health check endpoint**

   Once deployed, you can access the health check endpoint at:
   `https://your-service-name.onrender.com/`

## Connecting Your Frontend

1. **Update your frontend configuration**

   Update your frontend code to use the Render.com URL:

   ```javascript
   const LIVEKIT_URL = "YOUR_LIVEKIT_URL"; // Your LiveKit Cloud URL
   ```

2. **Generate a token**

   Use the token generation script to create a token for testing:

   ```bash
   python scripts/generate_token.py
   ```

3. **Test the connection**

   Use the frontend example to test the connection to your deployed agent.

## Monitoring and Scaling

- **Monitor usage**: Check the Render.com dashboard for usage metrics
- **Logs**: View logs in the Render.com dashboard
- **Scaling**: Upgrade to a paid plan if you need more resources

## Troubleshooting

- **Deployment fails**: Check the logs for error messages
- **Agent not connecting**: Verify your LiveKit credentials
- **Health check fails**: Make sure the health check endpoint is working

## Limitations of Free Tier

- **CPU/Memory**: Limited resources (shared CPU, 512 MB RAM)
- **Disk**: 1 GB persistent disk
- **Bandwidth**: Limited bandwidth
- **Sleep**: Free services sleep after 15 minutes of inactivity

To prevent sleeping, you can:

1. Set up a cron job to ping your service every 14 minutes
2. Upgrade to a paid plan ($7/month for the "Starter" plan)

## Next Steps

1. Set up a custom domain (requires paid plan)
2. Configure automatic scaling (requires paid plan)
3. Set up monitoring and alerts
