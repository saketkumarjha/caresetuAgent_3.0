"""
PDF File System Monitor
Monitors PDF directory for changes and triggers automatic updates
"""

import os
import asyncio
import logging
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileEventType(Enum):
    """Types of file system events."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"

@dataclass
class FileSystemEvent:
    """Represents a file system event."""
    event_type: FileEventType
    file_path: str
    timestamp: datetime
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    old_path: Optional[str] = None  # For move events

class RetryManager:
    """Manages retry logic with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Initialize retry manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_counts: Dict[str, int] = {}
        self.last_attempt: Dict[str, datetime] = {}
    
    def should_retry(self, file_path: str) -> bool:
        """
        Check if a file should be retried.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if should retry, False otherwise
        """
        retry_count = self.retry_counts.get(file_path, 0)
        return retry_count < self.max_retries
    
    def get_delay(self, file_path: str) -> float:
        """
        Get delay for next retry attempt.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Delay in seconds
        """
        retry_count = self.retry_counts.get(file_path, 0)
        delay = self.base_delay * (2 ** retry_count)
        return min(delay, self.max_delay)
    
    def record_attempt(self, file_path: str):
        """
        Record a retry attempt.
        
        Args:
            file_path: Path to the file
        """
        self.retry_counts[file_path] = self.retry_counts.get(file_path, 0) + 1
        self.last_attempt[file_path] = datetime.now()
    
    def reset_retries(self, file_path: str):
        """
        Reset retry count for a file.
        
        Args:
            file_path: Path to the file
        """
        self.retry_counts.pop(file_path, None)
        self.last_attempt.pop(file_path, None)

class ChangeHandler:
    """Processes file system events."""
    
    def __init__(self, callback: Callable[[FileSystemEvent], None]):
        """
        Initialize change handler.
        
        Args:
            callback: Callback function to handle events
        """
        self.callback = callback
        self.retry_manager = RetryManager()
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info("Change handler initialized")
    
    async def start(self):
        """Start the change handler."""
        if self._running:
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Change handler started")
    
    async def stop(self):
        """Stop the change handler."""
        if not self._running:
            return
        
        self._running = False
        
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        self.executor.shutdown(wait=True)
        logger.info("Change handler stopped")
    
    async def handle_event(self, event: FileSystemEvent):
        """
        Handle a file system event.
        
        Args:
            event: File system event to handle
        """
        await self.processing_queue.put(event)
    
    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                # Wait for event with timeout to allow checking _running flag
                event = await asyncio.wait_for(self.processing_queue.get(), timeout=1.0)
                await self._process_single_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing events: {e}")
    
    async def _process_single_event(self, event: FileSystemEvent):
        """
        Process a single file system event.
        
        Args:
            event: File system event to process
        """
        try:
            logger.info(f"Processing event: {event.event_type.value} for {event.file_path}")
            
            # Call the callback in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self.callback, event)
            
            # Reset retry count on successful processing
            self.retry_manager.reset_retries(event.file_path)
            
        except Exception as e:
            logger.error(f"Error processing event for {event.file_path}: {e}")
            
            # Handle retry logic
            if self.retry_manager.should_retry(event.file_path):
                self.retry_manager.record_attempt(event.file_path)
                delay = self.retry_manager.get_delay(event.file_path)
                
                logger.info(f"Scheduling retry for {event.file_path} in {delay} seconds")
                
                # Schedule retry
                asyncio.create_task(self._schedule_retry(event, delay))
            else:
                logger.error(f"Max retries exceeded for {event.file_path}")
                self.retry_manager.reset_retries(event.file_path)
    
    async def _schedule_retry(self, event: FileSystemEvent, delay: float):
        """
        Schedule a retry for an event.
        
        Args:
            event: Event to retry
            delay: Delay before retry
        """
        await asyncio.sleep(delay)
        await self.processing_queue.put(event)

class UpdateScheduler:
    """Manages incremental updates."""
    
    def __init__(self):
        """Initialize update scheduler."""
        self.pending_updates: Dict[str, FileSystemEvent] = {}
        self.batch_delay = 5.0  # Seconds to wait before processing batch
        self.last_update: Dict[str, datetime] = {}
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("Update scheduler initialized")
    
    async def start(self):
        """Start the update scheduler."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._process_updates())
        logger.info("Update scheduler started")
    
    async def stop(self):
        """Stop the update scheduler."""
        if not self._running:
            return
        
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Update scheduler stopped")
    
    def schedule_update(self, event: FileSystemEvent):
        """
        Schedule an update for a file.
        
        Args:
            event: File system event
        """
        # Store the latest event for each file
        self.pending_updates[event.file_path] = event
        logger.debug(f"Scheduled update for {event.file_path}")
    
    async def _process_updates(self):
        """Process pending updates in batches."""
        while self._running:
            try:
                await asyncio.sleep(self.batch_delay)
                
                if not self.pending_updates:
                    continue
                
                # Get pending updates
                updates_to_process = dict(self.pending_updates)
                self.pending_updates.clear()
                
                logger.info(f"Processing batch of {len(updates_to_process)} updates")
                
                # Process each update
                for file_path, event in updates_to_process.items():
                    try:
                        await self._process_update(event)
                        self.last_update[file_path] = datetime.now()
                    except Exception as e:
                        logger.error(f"Error processing update for {file_path}: {e}")
                        # Re-schedule failed update
                        self.pending_updates[file_path] = event
                
            except Exception as e:
                logger.error(f"Error in update scheduler: {e}")
    
    async def _process_update(self, event: FileSystemEvent):
        """
        Process a single update.
        
        Args:
            event: File system event to process
        """
        # This method should be overridden by subclasses or set via callback
        logger.info(f"Processing update: {event.event_type.value} for {event.file_path}")

class PDFDirectoryWatcher:
    """Monitors company_pdfs directory for changes."""
    
    def __init__(self, 
                 directory: str = "company_pdfs",
                 callback: Optional[Callable[[FileSystemEvent], None]] = None):
        """
        Initialize PDF directory watcher.
        
        Args:
            directory: Directory to monitor
            callback: Callback function for file changes
        """
        self.directory = Path(directory)
        self.callback = callback
        self.change_handler = ChangeHandler(self._internal_handle_change)
        self.update_scheduler = UpdateScheduler()
        
        # File tracking
        self.file_states: Dict[str, Dict[str, Any]] = {}
        self.monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Ensure directory exists
        self.directory.mkdir(exist_ok=True)
        
        logger.info(f"PDF directory watcher initialized for: {directory}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File hash
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'hash': self._calculate_file_hash(file_path)
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}
    
    def _scan_directory(self) -> Dict[str, Dict[str, Any]]:
        """
        Scan directory for PDF files.
        
        Returns:
            Dictionary mapping file paths to file information
        """
        current_files = {}
        
        try:
            for file_path in self.directory.glob("*.pdf"):
                if file_path.is_file():
                    file_info = self._get_file_info(str(file_path))
                    if file_info:
                        current_files[str(file_path)] = file_info
        except Exception as e:
            logger.error(f"Error scanning directory {self.directory}: {e}")
        
        return current_files
    
    def _detect_changes(self, current_files: Dict[str, Dict[str, Any]]) -> List[FileSystemEvent]:
        """
        Detect changes between current and previous file states.
        
        Args:
            current_files: Current file states
            
        Returns:
            List of file system events
        """
        events = []
        current_time = datetime.now()
        
        # Check for new and modified files
        for file_path, file_info in current_files.items():
            if file_path not in self.file_states:
                # New file
                events.append(FileSystemEvent(
                    event_type=FileEventType.CREATED,
                    file_path=file_path,
                    timestamp=current_time,
                    file_size=file_info.get('size'),
                    file_hash=file_info.get('hash')
                ))
            elif file_info.get('hash') != self.file_states[file_path].get('hash'):
                # Modified file
                events.append(FileSystemEvent(
                    event_type=FileEventType.MODIFIED,
                    file_path=file_path,
                    timestamp=current_time,
                    file_size=file_info.get('size'),
                    file_hash=file_info.get('hash')
                ))
        
        # Check for deleted files
        for file_path in self.file_states:
            if file_path not in current_files:
                events.append(FileSystemEvent(
                    event_type=FileEventType.DELETED,
                    file_path=file_path,
                    timestamp=current_time
                ))
        
        return events
    
    def _internal_handle_change(self, event: FileSystemEvent):
        """
        Internal handler for change events (called by ChangeHandler).
        
        Args:
            event: File system event
        """
        logger.info(f"Handling change: {event.event_type.value} for {event.file_path}")
        
        # Schedule update
        self.update_scheduler.schedule_update(event)
        
        # Call external callback if provided
        if self.callback:
            try:
                if asyncio.iscoroutinefunction(self.callback):
                    # For async callbacks, we need to handle them properly
                    try:
                        # Try to get the current event loop
                        loop = asyncio.get_running_loop()
                        # Schedule the coroutine to run in the main thread
                        future = asyncio.run_coroutine_threadsafe(self.callback(event), loop)
                        # Wait for completion with timeout
                        future.result(timeout=30)
                    except RuntimeError:
                        # No running loop, create a new one
                        asyncio.run(self.callback(event))
                else:
                    # Synchronous callback
                    self.callback(event)
            except Exception as e:
                logger.error(f"Error in callback for {event.file_path}: {e}")
                raise  # Re-raise to trigger retry mechanism
    
    async def start_monitoring(self):
        """Start monitoring the PDF directory."""
        if self.monitoring:
            logger.warning("Already monitoring")
            return
        
        self.monitoring = True
        
        # Start components
        await self.change_handler.start()
        await self.update_scheduler.start()
        
        # Initial scan
        self.file_states = self._scan_directory()
        logger.info(f"Initial scan found {len(self.file_states)} PDF files")
        
        # Start monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        
        logger.info("PDF directory monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring the PDF directory."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        
        # Stop monitoring task
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop components
        await self.change_handler.stop()
        await self.update_scheduler.stop()
        
        logger.info("PDF directory monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Scan for changes
                current_files = self._scan_directory()
                events = self._detect_changes(current_files)
                
                # Process events
                for event in events:
                    await self.change_handler.handle_event(event)
                
                # Update file states
                self.file_states = current_files
                
                # Wait before next scan
                await asyncio.sleep(2.0)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5.0)  # Wait longer on error
    
    def get_monitored_files(self) -> List[str]:
        """
        Get list of currently monitored files.
        
        Returns:
            List of file paths
        """
        return list(self.file_states.keys())
    
    def get_file_status(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File status information or None if not found
        """
        return self.file_states.get(file_path)

# Integration class for the PDF RAG system
class PDFMonitorIntegration:
    """Integrates PDF file monitoring with the RAG system."""
    
    def __init__(self, 
                 pdf_processor=None,
                 knowledge_base=None,
                 directory: str = "company_pdfs"):
        """
        Initialize PDF monitor integration.
        
        Args:
            pdf_processor: PDF processor instance
            knowledge_base: Knowledge base instance
            directory: Directory to monitor
        """
        self.pdf_processor = pdf_processor
        self.knowledge_base = knowledge_base
        self.watcher = PDFDirectoryWatcher(directory, self._handle_file_change)
        self.processing_lock = asyncio.Lock()
        
        logger.info("PDF monitor integration initialized")
    
    async def _handle_file_change(self, event: FileSystemEvent):
        """
        Handle file change events.
        
        Args:
            event: File system event
        """
        async with self.processing_lock:
            try:
                if event.event_type == FileEventType.CREATED:
                    await self._process_new_file(event.file_path)
                elif event.event_type == FileEventType.MODIFIED:
                    await self._process_modified_file(event.file_path)
                elif event.event_type == FileEventType.DELETED:
                    await self._process_deleted_file(event.file_path)
                
                logger.info(f"Successfully processed {event.event_type.value} event for {event.file_path}")
                
            except Exception as e:
                logger.error(f"Error handling file change for {event.file_path}: {e}")
                raise
    
    async def _process_new_file(self, file_path: str):
        """
        Process a new PDF file.
        
        Args:
            file_path: Path to the new file
        """
        logger.info(f"Processing new PDF file: {file_path}")
        
        if self.pdf_processor:
            # Process the PDF
            processed_doc = await self.pdf_processor.process_pdf(file_path)
            
            if self.knowledge_base and processed_doc:
                # Update knowledge base
                self.knowledge_base.update_from_pdfs([processed_doc])
                logger.info(f"Added new PDF to knowledge base: {file_path}")
    
    async def _process_modified_file(self, file_path: str):
        """
        Process a modified PDF file.
        
        Args:
            file_path: Path to the modified file
        """
        logger.info(f"Processing modified PDF file: {file_path}")
        
        # For modified files, we need to remove old content and add new content
        if self.knowledge_base:
            # Remove old content (this would need to be implemented in knowledge base)
            # For now, we'll just reprocess and let the merger handle duplicates
            pass
        
        # Process the updated file
        await self._process_new_file(file_path)
    
    async def _process_deleted_file(self, file_path: str):
        """
        Process a deleted PDF file.
        
        Args:
            file_path: Path to the deleted file
        """
        logger.info(f"Processing deleted PDF file: {file_path}")
        
        if self.knowledge_base:
            # Remove content from knowledge base
            # This would need to be implemented in the knowledge base
            logger.info(f"Should remove content for deleted file: {file_path}")
    
    async def start(self):
        """Start the PDF monitoring integration."""
        await self.watcher.start_monitoring()
        logger.info("PDF monitoring integration started")
    
    async def stop(self):
        """Stop the PDF monitoring integration."""
        await self.watcher.stop_monitoring()
        logger.info("PDF monitoring integration stopped")

# Example usage and testing
async def test_pdf_monitor():
    """Test the PDF file monitor."""
    print("Testing PDF File Monitor")
    print("=" * 50)
    
    def handle_change(event: FileSystemEvent):
        print(f"File change detected: {event.event_type.value} - {event.file_path}")
        print(f"  Timestamp: {event.timestamp}")
        print(f"  Size: {event.file_size}")
        print(f"  Hash: {event.file_hash}")
        print()
    
    # Create monitor
    monitor = PDFDirectoryWatcher("company_pdfs", handle_change)
    
    try:
        # Start monitoring
        await monitor.start_monitoring()
        print("Monitoring started. Add, modify, or delete PDF files in company_pdfs/")
        print("Press Ctrl+C to stop...")
        
        # Monitor for a while
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        await monitor.stop_monitoring()
        print("Monitor stopped")

if __name__ == "__main__":
    asyncio.run(test_pdf_monitor())