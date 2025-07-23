"""
Conversation Learning System
Implements learning from user conversations to continuously improve knowledge base
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import re

logger = logging.getLogger(__name__)

class LearningType(Enum):
    """Types of learning from conversations."""
    KNOWLEDGE_GAP_FILL = "knowledge_gap_fill"
    USER_CORRECTION = "user_correction"
    NEW_INFORMATION = "new_information"
    CLARIFICATION = "clarification"
    CONTEXT_ENHANCEMENT = "context_enhancement"

class ConfidenceLevel(Enum):
    """Confidence levels for learned information."""
    HIGH = "high"      # User explicitly taught or corrected
    MEDIUM = "medium"  # Inferred from conversation context
    LOW = "low"        # Uncertain or needs validation

@dataclass
class LearnedInformation:
    """Represents information learned from conversations."""
    id: str
    content: str
    topic: str
    learning_type: LearningType
    confidence_level: ConfidenceLevel
    source_session_id: str
    source_conversation_turn: int
    user_query: str
    agent_response: str
    timestamp: datetime
    validation_count: int = 0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    tags: List[str] = None
    related_documents: List[str] = None
    conflicts_with_pdf: bool = False
    pdf_conflict_details: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.related_documents is None:
            self.related_documents = []

@dataclass
class KnowledgeGap:
    """Represents identified knowledge gaps."""
    id: str
    query: str
    topic: str
    session_id: str
    timestamp: datetime
    attempted_sources: List[str]
    gap_type: str  # "missing_info", "incomplete_info", "outdated_info"
    user_provided_info: Optional[str] = None
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

class ConversationLearningEngine:
    """Engine for learning from conversations and managing learned knowledge."""
    
    def __init__(self, storage_path: str = "learned_knowledge"):
        """
        Initialize conversation learning engine.
        
        Args:
            storage_path: Path to store learned knowledge
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Storage files
        self.learned_info_file = self.storage_path / "learned_information.json"
        self.knowledge_gaps_file = self.storage_path / "knowledge_gaps.json"
        self.learning_stats_file = self.storage_path / "learning_statistics.json"
        
        # In-memory storage
        self.learned_information: Dict[str, LearnedInformation] = {}
        self.knowledge_gaps: Dict[str, KnowledgeGap] = {}
        self.learning_statistics = {
            "total_learned_items": 0,
            "total_knowledge_gaps": 0,
            "successful_applications": 0,
            "conflict_resolutions": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        # Learning patterns for detecting user-provided information
        self.learning_patterns = {
            "explicit_teaching": [
                r"actually,?\s+(.+)",
                r"let me tell you,?\s+(.+)",
                r"the correct (answer|information) is\s+(.+)",
                r"i should mention that\s+(.+)",
                r"for your information,?\s+(.+)"
            ],
            "corrections": [
                r"no,?\s+(.+)",
                r"that's not right,?\s+(.+)",
                r"incorrect,?\s+(.+)",
                r"wrong,?\s+(.+)",
                r"actually it's\s+(.+)"
            ],
            "additional_info": [
                r"also,?\s+(.+)",
                r"additionally,?\s+(.+)",
                r"furthermore,?\s+(.+)",
                r"by the way,?\s+(.+)",
                r"i forgot to mention\s+(.+)"
            ],
            "clarifications": [
                r"what i meant was\s+(.+)",
                r"to clarify,?\s+(.+)",
                r"let me be more specific,?\s+(.+)",
                r"in other words,?\s+(.+)"
            ]
        }
        
        # Load existing data
        self._load_learned_data()
        
        logger.info(f"Conversation learning engine initialized with {len(self.learned_information)} learned items")
    
    def _load_learned_data(self):
        """Load learned information from storage."""
        try:
            # Load learned information
            if self.learned_info_file.exists():
                with open(self.learned_info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        # Convert datetime strings back to datetime objects
                        item_data['timestamp'] = datetime.fromisoformat(item_data['timestamp'])
                        if item_data.get('last_used'):
                            item_data['last_used'] = datetime.fromisoformat(item_data['last_used'])
                        
                        # Convert enums
                        item_data['learning_type'] = LearningType(item_data['learning_type'])
                        item_data['confidence_level'] = ConfidenceLevel(item_data['confidence_level'])
                        
                        learned_info = LearnedInformation(**item_data)
                        self.learned_information[learned_info.id] = learned_info
            
            # Load knowledge gaps
            if self.knowledge_gaps_file.exists():
                with open(self.knowledge_gaps_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for gap_data in data:
                        # Convert datetime strings
                        gap_data['timestamp'] = datetime.fromisoformat(gap_data['timestamp'])
                        if gap_data.get('resolution_timestamp'):
                            gap_data['resolution_timestamp'] = datetime.fromisoformat(gap_data['resolution_timestamp'])
                        
                        gap = KnowledgeGap(**gap_data)
                        self.knowledge_gaps[gap.id] = gap
            
            # Load statistics
            if self.learning_stats_file.exists():
                with open(self.learning_stats_file, 'r', encoding='utf-8') as f:
                    self.learning_statistics = json.load(f)
            
        except Exception as e:
            logger.error(f"Error loading learned data: {e}")
    
    def _save_learned_data(self):
        """Save learned information to storage."""
        try:
            # Save learned information
            learned_data = []
            for learned_info in self.learned_information.values():
                data = asdict(learned_info)
                # Convert datetime objects to strings
                data['timestamp'] = learned_info.timestamp.isoformat()
                if learned_info.last_used:
                    data['last_used'] = learned_info.last_used.isoformat()
                else:
                    data['last_used'] = None
                
                # Convert enums to strings
                data['learning_type'] = learned_info.learning_type.value
                data['confidence_level'] = learned_info.confidence_level.value
                
                learned_data.append(data)
            
            with open(self.learned_info_file, 'w', encoding='utf-8') as f:
                json.dump(learned_data, f, indent=2, ensure_ascii=False)
            
            # Save knowledge gaps
            gaps_data = []
            for gap in self.knowledge_gaps.values():
                data = asdict(gap)
                data['timestamp'] = gap.timestamp.isoformat()
                if gap.resolution_timestamp:
                    data['resolution_timestamp'] = gap.resolution_timestamp.isoformat()
                else:
                    data['resolution_timestamp'] = None
                gaps_data.append(data)
            
            with open(self.knowledge_gaps_file, 'w', encoding='utf-8') as f:
                json.dump(gaps_data, f, indent=2, ensure_ascii=False)
            
            # Save statistics
            self.learning_statistics['last_updated'] = datetime.now().isoformat()
            with open(self.learning_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_statistics, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error saving learned data: {e}")
    
    def identify_knowledge_gap(self, 
                             user_query: str,
                             attempted_sources: List[str],
                             session_id: str,
                             topic: str = None) -> Optional[KnowledgeGap]:
        """
        Identify a knowledge gap when no relevant information is found.
        
        Args:
            user_query: User's query that couldn't be answered
            attempted_sources: Sources that were searched but didn't contain relevant info
            session_id: Current session ID
            topic: Detected topic/intent
            
        Returns:
            KnowledgeGap object if gap is identified
        """
        # Determine gap type based on query and sources
        gap_type = self._classify_knowledge_gap(user_query, attempted_sources)
        
        # Create knowledge gap
        gap = KnowledgeGap(
            id=str(uuid.uuid4()),
            query=user_query,
            topic=topic or "general",
            session_id=session_id,
            timestamp=datetime.now(),
            attempted_sources=attempted_sources,
            gap_type=gap_type
        )
        
        self.knowledge_gaps[gap.id] = gap
        self.learning_statistics['total_knowledge_gaps'] += 1
        
        logger.info(f"Identified knowledge gap: {gap.topic} - {gap.gap_type}")
        self._save_learned_data()
        
        return gap
    
    def _classify_knowledge_gap(self, query: str, attempted_sources: List[str]) -> str:
        """Classify the type of knowledge gap."""
        query_lower = query.lower()
        
        # Check for specific gap indicators
        if any(word in query_lower for word in ['new', 'recent', 'latest', 'updated']):
            return "outdated_info"
        elif any(word in query_lower for word in ['how', 'steps', 'process', 'procedure']):
            return "incomplete_info"
        else:
            return "missing_info"
    
    def detect_user_learning_opportunity(self, 
                                       user_message: str,
                                       conversation_context: Dict[str, Any]) -> Optional[Tuple[LearningType, str]]:
        """
        Detect when user is providing information that could be learned.
        
        Args:
            user_message: User's message
            conversation_context: Context from conversation
            
        Returns:
            Tuple of (LearningType, extracted_content) if learning opportunity detected
        """
        user_message_lower = user_message.lower()
        
        # Check each learning pattern type
        for learning_type_name, patterns in self.learning_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, user_message_lower, re.IGNORECASE)
                if match:
                    # Extract the informational content
                    if match.groups():
                        content = match.group(1).strip()
                    else:
                        content = user_message.strip()
                    
                    # Map pattern type to LearningType enum
                    learning_type_map = {
                        "explicit_teaching": LearningType.NEW_INFORMATION,
                        "corrections": LearningType.USER_CORRECTION,
                        "additional_info": LearningType.CONTEXT_ENHANCEMENT,
                        "clarifications": LearningType.CLARIFICATION
                    }
                    
                    learning_type = learning_type_map.get(learning_type_name, LearningType.NEW_INFORMATION)
                    
                    # Validate that content is substantial
                    if len(content.split()) >= 3:  # At least 3 words
                        return learning_type, content
        
        # Check for implicit learning opportunities
        if self._is_informative_statement(user_message):
            return LearningType.NEW_INFORMATION, user_message.strip()
        
        return None
    
    def _is_informative_statement(self, message: str) -> bool:
        """Check if message contains informative content worth learning."""
        message_lower = message.lower()
        
        # Indicators of informative content
        informative_indicators = [
            'the reason is', 'because', 'due to', 'caused by',
            'the process is', 'you need to', 'it works by',
            'the policy states', 'according to', 'the rule is',
            'typically', 'usually', 'normally', 'generally',
            'in my experience', 'i found that', 'what works is'
        ]
        
        # Check for informative patterns
        has_informative_pattern = any(indicator in message_lower for indicator in informative_indicators)
        
        # Check message length (substantial content)
        is_substantial = len(message.split()) >= 10
        
        # Check for question format (less likely to be informative)
        is_question = message.strip().endswith('?') or message_lower.startswith(('what', 'how', 'when', 'where', 'why', 'who'))
        
        return has_informative_pattern and is_substantial and not is_question
    
    def store_learned_information(self,
                                content: str,
                                learning_type: LearningType,
                                session_id: str,
                                conversation_turn: int,
                                user_query: str,
                                agent_response: str,
                                topic: str = None,
                                confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM,
                                related_documents: List[str] = None) -> LearnedInformation:
        """
        Store learned information from conversation.
        
        Args:
            content: The learned content
            learning_type: Type of learning
            session_id: Session where learning occurred
            conversation_turn: Turn number in conversation
            user_query: User's original query
            agent_response: Agent's response
            topic: Topic/intent of the learning
            confidence_level: Confidence in the learned information
            related_documents: Documents related to this learning
            
        Returns:
            LearnedInformation object
        """
        # Generate tags from content
        tags = self._extract_tags_from_content(content, topic)
        
        learned_info = LearnedInformation(
            id=str(uuid.uuid4()),
            content=content,
            topic=topic or "general",
            learning_type=learning_type,
            confidence_level=confidence_level,
            source_session_id=session_id,
            source_conversation_turn=conversation_turn,
            user_query=user_query,
            agent_response=agent_response,
            timestamp=datetime.now(),
            tags=tags,
            related_documents=related_documents or []
        )
        
        self.learned_information[learned_info.id] = learned_info
        self.learning_statistics['total_learned_items'] += 1
        
        logger.info(f"Stored learned information: {learning_type.value} - {topic}")
        self._save_learned_data()
        
        return learned_info
    
    def _extract_tags_from_content(self, content: str, topic: str = None) -> List[str]:
        """Extract relevant tags from learned content."""
        tags = []
        
        # Add topic as tag
        if topic:
            tags.append(topic)
        
        # Extract key terms (nouns and important words)
        content_lower = content.lower()
        
        # Domain-specific keywords
        domain_keywords = {
            'healthcare': ['patient', 'doctor', 'medical', 'health', 'treatment', 'diagnosis', 'medication'],
            'appointment': ['booking', 'schedule', 'calendar', 'time', 'date', 'availability'],
            'billing': ['payment', 'cost', 'price', 'invoice', 'charge', 'fee', 'billing'],
            'policy': ['rule', 'guideline', 'procedure', 'regulation', 'policy', 'requirement'],
            'technical': ['system', 'error', 'bug', 'issue', 'problem', 'solution', 'fix']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(domain)
        
        # Extract specific terms (simple keyword extraction)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content)  # Words with 4+ characters
        important_words = [word.lower() for word in words if word.lower() not in {
            'that', 'this', 'with', 'from', 'they', 'have', 'been', 'were', 'will', 'would', 'could', 'should'
        }]
        
        # Add most frequent important words as tags
        word_freq = {}
        for word in important_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Add top 3 most frequent words as tags
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        tags.extend([word for word, freq in top_words if freq > 1])
        
        return list(set(tags))  # Remove duplicates
    
    def search_learned_information(self, 
                                 query: str,
                                 topic: str = None,
                                 min_confidence: ConfidenceLevel = ConfidenceLevel.LOW) -> List[LearnedInformation]:
        """
        Search for relevant learned information.
        
        Args:
            query: Search query
            topic: Topic filter
            min_confidence: Minimum confidence level
            
        Returns:
            List of relevant learned information
        """
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        relevant_items = []
        confidence_order = {ConfidenceLevel.HIGH: 3, ConfidenceLevel.MEDIUM: 2, ConfidenceLevel.LOW: 1}
        min_confidence_value = confidence_order[min_confidence]
        
        for learned_info in self.learned_information.values():
            # Filter by confidence level
            if confidence_order[learned_info.confidence_level] < min_confidence_value:
                continue
            
            # Filter by topic if specified
            if topic and learned_info.topic != topic:
                continue
            
            # Calculate relevance score
            relevance_score = self._calculate_learned_info_relevance(learned_info, query_words, query_lower)
            
            if relevance_score > 0.1:  # Minimum relevance threshold
                learned_info.relevance_score = relevance_score  # Add score for sorting
                relevant_items.append(learned_info)
        
        # Sort by relevance score (highest first)
        relevant_items.sort(key=lambda x: getattr(x, 'relevance_score', 0), reverse=True)
        
        return relevant_items
    
    def _calculate_learned_info_relevance(self, 
                                        learned_info: LearnedInformation,
                                        query_words: set,
                                        query_lower: str) -> float:
        """Calculate relevance score for learned information."""
        score = 0.0
        
        # Content matching
        content_lower = learned_info.content.lower()
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        
        # Word overlap score
        word_overlap = len(query_words.intersection(content_words))
        if word_overlap > 0:
            score += (word_overlap / len(query_words)) * 0.4
        
        # Exact phrase matching
        if query_lower in content_lower:
            score += 0.3
        
        # Tag matching
        tag_matches = sum(1 for tag in learned_info.tags if tag.lower() in query_lower)
        if tag_matches > 0:
            score += min(0.2, tag_matches * 0.1)
        
        # Topic matching
        if learned_info.topic.lower() in query_lower:
            score += 0.1
        
        # Confidence boost
        confidence_boost = {
            ConfidenceLevel.HIGH: 0.2,
            ConfidenceLevel.MEDIUM: 0.1,
            ConfidenceLevel.LOW: 0.0
        }
        score += confidence_boost[learned_info.confidence_level]
        
        # Usage frequency boost (more used = more reliable)
        if learned_info.usage_count > 0:
            score += min(0.1, learned_info.usage_count * 0.02)
        
        return min(1.0, score)
    
    def check_pdf_conflict(self, 
                         learned_info: LearnedInformation,
                         pdf_content: str) -> Tuple[bool, Optional[str]]:
        """
        Check if learned information conflicts with PDF content.
        
        Args:
            learned_info: Learned information to check
            pdf_content: Relevant PDF content
            
        Returns:
            Tuple of (has_conflict, conflict_description)
        """
        if not pdf_content:
            return False, None
        
        learned_content_lower = learned_info.content.lower()
        pdf_content_lower = pdf_content.lower()
        
        # Simple conflict detection patterns
        conflict_patterns = [
            (r'not\s+(.+)', r'(.+)'),  # "not X" vs "X"
            (r'cannot\s+(.+)', r'can\s+(.+)'),  # "cannot do" vs "can do"
            (r'(\d+)\s*(hours?|days?|minutes?)', r'(\d+)\s*(hours?|days?|minutes?)'),  # Different time values
            (r'(\$\d+)', r'(\$\d+)'),  # Different price values
        ]
        
        # Check for direct contradictions
        for neg_pattern, pos_pattern in conflict_patterns:
            neg_match = re.search(neg_pattern, learned_content_lower)
            pos_match = re.search(pos_pattern, pdf_content_lower)
            
            if neg_match and pos_match:
                return True, f"Learned info says '{neg_match.group()}' but PDF says '{pos_match.group()}'"
        
        # Check for different factual claims about the same topic
        # This is a simplified approach - in practice, you'd want more sophisticated NLP
        key_terms = re.findall(r'\b(?:cost|price|time|hours|days|policy|procedure)\b', learned_content_lower)
        
        for term in key_terms:
            # Look for sentences containing the same key term in both contents
            learned_sentences = [s.strip() for s in learned_info.content.split('.') if term in s.lower()]
            pdf_sentences = [s.strip() for s in pdf_content.split('.') if term in s.lower()]
            
            if learned_sentences and pdf_sentences:
                # Simple heuristic: if they contain different numbers, might be a conflict
                learned_numbers = re.findall(r'\d+', ' '.join(learned_sentences))
                pdf_numbers = re.findall(r'\d+', ' '.join(pdf_sentences))
                
                if learned_numbers and pdf_numbers and set(learned_numbers) != set(pdf_numbers):
                    return True, f"Different {term} values: learned='{learned_numbers}' vs PDF='{pdf_numbers}'"
        
        return False, None
    
    def mark_learned_info_used(self, learned_info_id: str):
        """Mark learned information as used in a response."""
        if learned_info_id in self.learned_information:
            learned_info = self.learned_information[learned_info_id]
            learned_info.usage_count += 1
            learned_info.last_used = datetime.now()
            
            self.learning_statistics['successful_applications'] += 1
            self._save_learned_data()
            
            logger.info(f"Marked learned info as used: {learned_info_id} (usage count: {learned_info.usage_count})")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about the learning system."""
        stats = self.learning_statistics.copy()
        
        # Add current counts
        stats.update({
            "current_learned_items": len(self.learned_information),
            "current_knowledge_gaps": len([g for g in self.knowledge_gaps.values() if not g.resolved]),
            "resolved_knowledge_gaps": len([g for g in self.knowledge_gaps.values() if g.resolved]),
            "high_confidence_items": len([l for l in self.learned_information.values() 
                                        if l.confidence_level == ConfidenceLevel.HIGH]),
            "medium_confidence_items": len([l for l in self.learned_information.values() 
                                          if l.confidence_level == ConfidenceLevel.MEDIUM]),
            "low_confidence_items": len([l for l in self.learned_information.values() 
                                       if l.confidence_level == ConfidenceLevel.LOW]),
        })
        
        # Add learning type breakdown
        learning_type_counts = {}
        for learned_info in self.learned_information.values():
            learning_type = learned_info.learning_type.value
            learning_type_counts[learning_type] = learning_type_counts.get(learning_type, 0) + 1
        
        stats['learning_type_breakdown'] = learning_type_counts
        
        return stats
    
    def cleanup_old_learned_info(self, max_age_days: int = 90, min_usage_count: int = 0):
        """Clean up old, unused learned information."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        items_to_remove = []
        for learned_id, learned_info in self.learned_information.items():
            if (learned_info.timestamp < cutoff_date and 
                learned_info.usage_count <= min_usage_count and
                learned_info.confidence_level == ConfidenceLevel.LOW):
                items_to_remove.append(learned_id)
        
        for learned_id in items_to_remove:
            del self.learned_information[learned_id]
        
        if items_to_remove:
            logger.info(f"Cleaned up {len(items_to_remove)} old learned information items")
            self._save_learned_data()
        
        return len(items_to_remove)

# Test the conversation learning system
async def test_conversation_learning():
    """Test conversation learning functionality."""
    print("🧪 Testing Conversation Learning System")
    print("=" * 50)
    
    # Initialize learning engine
    learning_engine = ConversationLearningEngine()
    
    # Test knowledge gap identification
    gap = learning_engine.identify_knowledge_gap(
        user_query="What are the new COVID-19 protocols?",
        attempted_sources=["FAQ", "Policy Documents"],
        session_id="test_session_1",
        topic="healthcare"
    )
    print(f"✅ Identified knowledge gap: {gap.gap_type}")
    
    # Test learning opportunity detection
    user_messages = [
        "Actually, the new policy requires 48-hour notice for cancellations",
        "Let me tell you, the system is down every Tuesday for maintenance",
        "No, that's not right, the fee is $25, not $20",
        "Also, you need to bring your insurance card"
    ]
    
    for message in user_messages:
        opportunity = learning_engine.detect_user_learning_opportunity(
            message, {"session_id": "test_session_1"}
        )
        if opportunity:
            learning_type, content = opportunity
            print(f"✅ Detected learning opportunity: {learning_type.value} - {content}")
            
            # Store the learned information
            learned_info = learning_engine.store_learned_information(
                content=content,
                learning_type=learning_type,
                session_id="test_session_1",
                conversation_turn=1,
                user_query=message,
                agent_response="Thank you for that information.",
                topic="policy",
                confidence_level=ConfidenceLevel.HIGH
            )
    
    # Test searching learned information
    search_results = learning_engine.search_learned_information(
        query="cancellation policy",
        min_confidence=ConfidenceLevel.MEDIUM
    )
    print(f"✅ Found {len(search_results)} relevant learned items")
    
    # Test statistics
    stats = learning_engine.get_learning_statistics()
    print(f"📊 Learning Statistics: {stats['current_learned_items']} items learned")
    
    print("✅ Conversation learning test completed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_conversation_learning())