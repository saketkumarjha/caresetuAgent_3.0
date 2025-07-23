"""Main Voice Agent using LiveKit Agents framework - Working Version with Appointments."""

import asyncio
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm, AgentSession, Agent
from livekit.plugins import assemblyai, google, elevenlabs, cartesia, silero
from livekit import rtc
from config import config
from stt_config import create_assemblyai_stt
from simple_rag_engine import SimpleRAGEngine
from unified_knowledge_base import UnifiedKnowledgeBase
from conversation_learning import ConversationLearningEngine, LearningType, ConfidenceLevel
from google_calendar_integration import GoogleCalendarIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BusinessVoiceAgent(Agent):
    """Main business voice agent with STT → LLM → TTS pipeline enhanced with RAG and appointment booking."""
    
    def __init__(self):
        """Initialize the voice agent with all components including RAG and calendar."""
        if not config:
            raise ValueError("Configuration not loaded. Please check your .env file.")
        
        # Initialize STT with business optimizations
        stt = create_assemblyai_stt()
        logger.info("✅ AssemblyAI STT initialized with business word boost")
        
        # Initialize LLM (Google Gemini) with business context
        llm_instance = google.LLM(
            model="gemini-1.5-flash",
            api_key=config.google.api_key,
            temperature=0.7,  # Balanced creativity for business conversations
        )
        logger.info("✅ Google Gemini LLM initialized")
        
        # Initialize TTS (Cartesia preferred, ElevenLabs or Google Cloud TTS fallback)
        tts = self._create_tts()
        logger.info("✅ TTS service initialized")
        
        # Initialize RAG components
        self._initialize_rag_components()
        
        # Initialize calendar integration
        self._initialize_calendar()
        
        # Initialize conversation context manager (simplified)
        self.context_manager = None  # Simplified for now
        logger.info("✅ Conversation context manager initialized (simplified)")
        
        # Initialize conversation learning engine
        self.learning_engine = ConversationLearningEngine()
        logger.info("✅ Conversation learning engine initialized")
        
        # Create business context for the LLM
        business_context = self._create_business_context()
        
        # Initialize the Agent base class with required parameters
        super().__init__(
            instructions="""You are a professional careSetu healthcare voice assistant enhanced with comprehensive knowledge retrieval and real-time appointment booking capabilities.

PERSONALITY & TONE:
- Professional, friendly, and helpful
- Patient and understanding with customers
- Clear and concise communication
- Warm but not overly casual

CORE CAPABILITIES:
1. HEALTHCARE GUIDANCE: Answer health-related questions using company documents
2. APP SUPPORT: Help with careSetu app navigation
3. REAL-TIME APPOINTMENT BOOKING: Check availability and book appointments instantly
4. APPOINTMENT MANAGEMENT: Cancel, reschedule, and modify existing appointments
5. GENERAL SUPPORT: Handle customer service inquiries with policy references

APPOINTMENT SCHEDULING FEATURES:
- Check real-time availability for any date
- Book appointments immediately during conversation
- Google Calendar automatically sends confirmation emails and reminders
- Handle appointment modifications and cancellations
- Provide business hours and scheduling information

RAG-ENHANCED RESPONSES:
- Use retrieved document content to provide accurate, up-to-date information
- Cite sources when providing information from company documents
- Combine retrieved knowledge with conversational context
- Maintain conversation flow while incorporating document-based answers

CARESETU KNOWLEDGE:
- Comprehensive healthcare platform with online consultations
- Mobile app available on Play Store and App Store
- Services: consultations, lab tests, medicine delivery, home healthcare
- Support: saket@jha.com
- Business hours: 9 AM - 6 PM, Monday-Friday
- Emergency support available 24/7

APPOINTMENT BOOKING PROCESS:
1. When user requests appointment, check their preferred date/time
2. Use calendar integration to verify availability
3. Get customer name and email address
4. Book the appointment in Google Calendar
5. Confirm booking details and next steps
6. Google Calendar will send automatic confirmation and reminders

Remember: You're representing careSetu with full appointment booking capabilities. Be efficient and helpful while maintaining professionalism.""",
            chat_ctx=business_context,
            stt=stt,
            llm=llm_instance,
            tts=tts,
            vad=silero.VAD.load(
                min_speech_duration=0.1,  # Faster detection
                min_silence_duration=0.5   # Shorter silence before stopping
            ),
            allow_interruptions=True
        )
        
        # Store components for later use
        self.business_context = business_context
        self.current_session_id = None
        
        logger.info("✅ BusinessVoiceAgent with RAG and appointment booking capabilities initialized successfully")
    
    def _initialize_rag_components(self):
        """Initialize RAG engine and knowledge base components."""
        try:
            # Initialize unified knowledge base
            self.knowledge_base = UnifiedKnowledgeBase(
                json_kb_path="knowledge_base",
                pdf_content_path="unified_knowledge_base"
            )
            logger.info("✅ Unified knowledge base initialized")
            
            # Initialize RAG engine
            self.rag_engine = SimpleRAGEngine(self.knowledge_base)
            logger.info("✅ RAG engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG components: {e}")
            # Set fallback None values
            self.knowledge_base = None
            self.rag_engine = None
    
    def _initialize_calendar(self):
        """Initialize Google Calendar integration for appointment scheduling."""
        try:
            self.calendar = GoogleCalendarIntegration()
            logger.info("✅ Google Calendar integration initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize calendar integration: {e}")
            self.calendar = None
    
    def _create_tts(self):
        """Create TTS service with Silero as primary (most reliable) and proper fallbacks."""
        # Start with Silero TTS as primary (free, local, no connection issues)
        try:
            logger.info("🔊 Initializing Silero TTS (primary - reliable and local)")
            return silero.TTS()
        except Exception as e:
            logger.warning(f"Silero TTS failed, trying Google TTS: {e}")
        
        # Fallback to Google TTS as it's reliable and free
        try:
            logger.info("🔊 Initializing Google TTS (fallback - reliable)")
            return google.TTS(
                voice="en-US-Neural2-F",  # Professional female voice
                speed=1.0,
                pitch=0.0,
            )
        except Exception as e:
            logger.warning(f"Google TTS failed, trying Cartesia: {e}")
        
        # Try Cartesia as secondary (it's having connection issues)
        if hasattr(config, 'cartesia') and config.cartesia.api_key and config.cartesia.api_key.startswith("sk_car_"):
            try:
                logger.info("🔊 Initializing Cartesia TTS (secondary - fast and high quality)")
                return cartesia.TTS(
                    api_key=config.cartesia.api_key,
                    model="sonic-turbo",
                    voice="bf0a246a-8642-498a-9950-80c35e9276b5",
                    language="en",
                )
            except Exception as e:
                logger.warning(f"Cartesia TTS failed, trying ElevenLabs: {e}")
        
        # Try ElevenLabs as tertiary fallback if API key is available and valid
        if (hasattr(config, 'elevenlabs') and config.elevenlabs.api_key and 
            config.elevenlabs.api_key != "ELEVENLABS_API_KEY" and
            len(config.elevenlabs.api_key) > 10):
            try:
                logger.info("🔊 Initializing ElevenLabs TTS (tertiary fallback)")
                return elevenlabs.TTS(
                    api_key=config.elevenlabs.api_key,
                    voice="21m00Tcm4TlvDq8ikWAM",
                    model="eleven_turbo_v2",
                    stability=0.5,
                    similarity_boost=0.8,
                    style=0.2,
                )
            except Exception as e:
                logger.warning(f"ElevenLabs TTS failed: {e}")
        
        # Final fallback to basic Google TTS
        logger.info("🔊 Using basic Google TTS (final fallback)")
        try:
            return google.TTS(voice="en-US-Standard-A")
        except Exception as e:
            logger.error(f"All TTS services failed: {e}")
            # Last resort - basic Silero
            return silero.TTS(model="v3_en")
    
    def _create_business_context(self) -> llm.ChatContext:
        """Create chat context with business-specific instructions."""
        system_prompt = """You are a professional careSetu healthcare voice assistant with real-time appointment scheduling capabilities.

PERSONALITY & TONE:
- Professional, friendly, and helpful
- Patient and understanding with customers
- Clear and concise communication
- Warm but not overly casual

CORE CAPABILITIES:
1. HEALTHCARE GUIDANCE: Answer health-related questions using company documents
2. APP SUPPORT: Help with careSetu app navigation
3. REAL-TIME APPOINTMENT BOOKING: Check availability and book appointments instantly
4. APPOINTMENT MANAGEMENT: Cancel, reschedule, and modify existing appointments
5. GENERAL SUPPORT: Handle customer service inquiries with policy references

APPOINTMENT SCHEDULING FEATURES:
- Check real-time availability for any date
- Book appointments immediately during conversation
- Google Calendar automatically sends confirmation emails and reminders
- Handle appointment modifications and cancellations
- Provide business hours and scheduling information

CONVERSATION GUIDELINES:
- Always greet customers professionally
- Listen carefully and ask clarifying questions
- For appointments: get name, email, preferred date/time
- Confirm appointment details before booking
- Provide clear, actionable responses
- Offer alternatives when first option isn't available
- Escalate complex issues to human agents
- End conversations politely with next steps

CARESETU KNOWLEDGE:
- Comprehensive healthcare platform with online consultations
- Mobile app available on Play Store and App Store
- Services: consultations, lab tests, medicine delivery, home healthcare
- Support: saket@jha.com
- Business hours: 9 AM - 6 PM, Monday-Friday
- Emergency support available 24/7

APPOINTMENT BOOKING PROCESS:
1. When user requests appointment, check their preferred date/time
2. Use calendar integration to verify availability
3. Get customer name and email address
4. Book the appointment in Google Calendar
5. Confirm booking details and next steps
6. Google Calendar will send automatic confirmation and reminders

RESPONSE FORMAT:
- Keep responses conversational but professional
- Use natural speech patterns (contractions, pauses)
- Avoid technical jargon unless necessary
- Ask one question at a time
- Provide specific next steps

Remember: You're representing careSetu with full appointment booking capabilities. Be efficient and helpful while maintaining professionalism."""
        
        chat_ctx = llm.ChatContext()
        # Add system message using keyword arguments
        chat_ctx.add_message(
            role="system",
            content=system_prompt
        )
        return chat_ctx
    
    # Calendar Integration Methods
    def detect_calendar_intent(self, user_message: str) -> bool:
        """Detect if user wants to schedule something
        
        Args:
            user_message: User's message
            
        Returns:
            True if calendar/scheduling intent detected
        """
        message_lower = user_message.lower()
        calendar_keywords = [
            'appointment', 'schedule', 'book', 'booking', 'available',
            'availability', 'time', 'date', 'cancel', 'reschedule',
            'modify', 'change', 'when', 'free', 'slots'
        ]
        return any(keyword in message_lower for keyword in calendar_keywords)
    
    async def handle_calendar_request(self, user_message: str, session_id: str = None) -> str:
        """Handle calendar-related requests
        
        Args:
            user_message: User's message
            session_id: Session identifier
            
        Returns:
            Response message
        """
        if not self.calendar:
            return ("I apologize, but appointment scheduling is currently unavailable. "
                   "Please try again later or contact us directly at saket@jha.com")
        
        message_lower = user_message.lower()
        
        try:
            # Check availability request
            if any(word in message_lower for word in ['available', 'availability', 'free', 'open', 'slots']):
                return await self._handle_availability_check(user_message)
            
            # Book appointment request
            elif any(word in message_lower for word in ['book', 'schedule', 'appointment', 'make']):
                return await self._handle_booking_request(user_message, session_id)
            
            # Cancel appointment
            elif any(word in message_lower for word in ['cancel', 'delete']):
                return await self._handle_cancellation_request(user_message)
            
            # Reschedule appointment
            elif any(word in message_lower for word in ['reschedule', 'change', 'move']):
                return await self._handle_reschedule_request(user_message)
            
            # General scheduling help
            else:
                return self._get_scheduling_help()
                
        except Exception as e:
            logger.error(f"Error handling calendar request: {e}")
            return ("I encountered an issue with the scheduling system. "
                   "Please try again or contact our support team.")
    
    async def _handle_availability_check(self, user_message: str) -> str:
        """Handle availability checking requests."""
        try:
            # Extract date from message (simplified - in production use NLP)
            today = datetime.now().date()
            check_date = today.strftime('%Y-%m-%d')
            
            # Check for common date references
            message_lower = user_message.lower()
            if 'tomorrow' in message_lower:
                check_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'next week' in message_lower:
                check_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
            elif 'monday' in message_lower:
                days_ahead = (0 - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            elif 'tuesday' in message_lower:
                days_ahead = (1 - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            elif 'wednesday' in message_lower:
                days_ahead = (2 - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            elif 'thursday' in message_lower:
                days_ahead = (3 - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            elif 'friday' in message_lower:
                days_ahead = (4 - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                check_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            # Check availability
            slots = self.calendar.check_availability(check_date)
            if not slots:
                return f"I don't have any available appointment slots for {check_date}. Would you like me to check a different date?"
            
            # Format available slots
            date_obj = datetime.strptime(check_date, '%Y-%m-%d')
            day_name = date_obj.strftime('%A, %B %d')
            slots_text = []
            for i, slot in enumerate(slots[:5], 1):  # Show first 5 slots
                slots_text.append(f"{slot['start_time']}")
            
            return (f"I have the following appointment times available for {day_name}:\n\n"
                   f"{', '.join(slots_text)}\n\n"
                   f"Which time works best for you? I can book it right away once you provide your name and email.")
                   
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return "I'm having trouble checking availability right now. Please try again or contact our support team."
    
    async def _handle_booking_request(self, user_message: str, session_id: str = None) -> str:
        """Handle appointment booking requests."""
        try:
            # This is a simplified booking flow - in production you'd use NLP to extract details
            return ("I'd be happy to help you book an appointment! To get started, I'll need:\n\n"
                   "1. Your full name\n"
                   "2. Your email address\n"
                   "3. Your preferred date and time\n\n"
                   "What date and time would work best for you? I can check availability and book it immediately.")
        except Exception as e:
            logger.error(f"Error handling booking request: {e}")
            return "I'm having trouble with the booking system right now. Please try again or contact our support team."
    
    async def _handle_cancellation_request(self, user_message: str) -> str:
        """Handle appointment cancellation requests."""
        try:
            return ("I can help you cancel your appointment. To find your booking, I'll need either:\n\n"
                   "• Your email address, or\n"
                   "• The appointment date and time\n\n"
                   "Could you please provide one of these details?")
        except Exception as e:
            logger.error(f"Error handling cancellation request: {e}")
            return "I'm having trouble accessing the cancellation system right now. Please try again or contact our support team."
    
    async def _handle_reschedule_request(self, user_message: str) -> str:
        """Handle appointment rescheduling requests."""
        try:
            return ("I can help you reschedule your appointment. First, let me find your existing booking.\n\n"
                   "Please provide either:\n"
                   "• Your email address, or\n"
                   "• Your current appointment date and time\n\n"
                   "Then I'll show you available times to reschedule to.")
        except Exception as e:
            logger.error(f"Error handling reschedule request: {e}")
            return "I'm having trouble with the rescheduling system right now. Please try again or contact our support team."
    
    def _get_scheduling_help(self) -> str:
        """Get general scheduling help message."""
        return ("I can help you with appointments at CareSetu Healthcare! Here's what I can do:\n\n"
               "• **Check availability** - \"What times are available tomorrow?\"\n"
               "• **Book appointments** - \"I'd like to schedule an appointment\"\n"
               "• **Cancel appointments** - \"I need to cancel my appointment\"\n"
               "• **Reschedule appointments** - \"Can I reschedule my appointment?\"\n\n"
               "Our business hours are Monday to Friday, 9 AM to 6 PM.\n\n"
               "What would you like to do?")
    
    async def quick_book_appointment(self, customer_name: str,
                                   customer_email: str,
                                   preferred_date: str,
                                   preferred_time: str,
                                   appointment_type: str = 'consultation') -> str:
        """Quick booking interface for voice agent
        
        Args:
            customer_name: Customer's name
            customer_email: Customer's email
            preferred_date: Date in YYYY-MM-DD format
            preferred_time: Time in HH:MM format
            appointment_type: Type of appointment
            
        Returns:
            Booking result message
        """
        if not self.calendar:
            return "Sorry, appointment booking is not available right now."
        
        try:
            # Combine date and time
            datetime_str = f"{preferred_date}T{preferred_time}:00"
            
            # Try to book the appointment
            result = self.calendar.book_appointment(
                customer_name=customer_name,
                customer_email=customer_email,
                start_datetime=datetime_str,
                appointment_type=appointment_type,
                description=f"Appointment booked via CareSetu voice agent for {customer_name}"
            )
            
            if result['success']:
                return (f"✅ Perfect! I've booked your {appointment_type} appointment for "
                       f"{result['start_time']} on {preferred_date}.\n\n"
                       f"📧 Google Calendar will automatically send you:\n"
                       f"• A calendar invitation to {customer_email}\n"
                       f"• Email reminders 24 hours and 1 hour before your appointment\n\n"
                       f"Your appointment ID is: {result['event_id']}\n\n"
                       f"Is there anything else I can help you with?")
            else:
                return f"I'm sorry, I couldn't book that appointment: {result['message']}. Would you like to try a different time?"
                
        except Exception as e:
            logger.error(f"Error in quick booking: {e}")
            return f"I encountered an error while booking your appointment: {str(e)}. Please try again or contact our support team."    

    async def _generate_rag_enhanced_response(self, user_query: str, session_id: str = None) -> Optional[str]:
        """Generate response enhanced with RAG retrieval, conversation context, and calendar integration."""
        try:
            # Check for calendar intent first - handle immediately for real-time scheduling
            if self.detect_calendar_intent(user_query):
                logger.info("🗓️ Calendar intent detected, handling scheduling request")
                calendar_response = await self.handle_calendar_request(user_query, session_id)
                if calendar_response:
                    return calendar_response
            
            if not self.rag_engine:
                logger.warning("RAG engine not available, using fallback response")
                return None
            
            # Use session_id or create a default one
            if not session_id:
                session_id = self.current_session_id or "default_session"
            
            # Get comprehensive conversation context for RAG
            context_summary = ""
            conversation_context = None
            if self.context_manager:
                try:
                    # Get conversation context for contextual filtering
                    conversation_context = await self.context_manager.get_or_create_context(session_id)
                    context_summary = await self.context_manager.get_conversation_summary(session_id, last_n_turns=5)
                    
                    # Set knowledge context if available
                    if conversation_context.relevant_documents:
                        await self.context_manager.set_knowledge_context(
                            session_id,
                            f"Previously accessed documents: {', '.join(conversation_context.relevant_documents[-5:])}",
                            conversation_context.relevant_documents
                        )
                except Exception as e:
                    logger.warning(f"Could not get conversation context: {e}")
                    context_summary = ""
            
            # Perform RAG search and generation with enhanced context
            rag_response = await self.rag_engine.search_and_generate(
                query=user_query,
                context=context_summary,
                session_id=session_id  # Pass session_id for contextual filtering
            )
            
            if rag_response and rag_response.answer:
                # Log RAG usage with enhanced details
                logger.info(f"🔍 RAG retrieved {len(rag_response.retrieved_content)} results with confidence {rag_response.confidence:.2f}")
                logger.info(f"📚 Sources used: {[result.source_file for result in rag_response.retrieved_content[:3]]}")
                
                # Log domain expertise information if available
                if hasattr(rag_response, 'domain_expertise') and rag_response.domain_expertise:
                    domain_info = rag_response.domain_expertise
                    logger.info(f"🎯 Domain expertise applied: {domain_info['detected_domain']} "
                               f"(terminology: {domain_info.get('terminology_used', [])})")
                
                # Extract sources and document types for context tracking
                sources_used = [result.source_file for result in rag_response.retrieved_content]
                document_types = [result.document_type for result in rag_response.retrieved_content]
                
                # Detect intent from query and response (enhanced with domain info)
                detected_intent = self._detect_query_intent(user_query, rag_response.retrieved_content, rag_response)
                
                # Add conversation turn to context manager with enhanced metadata
                if self.context_manager:
                    try:
                        await self.context_manager.add_conversation_turn(
                            session_id=session_id,
                            user_message=user_query,
                            agent_response=rag_response.answer,
                            intent=detected_intent,
                            confidence=rag_response.confidence,
                            sources_used=sources_used
                        )
                        
                        # Update context with current topic based on document types
                        current_topic = self._determine_topic_from_documents(document_types, detected_intent)
                        if current_topic:
                            await self.context_manager.update_context_data(
                                session_id,
                                current_topic=current_topic
                            )
                    except Exception as e:
                        logger.warning(f"Could not update conversation context: {e}")
                
                # Enhance response with conversation coherence
                enhanced_response = self._ensure_conversation_coherence(
                    rag_response.answer, user_query, conversation_context,
                    rag_response.retrieved_content
                )
                
                return enhanced_response
                
        except Exception as e:
            logger.error(f"Error in RAG response generation: {e}")
            return None
    
    def _detect_query_intent(self, query: str, retrieved_content: List, rag_response=None) -> str:
        """Detect intent from query, retrieved content, and domain expertise."""
        query_lower = query.lower()
        
        # Enhanced intent patterns with domain-specific keywords
        intent_patterns = {
            'booking': ['book', 'schedule', 'appointment', 'make', 'create', 'set up', 'arrange'],
            'cancellation': ['cancel', 'remove', 'delete', 'reschedule', 'change'],
            'information': ['what', 'tell me', 'information', 'details', 'about', 'explain'],
            'procedure': ['how', 'steps', 'process', 'procedure', 'method', 'guide'],
            'policy': ['policy', 'rule', 'guideline', 'allowed', 'permitted', 'can i'],
            'contact': ['contact', 'phone', 'email', 'reach', 'call', 'support'],
            'hours': ['hours', 'time', 'open', 'available', 'schedule', 'when'],
            'cost': ['cost', 'price', 'fee', 'charge', 'payment', 'billing', 'how much'],
            'technical': ['error', 'problem', 'issue', 'not working', 'broken', 'fix'],
            'healthcare': ['health', 'medical', 'doctor', 'consultation', 'symptoms', 'treatment']
        }
        
        # Check domain expertise for enhanced intent detection
        detected_domain = None
        if rag_response and hasattr(rag_response, 'domain_expertise') and rag_response.domain_expertise:
            detected_domain = rag_response.domain_expertise.get('detected_domain')
        
        # Map domain to likely intents
        domain_intent_mapping = {
            'healthcare': 'healthcare',
            'legal': 'policy',
            'technical_support': 'technical',
            'billing': 'cost',
            'appointment': 'booking',
            'general': 'information'
        }
        
        # If domain suggests a specific intent, prioritize it
        if detected_domain in domain_intent_mapping:
            domain_suggested_intent = domain_intent_mapping[detected_domain]
            # Check if query matches the domain-suggested intent
            if any(keyword in query_lower for keyword in intent_patterns.get(domain_suggested_intent, [])):
                logger.info(f"🎯 Domain-enhanced intent detection: {domain_suggested_intent} (from {detected_domain} domain)")
                return domain_suggested_intent
        
        # Check query patterns
        for intent, keywords in intent_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        
        # Check document types from retrieved content
        if retrieved_content:
            doc_types = [result.document_type for result in retrieved_content]
            if 'procedure' in doc_types:
                return 'procedure'
            elif 'policy' in doc_types:
                return 'policy'
            elif 'faq' in doc_types:
                return 'information'
        
        # Fallback to domain-based intent if available
        if detected_domain:
            domain_fallback_mapping = {
                'healthcare': 'healthcare',
                'legal': 'policy',
                'technical_support': 'technical',
                'billing': 'cost',
                'appointment': 'booking'
            }
            if detected_domain in domain_fallback_mapping:
                return domain_fallback_mapping[detected_domain]
        
        return 'general'
    
    def _determine_topic_from_documents(self, document_types: List[str], intent: str) -> Optional[str]:
        """Determine current conversation topic from document types and intent."""
        if not document_types:
            return None
        
        # Map document types and intents to topics
        topic_mapping = {
            ('procedure', 'booking'): 'appointment_booking',
            ('procedure', 'cancellation'): 'appointment_management',
            ('policy', 'cancellation'): 'cancellation_policy',
            ('faq', 'information'): 'general_information',
            ('manual', 'technical'): 'technical_support',
            ('procedure', 'healthcare'): 'healthcare_guidance',
            ('policy', 'cost'): 'billing_policy'
        }
        
        # Find matching topic
        for doc_type in document_types:
            key = (doc_type, intent)
            if key in topic_mapping:
                return topic_mapping[key]
        
        # Fallback to document type
        if 'procedure' in document_types:
            return 'procedure_guidance'
        elif 'policy' in document_types:
            return 'policy_information'
        elif 'faq' in document_types:
            return 'general_support'
        
        return None
    
    def _ensure_conversation_coherence(self, rag_answer: str, user_query: str, conversation_context, retrieved_content: List) -> str:
        """Ensure RAG response maintains conversation coherence."""
        if not conversation_context or not conversation_context.turns:
            return rag_answer
        
        # Check if this is a follow-up question
        is_follow_up = self._is_follow_up_question(user_query, conversation_context)
        
        if is_follow_up:
            # Add contextual references for follow-up questions
            recent_topic = conversation_context.current_topic
            if recent_topic:
                coherence_prefix = self._get_coherence_prefix(recent_topic, user_query)
                if coherence_prefix:
                    return f"{coherence_prefix} {rag_answer}"
        
        # Check for topic transitions
        if conversation_context.current_topic:
            current_doc_types = [result.document_type for result in retrieved_content]
            if self._is_topic_transition(conversation_context.current_topic, current_doc_types):
                transition_phrase = "Let me help you with that. "
                return f"{transition_phrase}{rag_answer}"
        
        return rag_answer
    
    def _is_follow_up_question(self, query: str, conversation_context) -> bool:
        """Check if the query is a follow-up to previous conversation."""
        query_lower = query.lower()
        
        # Follow-up indicators
        follow_up_patterns = [
            'what about', 'how about', 'and', 'also', 'additionally',
            'can you', 'could you', 'please tell me', 'more', 'other',
            'it', 'that', 'this', 'they', 'them'
        ]
        
        return any(pattern in query_lower for pattern in follow_up_patterns)
    
    def _is_topic_transition(self, current_topic: str, new_doc_types: List[str]) -> bool:
        """Check if there's a topic transition in the conversation."""
        if not current_topic or not new_doc_types:
            return False
        
        # Define topic-document type relationships
        topic_doc_mapping = {
            'appointment_booking': ['procedure'],
            'appointment_management': ['procedure', 'policy'],
            'general_information': ['faq'],
            'technical_support': ['manual', 'procedure'],
            'healthcare_guidance': ['procedure', 'faq'],
            'billing_policy': ['policy']
        }
        
        expected_doc_types = topic_doc_mapping.get(current_topic, [])
        return not any(doc_type in expected_doc_types for doc_type in new_doc_types)
    
    def _get_coherence_prefix(self, topic: str, query: str) -> Optional[str]:
        """Get appropriate prefix for conversation coherence."""
        coherence_prefixes = {
            'appointment_booking': "Regarding your appointment booking,",
            'appointment_management': "For your appointment,",
            'general_information': "To add to that information,",
            'technical_support': "Continuing with the technical issue,",
            'healthcare_guidance': "For your healthcare question,",
            'billing_policy': "Regarding the billing policy,"
        }
        
        return coherence_prefixes.get(topic)
    
    async def _on_user_speech(self, event):
        """Handle user speech events."""
        try:
            # Extract user text from event - handle different event structures
            user_text = ""
            if hasattr(event, 'alternatives') and event.alternatives:
                user_text = event.alternatives[0].text
            elif hasattr(event, 'text'):
                user_text = event.text
            elif hasattr(event, 'content'):
                user_text = event.content
            else:
                user_text = str(event)
            
            logger.info(f"👤 User said: {user_text}")
            
            if user_text:
                # Extract context from the conversation
                context = {
                    "user_text": user_text,
                    "timestamp": getattr(event, 'timestamp', None),
                    "room_name": "voice_agent_room"
                }
                
                # Process the user input (can be extended with intent routing)
                logger.info(f"Processing user input: {user_text}")
                
        except Exception as e:
            logger.error(f"Error processing user speech: {e}")
    
    async def _on_agent_speech(self, event):
        """Handle agent speech events."""
        try:
            # Extract agent text from event - handle different event structures
            agent_text = ""
            if hasattr(event, 'alternatives') and event.alternatives:
                agent_text = event.alternatives[0].text
            elif hasattr(event, 'text'):
                agent_text = event.text
            elif hasattr(event, 'content'):
                agent_text = event.content
            else:
                agent_text = str(event)
            
            logger.info(f"🤖 Agent said: {agent_text}")
            
        except Exception as e:
            logger.error(f"Error processing agent speech: {e}")
    
    async def _on_function_calls_finished(self, event):
        """Handle completion of function calls (future integration actions)."""
        logger.info("🔧 Function calls completed")


class RAGEnhancedSession:
    """Wrapper for AgentSession that integrates RAG capabilities."""
    
    def __init__(self, session: AgentSession, agent: BusinessVoiceAgent):
        """Initialize RAG-enhanced session wrapper."""
        self.session = session
        self.agent = agent
        self.original_generate_reply = session.generate_reply
        
        # Track API usage for rate limiting
        self.google_api_calls = 0
        self.max_google_calls = 10  # Google API limit
        self.fallback_mode = False
        
        # Override the generate_reply method to include RAG
        session.generate_reply = self._rag_enhanced_generate_reply
        
        logger.info("✅ RAG-enhanced session wrapper initialized")
    
    async def _rag_enhanced_generate_reply(self, instructions: str = None, **kwargs):
        """Generate reply enhanced with RAG retrieval, conversation context, and learning capabilities."""
        try:
            # Check Google API rate limit
            if self.google_api_calls >= self.max_google_calls:
                logger.warning(f"🚫 Google API limit reached ({self.google_api_calls}/{self.max_google_calls}). Using RAG-only mode.")
                self.fallback_mode = True
            
            # Get the last user message from the chat context
            user_query = self._extract_last_user_message()
            
            if user_query:
                session_id = self.agent.current_session_id or "default_session"
                
                # Check for learning opportunities in user message
                learning_opportunity = self.agent.learning_engine.detect_user_learning_opportunity(
                    user_query, {"session_id": session_id}
                )
                
                # Try to get RAG-enhanced response with conversation context
                rag_response = await self.agent._generate_rag_enhanced_response(user_query, session_id)
                
                # Store the RAG response for domain expertise access
                self.agent.last_rag_response = rag_response
                
                # Search for learned information that might be relevant
                learned_info_results = self.agent.learning_engine.search_learned_information(
                    query=user_query,
                    min_confidence=ConfidenceLevel.MEDIUM
                )
                
                # Combine RAG response with learned information
                combined_response = rag_response
                learned_content_used = []
                
                if learned_info_results:
                    # Check for conflicts between learned info and PDF content
                    pdf_content = rag_response if rag_response else ""
                    relevant_learned_info = []
                    
                    for learned_info in learned_info_results[:3]:  # Top 3 most relevant
                        has_conflict, conflict_details = self.agent.learning_engine.check_pdf_conflict(
                            learned_info, pdf_content
                        )
                        
                        if not has_conflict:
                            relevant_learned_info.append(learned_info)
                            learned_content_used.append(learned_info.id)
                            # Mark as used
                            self.agent.learning_engine.mark_learned_info_used(learned_info.id)
                        else:
                            logger.info(f"Conflict detected with learned info: {conflict_details}")
                    
                    # Integrate learned information into response
                    if relevant_learned_info:
                        learned_content = "\n\nAdditionally, from previous conversations I learned:\n"
                        for learned_info in relevant_learned_info:
                            learned_content += f"- {learned_info.content} (learned from conversation on {learned_info.timestamp.strftime('%Y-%m-%d')})\n"
                        
                        if combined_response:
                            combined_response += learned_content
                        else:
                            combined_response = f"Based on what I've learned from previous conversations:\n{learned_content}"
                
                if combined_response:
                    # If we're in fallback mode (Google API limit reached), return RAG response directly
                    if self.fallback_mode:
                        logger.info("🔄 Using RAG-only response due to API limits")
                        return combined_response
                    
                    # Extract domain expertise information for enhanced instructions
                    domain_guidance = ""
                    if (hasattr(self.agent, 'rag_engine') and self.agent.rag_engine and 
                        hasattr(self.agent.rag_engine, 'last_rag_response') and 
                        hasattr(self.agent.rag_engine.last_rag_response, 'domain_expertise')):
                        
                        domain_info = self.agent.rag_engine.last_rag_response.domain_expertise
                        if domain_info:
                            detected_domain = domain_info.get('detected_domain', 'general')
                            terminology_used = domain_info.get('terminology_used', [])
                            clarifying_questions = domain_info.get('clarifying_questions', [])
                            
                            domain_guidance = f"""DOMAIN EXPERTISE GUIDANCE:
- Detected domain: {detected_domain}
- Use appropriate terminology: {', '.join(terminology_used) if terminology_used else 'standard business language'}
- Consider asking clarifying questions if needed: {'; '.join(clarifying_questions) if clarifying_questions else 'none suggested'}
- Adapt your language and expertise level to match the {detected_domain} domain"""
                    
                    # Enhanced instructions with RAG content and domain guidance
                    enhanced_instructions = f"""{instructions or 'Respond professionally and helpfully to the user.'}

RETRIEVED KNOWLEDGE:
{combined_response}

{domain_guidance}

RESPONSE GUIDELINES:
- Use the retrieved knowledge to provide accurate, detailed responses
- Cite sources when appropriate (mention document names)
- Maintain conversational flow while incorporating the retrieved information
- If the retrieved knowledge doesn't fully answer the question, acknowledge this and offer to help further"""
                    
                    # Increment API call counter
                    self.google_api_calls += 1
                    logger.info(f"📊 Google API calls: {self.google_api_calls}/{self.max_google_calls}")
                    
                    # Call original generate_reply with enhanced instructions
                    try:
                        # Update the chat context with enhanced instructions
                        if hasattr(self.session, 'chat_ctx') and self.session.chat_ctx:
                            self.session.chat_ctx.add_message(role="system", content=enhanced_instructions)
                        
                        return await self.original_generate_reply()
                    except Exception as e:
                        logger.error(f"❌ Google API call failed: {e}")
                        # Switch to fallback mode
                        self.fallback_mode = True
                        logger.warning("🔄 Switching to RAG-only mode due to API error")
                        return combined_response
                
                # If no RAG response available, check if we should use fallback
                elif self.fallback_mode:
                    logger.info("🔄 Using fallback response - no RAG content available")
                    return "I'm here to help you with your healthcare needs. Could you please rephrase your question or ask about our services, appointments, or general information?"
            
            # If no user query or in fallback mode, use original method with rate limiting
            if not self.fallback_mode:
                self.google_api_calls += 1
                logger.info(f"📊 Google API calls: {self.google_api_calls}/{self.max_google_calls}")
                
                try:
                    # Update the chat context with instructions if provided
                    if instructions and hasattr(self.session, 'chat_ctx') and self.session.chat_ctx:
                        self.session.chat_ctx.add_message(role="system", content=instructions)
                    
                    return await self.original_generate_reply()
                except Exception as e:
                    logger.error(f"❌ Google API call failed: {e}")
                    self.fallback_mode = True
                    return "I'm here to help you with your healthcare needs. How can I assist you today?"
            else:
                # Fallback response when API limit reached
                return "I'm here to help you with your healthcare needs. How can I assist you today?"
                
        except Exception as e:
            logger.error(f"❌ Error in RAG-enhanced generate_reply: {e}")
            # Return a safe fallback response
            return "I apologize, but I'm experiencing some technical difficulties. Please let me know how I can help you with your healthcare needs."
    
    def _extract_last_user_message(self) -> Optional[str]:
        """Extract the last user message from the chat context."""
        try:
            if hasattr(self.session, 'chat_ctx') and self.session.chat_ctx:
                messages = self.session.chat_ctx.messages
                
                # Find the last user message
                for message in reversed(messages):
                    if hasattr(message, 'role') and message.role == 'user':
                        return message.content
                    elif hasattr(message, 'content') and isinstance(message.content, str):
                        # Fallback for different message structures
                        return message.content
                
            return None
        except Exception as e:
            logger.error(f"Error extracting user message: {e}")
            return None


def prewarm_process(proc: WorkerOptions):
    """Prewarm the worker process with necessary components."""
    logger.info("🔥 Prewarming voice agent components...")
    
    # Prewarm RAG components
    try:
        # Initialize knowledge base
        kb = UnifiedKnowledgeBase(
            json_kb_path="knowledge_base",
            pdf_content_path="unified_knowledge_base"
        )
        logger.info("✅ Knowledge base prewarmed")
        
        # Initialize RAG engine
        rag_engine = SimpleRAGEngine(kb)
        logger.info("✅ RAG engine prewarmed")
    except Exception as e:
        logger.warning(f"⚠️ RAG components prewarming failed: {e}")
    
    logger.info("✅ Voice agent prewarm completed")


async def entrypoint(ctx: JobContext):
    """Main entrypoint with improved connection handling and error recovery."""
    logger.info(f"🚀 Starting voice agent for room: {ctx.room.name}")
    
    # Verify configuration
    if not config:
        raise ValueError("Configuration not loaded. Please check your .env file.")
    
    try:
        # Create agent with all RAG components
        agent = BusinessVoiceAgent()
        
        # Set session ID for conversation context
        agent.current_session_id = ctx.room.name or f"session_{ctx.room.sid}"
        
        # Create session using the agent's components
        session = AgentSession(
            stt=agent.stt,
            llm=agent.llm,
            tts=agent.tts,
            vad=agent.vad,
            allow_interruptions=agent.allow_interruptions,
        )
        
        # Create RAG-enhanced session wrapper
        rag_session = RAGEnhancedSession(session, agent)
        
        # Connect to the room with timeout and retry logic
        connection_timeout = 15  # Increased from default 10 seconds
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔗 Attempting to connect to room (attempt {attempt + 1}/{max_retries})")
                # Connect with timeout
                await asyncio.wait_for(ctx.connect(), timeout=connection_timeout)
                logger.info("✅ Successfully connected to LiveKit room")
                break
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Connection attempt {attempt + 1} timed out after {connection_timeout}s")
                if attempt == max_retries - 1:
                    raise Exception("Failed to connect to LiveKit room after multiple attempts")
                await asyncio.sleep(2)  # Wait before retry
            except Exception as e:
                logger.error(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2)  # Wait before retry
        
        # Start the session with the room and agent
        await session.start(
            room=ctx.room,
            agent=agent,
        )
        
        # Generate initial greeting with error handling
        try:
            # Add greeting instruction to chat context
            if hasattr(session, 'chat_ctx') and session.chat_ctx:
                session.chat_ctx.add_message(
                    role="system", 
                    content="Greet the customer professionally as a careSetu healthcare assistant with appointment booking capabilities and ask how you can help them today."
                )
            await session.generate_reply()
        except Exception as e:
            logger.warning(f"Initial greeting failed: {e}")
            # Fallback greeting without LLM
            try:
                await session.say("Hello! I'm your careSetu healthcare assistant with appointment booking capabilities. How can I help you today?")
            except Exception as fallback_error:
                logger.error(f"Even fallback greeting failed: {fallback_error}")
        
        logger.info("🎤 Voice agent with RAG and appointment booking capabilities ready for conversations")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize voice agent: {e}")
        # Try to provide a minimal fallback service
        try:
            await ctx.connect()
            logger.info("🔄 Connected with minimal fallback service")
        except Exception as fallback_error:
            logger.error(f"❌ Complete failure - could not establish any connection: {fallback_error}")
            raise


def main():
    """Main function to run the voice agent."""
    logger.info("🎯 CareSetu Voice Agent with Appointment Booking Starting...")
    
    # Run with LiveKit CLI using standalone entrypoint
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm_process,
    ))


if __name__ == "__main__":
    main()