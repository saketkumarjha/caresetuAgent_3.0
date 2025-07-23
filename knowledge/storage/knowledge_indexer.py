"""
Knowledge Indexer
Implements text-based indexing for search and metadata tagging for document sections
"""

import re
import json
import os
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime
import math
from dataclasses import dataclass

from knowledge.storage.data_models import CompanyConfig, DocumentChunk, KnowledgeEntry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchResult:
    """Represents a search result."""
    
    def __init__(self,
                 entry_id: str,
                 title: str,
                 content: str,
                 relevance_score: float,
                 category: str,
                 source_type: str,
                 source_file: str,
                 document_id: Optional[str] = None,
                 section_id: Optional[str] = None,
                 section_type: Optional[str] = None,
                 snippet: str = "",
                 matched_terms: List[str] = None):
        """
        Initialize search result.
        
        Args:
            entry_id: Knowledge entry ID
            title: Entry title
            content: Entry content
            relevance_score: Relevance score (0-1)
            category: Entry category
            source_type: Source type (json/pdf)
            source_file: Source file name
            document_id: Document ID (for PDF entries)
            section_id: Section ID (for PDF entries)
            section_type: Section type (for PDF entries)
            snippet: Content snippet with highlighted terms
            matched_terms: List of matched search terms
        """
        self.entry_id = entry_id
        self.title = title
        self.content = content
        self.relevance_score = relevance_score
        self.category = category
        self.source_type = source_type
        self.source_file = source_file
        self.document_id = document_id
        self.section_id = section_id
        self.section_type = section_type
        self.snippet = snippet
        self.matched_terms = matched_terms or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "category": self.category,
            "source_type": self.source_type,
            "source_file": self.source_file,
            "document_id": self.document_id,
            "section_id": self.section_id,
            "section_type": self.section_type,
            "snippet": self.snippet,
            "matched_terms": self.matched_terms
        }

class TextProcessor:
    """Handles text processing for indexing."""
    
    def __init__(self):
        """Initialize text processor."""
        # Common stop words to filter out
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'you', 'your', 'we', 'our', 'us',
            'i', 'me', 'my', 'this', 'these', 'they', 'them', 'their', 'have',
            'had', 'can', 'could', 'should', 'would', 'may', 'might', 'must',
            'shall', 'do', 'does', 'did', 'get', 'got', 'go', 'went', 'come',
            'came', 'see', 'saw', 'know', 'knew', 'think', 'thought', 'say',
            'said', 'tell', 'told', 'ask', 'asked', 'give', 'gave', 'take',
            'took', 'make', 'made', 'put', 'set', 'let', 'use', 'used', 'find',
            'found', 'work', 'worked', 'call', 'called', 'try', 'tried', 'need',
            'needed', 'feel', 'felt', 'seem', 'seemed', 'leave', 'left', 'move',
            'moved', 'turn', 'turned', 'start', 'started', 'show', 'showed',
            'play', 'played', 'run', 'ran', 'begin', 'began', 'help', 'helped',
            'talk', 'talked', 'become', 'became', 'change', 'changed', 'end',
            'ended', 'why', 'how', 'where', 'when', 'what', 'who', 'which',
            'whom', 'whose', 'if', 'then', 'than', 'or', 'but', 'not', 'no',
            'yes', 'all', 'any', 'each', 'every', 'some', 'many', 'much',
            'more', 'most', 'other', 'another', 'such', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'now', 'here', 'there',
            'up', 'out', 'down', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'also', 'back', 'still', 'well', 'away', 'around',
            'because', 'before', 'after', 'above', 'below', 'between', 'through',
            'during', 'without', 'within', 'along', 'following', 'across',
            'behind', 'beyond', 'plus', 'except', 'but', 'up', 'out', 'about',
            'into', 'onto', 'upon'
        }
        
        logger.info("Text processor initialized")
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and extract words
        text = text.lower()
        tokens = re.findall(r'\b[a-zA-Z]+\b', text)
        
        # Filter out stop words and short words
        filtered_tokens = [token for token in tokens 
                          if token not in self.stop_words and len(token) > 2]
        
        return filtered_tokens
    
    def extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """
        Extract keywords from text using frequency analysis.
        
        Args:
            text: Input text
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords sorted by importance
        """
        tokens = self.tokenize(text)
        
        # Count token frequencies
        token_counts = Counter(tokens)
        
        # Get most common tokens as keywords
        keywords = [token for token, count in token_counts.most_common(max_keywords)]
        
        return keywords
    
    def create_snippet(self, text: str, search_terms: List[str], max_length: int = 200) -> str:
        """
        Create a snippet from text highlighting search terms.
        
        Args:
            text: Source text
            search_terms: Terms to highlight
            max_length: Maximum snippet length
            
        Returns:
            Text snippet with highlighted terms
        """
        if not search_terms:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Find the best position to start the snippet
        text_lower = text.lower()
        best_pos = 0
        max_matches = 0
        
        # Look for position with most search term matches
        for i in range(0, len(text) - max_length + 1, 50):
            snippet_text = text_lower[i:i + max_length]
            matches = sum(1 for term in search_terms if term.lower() in snippet_text)
            if matches > max_matches:
                max_matches = matches
                best_pos = i
        
        # Extract snippet
        snippet = text[best_pos:best_pos + max_length]
        
        # Add ellipsis if needed
        if best_pos > 0:
            snippet = "..." + snippet
        if best_pos + max_length < len(text):
            snippet = snippet + "..."
        
        # Highlight search terms (simple approach)
        for term in search_terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            snippet = pattern.sub(f"**{term}**", snippet)
        
        return snippet

class KnowledgeIndexer:
    """
    Knowledge indexer that provides text-based indexing for search.
    """
    
    def __init__(self, knowledge_base, index_storage_path: str = "knowledge_index"):
        # Import here to avoid circular import
        from knowledge.storage.unified_knowledge_base import UnifiedKnowledgeBase
        self.knowledge_base = knowledge_base
        self.index_storage_path = index_storage_path
        self.text_processor = TextProcessor()
        
        # Create index storage directory
        os.makedirs(index_storage_path, exist_ok=True)
        
        # Index structures
        self.word_index: Dict[str, Set[str]] = defaultdict(set)  # word -> set of entry_ids
        self.entry_keywords: Dict[str, List[str]] = {}  # entry_id -> keywords
        self.entry_metadata: Dict[str, Dict[str, Any]] = {}  # entry_id -> metadata
        self.category_index: Dict[str, Set[str]] = defaultdict(set)  # category -> entry_ids
        self.source_index: Dict[str, Set[str]] = defaultdict(set)  # source_type -> entry_ids
        self.document_index: Dict[str, Set[str]] = defaultdict(set)  # document_id -> entry_ids
        
        logger.info(f"Knowledge indexer initialized with storage path: {index_storage_path}")
    
    def build_index(self):
        """Build the search index from knowledge base."""
        logger.info("Building knowledge index...")
        
        # Clear existing index
        self.word_index.clear()
        self.entry_keywords.clear()
        self.entry_metadata.clear()
        self.category_index.clear()
        self.source_index.clear()
        self.document_index.clear()
        
        # Index each knowledge entry
        for entry in self.knowledge_base.knowledge_entries:
            self._index_entry(entry)
        
        # Save index to storage
        self._save_index()
        
        logger.info(f"Index built with {len(self.entry_metadata)} entries, {len(self.word_index)} unique words")
    
    def _index_entry(self, entry: KnowledgeEntry):
        """
        Index a single knowledge entry.
        
        Args:
            entry: Knowledge entry to index
        """
        # Extract keywords from title and content
        title_keywords = self.text_processor.extract_keywords(entry.title, 10)
        content_keywords = self.text_processor.extract_keywords(entry.content, 30)
        
        # Combine and deduplicate keywords
        all_keywords = list(set(title_keywords + content_keywords))
        self.entry_keywords[entry.id] = all_keywords
        
        # Index words
        for keyword in all_keywords:
            self.word_index[keyword].add(entry.id)
        
        # Index tags
        for tag in entry.tags:
            tag_words = self.text_processor.tokenize(tag)
            for word in tag_words:
                self.word_index[word].add(entry.id)
        
        # Store entry metadata for search results
        self.entry_metadata[entry.id] = {
            "title": entry.title,
            "content": entry.content,
            "category": entry.category,
            "source_type": entry.source_type,
            "source_file": entry.source_file,
            "document_id": entry.document_id,
            "section_id": entry.section_id,
            "section_type": entry.section_type,
            "tags": entry.tags,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat()
        }
        
        # Build category index
        self.category_index[entry.category].add(entry.id)
        
        # Build source index
        self.source_index[entry.source_type].add(entry.id)
        
        # Build document index (for PDF entries)
        if entry.document_id:
            self.document_index[entry.document_id].add(entry.id)
    
    def search(self, 
               query: str, 
               category: Optional[str] = None,
               source_type: Optional[str] = None,
               document_id: Optional[str] = None,
               max_results: int = 20) -> List[SearchResult]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query
            category: Filter by category
            source_type: Filter by source type
            document_id: Filter by document ID
            max_results: Maximum number of results
            
        Returns:
            List of search results sorted by relevance
        """
        if not query.strip():
            return []
        
        # Tokenize query
        query_terms = self.text_processor.tokenize(query)
        if not query_terms:
            return []
        
        # Find matching entries
        matching_entries = self._find_matching_entries(query_terms)
        
        # Apply filters
        if category:
            matching_entries = matching_entries.intersection(self.category_index[category])
        
        if source_type:
            matching_entries = matching_entries.intersection(self.source_index[source_type])
        
        if document_id:
            matching_entries = matching_entries.intersection(self.document_index[document_id])
        
        # Calculate relevance scores and create results
        results = []
        for entry_id in matching_entries:
            if entry_id not in self.entry_metadata:
                continue
            
            metadata = self.entry_metadata[entry_id]
            relevance_score = self._calculate_relevance(entry_id, query_terms)
            
            # Create snippet
            snippet = self.text_processor.create_snippet(
                metadata["content"], 
                query_terms
            )
            
            # Find matched terms
            entry_keywords = self.entry_keywords.get(entry_id, [])
            matched_terms = [term for term in query_terms if term in entry_keywords]
            
            result = SearchResult(
                entry_id=entry_id,
                title=metadata["title"],
                content=metadata["content"],
                relevance_score=relevance_score,
                category=metadata["category"],
                source_type=metadata["source_type"],
                source_file=metadata["source_file"],
                document_id=metadata["document_id"],
                section_id=metadata["section_id"],
                section_type=metadata["section_type"],
                snippet=snippet,
                matched_terms=matched_terms
            )
            results.append(result)
        
        # Sort by relevance score (descending)
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:max_results]
    
    def _find_matching_entries(self, query_terms: List[str]) -> Set[str]:
        """
        Find entries that match query terms.
        
        Args:
            query_terms: List of query terms
            
        Returns:
            Set of matching entry IDs
        """
        if not query_terms:
            return set()
        
        # Find entries for each term
        term_matches = []
        for term in query_terms:
            matches = self.word_index.get(term, set())
            term_matches.append(matches)
        
        # Start with entries that match the first term
        if not term_matches:
            return set()
        
        matching_entries = term_matches[0].copy()
        
        # For multiple terms, use intersection (AND logic)
        if len(term_matches) > 1:
            for matches in term_matches[1:]:
                matching_entries = matching_entries.intersection(matches)
        
        # If no exact matches, try OR logic (any term matches)
        if not matching_entries and len(term_matches) > 1:
            matching_entries = set()
            for matches in term_matches:
                matching_entries = matching_entries.union(matches)
        
        return matching_entries
    
    def _calculate_relevance(self, entry_id: str, query_terms: List[str]) -> float:
        """
        Calculate relevance score for an entry.
        
        Args:
            entry_id: Entry ID
            query_terms: Query terms
            
        Returns:
            Relevance score between 0 and 1
        """
        if entry_id not in self.entry_metadata or entry_id not in self.entry_keywords:
            return 0.0
        
        metadata = self.entry_metadata[entry_id]
        entry_keywords = self.entry_keywords[entry_id]
        
        # Calculate term frequency score
        tf_score = 0.0
        for term in query_terms:
            if term in entry_keywords:
                # Count occurrences in title (weighted higher)
                title_count = metadata["title"].lower().count(term)
                content_count = metadata["content"].lower().count(term)
                
                tf_score += (title_count * 2.0) + content_count
        
        # Normalize by content length
        content_length = len(metadata["content"].split())
        if content_length > 0:
            tf_score = tf_score / math.log(content_length + 1)
        
        # Calculate coverage score (how many query terms are matched)
        matched_terms = sum(1 for term in query_terms if term in entry_keywords)
        coverage_score = matched_terms / len(query_terms)
        
        # Calculate tag bonus
        tag_bonus = 0.0
        for tag in metadata["tags"]:
            tag_words = self.text_processor.tokenize(tag)
            for term in query_terms:
                if term in tag_words:
                    tag_bonus += 0.1
        
        # Calculate recency bonus (newer content gets slight boost)
        try:
            updated_at = datetime.fromisoformat(metadata["updated_at"])
            days_old = (datetime.now() - updated_at).days
            recency_bonus = max(0, 1.0 - (days_old / 365.0)) * 0.1
        except:
            recency_bonus = 0.0
        
        # Combine scores
        final_score = (tf_score * 0.5) + (coverage_score * 0.3) + tag_bonus + recency_bonus
        
        # Normalize to 0-1 range
        return min(1.0, final_score)
    
    def get_suggestions(self, partial_query: str, max_suggestions: int = 10) -> List[str]:
        """
        Get search suggestions based on partial query.
        
        Args:
            partial_query: Partial search query
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested search terms
        """
        if len(partial_query) < 2:
            return []
        
        partial_lower = partial_query.lower()
        suggestions = []
        
        # Find words that start with the partial query
        for word in self.word_index:
            if word.startswith(partial_lower):
                suggestions.append(word)
        
        # Sort by frequency (number of entries containing the word)
        suggestions.sort(key=lambda w: len(self.word_index[w]), reverse=True)
        
        return suggestions[:max_suggestions]
    
    def get_related_terms(self, term: str, max_terms: int = 10) -> List[str]:
        """
        Get terms related to the given term.
        
        Args:
            term: Input term
            max_terms: Maximum number of related terms
            
        Returns:
            List of related terms
        """
        if term not in self.word_index:
            return []
        
        # Get entries containing the term
        term_entries = self.word_index[term]
        
        # Count co-occurring terms
        cooccurrence_counts = Counter()
        for entry_id in term_entries:
            if entry_id in self.entry_keywords:
                for keyword in self.entry_keywords[entry_id]:
                    if keyword != term:
                        cooccurrence_counts[keyword] += 1
        
        # Return most common co-occurring terms
        related_terms = [term for term, count in cooccurrence_counts.most_common(max_terms)]
        return related_terms
    
    def _save_index(self):
        """Save index to storage."""
        try:
            # Convert sets to lists for JSON serialization
            serializable_word_index = {word: list(entries) for word, entries in self.word_index.items()}
            serializable_category_index = {cat: list(entries) for cat, entries in self.category_index.items()}
            serializable_source_index = {src: list(entries) for src, entries in self.source_index.items()}
            serializable_document_index = {doc: list(entries) for doc, entries in self.document_index.items()}
            
            # Save word index
            with open(os.path.join(self.index_storage_path, "word_index.json"), 'w', encoding='utf-8') as f:
                json.dump(serializable_word_index, f, indent=2, ensure_ascii=False)
            
            # Save entry keywords
            with open(os.path.join(self.index_storage_path, "entry_keywords.json"), 'w', encoding='utf-8') as f:
                json.dump(self.entry_keywords, f, indent=2, ensure_ascii=False)
            
            # Save entry metadata
            with open(os.path.join(self.index_storage_path, "entry_metadata.json"), 'w', encoding='utf-8') as f:
                json.dump(self.entry_metadata, f, indent=2, ensure_ascii=False)
            
            # Save category index
            with open(os.path.join(self.index_storage_path, "category_index.json"), 'w', encoding='utf-8') as f:
                json.dump(serializable_category_index, f, indent=2, ensure_ascii=False)
            
            # Save source index
            with open(os.path.join(self.index_storage_path, "source_index.json"), 'w', encoding='utf-8') as f:
                json.dump(serializable_source_index, f, indent=2, ensure_ascii=False)
            
            # Save document index
            with open(os.path.join(self.index_storage_path, "document_index.json"), 'w', encoding='utf-8') as f:
                json.dump(serializable_document_index, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Index saved to {self.index_storage_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _load_index(self) -> bool:
        """
        Load index from storage.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Load word index
            word_index_path = os.path.join(self.index_storage_path, "word_index.json")
            if os.path.exists(word_index_path):
                with open(word_index_path, 'r', encoding='utf-8') as f:
                    word_index_data = json.load(f)
                self.word_index = {word: set(entries) for word, entries in word_index_data.items()}
            
            # Load entry keywords
            keywords_path = os.path.join(self.index_storage_path, "entry_keywords.json")
            if os.path.exists(keywords_path):
                with open(keywords_path, 'r', encoding='utf-8') as f:
                    self.entry_keywords = json.load(f)
            
            # Load entry metadata
            metadata_path = os.path.join(self.index_storage_path, "entry_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.entry_metadata = json.load(f)
            
            # Load category index
            category_path = os.path.join(self.index_storage_path, "category_index.json")
            if os.path.exists(category_path):
                with open(category_path, 'r', encoding='utf-8') as f:
                    category_data = json.load(f)
                self.category_index = {cat: set(entries) for cat, entries in category_data.items()}
            
            # Load source index
            source_path = os.path.join(self.index_storage_path, "source_index.json")
            if os.path.exists(source_path):
                with open(source_path, 'r', encoding='utf-8') as f:
                    source_data = json.load(f)
                self.source_index = {src: set(entries) for src, entries in source_data.items()}
            
            # Load document index
            document_path = os.path.join(self.index_storage_path, "document_index.json")
            if os.path.exists(document_path):
                with open(document_path, 'r', encoding='utf-8') as f:
                    document_data = json.load(f)
                self.document_index = {doc: set(entries) for doc, entries in document_data.items()}
            
            logger.info("Index loaded from storage")
            return True
            
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            return False
    
    def update_index(self, new_entries: List[KnowledgeEntry]):
        """
        Update index with new entries.
        
        Args:
            new_entries: List of new knowledge entries
        """
        for entry in new_entries:
            self._index_entry(entry)
        
        self._save_index()
        logger.info(f"Index updated with {len(new_entries)} new entries")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "total_entries": len(self.entry_metadata),
            "unique_words": len(self.word_index),
            "categories": list(self.category_index.keys()),
            "source_types": list(self.source_index.keys()),
            "documents": list(self.document_index.keys()),
            "avg_keywords_per_entry": sum(len(keywords) for keywords in self.entry_keywords.values()) / max(1, len(self.entry_keywords))
        }

# Example usage and testing
def test_knowledge_indexer():
    """Test the knowledge indexer."""
    print("Testing Knowledge Indexer")
    print("=" * 50)
    
    # Initialize knowledge base and indexer
    kb = UnifiedKnowledgeBase()
    kb.load_all_knowledge()
    
    indexer = KnowledgeIndexer(kb)
    indexer.build_index()
    
    # Get index statistics
    stats = indexer.get_index_stats()
    print("Index Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test search functionality
    test_queries = [
        "appointment booking",
        "cancellation policy",
        "privacy policy",
        "customer support",
        "healthcare services"
    ]
    
    print("\nSearch Results:")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = indexer.search(query, max_results=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result.source_type}] {result.title}")
                print(f"     Score: {result.relevance_score:.3f}")
                print(f"     Category: {result.category}")
                print(f"     Snippet: {result.snippet[:100]}...")
                print(f"     Matched terms: {result.matched_terms}")
        else:
            print("  No results found")
    
    # Test suggestions
    print("\nSearch Suggestions:")
    partial_queries = ["app", "pol", "can"]
    for partial in partial_queries:
        suggestions = indexer.get_suggestions(partial)
        print(f"  '{partial}' -> {suggestions[:5]}")
    
    # Test related terms
    print("\nRelated Terms:")
    terms = ["appointment", "policy", "service"]
    for term in terms:
        related = indexer.get_related_terms(term)
        print(f"  '{term}' -> {related[:5]}")

if __name__ == "__main__":
    test_knowledge_indexer()