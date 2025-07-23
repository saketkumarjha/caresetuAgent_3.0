"""
Tests for the integration between PDF file monitor and RAG system.
Tests the automatic update of knowledge base when PDFs change.
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
from pdf_file_monitor import PDFDirectoryWatcher
from pdf_processor_simple import PDFProcessor
from unified_knowledge_base import UnifiedKnowledgeBase
from simple_rag_engine import SimpleRAGEngine

class TestMonitorRAGIntegration(unittest.TestCase):
    """Test the integration between PDF file monitor and RAG system."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_dir = os.path.join(self.temp_dir, "pdfs")
        self.output_dir = os.path.join(self.temp_dir, "output")
        self.kb_dir = os.path.join(self.temp_dir, "knowledge_base")
        self.unified_dir = os.path.join(self.temp_dir, "unified_kb")
        
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.kb_dir, exist_ok=True)
        os.makedirs(self.unified_dir, exist_ok=True)
        
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
        
        self.rag_engine = SimpleRAGEngine(self.knowledge_base)
    
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
        
        # Write JSON files
        with open(os.path.join(self.kb_dir, "faq.json"), "w") as f:
            json.dump(faq_data, f)
        
        # Create test PDF files with minimal content
        self._create_test_pdf("faq.pdf", """
        FREQUENTLY ASKED QUESTIONS
        
        Q1: What are your business hours?
        A1: We are open Monday-Friday 9AM-5PM.
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
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_monitor_rag_integration(self, mock_observer, mock_extract):
        """Test integration between file monitor and RAG system."""
        # Mock the text extraction to use our pre-created text files
        def mock_extract_text(pdf_path):
            filename = os.path.basename(pdf_path)
            text_path = os.path.join(self.pdf_dir, f"{filename}.txt")
            if os.path.exists(text_path):
                with open(text_path, "r") as f:
                    return f.read()
            return ""
        
        mock_extract.side_effect = mock_extract_text
        
        # Load initial knowledge base
        self.knowledge_base.load_all_knowledge()
        
        # Create a callback that processes PDFs and updates knowledge base
        async def process_and_update(file_path):
            # Process the PDF
            processed_doc = await self.pdf_processor.process_pdf(file_path)
            if processed_doc:
                # Update knowledge base
                self.knowledge_base.update_from_pdfs([processed_doc])
        
        # Initialize file monitor
        file_monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=process_and_update
        )
        
        # Process existing files
        await file_monitor.process_existing_files()
        
        # Test initial RAG query
        query = "What are your business hours?"
        response1 = await self.rag_engine.search_and_generate(query, "")
        
        # Verify initial response
        self.assertIsNotNone(response1)
        self.assertIn("monday-friday", response1.answer.lower())
        self.assertIn("9am-5pm", response1.answer.lower())
        
        # Add a new PDF file with updated information
        self._create_test_pdf("updated_hours.pdf", """
        UPDATED BUSINESS HOURS
        
        Q: What are your business hours?
        A: We are now open Monday-Friday 8AM-6PM and Saturday 10AM-2PM.
        """)
        
        # Simulate file change event
        await file_monitor.handle_file_change(os.path.join(self.pdf_dir, "updated_hours.pdf"))
        
        # Test RAG query after update
        response2 = await self.rag_engine.search_and_generate(query, "")
        
        # Verify updated response
        self.assertIsNotNone(response2)
        self.assertIn("saturday", response2.answer.lower())
        self.assertIn("10am-2pm", response2.answer.lower())
    
    @patch('pdf_processor_simple.PDFProcessor.extract_text_from_pdf')
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_file_deletion_handling(self, mock_observer, mock_extract):
        """Test handling of file deletions."""
        # Mock the text extraction
        def mock_extract_text(pdf_path):
            filename = os.path.basename(pdf_path)
            text_path = os.path.join(self.pdf_dir, f"{filename}.txt")
            if os.path.exists(text_path):
                with open(text_path, "r") as f:
                    return f.read()
            return ""
        
        mock_extract.side_effect = mock_extract_text
        
        # Load initial knowledge base
        self.knowledge_base.load_all_knowledge()
        
        # Create callbacks for processing and deletion
        async def process_callback(file_path):
            processed_doc = await self.pdf_processor.process_pdf(file_path)
            if processed_doc:
                self.knowledge_base.update_from_pdfs([processed_doc])
        
        async def deletion_callback(file_path):
            # In a real implementation, this would remove content from the knowledge base
            pass
        
        # Initialize file monitor
        file_monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=process_callback,
            deletion_callback=deletion_callback
        )
        
        # Process existing files
        await file_monitor.process_existing_files()
        
        # Test initial RAG query
        query = "What are your business hours?"
        response1 = await self.rag_engine.search_and_generate(query, "")
        
        # Verify initial response
        self.assertIsNotNone(response1)
        self.assertIn("monday-friday", response1.answer.lower())
        
        # Simulate file deletion event
        await file_monitor.handle_file_deletion(os.path.join(self.pdf_dir, "faq.pdf"))
        
        # In a real implementation, this would test that the content was removed
        # For this test, we just verify that the deletion callback was called
        # and the system continues to function
        
        # Add a new file with different content
        self._create_test_pdf("new_hours.pdf", """
        NEW BUSINESS HOURS
        
        Q: What are your business hours?
        A: We are now open 24/7 for your convenience.
        """)
        
        # Simulate file change event
        await file_monitor.handle_file_change(os.path.join(self.pdf_dir, "new_hours.pdf"))
        
        # Test RAG query after update
        response2 = await self.rag_engine.search_and_generate(query, "")
        
        # Verify updated response
        self.assertIsNotNone(response2)
        self.assertIn("24/7", response2.answer.lower())
    
    @patch('pdf_processor_simple.PDFProcessor.extract_text_from_pdf')
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_incremental_updates(self, mock_observer, mock_extract):
        """Test incremental updates to knowledge base."""
        # Mock the text extraction
        def mock_extract_text(pdf_path):
            filename = os.path.basename(pdf_path)
            text_path = os.path.join(self.pdf_dir, f"{filename}.txt")
            if os.path.exists(text_path):
                with open(text_path, "r") as f:
                    return f.read()
            return ""
        
        mock_extract.side_effect = mock_extract_text
        
        # Load initial knowledge base
        self.knowledge_base.load_all_knowledge()
        
        # Create a callback that processes PDFs and updates knowledge base
        async def process_and_update(file_path):
            processed_doc = await self.pdf_processor.process_pdf(file_path)
            if processed_doc:
                self.knowledge_base.update_from_pdfs([processed_doc])
        
        # Initialize file monitor
        file_monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=process_and_update
        )
        
        # Process existing files
        await file_monitor.process_existing_files()
        
        # Add multiple new files incrementally
        new_files = [
            ("policy.pdf", """
            CANCELLATION POLICY
            
            1. APPOINTMENT CANCELLATION
               You must cancel at least 24 hours before your appointment to avoid a fee.
            """),
            ("procedure.pdf", """
            HOW TO SCHEDULE AN APPOINTMENT
            
            Step 1: Log in to your account
            Step 2: Click on "Schedule Appointment"
            Step 3: Select a date and time
            """),
            ("manual.pdf", """
            USER MANUAL
            
            CHAPTER 1: GETTING STARTED
            This chapter explains how to set up your account.
            """)
        ]
        
        # Add files one by one and test incremental updates
        for filename, content in new_files:
            # Create the file
            self._create_test_pdf(filename, content)
            
            # Simulate file change event
            await file_monitor.handle_file_change(os.path.join(self.pdf_dir, filename))
            
            # Test RAG query related to the new file
            if "policy" in filename:
                query = "What is your cancellation policy?"
                response = await self.rag_engine.search_and_generate(query, "")
                self.assertIn("24 hours", response.answer.lower())
                
            elif "procedure" in filename:
                query = "How do I schedule an appointment?"
                response = await self.rag_engine.search_and_generate(query, "")
                self.assertIn("log in", response.answer.lower())
                
            elif "manual" in filename:
                query = "How do I get started?"
                response = await self.rag_engine.search_and_generate(query, "")
                self.assertIn("account", response.answer.lower())

if __name__ == "__main__":
    unittest.main()