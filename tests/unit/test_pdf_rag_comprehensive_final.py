"""
Comprehensive test for the PDF RAG integration.
Tests the complete flow from PDF processing to RAG response generation.
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
from pdf_processor_simple import PDFProcessor
from document_type_detector import DocumentTypeDetector
from document_parsers import DocumentParser
from unified_knowledge_base import UnifiedKnowledgeBase
from simple_rag_engine import SimpleRAGEngine
from knowledge_indexer import KnowledgeIndexer
from conversation_context import ConversationContextManager
from pdf_file_monitor import PDFDirectoryWatcher

class TestPDFRAGComprehensive(unittest.TestCase):
    """Comprehensive test for the PDF RAG integration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_dir = os.path.join(self.temp_dir, "pdfs")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.kb_dir = os.path.join(self.temp_dir, "knowledge_base")
        self.unified_dir = os.path.join(self.temp_dir, "unified_kb")
        self.index_dir = os.path.join(self.temp_dir, "knowledge_index")
        
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.unified_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Create test files
        self._create_test_files()
        
        # Initialize components
        self.pdf_processor = PDFProcessor(
            pdf_directory=self.pdf_dir,
            output_directory=self.output_dir
        )
        
        self.knowledge_base = UnifiedKnowledgeBase(
            json_kb_path=self.kb_dir,
            pdf_content_path=self.output_dir,
            unified_storage_path=self.unified_dir
        )
        
        self.indexer = KnowledgeIndexer(
            index_directory=self.index_dir
        )
        
        self.rag_engine = SimpleRAGEngine(self.knowledge_base)
        self.context_manager = ConversationContextManager()
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_files(self):
        """Create test files for testing."""
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
        
        # Create test PDF files with minimal content
        self._create_test_pdf("faq.pdf", """
        FREQUENTLY ASKED QUESTIONS
        
        Q1: What are your business hours?
        A1: We are open Monday-Friday 9AM-5PM.
        
        Q2: How do I schedule an appointment?
        A2: You can schedule online or call our office at (555) 123-4567.
        """)
        
        self._create_test_pdf("policy.pdf", """
        CANCELLATION POLICY
        
        1. APPOINTMENT CANCELLATION
           You must cancel at least 24 hours before your appointment to avoid a fee.
        
        2. REFUND POLICY
           Refunds are processed within 5-7 business days.
        """)
        
        self._create_test_pdf("procedure.pdf", """
        HOW TO SCHEDULE AN APPOINTMENT
        
        Step 1: Log in to your account
        Step 2: Click on "Schedule Appointment"
        Step 3: Select a date and time
        Step 4: Confirm your appointment
        """)
    
    def _create_test_pdf(self, filename, content):
        """Create a test PDF file with minimal content."""
        pdf_path = os.path.join(self.pdf_dir, filename)
        
        # Create a minimal PDF file
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.5\n")  # Minimal PDF header
        
        # Mock the text extraction by creating a text file with the same name
        text_path = os.path.join(self.pdf_dir, f"{filename}.txt")
        with open(text_path, "w") as f:
            f.write(content)
    
    @patch('pdf_processor_simple.PDFProcessor.extract_text_from_pdf')
    async def test_end_to_end_pdf_rag_flow(self, mock_extract):
        """Test the end-to-end flow from PDF processing to RAG response."""
        # Mock the text extraction to use our pre-created text files
        def mock_extract_text(pdf_path):
            filename = os.path.basename(pdf_path)
            text_path = os.path.join(self.pdf_dir, f"{filename}.txt")
            if os.path.exists(text_path):
                with open(text_path, "r") as f:
                    return f.read()
            return ""
        
        mock_extract.side_effect = mock_extract_text
        
        # Step 1: Process PDF files
        processed_docs = await self.pdf_processor.process_all_pdfs()
        
        # Verify PDF processing
        self.assertEqual(len(processed_docs), 3)
        self.assertTrue(any(doc["document_type"] == "faq" for doc in processed_docs))
        self.assertTrue(any(doc["document_type"] == "policy" for doc in processed_docs))
        self.assertTrue(any(doc["document_type"] == "procedure" for doc in processed_docs))
        
        # Step 2: Load knowledge base
        kb_stats = self.knowledge_base.load_all_knowledge()
        
        # Verify knowledge base loading
        self.assertGreater(kb_stats["total_entries"], 0)
        self.assertGreater(kb_stats["json_entries"], 0)
        self.assertGreater(kb_stats["pdf_entries"], 0)
        
        # Step 3: Test RAG search and response generation
        queries = [
            "What are your business hours?",
            "How do I schedule an appointment?",
            "What is your cancellation policy?",
            "How do I cancel an appointment?"
        ]
        
        for query in queries:
            response = await self.rag_engine.search_and_generate(query, "")
            
            # Verify response
            self.assertIsNotNone(response)
            self.assertGreater(len(response.answer), 0)
            self.assertGreater(len(response.retrieved_content), 0)
            self.assertGreater(response.confidence, 0)
            
            # Check that the response contains relevant information
            query_terms = query.lower().split()
            response_lower = response.answer.lower()
            
            # Check if at least one query term is in the response
            self.assertTrue(any(term in response_lower for term in query_terms))
    
    @patch('pdf_processor_simple.PDFProcessor.extract_text_from_pdf')
    async def test_context_aware_rag_search(self, mock_extract):
        """Test context-aware RAG search."""
        # Mock the text extraction
        def mock_extract_text(pdf_path):
            filename = os.path.basename(pdf_path)
            text_path = os.path.join(self.pdf_dir, f"{filename}.txt")
            if os.path.exists(text_path):
                with open(text_path, "r") as f:
                    return f.read()
            return ""
        
        mock_extract.side_effect = mock_extract_text
        
        # Process PDFs and load knowledge base
        await self.pdf_processor.process_all_pdfs()
        self.knowledge_base.load_all_knowledge()
        
        # Test conversation context
        session_id = "test_session"
        
        # First query to establish context
        query1 = "What are your business hours?"
        response1 = await self.rag_engine.search_and_generate(query1, "", session_id)
        
        # Verify first response
        self.assertIsNotNone(response1)
        self.assertIn("monday-friday", response1.answer.lower())
        self.assertIn("9am-5pm", response1.answer.lower())
        
        # Follow-up query that relies on context
        query2 = "Can I schedule an appointment outside those hours?"
        context2 = f"Previous question: {query1}"
        response2 = await self.rag_engine.search_and_generate(query2, context2, session_id)
        
        # Verify that context was used
        self.assertIsNotNone(response2)
        self.assertGreater(len(response2.answer), 0)
        
        # The response should reference business hours or appointments
        self.assertTrue(
            "hour" in response2.answer.lower() or
            "appointment" in response2.answer.lower() or
            "schedule" in response2.answer.lower()
        )
    
    @patch('pdf_processor_simple.PDFProcessor.extract_text_from_pdf')
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_file_monitor_integration(self, mock_observer, mock_extract):
        """Test file monitor integration with PDF processing."""
        # Mock the text extraction
        def mock_extract_text(pdf_path):
            filename = os.path.basename(pdf_path)
            text_path = os.path.join(self.pdf_dir, f"{filename}.txt")
            if os.path.exists(text_path):
                with open(text_path, "r") as f:
                    return f.read()
            return ""
        
        mock_extract.side_effect = mock_extract_text
        
        # Create a callback to track processed files
        processed_files = []
        
        async def process_callback(file_path):
            processed_files.append(file_path)
            await self.pdf_processor.process_pdf(file_path)
        
        # Initialize file monitor
        file_monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=process_callback
        )
        
        # Start monitoring
        file_monitor.start_monitoring()
        
        # Process initial files
        await file_monitor.process_existing_files()
        
        # Verify that existing files were processed
        self.assertEqual(len(processed_files), 3)
        
        # Add a new file
        new_pdf_content = """
        NEW DOCUMENT
        
        This is a new document added during monitoring.
        
        Q: What is the new feature?
        A: The new feature allows real-time document processing.
        """
        
        self._create_test_pdf("new_document.pdf", new_pdf_content)
        
        # Simulate file change event
        await file_monitor.handle_file_change(os.path.join(self.pdf_dir, "new_document.pdf"))
        
        # Verify that the new file was processed
        self.assertEqual(len(processed_files), 4)
        self.assertIn(os.path.join(self.pdf_dir, "new_document.pdf"), processed_files)
        
        # Stop monitoring
        file_monitor.stop_monitoring()

if __name__ == "__main__":
    unittest.main()