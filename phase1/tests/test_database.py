"""
Test cases for database.py - Database models and connections
"""

import pytest
from unittest.mock import patch, Mock
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from src.database import (
    Product, Review, IngestionLog, DatabaseManager,
    init_database, get_db, db_manager
)


class TestProduct:
    """Test cases for Product model"""
    
    def test_product_creation(self, sample_product):
        """Test creating a Product instance"""
        assert sample_product.name == 'Groww'
        assert sample_product.app_store_id == '123456789'
        assert sample_product.play_store_url == 'https://play.google.com/store/apps/details?id=com.nextbillion.groww'
        assert sample_product.id is None  # Not yet saved to database
        assert isinstance(sample_product.created_at, datetime)
        assert isinstance(sample_product.updated_at, datetime)
    
    def test_product_repr(self, sample_product):
        """Test Product string representation"""
        expected = f"<Product(id=None, name='Groww')>"
        assert repr(sample_product) == expected
    
    def test_product_unique_name_constraint(self, test_db_session):
        """Test that product names must be unique"""
        product1 = Product(name='Groww', app_store_id='123', play_store_url='http://example.com')
        product2 = Product(name='Groww', app_store_id='456', play_store_url='http://example2.com')
        
        test_db_session.add(product1)
        test_db_session.commit()
        
        test_db_session.add(product2)
        with pytest.raises(SQLAlchemyError):
            test_db_session.commit()


class TestReview:
    """Test cases for Review model"""
    
    def test_review_creation(self, sample_review):
        """Test creating a Review instance"""
        assert sample_review.product_id == 1
        assert sample_review.source == 'app_store'
        assert sample_review.external_review_id == 'review_123'
        assert sample_review.review_text == 'Great app! Very user friendly.'
        assert sample_review.rating == 5
        assert sample_review.author_name == 'John Doe'
        assert sample_review.review_date == '2024-01-15T10:30:00Z'
        assert sample_review.review_url == 'https://example.com/review/123'
        assert sample_review.version == '1.2.3'
        assert sample_review.title == 'Excellent'
        assert isinstance(sample_review.created_at, datetime)
        assert isinstance(sample_review.updated_at, datetime)
    
    def test_review_source_constraint(self, test_db_session):
        """Test that review source must be valid"""
        with pytest.raises(SQLAlchemyError):
            review = Review(
                product_id=1,
                source='invalid_source',
                external_review_id='review_123',
                review_text='Test review',
                rating=5,
                review_date=datetime.utcnow()
            )
            test_db_session.add(review)
            test_db_session.commit()
    
    def test_review_rating_constraint(self, test_db_session):
        """Test that review rating must be between 1 and 5"""
        # Test invalid rating (0)
        with pytest.raises(SQLAlchemyError):
            review = Review(
                product_id=1,
                source='app_store',
                external_review_id='review_123',
                review_text='Test review',
                rating=0,
                review_date=datetime.utcnow()
            )
            test_db_session.add(review)
            test_db_session.commit()
        
        # Test invalid rating (6)
        with pytest.raises(SQLAlchemyError):
            review = Review(
                product_id=1,
                source='app_store',
                external_review_id='review_124',
                review_text='Test review 2',
                rating=6,
                review_date=datetime.utcnow()
            )
            test_db_session.add(review)
            test_db_session.commit()
    
    def test_review_repr(self, sample_review):
        """Test Review string representation"""
        expected = f"<Review(id=None, product_id=1, source='app_store', external_review_id='review_123')>"
        assert repr(sample_review) == expected


class TestIngestionLog:
    """Test cases for IngestionLog model"""
    
    def test_ingestion_log_creation(self, sample_ingestion_log):
        """Test creating an IngestionLog instance"""
        assert sample_ingestion_log.product_id == 1
        assert sample_ingestion_log.source == 'app_store'
        assert sample_ingestion_log.status == 'success'
        assert sample_ingestion_log.reviews_collected == 50
        assert sample_ingestion_log.reviews_processed == 45
        assert sample_ingestion_log.duration_seconds == 120
        assert sample_ingestion_log.error_message is None
        assert sample_ingestion_log.completed_at is None
        assert isinstance(sample_ingestion_log.started_at, datetime)
    
    def test_ingestion_log_status_constraint(self, test_db_session):
        """Test that ingestion log status must be valid"""
        with pytest.raises(SQLAlchemyError):
            log = IngestionLog(
                product_id=1,
                source='app_store',
                status='invalid_status'
            )
            test_db_session.add(log)
            test_db_session.commit()
    
    def test_ingestion_log_repr(self, sample_ingestion_log):
        """Test IngestionLog string representation"""
        expected = f"<IngestionLog(id=None, product_id=1, source='app_store', status='success')>"
        assert repr(sample_ingestion_log) == expected


class TestDatabaseManager:
    """Test cases for DatabaseManager class"""
    
    def test_database_manager_initialization(self, database_manager):
        """Test DatabaseManager initialization"""
        assert database_manager.config is not None
        assert database_manager.engine is not None
        assert database_manager.SessionLocal is not None
    
    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_config_success(self, mock_yaml_load, mock_open, database_manager):
        """Test successful configuration loading"""
        mock_yaml_load.return_value = {'database': {'host': 'localhost'}}
        mock_open.return_value.__enter__.return_value.read.return_value = 'test'
        
        config = database_manager._load_config('test_config.yaml')
        assert config == {'database': {'host': 'localhost'}}
    
    @patch('builtins.open')
    def test_load_config_file_not_found(self, mock_open, database_manager):
        """Test configuration loading with missing file"""
        mock_open.side_effect = FileNotFoundError("Config file not found")
        
        with pytest.raises(FileNotFoundError):
            database_manager._load_config('nonexistent_config.yaml')
    
    def test_create_engine(self, database_manager):
        """Test SQLAlchemy engine creation"""
        engine = database_manager._create_engine()
        assert engine is not None
        assert engine.url.drivername == 'postgresql'
    
    def test_get_session(self, database_manager):
        """Test getting a database session"""
        session = database_manager.get_session()
        assert session is not None
        session.close()
    
    def test_create_tables(self, database_manager):
        """Test creating database tables"""
        # Should not raise an exception
        database_manager.create_tables()
    
    def test_drop_tables(self, database_manager):
        """Test dropping database tables"""
        # Should not raise an exception
        database_manager.drop_tables()
    
    def test_close(self, database_manager):
        """Test closing database connection"""
        # Should not raise an exception
        database_manager.close()


class TestDatabaseFunctions:
    """Test cases for database module functions"""
    
    @patch('src.database.DatabaseManager')
    def test_init_database(self, mock_db_manager_class):
        """Test init_database function"""
        mock_db_manager = Mock()
        mock_db_manager_class.return_value = mock_db_manager
        
        result = init_database('test_config.yaml')
        
        assert result == mock_db_manager
        mock_db_manager_class.assert_called_once_with('test_config.yaml')
    
    @patch('src.database.db_manager', None)
    @patch('src.database.init_database')
    def test_get_db_no_manager(self, mock_init_db):
        """Test get_db when no manager exists"""
        mock_session = Mock()
        mock_db_manager = Mock()
        mock_db_manager.get_session.return_value = mock_session
        mock_init_db.return_value = mock_db_manager
        
        result = get_db()
        
        assert result == mock_session
        mock_init_db.assert_called_once()
    
    @patch('src.database.db_manager')
    def test_get_db_with_manager(self, mock_db_manager):
        """Test get_db when manager exists"""
        mock_session = Mock()
        mock_db_manager.get_session.return_value = mock_session
        
        result = get_db()
        
        assert result == mock_session
        mock_db_manager.get_session.assert_called_once()


class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    def test_full_product lifecycle(self, test_db_session):
        """Test complete product lifecycle"""
        # Create product
        product = Product(
            name='Test App',
            app_store_id='987654321',
            play_store_url='https://play.google.com/store/apps/details?id=test.app'
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        assert product.id is not None
        
        # Read product
        retrieved = test_db_session.query(Product).filter(Product.id == product.id).first()
        assert retrieved is not None
        assert retrieved.name == 'Test App'
        
        # Update product
        retrieved.name = 'Updated Test App'
        test_db_session.commit()
        
        updated = test_db_session.query(Product).filter(Product.id == product.id).first()
        assert updated.name == 'Updated Test App'
        
        # Delete product
        test_db_session.delete(updated)
        test_db_session.commit()
        
        deleted = test_db_session.query(Product).filter(Product.id == product.id).first()
        assert deleted is None
    
    def test_product_review_relationship(self, test_db_session):
        """Test relationship between products and reviews"""
        # Create product
        product = Product(
            name='Test App',
            app_store_id='987654321',
            play_store_url='https://play.google.com/store/apps/details?id=test.app'
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        # Create reviews for the product
        review1 = Review(
            product_id=product.id,
            source='app_store',
            external_review_id='review_1',
            review_text='Great app!',
            rating=5,
            review_date=datetime.utcnow()
        )
        review2 = Review(
            product_id=product.id,
            source='google_play',
            external_review_id='review_2',
            review_text='Good app',
            rating=4,
            review_date=datetime.utcnow()
        )
        
        test_db_session.add_all([review1, review2])
        test_db_session.commit()
        
        # Verify relationship
        reviews = test_db_session.query(Review).filter(Review.product_id == product.id).all()
        assert len(reviews) == 2
        assert all(review.product_id == product.id for review in reviews)
    
    def test_ingestion_log_with_product(self, test_db_session):
        """Test ingestion log relationship with product"""
        # Create product
        product = Product(
            name='Test App',
            app_store_id='987654321',
            play_store_url='https://play.google.com/store/apps/details?id=test.app'
        )
        test_db_session.add(product)
        test_db_session.commit()
        
        # Create ingestion log
        log = IngestionLog(
            product_id=product.id,
            source='app_store',
            status='success',
            reviews_collected=10,
            reviews_processed=10,
            duration_seconds=60
        )
        test_db_session.add(log)
        test_db_session.commit()
        
        # Verify relationship
        retrieved_log = test_db_session.query(IngestionLog).filter(IngestionLog.id == log.id).first()
        assert retrieved_log.product_id == product.id
