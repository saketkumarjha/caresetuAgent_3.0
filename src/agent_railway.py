"""
Railway Optimized Voice Agent - Minimal Memory Footprint
Optimized for Railway's 512MB RAM + 1 vCPU free tier
"""

import asyncio
import logging
import os
import gc
from typing import Optional, List
from datetime import datetime, timedelta
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm, AgentSession, Agent
from livekit.plugins import assemblyai, google
from livekit import rtc
import sys

# Memory optimization
gc.set_threshold(700, 10, 10)  # More aggressive garbage collection

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import optimized modules
try:
    from config_railway import config
    from core.stt_config_railway import create_assemblyai_stt
    from knowledge.engines.simple_search_engine import SimpleSearchEngine
    from integrations.google_calendar_integration import GoogleCalendarIntegration
except ImportError as e:
    logging.error(f"Import error: {e}")
    sys.exit(1)

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RailwayVoiceAgent(Agent):
    """Memory-optimized voice agent for Railway deployment."""
    
    def __init__(self):
        """Initialize with minimal memory footprint."""
        if not config:
            raise ValueError("Configuration not loaded. Check environment variables.")
        
        # Limit concurrent sessions for free tier
        self.max_concurrent_sessions = 1
        self.current_sessions = 0
        
        # Initialize STT (lightweight)
        stt = create_assemblyai_stt()
        logger.info("✅ AssemblyAI STT initialized (Railway optimized)")
        
        # Initialize LLM (Google Gemini - free tier friendly)
        llm_instance = google.LLM(
            model="gemini-1.5-flash",
            api_key=config.google.api_key,
            temperature=0.6,  # Slightly lower for consistency
        )
        logger.info("✅ Google Gemini LLM initialized")
        
        # Initialize TTS (Google only - free and reliable)
        tts = google.TTS()
        logger.info("✅ Google TTS initialized (free tier)")
        
        # Initialize lightweight search engine (no vector DB)
        self.search_engine = SimpleSearchEngine()
        logger.info("✅ Simple search engine initialized")
        
        # Initialize calendar (optional)
        try:
            self.calendar = GoogleCalendarIntegration()
            logger.info("✅ Google Calendar integration initialized")
        except Exception as e:
            logger.warning(f"Calendar integration failed: {e}")
            self.calendar = None
        
        # Initialize Agent with minimal context
        super().__init__(
            instructions=self._create_minimal_context(),
            stt=stt,
            llm=llm_instance,
            tts=tts,
            vad=None,  # Disable VAD to save memory
            allow_interruptions=False,  # Simplify for free tier
        )
        
        logger.info("🚀 Railway Voice Agent initialized successfully")
    
    def _create_minimal_context(self) -> str:
        """Create lightweight system prompt."""
        return """You are CareSetu healthcare voice assistant.

CORE FUNCTIONS:
- Answer healthcare questions clearly and professionally
- Help with appointment scheduling
- Provide app support

GUIDELINES:
- Keep responses concise and helpful
- Ask for clarification when needed
- Be professional and friendly
- For appointments: get name, email, preferred time

LIMITATIONS:
- One conversation at a time
- Basic appointment booking only
- Simple Q&A support

Remember: You represent CareSetu healthcare platform."""
    
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

# Health check endpoint for Railway
async def health_check():
    """Simple health check for Railway."""
    return {"status": "healthy", "service": "caresetu-voice-agent"}

async def entrypoint(ctx: JobContext):
    """Railway optimized entrypoint."""
    logger.info(f"🚀 Starting Railway Voice Agent for room: {ctx.room.name}")
    
    # Memory monitoring
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"📊 Memory usage: {memory_mb:.1f} MB")
    
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
        
        # Monitor memory usage
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"📊 Memory after startup: {memory_mb:.1f} MB")
        
    except Exception as e:
        logger.error(f"❌ Error in entrypoint: {e}")
        raise

def prewarm_process(proc: WorkerOptions):
    """Minimal prewarming for Railway."""
    logger.info("🔥 Prewarming Railway Voice Agent...")
    
    # Force garbage collection
    gc.collect()
    
    # Log memory usage
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"📊 Prewarm memory usage: {memory_mb:.1f} MB")

def main():
    """Main function optimized for Railway."""
    logger.info("🚀 CareSetu Voice Agent - Railway Deployment Starting...")
    
    # Set Railway-specific port
    port = int(os.getenv('PORT', 8080))
    logger.info(f"🌐 Using port: {port}")
    
    # Start health check server for Railway
    try:
        from health_check import start_health_check_server
        if start_health_check_server(port):
            logger.info("✅ Health check server started for Railway")
        else:
            logger.warning("⚠️ Health check server failed to start")
    except Exception as e:
        logger.error(f"❌ Could not start health check server: {e}")
    
    # Run with minimal configuration
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm_process,
    ))

if __name__ == "__main__":
    main()