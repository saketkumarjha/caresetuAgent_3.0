"""
Enhanced Support Agent with ChromaDB Cloud Vector Search
Provides intelligent customer support using semantic search and RAG
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from knowledge_base_chromadb_cloud import CloudKnowledgeBaseConnector, SearchResult
from conversation_context import ConversationMemory, ContextType

logger = logging.getLogger(__name__)

@dataclass
class SupportResponse:
    """Represents a support agent response with metadata."""
    response: str
    confidence: float
    sources: List[str]
    escalation_needed: bool
    escalation_reason: Optional[str] = None
    search_results_count: int = 0
    processing_time: float = 0.0

class EnhancedSupportAgent:
    """
    Enhanced support agent with ChromaDB Cloud integration for semantic search.
    Provides intelligent responses using vector similarity and RAG.
    """
    
    def __init__(self, 
                 company_id: str,
                 llm_instance=None,
                 api_key: Optional[str] = None,
                 tenant: Optional[str] = None,
                 database: Optional[str] = None):
        """
        Initialize enhanced support agent.
        
        Args:
            company_id: Company identifier
            llm_instance: LLM instance for response generation
            api_key: ChromaDB Cloud API key
            tenant: ChromaDB Cloud tenant ID
            database: ChromaDB Cloud database name
        """
        self.company_id = company_id
        self.llm = llm_instance
        
        # Initialize ChromaDB Cloud knowledge base
        self.knowledge_base = CloudKnowledgeBaseConnector(
            company_id=company_id,
            api_key=api_key,
            tenant=tenant,
            database=database
        )
        
        # Conversation contexts for session management
        self.conversation_contexts: Dict[str, ConversationMemory] = {}
        
        # Escalation triggers
        self.escalation_triggers = self._setup_escalation_triggers()
        
        logger.info(f"✅ Enhanced support agent initialized for company: {company_id}")
    
    async def initialize(self):
        """Initialize the support agent by loading knowledge base."""
        await self.knowledge_base.load_knowledge_base()
        logger.info("✅ Support agent knowledge base loaded from ChromaDB Cloud")
    
    def _setup_escalation_triggers(self) -> List[Dict[str, Any]]:
        """Set up escalation triggers for different scenarios."""
        return [
            {
                "type": "confidence",
                "threshold": 0.3,
                "message": "I want to make sure you get the most accurate information. Let me connect you with a specialist."
            },
            {
                "type": "keywords",
                "keywords": ["urgent", "emergency", "complaint", "legal", "lawsuit", "refund", "manager", "supervisor"],
                "message": "I understand this is important. Let me get a manager to assist you right away."
            },
            {
                "type": "escalation_count",
                "threshold": 2,
                "message": "I see we've had some difficulty resolving this. Let me transfer you to our senior support team."
            }
        ]
    
    def get_or_create_context(self, session_id: str, customer_phone: str = None) -> ConversationMemory:
        """Get existing conversation context or create new one."""
        if session_id not in self.conversation_contexts:
            # Create a simple conversation context for now
            from dataclasses import dataclass
            from typing import List, Dict, Any
            
            @dataclass
            class SimpleContext:
                session_id: str
                customer_phone: str = None
                conversation_history: List[Dict[str, Any]] = None
                escalation_count: int = 0
                
                def __post_init__(self):
                    if self.conversation_history is None:
                        self.conversation_history = []
                
                def add_turn(self, user_message: str, agent_response: str, sources: List[str] = None):
                    turn = {
                        "timestamp": datetime.now().isoformat(),
                        "user_message": user_message,
                        "agent_response": agent_response,
                        "sources": sources or []
                    }
                    self.conversation_history.append(turn)
            
            self.conversation_contexts[session_id] = SimpleContext(
                session_id=session_id,
                customer_phone=customer_phone
            )
        return self.conversation_contexts[session_id]
    
    def should_escalate(self, query: str, confidence: float, context) -> tuple[bool, str]:
        """Check if conversation should be escalated to human agent."""
        query_lower = query.lower()
        
        for trigger in self.escalation_triggers:
            if trigger["type"] == "confidence" and confidence < trigger["threshold"]:
                return True, trigger["message"]
            
            elif trigger["type"] == "keywords":
                if any(keyword in query_lower for keyword in trigger["keywords"]):
                    return True, trigger["message"]
            
            elif trigger["type"] == "escalation_count":
                if context.escalation_count >= trigger["threshold"]:
                    return True, trigger["message"]
        
        return False, ""
    
    async def process_customer_query(self, 
                                   query: str, 
                                   session_id: str, 
                                   customer_phone: str = None,
                                   context: Dict[str, Any] = None) -> SupportResponse:
        """
        Process customer query using ChromaDB Cloud semantic search and RAG.
        
        Args:
            query: Customer query
            session_id: Unique session identifier
            customer_phone: Customer phone number
            context: Additional context information
            
        Returns:
            SupportResponse with generated response and metadata
        """
        start_time = datetime.now()
        
        logger.info(f"🤖 Processing query for session {session_id}: '{query}'")
        
        # Get or create conversation context
        conv_context = self.get_or_create_context(session_id, customer_phone)
        
        try:
            # Search knowledge base using ChromaDB Cloud
            search_results = await self.knowledge_base.search(
                query=query,
                max_results=5,
                min_score=0.2
            )
            
            # Calculate confidence from search results
            confidence = max(result.score for result in search_results) if search_results else 0.0
            
            # Check for escalation triggers
            should_escalate, escalation_message = self.should_escalate(query, confidence, conv_context)
            
            if should_escalate:
                conv_context.escalation_count += 1
                response = SupportResponse(
                    response=escalation_message,
                    confidence=confidence,
                    sources=[],
                    escalation_needed=True,
                    escalation_reason=escalation_message,
                    search_results_count=len(search_results),
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            else:
                # Generate response using LLM with knowledge context
                response_text = await self._generate_llm_response(
                    query, search_results, conv_context, context
                )
                
                response = SupportResponse(
                    response=response_text,
                    confidence=confidence,
                    sources=[result.document.title for result in search_results],
                    escalation_needed=False,
                    search_results_count=len(search_results),
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
            
            # Add turn to conversation history
            conv_context.add_turn(
                user_message=query,
                agent_response=response.response,
                sources=response.sources
            )
            
            logger.info(f"✅ Generated response (confidence: {confidence:.2f}, time: {response.processing_time:.2f}s)")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            return SupportResponse(
                response="I apologize, but I'm experiencing technical difficulties. Let me connect you with someone who can help you directly.",
                confidence=0.0,
                sources=[],
                escalation_needed=True,
                escalation_reason=f"Technical error: {str(e)}",
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    async def _generate_llm_response(self, 
                                   query: str, 
                                   search_results: List[SearchResult], 
                                   conv_context,
                                   context: Dict[str, Any] = None) -> str:
        """Generate response using LLM with ChromaDB Cloud search results."""
        
        # Prepare knowledge context from search results
        knowledge_context = self._prepare_knowledge_context(search_results)
        
        # Prepare conversation history
        conversation_history = self._prepare_conversation_history(conv_context)
        
        # Create system prompt with enhanced context
        system_prompt = f"""You are a helpful customer service representative for {self.company_id}. Use the provided knowledge base information from our ChromaDB Cloud vector database to answer the customer's question accurately and professionally.

KNOWLEDGE BASE INFORMATION (from semantic search):
{knowledge_context}

CONVERSATION HISTORY:
{conversation_history}

INSTRUCTIONS:
1. Answer based primarily on the knowledge base information provided
2. Be conversational and helpful
3. If the knowledge base doesn't fully answer the question, acknowledge this and offer to help further
4. Keep responses concise but complete
5. Use a professional but friendly tone
6. If you need to escalate or get more information, say so clearly
7. Reference specific policies or procedures when relevant

CONVERSATION CONTEXT:
{json.dumps(context or {}, indent=2)}

Remember: You're representing {self.company_id}, so maintain professionalism while being genuinely helpful."""
        
        user_prompt = f"Customer question: {query}"
        
        try:
            # Generate response using LLM
            if self.llm and hasattr(self.llm, 'achat'):
                # For testing with MockLLM or similar
                full_prompt = f"{system_prompt}\n\nUser: {user_prompt}\nAssistant:"
                
                class SimplePrompt:
                    def __init__(self, text):
                        self.text = text
                
                response = await self.llm.achat(SimplePrompt(full_prompt))
                return response.content.strip()
            else:
                # Fallback response when no LLM is available
                if search_results:
                    best_result = search_results[0]
                    return f"Based on our {best_result.document.category} information: {best_result.document.content[:200]}... Would you like me to provide more specific details about this?"
                else:
                    return "I don't have specific information about that in our knowledge base right now. Let me connect you with someone who can help you with that question."
            
        except Exception as e:
            logger.error(f"❌ Error generating LLM response: {e}")
            return "I apologize, but I'm having trouble accessing our information right now. Let me connect you with someone who can help you directly."
    
    def _prepare_knowledge_context(self, search_results: List[SearchResult]) -> str:
        """Prepare knowledge context from ChromaDB Cloud search results."""
        if not search_results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            doc = result.document
            context_parts.append(f"""
Knowledge Source {i} (Relevance Score: {result.score:.3f}, Vector Distance: {result.vector_distance:.3f}):
Title: {doc.title}
Category: {doc.category}
Tags: {', '.join(doc.tags)}
Content: {doc.content}
Relevance: {result.relevance_explanation}
""")
        
        return "\n".join(context_parts)
    
    def _prepare_conversation_history(self, conv_context) -> str:
        """Prepare conversation history for LLM context."""
        if not conv_context.conversation_history:
            return "No previous conversation history."
        
        history_parts = []
        # Only include last 3 turns to keep context manageable
        recent_history = conv_context.conversation_history[-3:]
        
        for turn in recent_history:
            history_parts.append(f"""
Previous Turn:
Customer: {turn['user_message']}
Agent: {turn['agent_response']}
Sources Used: {', '.join(turn['sources']) if turn['sources'] else 'None'}
""")
        
        return "\n".join(history_parts)
    
    async def add_knowledge_document(self, title: str, content: str, category: str, tags: List[str]) -> bool:
        """Add a new knowledge document to ChromaDB Cloud."""
        from knowledge_base_chromadb_cloud import KnowledgeDocument
        
        doc = KnowledgeDocument(
            id=f"{self.company_id}_{title.lower().replace(' ', '_')}",
            title=title,
            content=content,
            category=category,
            tags=tags,
            company_id=self.company_id
        )
        
        return await self.knowledge_base.add_document(doc)
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        return await self.knowledge_base.get_cloud_stats()

# Test the enhanced support agent
async def test_enhanced_support_agent():
    """Test enhanced support agent with ChromaDB Cloud."""
    
    print("🧪 Testing Enhanced Support Agent with ChromaDB Cloud")
    print("=" * 60)
    
    try:
        # Initialize enhanced support agent
        agent = EnhancedSupportAgent(
            company_id="test_company",
            api_key='ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
            tenant='952f5e15-854e-461e-83d1-3cef021c755c',
            database='Assembly_AI'
        )
        
        await agent.initialize()
        
        # Test queries
        test_queries = [
            "What are your business hours?",
            "How do I cancel my appointment?",
            "I need help with billing issues",
            "Can you help me reschedule my appointment?",
            "I'm having technical problems with your website"
        ]
        
        session_id = "test_session_001"
        
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            response = await agent.process_customer_query(
                query=query,
                session_id=session_id,
                customer_phone="555-123-4567"
            )
            
            print(f"  Response: {response.response}")
            print(f"  Confidence: {response.confidence:.3f}")
            print(f"  Sources: {response.sources}")
            print(f"  Escalation needed: {response.escalation_needed}")
            print(f"  Processing time: {response.processing_time:.3f}s")
            
            if response.escalation_needed:
                print(f"  Escalation reason: {response.escalation_reason}")
        
        # Get knowledge stats
        stats = await agent.get_knowledge_stats()
        print(f"\n📊 Knowledge Base Stats: {stats}")
        
        print("\n✅ Enhanced support agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Enhanced support agent test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_support_agent())