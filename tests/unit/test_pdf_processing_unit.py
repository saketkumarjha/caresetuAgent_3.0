"""
Unit tests for PDF processing components.
Tests the PDF processor, document type detector, and document parsers.
"""

import os
import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import components to test
from pdf_processor_simple import PDFProcessor, DocumentType
from document_type_detector import DocumentTypeDetector
from document_parsers import DocumentParser, DocumentSection

class TestPDFProcessor(unittest.TestCase):
    """Test the PDF processor component."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_dir = os.path.join(self.temp_dir, "pdfs")
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # Create a processor instance for testing
        self.processor = PDFProcessor(
            pdf_directory=self.pdf_dir,
            output_directory=self.output_dir
        )
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    @patch('pdf_processor_simple.PDFProcessor.extract_text_from_pdf')
    def test_process_pdf(self, mock_extract):
        """Test processing a single PDF file."""
        # Mock the text extraction
        mock_extract.return_value = """
        FREQUENTLY ASKED QUESTIONS
        
        Q1: What are your business hours?
        A1: We are open Monday-Friday 9AM-5PM.
        
        Q2: How do I schedule an appointment?
        A2: You can schedule online or call our office.
        """
        
        # Create a test PDF file
        test_pdf_path = os.path.join(self.pdf_dir, "test_faq.pdf")
        with open(test_pdf_path, "wb") as f:
            f.write(b"%PDF-1.5\n")  # Minimal PDF header
        
        # Process the PDF
        result = asyncio.run(self.processor.process_pdf(test_pdf_path))
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["filename"], "test_faq.pdf")
        self.assertEqual(result["document_type"], DocumentType.FAQ)
        
        # Check that output files were created
        files = os.listdir(self.output_dir)
        self.assertTrue(any("_content.txt" in f for f in files))
        self.assertTrue(any("_metadata.json" in f for f in files))
    
    @patch('pdf_processor_simple.PDFProcessor.extract_text_from_pdf')
    def test_detect_document_type(self, mock_extract):
        """Test document type detection."""
        # Test different document types
        test_cases = [
            ("faq.pdf", "What are FAQs? Frequently Asked Questions", DocumentType.FAQ),
            ("policy.pdf", "Company Policies and Procedures", DocumentType.POLICY),
            ("procedure.pdf", "Step 1: Do this. Step 2: Do that.", DocumentType.PROCEDURE),
            ("manual.pdf", "User Manual Chapter 1: Introduction", DocumentType.MANUAL),
            ("general.pdf", "General information about our company", DocumentType.GENERAL)
        ]
        
        for filename, content, expected_type in test_cases:
            detected_type = self.processor.detect_document_type(content, filename)
            self.assertEqual(detected_type, expected_type, f"Failed for {filename}")
    
    @patch('pdf_processor_simple.PDFProcessor.process_pdf')
    def test_process_all_pdfs(self, mock_process):
        """Test processing all PDFs in a directory."""
        # Create test PDF files
        pdf_files = ["test1.pdf", "test2.pdf", "test3.pdf"]
        for pdf_file in pdf_files:
            with open(os.path.join(self.pdf_dir, pdf_file), "wb") as f:
                f.write(b"%PDF-1.5\n")  # Minimal PDF header
        
        # Mock the process_pdf method
        mock_process.side_effect = lambda path: {"filename": os.path.basename(path), "document_type": DocumentType.GENERAL}
        
        # Process all PDFs
        results = asyncio.run(self.processor.process_all_pdfs())
        
        # Verify results
        self.assertEqual(len(results), 3)
        self.assertEqual(mock_process.call_count, 3)

class TestDocumentTypeDetector(unittest.TestCase):
    """Test the document type detector component."""
    
    def setUp(self):
        """Set up test environment."""
        self.detector = DocumentTypeDetector()
    
    def test_detect_document_type(self):
        """Test document type detection with various content."""
        # Test FAQ detection
        faq_content = """
        FREQUENTLY ASKED QUESTIONS
        
        Q1: What are your business hours?
        A1: We are open Monday-Friday 9AM-5PM.
        
        Q2: How do I schedule an appointment?
        A2: You can schedule online or call our office.
        """
        doc_type, confidence = self.detector.detect_document_type(faq_content, "document.pdf")
        self.assertEqual(doc_type, DocumentType.FAQ)
        self.assertGreaterEqual(confidence, 0.7)
        
        # Test policy detection
        policy_content = """
        PRIVACY POLICY
        
        1. INFORMATION COLLECTION
           We collect personal information when you use our services.
        
        2. DATA USAGE
           We use your data to improve our services.
        """
        doc_type, confidence = self.detector.detect_document_type(policy_content, "document.pdf")
        self.assertEqual(doc_type, DocumentType.POLICY)
        self.assertGreaterEqual(confidence, 0.7)
        
        # Test procedure detection
        procedure_content = """
        HOW TO SCHEDULE AN APPOINTMENT
        
        Step 1: Log in to your account
        Step 2: Click on "Schedule Appointment"
        Step 3: Select a date and time
        Step 4: Confirm your appointment
        """
        doc_type, confidence = self.detector.detect_document_type(procedure_content, "document.pdf")
        self.assertEqual(doc_type, DocumentType.PROCEDURE)
        self.assertGreaterEqual(confidence, 0.7)
        
        # Test manual detection
        manual_content = """
        USER MANUAL
        
        CHAPTER 1: GETTING STARTED
        This chapter explains how to set up your account.
        
        CHAPTER 2: USING THE SYSTEM
        This chapter explains how to use the system.
        """
        doc_type, confidence = self.detector.detect_document_type(manual_content, "document.pdf")
        self.assertEqual(doc_type, DocumentType.MANUAL)
        self.assertGreaterEqual(confidence, 0.7)
        
        # Test general content detection
        general_content = """
        This is some general information about our company.
        We provide various services to our customers.
        """
        doc_type, confidence = self.detector.detect_document_type(general_content, "document.pdf")
        self.assertEqual(doc_type, DocumentType.GENERAL)
    
    def test_filename_based_detection(self):
        """Test document type detection based on filename."""
        # Test different filenames
        test_cases = [
            ("faq.pdf", "Some content", DocumentType.FAQ),
            ("frequently_asked_questions.pdf", "Some content", DocumentType.FAQ),
            ("privacy_policy.pdf", "Some content", DocumentType.POLICY),
            ("terms_and_conditions.pdf", "Some content", DocumentType.POLICY),
            ("procedure_guide.pdf", "Some content", DocumentType.PROCEDURE),
            ("how_to_guide.pdf", "Some content", DocumentType.PROCEDURE),
            ("user_manual.pdf", "Some content", DocumentType.MANUAL),
            ("handbook.pdf", "Some content", DocumentType.MANUAL),
            ("general_info.pdf", "Some content", DocumentType.GENERAL)
        ]
        
        for filename, content, expected_type in test_cases:
            doc_type, confidence = self.detector.detect_document_type(content, filename)
            self.assertEqual(doc_type, expected_type, f"Failed for {filename}")
            if expected_type != DocumentType.GENERAL:
                self.assertGreaterEqual(confidence, 0.9)  # High confidence for filename match
    
    def test_analyze_document_structure(self):
        """Test document structure analysis."""
        content = """
        FREQUENTLY ASKED QUESTIONS
        
        Q1: What are your business hours?
        A1: We are open Monday-Friday 9AM-5PM.
        
        Q2: How do I schedule an appointment?
        A2: You can schedule online at https://example.com or call our office at (555) 123-4567.
        
        For more information, contact support@example.com.
        
        • Item 1
        • Item 2
        
        1. First step
        2. Second step
        """
        
        analysis = self.detector.analyze_document_structure(content)
        
        self.assertGreaterEqual(analysis["paragraphs"], 3)
        self.assertEqual(analysis["questions"], 2)
        self.assertGreaterEqual(analysis["numbered_items"], 2)
        self.assertGreaterEqual(analysis["bullet_points"], 2)
        self.assertEqual(analysis["urls"], 1)
        self.assertEqual(analysis["emails"], 1)

class TestDocumentParser(unittest.TestCase):
    """Test the document parser component."""
    
    def setUp(self):
        """Set up test environment."""
        self.parser = DocumentParser()
    
    def test_parse_faq_document(self):
        """Test parsing FAQ document."""
        faq_content = """
        FREQUENTLY ASKED QUESTIONS
        
        Q1: What are your business hours?
        A1: We are open Monday-Friday 9AM-5PM.
        
        Q2: How do I schedule an appointment?
        A2: You can schedule online or call our office.
        """
        
        sections = self.parser.parse_document(faq_content, DocumentType.FAQ, "faq.pdf")
        
        self.assertGreaterEqual(len(sections), 2)  # At least 2 Q&A pairs
        self.assertEqual(sections[0].section_type, "qa_pair")
        self.assertIn("business hours", sections[0].title.lower())
        self.assertIn("monday-friday", sections[0].content.lower())
    
    def test_parse_policy_document(self):
        """Test parsing policy document."""
        policy_content = """
        PRIVACY POLICY
        
        1. INFORMATION COLLECTION
           We collect personal information when you use our services.
        
        2. DATA USAGE
           We use your data to improve our services.
        """
        
        sections = self.parser.parse_document(policy_content, DocumentType.POLICY, "policy.pdf")
        
        self.assertGreaterEqual(len(sections), 2)  # At least 2 sections
        self.assertEqual(sections[0].section_type, "policy_section")
        self.assertIn("information collection", sections[0].title.lower())
        self.assertIn("personal information", sections[0].content.lower())
    
    def test_parse_procedure_document(self):
        """Test parsing procedure document."""
        procedure_content = """
        HOW TO SCHEDULE AN APPOINTMENT
        
        Step 1: Log in to your account
        Step 2: Click on "Schedule Appointment"
        Step 3: Select a date and time
        Step 4: Confirm your appointment
        """
        
        sections = self.parser.parse_document(procedure_content, DocumentType.PROCEDURE, "procedure.pdf")
        
        self.assertGreaterEqual(len(sections), 4)  # At least 4 steps
        self.assertEqual(sections[0].section_type, "step")
        self.assertIn("log in", sections[0].content.lower())
    
    def test_parse_manual_document(self):
        """Test parsing manual document."""
        manual_content = """
        USER MANUAL
        
        CHAPTER 1: GETTING STARTED
        This chapter explains how to set up your account.
        
        CHAPTER 2: USING THE SYSTEM
        This chapter explains how to use the system.
        """
        
        sections = self.parser.parse_document(manual_content, DocumentType.MANUAL, "manual.pdf")
        
        self.assertGreaterEqual(len(sections), 2)  # At least 2 chapters
        self.assertEqual(sections[0].section_type, "chapter")
        self.assertIn("getting started", sections[0].title.lower())
        self.assertIn("set up your account", sections[0].content.lower())
    
    def test_parse_general_document(self):
        """Test parsing general document."""
        general_content = """
        COMPANY INFORMATION
        
        ABOUT US
        We are a healthcare company dedicated to providing quality services.
        
        SERVICES
        We offer various healthcare services to our customers.
        """
        
        sections = self.parser.parse_document(general_content, DocumentType.GENERAL, "general.pdf")
        
        self.assertGreaterEqual(len(sections), 2)  # At least 2 sections
        self.assertEqual(sections[0].section_type, "paragraph")
        self.assertIn("company information", sections[0].title.lower())

if __name__ == "__main__":
    unittest.main()