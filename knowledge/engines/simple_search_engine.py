"""
Simple Search Engine for Railway
Lightweight text-based search without vector databases
Memory optimized for Railway's 512MB limit
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Lightweight search result."""
    content: str
    relevance_score: float
    source: str
    snippet: str

class SimpleSearchEngine:
    """Memory-efficient search engine for Railway deployment."""
    
    def __init__(self):
        """Initialize with minimal memory footprint."""
        self.knowledge_base = {}
        self.load_basic_knowledge()
        logger.info("✅ Simple search engine initialized")
    
    def load_basic_knowledge(self):
        """Load essential knowledge base (hardcoded for Railway)."""
        
        # Basic CareSetu knowledge (no file I/O to save memory)
        self.knowledge_base = {
            "app_info": {
                "content": "CareSetu is a comprehensive healthcare platform offering online consultations, medicine delivery, lab tests, and home healthcare services. Available on Play Store and App Store.",
                "keywords": ["app", "platform", "services", "download", "mobile"]
            },
            
            "consultations": {
                "content": "Book online consultations with qualified doctors through CareSetu app. Available 24/7 with specialists in various fields including general medicine, pediatrics, and mental health.",
                "keywords": ["consultation", "doctor", "online", "appointment", "medical"]
            },
            
            "appointments": {
                "content": "Schedule appointments easily through the app or website. Available slots Monday to Friday 9 AM to 6 PM. Emergency consultations available 24/7.",
                "keywords": ["appointment", "schedule", "booking", "time", "availability"]
            },
            
            "medicines": {
                "content": "Order medicines online with prescription upload. Home delivery within 24 hours. Generic and branded medicines available with discounts.",
                "keywords": ["medicine", "pharmacy", "delivery", "prescription", "order"]
            },
            
            "support": {
                "content": "Customer support available through app chat, email, or phone. Technical issues resolved within 24 hours. Emergency support available 24/7.",
                "keywords": ["support", "help", "contact", "technical", "customer"]
            },
            
            "lab_tests": {
                "content": "Home sample collection for lab tests. Reports available within 24-48 hours. Wide range of tests including blood work, urine tests, and health checkups.",
                "keywords": ["lab", "test", "sample", "blood", "report", "home"]
            }
        }
        
        logger.info(f"📚 Loaded {len(self.knowledge_base)} knowledge entries")
    
    def search(self, query: str, max_results: int = 3) -> List[SearchResult]:
        """
        Simple keyword-based search.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        if not query.strip():
            return []
        
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        results = []
        
        for key, data in self.knowledge_base.items():
            content = data["content"]
            keywords = data["keywords"]
            
            # Calculate relevance score
            score = 0
            
            # Keyword matching
            keyword_matches = sum(1 for keyword in keywords if keyword in query_lower)
            score += keyword_matches * 2
            
            # Content word matching
            content_words = set(re.findall(r'\w+', content.lower()))
            word_matches = len(query_words.intersection(content_words))
            score += word_matches
            
            # Exact phrase matching (bonus)
            if query_lower in content.lower():
                score += 5
            
            if score > 0:
                # Create snippet
                snippet = self._create_snippet(content, query_words)
                
                results.append(SearchResult(
                    content=content,
                    relevance_score=score,
                    source=key,
                    snippet=snippet
                ))
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:max_results]
    
    def _create_snippet(self, content: str, query_words: set, max_length: int = 150) -> str:
        """Create a snippet highlighting relevant parts."""
        
        # Find sentences containing query words
        sentences = content.split('.')
        best_sentence = ""
        max_matches = 0
        
        for sentence in sentences:
            sentence_words = set(re.findall(r'\w+', sentence.lower()))
            matches = len(query_words.intersection(sentence_words))
            
            if matches > max_matches:
                max_matches = matches
                best_sentence = sentence.strip()
        
        # Truncate if too long
        if len(best_sentence) > max_length:
            best_sentence = best_sentence[:max_length] + "..."
        
        return best_sentence or content[:max_length] + "..."
    
    def get_answer(self, query: str) -> Optional[str]:
        """
        Get a direct answer for the query.
        
        Args:
            query: User question
            
        Returns:
            Direct answer or None
        """
        results = self.search(query, max_results=1)
        
        if results:
            best_result = results[0]
            
            # If high relevance, return direct answer
            if best_result.relevance_score >= 3:
                return best_result.content
        
        return None
    
    def add_knowledge(self, key: str, content: str, keywords: List[str]):
        """Add new knowledge entry (for future expansion)."""
        self.knowledge_base[key] = {
            "content": content,
            "keywords": keywords
        }
        logger.info(f"📝 Added knowledge entry: {key}")

# Test function for Railway deployment
def test_search_engine():
    """Test the search engine functionality."""
    
    engine = SimpleSearchEngine()
    
    test_queries = [
        "How do I book an appointment?",
        "What services does CareSetu offer?",
        "How to order medicines?",
        "Customer support contact"
    ]
    
    print("🔍 Railway Search Engine Test")
    print("=" * 40)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = engine.search(query)
        
        if results:
            best_result = results[0]
            print(f"Answer: {best_result.snippet}")
            print(f"Score: {best_result.relevance_score}")
        else:
            print("No results found")
    
    print("\n✅ Search engine test completed")

if __name__ == "__main__":
    test_search_engine()