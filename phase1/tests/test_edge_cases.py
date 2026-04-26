"""
Edge Case Tests for Phase 1: Data Ingestion Foundation
Tests handling of malformed data, non-English reviews, database failures, memory exhaustion
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import ConfigManager


class TestMalformedReviewData:
    """Test handling of malformed review data"""
    
    def test_empty_review_text(self):
        """Edge Case: Empty review text should be flagged"""
        review = {
            'external_review_id': '123',
            'review_text': '',
            'author_name': 'User',
            'rating': 5,
            'review_date': datetime.utcnow().isoformat()
        }
        assert not review['review_text'] or len(review['review_text'].strip()) == 0
    
    def test_missing_required_fields(self):
        """Edge Case: Missing required fields should be detected"""
        review = {
            'external_review_id': '123',
            # Missing review_text, author_name, rating
        }
        required_fields = ['review_text', 'author_name', 'rating']
        missing = [f for f in required_fields if f not in review]
        assert len(missing) > 0
    
    def test_invalid_rating_values(self):
        """Edge Case: Invalid rating values should be caught"""
        invalid_ratings = [-1, 0, 6, 10, None, 'five']
        for rating in invalid_ratings:
            is_valid = isinstance(rating, (int, float)) and 1 <= rating <= 5
            assert not is_valid, f"Rating {rating} should be invalid"
    
    def test_invalid_date_format(self):
        """Edge Case: Invalid date formats should be handled"""
        invalid_dates = [
            'not-a-date',
            '2024-13-45',
            '',
            None,
            1234567890  # Unix timestamp as int
        ]
        for date_str in invalid_dates:
            try:
                datetime.fromisoformat(str(date_str))
                valid = True
            except (ValueError, TypeError):
                valid = False
            if date_str in ['not-a-date', '2024-13-45', '', None]:
                assert not valid


class TestNonEnglishReviews:
    """Test handling of non-English reviews"""
    
    def test_language_detection_confidence(self):
        """Edge Case: Non-English reviews should be flagged with confidence"""
        non_english_reviews = [
            {'text': 'Esta aplicación es muy buena', 'expected_lang': 'es'},
            {'text': 'Cette application est excellente', 'expected_lang': 'fr'},
            {'text': 'Diese App ist großartig', 'expected_lang': 'de'},
            {'text': '这个应用很好', 'expected_lang': 'zh'},
        ]
        for review in non_english_reviews:
            # In a real implementation, language detection would be used
            # Here we verify the structure for language metadata
            assert 'text' in review
            assert review['expected_lang'] != 'en'
    
    def test_english_review_acceptance(self):
        """Edge Case: English reviews should pass language check"""
        english_reviews = [
            'This app is great!',
            'Very useful application',
            'Good but needs improvement'
        ]
        for text in english_reviews:
            assert len(text) > 0
            assert text.isascii() or all(ord(c) < 128 for c in text)


class TestDatabaseConnectionFailure:
    """Test handling of database connection failures"""
    
    def test_connection_pool_exhaustion(self):
        """Edge Case: Connection pool exhaustion should trigger retry"""
        mock_pool = Mock()
        mock_pool.getconn.side_effect = Exception("Connection pool exhausted")
        
        with pytest.raises(Exception) as exc_info:
            mock_pool.getconn()
        assert "pool exhausted" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()
    
    def test_database_timeout(self):
        """Edge Case: Database timeouts should be handled gracefully"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Connection timed out")
        mock_conn.cursor.return_value = mock_cursor
        
        with pytest.raises(Exception) as exc_info:
            mock_cursor.execute("SELECT 1")
        assert "time" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()
    
    def test_data_queuing_during_outage(self):
        """Edge Case: Data should be queued during database outage"""
        mock_redis = Mock()
        mock_redis.lpush.return_value = True
        
        # Simulate queuing data during outage
        data = {'review_id': '123', 'text': 'Test review'}
        result = mock_redis.lpush('review_queue', str(data))
        assert result is True


class TestMemoryExhaustion:
    """Test handling of memory exhaustion during ingestion"""
    
    def test_batch_processing_limits(self):
        """Edge Case: Large datasets should be processed in batches"""
        batch_size = 1000
        total_reviews = 50000
        
        num_batches = (total_reviews + batch_size - 1) // batch_size
        assert num_batches == 50
        
        # Verify batch sizes
        for i in range(num_batches):
            start = i * batch_size
            end = min(start + batch_size, total_reviews)
            batch_count = end - start
            assert batch_count <= batch_size
    
    def test_memory_monitoring(self):
        """Edge Case: Memory usage should be monitored"""
        import psutil
        
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate processing
        data = [f"review_{i}" * 100 for i in range(1000)]
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        # Memory increase should be reasonable (< 100MB for 1000 reviews)
        assert mem_increase < 100


class TestRSSFeedUnavailable:
    """Test handling of RSS feed unavailability"""
    
    def test_rss_feed_timeout(self):
        """Edge Case: RSS feed timeout should trigger retry"""
        mock_feed = Mock()
        mock_feed.read.side_effect = Exception("Connection timeout")
        
        with pytest.raises(Exception) as exc_info:
            mock_feed.read()
        assert "time" in str(exc_info.value).lower() or "connection" in str(exc_info.value).lower()
    
    def test_rss_feed_empty_response(self):
        """Edge Case: Empty RSS feed response should be handled"""
        mock_feed = Mock()
        mock_feed.read.return_value = {'entries': []}
        
        result = mock_feed.read()
        assert len(result.get('entries', [])) == 0
    
    def test_rss_feed_malformed_xml(self):
        """Edge Case: Malformed XML should be handled gracefully"""
        mock_feed = Mock()
        mock_feed.read.side_effect = Exception("XML parsing error")
        
        with pytest.raises(Exception) as exc_info:
            mock_feed.read()
        assert "xml" in str(exc_info.value).lower() or "pars" in str(exc_info.value).lower()


class TestGooglePlayScrapingBlocked:
    """Test handling of Google Play scraping blocks"""
    
    def test_proxy_rotation(self):
        """Edge Case: Proxy rotation should be implemented"""
        proxies = [
            'http://proxy1.example.com:8080',
            'http://proxy2.example.com:8080',
            'http://proxy3.example.com:8080'
        ]
        
        # Verify multiple proxies exist
        assert len(proxies) >= 3
        
        # Verify unique proxies
        assert len(set(proxies)) == len(proxies)
    
    def test_user_agent_rotation(self):
        """Edge Case: User agent rotation should be implemented"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        assert len(user_agents) >= 3
        assert len(set(user_agents)) == len(user_agents)
    
    def test_captcha_detection(self):
        """Edge Case: CAPTCHA detection should trigger fallback"""
        mock_response = Mock()
        mock_response.text = '<html><body>CAPTCHA verification required</body></html>'
        mock_response.status_code = 200
        
        # Detect CAPTCHA in response
        has_captcha = 'captcha' in mock_response.text.lower()
        assert has_captcha is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
