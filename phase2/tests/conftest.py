"""
Pytest configuration and fixtures for Phase 2 testing
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime
import yaml

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock heavy dependencies
sys.modules['openai'] = Mock()
sys.modules['pinecone'] = Mock()
sys.modules['langdetect'] = Mock()
sys.modules['textblob'] = Mock()
sys.modules['sentence_transformers'] = Mock()
sys.modules['redis'] = Mock()

# Import Phase 2 components
from review_preprocessor import ReviewPreprocessor, ProcessedReview, ProcessingStatus
from embedding_service import EmbeddingService, EmbeddingResult
from data_quality_pipeline import DataQualityPipeline, QualityMetrics
from vector_database import VectorDatabase, VectorRecord
from cache_manager import CacheManager


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'preprocessing': {
            'target_language': 'en',
            'min_text_length': 10,
            'max_text_length': 5000,
            'duplicate_threshold': 0.9,
            'quality_threshold': 0.3
        },
        'embeddings': {
            'model': 'text-embedding-3-small',
            'batch_size': 10,
            'max_tokens': 8192,
            'dimension': 1536,
            'cache_enabled': True,
            'fallback_enabled': True,
            'openai_api_key': 'test-key'
        },
        'quality_pipeline': {
            'quality_thresholds': {
                'excellent': 0.8,
                'good': 0.6,
                'acceptable': 0.4,
                'poor': 0.2
            },
            'anomaly_thresholds': {
                'rating_spike_threshold': 3.0,
                'text_length_min': 10,
                'text_length_max': 2000,
                'sentiment_threshold': 0.8,
                'duplicate_similarity_threshold': 0.9,
                'spam_keywords_threshold': 0.3,
                'bot_pattern_threshold': 0.7
            }
        },
        'vector_database': {
            'index_name': 'test-review-embeddings',
            'dimension': 1536,
            'metric': 'cosine',
            'cloud': 'aws',
            'region': 'us-west-2',
            'batch_size': 10,
            'namespace': 'test-reviews',
            'api_key': 'test-pinecone-key'
        },
        'cache_manager': {
            'default_backend': 'memory',
            'redis': {
                'enabled': False,
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'prefix': 'test-phase2:'
            },
            'memory': {
                'max_size': 100,
                'default_ttl': 3600
            }
        },
        'redis': {
            'host': 'localhost',
            'port': 6379
        }
    }


@pytest.fixture
def sample_review():
    """Sample review data for testing"""
    return {
        'external_review_id': 'test_review_001',
        'title': 'Great app!',
        'review_text': 'This is an excellent investment app with great features and user-friendly interface.',
        'author_name': 'Test User',
        'rating': 5,
        'review_date': '2024-01-15T10:00:00Z',
        'review_url': 'https://play.google.com/store/apps/details?id=com.test',
        'version': '2.1.0',
        'source': 'google_play',
        'product_id': 1
    }


@pytest.fixture
def sample_reviews():
    """Sample batch of reviews for testing"""
    return [
        {
            'external_review_id': f'test_review_{i:03d}',
            'title': f'Review title {i}',
            'review_text': f'This is review number {i} with some content about the investment app.',
            'author_name': f'User {i}',
            'rating': (i % 5) + 1,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': f'https://play.google.com/store/apps/details?id=test_{i}',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        }
        for i in range(1, 21)  # 20 reviews
    ]


@pytest.fixture
def preprocessor(sample_config):
    """Review preprocessor fixture"""
    return ReviewPreprocessor(sample_config)


@pytest.fixture
def embedding_service(sample_config):
    """Embedding service fixture"""
    return EmbeddingService(sample_config)


@pytest.fixture
def quality_pipeline(sample_config):
    """Quality pipeline fixture"""
    return DataQualityPipeline(sample_config)


@pytest.fixture
def vector_database(sample_config):
    """Vector database fixture"""
    return VectorDatabase(sample_config)


@pytest.fixture
def cache_manager(sample_config):
    """Cache manager fixture"""
    return CacheManager(sample_config)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    mock_response = Mock()
    mock_response.data = [
        Mock(
            embedding=[0.1, 0.2, 0.3] * 512,  # 1536 dimensions
            index=0
        )
    ]
    return mock_response


@pytest.fixture
def mock_pinecone_index():
    """Mock Pinecone index"""
    mock_index = Mock()
    mock_index.upsert.return_value = {'upserted_count': 10}
    mock_index.query.return_value = {
        'matches': [
            {
                'id': 'test_id',
                'score': 0.95,
                'metadata': {'test': 'data'},
                'values': [0.1, 0.2, 0.3] * 512
            }
        ]
    }
    mock_index.describe_index_stats.return_value = {
        'totalVectorCount': 100,
        'dimension': 1536,
        'indexFullness': 0.5
    }
    return mock_index


@pytest.fixture
def processed_review():
    """Sample processed review"""
    return ProcessedReview(
        external_review_id='test_review_001',
        title='Great app!',
        review_text='This is an excellent investment app.',
        cleaned_text='this is an excellent investment app',
        author_name='Test User',
        rating=5,
        review_date=datetime(2024, 1, 15, 10, 0, 0),
        review_url='https://play.google.com/store/apps/details?id=test',
        version='2.1.0',
        source='google_play',
        product_id=1,
        language='en',
        sentiment_score=0.8,
        text_length=35,
        word_count=6,
        processed_at=datetime.utcnow(),
        status=ProcessingStatus.SUCCESS,
        quality_score=0.85
    )


# Test utilities
def create_mock_embedding(text: str, dimension: int = 1536) -> list:
    """Create mock embedding for testing"""
    import random
    random.seed(hash(text))
    return [random.uniform(-1, 1) for _ in range(dimension)]


def create_mock_embedding_result(text: str, success: bool = True) -> EmbeddingResult:
    """Create mock embedding result"""
    return EmbeddingResult(
        text=text,
        embedding=create_mock_embedding(text) if success else [],
        embedding_id=f'emb_{int(datetime.utcnow().timestamp() * 1000)}',
        model_used='mock',
        processing_time=0.1,
        token_count=len(text) // 4,
        success=success,
        error_message=None if success else "Test error"
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests"
    )


# Mock decorators
def mock_openai():
    """Mock OpenAI library"""
    mock_client = Mock()
    mock_client.embeddings.create.return_value = Mock(
        data=[Mock(embedding=[0.1, 0.2, 0.3] * 512)]
    )
    return mock_client


def mock_pinecone():
    """Mock Pinecone library"""
    mock_pc = Mock()
    mock_pc.Index.return_value = Mock()
    mock_pc.list_indexes.return_value = Mock(names=[])
    return mock_pc


def mock_redis():
    """Mock Redis library"""
    mock_redis_client = Mock()
    mock_redis_client.ping.return_value = True
    mock_redis_client.get.return_value = None
    mock_redis_client.set.return_value = True
    mock_redis_client.delete.return_value = 1
    mock_redis_client.exists.return_value = False
    mock_redis_client.info.return_value = {
        'used_memory_human': '1M',
        'connected_clients': 1,
        'total_commands_processed': 100,
        'keyspace_hits': 80,
        'keyspace_misses': 20
    }
    return mock_redis_client


# Test data generators
def generate_test_reviews(count: int = 10) -> list:
    """Generate test reviews"""
    reviews = []
    for i in range(count):
        reviews.append({
            'external_review_id': f'test_review_{i:03d}',
            'title': f'Test Review {i}',
            'review_text': f'This is test review number {i} with some sample content.',
            'author_name': f'Test User {i}',
            'rating': (i % 5) + 1,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': f'https://play.google.com/store/apps/details?id=test_{i}',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        })
    return reviews


def generate_spam_reviews(count: int = 5) -> list:
    """Generate spam reviews for testing"""
    spam_texts = [
        "CLICK HERE NOW!!! Buy this amazing product!!!",
        "GET RICH QUICK!!! Free money guaranteed!!!",
        "LIMITED TIME OFFER!!! Act now or miss out!!!",
        "http://spam.com/buy-now click here for deals",
        "BUY NOW!!! 100% FREE MONEY!!! GUARANTEED!!!"
    ]
    
    reviews = []
    for i in range(count):
        reviews.append({
            'external_review_id': f'spam_review_{i:03d}',
            'title': f'SPAM {i}',
            'review_text': spam_texts[i % len(spam_texts)],
            'author_name': f'Spammer{i:03d}',
            'rating': 5,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': f'https://spam.com/review/{i}',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        })
    return reviews


def generate_bot_reviews(count: int = 5) -> list:
    """Generate bot reviews for testing"""
    bot_names = ['user123', 'test456', 'guest789', 'bot001', 'user999']
    
    reviews = []
    for i in range(count):
        reviews.append({
            'external_review_id': f'bot_review_{i:03d}',
            'title': f'Bot Review {i}',
            'review_text': f'This is a generic bot review number {i}.',
            'author_name': bot_names[i % len(bot_names)],
            'rating': 5,
            'review_date': '2024-01-15T10:00:00Z',
            'review_url': f'https://bot.com/review/{i}',
            'version': '2.1.0',
            'source': 'google_play',
            'product_id': 1
        })
    return reviews
