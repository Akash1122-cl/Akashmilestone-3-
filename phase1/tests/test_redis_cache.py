"""
Test cases for redis_cache.py - Redis caching functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import redis

from src.redis_cache import RedisCache, init_redis_cache, redis_cache


class TestRedisCache:
    """Test cases for RedisCache class"""
    
    def test_redis_cache_initialization(self, redis_manager):
        """Test RedisCache initialization"""
        assert redis_manager.client is not None
        assert redis_manager.host == 'localhost'
        assert redis_manager.port == 6379
        assert redis_manager.db == 1
        assert redis_manager.password is None
    
    @patch('redis.Redis')
    def test_redis_cache_connection_success(self, mock_redis_class):
        """Test successful Redis connection"""
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client
        
        config = {'redis': {
            'host': 'localhost',
            'port': 6379,
            'password': None,
            'db': 1,
            'max_connections': 10
        }}
        
        cache = RedisCache(config)
        assert cache.client == mock_client
        mock_client.ping.assert_called_once()
    
    @patch('redis.Redis')
    def test_redis_cache_connection_failure(self, mock_redis_class):
        """Test Redis connection failure"""
        mock_client = Mock()
        mock_client.ping.side_effect = redis.ConnectionError("Connection failed")
        mock_redis_class.return_value = mock_client
        
        config = {'redis': {
            'host': 'localhost',
            'port': 6379,
            'password': None,
            'db': 1,
            'max_connections': 10
        }}
        
        with pytest.raises(redis.ConnectionError):
            RedisCache(config)
    
    def test_generate_key(self, redis_manager):
        """Test cache key generation"""
        key = redis_manager._generate_key("review", 1, "app_store", "review_123")
        assert key == "review:1:app_store:review_123"
        
        key2 = redis_manager._generate_key("feed", "app_id", 1)
        assert key2 == "feed:app_id:1"
    
    def test_hash_content(self, redis_manager):
        """Test content hashing"""
        content = "test review content"
        hash_val = redis_manager._hash_content(content)
        assert len(hash_val) == 32  # MD5 hash length
        assert isinstance(hash_val, str)
        
        # Same content should produce same hash
        hash_val2 = redis_manager._hash_content(content)
        assert hash_val == hash_val2
        
        # Different content should produce different hash
        hash_val3 = redis_manager._hash_content("different content")
        assert hash_val != hash_val3
    
    def test_set_string_value(self, redis_manager):
        """Test setting a string value in cache"""
        redis_manager.client.set.return_value = True
        
        result = redis_manager.set("test_key", "test_value")
        assert result is True
        redis_manager.client.set.assert_called_once_with("test_key", "test_value")
    
    def test_set_dict_value(self, redis_manager):
        """Test setting a dictionary value in cache"""
        redis_manager.client.set.return_value = True
        
        test_dict = {"key": "value", "number": 123}
        result = redis_manager.set("test_key", test_dict)
        
        assert result is True
        redis_manager.client.set.assert_called_once_with("test_key", json.dumps(test_dict))
    
    def test_set_with_ttl(self, redis_manager):
        """Test setting a value with TTL"""
        redis_manager.client.setex.return_value = True
        
        result = redis_manager.set("test_key", "test_value", ttl=3600)
        assert result is True
        redis_manager.client.setex.assert_called_once_with("test_key", 3600, "test_value")
    
    def test_set_error_handling(self, redis_manager):
        """Test error handling when setting value"""
        redis_manager.client.set.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.set("test_key", "test_value")
        assert result is False
    
    def test_get_string_value(self, redis_manager):
        """Test getting a string value from cache"""
        redis_manager.client.get.return_value = "test_value"
        
        result = redis_manager.get("test_key")
        assert result == "test_value"
        redis_manager.client.get.assert_called_once_with("test_key")
    
    def test_get_json_value(self, redis_manager):
        """Test getting a JSON value from cache"""
        test_dict = {"key": "value", "number": 123}
        redis_manager.client.get.return_value = json.dumps(test_dict)
        
        result = redis_manager.get("test_key")
        assert result == test_dict
    
    def test_get_nonexistent_key(self, redis_manager):
        """Test getting a non-existent key"""
        redis_manager.client.get.return_value = None
        
        result = redis_manager.get("nonexistent_key")
        assert result is None
    
    def test_get_error_handling(self, redis_manager):
        """Test error handling when getting value"""
        redis_manager.client.get.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.get("test_key")
        assert result is None
    
    def test_delete_key(self, redis_manager):
        """Test deleting a key"""
        redis_manager.client.delete.return_value = 1
        
        result = redis_manager.delete("test_key")
        assert result is True
        redis_manager.client.delete.assert_called_once_with("test_key")
    
    def test_delete_nonexistent_key(self, redis_manager):
        """Test deleting a non-existent key"""
        redis_manager.client.delete.return_value = 0
        
        result = redis_manager.delete("nonexistent_key")
        assert result is False
    
    def test_delete_error_handling(self, redis_manager):
        """Test error handling when deleting key"""
        redis_manager.client.delete.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.delete("test_key")
        assert result is False
    
    def test_exists_key(self, redis_manager):
        """Test checking if key exists"""
        redis_manager.client.exists.return_value = 1
        
        result = redis_manager.exists("test_key")
        assert result is True
        redis_manager.client.exists.assert_called_once_with("test_key")
    
    def test_exists_nonexistent_key(self, redis_manager):
        """Test checking if non-existent key exists"""
        redis_manager.client.exists.return_value = 0
        
        result = redis_manager.exists("nonexistent_key")
        assert result is False
    
    def test_exists_error_handling(self, redis_manager):
        """Test error handling when checking key existence"""
        redis_manager.client.exists.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.exists("test_key")
        assert result is False
    
    def test_check_duplicate_review(self, redis_manager):
        """Test checking for duplicate review"""
        redis_manager.client.exists.return_value = 1
        
        result = redis_manager.check_duplicate_review(1, "app_store", "review_123")
        assert result is True
        
        expected_key = "review:1:app_store:review_123"
        redis_manager.client.exists.assert_called_once_with(expected_key)
    
    def test_cache_review(self, redis_manager):
        """Test caching a review"""
        redis_manager.client.setex.return_value = True
        
        result = redis_manager.cache_review(1, "app_store", "review_123")
        assert result is True
        
        expected_key = "review:1:app_store:review_123"
        redis_manager.client.setex.assert_called_once_with(expected_key, 86400, "1")
    
    def test_cache_review_custom_ttl(self, redis_manager):
        """Test caching a review with custom TTL"""
        redis_manager.client.setex.return_value = True
        
        result = redis_manager.cache_review(1, "app_store", "review_123", ttl=7200)
        assert result is True
        
        expected_key = "review:1:app_store:review_123"
        redis_manager.client.setex.assert_called_once_with(expected_key, 7200, "1")
    
    def test_cache_feed_data(self, redis_manager):
        """Test caching feed data"""
        redis_manager.client.setex.return_value = True
        
        test_data = {"reviews": [{"id": 1, "text": "Great app"}]}
        result = redis_manager.cache_feed_data("app_id", 1, test_data)
        
        assert result is True
        expected_key = "feed:app_id:1"
        redis_manager.client.setex.assert_called_once_with(expected_key, 3600, json.dumps(test_data))
    
    def test_get_feed_data(self, redis_manager):
        """Test getting cached feed data"""
        test_data = {"reviews": [{"id": 1, "text": "Great app"}]}
        redis_manager.client.get.return_value = json.dumps(test_data)
        
        result = redis_manager.get_feed_data("app_id", 1)
        assert result == test_data
        
        expected_key = "feed:app_id:1"
        redis_manager.client.get.assert_called_once_with(expected_key)
    
    def test_cache_scrape_data(self, redis_manager):
        """Test caching scraped data"""
        redis_manager.client.setex.return_value = True
        
        test_data = {"reviews": [{"id": 1, "text": "Good app"}]}
        result = redis_manager.cache_scrape_data("com.example.app", test_data)
        
        assert result is True
        expected_key = "scrape:com.example.app"
        redis_manager.client.setex.assert_called_once_with(expected_key, 1800, json.dumps(test_data))
    
    def test_get_scrape_data(self, redis_manager):
        """Test getting cached scraped data"""
        test_data = {"reviews": [{"id": 1, "text": "Good app"}]}
        redis_manager.client.get.return_value = json.dumps(test_data)
        
        result = redis_manager.get_scrape_data("com.example.app")
        assert result == test_data
        
        expected_key = "scrape:com.example.app"
        redis_manager.client.get.assert_called_once_with(expected_key)
    
    def test_increment_counter(self, redis_manager):
        """Test incrementing a counter"""
        redis_manager.client.incr.return_value = 5
        
        result = redis_manager.increment_counter("test_counter", 2)
        assert result == 5
        redis_manager.client.incr.assert_called_once_with("test_counter", 2)
    
    def test_increment_counter_error(self, redis_manager):
        """Test error handling when incrementing counter"""
        redis_manager.client.incr.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.increment_counter("test_counter")
        assert result == 0
    
    def test_get_counter(self, redis_manager):
        """Test getting counter value"""
        redis_manager.client.get.return_value = "10"
        
        result = redis_manager.get_counter("test_counter")
        assert result == 10
        redis_manager.client.get.assert_called_once_with("test_counter")
    
    def test_get_counter_nonexistent(self, redis_manager):
        """Test getting non-existent counter"""
        redis_manager.client.get.return_value = None
        
        result = redis_manager.get_counter("nonexistent_counter")
        assert result == 0
    
    def test_get_counter_error(self, redis_manager):
        """Test error handling when getting counter"""
        redis_manager.client.get.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.get_counter("test_counter")
        assert result == 0
    
    def test_set_counter(self, redis_manager):
        """Test setting counter value"""
        redis_manager.client.set.return_value = True
        
        result = redis_manager.set_counter("test_counter", 15)
        assert result is True
        redis_manager.client.set.assert_called_once_with("test_counter", 15)
    
    def test_set_counter_error(self, redis_manager):
        """Test error handling when setting counter"""
        redis_manager.client.set.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.set_counter("test_counter", 15)
        assert result is False
    
    def test_clear_pattern(self, redis_manager):
        """Test clearing keys matching pattern"""
        redis_manager.client.keys.return_value = ["key1", "key2", "key3"]
        redis_manager.client.delete.return_value = 3
        
        result = redis_manager.clear_pattern("test:*")
        assert result == 3
        redis_manager.client.keys.assert_called_once_with("test:*")
        redis_manager.client.delete.assert_called_once_with("key1", "key2", "key3")
    
    def test_clear_pattern_no_keys(self, redis_manager):
        """Test clearing pattern with no matching keys"""
        redis_manager.client.keys.return_value = []
        
        result = redis_manager.clear_pattern("nonexistent:*")
        assert result == 0
        redis_manager.client.keys.assert_called_once_with("nonexistent:*")
        redis_manager.client.delete.assert_not_called()
    
    def test_clear_pattern_error(self, redis_manager):
        """Test error handling when clearing pattern"""
        redis_manager.client.keys.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.clear_pattern("test:*")
        assert result == 0
    
    def test_get_stats(self, redis_manager):
        """Test getting Redis statistics"""
        redis_manager.client.info.return_value = {
            'connected_clients': 5,
            'used_memory_human': '2.5M',
            'keyspace_hits': 100,
            'keyspace_misses': 10
        }
        redis_manager.client.dbsize.return_value = 50
        
        result = redis_manager.get_stats()
        
        expected = {
            'connected_clients': 5,
            'used_memory_human': '2.5M',
            'total_keys': 50,
            'hits': 100,
            'misses': 10
        }
        assert result == expected
    
    def test_get_stats_error(self, redis_manager):
        """Test error handling when getting stats"""
        redis_manager.client.info.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.get_stats()
        assert result == {}
    
    def test_flush_db(self, redis_manager):
        """Test flushing database"""
        redis_manager.client.flushdb.return_value = True
        
        result = redis_manager.flush_db()
        assert result is True
        redis_manager.client.flushdb.assert_called_once()
    
    def test_flush_db_error(self, redis_manager):
        """Test error handling when flushing database"""
        redis_manager.client.flushdb.side_effect = redis.RedisError("Redis error")
        
        result = redis_manager.flush_db()
        assert result is False
    
    def test_close(self, redis_manager):
        """Test closing Redis connection"""
        redis_manager.client.close.return_value = None
        
        redis_manager.close()
        redis_manager.client.close.assert_called_once()
    
    def test_close_error(self, redis_manager):
        """Test error handling when closing connection"""
        redis_manager.client.close.side_effect = redis.RedisError("Redis error")
        
        # Should not raise an exception
        redis_manager.close()


class TestRedisCacheIntegration:
    """Integration tests for Redis cache functionality"""
    
    def test_review_deduplication_workflow(self, redis_manager):
        """Test complete review deduplication workflow"""
        product_id = 1
        source = "app_store"
        external_id = "review_123"
        
        # Initially no duplicate
        assert not redis_manager.check_duplicate_review(product_id, source, external_id)
        
        # Cache the review
        assert redis_manager.cache_review(product_id, source, external_id)
        
        # Now it should be detected as duplicate
        assert redis_manager.check_duplicate_review(product_id, source, external_id)
        
        # Delete the cached review
        key = redis_manager._generate_key("review", product_id, source, external_id)
        assert redis_manager.delete(key)
        
        # Should no longer be a duplicate
        assert not redis_manager.check_duplicate_review(product_id, source, external_id)
    
    def test_feed_caching_workflow(self, redis_manager):
        """Test complete feed caching workflow"""
        app_id = "123456789"
        page = 1
        feed_data = {
            "reviews": [
                {"id": "1", "text": "Great app!"},
                {"id": "2", "text": "Good app"}
            ]
        }
        
        # Cache feed data
        assert redis_manager.cache_feed_data(app_id, page, feed_data)
        
        # Retrieve cached data
        cached_data = redis_manager.get_feed_data(app_id, page)
        assert cached_data == feed_data
        
        # Clear cached data
        key = redis_manager._generate_key("feed", app_id, page)
        assert redis_manager.delete(key)
        
        # Should return None after deletion
        assert redis_manager.get_feed_data(app_id, page) is None
    
    def test_counter_operations(self, redis_manager):
        """Test counter operations"""
        counter_key = "ingestion_counter"
        
        # Set initial value
        assert redis_manager.set_counter(counter_key, 10)
        
        # Get current value
        assert redis_manager.get_counter(counter_key) == 10
        
        # Increment counter
        assert redis_manager.increment_counter(counter_key, 5) == 15
        
        # Verify new value
        assert redis_manager.get_counter(counter_key) == 15
        
        # Increment by default amount (1)
        assert redis_manager.increment_counter(counter_key) == 16


class TestRedisCacheModule:
    """Test cases for Redis cache module functions"""
    
    @patch('src.redis_cache.RedisCache')
    def test_init_redis_cache(self, mock_redis_cache_class):
        """Test init_redis_cache function"""
        mock_cache = Mock()
        mock_redis_cache_class.return_value = mock_cache
        
        config = {'redis': {'host': 'localhost'}}
        
        result = init_redis_cache(config)
        assert result == mock_cache
        mock_redis_cache_class.assert_called_once_with(config)
    
    @patch('src.redis_cache.redis_cache')
    @patch('src.redis_cache.init_redis_cache')
    def test_init_redis_cache_with_existing_instance(self, mock_init, mock_global_cache):
        """Test init_redis_cache when instance already exists"""
        mock_global_cache.return_value = Mock()
        
        config = {'redis': {'host': 'localhost'}}
        
        result = init_redis_cache(config)
        assert result == mock_global_cache.return_value
        mock_init.assert_not_called()
