"""
Railway Optimized Voice Agent - Production Ready
Optimized for Railway deployment with auto-scaling support
"""

import asyncio
import logging
import os
import gc
from typing import Optional
from livekit.agents import JobContext, WorkerOptions, cli, AgentSession, Agent
from livekit.plugins import assemblyai, google
from livekit import rtc
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import threading

# Memory optimization for Railway
gc.set_threshold(700, 10, 10)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import optimized modules
try:
    from config_railway import config
    from core.stt_config_railway import create_assemblyai_stt
except ImportError as e:
    logging.error(f"Import error: {e}")
    # Create minimal fallback config
    class FallbackConfig:
        def __init__(self):
            self.railway = type('obj', (object,), {'port': int(os.getenv('PORT', 8080))})()
    config = FallbackConfig()

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RailwayVoiceAgent(Agent):
    """Production-ready voice agent for Railway deployment."""
    
    def __init__(self):
        """Initialize with Railway optimizations."""
        if not config:
            raise ValueError("Configuration not loaded. Check environment variables.")
        
        # Railway auto-scaling friendly
        self.max_concurrent_sessions = 3  # Railway can handle more
        self.current_sessions = 0
        
        # Initialize STT
        stt = create_assemblyai_stt()
        logger.info("✅ AssemblyAI STT initialized")
        
        # Initialize LLM (Google Gemini)
        llm_instance = google.LLM(
            model="gemini-1.5-flash",
            api_key=os.getenv('GOOGLE_API_KEY'),
            temperature=0.7,
        )
        logger.info("✅ Google Gemini LLM initialized")
        
        # Initialize TTS
        tts = google.TTS()
        logger.info("✅ Google TTS initialized")
        
        # Initialize Agent
        super().__init__(
            instructions=self._create_system_prompt(),
            stt=stt,
            llm=llm_instance,
            tts=tts,
            allow_interruptions=True,
        )
        
        logger.info("🚀 Railway Voice Agent initialized successfully")
    
    def _create_system_prompt(self) -> str:
        """Create optimized system prompt for Railway."""
        return """You are CareSetu's AI healthcare assistant, deployed on Railway cloud platform.

CORE CAPABILITIES:
- Healthcare consultation support
- Appointment scheduling assistance  
- Medical information guidance
- CareSetu app support

INTERACTION STYLE:
- Professional yet friendly tone
- Clear, concise responses
- Ask clarifying questions when needed
- Provide actionable guidance

HEALTHCARE FOCUS:
- General health information
- Symptom assessment guidance
- Medication reminders
- Wellness tips

TECHNICAL CONSTRAINTS:
- Optimized for voice interaction
- Railway cloud deployment
- Real-time response capability

Remember: You represent CareSetu's commitment to accessible healthcare technology."""
    
    async def handle_user_message(self, message: str, session_id: str = None) -> str:
        """Handle user messages with memory optimization."""
        try:
            # Check session limit
            if self.current_sessions >= self.max_concurrent_sessions:
                return "I'm currently helping another user. Please try again in a moment."
            
            self.current_sessions += 1
            
            # Simple intent detection
            message_lower = message.lower()
            
            # Handle appointment requests
            if any(word in message_lower for word in ['appointment', 'book', 'schedule']):
                response = await self._handle_appointment_request(message)
            
            # Handle availability checks
            elif any(word in message_lower for word in ['available', 'availability', 'free']):
                response = await self._handle_availability_check(message)
            
            # Handle general questions
            else:
                response = await self._handle_general_question(message)
            
            # Force garbage collection after each interaction
            gc.collect()
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return "I'm sorry, I encountered an error. Please try again."
        
        finally:
            self.current_sessions = max(0, self.current_sessions - 1)
    
    async def _handle_appointment_request(self, message: str) -> str:
        """Handle appointment booking requests."""
        if not self.calendar:
            return ("I can help you with appointment information, but booking is currently unavailable. "
                   "Please contact our support team directly.")
        
        return ("I'd be happy to help you schedule an appointment! "
               "I'll need your name, email, and preferred date/time. "
               "What works best for you?")
    
    async def _handle_availability_check(self, message: str) -> str:
        """Handle availability check requests."""
        return ("Our general availability is Monday to Friday, 9 AM to 6 PM. "
               "For specific appointment slots, please let me know your preferred date "
               "and I'll check what's available.")
    
    async def _handle_general_question(self, message: str) -> str:
        """Handle general healthcare questions."""
        # Simple keyword-based responses (no heavy ML processing)
        keywords = {
            'app': "CareSetu app is available on Play Store and App Store. You can book consultations, order medicines, and access health records.",
            'consultation': "We offer online consultations with qualified doctors. You can book through our app or website.",
            'medicine': "Medicine delivery is available through our platform. Orders are typically delivered within 24 hours.",
            'support': "For technical support, you can email us or use the in-app help feature.",
            'hours': "Our support is available 9 AM to 6 PM, Monday to Friday. Emergency support is available 24/7.",
        }
        
        message_lower = message.lower()
        for keyword, response in keywords.items():
            if keyword in message_lower:
                return response
        
        # Default response
        return ("I'm here to help with CareSetu healthcare services. "
               "I can assist with appointments, app support, and general health questions. "
               "What would you like to know?")

# FastAPI app for Railway health checks
app = FastAPI(title="CareSetu Voice Agent", version="1.0.0")

@app.get("/health")
async def health_check():
    """Railway health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "caresetu-voice-agent",
        "platform": "railway",
        "version": "1.0.0"
    })

@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse({
        "message": "CareSetu Voice Agent - Railway Deployment",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs"
        }
    })

async def entrypoint(ctx: JobContext):
    """Railway optimized entrypoint."""
    logger.info(f"🚀 Starting Railway Voice Agent for room: {ctx.room.name}")
    
    # Memory monitoring (simplified for Railway)
    logger.info("📊 Starting Railway Voice Agent")
    
    try:
        # Create optimized agent
        agent = RailwayVoiceAgent()
        
        # Create session with minimal configuration
        session = AgentSession(
            stt=agent.stt,
            llm=agent.llm,
            tts=agent.tts,
            allow_interruptions=False,  # Simplify for free tier
        )
        
        # Start session
        await session.start(ctx.room)
        logger.info("✅ Railway Voice Agent session started")
        
        # Log successful startup
        logger.info("📊 Railway Voice Agent startup completed")
        
    except Exception as e:
        logger.error(f"❌ Error in entrypoint: {e}")
        raise

def prewarm_process(proc: WorkerOptions):
    """Minimal prewarming for Railway."""
    logger.info("🔥 Prewarming Railway Voice Agent...")
    
    # Force garbage collection
    gc.collect()
    
    # Log memory usage (simplified)
    logger.info("📊 Prewarm completed")

def start_health_server():
    """Start FastAPI health check server for Railway."""
    port = int(os.getenv('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def main():
    """Main function optimized for Railway deployment."""
    logger.info("🚀 CareSetu Voice Agent - Railway Deployment Starting...")
    
    # Start health check server in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    logger.info("✅ Health check server started")
    
    # Run LiveKit agent
    try:
        cli.run_app(WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm_process,
        ))
    except Exception as e:
        logger.error(f"❌ Agent startup failed: {e}")
        raise

if __name__ == "__main__":
    main()