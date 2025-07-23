"""
Enhanced Voice Agent with Calendar Integration
Example of how to integrate calendar scheduling with existing agent
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import google, assemblyai, cartesia

from appointment_scheduler import AppointmentScheduler

logger = logging.getLogger("voice-agent-calendar")

class CalendarEnabledVoiceAgent:
    """
    Voice agent with calendar scheduling capabilities
    """
    
    def __init__(self):
        """Initialize the calendar-enabled voice agent"""
        self.scheduler = None
        self.customer_info = {}
        
    async def initialize_calendar(self):
        """Initialize calendar integration"""
        try:
            self.scheduler = AppointmentScheduler()
            logger.info("Calendar integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize calendar: {e}")
            self.scheduler = None
    
    def create_assistant(self) -> VoiceAssistant:
        """Create voice assistant with calendar functions"""
        
        # Base system prompt with calendar capabilities
        system_prompt = """
        You are a helpful customer service agent for CareSetu Healthcare.
        
        You can help customers with:
        1. General questions about our services
        2. Scheduling appointments
        3. Checking appointment availability
        4. Modifying or cancelling appointments
        
        CALENDAR CAPABILITIES:
        - You have access to real-time calendar functions
        - You can check availability and book appointments immediately
        - Google Calendar will automatically send confirmation emails
        - Always confirm customer details before booking
        
        CONVERSATION STYLE:
        - Be friendly and professional
        - Ask for customer name and email before booking
        - Confirm appointment details before finalizing
        - Provide clear next steps after booking
        
        When handling appointments:
        1. First check availability for requested date/time
        2. Get customer name and email
        3. Book the appointment
        4. Confirm the booking details
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
        
        # Create voice assistant
        assistant = VoiceAssistant(
            vad=assemblyai.VAD(),
            stt=assemblyai.STT(),
            llm=model,
            tts=cartesia.TTS(),
            chat_ctx=llm.ChatContext(
                messages=[
                    llm.ChatMessage(
                        role="system",
                        content=system_prompt
                    )
                ]
            ),
            fnc_ctx=llm.FunctionContext() if not function_contexts else llm.FunctionContext(*function_contexts),
        )
        
        # Add function call handler
        if self.scheduler:
            assistant.llm.on("function_calls_finished", self._handle_function_calls)
        
        return assistant
    
    async def _handle_function_calls(self, called_functions):
        """Handle function calls from the LLM"""
        if not self.scheduler:
            return
        
        for func_call in called_functions:
            function_name = func_call.function_info.name
            arguments = func_call.arguments
            
            try:
                # Execute calendar function
                result = await self.scheduler.execute_calendar_function(
                    function_name, **arguments
                )
                
                # Set the result
                func_call.result = result
                
                logger.info(f"Executed {function_name}: {result}")
                
            except Exception as e:
                error_msg = f"Error executing {function_name}: {str(e)}"
                func_call.result = error_msg
                logger.error(error_msg)
    
    async def entrypoint(self, ctx: JobContext):
        """Main entrypoint for the voice agent"""
        
        # Initialize calendar integration
        await self.initialize_calendar()
        
        # Create assistant
        assistant = self.create_assistant()
        
        # Start the assistant
        assistant.start(ctx.room)
        
        # Handle conversation
        await assistant.say("Hello! I'm your CareSetu Healthcare assistant. I can help you with questions about our services or schedule an appointment. How can I help you today?")
        
        logger.info("Voice agent with calendar integration started")

# Example of how to integrate with existing agent
class EnhancedCustomerAgent:
    """
    Enhanced version of existing customer agent with calendar
    """
    
    def __init__(self):
        self.scheduler = None
        self.knowledge_base = None  # Your existing knowledge base
        self.crm = None  # Your existing CRM integration
    
    async def initialize(self):
        """Initialize all components"""
        # Initialize calendar
        try:
            self.scheduler = AppointmentScheduler()
            logger.info("Calendar scheduler initialized")
        except Exception as e:
            logger.warning(f"Calendar not available: {e}")
        
        # Initialize your existing components
        # self.knowledge_base = YourKnowledgeBase()
        # self.crm = YourCRMIntegration()
    
    async def handle_customer_request(self, message: str, customer_info: Dict[str, Any] = None) -> str:
        """
        Handle customer requests with calendar integration
        
        Args:
            message: Customer message
            customer_info: Customer information from CRM
            
        Returns:
            Response message
        """
        
        # Check if this is a scheduling request
        if self.scheduler and self.scheduler.detect_scheduling_intent(message):
            return await self.scheduler.handle_scheduling_request(message, customer_info)
        
        # Handle other requests with existing systems
        # if self.knowledge_base:
        #     return await self.knowledge_base.get_response(message)
        
        return "I can help you with general questions or schedule an appointment. What would you like to do?"
    
    async def quick_appointment_booking(self, 
                                      customer_name: str,
                                      customer_email: str,
                                      preferred_date: str,
                                      preferred_time: str) -> str:
        """Quick booking interface for voice agent"""
        if not self.scheduler:
            return "Sorry, appointment booking is not available right now."
        
        return await self.scheduler.quick_book_appointment(
            customer_name, customer_email, preferred_date, preferred_time
        )

# Example usage and testing
async def test_enhanced_agent():
    """Test the enhanced agent with calendar"""
    
    print("🤖 Testing Enhanced Agent with Calendar")
    print("=" * 45)
    
    agent = EnhancedCustomerAgent()
    await agent.initialize()
    
    # Test scheduling detection
    test_messages = [
        "I need to book an appointment",
        "What are your hours?",
        "Can I schedule something for tomorrow?",
        "Tell me about your services"
    ]
    
    for message in test_messages:
        response = await agent.handle_customer_request(message)
        print(f"Customer: {message}")
        print(f"Agent: {response}\n")

if __name__ == "__main__":
    # For testing the enhanced agent
    asyncio.run(test_enhanced_agent())
    
    # For running the LiveKit agent
    # cli.run_app(WorkerOptions(entrypoint_fnc=CalendarEnabledVoiceAgent().entrypoint))