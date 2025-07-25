# 🚂 Railway Deployment Guide for CareSetu Voice Agent

## 📋 Pre-Deployment Checklist

### 1. **Get Your API Keys Ready**

```bash
# Required API Keys:
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_secret
ASSEMBLYAI_API_KEY=your_assemblyai_key
GOOGLE_API_KEY=your_google_gemini_key
```

### 2. **Test Locally First**

```bash
# Install Railway optimized dependencies
pip install -r requirements-railway.txt

# Set environment variables
export LIVEKIT_URL="your_url"
export LIVEKIT_API_KEY="your_key"
# ... (set all required vars)

# Test the optimized agent
python src/agent_railway.py
```

## 🚀 Railway Deployment Steps

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (recommended)
3. Verify your account

### Step 2: Deploy from GitHub

1. **Push your code to GitHub** (make sure all Railway files are included)
2. **Connect Railway to your GitHub repo**:
   - Click "New Project" in Railway
   - Select "Deploy from GitHub repo"
   - Choose your CareSetu repository
   - Railway will auto-detect the Dockerfile

### Step 3: Configure Environment Variables

In Railway dashboard, go to your project → Variables tab:

```bash
# Core LiveKit Configuration
LIVEKIT_URL = wss://your-project.livekit.cloud
LIVEKIT_API_KEY = your_livekit_api_key
LIVEKIT_API_SECRET = your_livekit_secret

# AI Services
ASSEMBLYAI_API_KEY = your_assemblyai_key
GOOGLE_API_KEY = your_google_gemini_key

# Railway will auto-set these:
PORT = 8080
RAILWAY_ENVIRONMENT = production
```

### Step 4: Deploy

1. Railway will automatically build and deploy
2. Monitor the build logs for any errors
3. Once deployed, you'll get a public URL

## 📊 Railway Free Tier Limits

### **What You Get:**

- ✅ **512MB RAM** (sufficient for optimized agent)
- ✅ **1 vCPU** (adequate for single user sessions)
- ✅ **$5 monthly credit** (covers ~100 hours of usage)
- ✅ **Persistent storage** (for knowledge base)
- ✅ **Custom domains** (optional)

### **Usage Monitoring:**

- Check Railway dashboard for resource usage
- Monitor memory consumption in logs
- Track monthly credit usage

## 🔧 Optimization Features Included

### **Memory Optimizations:**

- ❌ Removed heavy dependencies (torch, transformers, chromadb)
- ✅ Lightweight search engine (no vector DB)
- ✅ Aggressive garbage collection
- ✅ Single concurrent session limit
- ✅ Minimal knowledge base in memory

### **Performance Optimizations:**

- ✅ Google TTS only (free and reliable)
- ✅ Essential business terms for STT
- ✅ Simplified conversation flow
- ✅ Reduced API calls
- ✅ Efficient error handling

## 🚨 Troubleshooting

### **Common Issues:**

**1. Memory Limit Exceeded**

```bash
# Check logs for memory usage
railway logs

# If memory issues persist:
# - Reduce concurrent sessions further
# - Remove more dependencies
# - Consider upgrading to paid plan
```

**2. Build Failures**

```bash
# Check build logs
railway logs --build

# Common fixes:
# - Verify Dockerfile.railway exists
# - Check requirements-railway.txt
# - Ensure all imports are correct
```

**3. Environment Variable Issues**

```bash
# Verify all required vars are set
railway variables

# Test locally with same variables
export LIVEKIT_URL="your_url"
python src/agent_railway.py
```

## 📈 Scaling Strategy

### **Phase 1: Free Tier (0-100 users/month)**

- Use Railway free tier
- Monitor usage and performance
- Optimize based on real usage patterns

### **Phase 2: Light Usage ($5-20/month)**

- Upgrade to Railway Pro if needed
- Add more concurrent sessions
- Enable additional features

### **Phase 3: Production ($20-50/month)**

- Consider dedicated hosting
- Add monitoring and analytics
- Scale based on user demand

## 🔗 Useful Railway Commands

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# View logs
railway logs

# Check status
railway status

# Deploy manually
railway up
```

## 📞 Support Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **LiveKit Docs**: [docs.livekit.io](https://docs.livekit.io)

## ✅ Post-Deployment Checklist

1. **Test voice functionality** with frontend
2. **Monitor memory usage** in Railway dashboard
3. **Check error logs** for any issues
4. **Verify API integrations** are working
5. **Test appointment booking** if enabled
6. **Monitor monthly credit usage**

Your CareSetu Voice Agent is now optimized for Railway's free tier! 🎉
