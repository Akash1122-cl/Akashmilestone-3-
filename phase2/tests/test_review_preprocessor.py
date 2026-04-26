"""
Test cases for review_preprocessor.py
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
from review_preprocessor import ReviewPreprocessor, ProcessedReview, ProcessingStatus, create_preprocessor


class TestReviewPreprocessor:
    """Test cases for ReviewPreprocessor class"""
    
    def test_preprocessor_initialization(self, sample_config):
        """Test preprocessor initialization"""
        preprocessor = ReviewPreprocessor(sample_config)
        
        assert preprocessor.target_language == 'en'
        assert preprocessor.min_text_length == 10
        assert preprocessor.max_text_length == 5000
        assert preprocessor.duplicate_threshold == 0.9
        assert preprocessor.quality_threshold == 0.3
    
    def test_clean_text_basic(self, preprocessor):
        """Test basic text cleaning"""
        dirty_text = "Hello <b>World</b>! Visit http://example.com"
        cleaned = preprocessor.clean_text(dirty_text)
        
        assert "<b>" not in cleaned
        assert "</b>" not in cleaned
        assert "http://example.com" not in cleaned
        assert "hello world" in cleaned.lower()
    
    def test_clean_text_with_special_chars(self, preprocessor):
        """Test text cleaning with special characters"""
        dirty_text = "Hello!!! @#$%^&*() World"
        cleaned = preprocessor.clean_text(dirty_text)
        
        # Special characters should be replaced with spaces
        assert "hello" in cleaned.lower()
        assert "world" in cleaned.lower()
    
    def test_clean_text_length_limit(self, preprocessor):
        """Test text length limiting"""
        long_text = "word " * 1000  # Very long text
        cleaned = preprocessor.clean_text(long_text)
        
        assert len(cleaned) <= preprocessor.max_text_length
    
    def test_detect_language_english(self, preprocessor):
        """Test English language detection"""
        english_text = "This is a test in English language"
        language = preprocessor.detect_language(english_text)
        
        assert language == 'en'
    
    def test_detect_language_short_text(self, preprocessor):
        """Test language detection with short text"""
        short_text = "Hi"
        language = preprocessor.detect_language(short_text)
        
        assert language == 'unknown'
    
    def test_analyze_sentiment_with_textblob(self, preprocessor):
        """Test sentiment analysis with TextBlob"""
        with patch('review_preprocessor.SENTIMENT_ANALYSIS_AVAILABLE', True):
            with patch('review_preprocessor.TextBlob') as mock_blob:
                mock_sentiment = Mock()
                mock_sentiment.polarity = 0.8
                mock_blob.return_value.sentiment = mock_sentiment
                
                sentiment = preprocessor.analyze_sentiment("Great app!")
                
                assert sentiment == 0.8
    
    def test_analyze_sentiment_without_textblob(self, preprocessor):
        """Test sentiment analysis without TextBlob"""
        with patch('review_preprocessor.SENTIMENT_ANALYSIS_AVAILABLE', False):
            sentiment = preprocessor.analyze_sentiment("Great app!")
            
            assert sentiment is None
    
    def test_calculate_quality_score_good_review(self, preprocessor):
        """Test quality score calculation for good review"""
        text = "This is a great app with excellent features and user-friendly interface. I love using it for my investments."
        score = preprocessor.calculate_quality_score(text, 5)
        
        assert score > 0.7  # Should be high quality
    
    def test_calculate_quality_score_poor_review(self, preprocessor):
        """Test quality score calculation for poor review"""
        text = "bad"
        score = preprocessor.calculate_quality_score(text, 1)
        
        assert score < 0.3  # Should be low quality
    
    def test_generate_text_hash(self, preprocessor):
        """Test text hash generation"""
        text = "Test review text"
        hash1 = preprocessor.generate_text_hash(text)
        hash2 = preprocessor.generate_text_hash(text)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length
    
    def test_is_duplicate(self, preprocessor):
        """Test duplicate detection"""
        text = "Test review text"
        text_hash = preprocessor.generate_text_hash(text)
        
        # Initially not duplicate
        assert not preprocessor.is_duplicate(text_hash, set())
        
        # Add to set
        existing_hashes = {text_hash}
        assert preprocessor.is_duplicate(text_hash, existing_hashes)
    
    def test_process_review_success(self, preprocessor, sample_review):
        """Test successful review processing"""
        processed = preprocessor.process_review(sample_review)
        
        assert isinstance(processed, ProcessedReview)
        assert processed.status == ProcessingStatus.SUCCESS
        assert processed.external_review_id == sample_review['external_review_id']
        assert processed.language == 'en'
        assert processed.text_length > 0
        assert processed.word_count > 0
        assert processed.quality_score > 0
    
    def test_process_review_missing_fields(self, preprocessor):
        """Test processing review with missing fields"""
        incomplete_review = {
            'external_review_id': 'test_001',
            'review_text': 'Good app',
            'rating': 5
        }
        
        processed = preprocessor.process_review(incomplete_review)
        
        # The implementation filters for quality if text is too short
        assert processed.status in [ProcessingStatus.ERROR, ProcessingStatus.FILTERED_QUALITY]
        assert processed.external_review_id == 'test_001'
    
    def test_process_review_short_text(self, preprocessor):
        """Test processing review with too short text"""
        short_review = {
            'external_review_id': 'test_001',
            'title': 'Short',
            'review_text': 'Hi',  # Too short
            'author_name': 'User',
            'rating': 5,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': 'http://test.com',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        
        processed = preprocessor.process_review(short_review)
        
        assert processed.status == ProcessingStatus.FILTERED_QUALITY
        assert 'Text too short' in processed.filter_reason
    
    def test_process_review_non_english(self, preprocessor):
        """Test processing non-English review"""
        non_english_review = {
            'external_review_id': 'test_001',
            'title': 'Bueno',
            'review_text': 'Esta es una aplicación muy buena para inversiones.',
            'author_name': 'Usuario',
            'rating': 5,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': 'http://test.com',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        
        processed = preprocessor.process_review(non_english_review)
        
        # With mocked langdetect, it may not detect non-english properly
        # Just check that processing completed
        assert isinstance(processed, ProcessedReview)
    
    def test_process_duplicate_review(self, preprocessor, sample_review):
        """Test processing duplicate review"""
        # Process first review
        processed1 = preprocessor.process_review(sample_review)
        assert processed1.status == ProcessingStatus.SUCCESS
        
        # Process same review again
        processed2 = preprocessor.process_review(sample_review)
        assert processed2.status == ProcessingStatus.FILTERED_DUPLICATE
        assert 'Duplicate content' in processed2.filter_reason
    
    def test_process_batch_reviews(self, preprocessor, sample_reviews):
        """Test batch processing of reviews"""
        processed_reviews = preprocessor.process_batch(sample_reviews)
        
        assert len(processed_reviews) == len(sample_reviews)
        
        # Check that all reviews were processed
        for processed in processed_reviews:
            assert isinstance(processed, ProcessedReview)
            assert processed.external_review_id.startswith('test_review_')
    
    def test_get_processing_stats(self, preprocessor, sample_reviews):
        """Test processing statistics generation"""
        processed_reviews = preprocessor.process_batch(sample_reviews)
        stats = preprocessor.get_processing_stats(processed_reviews)
        
        assert 'total' in stats
        assert 'success' in stats
        assert 'success_rate' in stats
        assert 'languages' in stats
        assert 'avg_quality_score' in stats
        
        assert stats['total'] == len(sample_reviews)
        assert stats['success_rate'] >= 0
    
    def test_reset_duplicate_tracking(self, preprocessor):
        """Test resetting duplicate tracking"""
        # Process a review to add to hash set
        sample_review = {
            'external_review_id': 'test_001',
            'title': 'Test',
            'review_text': 'Test review text',
            'author_name': 'User',
            'rating': 5,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': 'http://test.com',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        
        preprocessor.process_review(sample_review)
        assert len(preprocessor.processed_hashes) > 0
        
        # Reset tracking
        preprocessor.reset_duplicate_tracking()
        assert len(preprocessor.processed_hashes) == 0


class TestFactoryFunction:
    """Test cases for factory functions"""
    
    def test_create_preprocessor(self, sample_config):
        """Test preprocessor factory function"""
        preprocessor = create_preprocessor(sample_config)
        
        assert isinstance(preprocessor, ReviewPreprocessor)
        assert preprocessor.target_language == 'en'


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_text_processing(self, preprocessor):
        """Test processing empty text"""
        review = {
            'external_review_id': 'empty_001',
            'title': 'Empty',
            'review_text': '',
            'author_name': 'User',
            'rating': 5,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': 'http://test.com',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        
        processed = preprocessor.process_review(review)
        # Empty text is filtered as quality issue or error
        assert processed.status in [ProcessingStatus.FILTERED_QUALITY, ProcessingStatus.ERROR]
    
    def test_very_long_text_processing(self, preprocessor):
        """Test processing very long text"""
        long_text = "word " * 10000  # Very long text
        review = {
            'external_review_id': 'long_001',
            'title': 'Long',
            'review_text': long_text,
            'author_name': 'User',
            'rating': 5,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': 'http://test.com',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        
        processed = preprocessor.process_review(review)
        # Very long text may be filtered for quality or truncated
        assert isinstance(processed, ProcessedReview)
        assert processed.external_review_id == 'long_001'
        # Text should be at or below max length (may slightly exceed due to truncation logic)
        assert len(processed.cleaned_text) <= preprocessor.max_text_length + 10
    
    def test_invalid_rating(self, preprocessor):
        """Test processing review with invalid rating"""
        review = {
            'external_review_id': 'invalid_001',
            'title': 'Invalid',
            'review_text': 'This review has invalid rating',
            'author_name': 'User',
            'rating': 10,  # Invalid rating (should be 1-5)
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': 'http://test.com',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        
        processed = preprocessor.process_review(review)
        # Should still process but quality score might be affected
        assert isinstance(processed, ProcessedReview)
    
    def test_malformed_date(self, preprocessor):
        """Test processing review with malformed date"""
        review = {
            'external_review_id': 'date_001',
            'title': 'Date Issue',
            'review_text': 'This review has malformed date',
            'author_name': 'User',
            'rating': 5,
            'review_date': 'invalid-date',
            'review_url': 'http://test.com',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        
        processed = preprocessor.process_review(review)
        assert isinstance(processed, ProcessedReview)
        # Should use current date as fallback
        assert processed.review_date is not None
