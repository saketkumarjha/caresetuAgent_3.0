"""
Tests for the RAG integration with the voice agent.
Tests the integration between RAG engine and voice agent.
"""

import os
import unittest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Import components to test
from agent import BusinessVoiceAgent
from simple_rag_engine import SimpleRAGEngine, RAGResponse, SearchResult
from unified_knowledge_base import UnifiedKnowledgeBase
from conversation_context import ConversationContextManager
from domain_expertise import DomainExpertiseEngine

class TestRAGIntegration(unittest.TestCase):
    """Test the RAG integration with the voice agent."""
    
    def setUp(self):
        """Set up test environment."""
        # Create patches for agent initialization
        self.patches = patch.multiple(
            'agent.BusinessVoiceAgent',
            _create_tts=MagicMock(return_value=MagicMock()),
            _create_business_context=MagicMock(return_value=MagicMock())
        )
        self.patches.start()
        
        # Mock config
        self.config_patcher = patch('agent.config', autospec=True)
        self.mock_config = self.config_patcher.start()
        self.mock_config.google.api_key = "fake_api_key"
        
        # Mock LLM
        self.llm_patcher = patch('agent.google.LLM', autospec=True)
        self.mock_llm = self.llm_patcher.start()
        
        # Mock STT
        self.stt_patcher = patch('agent.create_assemblyai_stt', autospec=True)
        self.mock_stt = self.stt_patcher.start()
        
        # Mock VAD
        self.vad_patcher = patch('agent.silero.VAD.load', autospec=True)
        self.mock_vad = self.vad_patcher.start()
        
        # Create mocks for RAG components
        self.mock_kb = MagicMock(spec=UnifiedKnowledgeBase)
        self.mock_rag = MagicMock(spec=SimpleRAGEngine)
        self.mock_context = MagicMock(spec=ConversationContextManager)
        
        # Setup RAG response
        self.mock_rag_response = RAGResponse(
            answer="Our business hours are Monday-Friday 9AM-5PM.",
            sources=["faq.pdf"],
            confidence=0.9,
            context_used="",
            retrieved_content=[
                SearchResult(
                    document_id="doc1",
                    section_id="sec1",
                    content="Our business hours are Monday-Friday 9AM-5PM.",
                    relevance_score=0.9,
                    document_type="faq",
                    source_file="faq.pdf",
                    context_match="hours",
                    snippet="Our business hours",
                    title="Business Hours",
                    matched_terms=["hours", "business"]
                )
            ],
            processing_time=0.1
        )
        
        # Setup mock search_and_generate
        self.mock_rag.search_and_generate = AsyncMock(return_value=self.mock_rag_response)
    
    def tearDown(self):
        """Clean up after tests."""
        self.patches.stop()
        self.config_patcher.stop()
        self.llm_patcher.stop()
        self.stt_patcher.stop()
        self.vad_patcher.stop()
    
    @patch('agent.UnifiedKnowledgeBase')
    @patch('agent.SimpleRAGEngine')
    @patch('agent.ConversationContextManager')
    @patch('agent.ConversationLearningEngine')
    async def test_rag_enhanced_response_generation(self, mock_learning_cls, mock_context_cls, mock_rag_cls, mock_kb_cls):
        """Test RAG-enhanced response generation."""
        # Setup mocks
        mock_kb_cls.return_value = self.mock_kb
        mock_rag_cls.return_value = self.mock_rag
        mock_context_cls.return_value = self.mock_context
        
        # Setup context manager
        self.mock_context.get_or_create_context = AsyncMock()
        self.mock_context.get_conversation_summary = AsyncMock(return_value="")
        self.mock_context.add_conversation_turn = AsyncMock()
        
        # Initialize agent
        agent = BusinessVoiceAgent()
        
        # Test RAG-enhanced response generation
        user_query = "What are your business hours?"
        session_id = "test_session"
        
        response = await agent._generate_rag_enhanced_response(user_query, session_id)
        
        # Verify that RAG search was called with correct parameters
        self.mock_rag.search_and_generate.assert_called_once()
        call_args = self.mock_rag.search_and_generate.call_args[1]
        self.assertEqual(call_args["query"], user_query)
        self.assertEqual(call_args["session_id"], session_id)
        
        # Verify response
        self.assertIsNotNone(response)
        self.assertIn("business hours", response.lower())
        self.assertIn("monday-friday", response.lower())
    
    @patch('agent.UnifiedKnowledgeBase')
    @patch('agent.SimpleRAGEngine')
    @patch('agent.ConversationContextManager')
    @patch('agent.ConversationLearningEngine')
    async def test_context_aware_rag_search(self, mock_learning_cls, mock_context_cls, mock_rag_cls, mock_kb_cls):
        """Test context-aware RAG search."""
        # Setup mocks
        mock_kb_cls.return_value = self.mock_kb
        mock_rag_cls.return_value = self.mock_rag
        mock_context_cls.return_value = self.mock_context
        
        # Setup context manager
        context_obj = MagicMock()
        context_obj.turns = [MagicMock()]  # Non-empty turns
        context_obj.relevant_documents = ["faq.pdf"]
        
        self.mock_context.get_or_create_context = AsyncMock(return_value=context_obj)
        self.mock_context.get_conversation_summary = AsyncMock(return_value="Previous conversation about business hours")
        self.mock_context.add_conversation_turn = AsyncMock()
        self.mock_context.set_knowledge_context = AsyncMock()
        
        # Initialize agent
        agent = BusinessVoiceAgent()
        
        # Test RAG-enhanced response generation with context
        user_query = "Are you open on weekends?"
        session_id = "test_session"
        
        response = await agent._generate_rag_enhanced_response(user_query, session_id)
        
        # Verify that context was used
        self.mock_rag.search_and_generate.assert_called_once()
        call_args = self.mock_rag.search_and_generate.call_args[1]
        self.assertEqual(call_args["query"], user_query)
        self.assertEqual(call_args["context"], "Previous conversation about business hours")
        
        # Verify that context was updated
        self.mock_context.add_conversation_turn.assert_called_once()
    
    @patch('agent.UnifiedKnowledgeBase')
    @patch('agent.SimpleRAGEngine')
    @patch('agent.ConversationContextManager')
    @patch('agent.ConversationLearningEngine')
    def test_detect_query_intent(self, mock_learning_cls, mock_context_cls, mock_rag_cls, mock_kb_cls):
        """Test query intent detection."""
        # Setup mocks
        mock_kb_cls.return_value = self.mock_kb
        mock_rag_cls.return_value = self.mock_rag
        mock_context_cls.return_value = self.mock_context
        
        # Initialize agent
        agent = BusinessVoiceAgent()
        
        # Test different query intents
        test_cases = [
            ("How do I book an appointment?", "booking"),
            ("I need to cancel my appointment", "cancellation"),
            ("What services do you offer?", "information"),
            ("How do I use the patient portal?", "procedure"),
            ("What is your cancellation policy?", "policy"),
            ("How can I contact customer support?", "contact"),
            ("What are your business hours?", "hours"),
            ("How much does a consultation cost?", "cost"),
            ("My account is not working", "technical"),
            ("I have a question about my medication", "healthcare")
        ]
        
        for query, expected_intent in test_cases:
            intent = agent._detect_query_intent(query, [])
            self.assertEqual(intent, expected_intent, f"Failed for query: {query}")
    
    @patch('agent.UnifiedKnowledgeBase')
    @patch('agent.SimpleRAGEngine')
    @patch('agent.ConversationContextManager')
    @patch('agent.ConversationLearningEngine')
    def test_determine_topic_from_documents(self, mock_learning_cls, mock_context_cls, mock_rag_cls, mock_kb_cls):
        """Test topic determination from documents."""
        # Setup mocks
        mock_kb_cls.return_value = self.mock_kb
        mock_rag_cls.return_value = self.mock_rag
        mock_context_cls.return_value = self.mock_context
        
        # Initialize agent
        agent = BusinessVoiceAgent()
        
        # Test different document types and intents
        test_cases = [
            (["procedure"], "booking", "appointment_booking"),
            (["procedure"], "cancellation", "appointment_management"),
            (["policy"], "cancellation", "cancellation_policy"),
            (["faq"], "information", "general_information"),
            (["manual"], "technical", "technical_support"),
            (["procedure"], "healthcare", "healthcare_guidance"),
            (["policy"], "cost", "billing_policy")
        ]
        
        for doc_types, intent, expected_topic in test_cases:
            topic = agent._determine_topic_from_documents(doc_types, intent)
            self.assertEqual(topic, expected_topic, f"Failed for {doc_types}, {intent}")
    
    @patch('agent.UnifiedKnowledgeBase')
    @patch('agent.SimpleRAGEngine')
    @patch('agent.ConversationContextManager')
    @patch('agent.ConversationLearningEngine')
    def test_ensure_conversation_coherence(self, mock_learning_cls, mock_context_cls, mock_rag_cls, mock_kb_cls):
        """Test conversation coherence enhancement."""
        # Setup mocks
        mock_kb_cls.return_value = self.mock_kb
        mock_rag_cls.return_value = self.mock_rag
        mock_context_cls.return_value = self.mock_context
        
        # Initialize agent
        agent = BusinessVoiceAgent()
        
        # Create conversation context
        context = MagicMock()
        context.turns = [MagicMock()]  # Non-empty turns
        context.current_topic = "appointment_booking"
        
        # Test follow-up question
        rag_answer = "You can schedule online or call our office."
        user_query = "How about on weekends?"
        retrieved_content = [
            SearchResult(
                document_id="doc1",
                section_id="sec1",
                content="You can schedule appointments online or call our office.",
                relevance_score=0.9,
                document_type="procedure",
                source_file="procedure.pdf",
                context_match="appointment",
                snippet="schedule appointments",
                title="Scheduling",
                matched_terms=["schedule", "appointment"]
            )
        ]
        
        # Mock is_follow_up_question
        agent._is_follow_up_question = MagicMock(return_value=True)
        
        # Test coherence enhancement
        enhanced_response = agent._ensure_conversation_coherence(
            rag_answer, user_query, context, retrieved_content
        )
        
        # Verify enhancement
        self.assertIsNotNone(enhanced_response)
        self.assertNotEqual(enhanced_response, rag_answer)
        self.assertIn("appointment", enhanced_response.lower())
    
    @patch('agent.UnifiedKnowledgeBase')
    @patch('agent.SimpleRAGEngine')
    @patch('agent.ConversationContextManager')
    @patch('agent.ConversationLearningEngine')
    def test_domain_expertise_integration(self, mock_learning_cls, mock_context_cls, mock_rag_cls, mock_kb_cls):
        """Test domain expertise integration."""
        # Setup mocks
        mock_kb_cls.return_value = self.mock_kb
        mock_rag_cls.return_value = self.mock_rag
        mock_context_cls.return_value = self.mock_context
        
        # Add domain expertise to RAG response
        self.mock_rag_response.domain_expertise = {
            "detected_domain": "healthcare",
            "terminology_used": ["consultation", "medical", "healthcare"],
            "clarifying_questions": ["What specific healthcare service are you interested in?"]
        }
        
        # Initialize agent
        agent = BusinessVoiceAgent()
        agent.rag_engine.last_rag_response = self.mock_rag_response
        
        # Test domain-specific intent detection
        query = "I need to schedule a medical consultation for my diabetes"
        intent = agent._detect_query_intent(query, [])
        
        # Verify domain-specific intent
        self.assertEqual(intent, "healthcare")

if __name__ == "__main__":
    unittest.main()