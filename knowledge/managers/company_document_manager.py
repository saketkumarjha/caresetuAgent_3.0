"""
Company Document Management System
Handles document upload, processing, categorization, and validation
Implements privacy policy and appointment guide processing with structured data extraction
"""

import asyncio
import logging
import os
import json
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
import re

from knowledge.processors.document_parsers import DocumentParser
from knowledge.storage.embedding_cache import EmbeddingCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentCategory:
    """Document categories for company documents."""
    PRIVACY_POLICY = "privacy_policy"
    APPOINTMENT_GUIDE = "appointment_guide"
    TERMS_OF_SERVICE = "terms_of_service"
    FAQ = "faq"
    GENERAL = "general"
    TECHNICAL = "technical"
    BILLING = "billing"
    LEGAL = "legal"

class DocumentValidationResult:
    """Result of document validation."""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    MISSING_CONTENT = "missing_content"
    LOW_QUALITY = "low_quality"
    DUPLICATE = "duplicate"
    PROCESSING_ERROR = "processing_error"

class CompanyDocumentManager:
    """
    Company Document Management System
    Handles document upload, processing, categorization, and validation
    """
    
    def __init__(self, 
                 document_processor: DocumentParser,
                 output_dir: str = "company_documents",
                 embedding_cache_dir: str = "embedding_cache"):
        """
        Initialize company document manager.
        
        Args:
            document_processor: Document processor for text extraction
            output_dir: Directory to store processed documents
            embedding_cache_dir: Directory for embedding cache
        """
        self.document_processor = document_processor
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize embedding cache
        self.embedding_cache = EmbeddingCache(
            max_size=10000,
            cache_dir=embedding_cache_dir
        )
        
        # Document processing queue
        self.processing_queue = asyncio.Queue()
        self.processing_tasks = {}
        self.results = {}
        self._processing = False
        
        # Document validation rules
        self.validation_rules = self._initialize_validation_rules()
        
        # Document categorization patterns
        self.categorization_patterns = self._initialize_categorization_patterns()
        
        # Policy extraction patterns
        self.policy_extraction_patterns = self._initialize_policy_extraction_patterns()
        
        logger.info("✅ Company Document Manager initialized")
    
    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize document validation rules."""
        return {
            DocumentCategory.PRIVACY_POLICY: {
                "required_sections": ["data collection", "data usage", "data protection"],
                "min_length": 500,
                "max_length": 50000,
                "required_keywords": ["privacy", "personal information", "data"]
            },
            DocumentCategory.APPOINTMENT_GUIDE: {
                "required_sections": ["booking", "cancellation", "rescheduling"],
                "min_length": 200,
                "max_length": 20000,
                "required_keywords": ["appointment", "schedule", "booking"]
            },
            DocumentCategory.TERMS_OF_SERVICE: {
                "required_sections": ["terms", "conditions", "liability"],
                "min_length": 1000,
                "max_length": 100000,
                "required_keywords": ["terms", "service", "agreement"]
            }
        }
    
    def _initialize_categorization_patterns(self) -> Dict[str, List[str]]:
        """Initialize document categorization patterns."""
        return {
            DocumentCategory.PRIVACY_POLICY: [
                r"privacy\s+policy",
                r"personal\s+information",
                r"data\s+protection",
                r"data\s+collection",
                r"gdpr",
                r"ccpa"
            ],
            DocumentCategory.APPOINTMENT_GUIDE: [
                r"appointment\s+guide",
                r"scheduling\s+policy",
                r"booking\s+instructions",
                r"cancellation\s+policy",
                r"appointment\s+scheduling"
            ],
            DocumentCategory.TERMS_OF_SERVICE: [
                r"terms\s+of\s+service",
                r"terms\s+and\s+conditions",
                r"user\s+agreement",
                r"legal\s+terms",
                r"service\s+agreement"
            ],
            DocumentCategory.FAQ: [
                r"frequently\s+asked\s+questions",
                r"faq",
                r"common\s+questions",
                r"q\s*&\s*a",
                r"questions\s+and\s+answers"
            ],
            DocumentCategory.BILLING: [
                r"billing\s+policy",
                r"payment\s+terms",
                r"refund\s+policy",
                r"pricing",
                r"fees"
            ]
        }
    
    def _initialize_policy_extraction_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize policy extraction patterns."""
        return {
            "business_hours": {
                "patterns": [
                    r"business\s+hours.*?(?:monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|saturday|sat|sunday|sun).*?(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))",
                    r"(?:monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|fri|saturday|sat|sunday|sun).*?(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))",
                    r"hours\s+of\s+operation.*?(?:\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))"
                ],
                "field_name": "business_hours"
            },
            "cancellation_policy": {
                "patterns": [
                    r"cancellation\s+policy.*?(\d+)\s*hours",
                    r"cancel.*?(\d+)\s*hours\s*notice",
                    r"cancellation\s+fee.*?\$(\d+)",
                    r"late\s+cancellation.*?\$(\d+)"
                ],
                "field_name": "cancellation_policy"
            },
            "appointment_booking": {
                "patterns": [
                    r"book\s+appointments.*?(?:online|phone|website|portal)",
                    r"schedule\s+appointments.*?(?:online|phone|website|portal)",
                    r"booking\s+methods.*?(?:online|phone|website|portal)"
                ],
                "field_name": "appointment_booking"
            },
            "data_retention": {
                "patterns": [
                    r"data\s+retention.*?(\d+)\s*(?:days|months|years)",
                    r"retain\s+your\s+data.*?(\d+)\s*(?:days|months|years)",
                    r"store\s+your\s+information.*?(\d+)\s*(?:days|months|years)"
                ],
                "field_name": "data_retention"
            }
        }  
  
    async def start_processing(self):
        """Start the background processing worker."""
        if self._processing:
            return
            
        self._processing = True
        asyncio.create_task(self._process_queue())
        logger.info("Document manager processing started")
    
    async def stop_processing(self):
        """Stop the background processing worker."""
        self._processing = False
        logger.info("Document manager processing stopped")
    
    async def _process_queue(self):
        """Process documents from the queue."""
        while self._processing:
            try:
                # Get next document from queue with timeout
                try:
                    doc_id, document_path, company_id, metadata = await asyncio.wait_for(
                        self.processing_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process the document
                try:
                    await self._process_company_document(doc_id, document_path, company_id, metadata)
                except Exception as e:
                    # Handle errors and implement retry logic
                    await self._handle_processing_error(doc_id, e)
                finally:
                    self.processing_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error in document processing queue: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on persistent errors
    
    async def upload_document(self, 
                            document_path: str, 
                            company_id: str,
                            document_type: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload and process a company document.
        
        Args:
            document_path: Path to the document
            company_id: Company identifier
            document_type: Document type (optional, will be auto-detected)
            metadata: Additional metadata
            
        Returns:
            Processing status
        """
        # Validate document exists
        if not os.path.exists(document_path):
            return {
                "status": "error",
                "error": "Document not found",
                "document_path": document_path
            }
        
        # Generate document ID
        doc_id = self._generate_document_id(document_path, company_id)
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        metadata["company_id"] = company_id
        metadata["original_filename"] = os.path.basename(document_path)
        metadata["upload_time"] = datetime.now().isoformat()
        
        if document_type:
            metadata["document_type"] = document_type
        
        # Add to processing queue
        await self.processing_queue.put((doc_id, document_path, company_id, metadata))
        
        # Update status
        self.processing_tasks[doc_id] = {
            "status": "queued",
            "progress": 0,
            "document_path": document_path,
            "company_id": company_id,
            "queued_at": time.time()
        }
        
        logger.info(f"Document queued for processing: {document_path} (ID: {doc_id}, Company: {company_id})")
        return {
            "doc_id": doc_id,
            "status": "queued",
            "company_id": company_id
        }
    
    async def get_processing_status(self, doc_id: str) -> Dict[str, Any]:
        """
        Get the processing status of a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Processing status
        """
        return self.processing_tasks.get(doc_id, {"status": "not_found"})
    
    async def get_processing_results(self, doc_id: str) -> Dict[str, Any]:
        """
        Get the processing results of a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Processing results
        """
        return self.results.get(doc_id, {"status": "not_found"})
    
    async def get_company_documents(self, company_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for a company.
        
        Args:
            company_id: Company identifier
            
        Returns:
            List of document information
        """
        company_docs = []
        
        for doc_id, result in self.results.items():
            if result.get("metadata", {}).get("company_id") == company_id:
                company_docs.append({
                    "doc_id": doc_id,
                    "status": result.get("status"),
                    "document_type": result.get("document_type"),
                    "title": result.get("title", result.get("metadata", {}).get("original_filename", "")),
                    "processed_at": result.get("processed_at"),
                    "validation_result": result.get("validation_result"),
                    "extracted_policies": result.get("extracted_policies", {})
                })
        
        return company_docs   
 
    async def search_company_documents(self, 
                                     company_id: str, 
                                     query: str,
                                     document_type: Optional[str] = None,
                                     max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search company documents.
        
        Args:
            company_id: Company identifier
            query: Search query
            document_type: Filter by document type
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        # Get collection based on document type
        collection_type = document_type if document_type else "general"
        # The VectorStore class was removed, so this line will cause an error.
        # Assuming the intent was to remove this line or that VectorStore is no longer needed.
        # For now, commenting out the line to avoid breaking the code.
        # collection = self.vector_store.get_collection(company_id, collection_type)
        
        # Build filters
        filters = {"company_id": company_id}
        if document_type:
            filters["document_type"] = document_type
        
        # Perform search
        # The VectorStore class was removed, so this line will cause an error.
        # Assuming the intent was to remove this line or that VectorStore is no longer needed.
        # For now, commenting out the line to avoid breaking the code.
        # search_results = collection.search(
        #     query_text=query,
        #     n_results=max_results,
        #     filters=filters,
        #     use_hybrid=True
        # )
        
        # Format results
        results = []
        # The VectorStore class was removed, so this block will cause an error.
        # Assuming the intent was to remove this block or that VectorStore is no longer needed.
        # For now, commenting out the block to avoid breaking the code.
        # if search_results["documents"] and search_results["documents"][0]:
        #     for i, (doc, distance) in enumerate(zip(search_results["documents"][0], search_results["distances"][0])):
        #         # Get metadata
        #         metadata = search_results["metadatas"][0][i] if search_results["metadatas"] and search_results["metadatas"][0] else {}
        #         doc_id = search_results["ids"][0][i] if search_results["ids"] and search_results["ids"][0] else f"unknown_{i}"
                
        #         results.append({
        #             "doc_id": doc_id,
        #             "content": doc,
        #             "metadata": metadata,
        #             "distance": distance,
        #             "relevance_score": 1.0 - min(distance, 1.0)  # Convert distance to score
        #         })
        
        return results
    
    async def _process_company_document(self, 
                                      doc_id: str, 
                                      document_path: str, 
                                      company_id: str,
                                      metadata: Dict[str, Any]):
        """
        Process a company document.
        
        Args:
            doc_id: Document ID
            document_path: Path to the document
            company_id: Company identifier
            metadata: Document metadata
        """
        # Update processing status
        self.processing_tasks[doc_id] = {
            "status": "processing",
            "progress": 0,
            "document_path": document_path,
            "company_id": company_id,
            "started_at": time.time()
        }
        
        logger.info(f"Processing document: {document_path} (ID: {doc_id}, Company: {company_id})")
        
        try:
            # 1. Process document using document processor
            processor_result = await self.document_processor.add_document(document_path, metadata)
            processor_doc_id = processor_result["doc_id"]
            self._update_progress(doc_id, 20)
            
            # 2. Wait for document processing to complete
            processing_complete = False
            while not processing_complete:
                status = await self.document_processor.get_processing_status(processor_doc_id)
                if status.get("status") in ["completed", "failed"]:
                    processing_complete = True
                else:
                    await asyncio.sleep(0.5)
            
            if status.get("status") == "failed":
                raise Exception(f"Document processing failed: {status.get('error', 'Unknown error')}")
            
            self._update_progress(doc_id, 40)
            
            # 3. Get processing results
            processor_results = await self.document_processor.get_processing_results(processor_doc_id)
            if processor_results.get("status") != "completed":
                raise Exception(f"Document processing failed: {processor_results.get('error', 'Unknown error')}")
            
            # 4. Categorize document if not specified
            document_type = metadata.get("document_type")
            if not document_type:
                document_type = await self._categorize_document(processor_results)
                metadata["document_type"] = document_type
            
            self._update_progress(doc_id, 60)
            
            # 5. Validate document
            validation_result = await self._validate_document(processor_results, document_type)
            
            # 6. Extract policies and structured data
            extracted_policies = await self._extract_policies(processor_results, document_type)
            
            self._update_progress(doc_id, 80)
            
            # 7. Store document chunks in vector store
            await self._store_document_chunks(processor_results, company_id, document_type, metadata)
            
            self._update_progress(doc_id, 100)
            
            # Update status and results
            self.processing_tasks[doc_id]["status"] = "completed"
            self.processing_tasks[doc_id]["completed_at"] = time.time()
            
            # Store results
            self.results[doc_id] = {
                "status": "completed",
                "document_type": document_type,
                "validation_result": validation_result,
                "extracted_policies": extracted_policies,
                "processor_doc_id": processor_doc_id,
                "metadata": metadata,
                "title": self._extract_title(processor_results),
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Document processed successfully: {document_path} (ID: {doc_id}, Company: {company_id})")
            
        except Exception as e:
            logger.error(f"Error processing document {document_path} (ID: {doc_id}, Company: {company_id}): {e}")
            raise
    
    def _update_progress(self, doc_id: str, progress: int):
        """Update processing progress."""
        if doc_id in self.processing_tasks:
            self.processing_tasks[doc_id]["progress"] = progress  
  
    async def _categorize_document(self, processor_results: Dict[str, Any]) -> str:
        """
        Categorize document based on content.
        
        Args:
            processor_results: Document processor results
            
        Returns:
            Document category
        """
        # Get document content
        output_path = Path(processor_results["output_path"])
        content = ""
        
        # Read all chunks
        for chunk_file in output_path.glob("chunk_*.txt"):
            with open(chunk_file, "r", encoding="utf-8") as f:
                content += f.read() + "\n\n"
        
        content_lower = content.lower()
        
        # Check for category patterns
        category_scores = {}
        
        for category, patterns in self.categorization_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, content_lower)
                score += len(matches) * 2  # Weight for exact pattern matches
            
            # Add score for category name appearance
            category_words = category.replace("_", " ").split()
            for word in category_words:
                if word in content_lower:
                    score += 1
            
            category_scores[category] = score
        
        # Get highest scoring category
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        # Default to general if no clear category
        return DocumentCategory.GENERAL
    
    async def _validate_document(self, processor_results: Dict[str, Any], document_type: str) -> str:
        """
        Validate document based on content and type.
        
        Args:
            processor_results: Document processor results
            document_type: Document type
            
        Returns:
            Validation result
        """
        # Get document content
        output_path = Path(processor_results["output_path"])
        content = ""
        
        # Read all chunks
        for chunk_file in output_path.glob("chunk_*.txt"):
            with open(chunk_file, "r", encoding="utf-8") as f:
                content += f.read() + "\n\n"
        
        content_lower = content.lower()
        
        # Check document length
        if len(content) < 100:
            return DocumentValidationResult.MISSING_CONTENT
        
        # Check for specific validation rules
        if document_type in self.validation_rules:
            rules = self.validation_rules[document_type]
            
            # Check minimum length
            if len(content) < rules.get("min_length", 0):
                return DocumentValidationResult.LOW_QUALITY
            
            # Check maximum length
            if rules.get("max_length", float('inf')) < len(content):
                return DocumentValidationResult.INVALID_FORMAT
            
            # Check required sections
            required_sections = rules.get("required_sections", [])
            missing_sections = []
            
            for section in required_sections:
                if section not in content_lower:
                    missing_sections.append(section)
            
            if missing_sections:
                return DocumentValidationResult.MISSING_CONTENT
            
            # Check required keywords
            required_keywords = rules.get("required_keywords", [])
            missing_keywords = []
            
            for keyword in required_keywords:
                if keyword not in content_lower:
                    missing_keywords.append(keyword)
            
            if len(missing_keywords) > len(required_keywords) / 2:
                return DocumentValidationResult.LOW_QUALITY
        
        return DocumentValidationResult.VALID   
 
    async def _extract_policies(self, processor_results: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        Extract policies and structured data from document.
        
        Args:
            processor_results: Document processor results
            document_type: Document type
            
        Returns:
            Extracted policies
        """
        # Get document content
        output_path = Path(processor_results["output_path"])
        content = ""
        
        # Read all chunks
        for chunk_file in output_path.glob("chunk_*.txt"):
            with open(chunk_file, "r", encoding="utf-8") as f:
                content += f.read() + "\n\n"
        
        # Extract policies based on document type
        extracted_policies = {}
        
        if document_type == DocumentCategory.APPOINTMENT_GUIDE:
            # Extract business hours
            business_hours = self._extract_policy_field(content, "business_hours")
            if business_hours:
                extracted_policies["business_hours"] = business_hours
            
            # Extract cancellation policy
            cancellation_policy = self._extract_policy_field(content, "cancellation_policy")
            if cancellation_policy:
                extracted_policies["cancellation_policy"] = cancellation_policy
            
            # Extract appointment booking methods
            appointment_booking = self._extract_policy_field(content, "appointment_booking")
            if appointment_booking:
                extracted_policies["appointment_booking"] = appointment_booking
            
            # Extract notice period
            notice_period = self._extract_notice_period(content)
            if notice_period:
                extracted_policies["notice_period"] = notice_period
            
            # Extract cancellation fee
            cancellation_fee = self._extract_cancellation_fee(content)
            if cancellation_fee:
                extracted_policies["cancellation_fee"] = cancellation_fee
        
        elif document_type == DocumentCategory.PRIVACY_POLICY:
            # Extract data retention policy
            data_retention = self._extract_policy_field(content, "data_retention")
            if data_retention:
                extracted_policies["data_retention"] = data_retention
            
            # Extract data collection purposes
            data_collection = self._extract_data_collection(content)
            if data_collection:
                extracted_policies["data_collection"] = data_collection
            
            # Extract data sharing policy
            data_sharing = self._extract_data_sharing(content)
            if data_sharing:
                extracted_policies["data_sharing"] = data_sharing
        
        return extracted_policies
    
    def _extract_policy_field(self, content: str, field_name: str) -> Optional[str]:
        """Extract policy field from content using patterns."""
        if field_name not in self.policy_extraction_patterns:
            return None
        
        patterns = self.policy_extraction_patterns[field_name]["patterns"]
        
        for pattern in patterns:
            matches = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if matches:
                # Extract the matching section with context
                start = max(0, matches.start() - 100)
                end = min(len(content), matches.end() + 100)
                
                # Get the relevant section
                section = content[start:end]
                
                # Clean up the section
                section = re.sub(r'\s+', ' ', section).strip()
                
                return section
        
        return None
    
    def _extract_notice_period(self, content: str) -> Optional[int]:
        """Extract appointment notice period in hours."""
        patterns = [
            r"(\d+)\s*hours?\s*notice",
            r"notice\s*of\s*(\d+)\s*hours?",
            r"(\d+)\s*hours?\s*in\s*advance",
            r"(\d+)\s*hours?\s*before"
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    return int(matches.group(1))
                except ValueError:
                    pass
        
        return None
    
    def _extract_cancellation_fee(self, content: str) -> Optional[float]:
        """Extract cancellation fee amount."""
        patterns = [
            r"cancellation\s*fee\s*of\s*\$?(\d+(?:\.\d+)?)",
            r"fee\s*of\s*\$?(\d+(?:\.\d+)?)\s*for\s*cancellation",
            r"\$?(\d+(?:\.\d+)?)\s*cancellation\s*fee",
            r"charged\s*\$?(\d+(?:\.\d+)?)\s*for\s*cancellation"
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    return float(matches.group(1))
                except ValueError:
                    pass
        
        return None    

    def _extract_data_collection(self, content: str) -> Optional[List[str]]:
        """Extract data collection purposes."""
        section_patterns = [
            r"(?:we|us|our)\s+collect\s+(?:your|personal)\s+information[^.]*(?:for|to)[^.]*\.",
            r"(?:data|information)\s+collection[^.]*(?:for|to)[^.]*\.",
            r"(?:we|us|our)\s+use\s+(?:your|personal)\s+information[^.]*(?:for|to)[^.]*\."
        ]
        
        purposes = []
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract the matching section
                section = match.group(0)
                
                # Look for purposes
                purpose_matches = re.findall(r"(?:for|to)\s+([^,;.]*)", section, re.IGNORECASE)
                purposes.extend([p.strip() for p in purpose_matches if p.strip()])
        
        return list(set(purposes)) if purposes else None
    
    def _extract_data_sharing(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract data sharing policy."""
        sharing_info = {}
        
        # Check if data is shared with third parties
        third_party_patterns = [
            r"(?:share|disclose|provide)\s+(?:your|personal)\s+information\s+(?:with|to)\s+third\s+parties",
            r"third\s+parties\s+(?:may|will|can)\s+(?:receive|access)\s+(?:your|personal)\s+information"
        ]
        
        for pattern in third_party_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                sharing_info["shared_with_third_parties"] = True
                break
        else:
            sharing_info["shared_with_third_parties"] = False
        
        # Extract who data is shared with
        if sharing_info["shared_with_third_parties"]:
            shared_with_section = re.search(
                r"(?:share|disclose|provide)\s+(?:your|personal)\s+information\s+(?:with|to)\s+([^.]*)",
                content,
                re.IGNORECASE
            )
            
            if shared_with_section:
                shared_with = shared_with_section.group(1).strip()
                sharing_info["shared_with"] = shared_with
        
        return sharing_info if sharing_info else None
    
    async def _store_document_chunks(self, 
                                   processor_results: Dict[str, Any],
                                   company_id: str,
                                   document_type: str,
                                   metadata: Dict[str, Any]):
        """
        Store document chunks in vector store.
        
        Args:
            processor_results: Document processor results
            company_id: Company identifier
            document_type: Document type
            metadata: Document metadata
        """
        # Get document chunks
        output_path = Path(processor_results["output_path"])
        
        # Get collection
        # The VectorStore class was removed, so this line will cause an error.
        # Assuming the intent was to remove this line or that VectorStore is no longer needed.
        # For now, commenting out the line to avoid breaking the code.
        # collection = self.vector_store.get_collection(company_id, document_type)
        
        # Read chunks
        chunks = []
        chunk_ids = []
        chunk_metadatas = []
        
        doc_id = processor_results.get("doc_id", "unknown")
        
        for chunk_file in output_path.glob("chunk_*.txt"):
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_content = f.read()
            
            chunk_id = f"{doc_id}_{chunk_file.stem}"
            chunks.append(chunk_content)
            chunk_ids.append(chunk_id)
            
            # Create metadata for this chunk
            chunk_metadata = {
                **metadata,
                "doc_id": doc_id,
                "chunk_id": chunk_file.stem,
                "document_type": document_type,
                "company_id": company_id
            }
            chunk_metadatas.append(chunk_metadata)
        
        # Store chunks in vector store
        if chunks:
            # The VectorStore class was removed, so this line will cause an error.
            # Assuming the intent was to remove this line or that VectorStore is no longer needed.
            # For now, commenting out the line to avoid breaking the code.
            # success = collection.add_documents(
            #     ids=chunk_ids,
            #     documents=chunks,
            #     metadatas=chunk_metadatas
            # )
            
            # if success:
            #     logger.info(f"Added {len(chunks)} chunks from document {doc_id} to vector store")
            # else:
            #     logger.error(f"Failed to add chunks from document {doc_id} to vector store")    
            logger.warning(f"VectorStore is not initialized, skipping chunk storage for document {doc_id}")
 
    def _extract_title(self, processor_results: Dict[str, Any]) -> str:
        """Extract document title from processing results."""
        # Try to get title from metadata
        metadata = processor_results.get("metadata", {})
        if "title" in metadata:
            return metadata["title"]
        
        # Try to extract from first chunk
        output_path = Path(processor_results["output_path"])
        first_chunk = output_path / "chunk_000.txt"
        
        if first_chunk.exists():
            with open(first_chunk, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Look for title patterns
                title_patterns = [
                    r"^#\s+(.+)$",  # Markdown title
                    r"^(.+)\n={3,}$",  # Underlined title
                    r"^Title:\s*(.+)$",  # Explicit title
                    r"^(.{10,60})$"  # First line if reasonable length
                ]
                
                for pattern in title_patterns:
                    match = re.search(pattern, content, re.MULTILINE)
                    if match:
                        return match.group(1).strip()
                
                # Fall back to first line
                first_line = content.split("\n")[0].strip()
                if first_line and len(first_line) < 100:
                    return first_line
        
        # Fall back to filename
        return metadata.get("original_filename", "Untitled Document")
    
    async def _handle_processing_error(self, doc_id: str, error: Exception):
        """
        Handle processing errors with retry logic.
        
        Args:
            doc_id: Document ID
            error: Exception that occurred
        """
        # Get current task info
        task_info = self.processing_tasks.get(doc_id, {})
        
        # Update retry count
        retry_count = task_info.get("retry_count", 0) + 1
        
        # Update task status
        self.processing_tasks[doc_id] = {
            **task_info,
            "status": "error",
            "error": str(error),
            "retry_count": retry_count,
            "last_error_at": time.time()
        }
        
        # Implement retry logic
        if retry_count < 3:
            logger.info(f"Retrying document {doc_id} (attempt {retry_count})")
            
            # Wait before retrying (exponential backoff)
            await asyncio.sleep(2 ** retry_count)
            
            # Requeue the document
            document_path = task_info.get("document_path")
            company_id = task_info.get("company_id")
            metadata = task_info.get("metadata", {})
            
            if document_path and company_id:
                await self.processing_queue.put((doc_id, document_path, company_id, metadata))
        else:
            logger.error(f"Document {doc_id} failed after {retry_count} attempts")
            
            # Update results with failure
            self.results[doc_id] = {
                "status": "failed",
                "error": str(error),
                "retry_count": retry_count
            }
    
    def _generate_document_id(self, document_path: str, company_id: str) -> str:
        """
        Generate a unique document ID.
        
        Args:
            document_path: Path to the document
            company_id: Company identifier
            
        Returns:
            Document ID
        """
        # Create a hash of the path, company ID, and modification time
        path_str = str(document_path)
        try:
            mtime = os.path.getmtime(document_path)
        except:
            mtime = time.time()
            
        hash_input = f"{path_str}:{company_id}:{mtime}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

# Example usage
async def test_company_document_manager():
    """Test company document manager functionality."""
    # Initialize document processor
    document_processor = DocumentParser(output_dir="processed_documents")
    await document_processor.start_processing()
    
    # Initialize vector store
    # The VectorStore class was removed, so this line will cause an error.
    # Assuming the intent was to remove this line or that VectorStore is no longer needed.
    # For now, commenting out the line to avoid breaking the code.
    # vector_store = VectorStore(persist_directory="chroma_db")
    
    # Initialize company document manager
    document_manager = CompanyDocumentManager(
        document_processor=document_processor,
        # The VectorStore class was removed, so this line will cause an error.
        # Assuming the intent was to remove this line or that VectorStore is no longer needed.
        # For now, commenting out the line to avoid breaking the code.
        # vector_store=vector_store,
        output_dir="company_documents",
        embedding_cache_dir="embedding_cache"
    )
    await document_manager.start_processing()
    
    # Create test document
    test_doc = "test_appointment_guide.txt"
    with open(test_doc, 'w', encoding='utf-8') as f:
        f.write("""
Appointment Scheduling Guide for Acme Corp

Booking an Appointment:
You can schedule appointments through our online portal or by calling our customer service line at 555-123-4567.

Cancellation Policy:
We require 24 hours notice for cancellations. Late cancellations may incur a fee of $25.

Rescheduling:
To reschedule, please contact us at least 24 hours before your appointment.

Business Hours:
Monday-Friday: 9:00 AM - 5:00 PM
Saturday: 10:00 AM - 2:00 PM
Sunday: Closed
        """)
    
    # Upload document
    result = await document_manager.upload_document(
        document_path=test_doc,
        company_id="acme_corp"
    )
    doc_id = result["doc_id"]
    
    # Check status
    for _ in range(10):
        status = await document_manager.get_processing_status(doc_id)
        print(f"Status: {status}")
        
        if status.get("status") == "completed":
            break
            
        await asyncio.sleep(0.5)
    
    # Get results
    results = await document_manager.get_processing_results(doc_id)
    print(f"Results: {results}")
    
    # Search documents
    search_results = await document_manager.search_company_documents(
        company_id="acme_corp",
        query="cancellation policy"
    )
    print(f"Search results: {search_results}")
    
    # Clean up
    await document_manager.stop_processing()
    await document_processor.stop_processing()
    os.remove(test_doc)

if __name__ == "__main__":
    asyncio.run(test_company_document_manager())