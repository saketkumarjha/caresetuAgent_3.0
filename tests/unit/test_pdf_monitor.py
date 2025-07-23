"""
Tests for the PDF file monitor component.
Tests the file system monitoring and automatic updates.
"""

import os
import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock, call

# Import components to test
from pdf_file_monitor import PDFDirectoryWatcher
from pdf_processor_simple import PDFProcessor

class TestPDFMonitor(unittest.TestCase):
    """Test the PDF file monitor component."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.pdf_dir = os.path.join(self.temp_dir, "pdfs")
        self.output_dir = os.path.join(self.temp_dir, "output")
        
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create test PDF files
        self._create_test_pdf_files()
        
        # Create a processor instance for testing
        self.processor = PDFProcessor(
            pdf_directory=self.pdf_dir,
            output_directory=self.output_dir
        )
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_pdf_files(self):
        """Create test PDF files."""
        # Create minimal PDF files
        for i in range(3):
            pdf_path = os.path.join(self.pdf_dir, f"test{i}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(b"%PDF-1.5\n")  # Minimal PDF header
    
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    def test_monitor_initialization(self, mock_observer):
        """Test file monitor initialization."""
        # Create a callback function
        async def callback(file_path):
            pass
        
        # Initialize file monitor
        monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=callback
        )
        
        # Verify initialization
        self.assertEqual(monitor.directory, self.pdf_dir)
        self.assertEqual(monitor.callback, callback)
        self.assertFalse(monitor.is_monitoring)
    
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    def test_start_stop_monitoring(self, mock_observer):
        """Test starting and stopping monitoring."""
        # Create a callback function
        async def callback(file_path):
            pass
        
        # Initialize file monitor
        monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=callback
        )
        
        # Start monitoring
        monitor.start_monitoring()
        
        # Verify that monitoring was started
        self.assertTrue(monitor.is_monitoring)
        mock_observer.assert_called_once()
        
        # Stop monitoring
        monitor.stop_monitoring()
        
        # Verify that monitoring was stopped
        self.assertFalse(monitor.is_monitoring)
    
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_process_existing_files(self, mock_observer):
        """Test processing existing files."""
        # Create a callback to track processed files
        processed_files = []
        
        async def callback(file_path):
            processed_files.append(file_path)
        
        # Initialize file monitor
        monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=callback
        )
        
        # Process existing files
        await monitor.process_existing_files()
        
        # Verify that all files were processed
        self.assertEqual(len(processed_files), 3)
        for i in range(3):
            self.assertIn(os.path.join(self.pdf_dir, f"test{i}.pdf"), processed_files)
    
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_handle_file_change(self, mock_observer):
        """Test handling file change events."""
        # Create a callback to track processed files
        processed_files = []
        
        async def callback(file_path):
            processed_files.append(file_path)
        
        # Initialize file monitor
        monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=callback
        )
        
        # Create a new file
        new_file_path = os.path.join(self.pdf_dir, "new_file.pdf")
        with open(new_file_path, "wb") as f:
            f.write(b"%PDF-1.5\n")  # Minimal PDF header
        
        # Handle file change event
        await monitor.handle_file_change(new_file_path)
        
        # Verify that the file was processed
        self.assertIn(new_file_path, processed_files)
    
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_handle_file_deletion(self, mock_observer):
        """Test handling file deletion events."""
        # Create a callback to track deleted files
        deleted_files = []
        
        async def callback(file_path):
            pass
        
        async def deletion_callback(file_path):
            deleted_files.append(file_path)
        
        # Initialize file monitor
        monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=callback,
            deletion_callback=deletion_callback
        )
        
        # Handle file deletion event
        file_path = os.path.join(self.pdf_dir, "test0.pdf")
        await monitor.handle_file_deletion(file_path)
        
        # Verify that the file was processed
        self.assertIn(file_path, deleted_files)
    
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    @patch('pdf_processor_simple.PDFProcessor.process_pdf')
    async def test_integration_with_processor(self, mock_process, mock_observer):
        """Test integration with PDF processor."""
        # Mock the process_pdf method
        mock_process.return_value = {"filename": "test.pdf", "document_type": "faq"}
        
        # Create a callback that uses the processor
        async def callback(file_path):
            await self.processor.process_pdf(file_path)
        
        # Initialize file monitor
        monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=callback
        )
        
        # Process existing files
        await monitor.process_existing_files()
        
        # Verify that processor was called for each file
        self.assertEqual(mock_process.call_count, 3)
        
        # Verify call arguments
        expected_calls = [
            call(os.path.join(self.pdf_dir, "test0.pdf")),
            call(os.path.join(self.pdf_dir, "test1.pdf")),
            call(os.path.join(self.pdf_dir, "test2.pdf"))
        ]
        mock_process.assert_has_calls(expected_calls, any_order=True)
    
    @patch('pdf_file_monitor.PDFDirectoryWatcher._start_observer')
    async def test_retry_mechanism(self, mock_observer):
        """Test retry mechanism for file processing."""
        # Create a callback that fails on first attempt
        attempt_count = {}
        
        async def failing_callback(file_path):
            if file_path not in attempt_count:
                attempt_count[file_path] = 0
            
            attempt_count[file_path] += 1
            
            if attempt_count[file_path] == 1:
                raise Exception("Simulated failure")
        
        # Initialize file monitor with retry settings
        monitor = PDFDirectoryWatcher(
            directory=self.pdf_dir,
            callback=failing_callback,
            max_retries=3,
            retry_delay=0.1
        )
        
        # Handle file change event
        file_path = os.path.join(self.pdf_dir, "test0.pdf")
        await monitor.handle_file_change(file_path)
        
        # Verify that the callback was retried
        self.assertEqual(attempt_count[file_path], 2)  # First attempt fails, second succeeds

if __name__ == "__main__":
    unittest.main()