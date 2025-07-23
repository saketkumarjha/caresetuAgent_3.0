"""
Enhanced Knowledge Base with Semantic Search
Provides improved search across all collections
"""

import asyncio
import logging
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
from pathlib import Path

# Remove or comment out the following line:
# from cloud_vector_store import CloudVectorStore

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeDocument:
    """Represents a knowledge base document."""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    company_id: str
    embedding: Optional[List[float]] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class SearchResult:
    """Represents a search result from the knowledge base."""
    document: KnowledgeDocument
    score: float
    relevance_explanation: str
    vector_distance: float = 0.0

class SemanticKnowledgeBase:
    """
    Enhanced knowledge base with semantic search across all collections.
    """
    
    def __init__(self, 
                 company_id: str,
                 api_key: Optional[str] = None,
                 tenant: Optional[str] = None,
                 database: Optional[str] = None):
        """
        Initialize semantic knowledge base.
        
        Args:
            company_id: Company identifier
            api_key: ChromaDB Cloud API key
            tenant: ChromaDB Cloud tenant ID
            database: ChromaDB Cloud database name
        """
        self.company_id = company_id
        
        # Initialize ChromaDB Cloud vector store
        # Remove or comment out the following line:
        # self.vector_store = CloudVectorStore(
        #     api_key=api_key,
        #     tenant=tenant,
        #     database=database
        # )
        
        # Get collections for different document types
        self.collections = {
            "policies": self.vector_store.get_collection(company_id, "policies"),
            "faqs": self.vector_store.get_collection(company_id, "faqs"),
            "procedures": self.vector_store.get_collection(company_id, "procedures"),
            "general": self.vector_store.get_collection(company_id, "general")
        }
        
        logger.info(f"✅ Semantic knowledge base initialized for company: {company_id}")
    
    async def search(self, query: str, max_results: int = 5, min_score: float = 0.2) -> List[SearchResult]:
        """
        Search across all collections using semantic search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            min_score: Minimum relevance score
            
        Returns:
            List of search results ordered by relevance
        """
        logger.info(f"🔍 Searching all collections for: '{query}'")
        
        all_results = []
        
        # Search across all collections
        for collection_name, collection in self.collections.items():
            try:
                # Perform vector search
                search_results = collection.search(
                    query_text=query,
                    n_results=max_results,
                    use_hybrid=True  # Use hybrid search for better results
                )
                
                # Process results
                if search_results["documents"] and search_results["documents"][0]:
                    for i, (doc_text, doc_id, distance, metadata) in enumerate(zip(
                        search_results["documents"][0],
                        search_results["ids"][0],
                        search_results["distances"][0],
                        search_results["metadatas"][0] if search_results["metadatas"] else [{}] * len(search_results["documents"][0])
                    )):
                        # Calculate relevance score (invert distance)
                        relevance_score = 1.0 - min(distance, 1.0)
                        
                        # Use hybrid score if available
                        if "relevance_scores" in search_results and search_results["relevance_scores"]:
                            relevance_score = search_results["relevance_scores"][0][i]
                        
                        # Filter by minimum score
                        if relevance_score >= min_score:
                            # Create KnowledgeDocument from metadata
                            doc = KnowledgeDocument(
                                id=doc_id,
                                title=metadata.get("title", "Unknown"),
                                content=doc_text.split('\n\n', 1)[1] if '\n\n' in doc_text else doc_text,
                                category=metadata.get("category", collection_name),
                                tags=json.loads(metadata.get("tags", "[]")) if isinstance(metadata.get("tags"), str) else metadata.get("tags", []),
                                company_id=self.company_id
                            )
                            
                            # Generate relevance explanation
                            explanation = self._generate_relevance_explanation(doc, query, relevance_score)
                            
                            all_results.append(SearchResult(
                                document=doc,
                                score=relevance_score,
                                relevance_explanation=explanation,
                                vector_distance=distance
                            ))
                            
            except Exception as e:
                logger.error(f"❌ Error searching collection {collection_name}: {e}")
        
        # Sort by score (highest first) and limit results
        all_results.sort(key=lambda x: x.score, reverse=True)
        final_results = all_results[:max_results]
        
        logger.info(f"📋 Found {len(final_results)} relevant documents across all collections")
        return final_results
    
    def _generate_relevance_explanation(self, doc: KnowledgeDocument, query: str, score: float) -> str:
        """Generate explanation for why this document is relevant."""
        explanations = []
        
        query_lower = query.lower()
        
        if query_lower in doc.title.lower():
            explanations.append("title matches your question")
        
        if query_lower in doc.content.lower():
            explanations.append("content directly addresses your query")
        
        query_words = set(query_lower.split())
        tag_words = set(' '.join(doc.tags).lower().split())
        if query_words.intersection(tag_words):
            explanations.append("tagged with relevant keywords")
        
        if score > 0.8:
            explanations.append("high semantic similarity")
        elif score > 0.6:
            explanations.append("good semantic match")
        
        if not explanations:
            explanations.append("contains related information")
        
        return f"This document is relevant because it {' and '.join(explanations)} (score: {score:.2f})"
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        return self.vector_store.get_stats()

# Test the semantic knowledge base
async def test_semantic_search():
    """Test semantic search functionality."""
    
    print("🧪 Testing Semantic Knowledge Base")
    print("=" * 60)
    
    try:
        # Initialize semantic knowledge base
        kb = SemanticKnowledgeBase(
            company_id="caresetu",
            api_key='ck-8qMvVqpxS2ZPiA4rDDrPtT4Gjer1vawnCHNqANwqyxaF',
            tenant='952f5e15-854e-461e-83d1-3cef021c755c',
            database='Assembly_AI'
        )
        
        # Test queries
        test_queries = [
            "What are your business hours?",
            "How do I schedule an appointment?",
            "What is your cancellation policy?",
            "What services does CareSetu offer?",
            "How do I contact customer support?",
            "Is my medical data safe?",
            "How do I upload a prescription?",
            "Who can use the CareSetu app?"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = await kb.search(query, max_results=3)
            
            if results:
                print(f"  Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  Result {i}: {result.document.title}")
                    print(f"    Score: {result.score:.3f}")
                    print(f"    Category: {result.document.category}")
                    print(f"    Content: {result.document.content[:100]}...")
            else:
                print("  No results found")
        
        # Get stats
        stats = await kb.get_stats()
        print(f"\n📊 Knowledge Base Stats: {stats}")
        
        print("\n✅ Semantic search test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing semantic search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_semantic_search())