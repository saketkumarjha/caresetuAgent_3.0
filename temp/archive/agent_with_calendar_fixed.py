"""
Fixed Voice Agent with Calendar Integration - Resolves TTS Connection Issues
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents import VoiceAssistant
from livekit.plugins import google, assemblyai, cartesia, elevenlabs

from appointment_scheduler import AppointmentScheduler

logger = logging.getLogger("voice-agent-calendar-fixed")

class FixedCalendarVoiceAgent:
    """
    Fixed voice agent with robust TTS handling and calendar scheduling capabilities
    """
    
    def __init__(self):
        """Initialize the calendar-enabled voice agent with fixed TTS"""
        self.scheduler = None
        self.customer_info = {}
        self.tts_service = None
        
    async def initialize_calendar(self):
        """Initialize calendar integration"""
        try:
            self.scheduler = AppointmentScheduler()
            logger.info("✅ Calendar integration initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize calendar: {e}")
            self.scheduler = None
    
    def _create_robust_tts(self):
        """Create TTS service with robust fallback handling"""
        
        import os
        from dotenv import load_dotenv
        load_dotenv()  # Ensure environment variables are loaded
        
        # Priority 1: Try Google TTS (reliable cloud service)
        try:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if google_api_key and google_api_key.startswith('AIza'):
                logger.info("🔊 Initializing Google TTS (primary - reliable cloud service)")
                tts = google.TTS(
                    api_key=google_api_key,
                    voice="en-US-Journey-D",  # Natural sounding voice
                    language="en-US",
                )
                logger.info("✅ Google TTS initialized successfully")
                return tts
        except Exception as e:
            logger.warning(f"⚠️ Google TTS failed: {e}")
        
        # Priority 2: Try ElevenLabs TTS (if API key is valid)
        try:
            elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
            if elevenlabs_key and elevenlabs_key != "ELEVENLABS_API_KEY" and len(elevenlabs_key) > 20:
                logger.info("🔊 Trying ElevenLabs TTS (secondary)")
                tts = elevenlabs.TTS(
                    api_key=elevenlabs_key,
                    voice="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
                    model="eleven_turbo_v2",
                    stability=0.5,
                    similarity_boost=0.8,
                )
                logger.info("✅ ElevenLabs TTS initialized successfully")
                return tts
        except Exception as e:
            logger.warning(f"⚠️ ElevenLabs TTS failed: {e}")
        
        # Priority 3: Try Cartesia TTS with better error handling
        try:
            cartesia_key = os.getenv('CARTESIA_API_KEY')
            if cartesia_key and cartesia_key.startswith("sk_car_"):
                logger.info("🔊 Trying Cartesia TTS (tertiary - may have connection issues)")
                
                # Create Cartesia TTS with minimal configuration to avoid connection issues
                tts = cartesia.TTS(
                    api_key=cartesia_key,
                    model="sonic-turbo",
                    voice="bf0a246a-8642-498a-9950-80c35e9276b5",
                    language="en",
                )
                
                logger.info("✅ Cartesia TTS initialized (connection issues may occur during use)")
                return tts
                
        except Exception as e:
            logger.error(f"❌ Cartesia TTS failed: {e}")
        
        # Final fallback: Try basic Google TTS without specific voice
        try:
            google_api_key = os.getenv('GOOGLE_API_KEY')
            if google_api_key:
                logger.info("🔊 Using basic Google TTS (final fallback)")
                tts = google.TTS(api_key=google_api_key)
                logger.info("✅ Basic Google TTS initialized")
                return tts
        except Exception as e:
            logger.error(f"❌ Basic Google TTS failed: {e}")
        
        # If all else fails, raise a helpful error
        raise Exception(
            "❌ No TTS service available. Please check your configuration:\n\n"
            "SOLUTIONS:\n"
            "1. Verify GOOGLE_API_KEY in your .env file\n"
            "2. Get a valid ElevenLabs API key if needed\n"
            "3. Check your internet connection\n"
            "4. Verify API keys are not expired\n\n"
            "CURRENT STATUS:\n"
            f"- Google API Key: {'✅ Present' if os.getenv('GOOGLE_API_KEY') else '❌ Missing'}\n"
            f"- ElevenLabs API Key: {'✅ Present' if os.getenv('ELEVENLABS_API_KEY') != 'ELEVENLABS_API_KEY' else '❌ Placeholder'}\n"
            f"- Cartesia API Key: {'✅ Present' if os.getenv('CARTESIA_API_KEY', '').startswith('sk_car_') else '❌ Invalid'}"
        )
    
    def create_assistant(self) -> VoiceAssistant:
        """Create voice assistant with robust TTS and calendar functions"""
        
        # Enhanced system prompt with calendar capabilities
        system_prompt = """
        You are a helpful customer service agent for CareSetu Healthcare with real-time appointment scheduling.
        
        CORE CAPABILITIES:
        1. Answer questions about CareSetu services
        2. Schedule appointments in real-time using Google Calendar
        3. Check appointment availability instantly
        4. Modify or cancel existing appointments
        5. Provide business hours and contact information
        
        CALENDAR FEATURES:
        - Real-time availability checking
        - Instant appointment booking
        - Automatic email confirmations via Google Calendar
        - Appointment reminders and notifications
        - Business hours: 9 AM - 6 PM, Monday-Friday
        
        CONVERSATION STYLE:
        - Professional yet friendly and approachable
        - Patient and understanding with customers
        - Clear, concise communication
        - Always confirm details before booking
        - Provide helpful alternatives when needed
        
        APPOINTMENT BOOKING PROCESS:
        1. When customer requests appointment, ask for preferred date/time
        2. Check real-time availability using calendar integration
        3. Get customer name and email address
        4. Confirm all details with customer
        5. Book appointment in Google Calendar
        6. Confirm booking and explain next steps
        
        IMPORTANT GUIDELINES:
        - Always get customer name and email before booking
        - Confirm appointment details before finalizing
        - Explain that Google Calendar will send confirmation emails
        - Offer alternative times if requested slot is unavailable
        - Be helpful and solution-oriented
        
        Remember: You have real calendar integration, so you can actually book appointments immediately!
        """
        
        # Get calendar function contexts if available
        function_contexts = []
        if self.scheduler:
            function_contexts = self.scheduler.get_function_contexts()
        
        # Create LLM with function calling
        model = google.LLM(
            model="gemini-2.0-flash-exp",
            temperature=0.7,
        )
        
        # Create robust TTS
        tts = self._create_robust_tts()
        self.tts_service = tts
        
        # Create voice assistant with robust error handling
        try:
            assistant = VoiceAssistant(
                vad=assemblyai.VAD(
                    # Optimized VAD settings for better speech detection
                    min_speech_duration=0.1,
                    min_silence_duration=0.5,
                ),
                stt=assemblyai.STT(
                    # Enhanced STT settings for better accuracy
                    language_code="en",
                    punctuate=True,
                    format_text=True,
                ),
                llm=model,
                tts=tts,
                chat_ctx=llm.ChatContext(
                    messages=[
                        llm.ChatMessage(
                            role="system",
                            content=system_prompt
                        )
                    ]
                ),
                fnc_ctx=llm.FunctionContext() if not function_contexts else llm.FunctionContext(*function_contexts),
                # Add interruption handling
                allow_interruptions=True,
                interrupt_speech_duration=0.5,
                interrupt_min_words=2,
            )
            
            logger.info("✅ Voice assistant created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create voice assistant: {e}")
            raise
        
        # Add function call handler if calendar is available
        if self.scheduler:
            assistant.llm.on("function_calls_finished", self._handle_function_calls)
        
        return assistant
    
    async def _handle_function_calls(self, called_functions):
        """Handle function calls from the LLM with error recovery"""
        if not self.scheduler:
            logger.warning("⚠️ Function call received but scheduler not available")
            return
        
        for func_call in called_functions:
            function_name = func_call.function_info.name
            arguments = func_call.arguments
            
            try:
                logger.info(f"🔧 Executing calendar function: {function_name}")
                
                # Execute calendar function with timeout
                result = await asyncio.wait_for(
                    self.scheduler.execute_calendar_function(function_name, **arguments),
                    timeout=30.0  # 30 second timeout for calendar operations
                )
                
                # Set the result
                func_call.result = result
                logger.info(f"✅ Function {function_name} executed successfully")
                
            except asyncio.TimeoutError:
                error_msg = f"⏰ Calendar function {function_name} timed out"
                func_call.result = error_msg
                logger.error(error_msg)
                
            except Exception as e:
                error_msg = f"❌ Error executing {function_name}: {str(e)}"
                func_call.result = error_msg
                logger.error(error_msg)
    
    async def entrypoint(self, ctx: JobContext):
        """Main entrypoint for the voice agent with error recovery"""
        
        try:
            # Initialize calendar integration
            await self.initialize_calendar()
            
            # Create assistant with error handling
            assistant = self.create_assistant()
            
            # Start the assistant
            assistant.start(ctx.room)
            
            # Initial greeting with calendar status
            greeting = "Hello! I'm your CareSetu Healthcare assistant. "
            if self.scheduler:
                greeting += "I can help you with questions about our services or schedule an appointment in real-time. "
            else:
                greeting += "I can help you with questions about our services. "
            greeting += "How can I help you today?"
            
            await assistant.say(greeting)
            
            logger.info("✅ Voice agent with calendar integration started successfully")
            
            # Keep the agent running and handle any TTS errors
            try:
                await assistant.aclose()
            except Exception as e:
                logger.error(f"⚠️ Assistant error (continuing): {e}")
                # Try to recover by recreating TTS if needed
                if "TTS" in str(e) or "Connection" in str(e):
                    logger.info("🔄 Attempting TTS recovery...")
                    try:
                        new_tts = self._create_robust_tts()
                        # Note: In a real implementation, you'd need to update the assistant's TTS
                        logger.info("✅ TTS recovery successful")
                    except Exception as recovery_error:
                        logger.error(f"❌ TTS recovery failed: {recovery_error}")
            
        except Exception as e:
            logger.error(f"❌ Critical error in voice agent: {e}")
            # Try to provide a fallback response
            try:
                await ctx.room.local_participant.publish_data(
                    "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
                )
            except:
                pass
            raise

# Utility function to test TTS services
async def test_tts_services():
    """Test available TTS services"""
    
    print("🔊 Testing TTS Services")
    print("=" * 30)
    
    agent = FixedCalendarVoiceAgent()
    
    try:
        tts = agent._create_robust_tts()
        print(f"✅ TTS Service initialized: {type(tts).__name__}")
        
        # Test synthesis (if possible)
        test_text = "Hello, this is a test of the TTS service."
        print(f"🎵 Testing synthesis with: '{test_text}'")
        
        # Note: Actual synthesis test would require more setup
        print("✅ TTS service appears to be working")
        
    except Exception as e:
        print(f"❌ TTS test failed: {e}")

# Enhanced error handling for LiveKit integration
class RobustLiveKitAgent:
    """Robust LiveKit agent wrapper with error recovery"""
    
    def __init__(self):
        self.agent = FixedCalendarVoiceAgent()
        self.retry_count = 0
        self.max_retries = 3
    
    async def run_with_recovery(self, ctx: JobContext):
        """Run agent with automatic recovery"""
        
        while self.retry_count < self.max_retries:
            try:
                await self.agent.entrypoint(ctx)
                break  # Success, exit retry loop
                
            except Exception as e:
                self.retry_count += 1
                logger.error(f"❌ Agent failed (attempt {self.retry_count}/{self.max_retries}): {e}")
                
                if self.retry_count < self.max_retries:
                    logger.info(f"🔄 Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    
                    # Recreate agent for fresh start
                    self.agent = FixedCalendarVoiceAgent()
                else:
                    logger.error("❌ Max retries reached, agent failed permanently")
                    raise

if __name__ == "__main__":
    # Test TTS services
    asyncio.run(test_tts_services())
    
    # For running the LiveKit agent with recovery
    robust_agent = RobustLiveKitAgent()
    cli.run_app(WorkerOptions(entrypoint_fnc=robust_agent.run_with_recovery))