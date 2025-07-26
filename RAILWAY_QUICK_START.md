# 🚂 Railway Quick Start - CareSetu Voice Agent

## 🚀 One-Click Deployment

### **Method 1: GitHub Integration (Recommended)**

1. **Fork & Connect:**

   - Fork this repository
   - Go to [Railway Dashboard](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository

2. **Set Environment Variables:**

   ```bash
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_secret
   ASSEMBLYAI_API_KEY=your_assemblyai_key
   GOOGLE_API_KEY=your_google_gemini_key
   ```

3. **Deploy:**
   - Click "Deploy Now"
   - Wait 2-3 minutes for build completion
   - Your app will be live at `https://your-app.railway.app`

### **Method 2: Automated Script**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Run deployment script
python deploy_railway.py
```

## ✅ Verification

**Health Check:**

```bash
curl https://your-app.railway.app/health
```

**Expected Response:**

```json
{
  "status": "healthy",
  "service": "caresetu-voice-agent",
  "platform": "railway",
  "version": "1.0.0"
}
```

## 📊 What's Included

- **Optimized Agent**: `src/agent_railway.py`
- **Railway Config**: `railway.toml`
- **Health Checks**: FastAPI endpoints
- **Auto-scaling**: Railway handles scaling
- **SSL/HTTPS**: Automatic certificates
- **Monitoring**: Built-in Railway metrics

## 🔧 Configuration

All configuration is handled via environment variables in Railway dashboard:

- **LiveKit**: Voice communication platform
- **AssemblyAI**: Speech-to-text service
- **Google Gemini**: AI language model
- **Railway**: Automatic port and environment setup

## 📈 Scaling

Railway automatically handles:

- **Traffic spikes**: Auto-scaling instances
- **Resource allocation**: CPU and memory optimization
- **Load balancing**: Distributes requests
- **Health monitoring**: Restarts failed instances

## 💰 Cost

- **Free Tier**: $5 monthly credit (perfect for testing)
- **Pro Plan**: Pay-per-use (scales with usage)
- **No hidden fees**: Transparent pricing

## 🆘 Support

- **Logs**: Railway Dashboard → Deployments → Logs
- **Metrics**: Railway Dashboard → Metrics
- **Help**: Railway Discord or documentation

Your CareSetu Voice Agent is now production-ready on Railway! 🎉
