"""Enhanced Document Processor with ChromaDB Integration."""

import asyncio
import logging
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# PDF processing
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# NLP for intelligent chunking
try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from ..storage.knowledge_indexer import CompanyConfig, DocumentChunk

logger = logging.getLogger(__name__)

@dataclass
class ProcessingConfig:
    """Configuration for document processing."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    use_semantic_chunking: bool = True
    extract_policies: bool = True

@dataclass
class ExtractedPolicy:
    """Extracted policy information from documents."""
    policy_type: str
    policy_text: str
    structured_data: Dict[str, Any]
    confidence: float
    source_location: str

class IntelligentChunker:
    """Intelligent document chunking with semantic awareness."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self._init_nltk()
    
    def _init_nltk(self):
        """Initialize NLTK resources."""
        if NLTK_AVAILABLE:
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
            except Exception as e:
                logger.warning(f"NLTK initialization warning: {e}")
    
    def chunk_document(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """
        Intelligently chunk document text.
        
        Args:
            text: Full document text
            document_id: Document identifier
            
        Returns:
            List of text chunks with metadata
        """
        if self.config.use_semantic_chunking and NLTK_AVAILABLE:
            return self._semantic_chunking(text, document_id)
        else:
            return self._simple_chunking(text, document_id)
    
    def _semantic_chunking(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Semantic-aware chunking using sentence boundaries."""
        try:
            sentences = sent_tokenize(text)
            chunks = []
            current_chunk = ""
            current_sentences = []
            chunk_id = 1
            
            for sentence in sentences:
                # Check if adding this sentence would exceed chunk size
                potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
                
                if len(potential_chunk) <= self.config.chunk_size:
                    current_chunk = potential_chunk
                    current_sentences.append(sentence)
                else:
                    # Save current chunk if it meets minimum size
                    if len(current_chunk) >= self.config.min_chunk_size:
                        chunks.append({
                            "chunk_id": f"{document_id}_chunk_{chunk_id}",
                            "text": current_chunk.strip(),
                            "sentences": current_sentences,
                            "word_count": len(current_chunk.split()),
                            "char_count": len(current_chunk)
                        })
                        chunk_id += 1
                    
                    # Start new chunk with overlap
                    if self.config.chunk_overlap > 0 and current_sentences:
                        overlap_sentences = current_sentences[-2:] if len(current_sentences) > 1 else current_sentences
                        current_chunk = " ".join(overlap_sentences) + " " + sentence
                        current_sentences = overlap_sentences + [sentence]
                    else:
                        current_chunk = sentence
                        current_sentences = [sentence]
            
            # Add final chunk
            if current_chunk and len(current_chunk) >= self.config.min_chunk_size:
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{chunk_id}",
                    "text": current_chunk.strip(),
                    "sentences": current_sentences,
                    "word_count": len(current_chunk.split()),
                    "char_count": len(current_chunk)
                })
            
            logger.info(f"📝 Semantic chunking created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Semantic chunking failed: {e}")
            return self._simple_chunking(text, document_id)
    
    def _simple_chunking(self, text: str, document_id: str) -> List[Dict[str, Any]]:
        """Simple character-based chunking with sentence boundary awareness."""
        chunks = []
        start = 0
        chunk_id = 1
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                sentence_end = text.rfind('.', end - 200, end)
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text and len(chunk_text) >= self.config.min_chunk_size:
                chunks.append({
                    "chunk_id": f"{document_id}_chunk_{chunk_id}",
                    "text": chunk_text,
                    "word_count": len(chunk_text.split()),
                    "char_count": len(chunk_text)
                })
                chunk_id += 1
            
            # Move start position with overlap
            start = max(start + 1, end - self.config.chunk_overlap)
        
        logger.info(f"📝 Simple chunking created {len(chunks)} chunks")
        return chunks

class PolicyExtractor:
    """Extracts structured policy information from documents."""
    
    def __init__(self):
        self.policy_patterns = {
            "cancellation": {
                "patterns": [
                    r"(?i)(?:cancellation|cancel).*?(?:policy|notice|hours?|days?)",
                    r"(?i)(?:\d+)\s*(?:hours?|days?)\s*(?:notice|advance|prior)",
                    r"(?i)(?:no.?show|no show).*?(?:fee|charge|policy)"
                ],
                "extractors": [
                    r"(?i)(?:\d+)\s*(?:hours?|days?)",
                    r"(?i)\$?\d+(?:\.\d{2})?\s*(?:fee|charge)"
                ]
            },
            "appointment": {
                "patterns": [
                    r"(?i)(?:appointment|booking).*?(?:policy|hours?|schedule)",
                    r"(?i)(?:business|office)\s*hours?",
                    r"(?i)(?:same.?day|emergency).*?(?:appointment|available)"
                ],
                "extractors": [
                    r"(?i)(?:\d{1,2}:\d{2}|\d{1,2}\s*(?:AM|PM))",
                    r"(?i)(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
                ]
            },
            "privacy": {
                "patterns": [
                    r"(?i)(?:privacy|personal|data).*?(?:policy|information|collection)",
                    r"(?i)(?:collect|process|store).*?(?:information|data)",
                    r"(?i)(?:gdpr|ccpa|privacy\s*law)"
                ],
                "extractors": [
                    r"(?i)(?:personal|sensitive)\s*(?:information|data)",
                    r"(?i)(?:encrypt|secure|protect)"
                ]
            },
            "payment": {
                "patterns": [
                    r"(?i)(?:payment|billing).*?(?:policy|terms|due)",
                    r"(?i)(?:accept|payment\s*methods)",
                    r"(?i)(?:invoice|bill).*?(?:due|payment)"
                ],
                "extractors": [
                    r"(?i)(?:cash|check|credit\s*card|visa|mastercard)",
                    r"(?i)\$?\d+(?:\.\d{2})?"
                ]
            }
        }
    
    def extract_policies(self, text: str, document_title: str) -> List[ExtractedPolicy]:
        """
        Extract policy information from document text.
        
        Args:
            text: Document text
            document_title: Document title
            
        Returns:
            List of extracted policies
        """
        policies = []
        
        for policy_type, config in self.policy_patterns.items():
            policy_sections = self._find_policy_sections(text, config["patterns"])
            
            for section in policy_sections:
                structured_data = self._extract_structured_data(section, config["extractors"])
                
                if structured_data:  # Only add if we found structured data
                    policy = ExtractedPolicy(
                        policy_type=policy_type,
                        policy_text=section,
                        structured_data=structured_data,
                        confidence=self._calculate_confidence(section, structured_data),
                        source_location=document_title
                    )
                    policies.append(policy)
        
        logger.info(f"📋 Extracted {len(policies)} policies from {document_title}")
        return policies
    
    def _find_policy_sections(self, text: str, patterns: List[str]) -> List[str]:
        """Find text sections that match policy patterns."""
        sections = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Extract surrounding context (±200 characters)
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                section = text[start:end].strip()
                
                if len(section) > 50:  # Minimum section length
                    sections.append(section)
        
        return sections
    
    def _extract_structured_data(self, text: str, extractors: List[str]) -> Dict[str, Any]:
        """Extract structured data using regex patterns."""
        data = {}
        
        for extractor in extractors:
            matches = re.findall(extractor, text, re.IGNORECASE)
            if matches:
                # Categorize matches
                if re.search(r'\d+\s*(?:hours?|days?)', extractor, re.IGNORECASE):
                    data["time_requirements"] = matches
                elif re.search(r'\$|\d+\.\d{2}', extractor):
                    data["fees"] = matches
                elif re.search(r'(?:AM|PM|\d{1,2}:\d{2})', extractor, re.IGNORECASE):
                    data["times"] = matches
                elif re.search(r'(?:monday|tuesday)', extractor, re.IGNORECASE):
                    data["days"] = matches
                else:
                    data["other"] = matches
        
        return data
    
    def _calculate_confidence(self, text: str, structured_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted policy."""
        base_confidence = 0.5
        
        # Boost confidence based on structured data found
        if structured_data:
            base_confidence += 0.2 * len(structured_data)
        
        # Boost for specific keywords
        confidence_keywords = ["policy", "require", "must", "shall", "fee", "charge"]
        keyword_count = sum(1 for keyword in confidence_keywords if keyword.lower() in text.lower())
        base_confidence += 0.05 * keyword_count
        
        return min(1.0, base_confidence)

class EnhancedDocumentProcessor:
    """Enhanced document processor with ChromaDB integration."""
    
    def __init__(self, processing_config: ProcessingConfig = None):
        """
        Initialize enhanced document processor.
        
        Args:
            processing_config: Processing configuration
        """
        self.config = processing_config or ProcessingConfig()
        self.chunker = IntelligentChunker(self.config)
        self.policy_extractor = PolicyExtractor()
        
        if not PDF_AVAILABLE:
            logger.warning("PDF processing not available. Install with: pip install PyPDF2 pdfplumber")
    
    async def process_company_pdf(self, company_id: str, pdf_path: Path, 
                                document_type: str = "policy") -> Dict[str, Any]:
        """
        Process PDF document for a company.
        
        Args:
            company_id: Company identifier
            pdf_path: Path to PDF file
            document_type: Type of document
            
        Returns:
            Processing results with statistics
        """
        if not PDF_AVAILABLE:
            raise RuntimeError("PDF processing not available")
        
        logger.info(f"🏢 Processing PDF for company {company_id}: {pdf_path.name}")
        
        # Extract text from PDF
        pdf_data = await self._extract_pdf_text(pdf_path)
        
        # Generate document ID
        document_id = f"{company_id}_{hashlib.md5(pdf_path.name.encode()).hexdigest()[:12]}"
        
        # Intelligent chunking
        chunks_data = self.chunker.chunk_document(pdf_data["full_text"], document_id)
        
        # Extract policies if enabled
        policies = []
        if self.config.extract_policies:
            policies = self.policy_extractor.extract_policies(
                pdf_data["full_text"], 
                pdf_path.stem
            )
        
        # Create DocumentChunk objects
        document_chunks = []
        base_title = pdf_path.stem.replace('_', ' ').replace('-', ' ').title()
        
        for i, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                chunk_id=chunk_data["chunk_id"],
                company_id=company_id,
                document_id=document_id,
                title=f"{base_title} - Part {i+1}" if len(chunks_data) > 1 else base_title,
                content=chunk_data["text"],
                chunk_index=i + 1,
                total_chunks=len(chunks_data),
                category=document_type,
                tags=[document_type, company_id, "pdf", pdf_path.stem],
                metadata={
                    "source_file": pdf_path.name,
                    "word_count": chunk_data.get("word_count", 0),
                    "char_count": chunk_data.get("char_count", 0),
                    "page_count": pdf_data["page_count"],
                    "file_size": pdf_data["file_size"]
                },
                created_at=datetime.now()
            )
            document_chunks.append(chunk)
        
        # Add chunks to vector store
        
        # Prepare results
        results = {
            "success": True,
            "document_id": document_id,
            "chunks_created": len(document_chunks),
            "policies_extracted": len(policies),
            "file_info": {
                "filename": pdf_path.name,
                "size_bytes": pdf_data["file_size"],
                "page_count": pdf_data["page_count"]
            },
            "processing_stats": {
                "total_text_length": len(pdf_data["full_text"]),
                "average_chunk_size": sum(len(chunk.content) for chunk in document_chunks) // len(document_chunks) if document_chunks else 0,
                "processing_time": datetime.now().isoformat()
            },
            "extracted_policies": [asdict(policy) for policy in policies]
        }
        
        logger.info(f"✅ Processed {pdf_path.name}: {len(document_chunks)} chunks, {len(policies)} policies")
        return results
    
    async def _extract_pdf_text(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text from PDF with metadata."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = []
                full_text = ""
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text() or ""
                    pages.append({
                        "page_number": page_num,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                    full_text += f"\n\n--- Page {page_num} ---\n{page_text}"
                
                return {
                    "full_text": full_text.strip(),
                    "pages": pages,
                    "page_count": len(pages),
                    "file_size": pdf_path.stat().st_size,
                    "processed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error extracting PDF text: {e}")
            raise
    
    async def process_text_document(self, company_id: str, text: str, 
                                  title: str, document_type: str = "policy") -> Dict[str, Any]:
        """
        Process plain text document.
        
        Args:
            company_id: Company identifier
            text: Document text
            title: Document title
            document_type: Type of document
            
        Returns:
            Processing results
        """
        document_id = f"{company_id}_{hashlib.md5(title.encode()).hexdigest()[:12]}"
        
        # Chunk the text
        chunks_data = self.chunker.chunk_document(text, document_id)
        
        # Extract policies
        policies = []
        if self.config.extract_policies:
            policies = self.policy_extractor.extract_policies(text, title)
        
        # Create DocumentChunk objects
        document_chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk = DocumentChunk(
                chunk_id=chunk_data["chunk_id"],
                company_id=company_id,
                document_id=document_id,
                title=f"{title} - Part {i+1}" if len(chunks_data) > 1 else title,
                content=chunk_data["text"],
                chunk_index=i + 1,
                total_chunks=len(chunks_data),
                category=document_type,
                tags=[document_type, company_id, "text"],
                metadata={
                    "word_count": chunk_data.get("word_count", 0),
                    "char_count": chunk_data.get("char_count", 0)
                },
                created_at=datetime.now()
            )
            document_chunks.append(chunk)
        
        # Add to vector store
        
        return {
            "success": True,
            "document_id": document_id,
            "chunks_created": len(document_chunks),
            "policies_extracted": len(policies),
            "extracted_policies": [asdict(policy) for policy in policies]
        }

# Test the enhanced processor
async def test_enhanced_processor():
    """Test enhanced document processor."""
    print("🧪 Testing Enhanced Document Processor")
    print("=" * 50)
    
    # Initialize vector store
    
    # Register company
    
    # Initialize processor
    processor = EnhancedDocumentProcessor()
    
    # Test with sample text
    sample_policy = """
    Privacy Policy
    
    We collect personal information when you use our services. This includes your name, 
    email address, and phone number. We require 24 hours notice for appointment 
    cancellations. No-show appointments will be charged a $50 fee.
    
    Our business hours are Monday through Friday, 9:00 AM to 5:00 PM. Same-day 
    appointments may be available for emergency situations.
    
    We accept cash, check, and all major credit cards. Payment is due at time of service.
    """
    
    # Process text document
    results = await processor.process_text_document(
        "enhanced_test", 
        sample_policy, 
        "Company Privacy Policy",
        "policy"
    )
    
    print(f"✅ Processing Results:")
    print(f"   • Success: {results['success']}")
    print(f"   • Chunks created: {results['chunks_created']}")
    print(f"   • Policies extracted: {results['policies_extracted']}")
    
    # Test search
    
    # print(f"\n🔍 Search Results:")
    # for result in search_results:
    #     print(f"   • {result.chunk.title} (Score: {result.similarity_score:.3f})")
    #     print(f"     {result.chunk.content[:100]}...")
    
    # Show extracted policies
    if results['extracted_policies']:
        print(f"\n📋 Extracted Policies:")
        for policy in results['extracted_policies']:
            print(f"   • {policy['policy_type']}: {policy['confidence']:.2f} confidence")
            if policy['structured_data']:
                print(f"     Data: {policy['structured_data']}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_processor())