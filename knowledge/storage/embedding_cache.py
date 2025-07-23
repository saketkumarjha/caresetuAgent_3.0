"""
Embedding Cache for efficient vector operations
Provides caching for embeddings to improve performance
"""

import hashlib
import logging
import time
from typing import Dict, List, Any, Optional
import json
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Cache for document embeddings to improve performance."""
    
    def __init__(self, max_size: int = 10000, cache_dir: Optional[str] = None):
        """
        Initialize embedding cache.
        
        Args:
            max_size: Maximum number of embeddings to cache in memory
            cache_dir: Directory to persist cache (None for in-memory only)
        """
        self.cache = {}
        self.max_size = max_size
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.hits = 0
        self.misses = 0
        self.access_times = {}
        
        # Create cache directory if needed
        if self.cache_dir:
            self.cache_dir.mkdir(exist_ok=True)
            self._load_persistent_cache()
    
    def get(self, text: str) -> Optional[List[float]]:
        """
        Get embedding from cache.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            Embedding vector or None if not in cache
        """
        text_hash = self._hash_text(text)
        
        if text_hash in self.cache:
            self.hits += 1
            self.access_times[text_hash] = time.time()
            return self.cache[text_hash]
        
        self.misses += 1
        return None
    
    def set(self, text: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.
        
        Args:
            text: Text to store embedding for
            embedding: Embedding vector
        """
        text_hash = self._hash_text(text)
        self.cache[text_hash] = embedding
        self.access_times[text_hash] = time.time()
        
        # Persist to disk if enabled
        if self.cache_dir:
            self._save_embedding(text_hash, embedding)
        
        # Implement cache eviction if needed
        if len(self.cache) > self.max_size:
            self._evict_lru()
    
    def _hash_text(self, text: str) -> str:
        """Create a hash of the text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _evict_lru(self) -> None:
        """Evict least recently used items from cache."""
        if not self.access_times:
            return
        
        # Find oldest accessed item
        oldest_hash = min(self.access_times.items(), key=lambda x: x[1])[0]
        
        # Remove from cache and access times
        if oldest_hash in self.cache:
            del self.cache[oldest_hash]
        
        if oldest_hash in self.access_times:
            del self.access_times[oldest_hash]
        
        logger.debug(f"Evicted item from cache: {oldest_hash}")
    
    def _save_embedding(self, text_hash: str, embedding: List[float]) -> None:
        """Save embedding to disk."""
        try:
            cache_file = self.cache_dir / f"{text_hash}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "hash": text_hash,
                    "embedding": embedding,
                    "timestamp": time.time()
                }, f)
        except Exception as e:
            logger.error(f"Error saving embedding to disk: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Load cache from disk."""
        if not self.cache_dir.exists():
            return
        
        # Load up to max_size embeddings from disk
        loaded = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            if loaded >= self.max_size:
                break
                
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                text_hash = data["hash"]
                embedding = data["embedding"]
                timestamp = data.get("timestamp", time.time())
                
                self.cache[text_hash] = embedding
                self.access_times[text_hash] = timestamp
                loaded += 1
                
            except Exception as e:
                logger.error(f"Error loading embedding from {cache_file}: {e}")
        
        logger.info(f"Loaded {loaded} embeddings from persistent cache")
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_times.clear()
        
        # Clear persistent cache if enabled
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    os.remove(cache_file)
                except Exception as e:
                    logger.error(f"Error removing cache file {cache_file}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "persistent": self.cache_dir is not None
        }

# Example usage
if __name__ == "__main__":
    # Create cache
    cache = EmbeddingCache(max_size=100, cache_dir="embedding_cache")
    
    # Test cache
    test_text = "This is a test document"
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    # Set embedding
    cache.set(test_text, test_embedding)
    
    # Get embedding
    retrieved = cache.get(test_text)
    print(f"Retrieved embedding: {retrieved}")
    
    # Get stats
    print(f"Cache stats: {cache.get_stats()}")