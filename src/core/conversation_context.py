"""Conversation Context Management for multi-turn conversations."""

import asyncio
import logging
import json
import pickle
import redis
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class ContextType(Enum):
    """Types of conversation contexts."""
    GENERAL = "general"
    SUPPORT = "support"
    SCHEDULING = "scheduling"
    ESCALATION = "escalation"

@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""
    timestamp: datetime
    user_message: str
    agent_response: str
    intent: str
    confidence: float
    sources_used: List[str]
    escalation_triggered: bool = False
    
    def __post_init__(self):
        if self.sources_used is None:
            self.sources_used = []

@dataclass
class CustomerProfile:
    """Customer profile information."""
    customer_id: Optional[str] = None
    phone_number: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}

@dataclass
class ConversationMemory:
    """Persistent memory for ongoing conversations."""
    session_id: str
    customer_phone: Optional[str]
    customer_name: Optional[str]
    context_type: ContextType
    created_at: datetime
    last_updated: datetime
    turns: List[ConversationTurn]
    
    # Context-specific data
    current_topic: Optional[str] = None
    resolved_issues: List[str] = None
    pending_actions: List[str] = None
    customer_preferences: Dict[str, Any] = None
    business_data: Dict[str, Any] = None
    
    # Knowledge base context
    relevant_documents: List[str] = None
    knowledge_context: str = ""
    
    def __post_init__(self):
        if self.resolved_issues is None:
            self.resolved_issues = []
        if self.pending_actions is None:
            self.pending_actions = []
        if self.customer_preferences is None:
            self.customer_preferences = {}
        if self.business_data is None:
            self.business_data = {}
        if self.relevant_documents is None:
            self.relevant_documents = []

class ConversationContextManager:
    """
    Manages conversation context across multiple turns.
    Provides memory and context retention for natural conversations.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 context_ttl: int = 3600):  # 1 hour TTL
        """
        Initialize conversation context manager.
        
        Args:
            redis_url: Redis connection URL for persistent storage
            context_ttl: Time-to-live for conversation contexts in seconds
        """
        self.redis_url = redis_url
        self.context_ttl = context_ttl
        self.redis_client = None
        
        # In-memory cache for active conversations
        self.active_contexts: Dict[str, ConversationMemory] = {}
        
        # Context summarization thresholds
        self.max_turns_before_summary = 10
        self.summary_overlap_turns = 3
    
    async def initialize(self):
        """Initialize the context manager."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            # Test connection
            await asyncio.to_thread(self.redis_client.ping)
            logger.info("✅ Connected to Redis for conversation context")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed, using in-memory only: {e}")
            self.redis_client = None
    
    async def get_or_create_context(self, session_id: str, 
                                  context_type: ContextType = ContextType.GENERAL,
                                  customer_phone: str = None) -> ConversationMemory:
        """
        Get existing conversation context or create new one.
        
        Args:
            session_id: Unique session identifier
            context_type: Type of conversation context
            customer_phone: Customer phone number if available
            
        Returns:
            ConversationMemory instance
        """
        
        # Check in-memory cache first
        if session_id in self.active_contexts:
            context = self.active_contexts[session_id]
            context.last_updated = datetime.now()
            return context
        
        # Try to load from Redis
        if self.redis_client:
            try:
                stored_data = await asyncio.to_thread(
                    self.redis_client.get, f"conversation:{session_id}"
                )
                if stored_data:
                    context = pickle.loads(stored_data)
                    context.last_updated = datetime.now()
                    self.active_contexts[session_id] = context
                    logger.info(f"📥 Loaded conversation context for session: {session_id}")
                    return context
            except Exception as e:
                logger.error(f"Error loading context from Redis: {e}")
        
        # Create new context
        context = ConversationMemory(
            session_id=session_id,
            customer_phone=customer_phone,
            customer_name=None,
            context_type=context_type,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            turns=[]
        )
        
        self.active_contexts[session_id] = context
        await self._save_context(context)
        
        logger.info(f"🆕 Created new conversation context for session: {session_id}")
        return context
    
    async def add_conversation_turn(self, session_id: str, user_message: str,
                                 agent_response: str, intent: str, confidence: float,
                                 sources_used: List[str] = None,
                                 escalation_triggered: bool = False) -> ConversationMemory:
        """
        Add a new turn to the conversation.
        
        Args:
            session_id: Session identifier
            user_message: What the user said
            agent_response: Agent's response
            intent: Detected intent
            confidence: Confidence score
            sources_used: Knowledge sources used
            escalation_triggered: Whether escalation was triggered
            
        Returns:
            Updated ConversationMemory
        """
        
        context = await self.get_or_create_context(session_id)
        
        # Create new turn
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_message=user_message,
            agent_response=agent_response,
            intent=intent,
            confidence=confidence,
            sources_used=sources_used or [],
            escalation_triggered=escalation_triggered
        )
        
        context.turns.append(turn)
        context.last_updated = datetime.now()
        
        # Update relevant documents list
        if sources_used:
            for source in sources_used:
                if source not in context.relevant_documents:
                    context.relevant_documents.append(source)
        
        # Check if we need to summarize old turns
        if len(context.turns) > self.max_turns_before_summary:
            await self._summarize_old_turns(context)
        
        # Save updated context
        await self._save_context(context)
        
        logger.info(f"💬 Added conversation turn for session: {session_id} (Total turns: {len(context.turns)})")
        return context

    async def get_conversation_summary(self, session_id: str, 
                                    last_n_turns: int = 5) -> str:
        """
        Get a summary of recent conversation for LLM context.
        
        Args:
            session_id: Session identifier
            last_n_turns: Number of recent turns to include
            
        Returns:
            Formatted conversation summary
        """
        
        context = await self.get_or_create_context(session_id)
        
        if not context.turns:
            return "This is the beginning of the conversation."
        
        # Get recent turns
        recent_turns = context.turns[-last_n_turns:] if len(context.turns) > last_n_turns else context.turns
        
        summary_parts = []
        
        # Add context information
        if context.current_topic:
            summary_parts.append(f"Current topic: {context.current_topic}")
        
        if context.resolved_issues:
            summary_parts.append(f"Previously resolved: {', '.join(context.resolved_issues[-3:])}")
        
        if context.pending_actions:
            summary_parts.append(f"Pending actions: {', '.join(context.pending_actions)}")
        
        # Add conversation history
        summary_parts.append("\nRecent conversation:")
        for i, turn in enumerate(recent_turns, 1):
            summary_parts.append(f"{i}. Customer: {turn.user_message}")
            summary_parts.append(f"   Agent: {turn.agent_response}")
            if turn.sources_used:
                summary_parts.append(f"   (Used sources: {', '.join(turn.sources_used)})")
        
        # Add knowledge context if available
        if context.knowledge_context:
            summary_parts.append(f"\nRelevant knowledge context:\n{context.knowledge_context}")
        
        return "\n".join(summary_parts)
    
    async def update_context_data(self, session_id: str, **kwargs) -> ConversationMemory:
        """
        Update context-specific data.
        
        Args:
            session_id: Session identifier
            **kwargs: Data to update (current_topic, customer_name, etc.)
            
        Returns:
            Updated ConversationMemory
        """
        
        context = await self.get_or_create_context(session_id)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        
        context.last_updated = datetime.now()
        await self._save_context(context)
        
        logger.info(f"📝 Updated context data for session: {session_id}")
        return context
    
    async def set_knowledge_context(self, session_id: str, 
                                  knowledge_context: str,
                                  relevant_documents: List[str]) -> ConversationMemory:
        """
        Set knowledge base context for the conversation.
        
        Args:
            session_id: Session identifier
            knowledge_context: Formatted knowledge context
            relevant_documents: List of relevant document titles
            
        Returns:
            Updated ConversationMemory
        """
        
        context = await self.get_or_create_context(session_id)
        context.knowledge_context = knowledge_context
        context.relevant_documents = list(set(context.relevant_documents + relevant_documents))
        context.last_updated = datetime.now()
        
        await self._save_context(context)
        
        logger.info(f"📚 Set knowledge context for session: {session_id}")
        return context
    
    async def get_context_for_rag(self, session_id: str) -> Dict[str, Any]:
        """
        Get context information specifically formatted for RAG system.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with context information for RAG
        """
        context = await self.get_or_create_context(session_id)
        
        return {
            "session_id": session_id,
            "current_topic": context.current_topic,
            "relevant_documents": context.relevant_documents,
            "recent_intents": [turn.intent for turn in context.turns[-3:]] if context.turns else [],
            "conversation_length": len(context.turns),
            "last_sources_used": context.turns[-1].sources_used if context.turns else [],
            "knowledge_context": context.knowledge_context
        }
    
    async def is_follow_up_context(self, session_id: str, current_query: str) -> bool:
        """
        Determine if current query is a follow-up based on conversation context.
        
        Args:
            session_id: Session identifier
            current_query: Current user query
            
        Returns:
            True if this appears to be a follow-up question
        """
        context = await self.get_or_create_context(session_id)
        
        if not context.turns:
            return False
        
        query_lower = current_query.lower()
        
        # Check for follow-up indicators
        follow_up_patterns = [
            'what about', 'how about', 'and', 'also', 'additionally',
            'can you', 'could you', 'please tell me', 'more', 'other',
            'it', 'that', 'this', 'they', 'them', 'continue', 'next'
        ]
        
        # Check for pronoun references or follow-up phrases
        has_follow_up_indicators = any(pattern in query_lower for pattern in follow_up_patterns)
        
        # Check if query is very short (likely a follow-up)
        is_short_query = len(current_query.split()) <= 3
        
        # Check if recent conversation had similar topic
        recent_turn = context.turns[-1] if context.turns else None
        has_recent_context = recent_turn and len(recent_turn.sources_used) > 0
        
        return has_follow_up_indicators or (is_short_query and has_recent_context)
    
    async def _summarize_old_turns(self, context: ConversationMemory):
        """Summarize old conversation turns to save memory."""
        
        if len(context.turns) <= self.max_turns_before_summary:
            return
        
        # Keep recent turns and summarize older ones
        turns_to_summarize = context.turns[:-self.summary_overlap_turns]
        recent_turns = context.turns[-self.summary_overlap_turns:]
        
        # Create summary of old turns
        summary_points = []
        for turn in turns_to_summarize:
            if turn.escalation_triggered:
                summary_points.append(f"Escalation triggered: {turn.user_message}")
            if turn.sources_used:
                summary_points.append(f"Used knowledge sources: {', '.join(turn.sources_used)}")
        
        # Update context with summary
        if summary_points:
            existing_summary = context.knowledge_context
            new_summary = f"Previous conversation summary:\n{'; '.join(summary_points)}"
            context.knowledge_context = f"{existing_summary}\n\n{new_summary}" if existing_summary else new_summary
        
        # Keep only recent turns
        context.turns = recent_turns
        
        logger.info(f"📋 Summarized old conversation turns for session: {context.session_id}")
    
    async def _save_context(self, context: ConversationMemory):
        """Save conversation context to persistent storage."""
        
        if not self.redis_client:
            return  # Only in-memory storage available
        
        try:
            # Serialize context
            serialized_context = pickle.dumps(context)
            
            # Save to Redis with TTL
            await asyncio.to_thread(
                self.redis_client.setex,
                f"conversation:{context.session_id}",
                self.context_ttl,
                serialized_context
            )
            
        except Exception as e:
            logger.error(f"Error saving context to Redis: {e}")
    
    async def clear_context(self, session_id: str):
        """Clear conversation context."""
        
        # Remove from memory
        if session_id in self.active_contexts:
            del self.active_contexts[session_id]
        
        # Remove from Redis
        if self.redis_client:
            try:
                await asyncio.to_thread(
                    self.redis_client.delete, f"conversation:{session_id}"
                )
            except Exception as e:
                logger.error(f"Error clearing context from Redis: {e}")
        
        logger.info(f"🧹 Cleared conversation context for session: {session_id}")
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs."""
        return list(self.active_contexts.keys())
    
    async def cleanup_expired_contexts(self):
        """Clean up expired conversation contexts."""
        
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, context in self.active_contexts.items():
            if current_time - context.last_updated > timedelta(seconds=self.context_ttl):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.clear_context(session_id)
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired conversation contexts")

# Test the conversation context manager
async def test_conversation_context():
    """Test conversation context management."""
    
    print("🧪 Testing Conversation Context Manager")
    print("=" * 50)
    
    # Initialize context manager
    manager = ConversationContextManager()
    await manager.initialize()
    
    # Test creating and updating context
    session_id = "test_session_123"
    
    # Create context
    context = await manager.get_or_create_context(
        session_id, 
        ContextType.SUPPORT, 
        "+1234567890"
    )
    print(f"✅ Created context for session: {context.session_id}")
    
    # Add conversation turns
    turns_data = [
        ("I need help with billing", "I'd be happy to help with your billing question.", "support", 0.9),
        ("My last invoice was wrong", "Let me look into your billing history.", "support", 0.8),
        ("Can you fix this?", "I'll escalate this to our billing specialist.", "escalation", 0.7)
    ]
    
    for user_msg, agent_msg, intent, confidence in turns_data:
        await manager.add_conversation_turn(
            session_id, user_msg, agent_msg, intent, confidence,
            sources_used=["Billing FAQ", "Payment Policy"]
        )
    
    # Get conversation summary
    summary = await manager.get_conversation_summary(session_id)
    print(f"\n📋 Conversation Summary:\n{summary}")
    
    # Update context data
    await manager.update_context_data(
        session_id,
        current_topic="billing_dispute",
        customer_name="John Doe"
    )
    
    # Test knowledge context
    await manager.set_knowledge_context(
        session_id,
        "Customer has billing dispute. Previous issues resolved via credit adjustment.",
        ["Billing FAQ", "Dispute Resolution Guide"]
    )
    
    print(f"\n📊 Active sessions: {await manager.get_active_sessions()}")
    
    # Clean up
    await manager.clear_context(session_id)
    print(f"✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_conversation_context())