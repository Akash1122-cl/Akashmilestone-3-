"""
Unit tests for Quality Assurance
"""

import pytest
from src.quality_assurance import QualityAssurance, create_quality_assurance, QualityReport


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'quality_assurance': {
            'content_validation': {
                'min_themes': 3,
                'max_themes': 7,
                'min_quotes_per_theme': 2,
                'max_quotes_per_theme': 3,
                'min_action_ideas': 2,
                'max_action_ideas': 3
            },
            'format_validation': {
                'max_page_length': 1000,
                'min_section_length': 50,
                'required_sections': ['executive_summary', 'themes', 'quotes', 'action_ideas']
            },
            'readability': {
                'min_readability_score': 0.6,
                'max_sentence_length': 25,
                'max_paragraph_length': 150
            },
            'completeness': {
                'require_executive_summary': True,
                'require_themes': True,
                'require_quotes': True,
                'require_action_ideas': True
            }
        }
    }


@pytest.fixture
def sample_narrative_result():
    """Sample narrative result"""
    return {
        'executive_summary': 'This week the product received positive feedback overall with some areas for improvement.',
        'themes': [
            {
                'section_name': 'User Experience',
                'content': 'Users love the new interface and find it intuitive.',
                'metadata': {'cluster_size': 50, 'quote_count': 3}
            },
            {
                'section_name': 'Performance',
                'content': 'App performance has improved significantly.',
                'metadata': {'cluster_size': 30, 'quote_count': 2}
            }
        ],
        'quotes': [
            {
                'section_name': 'User Experience Quotes',
                'content': '1. "Great app"\n2. "Easy to use"',
                'metadata': {'quote_count': 2}
            }
        ],
        'action_ideas': [
            {
                'section_name': 'User Experience Actions',
                'content': '1. Improve UX\n2. Add tutorials',
                'metadata': {'action_count': 2}
            }
        ],
        'impact_analysis': 'Overall sentiment is positive with minor improvements needed.',
        'generation_timestamp': '2024-01-01T00:00:00',
        'processing_time_seconds': 0.5,
        'metadata': {}
    }


@pytest.fixture
def sample_formatted_report():
    """Sample formatted report"""
    return {
        'content': '<!DOCTYPE html><html><body><h2>Executive Summary</h2><p>This week the product received positive feedback.</p></body></html>',
        'format_type': 'html',
        'generation_timestamp': '2024-01-01T00:00:00',
        'processing_time_seconds': 0.3,
        'metadata': {}
    }


def test_quality_assurance_creation(sample_config):
    """Test quality assurance creation"""
    qa = create_quality_assurance(sample_config)
    assert qa is not None
    assert isinstance(qa, QualityAssurance)


def test_validate_report(sample_config, sample_narrative_result, sample_formatted_report):
    """Test complete report validation"""
    qa = create_quality_assurance(sample_config)
    result = qa.validate_report(sample_narrative_result, sample_formatted_report)
    
    assert isinstance(result, QualityReport)
    assert result.is_valid is not None
    assert result.overall_score >= 0.0
    assert result.overall_score <= 1.0
    assert len(result.content_checks) > 0
    assert len(result.format_checks) > 0


def test_validate_content(sample_config, sample_narrative_result):
    """Test content validation"""
    qa = create_quality_assurance(sample_config)
    checks = qa._validate_content(sample_narrative_result)
    
    assert len(checks) > 0
    assert all(c.check_name for c in checks)
    assert all(c.passed is not None for c in checks)
    assert all(c.severity in ['error', 'warning', 'info'] for c in checks)


def test_validate_format(sample_config, sample_formatted_report):
    """Test format validation"""
    qa = create_quality_assurance(sample_config)
    checks = qa._validate_format(sample_formatted_report)
    
    assert len(checks) >= 0
    assert all(c.check_name for c in checks)


def test_calculate_readability_score(sample_config, sample_narrative_result):
    """Test readability score calculation"""
    qa = create_quality_assurance(sample_config)
    score = qa._calculate_readability_score(sample_narrative_result)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_calculate_completeness_score(sample_config, sample_narrative_result):
    """Test completeness score calculation"""
    qa = create_quality_assurance(sample_config)
    score = qa._calculate_completeness_score(sample_narrative_result)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_validate_single_section(sample_config):
    """Test single section validation"""
    qa = create_quality_assurance(sample_config)
    
    # Valid section
    checks = qa.validate_single_section('test_section', 'This is a valid section with sufficient content.')
    assert len(checks) >= 0
    
    # Invalid section (too short)
    checks = qa.validate_single_section('test_section', 'Short')
    assert any('too short' in c.message.lower() for c in checks)


def test_quality_report_serialization(sample_config, sample_narrative_result, sample_formatted_report):
    """Test that QualityReport can be serialized"""
    qa = create_quality_assurance(sample_config)
    result = qa.validate_report(sample_narrative_result, sample_formatted_report)
    
    result_dict = result.__dict__
    assert isinstance(result_dict, dict)
    assert 'is_valid' in result_dict
    assert 'overall_score' in result_dict
    assert 'content_checks' in result_dict
    assert 'format_checks' in result_dict
