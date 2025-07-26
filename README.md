# CareSetu Voice Agent 🎤

An AI-powered healthcare voice assistant with real-time appointment booking, RAG (Retrieval-Augmented Generation) capabilities, and comprehensive knowledge management.

## 🌟 Features

### Core Capabilities

- **🎙️ Voice Interaction**: Natural speech-to-text and text-to-speech processing
- **📅 Real-time Appointment Booking**: Instant scheduling with Google Calendar integration
- **🧠 RAG-Enhanced Responses**: Intelligent document retrieval and knowledge synthesis
- **📚 Knowledge Management**: Comprehensive document processing and semantic search
- **💬 Conversation Learning**: Adaptive learning from user interactions
- **📧 Email Confirmations**: Immediate appointment confirmations via email

### Healthcare-Specific Features

- **🏥 Healthcare Guidance**: Answer medical questions using company documents
- **📱 App Support**: Help with CareSetu app navigation
- **📋 Appointment Management**: Book, cancel, and reschedule appointments
- **🔍 Semantic Search**: Find relevant information from knowledge base
- **📊 Multi-tenant Support**: Handle multiple healthcare organizations

## 🏗️ Architecture

```
caresetuAgent/
├── careSetuFrontend                  #frontend part
├── src/                              # Main source code
│   ├── agent.py                      # Main voice agent
│   ├── config.py                     # Configuration management
│   └── core/                         # Core components
├── integrations/                     # External service integrations
├── knowledge/                        # Knowledge management system
│   ├── engines/                      # RAG and search engines
│   ├── processors/                   # Document processing
│   ├── storage/                      # Knowledge storage
│   └── managers/                     # Knowledge management
├── data/                            # Data storage
├── tests/                           # Test suite
├── scripts/                         # Utility scripts
├── docs/                           # Documentation
└── config/                         # Configuration files
```

## 🚀 Quick Start

### 🚂 Railway Deployment (Recommended)

**One-Click Deploy:**

1. Fork this repository
2. Go to [Railway Dashboard](https://railway.app) → New Project → Deploy from GitHub
3. Set environment variables (see [Railway Quick Start](RAILWAY_QUICK_START.md))
4. Deploy and get instant HTTPS URL

**Automated Deploy:**

```bash
npm install -g @railway/cli
python deploy_railway.py
```

📖 **Full Guide**: [Railway Deployment Guide](RAILWAY_DEPLOYMENT.md)

### Prerequisites

- Python 3.11+
- Google Cloud Account (for Calendar API)
- LiveKit Account (Free tier available)
- AssemblyAI Account

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd caresetuAgent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Configure Google Calendar**

   - Follow the [Google Calendar Setup Guide](docs/GOOGLE_CALENDAR_SETUP.md)
   - Place `credentials.json` in the `config/` directory

5. **Run the agent locally**
   ```bash
   python main.py
   ```

### Deployment Options

1. **Docker (Local or Cloud)**

   ```bash
   # Windows
   deploy.bat

   # Linux/Mac
   docker build -t caresetu-voice-agent .
   docker run -p 8081:8081 --env-file .env caresetu-voice-agent
   ```

2. **Docker Compose**

   ```bash
   docker-compose up --build
   ```

3. **Cloud Deployment (Free Options)**
   - LiveKit Cloud (Free tier: 1,000 participant minutes/month)
   - Render.com (Free tier available)
   - Railway.app (Free tier available)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## ⚙️ Configuration

### Environment Variables

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Speech Services
ASSEMBLYAI_API_KEY=your-assemblyai-key
CARTESIA_API_KEY=your-cartesia-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# Google Services
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CLIENT_ID=your-google-client-id

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### Google Calendar Setup

1. **Enable Google Calendar API**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable Calendar API
   - Create OAuth2 credentials

2. **Download credentials**

   - Download `credentials.json`
   - Place in `config/` directory

3. **First-time authentication**
   ```bash
   python scripts/setup_calendar.py
   ```

## 📖 Usage

### Basic Voice Interaction

The agent supports natural language interactions for:

- **Appointment Booking**: "I'd like to book an appointment for tomorrow at 2 PM"
- **Availability Check**: "What times are available on Friday?"
- **Healthcare Questions**: "What services does CareSetu offer?"
- **App Support**: "How do I download the CareSetu app?"

### Appointment Management

```python
# Quick booking example
result = await agent.quick_book_appointment(
    customer_name="John Doe",
    customer_email="john@example.com",
    preferred_date="2025-07-25",
    preferred_time="14:00",
    appointment_type="consultation"
)
```

### Knowledge Base Integration

The agent automatically retrieves relevant information from:

- Company documents (PDFs)
- FAQ databases
- Policy documents
- Procedure manuals

## 🧪 Testing

### Run All Tests

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# Diagnostics
python tests/diagnostics/email_diagnostics.py
python tests/diagnostics/check_appointments.py
```

### Test Appointment Booking

```bash
python tests/integration/test_appointment_email.py
```

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION_GUIDE.md)
- [Google Calendar Setup](docs/GOOGLE_CALENDAR_SETUP.md)
- [PDF Upload Guide](docs/PDF_UPLOAD_GUIDE.md)
- [Agent Framework](docs/AGENT_FRAMEWORK_README.md)
- [TTS Integration](docs/CARTESIA_TTS_INTEGRATION.md)

## 🔧 Development

### Adding New Features

1. **Core functionality**: Add to `src/core/`
2. **Integrations**: Add to `integrations/`
3. **Knowledge processing**: Add to `knowledge/processors/`
4. **Tests**: Add corresponding tests in `tests/`

### Code Structure

- **Agent Core**: `src/agent.py` - Main voice agent logic
- **Configuration**: `src/config.py` - Configuration management
- **STT/TTS**: `src/core/stt_config.py` - Speech processing
- **RAG Engine**: `knowledge/engines/simple_rag_engine.py` - Knowledge retrieval
- **Calendar**: `integrations/google_calendar_integration.py` - Appointment booking

## 🚨 Troubleshooting

### Common Issues

1. **Email confirmations not working**

   ```bash
   python tests/diagnostics/email_diagnostics.py
   ```

2. **Calendar integration issues**

   ```bash
   python tests/diagnostics/check_appointments.py
   ```

3. **TTS connection problems**
   - Check API keys in `.env`
   - Verify network connectivity
   - Try different TTS providers

### Debug Mode

```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 📊 Monitoring

### Health Checks

```python
health_status = await agent.health_check()
print(health_status)
```

### Performance Metrics

- Response time tracking
- API usage monitoring
- Error rate analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Email**: saket@jha.com
- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues

## 🔄 Version History

- **v1.0.0**: Initial release with voice interaction and appointment booking
- **v1.1.0**: Added RAG capabilities and knowledge management
- **v1.2.0**: Enhanced email confirmations and multi-tenant support

---

**Built for CareSetu Healthcare**
