"""
Test cases for appstore_ingestor.py - App Store RSS ingestion
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
import feedparser

from src.appstore_ingestor import AppStoreIngestor
from src.database import Review, Product, IngestionLog


class TestAppStoreIngestor:
    """Test cases for AppStoreIngestor class"""
    
    def test_appstore_ingestor_initialization(self, config_manager):
        """Test AppStoreIngestor initialization"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        assert ingestor.config == config['app_store']
        assert 'rss_feed_url_template' in ingestor.config
        assert 'max_pages' in ingestor.config
        assert 'reviews_per_page' in ingestor.config
        assert 'request_timeout' in ingestor.config
        assert 'retry_attempts' in ingestor.config
        assert 'retry_delay' in ingestor.config
    
    @patch('src.appstore_ingestor.requests.get')
    @patch('src.appstore_ingestor.feedparser.parse')
    def test_fetch_reviews_success(self, mock_feedparser, mock_requests, config_manager):
        """Test successful review fetching"""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b'test rss content'
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Setup mock feed
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                id='https://example.com/review/1',
                title='Great app',
                content=[{'value': 'Very user friendly'}],
                author='John Doe',
                updated='2024-01-15T10:30:00Z',
                link='https://example.com/review/1',
                im_rating=5,
                im_version='1.2.3'
            )
        ]
        mock_feedparser.return_value = mock_feed
        
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        reviews = ingestor.fetch_reviews('123456789', days_back=30)
        
        assert len(reviews) == 1
        assert reviews[0]['external_review_id'] == '1'
        assert reviews[0]['title'] == 'Great app'
        assert reviews[0]['review_text'] == 'Very user friendly'
        assert reviews[0]['author_name'] == 'John Doe'
        assert reviews[0]['rating'] == 5
        assert reviews[0]['version'] == '1.2.3'
    
    @patch('src.appstore_ingestor.requests.get')
    def test_fetch_reviews_request_failure(self, mock_requests, config_manager):
        """Test review fetching with request failure"""
        mock_requests.side_effect = requests.exceptions.RequestException("Network error")
        
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        reviews = ingestor.fetch_reviews('123456789')
        
        assert reviews == []
    
    @patch('src.appstore_ingestor.requests.get')
    @patch('src.appstore_ingestor.feedparser.parse')
    def test_fetch_reviews_retry_success(self, mock_feedparser, mock_requests, config_manager):
        """Test review fetching with retry success"""
        # Setup mock response that fails then succeeds
        mock_response = Mock()
        mock_response.content = b'test rss content'
        mock_response.raise_for_status.return_value = None
        
        mock_requests.side_effect = [
            requests.exceptions.RequestException("Network error"),
            mock_response
        ]
        
        # Setup mock feed
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feedparser.return_value = mock_feed
        
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        reviews = ingestor.fetch_reviews('123456789')
        
        # Should have made 2 attempts (1 failure + 1 success)
        assert mock_requests.call_count == 2
    
    @patch('src.appstore_ingestor.requests.get')
    @patch('src.appstore_ingestor.feedparser.parse')
    def test_fetch_reviews_no_entries(self, mock_feedparser, mock_requests, config_manager):
        """Test review fetching when no entries found"""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b'test rss content'
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Setup mock feed with no entries
        mock_feed = Mock()
        mock_feed.entries = []
        mock_feedparser.return_value = mock_feed
        
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        reviews = ingestor.fetch_reviews('123456789')
        
        assert reviews == []
    
    @patch('src.appstore_ingestor.requests.get')
    @patch('src.appstore_ingestor.feedparser.parse')
    def test_fetch_reviews_cutoff_date(self, mock_feedparser, mock_requests, config_manager):
        """Test review fetching with cutoff date"""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = b'test rss content'
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Setup mock feed with old review
        old_date = (datetime.utcnow() - timedelta(days=100)).strftime('%Y-%m-%dT%H:%M:%SZ')
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                id='https://example.com/review/1',
                title='Old review',
                content=[{'value': 'Old content'}],
                author='John Doe',
                updated=old_date,
                link='https://example.com/review/1',
                im_rating=3,
                im_version='1.0.0'
            )
        ]
        mock_feedparser.return_value = mock_feed
        
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        reviews = ingestor.fetch_reviews('123456789', days_back=30)
        
        assert reviews == []  # Should be filtered out by cutoff date
    
    def test_parse_feed_success(self, config_manager):
        """Test successful feed parsing"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        # Create mock feed entries
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                id='https://example.com/review/1',
                title='Great app',
                content=[{'value': 'Very user friendly'}],
                author='John Doe',
                updated='2024-01-15T10:30:00Z',
                link='https://example.com/review/1',
                im_rating=5,
                im_version='1.2.3'
            ),
            Mock(
                id='https://example.com/review/2',
                title='Good app',
                content=[{'value': 'Pretty good'}],
                author='Jane Smith',
                updated='2024-01-14T15:45:00Z',
                link='https://example.com/review/2',
                im_rating=4,
                im_version='1.2.2'
            )
        ]
        
        reviews = ingestor._parse_feed(mock_feed, cutoff_date)
        
        assert len(reviews) == 2
        
        # Check first review
        assert reviews[0]['external_review_id'] == '1'
        assert reviews[0]['title'] == 'Great app'
        assert reviews[0]['review_text'] == 'Very user friendly'
        assert reviews[0]['author_name'] == 'John Doe'
        assert reviews[0]['rating'] == 5
        assert reviews[0]['version'] == '1.2.3'
        assert reviews[0]['review_url'] == 'https://example.com/review/1'
        
        # Check second review
        assert reviews[1]['external_review_id'] == '2'
        assert reviews[1]['title'] == 'Good app'
        assert reviews[1]['review_text'] == 'Pretty good'
        assert reviews[1]['author_name'] == 'Jane Smith'
        assert reviews[1]['rating'] == 4
        assert reviews[1]['version'] == '1.2.2'
    
    def test_parse_feed_old_review_filtered(self, config_manager):
        """Test feed parsing with old review filtered out"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        # Create mock feed with old entry
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_date = (datetime.utcnow() - timedelta(days=100)).strftime('%Y-%m-%dT%H:%M:%SZ')
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                id='https://example.com/review/1',
                title='Old review',
                content=[{'value': 'Old content'}],
                author='John Doe',
                updated=old_date,
                link='https://example.com/review/1',
                im_rating=3,
                im_version='1.0.0'
            )
        ]
        
        reviews = ingestor._parse_feed(mock_feed, cutoff_date)
        
        assert len(reviews) == 0  # Should be filtered out
    
    def test_parse_feed_parse_error_handling(self, config_manager):
        """Test feed parsing with entry parsing errors"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        mock_feed = Mock()
        mock_feed.entries = [
            Mock(
                id='https://example.com/review/1',
                title='Good review',
                content=[{'value': 'Good content'}],
                author='John Doe',
                updated='2024-01-15T10:30:00Z',
                link='https://example.com/review/1',
                im_rating=5,
                im_version='1.2.3'
            ),
            Mock(side_effect=Exception("Parse error"))  # This will cause an error
        ]
        
        reviews = ingestor._parse_feed(mock_feed, cutoff_date)
        
        # Should still parse the good review despite the error
        assert len(reviews) == 1
        assert reviews[0]['external_review_id'] == '1'
    
    def test_extract_rating_success(self, config_manager):
        """Test successful rating extraction"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        entry = {'im_rating': '5'}
        rating = ingestor._extract_rating(entry)
        assert rating == 5
    
    def test_extract_rating_missing(self, config_manager):
        """Test rating extraction when rating is missing"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        entry = {}
        rating = ingestor._extract_rating(entry)
        assert rating is None
    
    def test_extract_rating_invalid(self, config_manager):
        """Test rating extraction with invalid rating"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        entry = {'im_rating': 'invalid'}
        rating = ingestor._extract_rating(entry)
        assert rating is None
    
    def test_parse_date_rss_format(self, config_manager):
        """Test date parsing with RSS format"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        date_str = 'Mon, 15 Jan 2024 10:30:00 +0000'
        parsed_date = ingestor._parse_date(date_str)
        
        assert parsed_date is not None
        assert parsed_date.year == 2024
        assert parsed_date.month == 1
        assert parsed_date.day == 15
        assert parsed_date.hour == 10
        assert parsed_date.minute == 30
    
    def test_parse_date_iso_format(self, config_manager):
        """Test date parsing with ISO format"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        date_str = '2024-01-15T10:30:00Z'
        parsed_date = ingestor._parse_date(date_str)
        
        assert parsed_date is not None
        assert parsed_date.year == 2024
        assert parsed_date.month == 1
        assert parsed_date.day == 15
        assert parsed_date.hour == 10
        assert parsed_date.minute == 30
    
    def test_parse_date_invalid(self, config_manager):
        """Test date parsing with invalid date"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        date_str = 'invalid date'
        parsed_date = ingestor._parse_date(date_str)
        assert parsed_date is None
    
    def test_parse_date_none(self, config_manager):
        """Test date parsing with None"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        parsed_date = ingestor._parse_date(None)
        assert parsed_date is None
    
    def test_extract_version_success(self, config_manager):
        """Test successful version extraction"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        entry = {'im_version': '1.2.3'}
        version = ingestor._extract_version(entry)
        assert version == '1.2.3'
    
    def test_extract_version_missing(self, config_manager):
        """Test version extraction when version is missing"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        entry = {}
        version = ingestor._extract_version(entry)
        assert version is None
    
    def test_save_reviews_new_reviews(self, config_manager, test_db_session, sample_product):
        """Test saving new reviews to database"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        reviews = [
            {
                'external_review_id': 'review_1',
                'title': 'Great app',
                'review_text': 'Very user friendly',
                'author_name': 'John Doe',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://example.com/review/1',
                'version': '1.2.3'
            },
            {
                'external_review_id': 'review_2',
                'title': 'Good app',
                'review_text': 'Pretty good',
                'author_name': 'Jane Smith',
                'rating': 4,
                'review_date': datetime.utcnow(),
                'review_url': 'https://example.com/review/2',
                'version': '1.2.2'
            }
        ]
        
        saved_count = ingestor.save_reviews(reviews, sample_product.id, test_db_session)
        
        assert saved_count == 2
        
        # Verify reviews were saved
        saved_reviews = test_db_session.query(Review).filter(
            Review.product_id == sample_product.id,
            Review.source == 'app_store'
        ).all()
        
        assert len(saved_reviews) == 2
        assert saved_reviews[0].external_review_id == 'review_1'
        assert saved_reviews[1].external_review_id == 'review_2'
    
    def test_save_reviews_duplicates_skipped(self, config_manager, test_db_session, sample_product):
        """Test that duplicate reviews are skipped"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        # Create an existing review
        existing_review = Review(
            product_id=sample_product.id,
            source='app_store',
            external_review_id='review_1',
            review_text='Existing review',
            rating=5,
            review_date=datetime.utcnow()
        )
        test_db_session.add(existing_review)
        test_db_session.commit()
        
        reviews = [
            {
                'external_review_id': 'review_1',  # Duplicate
                'title': 'Updated title',
                'review_text': 'Updated text',
                'author_name': 'John Doe',
                'rating': 4,
                'review_date': datetime.utcnow(),
                'review_url': 'https://example.com/review/1',
                'version': '1.2.3'
            },
            {
                'external_review_id': 'review_2',  # New
                'title': 'New review',
                'review_text': 'New text',
                'author_name': 'Jane Smith',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://example.com/review/2',
                'version': '1.2.3'
            }
        ]
        
        saved_count = ingestor.save_reviews(reviews, sample_product.id, test_db_session)
        
        assert saved_count == 1  # Only the new review should be saved
        
        # Verify only one new review was saved
        saved_reviews = test_db_session.query(Review).filter(
            Review.product_id == sample_product.id,
            Review.source == 'app_store'
        ).all()
        
        assert len(saved_reviews) == 2  # 1 existing + 1 new
        assert saved_reviews[0].external_review_id == 'review_1'
        assert saved_reviews[1].external_review_id == 'review_2'
    
    def test_save_reviews_error_handling(self, config_manager, test_db_session, sample_product):
        """Test error handling when saving reviews"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        reviews = [
            {
                'external_review_id': 'review_1',
                'title': 'Great app',
                'review_text': 'Very user friendly',
                'author_name': 'John Doe',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://example.com/review/1',
                'version': '1.2.3'
            }
        ]
        
        # Mock database session to raise an exception
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")
        
        saved_count = ingestor.save_reviews(reviews, sample_product.id, mock_session)
        
        assert saved_count == 0
    
    @patch('src.appstore_ingestor.AppStoreIngestor.fetch_reviews')
    @patch('src.appstore_ingestor.AppStoreIngestor.save_reviews')
    def test_ingest_product_success(self, mock_save_reviews, mock_fetch_reviews, 
                                   config_manager, test_db_session, sample_product):
        """Test successful product ingestion"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        # Setup mocks
        mock_reviews = [
            {
                'external_review_id': 'review_1',
                'title': 'Great app',
                'review_text': 'Very user friendly',
                'author_name': 'John Doe',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://example.com/review/1',
                'version': '1.2.3'
            }
        ]
        mock_fetch_reviews.return_value = mock_reviews
        mock_save_reviews.return_value = 1
        
        log = ingestor.ingest_product(sample_product, test_db_session)
        
        assert log.status == 'success'
        assert log.product_id == sample_product.id
        assert log.source == 'app_store'
        assert log.reviews_collected == 1
        assert log.reviews_processed == 1
        assert log.error_message is None
        assert log.completed_at is not None
        assert log.duration_seconds is not None
        
        mock_fetch_reviews.assert_called_once_with(sample_product.app_store_id)
        mock_save_reviews.assert_called_once()
    
    @patch('src.appstore_ingestor.AppStoreIngestor.fetch_reviews')
    def test_ingest_product_failure(self, mock_fetch_reviews, config_manager, test_db_session, sample_product):
        """Test product ingestion failure"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        # Setup mock to raise exception
        mock_fetch_reviews.side_effect = Exception("Fetch error")
        
        log = ingestor.ingest_product(sample_product, test_db_session)
        
        assert log.status == 'failed'
        assert log.product_id == sample_product.id
        assert log.source == 'app_store'
        assert log.error_message == 'Fetch error'
        assert log.completed_at is not None
        assert log.duration_seconds is not None


class TestAppStoreIngestorIntegration:
    """Integration tests for AppStoreIngestor"""
    
    def test_full_ingestion_workflow(self, config_manager, test_db_session, sample_product):
        """Test complete ingestion workflow"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        # Mock the actual fetching to avoid network calls
        with patch.object(ingestor, 'fetch_reviews') as mock_fetch:
            mock_reviews = [
                {
                    'external_review_id': 'review_1',
                    'title': 'Great app',
                    'review_text': 'Very user friendly',
                    'author_name': 'John Doe',
                    'rating': 5,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://example.com/review/1',
                    'version': '1.2.3'
                },
                {
                    'external_review_id': 'review_2',
                    'title': 'Good app',
                    'review_text': 'Pretty good',
                    'author_name': 'Jane Smith',
                    'rating': 4,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://example.com/review/2',
                    'version': '1.2.2'
                }
            ]
            mock_fetch.return_value = mock_reviews
            
            # Run ingestion
            log = ingestor.ingest_product(sample_product, test_db_session)
            
            # Verify ingestion log
            assert log.status == 'success'
            assert log.reviews_collected == 2
            assert log.reviews_processed == 2
            
            # Verify reviews were saved
            saved_reviews = test_db_session.query(Review).filter(
                Review.product_id == sample_product.id,
                Review.source == 'app_store'
            ).all()
            
            assert len(saved_reviews) == 2
            assert saved_reviews[0].external_review_id == 'review_1'
            assert saved_reviews[1].external_review_id == 'review_2'
            
            # Verify ingestion log was saved
            ingestion_logs = test_db_session.query(IngestionLog).filter(
                IngestionLog.product_id == sample_product.id,
                IngestionLog.source == 'app_store'
            ).all()
            
            assert len(ingestion_logs) == 1
            assert ingestion_logs[0].status == 'success'
    
    def test_duplicate_prevention_across_ingestions(self, config_manager, test_db_session, sample_product):
        """Test that duplicates are prevented across multiple ingestions"""
        config = config_manager.config
        ingestor = AppStoreIngestor(config)
        
        # First ingestion
        with patch.object(ingestor, 'fetch_reviews') as mock_fetch:
            mock_reviews = [
                {
                    'external_review_id': 'review_1',
                    'title': 'Great app',
                    'review_text': 'Very user friendly',
                    'author_name': 'John Doe',
                    'rating': 5,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://example.com/review/1',
                    'version': '1.2.3'
                }
            ]
            mock_fetch.return_value = mock_reviews
            
            log1 = ingestor.ingest_product(sample_product, test_db_session)
            assert log1.reviews_processed == 1
        
        # Second ingestion with same reviews
        with patch.object(ingestor, 'fetch_reviews') as mock_fetch:
            mock_reviews = [
                {
                    'external_review_id': 'review_1',  # Same as before
                    'title': 'Updated title',
                    'review_text': 'Updated text',
                    'author_name': 'John Doe',
                    'rating': 4,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://example.com/review/1',
                    'version': '1.2.4'
                },
                {
                    'external_review_id': 'review_2',  # New review
                    'title': 'New review',
                    'review_text': 'New text',
                    'author_name': 'Jane Smith',
                    'rating': 5,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://example.com/review/2',
                    'version': '1.2.4'
                }
            ]
            mock_fetch.return_value = mock_reviews
            
            log2 = ingestor.ingest_product(sample_product, test_db_session)
            assert log2.reviews_collected == 2
            assert log2.reviews_processed == 1  # Only the new review should be processed
        
        # Verify final state
        all_reviews = test_db_session.query(Review).filter(
            Review.product_id == sample_product.id,
            Review.source == 'app_store'
        ).all()
        
        assert len(all_reviews) == 2  # review_1 + review_2
