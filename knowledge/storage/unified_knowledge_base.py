"""
Unified Knowledge Base
Integrates parsed PDF content with existing JSON knowledge base
"""

import json
import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

from ..processors.document_parsers import DocumentSection, DocumentParser
from knowledge.storage.data_models import KnowledgeEntry, ProcessedDocument

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentMerger:
    """Handles duplicate detection and content prioritization."""
    
    def __init__(self):
        """Initialize the content merger."""
        self.similarity_threshold = 0.8
        logger.info("Content merger initialized")
    
    def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score between 0 and 1
        """
        # Simple similarity calculation using common words
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def find_duplicates(self, entries: List[KnowledgeEntry]) -> List[List[KnowledgeEntry]]:
        """
        Find duplicate entries based on content similarity.
        
        Args:
            entries: List of knowledge entries
            
        Returns:
            List of duplicate groups
        """
        duplicates = []
        processed = set()
        
        for i, entry1 in enumerate(entries):
            if entry1.id in processed:
                continue
            
            duplicate_group = [entry1]
            processed.add(entry1.id)
            
            for j, entry2 in enumerate(entries[i+1:], i+1):
                if entry2.id in processed:
                    continue
                
                similarity = self.calculate_content_similarity(entry1.content, entry2.content)
                if similarity >= self.similarity_threshold:
                    duplicate_group.append(entry2)
                    processed.add(entry2.id)
            
            if len(duplicate_group) > 1:
                duplicates.append(duplicate_group)
        
        return duplicates
    
    def prioritize_content(self, duplicate_group: List[KnowledgeEntry]) -> KnowledgeEntry:
        """
        Prioritize content from duplicate group.
        PDF content takes priority over JSON content.
        
        Args:
            duplicate_group: List of duplicate entries
            
        Returns:
            Prioritized entry
        """
        # Sort by priority: PDF first, then by update time
        sorted_entries = sorted(duplicate_group, key=lambda x: (
            0 if x.source_type == "pdf" else 1,
            -x.updated_at.timestamp()
        ))
        
        return sorted_entries[0]
    
    def merge_entries(self, entries: List[KnowledgeEntry]) -> List[KnowledgeEntry]:
        """
        Merge entries by removing duplicates and prioritizing content.
        
        Args:
            entries: List of knowledge entries
            
        Returns:
            Merged list of entries
        """
        duplicates = self.find_duplicates(entries)
        merged_entries = []
        processed_ids = set()
        
        # Process duplicate groups
        for duplicate_group in duplicates:
            prioritized_entry = self.prioritize_content(duplicate_group)
            merged_entries.append(prioritized_entry)
            
            for entry in duplicate_group:
                processed_ids.add(entry.id)
        
        # Add non-duplicate entries
        for entry in entries:
            if entry.id not in processed_ids:
                merged_entries.append(entry)
        
        logger.info(f"Merged {len(entries)} entries into {len(merged_entries)} entries")
        return merged_entries

class UnifiedKnowledgeBase:
    """
    Unified knowledge base that combines PDF and JSON knowledge sources.
    """
    
    def __init__(self, 
                 json_kb_path: str = "knowledge_base",
                 pdf_content_path: str = "company_documents",
                 unified_storage_path: str = "unified_knowledge_base"):
        """
        Initialize the unified knowledge base.
        
        Args:
            json_kb_path: Path to JSON knowledge base directory
            pdf_content_path: Path to processed PDF content directory
            unified_storage_path: Path to store unified knowledge base
        """
        self.json_kb_path = json_kb_path
        self.pdf_content_path = pdf_content_path
        self.unified_storage_path = unified_storage_path
        self.parser = DocumentParser()
        self.merger = ContentMerger()
        
        # Create unified storage directory if it doesn't exist
        os.makedirs(unified_storage_path, exist_ok=True)
        
        # Storage for loaded knowledge
        self.knowledge_entries: List[KnowledgeEntry] = []
        self.processed_documents: Dict[str, ProcessedDocument] = {}
        
        logger.info(f"Unified knowledge base initialized with paths: {json_kb_path}, {pdf_content_path}")
    
    def _load_json_knowledge(self) -> List[KnowledgeEntry]:
        """
        Load knowledge from JSON files.
        
        Returns:
            List of knowledge entries from JSON files
        """
        entries = []
        
        if not os.path.exists(self.json_kb_path):
            logger.warning(f"JSON knowledge base path does not exist: {self.json_kb_path}")
            return entries
        
        for filename in os.listdir(self.json_kb_path):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.json_kb_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert JSON data to KnowledgeEntry
                entry = KnowledgeEntry(
                    id=data.get("id", str(uuid.uuid4())),
                    title=data.get("title", ""),
                    content=data.get("content", ""),
                    category=data.get("category", "general"),
                    tags=data.get("tags", []),
                    source_type="json",
                    source_file=filename,
                    company_id=data.get("company_id", "default"),
                    created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                    updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
                    metadata=data
                )
                entries.append(entry)
                
            except Exception as e:
                logger.error(f"Error loading JSON file {filename}: {e}")
        
        logger.info(f"Loaded {len(entries)} entries from JSON knowledge base")
        return entries
    
    def _load_pdf_knowledge(self) -> List[KnowledgeEntry]:
        """
        Load knowledge from processed PDF content.
        
        Returns:
            List of knowledge entries from PDF content
        """
        entries = []
        
        if not os.path.exists(self.pdf_content_path):
            logger.warning(f"PDF content path does not exist: {self.pdf_content_path}")
            return entries
        
        # Group content and metadata files
        content_files = {}
        metadata_files = {}
        
        for filename in os.listdir(self.pdf_content_path):
            if filename.endswith('_content.txt'):
                doc_id = filename.replace('_content.txt', '')
                content_files[doc_id] = filename
            elif filename.endswith('_metadata.json'):
                doc_id = filename.replace('_metadata.json', '')
                metadata_files[doc_id] = filename
        
        # Process each document
        for doc_id in content_files:
            if doc_id not in metadata_files:
                logger.warning(f"Missing metadata for document {doc_id}")
                continue
            
            try:
                # Load content
                content_path = os.path.join(self.pdf_content_path, content_files[doc_id])
                with open(content_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Load metadata
                metadata_path = os.path.join(self.pdf_content_path, metadata_files[doc_id])
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Parse document into sections
                doc_type = metadata.get("category", "general")
                sections = self.parser.parse_document(content, doc_type, metadata.get("title", "document.pdf"))
                
                # Create ProcessedDocument
                processed_doc = ProcessedDocument(
                    id=doc_id,
                    filename=metadata.get("title", "document.pdf"),
                    title=metadata.get("title", "Document"),
                    content=content,
                    document_type=doc_type,
                    sections=sections,
                    metadata=metadata,
                    processed_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                    source_path=content_path
                )
                
                self.processed_documents[doc_id] = processed_doc
                
                # Create knowledge entries for each section
                for section in sections:
                    entry = KnowledgeEntry(
                        id=f"{doc_id}_{section.id}",
                        title=section.title,
                        content=section.content,
                        category=doc_type,
                        tags=metadata.get("tags", []) + [section.section_type],
                        source_type="pdf",
                        source_file=metadata.get("title", "document.pdf"),
                        company_id=metadata.get("company_id", "default"),
                        created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                        updated_at=datetime.now(),
                        metadata=metadata,
                        document_id=doc_id,
                        section_id=section.id,
                        section_type=section.section_type,
                        parent_section=section.parent_section
                    )
                    entries.append(entry)
                
            except Exception as e:
                logger.error(f"Error processing PDF document {doc_id}: {e}")
        
        logger.info(f"Loaded {len(entries)} entries from PDF content")
        return entries
    
    def load_all_knowledge(self) -> Dict[str, Any]:
        """
        Load all knowledge from JSON and PDF sources.
        
        Returns:
            Dictionary containing loaded knowledge statistics
        """
        # Load from both sources
        json_entries = self._load_json_knowledge()
        pdf_entries = self._load_pdf_knowledge()
        
        # Combine and merge entries
        all_entries = json_entries + pdf_entries
        merged_entries = self.merger.merge_entries(all_entries)
        
        self.knowledge_entries = merged_entries
        
        # Save unified knowledge base
        self._save_unified_knowledge()
        
        stats = {
            "total_entries": len(merged_entries),
            "json_entries": len(json_entries),
            "pdf_entries": len(pdf_entries),
            "processed_documents": len(self.processed_documents),
            "categories": list(set(entry.category for entry in merged_entries)),
            "source_files": list(set(entry.source_file for entry in merged_entries))
        }
        
        logger.info(f"Loaded unified knowledge base: {stats}")
        return stats
    
    def _save_unified_knowledge(self):
        """Save unified knowledge base to storage."""
        try:
            # Save knowledge entries
            entries_path = os.path.join(self.unified_storage_path, "knowledge_entries.json")
            with open(entries_path, 'w', encoding='utf-8') as f:
                json.dump([entry.to_dict() for entry in self.knowledge_entries], f, indent=2, ensure_ascii=False)
            
            # Save processed documents
            docs_path = os.path.join(self.unified_storage_path, "processed_documents.json")
            with open(docs_path, 'w', encoding='utf-8') as f:
                json.dump({doc_id: doc.to_dict() for doc_id, doc in self.processed_documents.items()}, 
                         f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved unified knowledge base to {self.unified_storage_path}")
            
        except Exception as e:
            logger.error(f"Error saving unified knowledge base: {e}")
    
    def _load_unified_knowledge(self) -> bool:
        """
        Load unified knowledge base from storage.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Load knowledge entries
            entries_path = os.path.join(self.unified_storage_path, "knowledge_entries.json")
            if os.path.exists(entries_path):
                with open(entries_path, 'r', encoding='utf-8') as f:
                    entries_data = json.load(f)
                self.knowledge_entries = [KnowledgeEntry.from_dict(data) for data in entries_data]
            
            # Load processed documents
            docs_path = os.path.join(self.unified_storage_path, "processed_documents.json")
            if os.path.exists(docs_path):
                with open(docs_path, 'r', encoding='utf-8') as f:
                    docs_data = json.load(f)
                self.processed_documents = {doc_id: ProcessedDocument.from_dict(data) 
                                          for doc_id, data in docs_data.items()}
            
            logger.info(f"Loaded unified knowledge base from storage")
            return True
            
        except Exception as e:
            logger.error(f"Error loading unified knowledge base from storage: {e}")
            return False
    
    def update_from_pdfs(self, pdf_documents: List[ProcessedDocument]):
        """
        Update knowledge base with new PDF documents.
        
        Args:
            pdf_documents: List of processed PDF documents
        """
        new_entries = []
        
        for doc in pdf_documents:
            # Store processed document
            self.processed_documents[doc.id] = doc
            
            # Create knowledge entries for each section
            for section in doc.sections:
                entry = KnowledgeEntry(
                    id=f"{doc.id}_{section.id}",
                    title=section.title,
                    content=section.content,
                    category=doc.document_type,
                    tags=doc.metadata.get("tags", []) + [section.section_type],
                    source_type="pdf",
                    source_file=doc.filename,
                    company_id=doc.metadata.get("company_id", "default"),
                    created_at=doc.processed_at,
                    updated_at=datetime.now(),
                    metadata=doc.metadata,
                    document_id=doc.id,
                    section_id=section.id,
                    section_type=section.section_type,
                    parent_section=section.parent_section
                )
                new_entries.append(entry)
        
        # Merge with existing entries
        all_entries = self.knowledge_entries + new_entries
        merged_entries = self.merger.merge_entries(all_entries)
        self.knowledge_entries = merged_entries
        
        # Save updated knowledge base
        self._save_unified_knowledge()
        
        logger.info(f"Updated knowledge base with {len(pdf_documents)} PDF documents, {len(new_entries)} new entries")
    
    def get_knowledge_by_category(self, category: str) -> List[KnowledgeEntry]:
        """
        Get knowledge entries by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of knowledge entries in the category
        """
        return [entry for entry in self.knowledge_entries if entry.category == category]
    
    def get_knowledge_by_source(self, source_type: str) -> List[KnowledgeEntry]:
        """
        Get knowledge entries by source type.
        
        Args:
            source_type: Source type ("json" or "pdf")
            
        Returns:
            List of knowledge entries from the source
        """
        return [entry for entry in self.knowledge_entries if entry.source_type == source_type]
    
    def get_document_sections(self, document_id: str) -> List[KnowledgeEntry]:
        """
        Get all sections for a specific document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of knowledge entries for the document
        """
        return [entry for entry in self.knowledge_entries if entry.document_id == document_id]

# Example usage and testing
def test_unified_knowledge_base():
    """Test the unified knowledge base."""
    print("Testing Unified Knowledge Base")
    print("=" * 50)
    
    # Initialize knowledge base
    kb = UnifiedKnowledgeBase()
    
    # Load all knowledge
    stats = kb.load_all_knowledge()
    print(f"Knowledge Base Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nSample Knowledge Entries:")
    for i, entry in enumerate(kb.knowledge_entries[:5]):
        print(f"{i+1}. [{entry.source_type}] {entry.title}")
        print(f"   Category: {entry.category}")
        print(f"   Content: {entry.content[:100]}...")
        print(f"   Tags: {entry.tags}")
        print()
    
    # Test category filtering
    faq_entries = kb.get_knowledge_by_category("faqs")
    print(f"FAQ entries: {len(faq_entries)}")
    
    # Test source filtering
    pdf_entries = kb.get_knowledge_by_source("pdf")
    json_entries = kb.get_knowledge_by_source("json")
    print(f"PDF entries: {len(pdf_entries)}")
    print(f"JSON entries: {len(json_entries)}")

if __name__ == "__main__":
    test_unified_knowledge_base()