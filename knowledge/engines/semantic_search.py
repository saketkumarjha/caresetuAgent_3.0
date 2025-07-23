"""
Semantic Search for careSetu Support Agent
Provides enhanced search across all collections
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from knowledge.managers.knowledge_base_semantic import SemanticKnowledgeBase, SearchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SemanticSearchEngine:
    """
    Semantic search engine for careSetu support agent.
    Searches across all collections for better results.
    """
    
    def __init__(self, 
                 company_id: str,
                 api_key: Optional[str] = None,
                 tenant: Optional[str] = None,
                 database: Optional[str] = None):
        """
        Initialize semantic search engine.
        
        Args:
            company_id: Company identifier
            api_key: ChromaDB Cloud API key
            tenant: ChromaDB Cloud tenant ID
            database: ChromaDB Cloud database name
        """
        self.company_id = company_id
        
        # Initialize semantic knowledge base
        self.knowledge_base = SemanticKnowledgeBase(
            company_id=company_id,
            api_key=api_key,
            tenant=tenant,
            database=database
        )
        
        logger.info(f"✅ Semantic search engine initialized for company: {company_id}")
    
    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search across all collections and prepare response.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results and metadata
        """
        start_time = datetime.now()
        
        # Search across all collections
        results = await self.knowledge_base.search(query, max_results=max_results)
        
        # Calculate confidence from search results
        confidence = max(result.score for result in results) if results else 0.0
        
        # Prepare response data
        response_data = {
            "results": results,
            "confidence": confidence,
            "sources": [result.document.title for result in results],
            "search_results_count": len(results),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }
        
        return response_data
    
    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """
        Format search results for LLM prompt.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string for LLM prompt
        """
        if not results:
            return "No relevant information found in the knowledge base."
        
        formatted_parts = []
        
        for i, result in enumerate(results, 1):
            doc = result.document
            formatted_parts.append(f"""
Knowledge Source {i} (Relevance Score: {result.score:.2f}):
Title: {doc.title}
Category: {doc.category}
Tags: {', '.join(doc.tags)}
Content: {doc.content}
Relevance: {result.relevance_explanation}
""")
        
        return "\n".join(formatted_parts)

async def test_semantic_search_engine():
    """Test the semantic search engine."""
    
    print("🧪 Testing Semantic Search Engine")
    print("=" * 60)
    
    try:
        # Initialize semantic search engine
        engine = SemanticSearchEngine(
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
            response = await engine.search(query, max_results=3)
            
            print(f"  Confidence: {response['confidence']:.3f}")
            print(f"  Results: {response['search_results_count']}")
            print(f"  Sources: {response['sources']}")
            print(f"  Processing time: {response['processing_time']:.3f}s")
            
            if response['results']:
                print("\n  Top result:")
                top_result = response['results'][0]
                print(f"    Title: {top_result.document.title}")
                print(f"    Category: {top_result.document.category}")
                print(f"    Content: {top_result.document.content[:100]}...")
                
                # Format for LLM
                print("\n  LLM Format Sample:")
                llm_format = engine.format_results_for_llm([top_result])
                print(f"    {llm_format[:200]}...")
        
        print("\n✅ Semantic search engine test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing semantic search engine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_semantic_search_engine())