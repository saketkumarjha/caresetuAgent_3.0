# Deploying to LiveKit Cloud Agents

This guide will walk you through deploying your CareSetu Voice Agent to LiveKit Cloud Agents Beta.

## Prerequisites

1. Docker installed on your machine
2. LiveKit Cloud account
3. Access to LiveKit Cloud Agents Beta
4. Your project code with proper LiveKit Agents integration

## Step 1: Prepare Your Agent

Your agent is already set up to work with LiveKit Agents. The key components are:

1. **Dockerfile**: Configured to run `python src/agent.py start`
2. **agent.py**: Uses the LiveKit Agents CLI with proper worker options
3. **.env file**: Contains your LiveKit credentials

## Step 2: Sign Up for LiveKit Cloud Agents Beta

1. Visit [LiveKit Cloud Agents Beta](https://livekit.io/cloud-agents-beta)
2. Sign up for the beta program
3. Wait for approval (this may take some time)

## Step 3: Build Your Docker Image

```bash
# Run the deployment helper script
python deploy_to_livekit.py
```

This script will:

- Check your LiveKit credentials
- Verify Docker is installed
- Build your Docker image
- Open the LiveKit Cloud Agents Beta signup page
- Generate a token for testing

## Step 4: Deploy to LiveKit Cloud Agents

Once you have access to LiveKit Cloud Agents:

1. **Log in to LiveKit Cloud**
2. **Navigate to the Agents section**
3. **Click "Create Agent"**
4. **Configure your agent**:

   - **Name**: CareSetu Voice Agent
   - **Deployment Method**: Docker Image
   - **Docker Image**: caresetu-voice-agent
   - **Environment Variables**: Add all variables from your .env file
   - **Worker Pool Size**: Start with 1-2 workers (can scale later)
   - **CPU/Memory**: 1 CPU, 2GB memory per worker (minimum)

5. **Click "Deploy"**

## Step 5: Test Your Deployment

1. **Generate a token**:

   ```bash
   python scripts/generate_token.py
   ```

2. **Update your frontend**:

   - Open `frontend-example/index.html`
   - Update the LiveKit URL and token

3. **Test the connection**:
   - Open the frontend in your browser
   - Connect to your agent
   - Start a conversation

## Monitoring and Scaling

1. **Monitor usage** in the LiveKit Cloud dashboard
2. **Scale workers** based on demand:
   - For every 25 concurrent sessions, add 4 cores and 8GB of memory
   - Set worker `load_threshold` to 0.75 (default)
   - Configure autoscaling to scale up at 0.50 load

## Troubleshooting

1. **Agent not connecting**:

   - Check your LiveKit credentials
   - Verify your Docker image is built correctly
   - Check the logs in LiveKit Cloud dashboard

2. **Audio issues**:

   - Verify your STT and TTS services are configured correctly
   - Check API keys for external services

3. **Deployment fails**:
   - Check your Dockerfile
   - Verify your agent.py has the correct CLI setup
   - Check for any errors in the deployment logs

## Next Steps

1. **Set up multiple environments**:

   - Create separate projects for development, staging, and production
   - Each environment should have its own LiveKit credentials

2. **Implement monitoring**:

   - Set up alerts for high CPU/memory usage
   - Monitor worker availability

3. **Optimize performance**:
   - Fine-tune worker options
   - Adjust load thresholds based on your specific use case
