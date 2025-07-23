"""
Integration tests for the RAG system.
Tests the integration between knowledge base, indexer, and RAG engine.
"""

import os
import unittest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import components to test
from unified_knowledge_base import UnifiedKnowledgeBase, KnowledgeEntry
from knowledge_indexer import KnowledgeIndexer
from simple_rag_engine import SimpleRAGEngine, SearchResult, RAGResponse
from document_parsers import DocumentSection

class TestRAGSystemIntegration(unittest.TestCase):
    """Test the integration of RAG system components."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.kb_dir = os.path.join(self.temp_dir, "knowledge_base")
        self.pdf_dir = os.path.join(self.temp_dir, "pdf_content")
        self.unified_dir = os.path.join(self.temp_dir, "unified_kb")
        self.index_dir = os.path.join(self.temp_dir, "knowledge_index")
        
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.unified_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Create test knowledge base files
        self._create_test_knowledge_files()
        
        # Initialize components
        self.knowledge_base = UnifiedKnowledgeBase(
            json_kb_path=self.kb_dir,
            pdf_content_path=self.pdf_dir,
            unified_storage_path=self.unified_dir
        )
        
        # Load knowledge
        self.knowledge_base.load_all_knowledge()
        
        # Initialize RAG engine
        self.rag_engine = SimpleRAGEngine(self.knowledge_base)
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_knowledge_files(self):
        """Create test knowledge files for testing."""
        # Create JSON knowledge base files
        faq_data = {
            "id": "faq1",
            "title": "Appointment FAQs",
            "content": "Q: How do I schedule an appointment?\nA: You can schedule online or call our office.",
            "category": "faq",
            "tags": ["appointment", "scheduling"],
            "company_id": "caresetu",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        policy_data = {
            "id": "policy1",
            "title": "Cancellation Policy",
            "content": "You must cancel at least 24 hours before your appointment to avoid a fee.",
            "category": "policy",
            "tags": ["cancellation", "appointment"],
            "company_id": "caresetu",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Write JSON files
        with open(os.path.join(self.kb_dir, "faq.json"), "w") as f:
            json.dump(faq_data, f)
        
        with open(os.path.join(self.kb_dir, "policy.json"), "w") as f:
            json.dump(policy_data, f)
        
        # Create PDF content and metadata files
        pdf_content = """
        FREQUENTLY ASKED QUESTIONS
        
        Q1: What are your business hours?
        A1: We are open Monday-Friday 9AM-5PM.
        
        Q2: How do I schedule an appointment?
        A2: You can schedule online or call our office at (555) 123-4567.
        """
        
        pdf_metadata = {
            "filename": "faq.pdf",
            "content": pdf_content,
            "document_type": "faq",
            "file_size": 1024,
            "processed_at": datetime.now().isoformat(),
            "company_id": "caresetu",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Write PDF content and metadata files
        doc_id = "test_doc_123"
        with open(os.path.join(self.pdf_dir, f"caresetu_{doc_id}_content.txt"), "w") as f:
            f.write(pdf_content)
        
        with open(os.path.join(self.pdf_dir, f"caresetu_{doc_id}_metadata.json"), "w") as f:
            json.dump(pdf_metadata, f)
    
    def test_knowledge_base_loading(self):
        """Test loading knowledge from different sources."""
        # Verify that knowledge was loaded
        self.assertGreater(len(self.knowledge_base.knowledge_entries), 0)
        
        # Check that both JSON and PDF entries were loaded
        json_entries = self.knowledge_base.get_knowledge_by_source("json")
        pdf_entries = self.knowledge_base.get_knowledge_by_source("pdf")
        
        self.assertGreater(len(json_entries), 0)
        self.assertGreater(len(pdf_entries), 0)
        
        # Check categories
        faq_entries = self.knowledge_base.get_knowledge_by_category("faq")
        policy_entries = self.knowledge_base.get_knowledge_by_category("policy")
        
        self.assertGreater(len(faq_entries), 0)
        self.assertGreater(len(policy_entries), 0)
    
    async def test_rag_search_and_generate(self):
        """Test RAG search and response generation."""
        # Test appointment-related query
        query = "How do I schedule an appointment?"
        context = ""
        
        response = await self.rag_engine.search_and_generate(query, context)
        
        # Verify response
        self.assertIsNotNone(response)
        self.assertIsInstance(response, RAGResponse)
        self.assertGreater(len(response.answer), 0)
        self.assertGreater(len(response.retrieved_content), 0)
        self.assertGreater(response.confidence, 0)
        
        # Check that the response contains relevant information
        self.assertIn("appointment", response.answer.lower())
        self.assertIn("schedule", response.answer.lower())
    
    async def test_context_aware_search(self):
        """Test context-aware search functionality."""
        # First query to establish context
        query1 = "What are your business hours?"
        context1 = ""
        session_id = "test_session"
        
        response1 = await self.rag_engine.search_and_generate(query1, context1, session_id)
        
        # Follow-up query that relies on context
        query2 = "Can I schedule an appointment outside those hours?"
        context2 = f"Previous question: {query1}"
        
        response2 = await self.rag_engine.search_and_generate(query2, context2, session_id)
        
        # Verify that context was used
        self.assertIsNotNone(response2)
        self.assertGreater(len(response2.answer), 0)
        
        # The response should reference business hours
        self.assertTrue(
            any(["hour" in result.content.lower() for result in response2.retrieved_content]) or
            "hour" in response2.answer.lower()
        )
    
    def test_ranking_algorithm(self):
        """Test the ranking algorithm for search results."""
        # Create test search results
        results = [
            SearchResult(
                document_id="doc1",
                section_id="sec1",
                content="How to schedule an appointment: Call our office or book online.",
                relevance_score=0.5,
                document_type="faq",
                source_file="faq.pdf",
                context_match="appointment",
                snippet="How to schedule an appointment",
                title="Scheduling",
                matched_terms=["appointment", "schedule"]
            ),
            SearchResult(
                document_id="doc2",
                section_id="sec2",
                content="Our business hours are Monday-Friday 9AM-5PM.",
                relevance_score=0.3,
                document_type="faq",
                source_file="faq.pdf",
                context_match="hours",
                snippet="Our business hours",
                title="Business Hours",
                matched_terms=["hours", "business"]
            )
        ]
        
        # Test ranking for appointment query
        query = "How do I schedule an appointment?"
        ranked_results = self.rag_engine.rank_results(results, query)
        
        # Verify that appointment-related result is ranked higher
        self.assertEqual(ranked_results[0].document_id, "doc1")
        
        # Test ranking for hours query
        query = "What are your business hours?"
        ranked_results = self.rag_engine.rank_results(results, query)
        
        # Verify that hours-related result is ranked higher
        self.assertEqual(ranked_results[0].document_id, "doc2")
    
    async def test_response_synthesis(self):
        """Test response synthesis from search results."""
        # Create test search results
        results = [
            SearchResult(
                document_id="doc1",
                section_id="sec1",
                content="How to schedule an appointment: Call our office at (555) 123-4567 or book online at our website.",
                relevance_score=0.9,
                document_type="faq",
                source_file="faq.pdf",
                context_match="appointment",
                snippet="How to schedule an appointment",
                title="Scheduling",
                matched_terms=["appointment", "schedule"]
            ),
            SearchResult(
                document_id="doc2",
                section_id="sec2",
                content="Our business hours are Monday-Friday 9AM-5PM.",
                relevance_score=0.5,
                document_type="faq",
                source_file="faq.pdf",
                context_match="hours",
                snippet="Our business hours",
                title="Business Hours",
                matched_terms=["hours", "business"]
            )
        ]
        
        # Test response synthesis
        query = "How do I schedule an appointment?"
        response = self.rag_engine.synthesize_response(query, results)
        
        # Verify response
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 0)
        self.assertIn("appointment", response.lower())
        self.assertIn("call", response.lower())
        self.assertIn("online", response.lower())
    
    def test_domain_expertise_adaptation(self):
        """Test domain expertise adaptation."""
        # Create a healthcare-related query
        query = "What healthcare services do you offer?"
        
        # Test domain detection
        domain_info = self.rag_engine.domain_expertise_engine.detect_domain(query)
        
        # Verify domain detection
        self.assertIsNotNone(domain_info)
        self.assertEqual(domain_info.detected_domain, "healthcare")
        
        # Test domain-specific response adaptation
        adapted_response = self.rag_engine.domain_expertise_engine.adapt_response(
            "We offer various services.",
            domain_info
        )
        
        # Verify adaptation
        self.assertIsNotNone(adapted_response)
        self.assertGreater(len(adapted_response), 0)
        self.assertIn("healthcare", adapted_response.lower())

if __name__ == "__main__":
    unittest.main()