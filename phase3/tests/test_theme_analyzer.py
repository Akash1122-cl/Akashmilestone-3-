"""
Unit tests for Theme Analyzer
"""

import pytest
from src.theme_analyzer import ThemeAnalyzer, create_theme_analyzer, AnalysisResult, Theme


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'theme_analyzer': {
            'llm': {
                'model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 500,
                'api_key': 'test-key',
                'max_retries': 3,
                'retry_delay': 2
            },
            'theme_generation': {
                'max_themes': 7,
                'min_themes': 5,
                'require_action_ideas': True,
                'require_quotes': True,
                'quotes_per_theme': 3
            },
            'prompts': {
                'theme_naming': 'Analyze these reviews: {reviews}',
                'action_ideas': 'Generate ideas for: {theme_name}'
            }
        }
    }


@pytest.fixture
def sample_clusters():
    """Sample clusters for testing"""
    return {
        0: [
            {'id': '1', 'text': 'Great app, very useful', 'sentiment_score': 0.8},
            {'id': '2', 'text': 'Love the features', 'sentiment_score': 0.9},
            {'id': '3', 'text': 'Easy to use', 'sentiment_score': 0.7}
        ],
        1: [
            {'id': '4', 'text': 'Too many bugs', 'sentiment_score': 0.2},
            {'id': '5', 'text': 'Crashes often', 'sentiment_score': 0.1}
        ]
    }


@pytest.fixture
def sample_reviews():
    """Sample reviews for testing"""
    return [
        {'id': '1', 'text': 'Great app, very useful', 'sentiment_score': 0.8, 'product_id': 1, 'product_name': 'TestApp'},
        {'id': '2', 'text': 'Love the features', 'sentiment_score': 0.9, 'product_id': 1, 'product_name': 'TestApp'},
        {'id': '3', 'text': 'Easy to use', 'sentiment_score': 0.7, 'product_id': 1, 'product_name': 'TestApp'},
        {'id': '4', 'text': 'Too many bugs', 'sentiment_score': 0.2, 'product_id': 1, 'product_name': 'TestApp'},
        {'id': '5', 'text': 'Crashes often', 'sentiment_score': 0.1, 'product_id': 1, 'product_name': 'TestApp'}
    ]


def test_theme_analyzer_creation(sample_config):
    """Test theme analyzer creation"""
    analyzer = create_theme_analyzer(sample_config)
    assert analyzer is not None
    assert isinstance(analyzer, ThemeAnalyzer)


def test_analyze_themes(sample_config, sample_clusters, sample_reviews):
    """Test theme analysis"""
    analyzer = create_theme_analyzer(sample_config)
    result = analyzer.analyze_themes(sample_clusters, sample_reviews)
    
    assert isinstance(result, AnalysisResult)
    assert len(result.themes) > 0
    assert result.total_reviews == len(sample_reviews)
    assert result.processing_time_seconds > 0


def test_analyze_themes_mock_mode(sample_config, sample_clusters, sample_reviews):
    """Test theme analysis in mock mode"""
    analyzer = create_theme_analyzer(sample_config)
    analyzer.mock_mode = True
    
    result = analyzer.analyze_themes(sample_clusters, sample_reviews)
    
    assert isinstance(result, AnalysisResult)
    assert len(result.themes) > 0
    assert result.metadata.get('mock_mode') is True
    assert result.processing_time_seconds > 0


def test_analyze_single_cluster(sample_config, sample_clusters):
    """Test analysis of a single cluster"""
    analyzer = create_theme_analyzer(sample_config)
    analyzer.mock_mode = True
    
    cluster_id = 0
    cluster_reviews = sample_clusters[cluster_id]
    
    theme = analyzer._analyze_cluster(cluster_id, cluster_reviews)
    
    assert theme is not None
    assert isinstance(theme, Theme)
    assert theme.cluster_id == cluster_id
    assert theme.cluster_size == len(cluster_reviews)
    assert len(theme.representative_quotes) > 0
    assert len(theme.action_ideas) > 0


def test_extract_representative_quotes(sample_config):
    """Test quote extraction"""
    analyzer = create_theme_analyzer(sample_config)
    
    cluster_reviews = [
        {'text': 'This is a medium length quote that should be extracted properly'},
        {'text': 'Short'},
        {'text': 'This is a very long quote that exceeds the maximum length and should be truncated to fit within the limits'}
    ]
    
    quotes = analyzer._extract_representative_quotes(cluster_reviews, max_quotes=3)
    
    assert len(quotes) > 0
    assert all(isinstance(q, str) for q in quotes)
    assert all(len(q) <= 200 for q in quotes)


def test_calculate_sentiment_score(sample_config):
    """Test sentiment score calculation"""
    analyzer = create_theme_analyzer(sample_config)
    
    cluster_reviews = [
        {'sentiment_score': 0.8},
        {'sentiment_score': 0.9},
        {'sentiment_score': 0.7}
    ]
    
    score = analyzer._calculate_sentiment_score(cluster_reviews)
    
    assert isinstance(score, float)
    assert 0 <= score <= 1
    assert abs(score - 0.8) < 0.01  # Should be average


def test_calculate_quality_score(sample_config):
    """Test quality score calculation"""
    analyzer = create_theme_analyzer(sample_config)
    
    score = analyzer._calculate_quality_score(
        theme_name="Test Theme",
        theme_description="This is a test description for the theme",
        quotes=["Quote 1", "Quote 2"],
        action_ideas=["Action 1", "Action 2"]
    )
    
    assert isinstance(score, float)
    assert 0 <= score <= 1


def test_theme_serialization(sample_config, sample_clusters):
    """Test that Theme can be serialized"""
    analyzer = create_theme_analyzer(sample_config)
    analyzer.mock_mode = True
    
    theme = analyzer._analyze_cluster(0, sample_clusters[0])
    
    theme_dict = theme.__dict__
    assert isinstance(theme_dict, dict)
    assert 'theme_id' in theme_dict
    assert 'name' in theme_dict
    assert 'representative_quotes' in theme_dict


def test_analysis_result_serialization(sample_config, sample_clusters, sample_reviews):
    """Test that AnalysisResult can be serialized"""
    analyzer = create_theme_analyzer(sample_config)
    result = analyzer.analyze_themes(sample_clusters, sample_reviews)
    
    result_dict = result.__dict__
    assert isinstance(result_dict, dict)
    assert 'themes' in result_dict
    assert 'total_reviews' in result_dict
    assert 'processing_time_seconds' in result_dict
