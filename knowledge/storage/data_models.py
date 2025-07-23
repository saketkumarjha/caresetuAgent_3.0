from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class CompanyConfig:
    """Configuration for a company's document storage."""
    company_id: str
    name: str
    storage_path: str
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    collection_prefix: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "company_id": self.company_id,
            "name": self.name,
            "storage_path": self.storage_path,
            "embedding_model": self.embedding_model,
            "collection_prefix": self.collection_prefix
        }

@dataclass
class DocumentChunk:
    """A chunk of a document for vector storage."""
    chunk_id: str
    company_id: str
    document_id: str
    title: str
    content: str
    chunk_index: int
    total_chunks: int
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "company_id": self.company_id,
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "embedding": self.embedding
        }

@dataclass
class ProcessedDocument:
    """Represents a processed PDF document."""
    id: str
    filename: str
    title: str
    content: str
    document_type: str  # faq, policy, procedure, manual, general
    sections: List[Any]  # DocumentSection, but avoid import here
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
        # DocumentSection import should be handled in the caller
        return cls(
            id=data["id"],
            filename=data["filename"],
            title=data["title"],
            content=data["content"],
            document_type=data["document_type"],
            sections=data["sections"],
            metadata=data["metadata"],
            processed_at=datetime.fromisoformat(data["processed_at"]),
            source_path=data["source_path"]
        )

@dataclass
class KnowledgeEntry:
    """Unified knowledge entry that can come from JSON or PDF sources."""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    source_type: str  # "json" or "pdf"
    source_file: str
    company_id: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    # PDF-specific fields
    document_id: Optional[str] = None
    section_id: Optional[str] = None
    section_type: Optional[str] = None
    parent_section: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "source_type": self.source_type,
            "source_file": self.source_file,
            "company_id": self.company_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "document_id": self.document_id,
            "section_id": self.section_id,
            "section_type": self.section_type,
            "parent_section": self.parent_section
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntry':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            category=data["category"],
            tags=data["tags"],
            source_type=data["source_type"],
            source_file=data["source_file"],
            company_id=data["company_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
            document_id=data.get("document_id"),
            section_id=data.get("section_id"),
            section_type=data.get("section_type"),
            parent_section=data.get("parent_section")
        ) 