"""
Unit tests for Narrative Builder
"""

import pytest
from src.narrative_builder import NarrativeBuilder, create_narrative_builder, NarrativeResult


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'narrative_builder': {
            'template_engine': 'jinja2',
            'template_directory': './templates',
            'max_themes': 7,
            'min_themes': 5,
            'max_quotes_per_theme': 3,
            'max_action_ideas': 3,
            'llm': {
                'model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 500,
                'api_key': 'test-key',
                'max_retries': 3,
                'retry_delay': 2
            },
            'prompts': {
                'executive_summary': 'Generate summary for {product_name}',
                'quote_ranking': 'Rank quotes'
            }
        }
    }


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result"""
    return {
        'product_id': 1,
        'product_name': 'TestApp',
        'total_reviews': 100,
        'num_themes': 3,
        'metadata': {}
    }


@pytest.fixture
def sample_themes():
    """Sample themes"""
    return [
        {
            'theme_id': 'theme_0',
            'name': 'User Experience',
            'description': 'Users report UX issues',
            'cluster_id': 0,
            'cluster_size': 50,
            'representative_quotes': ['Great app', 'Easy to use', 'Love it'],
            'action_ideas': ['Improve UX', 'Add tutorials', 'Fix bugs']
        },
        {
            'theme_id': 'theme_1',
            'name': 'Performance',
            'description': 'App performance issues',
            'cluster_id': 1,
            'cluster_size': 30,
            'representative_quotes': ['Too slow', 'Crashes', 'Laggy'],
            'action_ideas': ['Optimize code', 'Fix memory leaks', 'Improve caching']
        }
    ]


def test_narrative_builder_creation(sample_config):
    """Test narrative builder creation"""
    builder = create_narrative_builder(sample_config)
    assert builder is not None
    assert isinstance(builder, NarrativeBuilder)


def test_build_narrative(sample_config, sample_analysis_result, sample_themes):
    """Test narrative building"""
    builder = create_narrative_builder(sample_config)
    result = builder.build_narrative(sample_analysis_result, sample_themes)
    
    assert isinstance(result, NarrativeResult)
    assert result.executive_summary is not None
    assert len(result.themes) > 0
    assert len(result.quotes) > 0
    assert len(result.action_ideas) > 0
    assert result.impact_analysis is not None
    assert result.processing_time_seconds > 0


def test_build_narrative_mock_mode(sample_config, sample_analysis_result, sample_themes):
    """Test narrative building in mock mode"""
    builder = create_narrative_builder(sample_config)
    builder.mock_mode = True
    
    result = builder.build_narrative(sample_analysis_result, sample_themes)
    
    assert isinstance(result, NarrativeResult)
    assert result.metadata.get('mock_mode') is True
    assert result.executive_summary is not None


def test_generate_executive_summary(sample_config, sample_analysis_result, sample_themes):
    """Test executive summary generation"""
    builder = create_narrative_builder(sample_config)
    builder.mock_mode = True
    
    summary = builder._generate_executive_summary(sample_analysis_result, sample_themes)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert 'TestApp' in summary or 'product' in summary.lower()


def test_build_theme_narratives(sample_config, sample_themes):
    """Test theme narrative building"""
    builder = create_narrative_builder(sample_config)
    
    narratives = builder._build_theme_narratives(sample_themes)
    
    assert len(narratives) > 0
    assert all(n.section_name for n in narratives)
    assert all(n.content for n in narratives)


def test_build_quote_sections(sample_config, sample_themes):
    """Test quote section building"""
    builder = create_narrative_builder(sample_config)
    
    quote_sections = builder._build_quote_sections(sample_themes)
    
    assert len(quote_sections) > 0
    assert all('quote' in n.section_name.lower() for n in quote_sections)


def test_build_action_idea_sections(sample_config, sample_themes):
    """Test action idea section building"""
    builder = create_narrative_builder(sample_config)
    
    action_sections = builder._build_action_idea_sections(sample_themes)
    
    assert len(action_sections) > 0
    assert all('action' in n.section_name.lower() for n in action_sections)


def test_generate_impact_analysis(sample_config, sample_themes):
    """Test impact analysis generation"""
    builder = create_narrative_builder(sample_config)
    
    impact = builder._generate_impact_analysis(sample_themes)
    
    assert isinstance(impact, str)
    assert len(impact) > 0
    assert 'Impact Analysis' in impact or 'impact' in impact.lower()


def test_narrative_result_serialization(sample_config, sample_analysis_result, sample_themes):
    """Test that NarrativeResult can be serialized"""
    builder = create_narrative_builder(sample_config)
    result = builder.build_narrative(sample_analysis_result, sample_themes)
    
    result_dict = result.__dict__
    assert isinstance(result_dict, dict)
    assert 'executive_summary' in result_dict
    assert 'themes' in result_dict
    assert 'processing_time_seconds' in result_dict
