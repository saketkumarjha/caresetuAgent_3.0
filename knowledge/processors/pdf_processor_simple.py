"""
Simple PDF Document Processor
Extracts text from PDF files without vector DB dependencies
"""

import os
import asyncio
import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
import re
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PDF libraries with fallbacks
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available. Install with: pip install PyPDF2")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available. Install with: pip install pdfplumber")

class DocumentType:
    """Document types for PDF documents."""
    FAQ = "faq"
    POLICY = "policy"
    PROCEDURE = "procedure"
    MANUAL = "manual"
    GENERAL = "general"

class PDFProcessor:
    """
    PDF processor that extracts text without vector DB dependencies.
    Implements document type detection based on content and filename.
    """
    
    def __init__(self, pdf_directory="company_pdfs", output_directory="company_documents"):
        """Initialize the PDF processor."""
        self.pdf_directory = Path(pdf_directory)
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True, parents=True)
        
        # Document type detection patterns
        self.document_type_patterns = {
            DocumentType.FAQ: [
                r"frequently\s+asked\s+questions",
                r"faq",
                r"common\s+questions",
                r"q\s*&\s*a",
                r"questions\s+and\s+answers"
            ],
            DocumentType.POLICY: [
                r"policy",
                r"policies",
                r"terms\s+of\s+service",
                r"terms\s+and\s+conditions",
                r"privacy",
                r"data\s+protection",
                r"compliance"
            ],
            DocumentType.PROCEDURE: [
                r"procedure",
                r"process",
                r"step\s+by\s+step",
                r"instructions",
                r"how\s+to",
                r"workflow"
            ],
            DocumentType.MANUAL: [
                r"manual",
                r"guide",
                r"handbook",
                r"documentation",
                r"reference"
            ]
        }
        
        # Check if PDF libraries are available
        if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            logger.warning("No PDF processing libraries available. Install PyPDF2 or pdfplumber.")
        
        logger.info(f"PDF Processor initialized with directory: {pdf_directory}")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        text = ""
        pdf_path = Path(pdf_path)
        
        if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            raise ImportError("No PDF processing libraries available. Install PyPDF2 or pdfplumber.")
        
        try:
            # Try PyPDF2 first if available
            if PDF_AVAILABLE:
                with open(pdf_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    for page_num, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- Page {page_num + 1} ---\n"
                                text += page_text + "\n\n"
                        except Exception as e:
                            logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
            
            # If text is empty or very short, try pdfplumber as fallback
            if (len(text) < 100) and PDFPLUMBER_AVAILABLE:
                import pdfplumber
                text = ""  # Reset text
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += f"\n--- Page {page_num + 1} ---\n"
                                text += page_text + "\n\n"
                        except Exception as e:
                            logger.warning(f"Error extracting text from page {page_num + 1} with pdfplumber: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise
        
        return text
    
    def detect_document_type(self, content, filename):
        """Detect document type based on content and filename."""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        # Check filename first (highest priority)
        for doc_type, patterns in self.document_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    logger.info(f"Document type detected from filename: {doc_type}")
                    return doc_type
        
        # Check content patterns
        type_scores = {}
        for doc_type, patterns in self.document_type_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, content_lower)
                score += len(matches) * 2
            type_scores[doc_type] = score
        
        # Get highest scoring type
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1])
            if best_type[1] > 0:
                logger.info(f"Document type detected from content: {best_type[0]} (score: {best_type[1]})")
                return best_type[0]
        
        # Default to general if no clear type
        logger.info("No specific document type detected, using general type")
        return DocumentType.GENERAL
    
    async def process_pdf(self, pdf_path):
        """Process a single PDF file."""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Extract text from PDF
            content = self.extract_text_from_pdf(pdf_path)
            
            if not content.strip():
                logger.error(f"No text content extracted from PDF: {pdf_path}")
                return None
            
            # Detect document type
            document_type = self.detect_document_type(content, pdf_path.name)
            
            # Create result
            result = {
                "filename": pdf_path.name,
                "content": content,
                "document_type": document_type,
                "file_size": os.path.getsize(pdf_path),
                "processed_at": datetime.now().isoformat()
            }
            
            # Save result
            self._save_processed_document(result)
            
            logger.info(f"Successfully processed PDF: {pdf_path} as {document_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None
    
    def _save_processed_document(self, document):
        """Save processed document to output directory."""
        # Generate ID
        doc_id = hashlib.md5(document["filename"].encode()).hexdigest()[:8]
        
        # Create company ID based subdirectory
        company_id = "caresetu"  # Default company ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save content file
        content_file = self.output_directory / f"{company_id}_{timestamp}_{doc_id}_content.txt"
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(document["content"])
        
        # Save metadata file
        metadata_file = self.output_directory / f"{company_id}_{timestamp}_{doc_id}_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(document, f, indent=2)
        
        logger.info(f"Saved processed document to {content_file}")
    
    async def process_all_pdfs(self):
        """Process all PDF files in the directory."""
        results = []
        
        # Check if directory exists
        if not self.pdf_directory.exists():
            logger.error(f"PDF directory not found: {self.pdf_directory}")
            return results
        
        # Process each PDF file
        for pdf_file in self.pdf_directory.glob("*.pdf"):
            try:
                processed_doc = await self.process_pdf(str(pdf_file))
                if processed_doc:
                    results.append(processed_doc)
            except Exception as e:
                logger.error(f"Error processing PDF {pdf_file}: {e}")
        
        logger.info(f"Processed {len(results)} PDF files")
        return results

# Example usage
async def test_pdf_processor():
    """Test the PDF processor."""
    processor = PDFProcessor()
    
    # Process all PDFs in the directory
    documents = await processor.process_all_pdfs()
    
    print(f"Processed {len(documents)} documents:")
    for doc in documents:
        print(f"- {doc['filename']}: {doc['document_type']}")

if __name__ == "__main__":
    asyncio.run(test_pdf_processor())