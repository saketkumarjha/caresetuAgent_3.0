"""
Tests for the conversation learning component.
Tests the ability to learn from conversations and use learned information.
"""

import os
import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import components to test
from conversation_learning import ConversationLearningEngine, LearningType, ConfidenceLevel
from conversation_context import ConversationContextManager

class TestConversationLearning(unittest.TestCase):
    """Test the conversation learning component."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.learned_dir = os.path.join(self.temp_dir, "learned_knowledge")
        
        os.makedirs(self.learned_dir, exist_ok=True)
        
        # Create initial learned information file
        self._create_initial_learned_info()
        
        # Initialize learning engine
        self.learning_engine = ConversationLearningEngine(
            storage_directory=self.learned_dir
        )
        
        # Initialize context manager
        self.context_manager = ConversationContextManager()
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def _create_initial_learned_info(self):
        """Create initial learned information file."""
        learned_info = [
            {
                "id": "learn1",
                "content": "The office is also open on Saturday from 10AM-2PM.",
                "source_conversation": "conv123",
                "timestamp": datetime.now().isoformat(),
                "confidence": "high",
                "learning_type": "explicit",
                "related_topics": ["hours", "schedule"],
                "usage_count": 5,
                "last_used": datetime.now().isoformat()
            },
            {
                "id": "learn2",
                "content": "Dr. Smith specializes in pediatric care.",
                "source_conversation": "conv456",
                "timestamp": datetime.now().isoformat(),
                "confidence": "medium",
                "learning_type": "implicit",
                "related_topics": ["doctor", "specialty"],
                "usage_count": 2,
                "last_used": datetime.now().isoformat()
            }
        ]
        
        # Write learned information file
        with open(os.path.join(self.learned_dir, "learned_information.json"), "w") as f:
            json.dump(learned_info, f, indent=2)
        
        # Create knowledge gaps file
        knowledge_gaps = [
            {
                "id": "gap1",
                "query": "What are your weekend hours?",
                "timestamp": datetime.now().isoformat(),
                "frequency": 3,
                "last_asked": datetime.now().isoformat()
            },
            {
                "id": "gap2",
                "query": "Do you offer pediatric services?",
                "timestamp": datetime.now().isoformat(),
                "frequency": 2,
                "last_asked": datetime.now().isoformat()
            }
        ]
        
        # Write knowledge gaps file
        with open(os.path.join(self.learned_dir, "knowledge_gaps.json"), "w") as f:
            json.dump(knowledge_gaps, f, indent=2)
    
    def test_load_learned_information(self):
        """Test loading learned information."""
        # Load learned information
        self.learning_engine.load_learned_information()
        
        # Verify that information was loaded
        self.assertEqual(len(self.learning_engine.learned_information), 2)
        self.assertEqual(len(self.learning_engine.knowledge_gaps), 2)
        
        # Check specific entries
        self.assertTrue(any(info.content == "The office is also open on Saturday from 10AM-2PM." 
                          for info in self.learning_engine.learned_information))
        self.assertTrue(any(gap.query == "What are your weekend hours?" 
                          for gap in self.learning_engine.knowledge_gaps))
    
    def test_detect_learning_opportunity(self):
        """Test detection of learning opportunities."""
        # Test explicit learning opportunity
        user_message = "Let me tell you that we also have Sunday hours from 12PM-4PM."
        context = {"session_id": "test_session"}
        
        result = self.learning_engine.detect_user_learning_opportunity(user_message, context)
        
        # Verify detection
        self.assertTrue(result)
        
        # Test implicit learning opportunity
        user_message = "I tried to call on Sunday but no one answered."
        context = {"session_id": "test_session"}
        
        result = self.learning_engine.detect_user_learning_opportunity(user_message, context)
        
        # Verify detection
        self.assertTrue(result)
        
        # Test non-learning message
        user_message = "What are your business hours?"
        context = {"session_id": "test_session"}
        
        result = self.learning_engine.detect_user_learning_opportunity(user_message, context)
        
        # Verify no detection
        self.assertFalse(result)
    
    def test_extract_learned_information(self):
        """Test extraction of learned information from user messages."""
        # Test explicit learning
        user_message = "Let me tell you that we also have Sunday hours from 12PM-4PM."
        context = {"session_id": "test_session"}
        
        learned_info = self.learning_engine.extract_learned_information(
            user_message, 
            context,
            LearningType.EXPLICIT
        )
        
        # Verify extraction
        self.assertIsNotNone(learned_info)
        self.assertEqual(learned_info.learning_type, "explicit")
        self.assertIn("sunday", learned_info.content.lower())
        self.assertIn("12pm-4pm", learned_info.content.lower())
        self.assertEqual(learned_info.confidence, "high")
        
        # Test implicit learning
        user_message = "I tried to call on Sunday but no one answered."
        context = {"session_id": "test_session"}
        
        learned_info = self.learning_engine.extract_learned_information(
            user_message, 
            context,
            LearningType.IMPLICIT
        )
        
        # Verify extraction
        self.assertIsNotNone(learned_info)
        self.assertEqual(learned_info.learning_type, "implicit")
        self.assertIn("sunday", learned_info.content.lower())
        self.assertEqual(learned_info.confidence, "low")
    
    def test_store_learned_information(self):
        """Test storing learned information."""
        # Create learned information
        user_message = "Let me tell you that we also have Sunday hours from 12PM-4PM."
        context = {"session_id": "test_session"}
        
        learned_info = self.learning_engine.extract_learned_information(
            user_message, 
            context,
            LearningType.EXPLICIT
        )
        
        # Store learned information
        self.learning_engine.store_learned_information(learned_info)
        
        # Verify storage
        self.assertGreaterEqual(len(self.learning_engine.learned_information), 3)
        self.assertTrue(any(info.content == learned_info.content 
                          for info in self.learning_engine.learned_information))
        
        # Check that file was updated
        with open(os.path.join(self.learned_dir, "learned_information.json"), "r") as f:
            stored_data = json.load(f)
        
        self.assertGreaterEqual(len(stored_data), 3)
        self.assertTrue(any(info["content"] == learned_info.content for info in stored_data))
    
    def test_search_learned_information(self):
        """Test searching learned information."""
        # Load learned information
        self.learning_engine.load_learned_information()
        
        # Search for hours information
        results = self.learning_engine.search_learned_information(
            query="What are your weekend hours?",
            min_confidence=ConfidenceLevel.MEDIUM
        )
        
        # Verify search results
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("saturday" in info.content.lower() for info in results))
        
        # Search for doctor information
        results = self.learning_engine.search_learned_information(
            query="Tell me about Dr. Smith",
            min_confidence=ConfidenceLevel.MEDIUM
        )
        
        # Verify search results
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("dr. smith" in info.content.lower() for info in results))
        
        # Search with high confidence threshold
        results = self.learning_engine.search_learned_information(
            query="Tell me about Dr. Smith",
            min_confidence=ConfidenceLevel.HIGH
        )
        
        # Verify that medium confidence results are filtered out
        self.assertEqual(len(results), 0)
    
    def test_track_knowledge_gap(self):
        """Test tracking knowledge gaps."""
        # Track a new knowledge gap
        query = "Do you offer telemedicine services?"
        self.learning_engine.track_knowledge_gap(query)
        
        # Verify tracking
        self.assertGreaterEqual(len(self.learning_engine.knowledge_gaps), 3)
        self.assertTrue(any(gap.query == query for gap in self.learning_engine.knowledge_gaps))
        
        # Track an existing gap
        query = "What are your weekend hours?"
        self.learning_engine.track_knowledge_gap(query)
        
        # Verify that frequency was incremented
        gap = next((g for g in self.learning_engine.knowledge_gaps if g.query == query), None)
        self.assertIsNotNone(gap)
        self.assertGreaterEqual(gap.frequency, 4)  # Initial 3 + 1
    
    def test_check_pdf_conflict(self):
        """Test checking for conflicts between learned info and PDF content."""
        # Create learned information
        learned_info = self.learning_engine.learned_information[0]  # Saturday hours
        
        # Test with conflicting PDF content
        pdf_content = "Our business hours are Monday-Friday 9AM-5PM. We are closed on weekends."
        
        has_conflict, details = self.learning_engine.check_pdf_conflict(learned_info, pdf_content)
        
        # Verify conflict detection
        self.assertTrue(has_conflict)
        self.assertIn("conflict", details.lower())
        
        # Test with non-conflicting PDF content
        pdf_content = "Our business hours are Monday-Friday 9AM-5PM."
        
        has_conflict, details = self.learning_engine.check_pdf_conflict(learned_info, pdf_content)
        
        # Verify no conflict
        self.assertFalse(has_conflict)
    
    def test_mark_learned_info_used(self):
        """Test marking learned information as used."""
        # Load learned information
        self.learning_engine.load_learned_information()
        
        # Get initial usage count
        info_id = self.learning_engine.learned_information[0].id
        initial_count = self.learning_engine.learned_information[0].usage_count
        
        # Mark as used
        self.learning_engine.mark_learned_info_used(info_id)
        
        # Verify usage count increment
        updated_info = next((info for info in self.learning_engine.learned_information if info.id == info_id), None)
        self.assertIsNotNone(updated_info)
        self.assertEqual(updated_info.usage_count, initial_count + 1)
    
    def test_integration_with_context_manager(self):
        """Test integration with conversation context manager."""
        # Create a session
        session_id = "test_session"
        context = self.context_manager.get_or_create_context(session_id)
        
        # Add conversation turns
        self.context_manager.add_conversation_turn(
            session_id=session_id,
            user_message="What are your business hours?",
            agent_response="We are open Monday-Friday 9AM-5PM.",
            intent="hours",
            confidence=0.9,
            sources_used=["faq.pdf"]
        )
        
        self.context_manager.add_conversation_turn(
            session_id=session_id,
            user_message="Are you open on weekends?",
            agent_response="I don't have information about weekend hours.",
            intent="hours",
            confidence=0.7,
            sources_used=[]
        )
        
        # User provides new information
        user_message = "Let me tell you that we are also open on Saturday from 10AM-2PM."
        
        # Detect learning opportunity
        result = self.learning_engine.detect_user_learning_opportunity(
            user_message, 
            {"session_id": session_id}
        )
        
        # Verify detection
        self.assertTrue(result)
        
        # Extract and store learned information
        learned_info = self.learning_engine.extract_learned_information(
            user_message, 
            {"session_id": session_id},
            LearningType.EXPLICIT
        )
        
        self.learning_engine.store_learned_information(learned_info)
        
        # Search for learned information in future conversation
        self.context_manager.add_conversation_turn(
            session_id=session_id,
            user_message="What are your weekend hours?",
            agent_response="Based on what I've learned, we are open on Saturday from 10AM-2PM.",
            intent="hours",
            confidence=0.9,
            sources_used=[]
        )
        
        results = self.learning_engine.search_learned_information(
            query="weekend hours",
            min_confidence=ConfidenceLevel.MEDIUM
        )
        
        # Verify that learned information is found
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("saturday" in info.content.lower() for info in results))

if __name__ == "__main__":
    unittest.main()