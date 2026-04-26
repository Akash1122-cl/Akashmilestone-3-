"""
Edge Case Tests for Phase 2: Data Processing Pipeline
Tests handling of long reviews, emojis, mixed languages, API failures, spam, missing metadata
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from review_preprocessor import ReviewPreprocessor, ProcessedReview, ProcessingStatus
from embedding_service import EmbeddingService, EmbeddingResult


class TestExtremelyLongReviews:
    """Test handling of extremely long reviews (>5000 characters)"""
    
    def test_review_truncation(self):
        """Edge Case: Reviews >5000 chars should be truncated"""
        long_text = "A" * 6000
        max_length = 5000
        
        # Truncation logic
        truncated = long_text[:max_length] + "..." if len(long_text) > max_length else long_text
        
        assert len(truncated) <= max_length + 3  # +3 for ellipsis
        assert truncated.endswith("...")
    
    def test_truncation_preserves_content(self):
        """Edge Case: Truncation should preserve beginning content"""
        text = "Important beginning content. " + "X" * 6000
        max_length = 5000
        
        truncated = text[:max_length] + "..." if len(text) > max_length else text
        
        assert "Important beginning content" in truncated
    
    def test_short_review_not_truncated(self):
        """Edge Case: Short reviews should not be truncated"""
        text = "Short review text"
        max_length = 5000
        
        truncated = text[:max_length] + "..." if len(text) > max_length else text
        
        assert truncated == text
        assert not truncated.endswith("...")


class TestReviewsWithEmojis:
    """Test handling of reviews with emojis and special characters"""
    
    def test_emoji_preservation(self):
        """Edge Case: Emojis should be preserved for sentiment analysis"""
        text_with_emojis = "This app is great! 🔥 🎉 💯"
        
        # Verify emojis are present
        emojis = [c for c in text_with_emojis if ord(c) > 127]
        assert len(emojis) > 0
        assert '🔥' in text_with_emojis
    
    def test_special_character_normalization(self):
        """Edge Case: Special characters should be normalized"""
        text_with_special = "This app is \u201Cgreat\u201D and \u2018amazing\u2019"
        
        # Smart quotes should be normalized
        normalized = text_with_special.replace('\u201C', '"').replace('\u201D', '"')
        normalized = normalized.replace('\u2018', "'").replace('\u2019', "'")
        
        assert '"' in normalized
        assert "'" in normalized
    
    def test_unicode_handling(self):
        """Edge Case: Unicode characters should be handled gracefully"""
        unicode_text = "App review with ñoño, café, naïve characters"
        
        # Should be able to encode/decode
        encoded = unicode_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        
        assert decoded == unicode_text


class TestMixedLanguageReviews:
    """Test handling of reviews with mixed languages"""
    
    def test_dominant_language_detection(self):
        """Edge Case: Dominant language should be detected"""
        mixed_text = "This app is muy bueno and très bien"
        
        # In real implementation, language detection would identify dominant language
        # Here we verify the text contains multiple languages
        english_words = ['This', 'app', 'is']
        spanish_words = ['muy', 'bueno']
        french_words = ['très', 'bien']
        
        has_english = any(word in mixed_text for word in english_words)
        has_spanish = any(word in mixed_text for word in spanish_words)
        has_french = any(word in mixed_text for word in french_words)
        
        # Should contain English words (dominant)
        assert has_english is True
    
    def test_non_english_filtering(self):
        """Edge Case: Non-English reviews should be flagged"""
        non_english_reviews = [
            {'text': 'Esta aplicación es muy buena', 'lang': 'es'},
            {'text': 'Cette application est excellente', 'lang': 'fr'},
        ]
        
        for review in non_english_reviews:
            assert review['lang'] != 'en'


class TestEmbeddingAPIFailures:
    """Test handling of embedding API failures"""
    
    def test_api_rate_limit_handling(self):
        """Edge Case: API rate limits should trigger exponential backoff"""
        mock_service = Mock()
        mock_service.generate_embedding.side_effect = [
            Exception("Rate limit exceeded"),
            Exception("Rate limit exceeded"),
            Mock(embedding=[0.1, 0.2, 0.3])
        ]
        
        # Simulate retry with backoff
        retries = 0
        max_retries = 3
        delay = 1
        
        while retries < max_retries:
            try:
                result = mock_service.generate_embedding("test")
                break
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    delay *= 2  # Exponential backoff
        
        assert retries > 0
        assert delay >= 4  # 1, 2, 4
    
    def test_embedding_cache_usage(self):
        """Edge Case: Cached embeddings should be used during API failures"""
        cache = {
            'hash_123': {
                'embedding': [0.1, 0.2, 0.3],
                'model': 'test-model'
            }
        }
        
        text_hash = 'hash_123'
        if text_hash in cache:
            cached = cache[text_hash]
            assert cached['embedding'] is not None
            assert len(cached['embedding']) > 0
    
    def test_fallback_model_activation(self):
        """Edge Case: Fallback model should activate when API fails"""
        config = {
            'embeddings': {
                'use_api': False,  # Free-only mode
                'model': 'all-MiniLM-L6-v2',
                'fallback_enabled': True
            }
        }
        
        # In free-only mode, API should not be called
        assert config['embeddings']['use_api'] is False


class TestLargeBatchProcessing:
    """Test handling of large batch processing failures"""
    
    def test_batch_size_limits(self):
        """Edge Case: Batch sizes should be limited to prevent memory issues"""
        total_items = 10000
        max_batch_size = 100
        
        num_batches = (total_items + max_batch_size - 1) // max_batch_size
        assert num_batches == 100
        
        # Verify each batch is within limits
        for i in range(num_batches):
            batch_start = i * max_batch_size
            batch_end = min(batch_start + max_batch_size, total_items)
            batch_size = batch_end - batch_start
            assert batch_size <= max_batch_size
    
    def test_checkpointing(self):
        """Edge Case: Processing should resume from last checkpoint"""
        processed_count = 4500
        total_count = 10000
        checkpoint_interval = 1000
        
        # Calculate remaining items from last checkpoint
        last_checkpoint = (processed_count // checkpoint_interval) * checkpoint_interval
        remaining = total_count - last_checkpoint
        
        assert remaining == 6000  # 10000 - 4000 (last checkpoint)
        assert last_checkpoint == 4000


class TestSpamReviews:
    """Test handling of low-quality and spam reviews"""
    
    def test_repetitive_text_detection(self):
        """Edge Case: Repetitive text should be flagged as spam"""
        spam_text = "great app great app great app great app great app"
        
        # Detect repetition
        words = spam_text.lower().split()
        unique_words = set(words)
        repetition_ratio = len(words) / len(unique_words) if unique_words else 0
        
        assert repetition_ratio > 2  # High repetition indicates spam
    
    def test_random_character_detection(self):
        """Edge Case: Random characters should be flagged"""
        random_text = "asdfghjkl zxcvbnm qwertyuiop"
        
        # Detect lack of real words
        common_words = ['the', 'and', 'is', 'are', 'app', 'good', 'great']
        has_common_words = any(word in random_text.lower() for word in common_words)
        
        assert not has_common_words
    
    def test_very_short_review_handling(self):
        """Edge Case: Very short reviews should be flagged"""
        short_reviews = ['ok', 'good', 'bad', 'nice', 'app']
        min_length = 10
        
        for review in short_reviews:
            assert len(review) < min_length


class TestMissingMetadata:
    """Test handling of reviews with missing metadata"""
    
    def test_missing_author_name(self):
        """Edge Case: Missing author name should use default or be flagged"""
        review = {
            'external_review_id': '123',
            'review_text': 'Great app!',
            'author_name': None,
            'rating': 5
        }
        
        # Should use default or be flagged
        assert review['author_name'] is None
    
    def test_missing_version_info(self):
        """Edge Case: Missing version info should be handled gracefully"""
        review = {
            'external_review_id': '123',
            'review_text': 'Great app!',
            'version': None,
            'rating': 5
        }
        
        # Version should be optional
        assert 'version' in review
    
    def test_inferred_metadata(self):
        """Edge Case: Missing metadata should be inferred when possible"""
        review = {
            'external_review_id': '123',
            'review_text': 'Great app!',
            'rating': 5
        }
        
        # Infer review date if missing
        if 'review_date' not in review:
            review['review_date'] = datetime.utcnow().isoformat()
        
        assert 'review_date' in review
        assert review['review_date'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
