"""
PDF Processor for extracting and processing PDF documents
"""

import os
import re
import hashlib
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Try to import PDF libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from .document_parsers import DocumentSection, DocumentParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Document types
class DocumentType:
    """Document type constants."""
    FAQ = "faq"
    POLICY = "policy"
    PROCEDURE = "procedure"
    MANUAL = "manual"
    GENERAL = "general"

@dataclass
class ProcessedDocument:
    """Represents a processed PDF document."""
    id: str
    filename: str
    title: str
    content: str
    document_type: str  # faq, policy, procedure, manual, general
    sections: List[DocumentSection]
    metadata: Dict[str, Any]
    processed_at: datetime
    source_path: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "content": self.content,
            "document_type": self.document_type,
            "sections": [section.to_dict() for section in self.sections],
            "metadata": self.metadata,
            "processed_at": self.processed_at.isoformat(),
            "source_path": self.source_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedDocument':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            filename=data["filename"],
            title=data["title"],
            content=data["content"],
            document_type=data["document_type"],
            sections=[DocumentSection.from_dict(s) for s in data["sections"]],
            metadata=data["metadata"],
            processed_at=datetime.fromisoformat(data["processed_at"]),
            source_path=data["source_path"]
        )

class PDFProcessor:
    """Processor for PDF documents."""
    
    def __init__(self, pdf_directory: str = "pdf_documents", output_directory: str = "processed_documents"):
        """
        Initialize the PDF processor.
        
        Args:
            pdf_directory: Directory containing PDF files
            output_directory: Directory to store processed documents
        """
        self.pdf_directory = pdf_directory
        self.output_directory = output_directory
        self.parser = DocumentParser()
        
        # Create output directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        # Content patterns for document type detection
        self.content_patterns = {
            DocumentType.FAQ: [
                (r"Q\s*:\s*(.*?)\s*\n\s*A\s*:\s*(.*?)(?=\n\s*Q\s*:|$)", 2),  # Q: ... A: format
                (r"Question\s*:\s*(.*?)\s*\n\s*Answer\s*:\s*(.*?)(?=\n\s*Question\s*:|$)", 3),  # Question: ... Answer: format
                (r"(?:^|\n)(?:(?!\n\s*\?\s*\n|$)(?:\n|.)*\?\s*\n)(?:(?!\n\s*\?\s*\n|$)(?:\n|.)*)", 1),  # Question ending with ? followed by answer
            ],
            DocumentType.POLICY: [
                (r"policy", 2),
                (r"terms", 2),
                (r"agreement", 2),
                (r"privacy", 3),
                (r"compliance", 2),
                (r"legal", 2),
                (r"rights", 1),
                (r"responsibilities", 1),
            ],
            DocumentType.PROCEDURE: [
                (r"step\s+\d+", 3),  # Step 1, Step 2, etc.
                (r"\d+\.\s+", 2),  # 1. 2. etc.
                (r"first.*then.*finally?", 3),
                (r"process", 1),
                (r"procedure", 2),
                (r"instructions", 2),
                (r"follow", 1),
            ],
            DocumentType.MANUAL: [
                (r"chapter", 3),
                (r"section", 2),
                (r"guide", 2),
                (r"manual", 3),
                (r"reference", 2),
                (r"appendix", 3),
                (r"figure", 1),
                (r"table", 1),
            ],
        }
        
        # Filename patterns for document type detection
        self.document_type_patterns = {
            DocumentType.FAQ: [
                r"faq",
                r"questions",
                r"q&a",
                r"frequently",
            ],
            DocumentType.POLICY: [
                r"policy",
                r"terms",
                r"agreement",
                r"privacy",
                r"legal",
                r"compliance",
            ],
            DocumentType.PROCEDURE: [
                r"procedure",
                r"process",
                r"how.?to",
                r"steps",
                r"guide",
                r"instructions",
            ],
            DocumentType.MANUAL: [
                r"manual",
                r"handbook",
                r"guide",
                r"reference",
                r"documentation",
            ],
        }
        
        logger.info(f"✅ PDF Processor initialized with directory: {pdf_directory}")
    
    async def process_all_pdfs(self) -> List[ProcessedDocument]:
        """
        Process all PDF files in the directory.
        
        Returns:
            List of processed documents
        """
        results = []
        
        # Check if directory exists
        if not self.pdf_directory.exists():
            logger.error(f"PDF directory not found: {self.pdf_directory}")
            return results
        
        # Process each PDF file
        for pdf_file in self.pdf_directory.glob("*.pdf"):
            try:
                processed_doc = await self.process_single_pdf(str(pdf_file))
                if processed_doc:
                    results.append(processed_doc)
            except Exception as e:
                logger.error(f"Error processing PDF {pdf_file}: {e}")
        
        logger.info(f"Processed {len(results)} PDF files")
        return results
    
    async def process_single_pdf(self, pdf_path: str) -> Optional[ProcessedDocument]:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Processed document or None if processing failed
        """
        # Check if file exists
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return None
            
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Generate document ID
            doc_id = self._generate_document_id(pdf_path)
            
            # Extract text from PDF
            content = self._extract_text_from_pdf(pdf_path)
            
            if not content.strip():
                logger.error(f"No text extracted from PDF: {pdf_path}")
                return None
                
            # Detect document type
            document_type = self._detect_document_type(content, pdf_path.name)
            
            # Extract title
            title = self._extract_title(content, pdf_path.name)
            
            # Parse document based on type
            sections = self._parse_document(content, document_type)
            
            # Create metadata
            metadata = {
                "original_filename": pdf_path.name,
                "file_size": os.path.getsize(pdf_path),
                "processed_at": datetime.now().isoformat(),
                "document_type": document_type,
                "detection_confidence": self._calculate_type_confidence(content, document_type),
            }
            
            # Create processed document
            processed_doc = ProcessedDocument(
                id=doc_id,
                filename=pdf_path.name,
                title=title,
                content=content,
                document_type=document_type,
                sections=sections,
                metadata=metadata,
                processed_at=datetime.now(),
                source_path=str(pdf_path),
            )
            
            # Save processed document
            self._save_processed_document(processed_doc)
            
            logger.info(f"Successfully processed PDF: {pdf_path} as {document_type}")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return None
    
    def _generate_document_id(self, pdf_path: Path) -> str:
        """
        Generate a unique document ID based on file path and modification time.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Unique document ID
        """
        # Create a hash of the file path and modification time
        file_info = f"{pdf_path}_{os.path.getmtime(pdf_path)}"
        return hashlib.md5(file_info.encode()).hexdigest()
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        
        # Check if PDF libraries are available
        if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            raise ImportError("No PDF processing libraries available. Install PyPDF2 or pdfplumber.")
        
        # Try PyPDF2 first if available
        if PDF_AVAILABLE:
            try:
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
            except Exception as e:
                logger.warning(f"Error with PyPDF2: {e}")
        
        # If text is empty or very short, try pdfplumber as fallback
        if (len(text) < 100) and PDFPLUMBER_AVAILABLE:
            try:
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
        
        return text
    
    def _detect_document_type(self, content: str, filename: str) -> str:
        """
        Detect document type based on content and filename.
        
        Args:
            content: Document content
            filename: Filename
            
        Returns:
            Document type
        """
        # Check filename first (highest priority)
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        for doc_type, patterns in self.document_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    logger.info(f"Document type detected from filename: {doc_type}")
                    return doc_type
        
        # Then check content patterns (more specific)
        type_scores = {}
        for doc_type in [DocumentType.FAQ, DocumentType.POLICY, DocumentType.PROCEDURE, DocumentType.MANUAL]:
            score = 0
            if doc_type in self.content_patterns:
                for pattern, weight in self.content_patterns[doc_type]:
                    matches = len(re.findall(pattern, content_lower))
                    score += matches * weight
            type_scores[doc_type] = score
        
        # Get highest scoring type
        best_type = max(type_scores.items(), key=lambda x: x[1])
        
        if best_type[1] > 0:
            logger.info(f"Document type detected from content: {best_type[0]} (score: {best_type[1]})")
            return best_type[0]
        
        # Default to general type if no clear type
        logger.info("No specific document type detected, using general type")
        return DocumentType.GENERAL
    
    def _calculate_type_confidence(self, content: str, document_type: str) -> float:
        """
        Calculate confidence score for document type detection.
        
        Args:
            content: Document content
            document_type: Document type
            
        Returns:
            Confidence score
        """
        # Default confidence for general type
        if document_type == DocumentType.GENERAL:
            return 0.5
        
        # Calculate confidence based on pattern matches
        total_score = 0
        type_score = 0
        
        # Check content patterns for all types
        for doc_type in [DocumentType.FAQ, DocumentType.POLICY, DocumentType.PROCEDURE, DocumentType.MANUAL]:
            score = 0
            if doc_type in self.content_patterns:
                for pattern, weight in self.content_patterns[doc_type]:
                    matches = len(re.findall(pattern, content.lower()))
                    score += matches * weight
            
            total_score += score
            if doc_type == document_type:
                type_score = score
        
        # Avoid division by zero
        if total_score == 0:
            return 0.5
        
        # Calculate confidence as ratio of type score to total score
        confidence = min(0.95, max(0.5, type_score / total_score))
        return confidence
    
    def _extract_title(self, content: str, filename: str) -> str:
        """
        Extract document title from content or filename.
        
        Args:
            content: Document content
            filename: Filename
            
        Returns:
            Document title
        """
        # Try to find title in first few lines
        lines = content.split('\n')
        
        # Look for title patterns in first 10 lines
        for i in range(min(10, len(lines))):
            line = lines[i].strip()
            
            # Skip empty lines and page markers
            if not line or line.lower().startswith('page'):
                continue
            
            # Good title candidates are not too long, and not starting with common
            # non-title text
            if (len(line) < 100 and 
                not line.lower().startswith('table of contents') and
                not line.lower().startswith('copyright') and
                not line.lower().startswith('all rights')):
                
                # Clean up the title (remove excessive whitespace, etc.)
                title = re.sub(r'\s+', ' ', line).strip()
                return title
        
        # Fallback to filename without extension
        return Path(filename).stem.replace('_', ' ').title()
    
    def _parse_document(self, content: str, document_type: str) -> List[Dict[str, Any]]:
        """
        Parse document based on document type.
        
        Args:
            content: Document content
            document_type: Document type
            
        Returns:
            List of sections
        """
        # Use different parsing strategies based on document type
        if document_type == DocumentType.FAQ:
            sections = self._parse_faq_document(content)
        elif document_type == DocumentType.POLICY:
            sections = self._parse_policy_document(content)
        elif document_type == DocumentType.PROCEDURE:
            sections = self._parse_procedure_document(content)
        elif document_type == DocumentType.MANUAL:
            sections = self._parse_manual_document(content)
        else:
            # General document parsing
            sections = self._parse_general_document(content)
        
        # If no sections were found, fall back to general parsing
        if not sections:
            sections = self._parse_general_document(content)
        
        return sections
    
    def _parse_faq_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse FAQ document into Q&A pairs.
        
        Args:
            content: Document content
            
        Returns:
            List of sections
        """
        sections = []
        
        # Try to find Q&A patterns
        qa_patterns = [
            r"Q\s*:\s*(.*?)\s*\n\s*A\s*:\s*(.*?)(?=\n\s*Q\s*:|$)",  # Q: ... A: format
            r"Question\s*:\s*(.*?)\s*\n\s*Answer\s*:\s*(.*?)(?=\n\s*Question\s*:|$)",  # Question: ... Answer: format
            r"(?:^|\n)(?:(?!\n\s*\?\s*\n|$)(?:\n|.)*\?\s*\n)(?:(?!\n\s*\?\s*\n|$)(?:\n|.)*)",  # Question ending with ? followed by answer
        ]
        
        qa_pairs = []
        for pattern in qa_patterns:
            qa_pairs = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if qa_pairs:
                break
        
        for i, pair in enumerate(qa_pairs):
            if len(pair) > 2:
                question = pair[0].strip()
                answer = pair[1].strip()
            else:
                question = pair[0].strip()
                answer = pair[1].strip()
            
            section = DocumentSection(
                section_id=str(uuid.uuid4()),
                title=question,
                content=answer,
                section_type="qa_pair",
                parent_section=None,
                order=i
            ).to_dict()
            
            sections.append(section)
        
        return sections
    
    def _parse_policy_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse policy document into sections and subsections.
        
        Args:
            content: Document content
            
        Returns:
            List of sections
        """
        sections = []
        
        # Split content into lines
        lines = content.split('\n')
        
        current_section = None
        current_subsection = None
        section_id = None
        subsection_id = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Check if line is a section header (all caps, numbered, etc.)
            if re.match(r'^[A-Z][A-Z\s]+:', line) or re.match(r'^[0-9]+\.[A-Z\s]+', line) or line.isupper():
                # Save previous section if exists
                if current_section and current_content:
                    section_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=section_id or str(uuid.uuid4()),
                        title=current_section,
                        content=section_content,
                        section_type="policy_section",
                        parent_section=None,
                        order=len(sections)
                    ).to_dict())
                
                current_section = line
                section_id = str(uuid.uuid4())
                current_subsection = None
                current_content = []
                
            # Check if line is a subsection header
            elif (line.endswith(':') and not line.isupper()) or re.match(r'^[0-9]+\.[0-9]+\.', line):
                # Save previous subsection if exists
                if current_subsection and current_content:
                    section_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=subsection_id or str(uuid.uuid4()),
                        title=current_subsection,
                        content=section_content,
                        section_type="policy_subsection",
                        parent_section=section_id,
                        order=len(sections)
                    ).to_dict())
                
                current_subsection = line
                subsection_id = str(uuid.uuid4())
                current_content = []
                
            else:
                current_content.append(line)
        
        # Add the last section or subsection
        if current_subsection and current_content:
            section_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=subsection_id or str(uuid.uuid4()),
                title=current_subsection,
                content=section_content,
                section_type="policy_subsection",
                parent_section=section_id,
                order=len(sections)
            ).to_dict())
        elif current_section and current_content:
            section_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=section_id or str(uuid.uuid4()),
                title=current_section,
                content=section_content,
                section_type="policy_section",
                parent_section=None,
                order=len(sections)
            ).to_dict())
        
        return sections
    
    def _parse_procedure_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse procedure document into steps.
        
        Args:
            content: Document content
            
        Returns:
            List of sections
        """
        sections = []
        
        # Split content into lines
        lines = content.split('\n')
        
        current_procedure = None
        procedure_id = None
        current_step = None
        step_id = None
        current_content = []
        step_number = 0
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Check if line is a procedure header
            if re.match(r'^[A-Z][A-Z\s]+:|^[0-9]+\.[A-Z\s]+', line) or line.isupper():
                # Save previous procedure if exists
                if current_procedure and not current_step and current_content:
                    procedure_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=procedure_id or str(uuid.uuid4()),
                        title=current_procedure,
                        content=procedure_content,
                        section_type="procedure",
                        parent_section=None,
                        order=len(sections)
                    ).to_dict())
                
                current_procedure = line
                procedure_id = str(uuid.uuid4())
                current_content = []
                step_number = 0
                
            # Check if line is a step
            elif re.match(r'^(?:Step|STEP)\s+[0-9]+|^[0-9]+\.\s+', line):
                # Save previous step if exists
                if current_step and current_content:
                    step_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=step_id or str(uuid.uuid4()),
                        title=current_step,
                        content=step_content,
                        section_type="step",
                        parent_section=procedure_id,
                        order=step_number
                    ).to_dict())
                
                current_step = line
                step_id = str(uuid.uuid4())
                step_number += 1
                current_content = []
                
            else:
                current_content.append(line)
        
        # Add the last procedure or step
        if current_step and current_content:
            step_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=step_id or str(uuid.uuid4()),
                title=current_step,
                content=step_content,
                section_type="step",
                parent_section=procedure_id,
                order=step_number
            ).to_dict())
        elif current_procedure and current_content:
            procedure_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=procedure_id or str(uuid.uuid4()),
                title=current_procedure,
                content=procedure_content,
                section_type="procedure",
                parent_section=None,
                order=len(sections)
            ).to_dict())
        
        return sections
    
    def _parse_manual_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse manual document into chapters and sections.
        
        Args:
            content: Document content
            
        Returns:
            List of sections
        """
        sections = []
        
        # Try to identify chapters and sections
        lines = content.split('\n')
        
        current_chapter = None
        chapter_id = None
        current_section = None
        section_id = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Check if line is a chapter header
            if re.match(r'^(?:Chapter|CHAPTER)\s+\d+|^[0-9]+\.\s+[A-Z]+', line) or line.isupper():
                # Save previous chapter if exists
                if current_chapter and not current_section and current_content:
                    chapter_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=chapter_id or str(uuid.uuid4()),
                        title=current_chapter,
                        content=chapter_content,
                        section_type="chapter",
                        parent_section=None,
                        order=len(sections)
                    ).to_dict())
                
                current_chapter = line
                chapter_id = str(uuid.uuid4())
                current_section = None
                current_content = []
                
            # Check if line is a section header
            elif (line.endswith(':') and line.isupper()) or re.match(r'^[0-9]+\.[0-9]+\.\s+', line):
                # Save previous section if exists
                if current_section and current_content:
                    section_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=section_id or str(uuid.uuid4()),
                        title=current_section,
                        content=section_content,
                        section_type="manual_section",
                        parent_section=chapter_id,
                        order=len(sections)
                    ).to_dict())
                
                current_section = line
                section_id = str(uuid.uuid4())
                current_content = []
                
            else:
                current_content.append(line)
        
        # Add the last chapter or section
        if current_section and current_content:
            section_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=section_id or str(uuid.uuid4()),
                title=current_section,
                content=section_content,
                section_type="manual_section",
                parent_section=chapter_id,
                order=len(sections)
            ).to_dict())
        elif current_chapter and current_content:
            chapter_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=chapter_id or str(uuid.uuid4()),
                title=current_chapter,
                content=chapter_content,
                section_type="chapter",
                parent_section=None,
                order=len(sections)
            ).to_dict())
        
        return sections
    
    def _parse_general_document(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse general document into paragraphs.
        
        Args:
            content: Document content
            
        Returns:
            List of sections
        """
        sections = []
        
        # Split content by page markers
        pages = re.split(r'\n---\s+Page\s+\d+\s*---\n', content)
        
        # Process each page
        for page_num, page_content in enumerate(pages):
            if not page_content.strip():
                continue
            
            # Split into paragraphs
            paragraphs = re.split(r'\n\s*\n', page_content)
            
            # Create section for each paragraph
            for para_num, paragraph in enumerate(paragraphs):
                paragraph = paragraph.strip()
                
                # Skip very short paragraphs
                if len(paragraph) < 20:
                    continue
                
                # Create section for paragraph
                section = DocumentSection(
                    section_id=str(uuid.uuid4()),
                    title=f"Paragraph {page_num + 1}.{para_num + 1}",
                    content=paragraph,
                    section_type="paragraph",
                    parent_section=None,
                    order=len(sections)
                ).to_dict()
                
                sections.append(section)
        
        return sections
    
    def _save_processed_document(self, document: ProcessedDocument) -> None:
        """
        Save processed document to output directory.
        
        Args:
            document: Processed document
        """
        # Create company ID based subdirectory
        company_id = "caresetu"  # Default company ID
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get document ID
        doc_id = document.id[:8]
        
        # Save content file
        content_file = self.output_directory / f"{company_id}_{timestamp}_{doc_id}_content.txt"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(document.content)
        
        # Save metadata file
        metadata_file = self.output_directory / f"{company_id}_{timestamp}_{doc_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(document.to_dict(), f, indent=2)
        
        logger.info(f"Saved processed document to {content_file}")
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported document types."""
        return [
            DocumentType.FAQ,
            DocumentType.POLICY,
            DocumentType.PROCEDURE,
            DocumentType.MANUAL,
            DocumentType.GENERAL
        ]

async def test_pdf_processor():
    """Test the PDF processor."""
    # Process all PDFs in the directory
    processor = PDFProcessor()
    documents = await processor.process_all_pdfs()
    print(f"Processed {len(documents)} documents:")
    
    for doc in documents:
        print(f"- {doc.filename}: {doc.document_type} ({len(doc.sections)} sections)")

if __name__ == "__main__":
    asyncio.run(test_pdf_processor())