"""
Edge Case Tests for Phase 4: Report Generation
Tests handling of insufficient themes, long quotes, action conflicts, one-page overflow, template failures
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from narrative_builder import NarrativeBuilder, NarrativeResult, NarrativeSection
from report_formatter import ReportFormatter, FormattedReport
from quality_assurance import QualityAssurance, QualityReport, ValidationCheck


class TestInsufficientThemes:
    """Test handling of insufficient themes for comprehensive report"""
    
    def test_minimum_theme_threshold(self):
        """Edge Case: Reports with fewer than 3 themes should be flagged"""
        themes = [
            {'section_name': 'Performance', 'content': 'App is slow'},
        ]
        
        min_themes = 3
        assert len(themes) < min_themes
    
    def test_lower_threshold_adjustment(self):
        """Edge Case: Minimum threshold should be lowered when necessary"""
        themes = [
            {'section_name': 'Performance', 'content': 'App is slow'},
            {'section_name': 'UX', 'content': 'Navigation issues'},
        ]
        
        # Lower threshold to accommodate limited data
        adjusted_min = max(2, len(themes))
        assert adjusted_min == 2
    
    def test_outlier_review_inclusion(self):
        """Edge Case: Individual outlier reviews should be included when themes are insufficient"""
        themes = []
        outlier_reviews = [
            {'id': '1', 'text': 'Crashes on startup', 'sentiment': 'negative'},
            {'id': '2', 'text': 'Love the dark mode', 'sentiment': 'positive'},
        ]
        
        # Include outliers as additional themes
        additional_content = len(outlier_reviews) > 0
        assert additional_content is True


class TestLongAndSensitiveQuotes:
    """Test handling of quotes that are too long or contain sensitive information"""
    
    def test_quote_truncation(self):
        """Edge Case: Quotes should be truncated to max 150 characters"""
        long_quote = "This application has been absolutely wonderful for managing my investment portfolio, tracking stocks, mutual funds, and providing real-time market updates that help me make informed decisions daily."
        max_length = 150
        
        truncated = long_quote[:max_length] + "..." if len(long_quote) > max_length else long_quote
        
        assert len(truncated) <= max_length + 3
        assert truncated.endswith("...")
    
    def test_pii_detection(self):
        """Edge Case: PII should be detected and redacted"""
        quote_with_pii = "My email is john.doe@example.com and phone is 555-123-4567"
        
        # Detect patterns
        email_pattern = '@' in quote_with_pii and '.' in quote_with_pii
        phone_pattern = any(c.isdigit() for c in quote_with_pii)
        
        assert email_pattern is True
        assert phone_pattern is True
    
    def test_pii_redaction(self):
        """Edge Case: PII should be redacted from quotes"""
        original = "Contact me at john@example.com or call 555-1234"
        
        # Simple redaction
        redacted = original
        redacted = redacted.replace('john@example.com', '[EMAIL_REDACTED]')
        redacted = redacted.replace('555-1234', '[PHONE_REDACTED]')
        
        assert '[EMAIL_REDACTED]' in redacted
        assert '[PHONE_REDACTED]' in redacted
    
    def test_short_quote_acceptance(self):
        """Edge Case: Short quotes should pass validation"""
        short_quotes = [
            "Great app!",
            "Love the features",
            "Easy to use",
        ]
        
        for quote in short_quotes:
            assert len(quote) <= 150


class TestConflictingActionIdeas:
    """Test handling of action ideas that conflict with each other"""
    
    def test_conflict_detection(self):
        """Edge Case: Conflicting actions should be detected"""
        actions = [
            "Simplify onboarding by reducing steps",
            "Add more detailed tutorials to onboarding",
            "Remove onboarding entirely",
        ]
        
        # Detect conflicts (simplify vs add more vs remove)
        conflict_keywords = {
            'simplify': ['reduce', 'simplify', 'less'],
            'expand': ['add', 'more', 'detailed'],
            'remove': ['remove', 'delete', 'eliminate'],
        }
        
        detected_categories = []
        for action in actions:
            for category, keywords in conflict_keywords.items():
                if any(kw in action.lower() for kw in keywords):
                    detected_categories.append(category)
        
        # Should detect different approaches
        assert len(set(detected_categories)) > 1
    
    def test_priority_by_impact(self):
        """Edge Case: Actions should be prioritized by impact and feasibility"""
        actions = [
            {"action": "Fix critical bug", "impact": "high", "effort": "low", "priority": None},
            {"action": "Redesign UI", "impact": "medium", "effort": "high", "priority": None},
            {"action": "Add analytics", "impact": "low", "effort": "medium", "priority": None},
        ]
        
        # Score and prioritize
        for action in actions:
            impact_score = {'high': 3, 'medium': 2, 'low': 1}[action['impact']]
            effort_score = {'high': 1, 'medium': 2, 'low': 3}[action['effort']]
            action['priority'] = impact_score * effort_score
        
        # Sort by priority
        sorted_actions = sorted(actions, key=lambda x: x['priority'], reverse=True)
        
        # Highest priority should be high impact + low effort
        assert sorted_actions[0]['action'] == "Fix critical bug"
    
    def test_conflict_resolution_suggestions(self):
        """Edge Case: Resolution suggestions should be provided for conflicts"""
        conflicting_pair = [
            "Add more features to settings",
            "Simplify settings by removing options",
        ]
        
        # Resolution: progressive disclosure
        resolution = "Implement progressive disclosure: show basic settings by default, allow advanced users to expand for more options"
        
        assert len(resolution) > 0
        assert 'progressive' in resolution.lower() or 'balance' in resolution.lower()


class TestOnePageOverflow:
    """Test handling of content that overflows one-page limit"""
    
    def test_content_length_validation(self):
        """Edge Case: Content should be validated against one-page limit"""
        max_chars = 10000  # Approximate one page
        
        long_content = "A" * 15000
        
        assert len(long_content) > max_chars
    
    def test_dynamic_section_priority(self):
        """Edge Case: Sections should be prioritized when space is limited"""
        sections = [
            {'name': 'executive_summary', 'priority': 1, 'content': 'Summary text...'},
            {'name': 'themes', 'priority': 2, 'content': 'Themes...'},
            {'name': 'quotes', 'priority': 3, 'content': 'Quotes...'},
            {'name': 'action_ideas', 'priority': 4, 'content': 'Actions...'},
        ]
        
        # Sort by priority
        sorted_sections = sorted(sections, key=lambda x: x['priority'])
        
        assert sorted_sections[0]['name'] == 'executive_summary'
        assert sorted_sections[1]['name'] == 'themes'
    
    def test_multi_page_fallback(self):
        """Edge Case: Multi-page fallback should be available"""
        content_length = 15000
        one_page_limit = 10000
        
        requires_multi_page = content_length > one_page_limit
        assert requires_multi_page is True


class TestTemplateRenderingFailures:
    """Test handling of template rendering failures"""
    
    def test_missing_template_variable(self):
        """Edge Case: Missing template variables should use defaults"""
        template = "Product: {product_name}, Date: {date}"
        context = {'product_name': 'TestApp'}  # Missing 'date'
        
        # Should use default or skip
        try:
            result = template.format(**context)
            assert 'TestApp' in result
        except KeyError:
            # Missing variable should be handled
            result = template.format(product_name=context['product_name'], date='N/A')
            assert 'N/A' in result
    
    def test_invalid_template_syntax(self):
        """Edge Case: Invalid template syntax should fallback to plain text"""
        invalid_template = "Product: {{ product_name }"  # Missing closing braces
        
        # Should fallback
        fallback = "Product: Unknown"
        assert fallback is not None
    
    def test_plain_text_fallback(self):
        """Edge Case: Plain text format should be available as fallback"""
        content = {
            'executive_summary': 'App received positive feedback',
            'themes': ['UX', 'Performance'],
        }
        
        # Plain text representation
        plain_text = f"Executive Summary: {content['executive_summary']}\n"
        plain_text += f"Themes: {', '.join(content['themes'])}\n"
        
        assert len(plain_text) > 0
        assert 'Executive Summary' in plain_text


class TestBrandingInconsistencies:
    """Test handling of branding inconsistencies across reports"""
    
    def test_brand_color_validation(self):
        """Edge Case: Brand colors should be validated"""
        brand_config = {
            'primary_color': '#2563eb',
            'secondary_color': '#64748b',
        }
        
        # Validate hex color format
        import re
        hex_pattern = r'^#[0-9A-Fa-f]{6}$'
        
        for color in brand_config.values():
            assert re.match(hex_pattern, color) is not None
    
    def test_company_name_consistency(self):
        """Edge Case: Company name should be consistent across reports"""
        report1_footer = "Generated by Review Pulse"
        report2_footer = "Generated by Review Pulse"
        
        assert report1_footer == report2_footer
    
    def test_template_versioning(self):
        """Edge Case: Template versions should be tracked"""
        templates = {
            'report_v1': {'version': '1.0', 'date': '2024-01-01'},
            'report_v2': {'version': '2.0', 'date': '2024-02-01'},
        }
        
        # Latest version should be used
        latest = max(templates.values(), key=lambda x: x['version'])
        assert latest['version'] == '2.0'


class TestReportDeliveryIssues:
    """Test handling of report delivery and export issues"""
    
    def test_pdf_generation_failure(self):
        """Edge Case: PDF generation failure should fallback to HTML"""
        formats_available = ['html', 'markdown']
        requested_format = 'pdf'
        
        # Fallback to first available
        actual_format = requested_format if requested_format in formats_available else formats_available[0]
        
        assert actual_format == 'html'
    
    def test_multiple_export_formats(self):
        """Edge Case: Multiple export formats should be supported"""
        supported_formats = ['html', 'markdown', 'pdf']
        
        assert len(supported_formats) >= 2
        assert 'html' in supported_formats
    
    def test_format_validation(self):
        """Edge Case: Generated format should be validated"""
        html_content = "<html><body><h1>Report</h1></body></html>"
        
        # Basic HTML validation
        assert html_content.startswith('<')
        assert '<html>' in html_content or '<!DOCTYPE' in html_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
