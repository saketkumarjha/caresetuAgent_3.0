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
from typing import Dict, List, Any, Optional, Tuple, Union
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

class ProcessedDoct:
    """Class representing a processed document."""
    
    def __init__(self, 
                 doc_id: str,
                 filename: str,
                 title: str,
                 content: str,
                 document_type: str,
                 sections: List[Dict[str, Any]],
                 metadata: Dict[str, Any],
                 source_path: str):
        """
        Initialize a processed document.
        
        Args:
            doc_id: Document ID
            filename: Original filename
            title: Document title
            content: Full document content
            document_type: Document type (faq, policy, procedure, manual, general)
            sections: List of document sections
            metadata: Document metadata
            source_path: Source file path
        """
        self.id = doc_id
        self.filename = filename
        self.title = title
        self.content = content
        self.document_type = document_type
        self.sections = sections
        self.metadata = metadata
        self.processed_at = datetime.now().isoformat()
        self.source_path = source_path
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "content": self.content,
            "document_type": self.document_type,
            "sections": self.sections,
            "metadata": self.metadata,
            "processed_at": self.processed_at,
            "source_path": self.source_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessedDocument':
        """Create from dictionary."""
        return cls(
            doc_id=data["id"],
            filename=data["filename"],
            title=data["title"],
            content=data["content"],
            document_type=data["document_type"],
            sections=data["sections"],
            metadata=data["metadata"],
            source_path=data["source_path"]
        )

class DocumentSect
    """Class representing a document section."""
    
    def __init__(self,
                 section_id: str,
                 title: str,
                 content: str,
                 section_type: str,
                 parent_section: Optional[str] = None,
                 order: int = 0,
                 metadata: Optional[Dict[str, Any]] = None):
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

class S:
    """
    Sim
    
    
    def __i"):
        """
        ocessor.
        
        Args:
            pdf_directory: Directory containing PDF files
           uments
        """
        self.pdf_directory = Path(pdf_directory)
        self.output_directory = Path(output_directory)
        
        
        # Document type detection patterns
        self.document_type_patt{
            DocumentType.FAQ: [
                r"frequ
                r"faq",
                r"common\s+qus",
                r"q\s*&\s*a",
              
            ],
            DocumentType.P[
                r"policy",
                r"policies",
                r"terms\s+of\s+service",
                r"terms\s+a
                r"privacy",
                r"data\s+protion",
              ce"
            ],
            DocumentType.PROC
                r"procedure
                r"process",
                r"step\s+by\s+step",
                r"instructions",
                r"how\s+to",
              "
            ],
            DocumentType.MANUAL: [
                r"manual",
                r"guide",
                r"handbook",
                r"documentat
             "
           ]
        }
        
        # Content-based detectionic)
        self.content_patterns =
            DocumentType.FAQ: [
                (r"Q\s*:.*?\nA\s*:", 5),  # Q: ... A: format with high weight
                (r"Question\s*:.*?\nAnswer\s*:", 5),  # Question: ... Ansormat
              
            ],
            DocumentType.POLICY: [
                (r"policy", 2)
                (r"terms", 2),
                (r"agreement", 2),
                (r"privacy", 3),
                (r"compliance",
                (r"legal", 2),
                (r"rights", 1),
              1)
            ],
            DocumentType.PROCEDURE: [
                (r"step\s+\d+", 3),  # Step 1, c.
                (r"\d+\.\s+", 2),  # 1. 2. etc.
                (r"first.*?then.
                (r"process", 1),
                (r"procedure", 2),
                (r"instruction 2),
              )
            ],
            DocumentType.MANUAL: [
                (r"chapter", 3),
                (r"section", 2
                (r"guide", 2),
                (r"manual", 3),
                (r"reference", 2)
                (r"appendix", 3),
                (r"figure", 1
             able", 1)
         
        }
        
        # Check if PDF libraries are available
        if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        
        
  

    async dcument]:
        """
        directory.
        
        Returns:
           
        """
        ts = []
        
        # Check if directory exists
        if not self.pdf_directory.exists():
            logger.error(f
        ults
        
        # Process each PDF file
        for pdf_f"):
            try:
                processed_doc = ae))
                if processed_doc:
                    results.appenddoc)
            except Exception as e:
        
        
        logger.info(f"iles")
    s
    
    async dnt]:
        """
        ile.
        
        Args:
            F file
            
        Returns:
           d
        """
        h)
        
        # Check if file exists
        if not pdf_path.exists():
            logger.erro
        rn None
        
        )
        
        try:
            # Generate document ID
            )
            
            # Extract text from PDF
            
            
            if not content.strip():
                logger.erro
            one
            
            # Detect document type
            e)
            
            # Extract title
            
            
            # Parse document based on type
            
            
            # Create metadata
            metadata = {
                "original_filename": pdf_path.name,
                "file_size": os.path.getsize(pdf_path),
                "processed_at": datetime.now().
                "document_type": document_type,
             )
            
            
            # Create processed document
            processed_doc = Pr
                doc_id=doc_id,
                filename=pdfth.name,
                title=title,
                content=content,
                document_type=docut_type,
                sections=sections,
                metadata=metadata,
             
            )
            
            # Save processed document
            
            
            logger.info(f"Succes
            d_doc
            
        except Exception as e:
            logger.error(f")
      
    
    def _generate_document_id(self, pdf_path: Path) -> str:
        """Generate a unique document ID based on file path an""
        # Create a hash of the file path and modification time
        file_info = f"{pdf_path}_{os.path.getmtime(pdf_pat"
    ()
    
    def _exstr:
        """
        F file.
        
        Args:
            
            
        Returns:
           
        """
        "
        
        if not PDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
        er.")
        
        try:
            # Try PyPDF2 firs
            if PDF_AVAILABLE:
                with open(pdf_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    for pageges):
                        try:
                            page_text = p
                            if page_text:
                                text += f"\n--- Page {page"
                                text += page_t"
                        except Exception as e:
            }: {e}")
            
            # If text is empty or very short, try pdfplumbck
            if (len(text) < 100) :
                import pdfplumber
                text = ""  # Reset text
                with pdfplumber.open(pdf_path) as pdf:
                    for page:
                        try:
                            page_text = p
                            if page_text:
                                text += f"\n--- Page {page"
                                text += page_t\n\n"
                        except Exception as e:
        e}")
        
        except Exception as e:
            loggeh}: {e}")
        raise
        
  xt  
  
    def _de
        """
        
        
        Args:
            content: Document 
            
            
        Returns:
           pe
        """
        content_lower = content.lower()
        ()
        
        # Check filename first (highest priority)
        for doc_type, patterns in sems():
            for pattern in patterns:
                if re.search(pattern, filename_lower):
                    logger.info(f"D")
        _type
        
        # Then check con
        type_scores = {}
        for doc_type UAL]:
            score = 0
            if doc_type in self.content_patterns:
                for pattern, weight in self.content_patterns[doc_type]:
                    matches = re.findall(pattern, 
                    score += len(matches)
        e
        
        # Check general patterns (less specific)
        for doc_type, patterns in self.document_ems():
            score = type_scores.get()
            for pattern in patterns:
                matches = re.findall(pattower)
                score += len(matches) * 2
        score
        
        # Get highest sng type
        if type_scores:
            best_type = max(type x: x[1])
            if best_type[1] > 0:
                logger.info(f"Docum")
        ype[0]
        
        # Default to general if no clear type
        logger.info("No specific do type")
    .GENERAL
    
    def _calculate_type_confidence(self, content: str, document_type: -> float:
        """Calculate confidence score for documen
        if document_type == DocumentType.GENERAL:
         type
        
        # Calculate conmatches
        total_score = 0
         0
        
        # Check content patterns for all types
        for doc_type NUAL]:
            score = 0
            if doc_type in self.content_patterns:
                for pattern, weight in self.content_patterns[doc_type]:
                    matches = len(re.findall())
             * weight
            
            if doc_type == documen:
                type_score = score
        score
        
        # Avoid division by zero
        if total_score:
        .5
        
        # Calculate confidence as ratio of type score to total sco
        confidence = min(0_score))
    
   
    def _ex
        """
        lename.
        
        Args:
            content: Document ntent
            
            
        Returns:
           title
        """
        # Try to find title in firslines
        
        
        # Look for title patterns in first 1
        for i in range(min(10, len():
            )
            
            # Skip page markers and empty lines
            if not line  < 3:
                ue
                
            # Good title candidates 
            if (len(line) < 100 and 
                )):
                
                # Clean up the title (remove excessive wh
                title = re.s)
        
        
        # Fall back to filename without extension
    
    
    def _pa Any]]:
        """
        
        
        Args:
            content: Document content
            e
            
        Returns:
           ons
        """
        
        
        # Use different parsing strategies baument type
        if document_type == DocumentType.FAQ:
            sections = self._parse_faq_document(cotent)
        elif document_type == DocumentType.POLICY:
            sections = self._parse_policy_document(co
        elif document_type == DocumentType.PROCEDURE:
            sections = self._parse_procedure_docum
        elif document_type == DocumentType.MANUAL:
            s)
        else:
            # General document parsing
        )
        
        # If no sections content
        if not sections:
            sections.append(DocumentSection(
                section_id=str(uuid.u,
                title="Main Contt",
                content=content,
                sectionon",
                order=0
        
        
   
  
    def _parse_faq_document(self, content: str) r, Any]]:
        """Parse FAQ """
        s = []
        
        # Try to find Q
        qa_patterns = [
            r"Q\s*:\s*(.*?)\s*\n\s*A\s*:\s*(.*?)(?=\n\s*Q\s*:|$)",  # Q: ... A: format
            r"Question\s*:\s*(.*?)\s*\n\s*Answer\s*:\s*(.*?)(?=\n\s*Question\s*:|$)",  # Question: ... Answer: format
         er
        ]
        
        for pattern in qa_patterns:
            qa_pairs = r)
            if qa_pairs:
                for i, pair in enumera):
                    if len(pair) >= 2:
                        question = pair[0].strip
                        
                        
                        if question and answer:
                            section = DocumentSection(
                                section_id=str(id4()),
                                title=question,
                                content=answer,
                                section",
                                order=i
                            ).to_dict()
        (section)
        
        # If no Q&A pairg
        if not sections:
            )
            
    
    
    def _parse_policy_document(self, content: str) -> List[Dict[st
        """Parse poli
        = []
        
        # Split content into lines
        
        
        current_section = None
        current_subsection = None
        current_content =
        section_id = None
         = None
        
        for line in lines:
            line = line.
            if not line:
            ue
            
            # Check if line is a section header (all caps, numbered, etc.)
            if re.match(r'^[0-9]+\.?\s+[A-Z]', liline):
                # Save previous section if exists
                if current_section and current_content:
                    section_content = '\n'.join(currtent)
                    sections.append(DocumentSection(
                        section_id=section_id ,
                        title=current_section,
                        content=section_content,
                        section_type="polic,
                        order=leions)
                    ).to_dict())
                ]
                
                current_section = line
                section_id = str(uuid.uui)
                e
                
            # Check if line is a subsection header
            elif current_section and (re.match(r'^[0-9]+\.[0-9]+\.?\s+', line) or 
                                     (line.endswith(er())):
                # Save previous subsection if exists
                if current_subsection and current_content:
                    section_content = '\n'.join(currt)
                    sections.append(DocumentSection(
                        section_id=subsection_id 
                        title=current_subsection,
                        content=section_content,
                        section_type="policy_subsection",
                        parent_section=sectd,
                        order=le)
                    ).to_dict())
                ntent = []
                
                current_subsection = line
                
                
            else:
        ine)
        
        # Add the last section or subsection
        if current_subsection and current_content:
            section_content = '\n'.join(currt)
            sections.append(DocumentSection(
                section_id=subsection_id uid4()),
                title=current_subsection,
                content=section_content,
                section_type="policy_subseon",
                parent_section=sectid,
                order=le
            ).to_dict())
        elif current_section and current_content:
            section_content = '\n'.join(curr)
            sections.append(DocumentSection(
                section_id=section_id ,
                title=current_section,
                content=section_content,
                section_type="polic
                order=les)
        t())
        
        # If no sections
        if not sections:
            nt)
            
         
    
    def _parse_procedure_document(self, content: sny]]:
        """Parse procs."""
        ions = []
        
        # Try to identify procedure
        ')
        
        current_procedure =
        current_step = None
        current_content = [
        procedure_id =
        step_id = None
        er = 0
        
        for line in lines:
            line = line.
            if not line:
            e
            
            # Check if line is a procedure header
            if re.match(r'^[A-Z][A-Z\s]+:|^[0-9]+\.):
                # Save previous procedure if exists
                if current_procedure and current_content and not c
                    procedure_content = '\n'.join(cunt)
                    sections.append(DocumentSection(
                        section_id=procedure_id uid4()),
                        title=current_procedure,
                        content=procedure_content,
                        section_type="proce",
                        order=leons)
                    ).to_dict())
                = []
                
                # Save previous step if exists
                if current_step and current_content:
                    step_content = '\n'.join(current)
                    sections.append(DocumentSection(
                        section_id=step_id ,
                        title=current_step,
                        content=step_content,
                        section_type="step",
                        parent_section=pr,
                        order=str
                    ).to_dict())
                = []
                
                current_procedure = line
                procedure_id = str(id4())
                current_step = None
                 0
                
            # Check if line is a step
            elif re.match(r'^(?:Step|STEP)\s+[):
                # Save previous step if exists
                if current_step and current_content:
                    step_content = '\n'.join(currentt)
                    sections.append(DocumentSection(
                        section_id=step_id 
                        title=current_step,
                        content=step_content,
                        section_type="step",
                        parent_section=pr
                        order=ster
                    ).to_dict())
                []
                
                current_step = line
                step_id = str(uu)
                er += 1
                
            else:
        (line)
        
        # Add the last procedure or step
        if current_step and current_content:
            step_content = '\n'.join(current
            sections.append(DocumentSection(
                section_id=step_id ,
                title=current_step,
                content=step_content,
                section_type="step",
                parent_section=pr_id,
                order=stumber
            ).to_dict())
        elif current_procedure and current_content:
            procedure_content = '\n'.join(cu)
            sections.append(DocumentSection(
                section_id=procedure_id d4()),
                title=current_procedure,
                content=procedure_content
                section_type="proce
                order=le)
        ())
        
        # If no sectionsg
        if not sections:
            
            
   sections 
   
    def _parse_manual_document(self, content: str) -> List[Dict, Any]]:
        """Parse manu"
        
        
        # Try to identify chapters ns
        n')
        
        current_chapter = None
        current_section = None
        current_content = []
        chapter_id = None
        None
        
        for line in lines:
            line = line.)
            if not line:
            tinue
            
            # Check if line is a chapter header
            if re.match(r'^(?:Chapter|CHAPTER)\s+):
                # Save previous chapter if exists
                if current_chapter and current_content and not cn:
                    chapter_content = '\n'.join(currt)
                    sections.append(DocumentSection(
                        section_id=chapter_id )),
                        title=current_chapter,
                        content=chapter_content,
                        section_type="chapt
                        order=les)
                    ).to_dict())
                tent = []
                
                # Save previous section if exists
                if current_section and current_content:
                    section_content = '\n'.join(currcontent)
                    sections.append(DocumentSection(
                        section_id=section_id id4()),
                        title=current_section,
                        content=section_content,
                        section_type="manual_secti,
                        parent_section=chap_id,
                        order=le
                    ).to_dict())
                ]
                
                current_chapter = line
                chapter_id = str(uuid.))
                n = None
                
            # Check if line is a section header
            elif current_chapter and (re.match(r'^[0-9]+\.[0-9]+\.?\s+', line) or 
                                     (line.endswi
                # Save previous section if exists
                if current_section and current_content:
                    section_content = '\n'.join(currt)
                    sections.append(DocumentSection(
                        section_id=section_id 
                        title=current_section,
                        content=section_content,
                        section_type="manual_secti",
                        parent_section=chap,
                        order=leections)
                    ).to_dict())
                = []
                
                current_section = line
                4())
                
            else:
        (line)
        
        # Add the last chapter or section
        if current_section and current_content:
            section_content = '\n'.join(currcontent)
            sections.append(DocumentSection(
                section_id=section_id 
                title=current_section,
                content=section_content,
                section_type="manual_secti",
                parent_section=chapter_id,
                order=le
            ).to_dict())
        elif current_chapter and current_content:
            chapter_content = '\n'.join(currnt)
            sections.append(DocumentSection(
                section_id=chapter_id ,
                title=current_chapter,
                content=chapter_content,
                section_type="chapt,
                order=les)
        
        
        # If no sections
        if not sections:
            
            
s
    
    def _parse_general_document(self, content: str):
        """Parse genehs."""
        s = []
        
        # Split content by pagkers
        page_pattern = r'\n-*---\n'
        
        
        # Process each page
        ages):
            if not page_co:
                continue
                
            # Split pageraphs
            ent)
            
            for para_num, paragraph in enumerats):
                paragraph = paragraph.strip()
                if len(paragraph) < 20:  # Skip very shragraphs
                    continue
                    
                # Create section for paragraph
                section = DocumentSection(
                    section_id=str(uuid.uuid4())
                    title=f"Paragraph {page_num",
                    content=paragraph,
                    section_typeaph",
                    order=len(sections)
                ()
                
                section)
        
        ections
    
    def _save_processed_document(self, documente:
        """
        Save processed document to output diectory.
        
        Args:
            document: Processed document
        """
        # Create hash-based subdireollisions
        doc_hash = docum
        ash
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Save content file
        content_file = output_dir / f"{docume
        with open(content_file, 'w', 
            f.write(document.con
        
        # Save metadataile
        metadata_file = "
         as f:
            json.dump(d=2)
     
        logger.info(f"Saved processed document to {out}")
    
    def get_supported_types(self) -tr]:
        """Get list of supp"""
        return [
        FAQ,
            DocumentType.POLICY,
            DocumentType.PROCEDURE,
            DocumentTypUAL,
        ENERAL
        ]

# Example usage
async de():
    """Test the PDF ())f_processor.run(test_pdncio   asyn__":
 "__maie__ == 

if __namsections)")s)} c.sectionen(do({lment_type} docue}: {doc.{doc.filenamrint(f"-      p
   uments:in docor doc   f:")
   documentsuments)}en(doced {lf"Processt( prin   

    ll_pdfs()rocess_aprocessor.p = await cumentsory
    doirectn the dll PDFs icess a   # Pro
 ()
    essorProcPDFimplecessor = S    pro"""
cessor.pro