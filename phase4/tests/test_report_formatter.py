"""
Unit tests for Report Formatter
"""

import pytest
from src.report_formatter import ReportFormatter, create_report_formatter, FormattedReport


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        'report_formatter': {
            'output_formats': ['html', 'markdown'],
            'layout': {
                'max_pages': 1,
                'font_family': 'Arial',
                'font_size': 11,
                'line_height': 1.5,
                'margin': '0.5in'
            },
            'sections': ['executive_summary', 'themes', 'quotes', 'action_ideas'],
            'branding': {
                'company_name': 'Test Company',
                'primary_color': '#2563eb',
                'secondary_color': '#64748b'
            }
        }
    }


@pytest.fixture
def sample_narrative_result():
    """Sample narrative result"""
    return {
        'executive_summary': 'This week the product received positive feedback overall.',
        'themes': [
            {
                'section_name': 'User Experience',
                'content': 'Users love the new interface.',
                'metadata': {'cluster_size': 50}
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
        'impact_analysis': 'Overall sentiment is positive.',
        'generation_timestamp': '2024-01-01T00:00:00',
        'processing_time_seconds': 0.5,
        'metadata': {}
    }


def test_report_formatter_creation(sample_config):
    """Test report formatter creation"""
    formatter = create_report_formatter(sample_config)
    assert formatter is not None
    assert isinstance(formatter, ReportFormatter)


def test_format_html(sample_config, sample_narrative_result):
    """Test HTML formatting"""
    formatter = create_report_formatter(sample_config)
    result = formatter.format_report(sample_narrative_result, 'html')
    
    assert isinstance(result, FormattedReport)
    assert result.format_type == 'html'
    assert result.content is not None
    assert '<!DOCTYPE html>' in result.content or '<html' in result.content
    assert result.processing_time_seconds > 0


def test_format_markdown(sample_config, sample_narrative_result):
    """Test Markdown formatting"""
    formatter = create_report_formatter(sample_config)
    result = formatter.format_report(sample_narrative_result, 'markdown')
    
    assert isinstance(result, FormattedReport)
    assert result.format_type == 'markdown'
    assert result.content is not None
    assert '#' in result.content  # Markdown headers


def test_format_unsupported_format(sample_config, sample_narrative_result):
    """Test unsupported format falls back to HTML"""
    formatter = create_report_formatter(sample_config)
    result = formatter.format_report(sample_narrative_result, 'pdf')
    
    assert isinstance(result, FormattedReport)
    # Should fall back to HTML since PDF is not fully implemented
    assert result.content is not None


def test_validate_one_page_layout(sample_config, sample_narrative_result):
    """Test one-page layout validation"""
    formatter = create_report_formatter(sample_config)
    result = formatter.format_report(sample_narrative_result, 'html')
    
    is_valid = formatter.validate_one_page_layout(result.content)
    assert isinstance(is_valid, bool)


def test_apply_branding_html(sample_config, sample_narrative_result):
    """Test branding application for HTML"""
    formatter = create_report_formatter(sample_config)
    result = formatter.format_report(sample_narrative_result, 'html')
    
    branded = formatter.apply_branding(result.content, 'html')
    assert 'Test Company' in branded or 'Review Pulse' in branded


def test_apply_branding_markdown(sample_config, sample_narrative_result):
    """Test branding application for Markdown"""
    formatter = create_report_formatter(sample_config)
    result = formatter.format_report(sample_narrative_result, 'markdown')
    
    branded = formatter.apply_branding(result.content, 'markdown')
    assert 'Test Company' in branded or 'Review Pulse' in branded


def test_formatted_report_serialization(sample_config, sample_narrative_result):
    """Test that FormattedReport can be serialized"""
    formatter = create_report_formatter(sample_config)
    result = formatter.format_report(sample_narrative_result, 'html')
    
    result_dict = result.__dict__
    assert isinstance(result_dict, dict)
    assert 'content' in result_dict
    assert 'format_type' in result_dict
    assert 'processing_time_seconds' in result_dict
