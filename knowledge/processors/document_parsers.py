"""
Specialized Document Parsers
Implements parsers for different document types (FAQ, policy, procedure, manual, general)
"""

import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Define document types
class DocumentType:
    """Document type constants."""
    FAQ = "faq"
    POLICY = "policy"
    PROCEDURE = "procedure"
    MANUAL = "manual"
    GENERAL = "general"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentSection:
    """Class representing a document section."""
    
    def __init__(self,
                 section_id: str,
                 title: str,
                 content: str,
                 section_type: str,
                 parent_section: Optional[str] = None,
                 order: int = 0,
                 metadata: Dict[str, Any] = None):
        """
        Initialize a document section.
        
        Args:
            section_id: Section ID
            title: Section title
            content: Section content
            section_type: Section type (header, paragraph, qa_pair, step, etc.)
            parent_section: Parent section ID
            order: Section order
            metadata: Section metadata
        """
        self.id = section_id
        self.title = title
        self.content = content
        self.section_type = section_type
        self.parent_section = parent_section
        self.order = order
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section_type": self.section_type,
            "parent_section": self.parent_section,
            "order": self.order,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentSection':
        """Create from dictionary."""
        return cls(
            section_id=data["id"],
            title=data["title"],
            content=data["content"],
            section_type=data["section_type"],
            parent_section=data.get("parent_section"),
            order=data.get("order", 0),
            metadata=data.get("metadata", {})
        )

class DocumentParser:
    """
    Base document parser class.
    Provides common functionality for all document parsers.
    """
    
    def __init__(self):
        """Initialize the document parser."""
        logger.info("Document parser initialized")
    
    def parse_document(self, content: str, doc_type: str = None, filename: str = "document.pdf") -> List[DocumentSection]:
        """
        Parse document content into sections based on document type.
        
        Args:
            content: Document content
            doc_type: Document type (if known)
            filename: Original filename
            
        Returns:
            List of document sections
        """
        # Use default document type if not provided
        if not doc_type:
            doc_type = DocumentType.GENERAL
        
        # Use appropriate parser based on document type
        if doc_type == DocumentType.FAQ:
            return self._parse_faq_document(content)
        elif doc_type == DocumentType.POLICY:
            return self._parse_policy_document(content)
        elif doc_type == DocumentType.PROCEDURE:
            return self._parse_procedure_document(content)
        elif doc_type == DocumentType.MANUAL:
            return self._parse_manual_document(content)
        else:
            return self._parse_general_document(content)
    
    def _parse_faq_document(self, content: str) -> List[DocumentSection]:
        """
        Parse FAQ document into question-answer pairs.
        
        Args:
            content: Document content
            
        Returns:
            List of document sections
        """
        sections = []
        
        # Try to find Q&A patterns
        qa_patterns = [
            # Q: ... A: format
            r"(?:^|\n)Q\s*:\s*(.*?)\s*(?:\n|\r\n)A\s*:\s*(.*?)(?=\n[QA]\s*:|$)",
            # Question: ... Answer: format
            r"(?:^|\n)Question\s*:\s*(.*?)\s*(?:\n|\r\n)Answer\s*:\s*(.*?)(?=\nQuestion|$)",
            # Q1. ... A1. format
            r"(?:^|\n)Q\d+[\.\)]\s*(.*?)\s*(?:\n|\r\n)A\d+[\.\)]\s*(.*?)(?=\nQ\d+|$)",
            # Numbered Q&A format
            r"(?:^|\n)\d+[\.\)]\s*(.*?\?)\s*(?:\n|\r\n)(.*?)(?=\n\d+[\.\)]|$)"
        ]
        
        qa_pairs = []
        for pattern in qa_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            if matches:
                for match in matches:
                    if len(match) >= 2:
                        question = match[0].strip()
                        answer = match[1].strip()
                        if question and answer:
                            qa_pairs.append((question, answer))
        
        # If no structured Q&A pairs found, try to identify question-like sentences
        if not qa_pairs:
            # Look for question marks followed by text
            questions = re.findall(r'(?:^|\n)([^?\n]*\?\s*)(?:\n|\r\n)(.*?)(?=\n[^\n]*\?|$)', content, re.DOTALL)
            for question, answer in questions:
                if len(question.strip()) > 10 and len(answer.strip()) > 10:
                    qa_pairs.append((question.strip(), answer.strip()))
        
        # Create sections for each Q&A pair
        for i, (question, answer) in enumerate(qa_pairs):
            section = DocumentSection(
                section_id=str(uuid.uuid4()),
                title=question,
                content=answer,
                section_type="qa_pair",
                order=i
            )
            sections.append(section)
        
        # If no sections were found, create a single section with all content
        if not sections:
            logger.warning("No Q&A pairs found in FAQ document, using general parsing")
            return self._parse_general_document(content)
        
        return sections
    
    def _parse_policy_document(self, content: str) -> List[DocumentSection]:
        """
        Parse policy document into sections and subsections.
        
        Args:
            content: Document content
            
        Returns:
            List of document sections
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
            if re.match(r'^[0-9]+\.?\s+[A-Z][A-Z\s]+', line) or re.match(r'^[A-Z][A-Z\s]+:', line) or line.isupper():
                # Save previous section if exists
                if current_section and current_content:
                    section_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=section_id or str(uuid.uuid4()),
                        title=current_section,
                        content=section_content,
                        section_type="policy_section",
                        order=len(sections)
                    ))
                
                # Start new section
                current_section = line
                section_id = str(uuid.uuid4())
                current_subsection = None
                subsection_id = None
                current_content = []
            
            # Check if line is a subsection header (numbered, etc.)
            elif current_section and (re.match(r'^[0-9]+\.[0-9]+\.?\s+', line) or re.match(r'^[a-z]\)\s+', line)):
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
                    ))
                
                # Start new subsection
                current_subsection = line
                subsection_id = str(uuid.uuid4())
                current_content = []
            
            else:
                # Add line to current content
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
            ))
        elif current_section and current_content:
            section_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=section_id or str(uuid.uuid4()),
                title=current_section,
                content=section_content,
                section_type="policy_section",
                order=len(sections)
            ))
        
        # If no sections were found, create a single section with all content
        if not sections:
            logger.warning("No sections found in policy document, using general parsing")
            return self._parse_general_document(content)
        
        return sections
    
    def _parse_procedure_document(self, content: str) -> List[DocumentSection]:
        """
        Parse procedure document into steps.
        
        Args:
            content: Document content
            
        Returns:
            List of document sections
        """
        sections = []
        
        # First, try to identify procedure sections using regex patterns
        procedure_patterns = [
            # Find numbered procedures like "1. APPOINTMENT BOOKING"
            (r'(?:^|\n)(\d+\.\s+[A-Z][A-Z\s]+)(?:\n|\r\n)(.*?)(?=\n\d+\.\s+[A-Z][A-Z\s]+|$)', re.DOTALL),
            # Find procedures with all caps headers like "APPOINTMENT BOOKING"
            (r'(?:^|\n)([A-Z][A-Z\s]+:?)(?:\n|\r\n)(.*?)(?=\n[A-Z][A-Z\s]+:?|$)', re.DOTALL)
        ]
        
        procedures = []
        for pattern, flags in procedure_patterns:
            matches = re.finditer(pattern, content, flags)
            for match in matches:
                if len(match.groups()) >= 2:
                    procedure_title = match.group(1).strip()
                    procedure_content = match.group(2).strip()
                    procedures.append((procedure_title, procedure_content))
        
        # If no procedures found, try to parse the whole document as one procedure
        if not procedures:
            procedures = [("PROCEDURE", content)]
        
        # Process each procedure and extract steps
        for procedure_idx, (procedure_title, procedure_content) in enumerate(procedures):
            procedure_id = str(uuid.uuid4())
            
            # Look for steps within the procedure content
            step_patterns = [
                # Find steps like "Step 1: Do something"
                r'(?:^|\n)(?:Step\s+(\d+)[\s:]+)([^\n]+)(?:\n|\r\n)(.*?)(?=\n(?:Step\s+\d+)|$)',
                # Find steps like "1. Do something"
                r'(?:^|\n)(?:(\d+)[\.\)]\s+)([^\n]+)(?:\n|\r\n)?(.*?)(?=\n\d+[\.\)]|$)'
            ]
            
            steps = []
            for pattern in step_patterns:
                matches = re.finditer(pattern, procedure_content, re.DOTALL)
                for match in matches:
                    if len(match.groups()) >= 2:
                        step_num = match.group(1)
                        step_title = match.group(2).strip()
                        step_content = match.group(3).strip() if len(match.groups()) >= 3 else ""
                        steps.append((int(step_num), f"Step {step_num}: {step_title}", step_content))
            
            # Sort steps by number
            steps.sort(key=lambda x: x[0])
            
            # Create procedure section
            procedure_section = DocumentSection(
                section_id=procedure_id,
                title=procedure_title,
                content=procedure_content,
                section_type="procedure",
                order=procedure_idx
            )
            sections.append(procedure_section)
            
            # Create step sections
            for step_idx, (step_num, step_title, step_content) in enumerate(steps):
                step_section = DocumentSection(
                    section_id=str(uuid.uuid4()),
                    title=step_title,
                    content=step_content,
                    section_type="step",
                    parent_section=procedure_id,
                    order=step_idx
                )
                sections.append(step_section)
            
            # If no steps were found but we have a procedure, try to extract steps using line-by-line analysis
            if not steps:
                lines = procedure_content.split('\n')
                current_step = None
                step_content = []
                step_idx = 0
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if line looks like a step
                    step_match = re.match(r'^(?:Step\s+(\d+)|(\d+)\.)\s+(.*)', line)
                    if step_match:
                        # Save previous step if exists
                        if current_step and step_content:
                            step_text = '\n'.join(step_content)
                            step_section = DocumentSection(
                                section_id=str(uuid.uuid4()),
                                title=current_step,
                                content=step_text,
                                section_type="step",
                                parent_section=procedure_id,
                                order=step_idx
                            )
                            sections.append(step_section)
                            step_idx += 1
                        
                        # Extract step number and title
                        step_num = step_match.group(1) or step_match.group(2)
                        step_title = step_match.group(3) if step_match.group(3) else f"Step {step_num}"
                        current_step = f"Step {step_num}: {step_title}"
                        step_content = []
                    else:
                        # Add line to current step content
                        if current_step:
                            step_content.append(line)
                
                # Add the last step
                if current_step and step_content:
                    step_text = '\n'.join(step_content)
                    step_section = DocumentSection(
                        section_id=str(uuid.uuid4()),
                        title=current_step,
                        content=step_text,
                        section_type="step",
                        parent_section=procedure_id,
                        order=step_idx
                    )
                    sections.append(step_section)
        
        # If no sections were found, create a single section with all content
        if not sections:
            logger.warning("No procedures or steps found in procedure document, using general parsing")
            return self._parse_general_document(content)
        
        return sections
    
    def _parse_manual_document(self, content: str) -> List[DocumentSection]:
        """
        Parse manual document into chapters and sections.
        
        Args:
            content: Document content
            
        Returns:
            List of document sections
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
            if re.match(r'^(?:Chapter|CHAPTER)\s+[0-9]+', line) or re.match(r'^[A-Z][A-Z\s]+:', line) or line.isupper():
                # Save previous chapter or section if exists
                if current_section and current_content:
                    section_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=section_id or str(uuid.uuid4()),
                        title=current_section,
                        content=section_content,
                        section_type="manual_section",
                        parent_section=chapter_id,
                        order=len(sections)
                    ))
                elif current_chapter and current_content:
                    chapter_content = '\n'.join(current_content)
                    sections.append(DocumentSection(
                        section_id=chapter_id or str(uuid.uuid4()),
                        title=current_chapter,
                        content=chapter_content,
                        section_type="chapter",
                        order=len(sections)
                    ))
                
                # Start new chapter
                current_chapter = line
                chapter_id = str(uuid.uuid4())
                current_section = None
                section_id = None
                current_content = []
            
            # Check if line is a section header
            elif current_chapter and (re.match(r'^[0-9]+\.[0-9]+\.?\s+', line) or re.match(r'^[A-Z][a-z]+\s+[A-Za-z\s]+', line)):
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
                    ))
                
                # Start new section
                current_section = line
                section_id = str(uuid.uuid4())
                current_content = []
            
            else:
                # Add line to current content
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
            ))
        elif current_chapter and current_content:
            chapter_content = '\n'.join(current_content)
            sections.append(DocumentSection(
                section_id=chapter_id or str(uuid.uuid4()),
                title=current_chapter,
                content=chapter_content,
                section_type="chapter",
                order=len(sections)
            ))
        
        # If no sections were found, create a single section with all content
        if not sections:
            logger.warning("No chapters or sections found in manual document, using general parsing")
            return self._parse_general_document(content)
        
        return sections
    
    def _parse_general_document(self, content: str) -> List[DocumentSection]:
        """
        Parse general document into paragraphs.
        
        Args:
            content: Document content
            
        Returns:
            List of document sections
        """
        sections = []
        
        # Split content by page markers
        page_pattern = r'\n---\s+Page\s+\d+\s+---\n'
        pages = re.split(page_pattern, content)
        
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
                
                section = DocumentSection(
                    section_id=str(uuid.uuid4()),
                    title=f"Page {page_num + 1}.{para_num + 1}",
                    content=paragraph,
                    section_type="paragraph",
                    order=len(sections)
                )
                sections.append(section)
        
        return sections

# Example usage
def test_document_parsers():
    """Test the document parsers."""
    parser = DocumentParser()
    
    # Test with sample content
    faq_content = """
    FREQUENTLY ASKED QUESTIONS
    
    Q1: What are your business hours?
    A1: We are open Monday-Friday 9AM-5PM, Saturday 10AM-2PM, closed Sunday.
    
    Q2: How do I contact customer support?
    A2: You can call us at (555) 123-4567 or email support@company.com
    
    APPOINTMENT QUESTIONS
    
    Q: How do I schedule an appointment?
    A: You can schedule online at our website or call our office.
    
    Q: Can I reschedule my appointment?
    A: Yes, please give us at least 24 hours notice.
    """
    
    policy_content = """
    COMPANY POLICIES DOCUMENT
    
    1. PRIVACY POLICY
       - How we collect personal information
       - How we use your data
       - Data sharing practices
       - Your privacy rights
    
    2. TERMS OF SERVICE
       - Service agreement terms
       - User responsibilities
       - Limitation of liability
       - Termination conditions
    
    3. CANCELLATION POLICY
       - How to cancel services
       - Cancellation fees
       - Refund procedures
       - Emergency cancellations
    """
    
    procedure_content = """
    OPERATIONAL PROCEDURES
    
    1. APPOINTMENT BOOKING
       Step 1: Customer calls or uses online system
       Step 2: Check availability in calendar
       Step 3: Confirm appointment details
       Step 4: Send confirmation
    
    2. CUSTOMER ONBOARDING
       Step 1: Welcome new customer
       Step 2: Collect required information
       Step 3: Set up account
       Step 4: Provide orientation
    """
    
    manual_content = """
    USER MANUAL
    
    CHAPTER 1: GETTING STARTED
    - Account setup instructions
    - First-time user guide
    - System requirements
    
    CHAPTER 2: USING OUR SERVICES
    - How to book appointments
    - How to make payments
    - How to access your account
    
    CHAPTER 3: TROUBLESHOOTING
    - Common issues and solutions
    - Error message explanations
    - When to contact support
    """
    
    general_content = """
    COMPANY INFORMATION
    
    ABOUT US
    - Company history and mission
    - Our values and commitment
    - Team information
    
    SERVICES WE OFFER
    - Service descriptions
    - Pricing information
    - Service areas
    
    CONTACT INFORMATION
    - Office locations
    - Phone numbers
    - Email addresses
    - Business hours
    """
    
    # Test parsing
    test_cases = [
        ("FAQ Document", faq_content, DocumentType.FAQ),
        ("Policy Document", policy_content, DocumentType.POLICY),
        ("Procedure Document", procedure_content, DocumentType.PROCEDURE),
        ("Manual Document", manual_content, DocumentType.MANUAL),
        ("General Document", general_content, DocumentType.GENERAL)
    ]
    
    print("Testing Document Parsers")
    print("=" * 50)
    
    for name, content, doc_type in test_cases:
        print(f"Parsing {name}:")
        sections = parser.parse_document(content, doc_type)
        print(f"Found {len(sections)} sections:")
        
        for i, section in enumerate(sections[:3]):  # Show first 3 sections
            print(f"  {i+1}. {section.section_type}: {section.title}")
            print(f"     Content: {section.content[:50]}...")
        
        if len(sections) > 3:
            print(f"  ... and {len(sections) - 3} more sections")
        
        print("-" * 50)

if __name__ == "__main__":
    test_document_parsers()