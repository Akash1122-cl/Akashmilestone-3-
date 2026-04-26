"""
Report Formatter for Phase 4
Implements report formatting for one-page layouts with multiple output formats
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from jinja2 import Environment, FileSystemLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("Jinja2 not available, using basic formatting")

logger = logging.getLogger(__name__)


@dataclass
class FormattedReport:
    """Represents a formatted report"""
    content: str
    format_type: str
    generation_timestamp: str
    processing_time_seconds: float
    metadata: Dict[str, Any]


class ReportFormatter:
    """Report formatter for one-page layouts with multiple output formats"""
    
    def __init__(self, config: dict):
        self.config = config.get('report_formatter', {})
        self.output_formats = self.config.get('output_formats', ['html', 'markdown'])
        self.layout_config = self.config.get('layout', {})
        self.sections_order = self.config.get('sections', [])
        self.branding = self.config.get('branding', {})
        
        self.max_pages = self.layout_config.get('max_pages', 1)
        self.font_family = self.layout_config.get('font_family', 'Arial')
        self.font_size = self.layout_config.get('font_size', 11)
        self.line_height = self.layout_config.get('line_height', 1.5)
        self.margin = self.layout_config.get('margin', '0.5in')
        
        self.jinja_env = None
        self.mock_mode = False
        
        if JINJA2_AVAILABLE:
            try:
                import os
                template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
                self.jinja_env = Environment(
                    loader=FileSystemLoader(template_dir),
                    autoescape=True
                )
                logger.info("Jinja2 environment initialized for report formatting")
            except Exception as e:
                logger.error(f"Failed to initialize Jinja2: {e}")
                self.mock_mode = True
        else:
            logger.info("Using mock report formatter mode")
            self.mock_mode = True
    
    def format_report(self, narrative_result: Dict, output_format: str = 'html') -> FormattedReport:
        """
        Format narrative result into a complete report
        
        Args:
            narrative_result: Narrative result from NarrativeBuilder
            output_format: Output format (html, markdown, pdf)
            
        Returns:
            FormattedReport with formatted content
        """
        import time
        start_time = time.time()
        
        try:
            logger.info(f"Formatting report in {output_format} format")
            
            if output_format not in self.output_formats:
                logger.warning(f"Unsupported format {output_format}, falling back to html")
                output_format = 'html'
            
            # Format based on output type
            if output_format == 'html':
                content = self._format_html(narrative_result)
            elif output_format == 'markdown':
                content = self._format_markdown(narrative_result)
            elif output_format == 'pdf':
                content = self._format_pdf(narrative_result)
            else:
                content = self._format_html(narrative_result)
            
            processing_time = time.time() - start_time
            
            result = FormattedReport(
                content=content,
                format_type=output_format,
                generation_timestamp=datetime.utcnow().isoformat(),
                processing_time_seconds=processing_time,
                metadata={
                    'sections_count': len(narrative_result.get('themes', [])),
                    'mock_mode': self.mock_mode
                }
            )
            
            logger.info(f"Report formatted in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to format report: {e}")
            raise
    
    def _format_html(self, narrative_result: Dict) -> str:
        """Format report as HTML"""
        try:
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Review Report</title>
    <style>
        body {{
            font-family: {self.font_family};
            font-size: {self.font_size}px;
            line-height: {self.line_height};
            margin: {self.margin};
            max-width: 800px;
        }}
        h1 {{ color: {self.branding.get('primary_color', '#2563eb')}; }}
        h2 {{ color: {self.branding.get('secondary_color', '#64748b')}; }}
        .theme {{ margin: 20px 0; padding: 15px; background: #f8fafc; border-left: 4px solid {self.branding.get('primary_color', '#2563eb')}; }}
        .quote {{ font-style: italic; color: #555; margin: 10px 0; }}
        .action {{ margin: 10px 0; padding: 10px; background: #ecfdf5; }}
        .executive-summary {{ background: #eff6ff; padding: 20px; margin: 20px 0; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>Weekly Product Review Report</h1>
    <p><strong>Generated:</strong> {narrative_result.get('generation_timestamp', 'N/A')}</p>
"""
            
            # Executive Summary
            html += f"""
    <div class="executive-summary">
        <h2>Executive Summary</h2>
        <p>{narrative_result.get('executive_summary', 'No summary available.')}</p>
    </div>
"""
            
            # Themes
            html += "<h2>Key Themes</h2>\n"
            for theme in narrative_result.get('themes', []):
                html += f"""
    <div class="theme">
        <h3>{theme.get('section_name', 'Theme')}</h3>
        <p>{theme.get('content', '')}</p>
    </div>
"""
            
            # Quotes
            html += "<h2>Representative Quotes</h2>\n"
            for quote_section in narrative_result.get('quotes', []):
                html += f"""
    <div class="theme">
        <h3>{quote_section.get('section_name', 'Quotes')}</h3>
        <div class="quote">{quote_section.get('content', '')}</div>
    </div>
"""
            
            # Action Ideas
            html += "<h2>Action Ideas</h2>\n"
            for action_section in narrative_result.get('action_ideas', []):
                html += f"""
    <div class="action">
        <h3>{action_section.get('section_name', 'Actions')}</h3>
        <p>{action_section.get('content', '')}</p>
    </div>
"""
            
            # Impact Analysis
            html += f"""
    <h2>Impact Analysis</h2>
    <div class="theme">
        {narrative_result.get('impact_analysis', 'No impact analysis available.')}
    </div>
    
    <hr>
    <p style="font-size: 10px; color: #888;">Generated by Review Pulse</p>
</body>
</html>
"""
            
            return html
            
        except Exception as e:
            logger.error(f"Failed to format HTML: {e}")
            return self._format_fallback(narrative_result)
    
    def _format_markdown(self, narrative_result: Dict) -> str:
        """Format report as Markdown"""
        try:
            md = f"""# Weekly Product Review Report

**Generated:** {narrative_result.get('generation_timestamp', 'N/A')}

---

## Executive Summary

{narrative_result.get('executive_summary', 'No summary available.')}

---

## Key Themes

"""
            
            for theme in narrative_result.get('themes', []):
                md += f"### {theme.get('section_name', 'Theme')}\n\n"
                md += f"{theme.get('content', '')}\n\n"
            
            md += "## Representative Quotes\n\n"
            
            for quote_section in narrative_result.get('quotes', []):
                md += f"### {quote_section.get('section_name', 'Quotes')}\n\n"
                md += f"{quote_section.get('content', '')}\n\n"
            
            md += "## Action Ideas\n\n"
            
            for action_section in narrative_result.get('action_ideas', []):
                md += f"### {action_section.get('section_name', 'Actions')}\n\n"
                md += f"{action_section.get('content', '')}\n\n"
            
            md += f"## Impact Analysis\n\n"
            md += f"{narrative_result.get('impact_analysis', 'No impact analysis available.')}\n\n"
            md += "---\n\n*Generated by Review Pulse*\n"
            
            return md
            
        except Exception as e:
            logger.error(f"Failed to format Markdown: {e}")
            return self._format_fallback(narrative_result)
    
    def _format_pdf(self, narrative_result: Dict) -> str:
        """Format report as PDF (placeholder - requires additional libraries)"""
        # PDF generation would require libraries like weasyprint or reportlab
        # For now, return HTML as a placeholder
        logger.warning("PDF format not fully implemented, returning HTML")
        return self._format_html(narrative_result)
    
    def _format_fallback(self, narrative_result: Dict) -> str:
        """Fallback formatting if specific format fails"""
        return str(narrative_result)
    
    def validate_one_page_layout(self, content: str) -> bool:
        """Validate that content fits on one page"""
        try:
            # Simple validation: check character count
            max_chars = 10000  # Approximate one page limit
            return len(content) <= max_chars
        except Exception as e:
            logger.error(f"Failed to validate layout: {e}")
            return False
    
    def apply_branding(self, content: str, format_type: str) -> str:
        """Apply branding to formatted content"""
        try:
            if format_type == 'html':
                # Branding is already applied in HTML formatting
                return content
            else:
                # Add branding footer
                footer = f"\n\n---\n*Generated by {self.branding.get('company_name', 'Review Pulse')}*"
                return content + footer
        except Exception as e:
            logger.error(f"Failed to apply branding: {e}")
            return content


# Factory function
def create_report_formatter(config: dict) -> ReportFormatter:
    """Create ReportFormatter instance"""
    return ReportFormatter(config)
