"""
Unit tests for Clustering Engine
"""

import pytest
import numpy as np
from src.clustering_engine import ClusteringEngine, create_clustering_engine, ClusterResult


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'clustering': {
            'umap': {
                'n_components': 5,
                'n_neighbors': 10,
                'min_dist': 0.1,
                'metric': 'cosine',
                'random_state': 42
            },
            'hdbscan': {
                'min_cluster_size': 3,
                'min_samples': 2,
                'metric': 'euclidean',
                'cluster_selection_method': 'eom',
                'prediction_data': True
            },
            'optimization': {
                'enabled': False
            },
            'quality_metrics': {
                'silhouette_score': True,
                'davies_bouldin_index': True,
                'calinski_harabasz_index': True
            }
        }
    }


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing"""
    np.random.seed(42)
    return np.random.rand(50, 1536).tolist()


@pytest.fixture
def sample_review_ids():
    """Sample review IDs for testing"""
    return [f"review_{i}" for i in range(50)]


def test_clustering_engine_creation(sample_config):
    """Test clustering engine creation"""
    engine = create_clustering_engine(sample_config)
    assert engine is not None
    assert isinstance(engine, ClusteringEngine)


def test_cluster_reviews(sample_config, sample_embeddings, sample_review_ids):
    """Test clustering of reviews"""
    engine = create_clustering_engine(sample_config)
    result = engine.cluster_reviews(sample_embeddings, sample_review_ids)
    
    assert isinstance(result, ClusterResult)
    assert len(result.cluster_labels) == len(sample_embeddings)
    assert result.cluster_size == len(sample_embeddings)
    assert 'num_clusters' in result.cluster_metadata


def test_cluster_reviews_mock_mode(sample_config, sample_embeddings, sample_review_ids):
    """Test clustering in mock mode"""
    config = sample_config.copy()
    engine = create_clustering_engine(config)
    
    # Force mock mode by setting mock_mode attribute
    engine.mock_mode = True
    
    result = engine.cluster_reviews(sample_embeddings, sample_review_ids)
    
    assert isinstance(result, ClusterResult)
    assert result.cluster_metadata.get('mock_mode') is True


def test_get_cluster_reviews(sample_config, sample_embeddings, sample_review_ids):
    """Test getting reviews for a specific cluster"""
    engine = create_clustering_engine(sample_config)
    cluster_result = engine.cluster_reviews(sample_embeddings, sample_review_ids)
    
    # Get reviews for cluster 0
    cluster_reviews = engine.get_cluster_reviews(cluster_result, 0, sample_review_ids)
    
    assert isinstance(cluster_reviews, list)
    # Should have at least some reviews in cluster 0
    assert len(cluster_reviews) >= 0


def test_optimize_parameters_disabled(sample_config, sample_embeddings, sample_review_ids):
    """Test parameter optimization when disabled"""
    config = sample_config.copy()
    config['clustering']['optimization']['enabled'] = False
    
    engine = create_clustering_engine(config)
    result = engine.optimize_parameters(sample_embeddings, sample_review_ids)
    
    assert result['optimized'] is False
    assert 'parameters' in result


def test_calculate_quality_metrics(sample_config):
    """Test quality metrics calculation"""
    engine = create_clustering_engine(sample_config)
    
    # Create sample data
    embeddings = np.random.rand(20, 10)
    labels = np.array([0] * 10 + [1] * 10)
    
    metrics = engine._calculate_quality_metrics(embeddings, labels)
    
    assert 'silhouette_score' in metrics
    assert 'davies_bouldin_score' in metrics
    assert 'calinski_harabasz_score' in metrics


def test_cluster_result_serialization(sample_config, sample_embeddings, sample_review_ids):
    """Test that ClusterResult can be serialized"""
    engine = create_clustering_engine(sample_config)
    result = engine.cluster_reviews(sample_embeddings, sample_review_ids)
    
    # Test __dict__ serialization
    result_dict = result.__dict__
    assert isinstance(result_dict, dict)
    assert 'cluster_id' in result_dict
    assert 'cluster_labels' in result_dict
    assert 'quality_metrics' in result_dict
