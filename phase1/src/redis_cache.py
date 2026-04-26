"""
Redis caching layer for Phase 1
Provides caching for deduplication and performance optimization
"""

import redis
import json
import hashlib
from typing import Optional, Any
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache manager for review deduplication and performance"""
    
    def __init__(self, config: dict):
        self.config = config['redis']
        self.host = self.config['host']
        self.port = self.config['port']
        self.db = self.config['db']
        self.password = self.config.get('password')
        self.max_connections = self.config['max_connections']
        
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password if self.password else None,
            max_connections=self.max_connections,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        try:
            self.client.ping()
            logger.info("Redis connection established successfully")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments"""
        key_parts = [prefix] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    def _hash_content(self, content: str) -> str:
        """Generate hash of content for deduplication"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except redis.RedisError as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except redis.RedisError as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            return bool(self.client.delete(key))
        except redis.RedisError as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        try:
            return bool(self.client.exists(key))
        except redis.RedisError as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def check_duplicate_review(self, product_id: int, source: str, external_id: str) -> bool:
        """Check if a review already exists in cache"""
        key = self._generate_key("review", product_id, source, external_id)
        return self.exists(key)
    
    def cache_review(self, product_id: int, source: str, external_id: str, ttl: int = 86400) -> bool:
        """Cache a review ID for deduplication (default 24 hours)"""
        key = self._generate_key("review", product_id, source, external_id)
        return self.set(key, "1", ttl)
    
    def cache_feed_data(self, app_id: str, page: int, data: dict, ttl: int = 3600) -> bool:
        """Cache RSS feed data (default 1 hour)"""
        key = self._generate_key("feed", app_id, page)
        return self.set(key, data, ttl)
    
    def get_feed_data(self, app_id: str, page: int) -> Optional[dict]:
        """Get cached RSS feed data"""
        key = self._generate_key("feed", app_id, page)
        return self.get(key)
    
    def cache_scrape_data(self, package_name: str, data: dict, ttl: int = 1800) -> bool:
        """Cache scraped data (default 30 minutes)"""
        key = self._generate_key("scrape", package_name)
        return self.set(key, data, ttl)
    
    def get_scrape_data(self, package_name: str) -> Optional[dict]:
        """Get cached scraped data"""
        key = self._generate_key("scrape", package_name)
        return self.get(key)
    
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        try:
            return self.client.incr(key, amount)
        except redis.RedisError as e:
            logger.error(f"Error incrementing counter {key}: {e}")
            return 0
    
    def get_counter(self, key: str) -> int:
        """Get a counter value"""
        try:
            value = self.client.get(key)
            return int(value) if value else 0
        except redis.RedisError as e:
            logger.error(f"Error getting counter {key}: {e}")
            return 0
    
    def set_counter(self, key: str, value: int) -> bool:
        """Set a counter value"""
        try:
            return self.client.set(key, value)
        except redis.RedisError as e:
            logger.error(f"Error setting counter {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Error clearing pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Get Redis statistics"""
        try:
            info = self.client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'total_keys': self.client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0)
            }
        except redis.RedisError as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {}
    
    def flush_db(self) -> bool:
        """Flush the current database (use with caution)"""
        try:
            self.client.flushdb()
            logger.warning("Redis database flushed")
            return True
        except redis.RedisError as e:
            logger.error(f"Error flushing Redis database: {e}")
            return False
    
    def close(self):
        """Close the Redis connection"""
        try:
            self.client.close()
            logger.info("Redis connection closed")
        except redis.RedisError as e:
            logger.error(f"Error closing Redis connection: {e}")


# Global Redis cache instance
redis_cache: Optional[RedisCache] = None


def init_redis_cache(config: dict) -> RedisCache:
    """Initialize the global Redis cache"""
    global redis_cache
    if redis_cache is None:
        redis_cache = RedisCache(config)
    return redis_cache
