"""Intent detection and routing for business conversations."""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from livekit.agents import llm

# Intent router now works independently without support agent module

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Types of customer intents."""
    SUPPORT = "support"
    SCHEDULING = "scheduling"
    GENERAL = "general"
    ESCALATION = "escalation"
    UNKNOWN = "unknown"

@dataclass
class ConversationContext:
    """Context for ongoing conversation."""
    session_id: str = ""
    current_intent: IntentType = IntentType.UNKNOWN
    customer_info: Dict[str, Any] = None
    conversation_history: list = None
    business_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.customer_info is None:
            self.customer_info = {}
        if self.conversation_history is None:
            self.conversation_history = []
        if self.business_data is None:
            self.business_data = {}

class IntentRouter:
    """Routes customer conversations based on detected intent."""
    
    def __init__(self, llm_instance: llm.LLM):
        """Initialize intent router with LLM for intent detection."""
        self.llm = llm_instance
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        
        # Intent router works independently now
        
        # Intent detection keywords
        self.intent_keywords = {
            IntentType.SUPPORT: [
                "help", "problem", "issue", "trouble", "error", "broken",
                "billing", "payment", "charge", "invoice", "account",
                "technical", "not working", "can't", "unable", "difficulty",
                "question", "how to", "explain", "understand"
            ],
            IntentType.SCHEDULING: [
                "appointment", "schedule", "book", "reserve", "meeting",
                "reschedule", "cancel", "change", "move", "availability",
                "available", "time", "date", "when", "calendar",
                "consultation", "session", "visit", "call back"
            ],
            IntentType.ESCALATION: [
                "manager", "supervisor", "human", "person", "representative",
                "escalate", "complaint", "unsatisfied", "frustrated",
                "speak to", "talk to", "transfer", "connect me"
            ]
        }
    
    async def detect_intent(self, user_text: str, context: Dict[str, Any]) -> IntentType:
        """
        Detect customer intent from their message.
        
        Args:
            user_text: What the customer said
            context: Additional context about the conversation
            
        Returns:
            Detected intent type
        """
        
        user_text_lower = user_text.lower()
        
        # First, check for keyword matches (fast path)
        keyword_scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in user_text_lower)
            if score > 0:
                keyword_scores[intent] = score
        
        # If we have clear keyword matches, use them
        if keyword_scores:
            best_intent = max(keyword_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"🎯 Intent detected via keywords: {best_intent.value}")
            return best_intent
        
        # Use LLM for more nuanced intent detection
        try:
            intent_prompt = f"""
            Analyze this customer message and determine their primary intent:

            Customer message: "{user_text}"
            
            Choose ONE of these intents:
            - SUPPORT: Customer needs help with a problem, has questions, or needs technical assistance
            - SCHEDULING: Customer wants to book, reschedule, cancel, or check appointment availability  
            - ESCALATION: Customer wants to speak with a human, manager, or is expressing frustration
            - GENERAL: General inquiry or greeting that doesn't fit other categories
            
            Consider the context:
            - This is a business phone call
            - Customer may use casual language
            - Intent should be based on what they actually need
            
            Respond with just the intent name: SUPPORT, SCHEDULING, ESCALATION, or GENERAL
            """
            
            response = await self.llm.achat(intent_prompt)
            intent_text = response.content.strip().upper()
            
            # Map response to enum
            intent_mapping = {
                "SUPPORT": IntentType.SUPPORT,
                "SCHEDULING": IntentType.SCHEDULING,
                "ESCALATION": IntentType.ESCALATION,
                "GENERAL": IntentType.GENERAL
            }
            
            detected_intent = intent_mapping.get(intent_text, IntentType.UNKNOWN)
            logger.info(f"🤖 Intent detected via LLM: {detected_intent.value}")
            return detected_intent
            
        except Exception as e:
            logger.error(f"Error in LLM intent detection: {e}")
            return IntentType.UNKNOWN
    
    async def process_user_input(self, user_text: str, context: Dict[str, Any]) -> str:
        """
        Process user input and route to appropriate handler.
        
        Args:
            user_text: What the customer said
            context: Conversation context
            
        Returns:
            Response or routing information
        """
        
        # Get or create conversation context
        session_id = context.get("room_name", "default")
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = ConversationContext(session_id=session_id)
        
        conv_context = self.conversation_contexts[session_id]
        
        # Detect intent
        detected_intent = await self.detect_intent(user_text, context)
        
        # Update conversation context
        conv_context.current_intent = detected_intent
        conv_context.conversation_history.append({
            "user": user_text,
            "intent": detected_intent.value,
            "timestamp": context.get("timestamp")
        })
        
        # Route based on intent
        routing_info = await self._route_conversation(detected_intent, user_text, conv_context)
        
        logger.info(f"📋 Conversation routed: {detected_intent.value} -> {routing_info}")
        return routing_info
    
    async def _route_conversation(self, intent: IntentType, user_text: str, 
                                context: ConversationContext) -> str:
        """
        Route conversation based on detected intent.
        
        Args:
            intent: Detected customer intent
            user_text: Original user message
            context: Conversation context
            
        Returns:
            Routing information or response guidance
        """
        
        routing_responses = {
            IntentType.SUPPORT: await self._handle_support_intent(user_text, context),
            IntentType.SCHEDULING: await self._handle_scheduling_intent(user_text, context),
            IntentType.ESCALATION: await self._handle_escalation_intent(user_text, context),
            IntentType.GENERAL: await self._handle_general_intent(user_text, context),
            IntentType.UNKNOWN: "I want to help you today. Could you tell me a bit more about what you need?"
        }
        
        return routing_responses.get(intent, routing_responses[IntentType.UNKNOWN])
    
    async def _handle_support_intent(self, user_text: str, context: ConversationContext) -> str:
        """Handle customer support requests using the support agent module."""
        
        try:
            # Initialize support agent if not already done
            if not hasattr(self.support_agent, 'is_initialized') or not self.support_agent.is_initialized:
                await self.support_agent.initialize()
                self.support_agent.is_initialized = True
            
            # Create context for support agent
            support_context = {
                'session_id': context.session_id,
                'customer_phone': context.customer_info.get('phone'),
                'customer_id': context.customer_info.get('id'),
                'timestamp': context.conversation_history[-1].get('timestamp') if context.conversation_history else None
            }
            
            # Handle support request through support agent module
            response_data = await self.support_agent.handle_support_request(user_text, support_context)
            
            # Return the response text
            return response_data.get('response', 'I apologize, but I need to connect you with someone who can help you better.')
            
        except Exception as e:
            logger.error(f"❌ Error in support intent handling: {e}")
            # Fallback response
            return "I understand you're having an issue, and I'm here to help. Can you tell me more about what's happening so I can assist you better?"
    
    async def _handle_scheduling_intent(self, user_text: str, context: ConversationContext) -> str:
        """Handle appointment scheduling requests."""
        
        # Check if they want to book, reschedule, or cancel
        if any(word in user_text.lower() for word in ["cancel", "cancellation"]):
            return "I can help you cancel your appointment. Can you provide me with your appointment details or the date and time?"
        
        elif any(word in user_text.lower() for word in ["reschedule", "change", "move"]):
            return "I'd be happy to help you reschedule. What's your current appointment time, and when would you prefer to meet instead?"
        
        elif any(word in user_text.lower() for word in ["availability", "available", "when"]):
            return "I can check our availability for you. What type of appointment are you looking for, and do you have any preferred dates or times?"
        
        else:
            # General booking request
            return "I'd be happy to help you schedule an appointment. What type of service do you need, and when would work best for you?"
    
    async def _handle_escalation_intent(self, user_text: str, context: ConversationContext) -> str:
        """Handle requests for human escalation."""
        
        return "I understand you'd like to speak with someone else. Let me connect you with one of our team members who can help you further. Please hold for just a moment."
    
    async def _handle_general_intent(self, user_text: str, context: ConversationContext) -> str:
        """Handle general inquiries and greetings."""
        
        # Check for greetings
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
        if any(greeting in user_text.lower() for greeting in greetings):
            return "Hello! Thank you for calling. I'm here to help with any questions or to schedule an appointment. How can I assist you today?"
        
        # General inquiry
        return "Thank you for calling. I'm here to help with customer support or appointment scheduling. What can I do for you today?"
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session."""
        return self.conversation_contexts.get(session_id)
    
    def clear_conversation_context(self, session_id: str):
        """Clear conversation context for a session."""
        if session_id in self.conversation_contexts:
            del self.conversation_contexts[session_id]
            logger.info(f"🧹 Cleared conversation context for session: {session_id}")

# Test the intent router
async def test_intent_detection():
    """Test intent detection with sample phrases."""
    
    # Mock LLM for testing
    class MockLLM:
        async def achat(self, prompt):
            class MockResponse:
                content = "SUPPORT"  # Default response
            return MockResponse()
    
    router = IntentRouter(MockLLM())
    
    test_cases = [
        ("I need help with my billing", IntentType.SUPPORT),
        ("I'd like to schedule an appointment", IntentType.SCHEDULING),
        ("Can I speak to a manager?", IntentType.ESCALATION),
        ("Hello, good morning", IntentType.GENERAL),
        ("My account isn't working", IntentType.SUPPORT),
        ("What's your availability next week?", IntentType.SCHEDULING),
        ("I want to cancel my appointment", IntentType.SCHEDULING),
        ("This is frustrating, get me a human", IntentType.ESCALATION)
    ]
    
    print("🧪 Testing Intent Detection")
    print("=" * 40)
    
    for text, expected in test_cases:
        detected = await router.detect_intent(text, {})
        status = "✅" if detected == expected else "❌"
        print(f"{status} '{text}' -> {detected.value} (expected: {expected.value})")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_intent_detection())