"""
Document Type Detector
Implements logic to identify document types (FAQ, policy, procedure, manual, general)
based on content patterns and keywords.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentType:
    """Document types for PDF documents."""
    FAQ = "faq"
    POLICY = "policy"
    PROCEDURE = "procedure"
    MANUAL = "manual"
    GENERAL = "general"
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported document types."""
        return [cls.FAQ, cls.POLICY, cls.PROCEDURE, cls.MANUAL, cls.GENERAL]

class DocumentTypeDetector:
    """
    Detects document types based on content patterns and keywords.
    Implements advanced detection rules for different document types.
    """
    
    def __init__(self):
        """Initialize the document type detector with detection patterns."""
        # Filename-based detection patterns (highest priority)
        self.filename_patterns = {
            DocumentType.FAQ: [
                r"faq",
                r"frequently\s*asked\s*questions",
                r"q\s*&\s*a",
                r"questions",
                r"answers"
            ],
            DocumentType.POLICY: [
                r"policy",
                r"policies",
                r"terms",
                r"agreement",
                r"privacy",
                r"compliance",
                r"legal",
                r"security"
            ],
            DocumentType.PROCEDURE: [
                r"procedure",
                r"process",
                r"workflow",
                r"steps",
                r"how\s*to",
                r"guide",
                r"instructions"
            ],
            DocumentType.MANUAL: [
                r"manual",
                r"handbook",
                r"guide",
                r"documentation",
                r"reference",
                r"user\s*guide"
            ]
        }
        
        # Content-based detection patterns with weights
        self.content_patterns = {
            DocumentType.FAQ: [
                # Q&A format patterns (high weight)
                (r"Q\s*:.*?\nA\s*:", 5),  # Q: ... A: format
                (r"Question\s*:.*?\nAnswer\s*:", 5),  # Question: ... Answer: format
                (r"(?:^|\n)Q[0-9]*[\.\)]\s+", 4),  # Q1. Q2. format
                (r"(?:^|\n)(?:What|How|Why|When|Where|Who|Can|Is|Are|Do|Does|Will|Should)\s+.+\?", 3),  # Question sentences
                (r"frequently\s+asked\s+questions", 5),
                (r"common\s+questions", 4),
                (r"faq", 5)
            ],
            DocumentType.POLICY: [
                (r"policy", 3),
                (r"terms\s+(?:of\s+service|and\s+conditions)", 5),
                (r"agreement", 2),
                (r"privacy", 3),
                (r"compliance", 2),
                (r"legal", 2),
                (r"rights\s+(?:and|or)\s+responsibilities", 4),
                (r"liability", 2),
                (r"copyright", 2),
                (r"intellectual\s+property", 3),
                (r"confidentiality", 3),
                (r"data\s+protection", 4)
            ],
            DocumentType.PROCEDURE: [
                (r"step\s+\d+", 4),  # Step 1, Step 2
                (r"\d+\.\s+", 2),  # 1. 2. etc.
                (r"procedure", 3),
                (r"process", 2),
                (r"instructions", 3),
                (r"follow\s+these\s+steps", 5),
                (r"how\s+to", 3),
                (r"workflow", 3),
                (r"first,?\s+.+\s+then,?\s+.+\s+(?:finally|lastly)", 4),  # First... Then... Finally...
                (r"(?:begin|start)\s+by", 3)
            ],
            DocumentType.MANUAL: [
                (r"chapter", 3),
                (r"section", 2),
                (r"manual", 5),
                (r"guide", 3),
                (r"handbook", 4),
                (r"reference", 2),
                (r"appendix", 3),
                (r"figure", 1),
                (r"table", 1),
                (r"troubleshooting", 4),
                (r"installation", 2),
                (r"configuration", 2),
                (r"setup", 2)
            ]
        }
        
        # Structural patterns for document types
        self.structural_patterns = {
            DocumentType.FAQ: [
                # Q&A pairs in various formats
                r"(?:^|\n)(?:Q|Question)[\d\.\s\:]+.+?(?:\n|\r\n)(?:A|Answer)[\d\.\s\:]+.+?(?=\n(?:Q|Question)|$)",
                r"(?:^|\n)(?:\d+[\.\)]\s*).+?\?(?:\s*\n|\s*\r\n).+?(?=\n\d+[\.\)]|$)"
            ],
            DocumentType.POLICY: [
                # Numbered sections with legal language
                r"(?:^|\n)(?:\d+[\.\)]\s*)[A-Z][A-Za-z\s]+(?:\n|\r\n)(?:[A-Za-z\s\d\.,;:\(\)\-\'\"]+(?=\n\d+[\.\)]|$))",
                r"(?:^|\n)(?:[A-Z][A-Za-z\s]+:)(?:\n|\r\n)(?:[A-Za-z\s\d\.,;:\(\)\-\'\"]+(?=\n[A-Z][A-Za-z\s]+:|$))"
            ],
            DocumentType.PROCEDURE: [
                # Step-by-step instructions
                r"(?:^|\n)(?:Step\s*\d+[\.\):\s]*).+?(?=\n(?:Step\s*\d+)|$)",
                r"(?:^|\n)(?:\d+[\.\)]\s*).+?(?=\n\d+[\.\)]|$)"
            ],
            DocumentType.MANUAL: [
                # Chapter/section structure
                r"(?:^|\n)(?:Chapter|Section)\s*\d+[\.\s\:]+.+?(?=\n(?:Chapter|Section)|$)",
                r"(?:^|\n)(?:\d+[\.\d]*\s+)[A-Z][A-Za-z\s]+(?:\n|\r\n)"
            ]
        }
        
        # Semantic indicators (key phrases that strongly indicate document type)
        self.semantic_indicators = {
            DocumentType.FAQ: [
                "frequently asked questions", "common questions", "questions and answers"
            ],
            DocumentType.POLICY: [
                "terms of service", "privacy policy", "data protection policy", 
                "refund policy", "cancellation policy", "code of conduct"
            ],
            DocumentType.PROCEDURE: [
                "step by step guide", "how to", "procedure for", "process flow",
                "follow these instructions", "workflow"
            ],
            DocumentType.MANUAL: [
                "user manual", "user guide", "reference guide", "handbook",
                "troubleshooting guide", "installation guide"
            ]
        }
        
        logger.info("Document type detector initialized with detection patterns")
    
    def detect_document_type(self, content: str, filename: str) -> Tuple[str, float]:
        """
        Detect document type based on content and filename.
        
        Args:
            content: Document content
            filename: Document filename
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        content_lower = content.lower()
        filename_lower = Path(filename).stem.lower()
        
        # Check filename first (highest priority)
        for doc_type, patterns in self.filename_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    logger.info(f"Document type detected from filename: {doc_type}")
                    return doc_type, 0.95  # High confidence for filename match
        
        # Initialize scores for each document type
        type_scores = {doc_type: 0.0 for doc_type in DocumentType.get_supported_types()}
        
        # Check content patterns with weights
        for doc_type, patterns in self.content_patterns.items():
            for pattern, weight in patterns:
                matches = re.findall(pattern, content_lower)
                type_scores[doc_type] += len(matches) * weight
        
        # Check structural patterns (these are more complex and indicate document structure)
        for doc_type, patterns in self.structural_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                # Structural matches are stronger indicators
                type_scores[doc_type] += len(matches) * 3
        
        # Check for semantic indicators (exact phrases that strongly indicate document type)
        for doc_type, indicators in self.semantic_indicators.items():
            for indicator in indicators:
                if indicator in content_lower:
                    type_scores[doc_type] += 10  # High weight for exact semantic indicators
        
        # Get highest scoring type
        if type_scores:
            # Find the document type with the highest score
            best_type = max(type_scores.items(), key=lambda x: x[1])
            
            # Calculate confidence based on score difference between top and second best
            scores = sorted(type_scores.values(), reverse=True)
            score_diff = scores[0] - scores[1] if len(scores) > 1 else scores[0]
            
            # Calculate confidence (normalized between 0.5 and 0.95)
            confidence = min(0.95, max(0.5, (best_type[1] / 100) + (score_diff / 100)))
            
            if best_type[1] > 0:
                logger.info(f"Document type detected: {best_type[0]} (score: {best_type[1]}, confidence: {confidence:.2f})")
                return best_type[0], confidence
        
        # Default to general if no clear type
        logger.info("No specific document type detected, using general type with low confidence")
        return DocumentType.GENERAL, 0.5
    
    def analyze_document_structure(self, content: str) -> Dict[str, int]:
        """
        Analyze document structure to provide detailed insights.
        
        Args:
            content: Document content
            
        Returns:
            Dictionary with structure analysis results
        """
        analysis = {
            "total_length": len(content),
            "paragraphs": len(re.findall(r'\n\s*\n', content)) + 1,
            "questions": len(re.findall(r'\?', content)),
            "numbered_items": len(re.findall(r'\n\s*\d+[\.\)]\s+', content)),
            "sections": len(re.findall(r'\n\s*[A-Z][A-Z\s]+\s*(?::|\.|\n)', content)),
            "bullet_points": len(re.findall(r'\n\s*[\•\-\*]\s+', content)),
            "tables": len(re.findall(r'\|\s*[\w\s]+\s*\|', content)),
            "urls": len(re.findall(r'https?://\S+', content)),
            "emails": len(re.findall(r'\S+@\S+\.\S+', content))
        }
        
        return analysis
    
    def get_document_sections(self, content: str, doc_type: str) -> List[Dict]:
        """
        Extract potential document sections based on document type.
        This is a preliminary analysis to help with document parsing.
        
        Args:
            content: Document content
            doc_type: Document type
            
        Returns:
            List of potential sections with their titles and positions
        """
        sections = []
        
        if doc_type == DocumentType.FAQ:
            # Look for question patterns
            questions = re.finditer(r'(?:^|\n)(?:Q[\d\.\:\s]*|Question[\d\.\:\s]*|\d+[\.\)]\s*)(.*?\?)', content)
            for i, match in enumerate(questions):
                sections.append({
                    "type": "question",
                    "title": match.group(1).strip(),
                    "position": match.start(),
                    "index": i
                })
                
        elif doc_type == DocumentType.POLICY:
            # Look for policy section headers
            headers = re.finditer(r'(?:^|\n)(?:\d+[\.\)]\s*)?([A-Z][A-Z\s]+)(?::|\.|\n)', content)
            for i, match in enumerate(headers):
                sections.append({
                    "type": "policy_section",
                    "title": match.group(1).strip(),
                    "position": match.start(),
                    "index": i
                })
                
        elif doc_type == DocumentType.PROCEDURE:
            # Look for steps or procedure sections
            steps = re.finditer(r'(?:^|\n)(?:Step\s*\d+[\.\):\s]*|\d+[\.\)]\s*)(.+?)(?=\n|$)', content)
            for i, match in enumerate(steps):
                sections.append({
                    "type": "step",
                    "title": match.group(1).strip(),
                    "position": match.start(),
                    "index": i
                })
                
        elif doc_type == DocumentType.MANUAL:
            # Look for chapters, sections, or headings
            headings = re.finditer(r'(?:^|\n)(?:Chapter|Section)?\s*(?:\d+[\.\d]*\s+)?([A-Z][A-Za-z\s]+)(?::|\.|\n)', content)
            for i, match in enumerate(headings):
                sections.append({
                    "type": "heading",
                    "title": match.group(1).strip(),
                    "position": match.start(),
                    "index": i
                })
        
        # For all document types, look for generic section headers
        generic_headers = re.finditer(r'(?:^|\n)([A-Z][A-Z\s]+:)', content)
        for i, match in enumerate(generic_headers):
            # Check if this header is already included
            header_pos = match.start()
            if not any(abs(section["position"] - header_pos) < 20 for section in sections):
                sections.append({
                    "type": "header",
                    "title": match.group(1).strip(':'),
                    "position": header_pos,
                    "index": len(sections)
                })
        
        # Sort sections by position
        sections.sort(key=lambda x: x["position"])
        
        return sections

# Example usage
def test_document_type_detector():
    """Test the document type detector."""
    detector = DocumentTypeDetector()
    
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
    
    # Test detection
    test_cases = [
        ("faq.pdf", faq_content),
        ("policy_document.pdf", policy_content),
        ("procedures.pdf", procedure_content),
        ("user_manual.pdf", manual_content),
        ("company_info.pdf", general_content),
        ("random_document.pdf", "This is some random content that doesn't fit any specific pattern.")
    ]
    
    print("Testing Document Type Detector")
    print("=" * 50)
    
    for filename, content in test_cases:
        doc_type, confidence = detector.detect_document_type(content, filename)
        print(f"File: {filename}")
        print(f"Detected Type: {doc_type}")
        print(f"Confidence: {confidence:.2f}")
        
        # Get structure analysis
        analysis = detector.analyze_document_structure(content)
        print(f"Structure Analysis: {analysis}")
        
        # Get sections
        sections = detector.get_document_sections(content, doc_type)
        print(f"Detected {len(sections)} sections:")
        for i, section in enumerate(sections[:3]):  # Show first 3 sections
            print(f"  {i+1}. {section['type']}: {section['title']}")
        
        if len(sections) > 3:
            print(f"  ... and {len(sections) - 3} more sections")
        
        print("-" * 50)

if __name__ == "__main__":
    test_document_type_detector()