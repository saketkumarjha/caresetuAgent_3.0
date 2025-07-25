# 🚂 Railway Deployment Guide - Clean & Simple

## 📋 Current Railway Setup

### **Essential Files Only:**

```
✅ requirements.txt          # Python dependencies
✅ runtime.txt              # Python 3.11.9
✅ Procfile                 # Process definition
✅ railway.toml             # Railway configuration
✅ src/agent_railway.py     # Optimized agent
✅ src/config_railway.py    # Railway config
✅ .railwayignore          # Build optimization
```

## 🚀 Quick Deployment

### **1. Set Environment Variables in Railway Dashboard:**

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_secret
ASSEMBLYAI_API_KEY=your_assemblyai_key
GOOGLE_API_KEY=your_google_gemini_key
```

### **2. Deploy:**

```bash
git add .
git commit -m "Clean Railway deployment setup"
git push origin main
```

### **3. Railway Auto-Detection:**

- ✅ Detects Python project from `requirements.txt`
- ✅ Uses Python 3.11.9 from `runtime.txt`
- ✅ Runs `python src/agent_railway.py` from `Procfile`
- ✅ Applies Railway configuration from `railway.toml`

## 📊 Optimizations

### **Memory Usage:**

- **Target**: <400MB (within 512MB limit)
- **Concurrent Users**: 1 (prevents overload)
- **Dependencies**: Minimal essential packages only

### **Performance:**

- **Build Time**: ~2-3 minutes (no Docker)
- **Cold Start**: ~10-15 seconds
- **Response Time**: 2-4 seconds for voice processing

## 🔧 Troubleshooting

### **Build Issues:**

```bash
# Check Railway logs
railway logs --build

# Common fixes:
# 1. Verify all environment variables are set
# 2. Check requirements.txt syntax
# 3. Ensure src/agent_railway.py exists
```

### **Runtime Issues:**

```bash
# Check application logs
railway logs

# Common fixes:
# 1. Verify API keys are correct
# 2. Check LiveKit configuration
# 3. Monitor memory usage
```

## ✅ Success Indicators

**Build Success:**

```
✅ Python 3.11.9 detected
✅ Installing dependencies from requirements.txt
✅ Build completed successfully
```

**Runtime Success:**

```
✅ CareSetu Voice Agent - Railway Deployment Starting...
✅ Railway configuration loaded successfully
✅ AssemblyAI STT initialized (Railway optimized)
✅ Google Gemini LLM initialized
✅ Google TTS initialized (free tier)
✅ Simple search engine initialized
✅ Railway Voice Agent initialized successfully
```

Your Railway deployment is now clean and optimized! 🎉
