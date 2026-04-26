"""
Unit tests for Validation Framework
"""

import pytest
from src.validation_framework import ValidationFramework, create_validation_framework, ValidationResult


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'validation': {
            'quote_verification': {
                'enabled': True,
                'fuzzy_match_threshold': 0.85,
                'max_quote_length': 200
            },
            'theme_consistency': {
                'enabled': True,
                'min_similarity_threshold': 0.6,
                'cross_validation': True
            },
            'quality_scoring': {
                'enabled': True,
                'weights': {
                    'quote_accuracy': 0.4,
                    'theme_coherence': 0.3,
                    'action_relevance': 0.3
                },
                'min_quality_score': 0.7
            }
        }
    }


@pytest.fixture
def sample_themes():
    """Sample themes for testing"""
    return [
        {
            'theme_id': 'theme_0',
            'name': 'User Experience',
            'description': 'Users report issues with app navigation',
            'cluster_id': 0,
            'cluster_size': 5,
            'representative_quotes': ['Great app, very useful', 'Easy to use'],
            'action_ideas': ['Improve navigation', 'Add tutorials']
        },
        {
            'theme_id': 'theme_1',
            'name': 'Performance',
            'description': 'App performance issues reported',
            'cluster_id': 1,
            'cluster_size': 3,
            'representative_quotes': ['Too slow', 'Crashes often'],
            'action_ideas': ['Optimize code', 'Fix bugs']
        }
    ]


@pytest.fixture
def sample_reviews():
    """Sample reviews for testing"""
    return [
        {'id': '1', 'text': 'Great app, very useful'},
        {'id': '2', 'text': 'Easy to use navigation'},
        {'id': '3', 'text': 'Too slow loading'},
        {'id': '4', 'text': 'App crashes often'},
        {'id': '5', 'text': 'Love the features'}
    ]


def test_validation_framework_creation(sample_config):
    """Test validation framework creation"""
    validator = create_validation_framework(sample_config)
    assert validator is not None
    assert isinstance(validator, ValidationFramework)


def test_validate_analysis(sample_config, sample_themes, sample_reviews):
    """Test complete analysis validation"""
    validator = create_validation_framework(sample_config)
    result = validator.validate_analysis(sample_themes, sample_reviews)
    
    assert isinstance(result, ValidationResult)
    assert 'is_valid' in result.__dict__
    assert 'quote_accuracy_score' in result.__dict__
    assert 'theme_coherence_score' in result.__dict__
    assert 'action_relevance_score' in result.__dict__
    assert 'overall_quality_score' in result.__dict__


def test_validate_quotes(sample_config, sample_themes, sample_reviews):
    """Test quote validation"""
    validator = create_validation_framework(sample_config)
    errors = []
    
    accuracy = validator._validate_quotes(sample_themes, sample_reviews, errors)
    
    assert isinstance(accuracy, float)
    assert 0 <= accuracy <= 1
    assert isinstance(errors, list)


def test_verify_quote_in_reviews(sample_config):
    """Test quote verification against reviews"""
    validator = create_validation_framework(sample_config)
    
    reviews = [
        'This is a great app',
        'Easy to use navigation',
        'Too slow loading'
    ]
    
    # Test exact match
    assert validator._verify_quote_in_reviews('great app', reviews) is True
    
    # Test partial match
    assert validator._verify_quote_in_reviews('navigation', reviews) is True
    
    # Test no match
    assert validator._verify_quote_in_reviews('not found', reviews) is False


def test_normalize_text(sample_config):
    """Test text normalization"""
    validator = create_validation_framework(sample_config)
    
    text1 = "This is a TEST!"
    text2 = "this is a test"
    
    normalized1 = validator._normalize_text(text1)
    normalized2 = validator._normalize_text(text2)
    
    assert normalized1 == normalized2
    assert normalized1.islower()


def test_validate_theme_consistency(sample_config, sample_themes, sample_reviews):
    """Test theme consistency validation"""
    validator = create_validation_framework(sample_config)
    warnings = []
    
    coherence = validator._validate_theme_consistency(sample_themes, sample_reviews, warnings)
    
    assert isinstance(coherence, float)
    assert 0 <= coherence <= 1
    assert isinstance(warnings, list)


def test_validate_action_ideas(sample_config, sample_themes):
    """Test action ideas validation"""
    validator = create_validation_framework(sample_config)
    warnings = []
    
    relevance = validator._validate_action_ideas(sample_themes, warnings)
    
    assert isinstance(relevance, float)
    assert 0 <= relevance <= 1
    assert isinstance(warnings, list)


def test_validate_single_theme(sample_config):
    """Test validation of a single theme"""
    validator = create_validation_framework(sample_config)
    
    theme = {
        'theme_id': 'theme_0',
        'name': 'Test Theme',
        'description': 'Test description',
        'representative_quotes': ['Test quote'],
        'action_ideas': ['Test action']
    }
    
    cluster_reviews = [
        {'text': 'Test quote here'}
    ]
    
    result = validator.validate_single_theme(theme, cluster_reviews)
    
    assert isinstance(result, ValidationResult)
    assert 'is_valid' in result.__dict__


def test_validation_result_serialization(sample_config, sample_themes, sample_reviews):
    """Test that ValidationResult can be serialized"""
    validator = create_validation_framework(sample_config)
    result = validator.validate_analysis(sample_themes, sample_reviews)
    
    result_dict = result.__dict__
    assert isinstance(result_dict, dict)
    assert 'is_valid' in result_dict
    assert 'validation_errors' in result_dict
    assert 'validation_warnings' in result_dict


def test_quote_length_validation(sample_config):
    """Test quote length validation"""
    validator = create_validation_framework(sample_config)
    
    long_quote = 'a' * 300  # Exceeds max length
    short_quote = 'a' * 50  # Within max length
    
    assert len(long_quote) > validator.max_quote_length
    assert len(short_quote) <= validator.max_quote_length
