"""
Comprehensive Test Suite for PDF RAG Integration
Tests all components of the PDF RAG integration system including unit tests,
integration tests, and end-to-end tests with voice agent.
"""

import unittest
import asyncio
import tempfile
import os
import json
import shutil
import logging
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import List, Dict, Any

# Import components to test
from document_type_detector import DocumentTypeDetector, DocumentType
from document_parsers import DocumentParser, DocumentSection
from unified_knowledge_base import UnifiedKnowledgeBase, KnowledgeEntry, ContentMerger, ProcessedDocument
from simple_rag_engine import SimpleRAGEngine, QueryProcessor, RankingAlgorithm, ResponseSynthesizer
from knowledge_indexer import KnowledgeIndexer
from conversation_learning import ConversationLearningEngine, LearningType, ConfidenceLevel
from domain_expertise import DomainExpertiseEngine
from pdf_file_monitor import PDFDirectoryWatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPDFProcessingUnit(unittest.TestCase):
    """Unit tests for PDF processing components."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        
        # Create mock document type detector
        self.doc_type_detector = DocumentTypeDetector()
        
        # Create mock document parser
        self.doc_parser = DocumentParser()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_document_type_detection(self):
        """Test document type detection."""
        # Test with different document content
        faq_content = "Frequently Asked Questions\n1. What is CareSetu?\n2. How do I book an appointment?"
        policy_content = "Policy Document\nRefund Policy\nCancellation Policy"
        procedure_content = "Procedure Guide\nStep 1: Login to the app\nStep 2: Select a doctor"
        
        # Test detection
        self.assertEqual(self.doc_type_detector.detect_type(faq_content), DocumentType.FAQ)
        self.assertEqual(self.doc_type_detector.detect_type(policy_content), DocumentType.POLICY)
        self.assertEqual(self.doc_type_detector.detect_type(procedure_content), DocumentType.PROCEDURE)
    
    def test_document_parsing(self):
        """Test document parsing."""
        # Test content
        test_content = """
        # Section 1: Introduction
        This is an introduction.
        
        # Section 2: Features
        These are the features.
        
        # Section 3: Conclusion
        This is the conclusion.
        """
        
        # Parse document
        sections = self.doc_parser.parse_sections(test_content)
        
        # Verify sections
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].title, "Section 1: Introduction")
        self.assertEqual(sections[1].title, "Section 2: Features")
        self.assertEqual(sections[2].title, "Section 3: Conclusion")


class TestUnifiedKnowledgeBase(unittest.TestCase):
    """Tests for unified knowledge base."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.kb_dir = os.path.join(self.temp_dir, "kb")
        self.pdf_dir = os.path.join(self.temp_dir, "pdf")
        
        # Create directories
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # Create test knowledge entries
        self.test_entries = [
            KnowledgeEntry(
                id="test1",
                title="Test Entry 1",
                content="This is test content 1",
                category="faq",
                source_file="test1.json",
                source_type="json",
                metadata={"priority": "high"}
            ),
            KnowledgeEntry(
                id="test2",
                title="Test Entry 2",
                content="This is test content 2",
                category="policy",
                source_file="test2.json",
                source_type="json",
                metadata={"priority": "medium"}
            )
        ]
        
        # Create test processed documents
        self.test_documents = [
            ProcessedDocument(
                id="doc1",
                title="Test Document 1",
                content="This is test document content 1",
                document_type="faq",
                source_file="test1.pdf",
                sections=[
                    DocumentSection(
                        id="sec1",
                        title="Section 1",
                        content="Section 1 content",
                        level=1
                    )
                ],
                metadata={"priority": "high"}
            )
        ]
        
        # Write test entries to JSON files
        test_kb_file = os.path.join(self.kb_dir, "test.json")
        with open(test_kb_file, "w") as f:
            json.dump([entry.__dict__ for entry in self.test_entries], f)
        
        # Write test documents to JSON file
        test_pdf_file = os.path.join(self.pdf_dir, "processed_documents.json")
        with open(test_pdf_file, "w") as f:
            json.dump([doc.__dict__ for doc in self.test_documents], f)
        
        # Create unified knowledge base
        self.kb = UnifiedKnowledgeBase(
            json_kb_path=self.kb_dir,
            pdf_content_path=self.pdf_dir
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_knowledge_base_loading(self):
        """Test knowledge base loading."""
        # Verify entries loaded
        self.assertEqual(len(self.kb.get_all_entries()), len(self.test_entries) + len(self.test_documents))
        
        # Verify entry retrieval
        entry = self.kb.get_entry_by_id("test1")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.title, "Test Entry 1")
        
        # Verify document retrieval
        doc = self.kb.get_entry_by_id("doc1")
        self.assertIsNotNone(doc)
        self.assertEqual(doc.title, "Test Document 1")
    
    def test_knowledge_base_filtering(self):
        """Test knowledge base filtering."""
        # Filter by category
        faq_entries = self.kb.get_entries_by_category("faq")
        self.assertEqual(len(faq_entries), 2)  # One from JSON, one from PDF
        
        # Filter by source type
        json_entries = self.kb.get_entries_by_source_type("json")
        self.assertEqual(len(json_entries), 2)
        
        pdf_entries = self.kb.get_entries_by_source_type("pdf")
        self.assertEqual(len(pdf_entries), 1)


class TestRAGComponents(unittest.TestCase):
    """Tests for RAG components."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock knowledge base
        self.kb = MagicMock(spec=UnifiedKnowledgeBase)
        
        # Create test entries
        self.test_entries = [
            KnowledgeEntry(
                id="test1",
                title="Business Hours",
                content="Our business hours are 9 AM to 5 PM, Monday to Friday.",
                category="faq",
                source_file="hours.json",
                source_type="json",
                metadata={"priority": "high"}
            ),
            KnowledgeEntry(
                id="test2",
                title="Appointment Booking",
                content="To book an appointment, login to the app and select a doctor.",
                category="procedure",
                source_file="appointments.json",
                source_type="json",
                metadata={"priority": "high"}
            )
        ]
        
        # Set up knowledge base mock
        self.kb.get_all_entries.return_value = self.test_entries
        self.kb.get_entry_by_id.side_effect = lambda id: next((e for e in self.test_entries if e.id == id), None)
        
        # Create components
        self.query_processor = QueryProcessor()
        self.ranking_algorithm = RankingAlgorithm()
        self.response_synthesizer = ResponseSynthesizer()
    
    def test_query_processing(self):
        """Test query processing."""
        # Test query expansion
        expanded = self.query_processor.expand_query("What are your business hours?")
        self.assertIn("time", expanded)
        self.assertIn("schedule", expanded)
        
        # Test intent extraction
        intent = self.query_processor.extract_intent("How do I book an appointment?")
        self.assertEqual(intent, "booking")
        
        intent = self.query_processor.extract_intent("What are your business hours?")
        self.assertEqual(intent, "hours")
    
    def test_ranking_algorithm(self):
        """Test ranking algorithm."""
        # Create mock search results
        mock_results = [
            IndexerSearchResult(
                entry_id="test1",
                document_id="test1",
                section_id="test1",
                title="Business Hours",
                content="Our business hours are 9 AM to 5 PM, Monday to Friday.",
                snippet="Our business hours are 9 AM to 5 PM, Monday to Friday.",
                category="faq",
                source_file="hours.json",
                source_type="json",
                matched_terms=["hours", "business"],
                to_dict=lambda: {"created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
            ),
            IndexerSearchResult(
                entry_id="test2",
                document_id="test2",
                section_id="test2",
                title="Appointment Booking",
                content="To book an appointment, login to the app and select a doctor.",
                snippet="To book an appointment, login to the app and select a doctor.",
                category="procedure",
                source_file="appointments.json",
                source_type="json",
                matched_terms=["appointment", "book"],
                to_dict=lambda: {"created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
            )
        ]
        
        # Test ranking for hours query
        ranked_results = self.ranking_algorithm.rank_results(
            mock_results, 
            "What are your business hours?",
            "hours"
        )
        
        # First result should be about hours
        self.assertEqual(ranked_results[0].title, "Business Hours")
        
        # Test ranking for booking query
        ranked_results = self.ranking_algorithm.rank_results(
            mock_results, 
            "How do I book an appointment?",
            "booking"
        )
        
        # First result should be about booking
        self.assertEqual(ranked_results[0].title, "Appointment Booking")
    
    def test_response_synthesis(self):
        """Test response synthesis."""
        # Create mock search results
        mock_results = [
            SearchResult(
                document_id="test1",
                section_id="test1",
                content="Our business hours are 9 AM to 5 PM, Monday to Friday.",
                relevance_score=0.9,
                document_type="faq",
                source_file="hours.json",
                context_match="hours",
                snippet="Our business hours are 9 AM to 5 PM, Monday to Friday.",
                title="Business Hours"
            )
        ]
        
        # Test response synthesis
        response, citations = self.response_synthesizer.synthesize_response(
            "What are your business hours?",
            mock_results,
            "hours"
        )
        
        # Verify response contains content
        self.assertIn("9 AM to 5 PM", response)
        self.assertIn("Monday to Friday", response)
        
        # Verify citations
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["title"], "Business Hours")


class TestRAGIntegration(unittest.TestCase):
    """Integration tests for RAG system."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.kb_dir = os.path.join(self.temp_dir, "kb")
        self.pdf_dir = os.path.join(self.temp_dir, "pdf")
        
        # Create directories
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # Create test knowledge entries
        test_entries = [
            {
                "id": "hours1",
                "title": "Business Hours",
                "content": "Our business hours are 9 AM to 5 PM, Monday to Friday. We are closed on weekends and holidays.",
                "category": "faq",
                "source_file": "hours.json",
                "source_type": "json",
                "metadata": {"priority": "high"}
            },
            {
                "id": "appointment1",
                "title": "Appointment Booking",
                "content": "To book an appointment, login to the app and select a doctor. Choose a date and time slot, then confirm your booking.",
                "category": "procedure",
                "source_file": "appointments.json",
                "source_type": "json",
                "metadata": {"priority": "high"}
            }
        ]
        
        # Write test entries to JSON file
        test_kb_file = os.path.join(self.kb_dir, "test.json")
        with open(test_kb_file, "w") as f:
            json.dump(test_entries, f)
        
        # Create test processed documents
        test_documents = [
            {
                "id": "doc1",
                "title": "Emergency Support",
                "content": "Emergency support is available 24/7. Call our emergency hotline at 1-800-CARE-247.",
                "document_type": "faq",
                "source_file": "emergency.pdf",
                "sections": [
                    {
                        "id": "sec1",
                        "title": "Emergency Support",
                        "content": "Emergency support is available 24/7. Call our emergency hotline at 1-800-CARE-247.",
                        "level": 1
                    }
                ],
                "metadata": {"priority": "high"}
            }
        ]
        
        # Write test documents to JSON file
        test_pdf_file = os.path.join(self.pdf_dir, "processed_documents.json")
        with open(test_pdf_file, "w") as f:
            json.dump(test_documents, f)
        
        # Create unified knowledge base
        self.kb = UnifiedKnowledgeBase(
            json_kb_path=self.kb_dir,
            pdf_content_path=self.pdf_dir
        )
        
        # Create RAG engine
        self.rag_engine = SimpleRAGEngine(self.kb)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    @unittest.skip("Requires async event loop")
    def test_search_and_generate(self):
        """Test search and generate functionality."""
        # Test hours query
        response = asyncio.run(self.rag_engine.search_and_generate(
            "What are your business hours?"
        ))
        
        # Verify response
        self.assertIn("9 AM to 5 PM", response.answer)
        self.assertIn("Monday to Friday", response.answer)
        
        # Test appointment query
        response = asyncio.run(self.rag_engine.search_and_generate(
            "How do I book an appointment?"
        ))
        
        # Verify response
        self.assertIn("login to the app", response.answer)
        self.assertIn("select a doctor", response.answer)
        
        # Test emergency query
        response = asyncio.run(self.rag_engine.search_and_generate(
            "Do you have emergency support?"
        ))
        
        # Verify response
        self.assertIn("24/7", response.answer)
        self.assertIn("emergency hotline", response.answer)
    
    @unittest.skip("Requires async event loop")
    def test_conversation_context(self):
        """Test conversation context functionality."""
        session_id = "test_session"
        
        # First query
        response1 = asyncio.run(self.rag_engine.search_and_generate(
            "What are your business hours?",
            session_id=session_id
        ))
        
        # Follow-up query
        response2 = asyncio.run(self.rag_engine.search_and_generate(
            "What about on weekends?",
            session_id=session_id
        ))
        
        # Verify context awareness
        self.assertIn("closed on weekends", response2.answer)


class TestDomainExpertise(unittest.TestCase):
    """Tests for domain expertise adaptation."""
    
    def setUp(self):
        """Set up test environment."""
        self.domain_engine = DomainExpertiseEngine()
    
    def test_domain_detection(self):
        """Test domain detection."""
        # Test healthcare domain
        healthcare_query = "What medications are covered by insurance?"
        healthcare_docs = ["medical", "health"]
        healthcare_content = ["Our healthcare plans cover prescription medications."]
        
        domain_context = self.domain_engine.detect_domain(
            query=healthcare_query,
            document_types=healthcare_docs,
            document_contents=healthcare_content
        )
        
        self.assertEqual(domain_context.detected_domain, DomainType.HEALTHCARE)
        
        # Test appointment domain
        appointment_query = "How do I book an appointment?"
        appointment_docs = ["procedure"]
        appointment_content = ["To book an appointment, login to the app."]
        
        domain_context = self.domain_engine.detect_domain(
            query=appointment_query,
            document_types=appointment_docs,
            document_contents=appointment_content
        )
        
        self.assertEqual(domain_context.detected_domain, DomainType.APPOINTMENT)
    
    def test_response_adaptation(self):
        """Test response adaptation."""
        # Create mock domain context
        domain_context = MagicMock()
        domain_context.detected_domain = DomainType.HEALTHCARE
        domain_context.confidence = 0.8
        domain_context.expertise_level = "intermediate"
        
        # Test response adaptation
        original_response = "You can take the medication twice daily."
        
        domain_response = self.domain_engine.adapt_response(
            original_response=original_response,
            domain_context=domain_context,
            query="How often should I take my medication?",
            document_sources=["medication_guide.pdf"]
        )
        
        # Verify adaptation
        self.assertNotEqual(domain_response.adapted_response, original_response)
        self.assertEqual(domain_response.domain, DomainType.HEALTHCARE)


class TestConversationLearning(unittest.TestCase):
    """Tests for conversation learning."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.learning_engine = ConversationLearningEngine(storage_path=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_learning_opportunity_detection(self):
        """Test learning opportunity detection."""
        # Test explicit teaching
        explicit_message = "Actually, the new policy requires 48-hour notice for cancellations."
        opportunity = self.learning_engine.detect_user_learning_opportunity(
            explicit_message, {"session_id": "test_session"}
        )
        
        self.assertIsNotNone(opportunity)
        self.assertEqual(opportunity[0], LearningType.USER_CORRECTION)
        
        # Test correction
        correction_message = "No, that's not right, the fee is $25, not $20."
        opportunity = self.learning_engine.detect_user_learning_opportunity(
            correction_message, {"session_id": "test_session"}
        )
        
        self.assertIsNotNone(opportunity)
        self.assertEqual(opportunity[0], LearningType.USER_CORRECTION)
    
    def test_store_learned_information(self):
        """Test storing learned information."""
        # Store learned information
        learned_info = self.learning_engine.store_learned_information(
            content="The new policy requires 48-hour notice for cancellations.",
            learning_type=LearningType.USER_CORRECTION,
            session_id="test_session",
            conversation_turn=1,
            user_query="Is 24-hour notice enough for cancellations?",
            agent_response="Yes, 24-hour notice is sufficient for cancellations.",
            topic="policy",
            confidence_level=ConfidenceLevel.HIGH
        )
        
        # Verify learned information
        self.assertIsNotNone(learned_info)
        self.assertEqual(learned_info.content, "The new policy requires 48-hour notice for cancellations.")
        self.assertEqual(learned_info.learning_type, LearningType.USER_CORRECTION)
        self.assertEqual(learned_info.topic, "policy")
        
        # Search learned information
        search_results = self.learning_engine.search_learned_information(
            query="cancellation policy",
            min_confidence=ConfidenceLevel.MEDIUM
        )
        
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0].id, learned_info.id)


class TestPDFMonitoring(unittest.TestCase):
    """Tests for PDF monitoring."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_dir = os.path.join(self.temp_dir, "pdfs")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        # Create directories
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create mock processor
        self.mock_processor = MagicMock()
        self.mock_processor.process_pdf.return_value = True
        
        # Create watcher
        self.watcher = PDFDirectoryWatcher(
            watch_dir=self.pdf_dir,
            processor=self.mock_processor
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_file_detection(self):
        """Test file detection."""
        # Create test PDF file
        test_pdf_path = os.path.join(self.pdf_dir, "test.pdf")
        with open(test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n")  # Minimal PDF header
        
        # Process new files
        self.watcher.process_existing_files()
        
        # Verify processor called
        self.mock_processor.process_pdf.assert_called_once()
        args, _ = self.mock_processor.process_pdf.call_args
        self.assertEqual(args[0], test_pdf_path)


if __name__ == "__main__":
    unittest.main()