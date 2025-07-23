# LiveKit Agents Installation Guide

## 🚀 Quick Installation

### Option 1: Automated Installation Script

```bash
python install_dependencies.py
```

### Option 2: Manual Installation Commands

#### Step 1: Install Core LiveKit Agents Framework

```bash
pip install "livekit-agents[assemblyai,google,cartesia,elevenlabs,silero]~=1.0"
```

#### Step 2: Install Additional Dependencies

```bash
pip install livekit>=0.11.0
pip install python-dotenv httpx aiohttp pydantic
```

#### Step 3: Install Optional Dependencies

```bash
pip install redis structlog
```

## 🔍 Verify Installation

Run the test framework to verify everything is working:

```bash
python test_agent_framework.py
```

## 🎤 Test Cartesia TTS Integration

Validate your Cartesia API key:

```bash
python validate_cartesia_key.py
```

## 🐛 Troubleshooting

### Common Issues:

1. **Import Errors**:

   ```bash
   pip install --upgrade --force-reinstall livekit-agents
   ```

2. **Plugin Not Found**:

   ```bash
   pip install livekit-plugins-assemblyai
   pip install livekit-plugins-google
   pip install livekit-plugins-cartesia
   pip install livekit-plugins-elevenlabs
   pip install livekit-plugins-silero
   ```

3. **Windows Build Issues**:

   - Install Visual Studio Build Tools
   - Or use conda: `conda install -c conda-forge livekit-agents`

4. **macOS Issues**:
   - Install Xcode Command Line Tools: `xcode-select --install`

### Version Requirements:

- Python 3.9+
- LiveKit Agents 1.0+
- All API keys configured in `.env` file

## 📋 Required API Keys

Make sure your `.env` file contains:

```bash
# LiveKit Cloud
LIVEKIT_URL=your-livekit-url
LIVEKIT_API_KEY=your-livekit-api-key
LIVEKIT_API_SECRET=your-livekit-api-secret

# Speech Services
ASSEMBLYAI_API_KEY=your-assemblyai-key
GOOGLE_API_KEY=your-google-gemini-key

# TTS Services
CARTESIA_API_KEY=sk_car_kzUZ2jcUyUziozLd9HtqsL
ELEVENLABS_API_KEY=your-elevenlabs-key  # Optional fallback
```

## 🎯 Test Sequence

1. **Install Dependencies**: `python install_dependencies.py`
2. **Test Framework**: `python test_agent_framework.py`
3. **Test Cartesia**: `python validate_cartesia_key.py`
4. **Run Agent**: `python agent.py`

## 📞 Support

If you encounter issues:

1. Check Python version: `python --version` (need 3.9+)
2. Check pip version: `pip --version`
3. Try virtual environment: `python -m venv venv && venv\Scripts\activate`
4. Clear pip cache: `pip cache purge`
