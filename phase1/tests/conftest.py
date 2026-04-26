"""
Pytest configuration and fixtures for Phase 1 tests
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import yaml
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from fastapi.testclient import TestClient

# Mock heavy dependencies to avoid import errors
import sys
from unittest.mock import Mock

# Mock modules that might not be available
sys.modules['redis'] = Mock()
sys.modules['psycopg2'] = Mock()
sys.modules['sqlalchemy'] = Mock()
sys.modules['celery'] = Mock()
sys.modules['feedparser'] = Mock()

# Now import the modules we need for testing
from src.config_manager import ConfigManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def test_config(temp_dir):
    """Create a test configuration file"""
    config_data = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'name': 'test_review_pulse',
            'user': 'postgres',
            'password': 'postgres',
            'pool_size': 5,
            'max_overflow': 10
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'password': None,
            'db': 1,
            'max_connections': 10
        },
        'app_store': {
            'rss_feed_url': 'https://itunes.apple.com/rss/customerreviews/page=1/id=123456789/sortby=mostrecent/xml',
            'request_timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 1
        },
        'google_play': {
            'base_url': 'https://play.google.com/store/apps/details',
            'request_timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 1,
            'proxies': []
        },
        'products': [
            {
                'id': 1,
                'name': 'Groww',
                'app_store_id': '123456789',
                'play_store_url': 'https://play.google.com/store/apps/details?id=com.nextbillion.groww',
                'enabled': True
            }
        ],
        'ingestion': {
            'schedule': '0 2 * * *',
            'batch_size': 100,
            'max_reviews_per_run': 1000
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'api': {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False
        }
    }
    
    config_path = os.path.join(temp_dir, 'config.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    
    return config_path


@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session"""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_redis():
    """Mock Redis connection"""
    mock_redis_client = Mock()
    mock_redis_client.ping.return_value = True
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    mock_redis_client.exists.return_value = False
    mock_redis_client.delete.return_value = 1
    mock_redis_client.keys.return_value = []
    mock_redis_client.info.return_value = {
        'used_memory': 1024000,
        'used_memory_human': '1.00M',
        'keyspace_hits': 100,
        'keyspace_misses': 10
    }
    return mock_redis_client


@pytest.fixture
def config_manager(test_config):
    """Create a test configuration manager"""
    return ConfigManager(test_config)


@pytest.fixture
def database_manager(test_config, test_db_engine):
    """Create a test database manager with SQLite"""
    # Patch the engine creation to use our test engine
    with patch.object(DatabaseManager, '_create_engine', return_value=test_db_engine):
        db_manager = DatabaseManager(test_config)
        yield db_manager


@pytest.fixture
def redis_manager(mock_redis):
    """Create a test Redis manager with mocked Redis"""
    with patch('redis.Redis', return_value=mock_redis):
        manager = RedisManager({'host': 'localhost', 'port': 6379, 'password': None, 'db': 1})
    return manager


@pytest.fixture
def sample_product():
    """Create a sample product for testing"""
    return Product(
        name='Groww',
        app_store_id='123456789',
        play_store_url='https://play.google.com/store/apps/details?id=com.nextbillion.groww'
    )


@pytest.fixture
def sample_review():
    """Create a sample review for testing"""
    return Review(
        product_id=1,
        source='app_store',
        external_review_id='review_123',
        review_text='Great app! Very user friendly.',
        rating=5,
        author_name='John Doe',
        review_date='2024-01-15T10:30:00Z',
        review_url='https://example.com/review/123',
        version='1.2.3',
        title='Excellent'
    )


@pytest.fixture
def sample_ingestion_log():
    """Create a sample ingestion log for testing"""
    return IngestionLog(
        product_id=1,
        source='app_store',
        status='success',
        reviews_collected=50,
        reviews_processed=45,
        duration_seconds=120
    )


@pytest.fixture
def test_client():
    """Create a FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def mock_feedparser():
    """Mock feedparser for App Store tests"""
    mock_feed = Mock()
    mock_feed.entries = [
        Mock(
            id='review_1',
            title='Great app',
            summary='Very user friendly',
            author=Mock(name='John Doe'),
            updated='2024-01-15T10:30:00Z',
            link='https://example.com/review/1',
            im_rating=5,
            im_version='1.2.3'
        ),
        Mock(
            id='review_2',
            title='Good but needs improvement',
            summary='Some features are missing',
            author=Mock(name='Jane Smith'),
            updated='2024-01-14T15:45:00Z',
            link='https://example.com/review/2',
            im_rating=4,
            im_version='1.2.2'
        )
    ]
    return mock_feed


@pytest.fixture
def mock_scraper():
    """Mock Google Play scraper"""
    mock_reviews = [
        {
            'id': 'gp_review_1',
            'userName': 'Alice Johnson',
            'content': 'Best investment app!',
            'score': 5,
            'at': '2024-01-15T12:00:00Z',
            'url': 'https://play.google.com/review/1',
            'version': '2.1.0',
            'title': 'Amazing'
        },
        {
            'id': 'gp_review_2',
            'userName': 'Bob Wilson',
            'content': 'Could be better',
            'score': 3,
            'at': '2024-01-14T09:30:00Z',
            'url': 'https://play.google.com/review/2',
            'version': '2.0.9',
            'title': 'Needs work'
        }
    ]
    return mock_reviews


@pytest.fixture
def mock_celery():
    """Mock Celery for testing tasks"""
    with patch('src.tasks.celery_app') as mock_celery:
        mock_celery.send_task.return_value = Mock(id='task_123')
        yield mock_celery
