"""
Cache Manager for Phase 2
Handles caching strategy for embeddings and processed data
"""

import logging
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import os
import redis
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: datetime
    size_bytes: int
    tags: List[str]


class CacheBackend(ABC):
    """Abstract base class for cache backends"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass


class RedisCacheBackend(CacheBackend):
    """Redis cache backend implementation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 6379)
        self.db = config.get('db', 0)
        self.password = config.get('password')
        self.prefix = config.get('prefix', 'phase2:')
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    def _make_key(self, key: str) -> str:
        """Make full key with prefix"""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self.client:
            return None
        
        try:
            full_key = self._make_key(key)
            data = self.client.get(full_key)
            
            if data:
                # Deserialize
                return pickle.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from Redis: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            data = pickle.dumps(value)
            
            if ttl:
                return self.client.setex(full_key, ttl, data)
            else:
                return self.client.set(full_key, data)
                
        except Exception as e:
            logger.error(f"Error setting to Redis: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Redis"""
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            return bool(self.client.delete(full_key))
            
        except Exception as e:
            logger.error(f"Error deleting from Redis: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        if not self.client:
            return False
        
        try:
            # Delete all keys with prefix
            pattern = f"{self.prefix}*"
            keys = self.client.keys(pattern)
            
            if keys:
                return self.client.delete(*keys)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing Redis: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            full_key = self._make_key(key)
            return bool(self.client.exists(full_key))
            
        except Exception as e:
            logger.error(f"Error checking existence in Redis: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis statistics"""
        if not self.client:
            return {"status": "disconnected"}
        
        try:
            info = self.client.info()
            
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human", "Unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        return (hits / total * 100) if total > 0 else 0.0


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend implementation"""
    
    def __init__(self, config: dict):
        self.max_size = config.get('max_size', 1000)
        self.default_ttl = config.get('default_ttl', 3600)  # 1 hour
        self.cache = {}
        self.access_times = {}
        self.expiry_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        try:
            # Check if key exists
            if key not in self.cache:
                return None
            
            # Check if expired
            if self._is_expired(key):
                self.delete(key)
                return None
            
            # Update access time
            self.access_times[key] = datetime.utcnow()
            
            return self.cache[key]
            
        except Exception as e:
            logger.error(f"Error getting from memory cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        try:
            # Check if cache is full
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            # Store value
            self.cache[key] = value
            self.access_times[key] = datetime.utcnow()
            
            # Set expiry
            if ttl:
                self.expiry_times[key] = datetime.utcnow() + timedelta(seconds=ttl)
            elif self.default_ttl:
                self.expiry_times[key] = datetime.utcnow() + timedelta(seconds=self.default_ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting to memory cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from memory cache"""
        try:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
            self.expiry_times.pop(key, None)
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from memory cache: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            self.cache.clear()
            self.access_times.clear()
            self.expiry_times.clear()
            return True
            
        except Exception as e:
            logger.error(f"Error clearing memory cache: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return key in self.cache and not self._is_expired(key)
            
        except Exception as e:
            logger.error(f"Error checking existence in memory cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics"""
        try:
            return {
                "status": "connected",
                "cache_size": len(self.cache),
                "max_size": self.max_size,
                "utilization": len(self.cache) / self.max_size * 100,
                "expired_keys": len([k for k in self.cache.keys() if self._is_expired(k)])
            }
            
        except Exception as e:
            logger.error(f"Error getting memory cache stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def _is_expired(self, key: str) -> bool:
        """Check if key is expired"""
        if key not in self.expiry_times:
            return False
        
        return datetime.utcnow() > self.expiry_times[key]
    
    def _evict_lru(self):
        """Evict least recently used key"""
        if not self.access_times:
            return
        
        # Find least recently used key
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self.delete(lru_key)


class CacheManager:
    """Main cache manager with multiple backends"""
    
    def __init__(self, config: dict):
        self.config = config.get('cache_manager', {})
        self.default_backend = self.config.get('default_backend', 'memory')
        self.backends = {}
        
        # Initialize backends
        self._initialize_backends()
        
        # Cache statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        logger.info(f"CacheManager initialized with default backend: {self.default_backend}")
    
    def _initialize_backends(self):
        """Initialize cache backends"""
        # Redis backend
        redis_config = self.config.get('redis', {})
        if redis_config.get('enabled', False):
            try:
                self.backends['redis'] = RedisCacheBackend(redis_config)
                logger.info("Redis cache backend initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis backend: {e}")
        
        # Memory backend (always available)
        memory_config = self.config.get('memory', {})
        self.backends['memory'] = MemoryCacheBackend(memory_config)
        logger.info("Memory cache backend initialized")
    
    def get_backend(self, backend_name: Optional[str] = None) -> CacheBackend:
        """Get cache backend"""
        backend_name = backend_name or self.default_backend
        
        if backend_name not in self.backends:
            logger.warning(f"Backend {backend_name} not available, using {self.default_backend}")
            backend_name = self.default_backend
        
        return self.backends[backend_name]
    
    def get(self, key: str, backend: Optional[str] = None) -> Optional[Any]:
        """Get value from cache"""
        self.stats['total_requests'] += 1
        
        cache_backend = self.get_backend(backend)
        value = cache_backend.get(key)
        
        if value is not None:
            self.stats['cache_hits'] += 1
            return value
        else:
            self.stats['cache_misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, backend: Optional[str] = None) -> bool:
        """Set value in cache"""
        self.stats['sets'] += 1
        
        cache_backend = self.get_backend(backend)
        return cache_backend.set(key, value, ttl)
    
    def delete(self, key: str, backend: Optional[str] = None) -> bool:
        """Delete value from cache"""
        self.stats['deletes'] += 1
        
        cache_backend = self.get_backend(backend)
        return cache_backend.delete(key)
    
    def clear(self, backend: Optional[str] = None) -> bool:
        """Clear cache"""
        cache_backend = self.get_backend(backend)
        return cache_backend.clear()
    
    def exists(self, key: str, backend: Optional[str] = None) -> bool:
        """Check if key exists"""
        cache_backend = self.get_backend(backend)
        return cache_backend.exists(key)
    
    def get_embedding(self, text: str, backend: Optional[str] = None) -> Optional[List[float]]:
        """Get cached embedding for text"""
        key = f"embedding:{self._hash_text(text)}"
        return self.get(key, backend)
    
    def set_embedding(self, text: str, embedding: List[float], ttl: Optional[int] = None, backend: Optional[str] = None) -> bool:
        """Cache embedding for text"""
        key = f"embedding:{self._hash_text(text)}"
        return self.set(key, embedding, ttl, backend)
    
    def get_processed_review(self, review_id: str, backend: Optional[str] = None) -> Optional[Dict]:
        """Get cached processed review"""
        key = f"processed_review:{review_id}"
        return self.get(key, backend)
    
    def set_processed_review(self, review_id: str, review_data: Dict, ttl: Optional[int] = None, backend: Optional[str] = None) -> bool:
        """Cache processed review"""
        key = f"processed_review:{review_id}"
        return self.set(key, review_data, ttl, backend)
    
    def get_quality_metrics(self, batch_id: str, backend: Optional[str] = None) -> Optional[Dict]:
        """Get cached quality metrics"""
        key = f"quality_metrics:{batch_id}"
        return self.get(key, backend)
    
    def set_quality_metrics(self, batch_id: str, metrics: Dict, ttl: Optional[int] = None, backend: Optional[str] = None) -> bool:
        """Cache quality metrics"""
        key = f"quality_metrics:{batch_id}"
        return self.set(key, metrics, ttl, backend)
    
    def get_vector_search_result(self, query_hash: str, backend: Optional[str] = None) -> Optional[List]:
        """Get cached vector search result"""
        key = f"vector_search:{query_hash}"
        return self.get(key, backend)
    
    def set_vector_search_result(self, query_hash: str, results: List, ttl: Optional[int] = None, backend: Optional[str] = None) -> bool:
        """Cache vector search result"""
        key = f"vector_search:{query_hash}"
        return self.set(key, results, ttl, backend)
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache manager statistics"""
        stats = self.stats.copy()
        
        # Calculate hit rate
        if stats['total_requests'] > 0:
            stats['hit_rate'] = (stats['cache_hits'] / stats['total_requests']) * 100
        else:
            stats['hit_rate'] = 0.0
        
        # Add backend stats
        stats['backends'] = {}
        for name, backend in self.backends.items():
            try:
                stats['backends'][name] = backend.get_stats()
            except Exception as e:
                stats['backends'][name] = {"status": "error", "error": str(e)}
        
        return stats
    
    def cleanup_expired(self, backend: Optional[str] = None) -> int:
        """Clean up expired entries"""
        cache_backend = self.get_backend(backend)
        
        if isinstance(cache_backend, MemoryCacheBackend):
            # Memory cache cleanup
            expired_keys = [k for k in cache_backend.cache.keys() if cache_backend._is_expired(k)]
            for key in expired_keys:
                cache_backend.delete(key)
            
            return len(expired_keys)
        else:
            # Redis handles expiry automatically
            return 0
    
    def warm_cache(self, data: Dict[str, Any], ttl: Optional[int] = None, backend: Optional[str] = None):
        """Warm cache with data"""
        logger.info(f"Warming cache with {len(data)} entries")
        
        for key, value in data.items():
            self.set(key, value, ttl, backend)
        
        logger.info("Cache warming completed")


# Factory function
def create_cache_manager(config: dict) -> CacheManager:
    """Create CacheManager instance"""
    return CacheManager(config)
