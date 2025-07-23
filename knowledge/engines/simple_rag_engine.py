"""
Simple RAG Engine
Implements text-based search without vector databases and creates ranking algorithm for search results
"""

import logging
import re
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter, deque
import uuid

from knowledge.storage.unified_knowledge_base import UnifiedKnowledgeBase, KnowledgeEntry
from knowledge.storage.knowledge_indexer import KnowledgeIndexer, SearchResult as IndexerSearchResult
from knowledge.engines.domain_expertise import DomainExpertiseEngine, DomainResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Enhanced search result for RAG system."""
    document_id: str
    section_id: str
    content: str
    relevance_score: float
    document_type: str
    source_file: str
    context_match: str
    snippet: str
    title: str = ""
    matched_terms: List[str] = None
    ranking_factors: Dict[str, float] = None
    
    def __post_init__(self):
        if self.matched_terms is None:
            self.matched_terms = []
        if self.ranking_factors is None:
            self.ranking_factors = {}

@dataclass
class RAGResponse:
    """Response from RAG system."""
    answer: str
    sources: List[str]
    confidence: float
    context_used: str
    retrieved_content: List[SearchResult]
    processing_time: float
    search_query: str = ""
    total_results_found: int = 0
    citations: List[Dict[str, Any]] = None
    synthesis_method: str = ""
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = []

class QueryProcessor:
    """Processes and enhances search queries."""
    
    def __init__(self):
        """Initialize query processor."""
        # Common question patterns and their expansions
        self.question_patterns = {
            r'\bhow\s+(?:do\s+i|can\s+i|to)\s+': ['process', 'steps', 'procedure', 'method'],
            r'\bwhat\s+is\s+': ['definition', 'meaning', 'explanation'],
            r'\bwhen\s+': ['time', 'schedule', 'hours', 'date'],
            r'\bwhere\s+': ['location', 'place', 'address'],
            r'\bwhy\s+': ['reason', 'explanation', 'cause'],
            r'\bwho\s+': ['person', 'contact', 'responsible'],
            r'\bcan\s+i\s+': ['permission', 'allowed', 'policy'],
            r'\bis\s+it\s+': ['status', 'condition', 'state']
        }
        
        # Domain-specific term expansions
        self.domain_expansions = {
            'appointment': ['booking', 'schedule', 'meeting', 'visit'],
            'cancel': ['cancellation', 'cancel', 'remove', 'delete'],
            'policy': ['rule', 'guideline', 'procedure', 'regulation'],
            'support': ['help', 'assistance', 'customer service', 'contact'],
            'payment': ['billing', 'cost', 'price', 'fee', 'charge'],
            'account': ['profile', 'user', 'login', 'registration'],
            'service': ['offering', 'feature', 'capability', 'function'],
            'privacy': ['data protection', 'confidential', 'security'],
            'hours': ['time', 'schedule', 'availability', 'open'],
            'contact': ['phone', 'email', 'address', 'reach']
        }
        
        logger.info("Query processor initialized")
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query with related terms and synonyms.
        
        Args:
            query: Original search query
            
        Returns:
            List of expanded query terms
        """
        expanded_terms = []
        query_lower = query.lower()
        
        # Add original query terms
        original_terms = re.findall(r'\b\w+\b', query_lower)
        expanded_terms.extend(original_terms)
        
        # Add question pattern expansions
        for pattern, expansions in self.question_patterns.items():
            if re.search(pattern, query_lower):
                expanded_terms.extend(expansions)
        
        # Add domain-specific expansions
        for term, expansions in self.domain_expansions.items():
            if term in query_lower:
                expanded_terms.extend(expansions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms
    
    def extract_intent(self, query: str) -> str:
        """
        Extract intent from query.
        
        Args:
            query: Search query
            
        Returns:
            Detected intent
        """
        query_lower = query.lower()
        
        # Intent patterns
        intent_patterns = {
            'booking': r'\b(book|schedule|make|create|set up|arrange).*appointment',
            'cancellation': r'\b(cancel|remove|delete|reschedule).*appointment',
            'information': r'\b(what|tell me|information|details|about)',
            'procedure': r'\b(how|steps|process|procedure|method)',
            'policy': r'\b(policy|rule|guideline|allowed|permitted)',
            'contact': r'\b(contact|phone|email|reach|call|support)',
            'hours': r'\b(hours|time|open|available|schedule)',
            'cost': r'\b(cost|price|fee|charge|payment|billing)'
        }
        
        for intent, pattern in intent_patterns.items():
            if re.search(pattern, query_lower):
                return intent
        
        return 'general'

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    id: str
    query: str
    intent: str
    response: str
    retrieved_documents: List[str]
    confidence: float
    timestamp: datetime
    context_keywords: List[str] = field(default_factory=list)
    
@dataclass
class ConversationContext:
    """Manages conversation context for context-aware search."""
    session_id: str
    turns: deque = field(default_factory=lambda: deque(maxlen=10))  # Keep last 10 turns
    current_topic: Optional[str] = None
    topic_keywords: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    last_accessed_documents: List[str] = field(default_factory=list)
    conversation_start: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, turn: ConversationTurn):
        """Add a new conversation turn."""
        self.turns.append(turn)
        self._update_context(turn)
    
    def _update_context(self, turn: ConversationTurn):
        """Update conversation context based on new turn."""
        # Update topic keywords
        self.topic_keywords.extend(turn.context_keywords)
        # Keep only unique keywords and limit to recent ones
        self.topic_keywords = list(set(self.topic_keywords))[-20:]
        
        # Update current topic based on intent patterns
        if turn.intent in ['booking', 'cancellation', 'procedure']:
            self.current_topic = turn.intent
        
        # Update last accessed documents
        self.last_accessed_documents.extend(turn.retrieved_documents)
        self.last_accessed_documents = list(set(self.last_accessed_documents))[-10:]
    
    def get_context_keywords(self) -> List[str]:
        """Get relevant context keywords from recent conversation."""
        context_keywords = []
        
        # Get keywords from recent turns (last 3 turns)
        recent_turns = list(self.turns)[-3:]
        for turn in recent_turns:
            context_keywords.extend(turn.context_keywords)
        
        # Add topic keywords
        context_keywords.extend(self.topic_keywords)
        
        # Remove duplicates and return
        return list(set(context_keywords))
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation for context."""
        if not self.turns:
            return ""
        
        recent_queries = [turn.query for turn in list(self.turns)[-3:]]
        return " | ".join(recent_queries)
    
    def is_follow_up_question(self, query: str) -> bool:
        """Determine if current query is a follow-up to previous questions."""
        if not self.turns:
            return False
        
        query_lower = query.lower()
        
        # Check for follow-up indicators
        follow_up_patterns = [
            r'\b(what about|how about|and|also|additionally|furthermore)\b',
            r'\b(can you|could you|please)\b.*\b(tell me|explain|show)\b',
            r'\b(more|additional|other|another)\b.*\b(information|details|options)\b'
        ]
        
        for pattern in follow_up_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check for pronoun references (it, that, this, they)
        pronoun_patterns = [r'\b(it|that|this|they|them)\b']
        for pattern in pronoun_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def get_related_documents(self) -> List[str]:
        """Get documents related to current conversation context."""
        return self.last_accessed_documents

class ContextualSearchFilter:
    """Filters and enhances search results based on conversation context."""
    
    def __init__(self):
        """Initialize contextual search filter."""
        logger.info("Contextual search filter initialized")
    
    def apply_context_filtering(self, 
                              results: List[SearchResult], 
                              context: ConversationContext,
                              query: str) -> List[SearchResult]:
        """
        Apply context-based filtering to search results.
        
        Args:
            results: Original search results
            context: Conversation context
            query: Current query
            
        Returns:
            Context-filtered search results
        """
        if not results or not context.turns:
            return results
        
        # Get context keywords
        context_keywords = context.get_context_keywords()
        
        # Check if this is a follow-up question
        is_follow_up = context.is_follow_up_question(query)
        
        # Apply different filtering strategies
        if is_follow_up:
            return self._filter_for_follow_up(results, context, context_keywords)
        else:
            return self._filter_for_new_topic(results, context, context_keywords)
    
    def _filter_for_follow_up(self, 
                            results: List[SearchResult], 
                            context: ConversationContext,
                            context_keywords: List[str]) -> List[SearchResult]:
        """Filter results for follow-up questions."""
        enhanced_results = []
        
        for result in results:
            # Boost score for documents from same source as previous queries
            context_boost = 0.0
            
            # Check if result is from recently accessed documents
            if result.source_file in context.last_accessed_documents:
                context_boost += 0.2
            
            # Check if result contains context keywords
            content_lower = result.content.lower()
            context_matches = sum(1 for keyword in context_keywords 
                                if keyword.lower() in content_lower)
            if context_matches > 0:
                context_boost += min(0.3, context_matches * 0.1)
            
            # Check if result is from same document type as current topic
            if context.current_topic:
                if ((context.current_topic == 'booking' and result.document_type in ['procedure', 'faq']) or
                    (context.current_topic == 'cancellation' and result.document_type in ['policy', 'procedure']) or
                    (context.current_topic == 'procedure' and result.document_type == 'procedure')):
                    context_boost += 0.15
            
            # Apply context boost to relevance score
            enhanced_score = min(1.0, result.relevance_score + context_boost)
            
            # Create enhanced result
            enhanced_result = SearchResult(
                document_id=result.document_id,
                section_id=result.section_id,
                content=result.content,
                relevance_score=enhanced_score,
                document_type=result.document_type,
                source_file=result.source_file,
                context_match=result.context_match,
                snippet=result.snippet,
                title=result.title,
                matched_terms=result.matched_terms,
                ranking_factors={**result.ranking_factors, 'context_boost': context_boost}
            )
            
            enhanced_results.append(enhanced_result)
        
        # Re-sort by enhanced scores
        enhanced_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return enhanced_results
    
    def _filter_for_new_topic(self, 
                            results: List[SearchResult], 
                            context: ConversationContext,
                            context_keywords: List[str]) -> List[SearchResult]:
        """Filter results for new topic questions."""
        # For new topics, apply lighter context filtering
        enhanced_results = []
        
        for result in results:
            context_boost = 0.0
            
            # Small boost for results that contain any context keywords
            content_lower = result.content.lower()
            context_matches = sum(1 for keyword in context_keywords 
                                if keyword.lower() in content_lower)
            if context_matches > 0:
                context_boost += min(0.1, context_matches * 0.05)
            
            # Apply minimal context boost
            enhanced_score = min(1.0, result.relevance_score + context_boost)
            
            # Create enhanced result
            enhanced_result = SearchResult(
                document_id=result.document_id,
                section_id=result.section_id,
                content=result.content,
                relevance_score=enhanced_score,
                document_type=result.document_type,
                source_file=result.source_file,
                context_match=result.context_match,
                snippet=result.snippet,
                title=result.title,
                matched_terms=result.matched_terms,
                ranking_factors={**result.ranking_factors, 'context_boost': context_boost}
            )
            
            enhanced_results.append(enhanced_result)
        
        # Re-sort by enhanced scores
        enhanced_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return enhanced_results

class ConversationContextManager:
    """Manages conversation contexts for multiple sessions."""
    
    def __init__(self):
        """Initialize conversation context manager."""
        self.contexts: Dict[str, ConversationContext] = {}
        self.context_filter = ContextualSearchFilter()
        logger.info("Conversation context manager initialized")
    
    def get_or_create_context(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one for session."""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(session_id=session_id)
        return self.contexts[session_id]
    
    def add_conversation_turn(self, 
                            session_id: str,
                            query: str,
                            intent: str,
                            response: str,
                            retrieved_documents: List[str],
                            confidence: float):
        """Add a conversation turn to the context."""
        context = self.get_or_create_context(session_id)
        
        # Extract context keywords from query
        context_keywords = self._extract_context_keywords(query, intent)
        
        turn = ConversationTurn(
            id=str(uuid.uuid4()),
            query=query,
            intent=intent,
            response=response,
            retrieved_documents=retrieved_documents,
            confidence=confidence,
            timestamp=datetime.now(),
            context_keywords=context_keywords
        )
        
        context.add_turn(turn)
    
    def _extract_context_keywords(self, query: str, intent: str) -> List[str]:
        """Extract keywords from query for context tracking."""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add intent as a keyword
        if intent != 'general':
            keywords.append(intent)
        
        return keywords[:10]  # Limit to top 10 keywords
    
    def apply_contextual_filtering(self, 
                                 session_id: str,
                                 results: List[SearchResult],
                                 query: str) -> List[SearchResult]:
        """Apply contextual filtering to search results."""
        context = self.get_or_create_context(session_id)
        return self.context_filter.apply_context_filtering(results, context, query)
    
    def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of conversation context."""
        if session_id not in self.contexts:
            return {"session_id": session_id, "turns": 0, "context": "No conversation history"}
        
        context = self.contexts[session_id]
        return {
            "session_id": session_id,
            "turns": len(context.turns),
            "current_topic": context.current_topic,
            "topic_keywords": context.topic_keywords,
            "last_accessed_documents": context.last_accessed_documents,
            "conversation_summary": context.get_conversation_summary(),
            "conversation_duration": (datetime.now() - context.conversation_start).total_seconds()
        }
    
    def cleanup_old_contexts(self, max_age_hours: int = 24):
        """Clean up old conversation contexts."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        contexts_to_remove = []
        for session_id, context in self.contexts.items():
            if context.conversation_start < cutoff_time:
                contexts_to_remove.append(session_id)
        
        for session_id in contexts_to_remove:
            del self.contexts[session_id]
        
        if contexts_to_remove:
            logger.info(f"Cleaned up {len(contexts_to_remove)} old conversation contexts")

class RankingAlgorithm:
    """Advanced ranking algorithm for search results."""
    
    def __init__(self):
        """Initialize ranking algorithm."""
        # Ranking weights
        self.weights = {
            'term_frequency': 0.25,
            'title_match': 0.20,
            'content_relevance': 0.20,
            'document_type_bonus': 0.10,
            'recency_bonus': 0.10,
            'completeness_bonus': 0.10,
            'source_authority': 0.05
        }
        
        # Document type priorities
        self.document_type_priority = {
            'faq': 1.0,
            'policy': 0.9,
            'procedure': 0.8,
            'manual': 0.7,
            'general': 0.6
        }
        
        logger.info("Ranking algorithm initialized")
    
    def calculate_term_frequency_score(self, content: str, query_terms: List[str]) -> float:
        """Calculate TF-IDF-like score for content."""
        if not query_terms:
            return 0.0
        
        content_lower = content.lower()
        content_words = re.findall(r'\b\w+\b', content_lower)
        total_words = len(content_words)
        
        if total_words == 0:
            return 0.0
        
        tf_score = 0.0
        for term in query_terms:
            term_count = content_lower.count(term.lower())
            if term_count > 0:
                # Term frequency
                tf = term_count / total_words
                # Simple IDF approximation (log of inverse frequency)
                idf = math.log(1 + (1 / (term_count / total_words)))
                tf_score += tf * idf
        
        return min(1.0, tf_score)
    
    def calculate_title_match_score(self, title: str, query_terms: List[str]) -> float:
        """Calculate how well the title matches query terms."""
        if not query_terms or not title:
            return 0.0
        
        title_lower = title.lower()
        matches = 0
        
        for term in query_terms:
            if term.lower() in title_lower:
                matches += 1
        
        return matches / len(query_terms)
    
    def calculate_content_relevance_score(self, content: str, query: str) -> float:
        """Calculate semantic relevance of content to query."""
        if not content or not query:
            return 0.0
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Check for exact phrase matches
        if query_lower in content_lower:
            return 1.0
        
        # Check for partial phrase matches
        query_words = query_lower.split()
        if len(query_words) > 1:
            for i in range(len(query_words) - 1):
                phrase = ' '.join(query_words[i:i+2])
                if phrase in content_lower:
                    return 0.8
        
        # Check for word proximity
        positions = []
        for word in query_words:
            word_positions = [m.start() for m in re.finditer(r'\b' + re.escape(word) + r'\b', content_lower)]
            if word_positions:
                positions.extend(word_positions)
        
        if len(positions) > 1:
            positions.sort()
            avg_distance = sum(positions[i+1] - positions[i] for i in range(len(positions)-1)) / (len(positions)-1)
            proximity_score = max(0, 1 - (avg_distance / 1000))  # Normalize by content length
            return proximity_score
        
        return 0.0
    
    def calculate_document_type_bonus(self, document_type: str, query_intent: str) -> float:
        """Calculate bonus based on document type and query intent."""
        base_score = self.document_type_priority.get(document_type, 0.5)
        
        # Intent-based bonuses
        intent_bonuses = {
            'booking': {'procedure': 0.2, 'faq': 0.1},
            'cancellation': {'policy': 0.2, 'faq': 0.1},
            'information': {'faq': 0.2, 'general': 0.1},
            'procedure': {'procedure': 0.3, 'manual': 0.2},
            'policy': {'policy': 0.3, 'faq': 0.1},
            'contact': {'faq': 0.2, 'general': 0.1}
        }
        
        bonus = intent_bonuses.get(query_intent, {}).get(document_type, 0.0)
        return min(1.0, base_score + bonus)
    
    def calculate_recency_bonus(self, created_at: datetime, updated_at: datetime) -> float:
        """Calculate bonus for recent content."""
        now = datetime.now()
        
        # Use the more recent of created_at or updated_at
        most_recent = max(created_at, updated_at)
        days_old = (now - most_recent).days
        
        # Exponential decay with half-life of 180 days
        if days_old <= 0:
            return 1.0
        
        return math.exp(-days_old / 180.0)
    
    def calculate_completeness_bonus(self, content: str, title: str) -> float:
        """Calculate bonus for complete, well-structured content."""
        if not content:
            return 0.0
        
        score = 0.0
        
        # Length bonus (not too short, not too long)
        content_length = len(content.split())
        if 50 <= content_length <= 500:
            score += 0.3
        elif 20 <= content_length < 50 or 500 < content_length <= 1000:
            score += 0.2
        elif content_length >= 20:
            score += 0.1
        
        # Structure bonus
        if title and title.strip():
            score += 0.2
        
        # Formatting bonus (presence of structure indicators)
        structure_indicators = ['\n\n', '1.', '2.', '•', '-', ':']
        structure_count = sum(1 for indicator in structure_indicators if indicator in content)
        score += min(0.3, structure_count * 0.1)
        
        # Question-answer format bonus
        if '?' in content and any(word in content.lower() for word in ['answer', 'response', 'solution']):
            score += 0.2
        
        return min(1.0, score)
    
    def calculate_source_authority_bonus(self, source_type: str, source_file: str) -> float:
        """Calculate bonus based on source authority."""
        # PDF sources generally more authoritative than JSON
        if source_type == 'pdf':
            return 1.0
        elif source_type == 'json':
            return 0.8
        
        return 0.5
    
    def rank_results(self, results: List[IndexerSearchResult], query: str, query_intent: str) -> List[SearchResult]:
        """
        Rank search results using multiple factors.
        
        Args:
            results: List of search results from indexer
            query: Original search query
            query_intent: Detected query intent
            
        Returns:
            List of ranked SearchResult objects
        """
        ranked_results = []
        
        for result in results:
            # Calculate individual ranking factors
            tf_score = self.calculate_term_frequency_score(result.content, result.matched_terms)
            title_score = self.calculate_title_match_score(result.title, result.matched_terms)
            relevance_score = self.calculate_content_relevance_score(result.content, query)
            doc_type_bonus = self.calculate_document_type_bonus(result.category, query_intent)
            
            # Parse dates for recency calculation
            try:
                created_at = datetime.fromisoformat(result.to_dict().get('created_at', datetime.now().isoformat()))
                updated_at = datetime.fromisoformat(result.to_dict().get('updated_at', datetime.now().isoformat()))
                recency_bonus = self.calculate_recency_bonus(created_at, updated_at)
            except:
                recency_bonus = 0.5
            
            completeness_bonus = self.calculate_completeness_bonus(result.content, result.title)
            authority_bonus = self.calculate_source_authority_bonus(result.source_type, result.source_file)
            
            # Calculate weighted final score
            ranking_factors = {
                'term_frequency': tf_score,
                'title_match': title_score,
                'content_relevance': relevance_score,
                'document_type_bonus': doc_type_bonus,
                'recency_bonus': recency_bonus,
                'completeness_bonus': completeness_bonus,
                'source_authority': authority_bonus
            }
            
            final_score = sum(
                self.weights[factor] * score 
                for factor, score in ranking_factors.items()
            )
            
            # Create enhanced search result
            enhanced_result = SearchResult(
                document_id=result.document_id or result.entry_id,
                section_id=result.section_id or result.entry_id,
                content=result.content,
                relevance_score=final_score,
                document_type=result.category,
                source_file=result.source_file,
                context_match=query,
                snippet=result.snippet,
                title=result.title,
                matched_terms=result.matched_terms,
                ranking_factors=ranking_factors
            )
            
            ranked_results.append(enhanced_result)
        
        # Sort by final relevance score
        ranked_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return ranked_results

class ResponseSynthesizer:
    """Synthesizes responses from retrieved content with source citations."""
    
    def __init__(self):
        """Initialize response synthesizer."""
        # Response templates for different query types
        self.response_templates = {
            'booking': "To {action}, follow these steps:\n{content}\n\nFor more information, refer to {sources}.",
            'cancellation': "Regarding {topic}:\n{content}\n\nThis information is based on {sources}.",
            'information': "Here's what I found about {topic}:\n{content}\n\nSource: {sources}",
            'procedure': "Here's how to {action}:\n{content}\n\nDetailed instructions can be found in {sources}.",
            'policy': "According to our policies:\n{content}\n\nFull policy details are available in {sources}.",
            'contact': "You can reach us through:\n{content}\n\nMore contact options are listed in {sources}.",
            'hours': "Our availability:\n{content}\n\nFor the most current information, check {sources}.",
            'cost': "Regarding pricing:\n{content}\n\nFor detailed pricing information, see {sources}.",
            'general': "{content}\n\nThis information comes from {sources}."
        }
        
        logger.info("Response synthesizer initialized")
    
    def synthesize_response(self, query: str, results: List[SearchResult], query_intent: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Synthesize a response from search results.
        
        Args:
            query: Original search query
            results: List of search results
            query_intent: Detected query intent
            
        Returns:
            Tuple of (synthesized_response, citations)
        """
        if not results:
            return "I couldn't find specific information about your question. Please try rephrasing your query or contact our support team for assistance.", []
        
        # Extract key information from top results
        synthesized_content = self._extract_and_combine_content(results, query)
        
        # Create citations
        citations = self._create_citations(results)
        
        # Format sources for response
        source_text = self._format_sources(results)
        
        # Extract action/topic from query for template
        action_topic = self._extract_action_topic(query, query_intent)
        
        # Select appropriate template
        template = self.response_templates.get(query_intent, self.response_templates['general'])
        
        # Format response using template
        if '{action}' in template:
            response = template.format(
                action=action_topic,
                content=synthesized_content,
                sources=source_text
            )
        elif '{topic}' in template:
            response = template.format(
                topic=action_topic,
                content=synthesized_content,
                sources=source_text
            )
        else:
            response = template.format(
                content=synthesized_content,
                sources=source_text
            )
        
        return response, citations
    
    def _extract_and_combine_content(self, results: List[SearchResult], query: str) -> str:
        """Extract and combine relevant content from search results."""
        if not results:
            return ""
        
        # Use the top result as primary content
        primary_result = results[0]
        
        # For FAQ results, extract Q&A format
        if primary_result.document_type == 'faqs' and 'Answer:' in primary_result.content:
            answer_part = primary_result.content.split('Answer:', 1)[1].strip()
            combined_content = answer_part
        else:
            combined_content = primary_result.content.strip()
        
        # Add supplementary information from other high-scoring results
        if len(results) > 1:
            supplementary_info = []
            
            for result in results[1:3]:  # Use up to 2 additional results
                if result.relevance_score > 0.5:  # Only use high-relevance results
                    # Extract key sentences that add new information
                    additional_info = self._extract_key_sentences(result.content, query)
                    if additional_info and additional_info not in combined_content:
                        supplementary_info.append(additional_info)
            
            if supplementary_info:
                combined_content += "\n\nAdditional information:\n" + "\n".join(f"• {info}" for info in supplementary_info)
        
        return combined_content
    
    def _extract_key_sentences(self, content: str, query: str) -> str:
        """Extract key sentences from content that are relevant to the query."""
        sentences = re.split(r'[.!?]+', content)
        query_words = set(query.lower().split())
        
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            # Score sentence based on query word overlap
            sentence_words = set(sentence.lower().split())
            overlap = len(query_words.intersection(sentence_words))
            score = overlap / len(query_words) if query_words else 0
            
            if score > best_score and score > 0.2:  # Minimum relevance threshold
                best_score = score
                best_sentence = sentence
        
        return best_sentence
    
    def _create_citations(self, results: List[SearchResult]) -> List[Dict[str, Any]]:
        """Create citation information for sources."""
        citations = []
        
        for i, result in enumerate(results, 1):
            citation = {
                "id": i,
                "title": result.title,
                "source_file": result.source_file,
                "document_type": result.document_type,
                "relevance_score": result.relevance_score,
                "snippet": result.snippet,
                "document_id": result.document_id,
                "section_id": result.section_id
            }
            citations.append(citation)
        
        return citations
    
    def _format_sources(self, results: List[SearchResult]) -> str:
        """Format source information for inclusion in response."""
        if not results:
            return "our knowledge base"
        
        # Group by source file to avoid repetition
        source_files = []
        seen_files = set()
        
        for result in results:
            if result.source_file not in seen_files:
                source_files.append(result.source_file)
                seen_files.add(result.source_file)
        
        if len(source_files) == 1:
            return source_files[0]
        elif len(source_files) == 2:
            return f"{source_files[0]} and {source_files[1]}"
        else:
            return f"{', '.join(source_files[:-1])}, and {source_files[-1]}"
    
    def _extract_action_topic(self, query: str, query_intent: str) -> str:
        """Extract the main action or topic from the query."""
        query_lower = query.lower()
        
        # Intent-specific extraction patterns
        if query_intent == 'booking':
            if 'appointment' in query_lower:
                return 'book an appointment'
            elif 'schedule' in query_lower:
                return 'schedule a service'
            else:
                return 'make a booking'
        
        elif query_intent == 'cancellation':
            return 'cancellation policy'
        
        elif query_intent == 'procedure':
            # Extract the action after "how to" or "how do I"
            how_match = re.search(r'how\s+(?:do\s+i\s+|to\s+)?(.+?)(?:\?|$)', query_lower)
            if how_match:
                return how_match.group(1).strip()
            else:
                return 'complete this process'
        
        elif query_intent == 'contact':
            return 'contact information'
        
        elif query_intent == 'hours':
            return 'business hours'
        
        elif query_intent == 'policy':
            # Extract policy type
            policy_match = re.search(r'(privacy|cancellation|refund|terms|data)\s+policy', query_lower)
            if policy_match:
                return f'{policy_match.group(1)} policy'
            else:
                return 'our policies'
        
        else:
            # Extract main topic (usually the last few words before question mark)
            topic_match = re.search(r'(?:what|about|regarding)\s+(.+?)(?:\?|$)', query_lower)
            if topic_match:
                return topic_match.group(1).strip()
            else:
                return 'your question'
    
    def format_response_with_citations(self, response: str, citations: List[Dict[str, Any]]) -> str:
        """Format response with numbered citations."""
        if not citations:
            return response
        
        # Add citation numbers to the response
        formatted_response = response
        
        # Add citations section
        citations_text = "\n\nSources:\n"
        for citation in citations:
            citations_text += f"[{citation['id']}] {citation['title']} ({citation['source_file']})\n"
        
        return formatted_response + citations_text

class SimpleRAGEngine:
    """
    Simple RAG engine that implements text-based search without vector databases.
    """
    
    def __init__(self, knowledge_base: UnifiedKnowledgeBase):
        """
        Initialize simple RAG engine.
        
        Args:
            knowledge_base: Unified knowledge base instance
        """
        self.knowledge_base = knowledge_base
        self.indexer = KnowledgeIndexer(knowledge_base)
        self.query_processor = QueryProcessor()
        self.ranking_algorithm = RankingAlgorithm()
        self.response_synthesizer = ResponseSynthesizer()
        self.context_manager = ConversationContextManager()
        
        # Initialize domain expertise engine
        self.domain_expertise_engine = DomainExpertiseEngine()
        
        # Track last search sources for learning engine
        self.last_search_sources = []
        
        # Build or load index
        if not self.indexer._load_index():
            logger.info("Building new search index...")
            self.indexer.build_index()
        
        logger.info("Simple RAG engine initialized with context-aware search and domain expertise")
    
    async def search_and_generate(self, query: str, context: str = "", max_results: int = 10, session_id: str = "default") -> RAGResponse:
        """
        Search knowledge base and prepare response data with context-aware search.
        
        Args:
            query: Search query
            context: Additional context for search
            max_results: Maximum number of results to return
            session_id: Session ID for conversation context tracking
            
        Returns:
            RAG response with search results and metadata
        """
        start_time = datetime.now()
        
        # Process and expand query
        expanded_terms = self.query_processor.expand_query(query)
        query_intent = self.query_processor.extract_intent(query)
        
        # Get conversation context
        conversation_context = self.context_manager.get_or_create_context(session_id)
        context_summary = conversation_context.get_conversation_summary()
        is_follow_up = conversation_context.is_follow_up_question(query)
        
        logger.info(f"Processing query: '{query}' with intent: {query_intent}")
        logger.info(f"Session: {session_id}, Follow-up: {is_follow_up}")
        logger.info(f"Expanded terms: {expanded_terms}")
        if context_summary:
            logger.info(f"Conversation context: {context_summary}")
        
        # Enhance search query with context if it's a follow-up
        if is_follow_up and context_summary:
            context_keywords = conversation_context.get_context_keywords()
            enhanced_terms = expanded_terms + context_keywords[:5]  # Add top 5 context keywords
            search_query = ' '.join(enhanced_terms)
            logger.info(f"Enhanced search with context keywords: {context_keywords[:5]}")
        else:
            search_query = ' '.join(expanded_terms)
        
        # Search using enhanced query
        raw_results = self.indexer.search(search_query, max_results=max_results * 2)  # Get more for better ranking
        
        # Rank results using advanced algorithm
        ranked_results = self.ranking_algorithm.rank_results(raw_results, query, query_intent)
        
        # Apply contextual filtering
        context_filtered_results = self.context_manager.apply_contextual_filtering(
            session_id, ranked_results, query
        )
        
        # Limit to requested number of results
        final_results = context_filtered_results[:max_results]
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(final_results, query)
        
        # Prepare sources list
        sources = [result.source_file for result in final_results]
        retrieved_documents = [result.document_id for result in final_results if result.document_id]
        
        # Track search sources for learning engine
        self.last_search_sources = list(set([result.source_file for result in raw_results]))
        if not self.last_search_sources:
            self.last_search_sources = ["PDF Documents", "JSON Knowledge Base"]
        
        # Synthesize response from search results
        synthesized_answer, citations = self.response_synthesizer.synthesize_response(
            query, final_results, query_intent
        )
        
        # Apply domain expertise adaptation
        domain_response = self._apply_domain_expertise(
            query=query,
            rag_response=synthesized_answer,
            search_results=final_results,
            conversation_context=conversation_context
        )
        
        # Use domain-adapted response if available
        final_answer = domain_response.adapted_response if domain_response else synthesized_answer
        
        # Add conversation turn to context
        self.context_manager.add_conversation_turn(
            session_id=session_id,
            query=query,
            intent=query_intent,
            response=final_answer,
            retrieved_documents=retrieved_documents,
            confidence=confidence
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create RAG response with domain expertise information
        response = RAGResponse(
            answer=final_answer,
            sources=sources,
            confidence=confidence,
            context_used=context_summary,
            retrieved_content=final_results,
            processing_time=processing_time,
            search_query=search_query,
            total_results_found=len(raw_results),
            citations=citations,
            synthesis_method="context_aware_template_with_domain_expertise"
        )
        
        # Add domain expertise metadata to response if available
        if domain_response:
            response.domain_expertise = {
                "detected_domain": domain_response.domain.value,
                "terminology_used": domain_response.terminology_used,
                "clarifying_questions": domain_response.clarifying_questions,
                "expertise_indicators": domain_response.expertise_indicators,
                "document_sources_prioritized": domain_response.document_sources_prioritized
            }
            
            # Use the domain-adapted response instead of the original
            response.answer = domain_response.adapted_response
        
        logger.info(f"Context-aware RAG search completed: {len(final_results)} results, confidence: {confidence:.3f}")
        logger.info(f"Response synthesized using {query_intent} template with context awareness")
        
        return response
    
    def _calculate_confidence(self, results: List[SearchResult], query: str) -> float:
        """
        Calculate overall confidence in search results.
        
        Args:
            results: List of search results
            query: Original query
            
        Returns:
            Confidence score between 0 and 1
        """
        if not results:
            return 0.0
        
        # Base confidence from top result
        top_score = results[0].relevance_score
        
        # Boost confidence if multiple results are consistent
        if len(results) > 1:
            score_consistency = 1.0 - (results[0].relevance_score - results[1].relevance_score)
            top_score = min(1.0, top_score + (score_consistency * 0.1))
        
        # Boost confidence for exact matches
        query_lower = query.lower()
        for result in results[:3]:  # Check top 3 results
            if query_lower in result.content.lower():
                top_score = min(1.0, top_score + 0.1)
                break
        
        return top_score
    
    def _apply_domain_expertise(self, query: str, rag_response: str, 
                              search_results: List[SearchResult],
                              conversation_context: ConversationContext) -> Optional[DomainResponse]:
        """
        Apply domain expertise adaptation to RAG response.
        
        Args:
            query: User query
            rag_response: Original RAG response
            search_results: Search results used for response
            conversation_context: Conversation context
            
        Returns:
            Domain-adapted response or None if no adaptation needed
        """
        try:
            # Extract document types and contents from search results
            document_types = [result.document_type for result in search_results]
            document_contents = [result.content for result in search_results]
            document_sources = [result.source_file for result in search_results]
            
            # Get conversation history for domain detection
            conversation_history = []
            if conversation_context and conversation_context.turns:
                recent_turns = list(conversation_context.turns)[-3:]  # Last 3 turns
                conversation_history = [turn.query for turn in recent_turns]
            
            # Apply domain expertise
            domain_response = self.domain_expertise_engine.process_query_with_domain_expertise(
                query=query,
                rag_response=rag_response,
                document_types=document_types,
                document_contents=document_contents,
                document_sources=document_sources,
                conversation_history=conversation_history
            )
            
            return domain_response
            
        except Exception as e:
            logger.error(f"Error applying domain expertise: {e}")
            return None
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions for partial query."""
        return self.indexer.get_suggestions(partial_query)
    
    def get_related_terms(self, term: str) -> List[str]:
        """Get terms related to the given term."""
        return self.indexer.get_related_terms(term)
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        index_stats = self.indexer.get_index_stats()
        
        return {
            "engine_type": "Simple RAG (Text-based)",
            "index_stats": index_stats,
            "ranking_weights": self.ranking_algorithm.weights,
            "document_type_priorities": self.ranking_algorithm.document_type_priority,
            "query_expansions": len(self.query_processor.domain_expansions)
        }
    
    def format_response_with_citations(self, response: RAGResponse) -> str:
        """
        Format RAG response with citations for display.
        
        Args:
            response: RAG response object
            
        Returns:
            Formatted response string with citations
        """
        return self.response_synthesizer.format_response_with_citations(
            response.answer, response.citations
        )
    
    def get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get conversation context summary for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Context summary dictionary
        """
        return self.context_manager.get_context_summary(session_id)
    
    def cleanup_old_conversations(self, max_age_hours: int = 24):
        """
        Clean up old conversation contexts.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        self.context_manager.cleanup_old_contexts(max_age_hours)

# Example usage and testing
def test_simple_rag_engine():
    """Test the simple RAG engine with context-aware search."""
    print("Testing Simple RAG Engine with Context-Aware Search")
    print("=" * 60)
    
    # Initialize knowledge base and RAG engine
    kb = UnifiedKnowledgeBase()
    kb.load_all_knowledge()
    
    rag_engine = SimpleRAGEngine(kb)
    
    # Get engine statistics
    stats = rag_engine.get_engine_stats()
    print("Engine Statistics:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    
    # Test context-aware conversation flow
    print("\n" + "=" * 60)
    print("CONTEXT-AWARE CONVERSATION SIMULATION")
    print("=" * 60)
    
    import asyncio
    
    # Simulate a conversation with context
    session_id = "test_session_001"
    
    conversation_flow = [
        "How do I book an appointment?",
        "What about cancelling it?",  # Follow-up question
        "What are the fees for this?",  # Another follow-up
        "What services do you offer?",  # New topic
        "How can I contact support about these services?",  # Follow-up to new topic
        "Is my data secure when I use the app?"  # Another new topic
    ]
    
    for i, query in enumerate(conversation_flow, 1):
        print(f"\n--- Turn {i} ---")
        print(f"Query: '{query}'")
        
        # Get conversation context before processing
        context_before = rag_engine.get_conversation_context(session_id)
        print(f"Context before: {context_before['turns']} turns, Topic: {context_before.get('current_topic', 'None')}")
        
        # Process query with context
        response = asyncio.run(rag_engine.search_and_generate(
            query, 
            session_id=session_id, 
            max_results=3
        ))
        
        print(f"Confidence: {response.confidence:.3f}")
        print(f"Context used: {response.context_used}")
        print(f"Synthesis method: {response.synthesis_method}")
        
        # Show synthesized answer (truncated)
        print(f"Answer: {response.answer[:200]}...")
        
        # Show context boost information for top result
        if response.retrieved_content:
            top_result = response.retrieved_content[0]
            if 'context_boost' in top_result.ranking_factors:
                print(f"Context boost applied: {top_result.ranking_factors['context_boost']:.3f}")
        
        # Get conversation context after processing
        context_after = rag_engine.get_conversation_context(session_id)
        print(f"Context after: {context_after['turns']} turns, Topic: {context_after.get('current_topic', 'None')}")
        if context_after['topic_keywords']:
            print(f"Topic keywords: {context_after['topic_keywords'][:5]}")
        
        print("-" * 40)
    
    # Show final conversation summary
    print(f"\n--- Final Conversation Summary ---")
    final_context = rag_engine.get_conversation_context(session_id)
    print(f"Session ID: {final_context['session_id']}")
    print(f"Total turns: {final_context['turns']}")
    print(f"Current topic: {final_context.get('current_topic', 'None')}")
    print(f"Conversation duration: {final_context['conversation_duration']:.1f} seconds")
    print(f"Conversation summary: {final_context['conversation_summary']}")
    print(f"Last accessed documents: {final_context['last_accessed_documents'][:3]}")
    
    # Test individual queries without context
    print("\n" + "=" * 60)
    print("INDIVIDUAL QUERIES (No Context)")
    print("=" * 60)
    
    test_queries = [
        "What are your business hours?",
        "How do I upload a prescription?",
        "Who can use the CareSetu app?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        # Use different session for no context
        response = asyncio.run(rag_engine.search_and_generate(
            query, 
            session_id="no_context_session", 
            max_results=3
        ))
        
        print(f"  Confidence: {response.confidence:.3f}")
        print(f"  Processing time: {response.processing_time:.3f}s")
        print(f"  Synthesis method: {response.synthesis_method}")
        
        # Show top result
        if response.retrieved_content:
            top_result = response.retrieved_content[0]
            print(f"  Top result: [{top_result.document_type}] {top_result.title}")
            print(f"  Relevance: {top_result.relevance_score:.3f}")
    
    # Test suggestions
    print("\n" + "=" * 60)
    print("SEARCH SUGGESTIONS")
    print("=" * 60)
    partial_queries = ["app", "pol", "can", "sup"]
    for partial in partial_queries:
        suggestions = rag_engine.get_search_suggestions(partial)
        print(f"  '{partial}' -> {suggestions[:5]}")
    
    # Cleanup test
    print(f"\n--- Cleanup Test ---")
    print(f"Contexts before cleanup: {len(rag_engine.context_manager.contexts)}")
    rag_engine.cleanup_old_conversations(max_age_hours=0)  # Force cleanup
    print(f"Contexts after cleanup: {len(rag_engine.context_manager.contexts)}")

if __name__ == "__main__":
    test_simple_rag_engine()

