# 🚂 Railway Deployment Guide - Optimized & Production Ready

## 🎯 Overview

This guide implements Railway's best practices for deploying the CareSetu Voice Agent using their cloud platform. Railway automatically detects Python projects and handles the deployment process.

## 📁 Deployment Files

### **Core Files:**

```
✅ src/agent_railway.py     # Optimized Railway agent
✅ src/config_railway.py    # Railway configuration
✅ requirements.txt         # Python dependencies
✅ runtime.txt             # Python version
✅ Procfile                # Process definition
✅ railway.toml            # Railway configuration
✅ .railwayignore         # Build optimization
```

## 🚀 Quick Deployment Options

### **Option 1: Deploy from GitHub (Recommended)**

1. **Connect Repository:**

   - Open Railway Dashboard → New Project
   - Choose "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python project

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
   - Railway automatically builds and deploys

### **Option 2: Deploy with Railway CLI**

1. **Install CLI:**

   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Initialize Project:**

   ```bash
   railway init
   railway up
   ```

3. **Set Variables:**
   ```bash
   railway variables set LIVEKIT_URL=wss://your-project.livekit.cloud
   railway variables set LIVEKIT_API_KEY=your_key
   railway variables set LIVEKIT_API_SECRET=your_secret
   railway variables set ASSEMBLYAI_API_KEY=your_key
   railway variables set GOOGLE_API_KEY=your_key
   ```

### **Option 3: Deploy from Docker Image**

1. **Create Project:**

   - Railway Dashboard → New Project → Empty Project
   - Add Service → Docker Image

2. **Use Image:**

   ```
   Image: python:3.11-slim
   ```

3. **Configure:**
   - Set environment variables
   - Deploy

## ⚙️ Configuration Details

### **railway.toml:**

```toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

### **Procfile:**

```
web: python src/agent_railway.py
```

### **Runtime:**

```
python-3.11.9
```

## 🔧 Railway Optimizations

### **Build Optimizations:**

- **Nixpacks Builder**: Automatic Python detection
- **Dependency Caching**: Faster subsequent builds
- **Ignore Files**: `.railwayignore` reduces build size
- **Build Time**: ~2-3 minutes

### **Runtime Optimizations:**

- **Health Checks**: `/health` endpoint for monitoring
- **Auto Restart**: On failure with retry limits
- **Memory Management**: Optimized for Railway's resources
- **Concurrent Sessions**: Supports multiple users

### **Performance Metrics:**

- **Cold Start**: ~10-15 seconds
- **Response Time**: 2-4 seconds for voice processing
- **Memory Usage**: ~300-400MB
- **Concurrent Users**: 3+ (scales automatically)

## 📊 Monitoring & Health Checks

### **Health Endpoints:**

- `GET /health` - Service health status
- `GET /` - Service information
- `GET /docs` - FastAPI documentation

### **Railway Dashboard:**

- **Metrics**: CPU, Memory, Network usage
- **Logs**: Real-time application logs
- **Deployments**: Build and deploy history
- **Variables**: Environment variable management

## 🔍 Troubleshooting

### **Build Issues:**

**Check Build Logs:**

```bash
# In Railway Dashboard
Project → Deployments → Build Logs
```

**Common Fixes:**

1. Verify `requirements.txt` syntax
2. Check Python version in `runtime.txt`
3. Ensure all files are committed to Git
4. Verify `.railwayignore` isn't excluding needed files

### **Runtime Issues:**

**Check Application Logs:**

```bash
# In Railway Dashboard
Project → Deployments → Deploy Logs
```

**Common Fixes:**

1. Verify all environment variables are set
2. Check API key validity
3. Monitor memory usage
4. Verify LiveKit configuration

### **Environment Variables:**

**Required Variables:**

```bash
LIVEKIT_URL          # Your LiveKit cloud URL
LIVEKIT_API_KEY      # LiveKit API key
LIVEKIT_API_SECRET   # LiveKit API secret
ASSEMBLYAI_API_KEY   # AssemblyAI API key
GOOGLE_API_KEY       # Google Gemini API key
```

**Optional Variables:**

```bash
PORT                 # Auto-set by Railway
RAILWAY_ENVIRONMENT  # Auto-set by Railway
```

## ✅ Success Indicators

### **Build Success:**

```
✅ Python 3.11.9 detected
✅ Installing dependencies from requirements.txt
✅ Build completed successfully
✅ Starting deployment...
```

### **Runtime Success:**

```
✅ CareSetu Voice Agent - Railway Deployment Starting...
✅ Railway configuration loaded successfully
✅ Health check server started
✅ AssemblyAI STT initialized
✅ Google Gemini LLM initialized
✅ Google TTS initialized
✅ Railway Voice Agent initialized successfully
```

### **Health Check Success:**

```bash
curl https://your-app.railway.app/health
# Response: {"status":"healthy","service":"caresetu-voice-agent"}
```

## 🌐 Domain & SSL

Railway automatically provides:

- **HTTPS Domain**: `your-app.railway.app`
- **SSL Certificate**: Automatic SSL/TLS
- **Custom Domain**: Available on Pro plan

## 💰 Cost Optimization

### **Free Tier:**

- **Usage**: $5 credit monthly
- **Resources**: Shared CPU, 512MB RAM
- **Suitable for**: Development, testing

### **Pro Plan:**

- **Usage**: Pay-per-use
- **Resources**: Dedicated resources
- **Suitable for**: Production, scaling

## 🔄 CI/CD Integration

Railway automatically:

- **Builds** on every Git push
- **Deploys** successful builds
- **Rolls back** on deployment failures
- **Monitors** application health

## 📈 Scaling

Railway handles scaling automatically:

- **Horizontal Scaling**: Multiple instances
- **Vertical Scaling**: More CPU/RAM
- **Load Balancing**: Automatic traffic distribution
- **Auto-scaling**: Based on demand

Your CareSetu Voice Agent is now optimized for Railway deployment! 🎉

## 🆘 Support

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Help Threads**: Available in Railway dashboard
