"""
Test cases for googleplay_ingestor.py - Google Play scraping
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

from src.googleplay_ingestor import GooglePlayIngestor
from src.database import Review, Product, IngestionLog


class TestGooglePlayIngestor:
    """Test cases for GooglePlayIngestor class"""
    
    def test_googleplay_ingestor_initialization(self, config_manager):
        """Test GooglePlayIngestor initialization"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        assert ingestor.config == config['google_play']
        assert 'max_reviews' in ingestor.config
        assert 'request_timeout' in ingestor.config
        assert 'retry_attempts' in ingestor.config
        assert 'retry_delay' in ingestor.config
        assert 'proxy_rotation' in ingestor.config
        assert 'user_agents' in ingestor.config
    
    def test_get_session(self, config_manager):
        """Test creating a requests session"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        session = ingestor._get_session()
        
        assert isinstance(session, requests.Session)
        assert 'User-Agent' in session.headers
        assert 'Accept' in session.headers
        assert 'Accept-Language' in session.headers
        assert 'Accept-Encoding' in session.headers
        assert 'Connection' in session.headers
    
    def test_get_proxy_with_rotation(self, config_manager):
        """Test getting a proxy when rotation is enabled"""
        config = config_manager.config
        config['google_play']['proxy_rotation'] = True
        config['google_play']['proxy_list'] = ['http://proxy1:8080', 'http://proxy2:8080']
        
        ingestor = GooglePlayIngestor(config)
        
        proxy = ingestor._get_proxy()
        
        assert proxy is not None
        assert 'http' in proxy
        assert 'https' in proxy
        assert proxy['http'] in config['google_play']['proxy_list']
        assert proxy['https'] in config['google_play']['proxy_list']
    
    def test_get_proxy_no_rotation(self, config_manager):
        """Test getting a proxy when rotation is disabled"""
        config = config_manager.config
        config['google_play']['proxy_rotation'] = False
        
        ingestor = GooglePlayIngestor(config)
        
        proxy = ingestor._get_proxy()
        
        assert proxy is None
    
    def test_get_proxy_empty_list(self, config_manager):
        """Test getting a proxy when proxy list is empty"""
        config = config_manager.config
        config['google_play']['proxy_rotation'] = True
        config['google_play']['proxy_list'] = []
        
        ingestor = GooglePlayIngestor(config)
        
        proxy = ingestor._get_proxy()
        
        assert proxy is None
    
    @patch('src.googleplay_ingestor.play_reviews')
    def test_fetch_reviews_with_play_scraper(self, mock_play_reviews, config_manager):
        """Test fetching reviews using play-scraper"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Setup mock play-scraper response
        mock_reviews = [
            {
                'id': 'gp_review_1',
                'userName': 'Alice Johnson',
                'content': 'Best investment app!',
                'score': 5,
                'at': '2024-01-15T12:00:00Z',
                'appId': 'com.example.app',
                'version': '2.1.0',
                'title': 'Amazing'
            },
            {
                'id': 'gp_review_2',
                'userName': 'Bob Wilson',
                'content': 'Could be better',
                'score': 3,
                'at': '2024-01-14T09:30:00Z',
                'appId': 'com.example.app',
                'version': '2.0.9',
                'title': 'Needs work'
            }
        ]
        mock_play_reviews.return_value = mock_reviews
        
        reviews = ingestor.fetch_reviews('com.example.app', days_back=30)
        
        assert len(reviews) == 2
        assert reviews[0]['external_review_id'] == 'gp_review_1'
        assert reviews[0]['author_name'] == 'Alice Johnson'
        assert reviews[0]['review_text'] == 'Best investment app!'
        assert reviews[0]['rating'] == 5
        assert reviews[0]['version'] == '2.1.0'
        assert reviews[0]['title'] == 'Amazing'
        
        assert reviews[1]['external_review_id'] == 'gp_review_2'
        assert reviews[1]['author_name'] == 'Bob Wilson'
        assert reviews[1]['review_text'] == 'Could be better'
        assert reviews[1]['rating'] == 3
        assert reviews[1]['version'] == '2.0.9'
        assert reviews[1]['title'] == 'Needs work'
    
    @patch('src.googleplay_ingestor.play_reviews')
    def test_fetch_reviews_play_scraper_failure_fallback(self, mock_play_reviews, config_manager):
        """Test fallback to manual scraping when play-scraper fails"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Setup mock play-scraper to raise exception
        mock_play_reviews.side_effect = Exception("play-scraper error")
        
        # Mock manual scraping
        with patch.object(ingestor, '_manual_scrape') as mock_manual:
            mock_manual.return_value = [
                {
                    'external_review_id': 'manual_review_1',
                    'title': 'Manual review',
                    'review_text': 'Manual scraping',
                    'author_name': 'Manual User',
                    'rating': 4,
                    'review_date': datetime.utcnow(),
                    'review_url': '',
                    'version': None
                }
            ]
            
            reviews = ingestor.fetch_reviews('com.example.app')
            
            assert len(reviews) == 1
            assert reviews[0]['external_review_id'] == 'manual_review_1'
            mock_manual.assert_called_once()
    
    @patch('src.googleplay_ingestor.play_reviews')
    def test_fetch_reviews_play_scraper_retry_success(self, mock_play_reviews, config_manager):
        """Test play-scraper retry success"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Setup mock to fail then succeed
        mock_reviews = [{'id': 'gp_review_1', 'userName': 'Test User', 'content': 'Test', 'score': 5}]
        mock_play_reviews.side_effect = [
            Exception("First failure"),
            mock_reviews
        ]
        
        reviews = ingestor.fetch_reviews('com.example.app')
        
        assert len(reviews) == 1
        assert mock_play_reviews.call_count == 2
    
    @patch('src.googleplay_ingestor.play_reviews')
    def test_fetch_reviews_play_scraper_import_error(self, mock_play_reviews, config_manager):
        """Test fallback when play-scraper is not available"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Mock ImportError
        with patch.dict('sys.modules', {'play_scraper': None}):
            with patch.object(ingestor, '_manual_scrape') as mock_manual:
                mock_manual.return_value = []
                
                reviews = ingestor.fetch_reviews('com.example.app')
                
                assert reviews == []
                mock_manual.assert_called_once()
    
    @patch('src.googleplay_ingestor.requests.Session')
    @patch('src.googleplay_ingestor.BeautifulSoup')
    def test_manual_scrape_success(self, mock_soup, mock_session_class, config_manager):
        """Test successful manual scraping"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Setup mock session
        mock_session = Mock()
        mock_response = Mock()
        mock_response.content = b'<html>test</html>'
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Setup mock BeautifulSoup
        mock_soup_instance = Mock()
        mock_review_element = Mock()
        mock_review_element.get.return_value = 'review_123'
        mock_soup_instance.find_all.return_value = [mock_review_element]
        mock_soup.return_value = mock_soup_instance
        
        # Mock parsing of HTML element
        with patch.object(ingestor, '_parse_html_element') as mock_parse:
            mock_parse.return_value = {
                'external_review_id': 'review_123',
                'title': 'Manual Review',
                'review_text': 'Manual content',
                'author_name': 'Manual User',
                'rating': 4,
                'review_date': datetime.utcnow(),
                'review_url': '',
                'version': None
            }
            
            reviews = ingestor._manual_scrape('com.example.app', datetime.utcnow() - timedelta(days=30))
            
            assert len(reviews) == 1
            assert reviews[0]['external_review_id'] == 'review_123'
    
    @patch('src.googleplay_ingestor.requests.Session')
    def test_manual_scrape_request_failure(self, mock_session_class, config_manager):
        """Test manual scraping with request failure"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Setup mock session to raise exception
        mock_session = Mock()
        mock_session.get.side_effect = requests.exceptions.RequestException("Network error")
        mock_session_class.return_value = mock_session
        
        reviews = ingestor._manual_scrape('com.example.app', datetime.utcnow() - timedelta(days=30))
        
        assert reviews == []
    
    def test_parse_review_success(self, config_manager):
        """Test successful review parsing from play-scraper output"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        review_data = {
            'id': 'gp_review_1',
            'userName': 'Alice Johnson',
            'content': 'Best investment app!',
            'score': 5,
            'at': '2024-01-15T12:00:00Z',
            'appId': 'com.example.app',
            'version': '2.1.0',
            'title': 'Amazing'
        }
        
        result = ingestor._parse_review(review_data, cutoff_date)
        
        assert result is not None
        assert result['external_review_id'] == 'gp_review_1'
        assert result['author_name'] == 'Alice Johnson'
        assert result['review_text'] == 'Best investment app!'
        assert result['rating'] == 5
        assert result['version'] == '2.1.0'
        assert result['title'] == 'Amazing'
        assert result['review_url'] == 'https://play.google.com/store/apps/details?id=com.example.app'
    
    def test_parse_review_old_review_filtered(self, config_manager):
        """Test that old reviews are filtered out"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        old_date = (datetime.utcnow() - timedelta(days=100)).strftime('%Y-%m-%dT%H:%M:%SZ')
        review_data = {
            'id': 'old_review',
            'userName': 'Old User',
            'content': 'Old review',
            'score': 3,
            'at': old_date,
            'appId': 'com.example.app'
        }
        
        result = ingestor._parse_review(review_data, cutoff_date)
        
        assert result is None  # Should be filtered out
    
    def test_parse_review_missing_fields(self, config_manager):
        """Test parsing review with missing fields"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        review_data = {
            'id': 'minimal_review',
            'userName': 'Minimal User',
            'content': 'Minimal review',
            'score': 4
            # Missing at, appId, version, title
        }
        
        result = ingestor._parse_review(review_data, cutoff_date)
        
        assert result is not None
        assert result['external_review_id'] == 'minimal_review'
        assert result['author_name'] == 'Minimal User'
        assert result['review_text'] == 'Minimal review'
        assert result['rating'] == 4
        assert result['version'] is None
        assert result['title'] == ''
        assert isinstance(result['review_date'], datetime)
    
    def test_parse_html_element_success(self, config_manager):
        """Test successful HTML element parsing"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Create mock HTML element
        mock_element = Mock()
        mock_element.get.return_value = 'html_review_123'
        
        # Create mock sub-elements
        mock_title = Mock()
        mock_title.get_text.return_value = 'HTML Review'
        
        mock_text = Mock()
        mock_text.get_text.return_value = 'HTML content'
        
        mock_author = Mock()
        mock_author.get_text.return_value = 'HTML User'
        
        mock_rating = Mock()
        mock_rating.get.return_value = 'Rated 4 stars'
        
        mock_date = Mock()
        mock_date.get_text.return_value = 'January 15, 2024'
        
        mock_element.find.side_effect = lambda class_name, **kwargs: {
            'review-title': mock_title,
            'review-body': mock_text,
            'author-name': mock_author,
            'rating': mock_rating,
            'review-date': mock_date
        }.get(class_name.split('-')[-1])
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        result = ingestor._parse_html_element(mock_element, cutoff_date)
        
        assert result is not None
        assert result['external_review_id'] == 'html_review_123'
        assert result['title'] == 'HTML Review'
        assert result['review_text'] == 'HTML content'
        assert result['author_name'] == 'HTML User'
        assert result['rating'] == 4
        assert isinstance(result['review_date'], datetime)
    
    def test_parse_html_element_missing_data(self, config_manager):
        """Test HTML element parsing with missing data"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Create mock HTML element with missing sub-elements
        mock_element = Mock()
        mock_element.get.return_value = 'minimal_review'
        mock_element.find.return_value = None  # All sub-elements missing
        
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        result = ingestor._parse_html_element(mock_element, cutoff_date)
        
        assert result is not None
        assert result['external_review_id'] == 'minimal_review'
        assert result['title'] == ''
        assert result['review_text'] == ''
        assert result['author_name'] == ''
        assert result['rating'] is None
        assert isinstance(result['review_date'], datetime)
    
    def test_parse_date_string_relative_date(self, config_manager):
        """Test parsing relative date strings"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Test relative date
        date_str = "2 days ago"
        result = ingestor._parse_date_string(date_str)
        
        assert result is not None
        assert isinstance(result, datetime)
    
    def test_parse_date_string_absolute_date(self, config_manager):
        """Test parsing absolute date strings"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Test absolute date
        date_str = "January 15, 2024"
        result = ingestor._parse_date_string(date_str)
        
        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_date_string_invalid(self, config_manager):
        """Test parsing invalid date strings"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Test invalid date
        date_str = "invalid date"
        result = ingestor._parse_date_string(date_str)
        
        assert result is None
    
    def test_parse_date_string_none(self, config_manager):
        """Test parsing None date string"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        result = ingestor._parse_date_string(None)
        
        assert result is None
    
    def test_extract_rating_from_html_success(self, config_manager):
        """Test successful rating extraction from HTML"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Create mock rating element
        mock_rating = Mock()
        mock_rating.get.return_value = 'Rated 4 stars out of 5'
        
        result = ingestor._extract_rating_from_html(mock_rating)
        
        assert result == 4
    
    def test_extract_rating_from_html_invalid_format(self, config_manager):
        """Test rating extraction with invalid format"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Create mock rating element with invalid format
        mock_rating = Mock()
        mock_rating.get.return_value = 'Invalid rating format'
        
        result = ingestor._extract_rating_from_html(mock_rating)
        
        assert result is None
    
    def test_extract_rating_from_html_missing_aria_label(self, config_manager):
        """Test rating extraction with missing aria-label"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Create mock rating element without aria-label
        mock_rating = Mock()
        mock_rating.get.return_value = None
        
        result = ingestor._extract_rating_from_html(mock_rating)
        
        assert result is None
    
    def test_save_reviews_new_reviews(self, config_manager, test_db_session, sample_product):
        """Test saving new reviews to database"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        reviews = [
            {
                'external_review_id': 'gp_review_1',
                'title': 'Great app',
                'review_text': 'Very user friendly',
                'author_name': 'John Doe',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://play.google.com/review/1',
                'version': '2.1.0'
            },
            {
                'external_review_id': 'gp_review_2',
                'title': 'Good app',
                'review_text': 'Pretty good',
                'author_name': 'Jane Smith',
                'rating': 4,
                'review_date': datetime.utcnow(),
                'review_url': 'https://play.google.com/review/2',
                'version': '2.0.9'
            }
        ]
        
        saved_count = ingestor.save_reviews(reviews, sample_product.id, test_db_session)
        
        assert saved_count == 2
        
        # Verify reviews were saved
        saved_reviews = test_db_session.query(Review).filter(
            Review.product_id == sample_product.id,
            Review.source == 'google_play'
        ).all()
        
        assert len(saved_reviews) == 2
        assert saved_reviews[0].external_review_id == 'gp_review_1'
        assert saved_reviews[1].external_review_id == 'gp_review_2'
    
    def test_save_reviews_duplicates_skipped(self, config_manager, test_db_session, sample_product):
        """Test that duplicate reviews are skipped"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Create an existing review
        existing_review = Review(
            product_id=sample_product.id,
            source='google_play',
            external_review_id='gp_review_1',
            review_text='Existing review',
            rating=5,
            review_date=datetime.utcnow()
        )
        test_db_session.add(existing_review)
        test_db_session.commit()
        
        reviews = [
            {
                'external_review_id': 'gp_review_1',  # Duplicate
                'title': 'Updated title',
                'review_text': 'Updated text',
                'author_name': 'John Doe',
                'rating': 4,
                'review_date': datetime.utcnow(),
                'review_url': 'https://play.google.com/review/1',
                'version': '2.1.0'
            },
            {
                'external_review_id': 'gp_review_2',  # New
                'title': 'New review',
                'review_text': 'New text',
                'author_name': 'Jane Smith',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://play.google.com/review/2',
                'version': '2.1.0'
            }
        ]
        
        saved_count = ingestor.save_reviews(reviews, sample_product.id, test_db_session)
        
        assert saved_count == 1  # Only the new review should be saved
        
        # Verify only one new review was saved
        saved_reviews = test_db_session.query(Review).filter(
            Review.product_id == sample_product.id,
            Review.source == 'google_play'
        ).all()
        
        assert len(saved_reviews) == 2  # 1 existing + 1 new
        assert saved_reviews[0].external_review_id == 'gp_review_1'
        assert saved_reviews[1].external_review_id == 'gp_review_2'
    
    def test_save_reviews_error_handling(self, config_manager, test_db_session, sample_product):
        """Test error handling when saving reviews"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        reviews = [
            {
                'external_review_id': 'gp_review_1',
                'title': 'Great app',
                'review_text': 'Very user friendly',
                'author_name': 'John Doe',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://play.google.com/review/1',
                'version': '2.1.0'
            }
        ]
        
        # Mock database session to raise an exception
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")
        
        saved_count = ingestor.save_reviews(reviews, sample_product.id, mock_session)
        
        assert saved_count == 0
    
    @patch('src.googleplay_ingestor.GooglePlayIngestor.fetch_reviews')
    @patch('src.googleplay_ingestor.GooglePlayIngestor.save_reviews')
    def test_ingest_product_success(self, mock_save_reviews, mock_fetch_reviews, 
                                   config_manager, test_db_session, sample_product):
        """Test successful product ingestion"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Setup mocks
        mock_reviews = [
            {
                'external_review_id': 'gp_review_1',
                'title': 'Great app',
                'review_text': 'Very user friendly',
                'author_name': 'John Doe',
                'rating': 5,
                'review_date': datetime.utcnow(),
                'review_url': 'https://play.google.com/review/1',
                'version': '2.1.0'
            }
        ]
        mock_fetch_reviews.return_value = mock_reviews
        mock_save_reviews.return_value = 1
        
        log = ingestor.ingest_product(sample_product, test_db_session)
        
        assert log.status == 'success'
        assert log.product_id == sample_product.id
        assert log.source == 'google_play'
        assert log.reviews_collected == 1
        assert log.reviews_processed == 1
        assert log.error_message is None
        assert log.completed_at is not None
        assert log.duration_seconds is not None
        
        # Verify package name extraction
        expected_package_name = sample_product.play_store_url.split('id=')[-1]
        mock_fetch_reviews.assert_called_once_with(expected_package_name)
        mock_save_reviews.assert_called_once()
    
    @patch('src.googleplay_ingestor.GooglePlayIngestor.fetch_reviews')
    def test_ingest_product_failure(self, mock_fetch_reviews, config_manager, test_db_session, sample_product):
        """Test product ingestion failure"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Setup mock to raise exception
        mock_fetch_reviews.side_effect = Exception("Fetch error")
        
        log = ingestor.ingest_product(sample_product, test_db_session)
        
        assert log.status == 'failed'
        assert log.product_id == sample_product.id
        assert log.source == 'google_play'
        assert log.error_message == 'Fetch error'
        assert log.completed_at is not None
        assert log.duration_seconds is not None


class TestGooglePlayIngestorIntegration:
    """Integration tests for GooglePlayIngestor"""
    
    def test_full_ingestion_workflow(self, config_manager, test_db_session, sample_product):
        """Test complete ingestion workflow"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # Mock the actual fetching to avoid network calls
        with patch.object(ingestor, 'fetch_reviews') as mock_fetch:
            mock_reviews = [
                {
                    'external_review_id': 'gp_review_1',
                    'title': 'Great app',
                    'review_text': 'Very user friendly',
                    'author_name': 'John Doe',
                    'rating': 5,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://play.google.com/review/1',
                    'version': '2.1.0'
                },
                {
                    'external_review_id': 'gp_review_2',
                    'title': 'Good app',
                    'review_text': 'Pretty good',
                    'author_name': 'Jane Smith',
                    'rating': 4,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://play.google.com/review/2',
                    'version': '2.0.9'
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
                Review.source == 'google_play'
            ).all()
            
            assert len(saved_reviews) == 2
            assert saved_reviews[0].external_review_id == 'gp_review_1'
            assert saved_reviews[1].external_review_id == 'gp_review_2'
            
            # Verify ingestion log was saved
            ingestion_logs = test_db_session.query(IngestionLog).filter(
                IngestionLog.product_id == sample_product.id,
                IngestionLog.source == 'google_play'
            ).all()
            
            assert len(ingestion_logs) == 1
            assert ingestion_logs[0].status == 'success'
    
    def test_duplicate_prevention_across_ingestions(self, config_manager, test_db_session, sample_product):
        """Test that duplicates are prevented across multiple ingestions"""
        config = config_manager.config
        ingestor = GooglePlayIngestor(config)
        
        # First ingestion
        with patch.object(ingestor, 'fetch_reviews') as mock_fetch:
            mock_reviews = [
                {
                    'external_review_id': 'gp_review_1',
                    'title': 'Great app',
                    'review_text': 'Very user friendly',
                    'author_name': 'John Doe',
                    'rating': 5,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://play.google.com/review/1',
                    'version': '2.1.0'
                }
            ]
            mock_fetch.return_value = mock_reviews
            
            log1 = ingestor.ingest_product(sample_product, test_db_session)
            assert log1.reviews_processed == 1
        
        # Second ingestion with same reviews
        with patch.object(ingestor, 'fetch_reviews') as mock_fetch:
            mock_reviews = [
                {
                    'external_review_id': 'gp_review_1',  # Same as before
                    'title': 'Updated title',
                    'review_text': 'Updated text',
                    'author_name': 'John Doe',
                    'rating': 4,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://play.google.com/review/1',
                    'version': '2.1.4'
                },
                {
                    'external_review_id': 'gp_review_2',  # New review
                    'title': 'New review',
                    'review_text': 'New text',
                    'author_name': 'Jane Smith',
                    'rating': 5,
                    'review_date': datetime.utcnow(),
                    'review_url': 'https://play.google.com/review/2',
                    'version': '2.1.4'
                }
            ]
            mock_fetch.return_value = mock_reviews
            
            log2 = ingestor.ingest_product(sample_product, test_db_session)
            assert log2.reviews_collected == 2
            assert log2.reviews_processed == 1  # Only the new review should be processed
        
        # Verify final state
        all_reviews = test_db_session.query(Review).filter(
            Review.product_id == sample_product.id,
            Review.source == 'google_play'
        ).all()
        
        assert len(all_reviews) == 2  # gp_review_1 + gp_review_2
    
    def test_proxy_rotation_functionality(self, config_manager):
        """Test proxy rotation functionality"""
        config = config_manager.config
        config['google_play']['proxy_rotation'] = True
        config['google_play']['proxy_list'] = [
            'http://proxy1:8080',
            'http://proxy2:8080',
            'http://proxy3:8080'
        ]
        
        ingestor = GooglePlayIngestor(config)
        
        # Test multiple calls to _get_proxy
        proxies = set()
        for _ in range(10):
            proxy = ingestor._get_proxy()
            if proxy:
                proxies.add(proxy['http'])
        
        # Should have used at least one proxy from the list
        assert len(proxies) > 0
        assert all(proxy in config['google_play']['proxy_list'] for proxy in proxies)
    
    def test_user_agent_rotation(self, config_manager):
        """Test user agent rotation"""
        config = config_manager.config
        config['google_play']['user_agents'] = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        ingestor = GooglePlayIngestor(config)
        
        # Test multiple sessions
        user_agents = set()
        for _ in range(10):
            session = ingestor._get_session()
            user_agents.add(session.headers['User-Agent'])
        
        # Should have used at least one user agent from the list
        assert len(user_agents) > 0
        assert all(ua in config['google_play']['user_agents'] for ua in user_agents)
