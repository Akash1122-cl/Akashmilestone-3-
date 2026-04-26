"""
Quality Assurance for Phase 4
Implements content validation, format consistency checks, and readability scoring
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class ValidationCheck:
    """Result of a single validation check"""
    check_name: str
    passed: bool
    message: str
    severity: str  # 'error', 'warning', 'info'


@dataclass
class QualityReport:
    """Quality assurance report for a generated report"""
    is_valid: bool
    overall_score: float
    content_checks: List[ValidationCheck]
    format_checks: List[ValidationCheck]
    readability_score: float
    completeness_score: float
    validation_timestamp: str
    metadata: Dict[str, Any]


class QualityAssurance:
    """Quality assurance for report validation"""
    
    def __init__(self, config: dict):
        self.config = config.get('quality_assurance', {})
        self.content_config = self.config.get('content_validation', {})
        self.format_config = self.config.get('format_validation', {})
        self.readability_config = self.config.get('readability', {})
        self.completeness_config = self.config.get('completeness', {})
        
        # Thresholds
        self.min_themes = self.content_config.get('min_themes', 3)
        self.max_themes = self.content_config.get('max_themes', 7)
        self.min_quotes_per_theme = self.content_config.get('min_quotes_per_theme', 2)
        self.max_quotes_per_theme = self.content_config.get('max_quotes_per_theme', 3)
        self.min_action_ideas = self.content_config.get('min_action_ideas', 2)
        self.max_action_ideas = self.content_config.get('max_action_ideas', 3)
        
        self.min_readability_score = self.readability_config.get('min_readability_score', 0.6)
        self.max_sentence_length = self.readability_config.get('max_sentence_length', 25)
        self.max_paragraph_length = self.readability_config.get('max_paragraph_length', 150)
    
    def validate_report(self, narrative_result: Dict, formatted_report: Dict) -> QualityReport:
        """
        Validate complete report for quality
        
        Args:
            narrative_result: Narrative result from NarrativeBuilder
            formatted_report: Formatted report from ReportFormatter
            
        Returns:
            QualityReport with validation results
        """
        try:
            logger.info("Starting quality assurance validation")
            
            content_checks = self._validate_content(narrative_result)
            format_checks = self._validate_format(formatted_report)
            readability_score = self._calculate_readability_score(narrative_result)
            completeness_score = self._calculate_completeness_score(narrative_result)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                content_checks, format_checks, readability_score, completeness_score
            )
            
            is_valid = overall_score >= 0.7
            
            result = QualityReport(
                is_valid=is_valid,
                overall_score=overall_score,
                content_checks=content_checks,
                format_checks=format_checks,
                readability_score=readability_score,
                completeness_score=completeness_score,
                validation_timestamp=datetime.utcnow().isoformat(),
                metadata={
                    'total_checks': len(content_checks) + len(format_checks),
                    'failed_checks': sum(1 for c in content_checks + format_checks if not c.passed)
                }
            )
            
            logger.info(f"Quality validation completed: valid={is_valid}, score={overall_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            raise
    
    def _validate_content(self, narrative_result: Dict) -> List[ValidationCheck]:
        """Validate content of narrative result"""
        checks = []
        
        # Check executive summary
        executive_summary = narrative_result.get('executive_summary', '')
        if not executive_summary or len(executive_summary) < 50:
            checks.append(ValidationCheck(
                check_name='executive_summary_length',
                passed=False,
                message='Executive summary is too short or missing',
                severity='error'
            ))
        else:
            checks.append(ValidationCheck(
                check_name='executive_summary_length',
                passed=True,
                message='Executive summary has appropriate length',
                severity='info'
            ))
        
        # Check themes count
        themes = narrative_result.get('themes', [])
        if len(themes) < self.min_themes:
            checks.append(ValidationCheck(
                check_name='themes_count',
                passed=False,
                message=f'Too few themes ({len(themes)} < {self.min_themes})',
                severity='error'
            ))
        elif len(themes) > self.max_themes:
            checks.append(ValidationCheck(
                check_name='themes_count',
                passed=False,
                message=f'Too many themes ({len(themes)} > {self.max_themes})',
                severity='warning'
            ))
        else:
            checks.append(ValidationCheck(
                check_name='themes_count',
                passed=True,
                message=f'Themes count is appropriate ({len(themes)})',
                severity='info'
            ))
        
        # Check quotes per theme
        for i, theme in enumerate(themes):
            quotes = theme.get('metadata', {}).get('quote_count', 0)
            if quotes < self.min_quotes_per_theme:
                checks.append(ValidationCheck(
                    check_name=f'theme_{i}_quotes',
                    passed=False,
                    message=f'Theme {i} has too few quotes ({quotes} < {self.min_quotes_per_theme})',
                    severity='warning'
                ))
        
        # Check action ideas
        action_ideas = narrative_result.get('action_ideas', [])
        if len(action_ideas) < self.min_action_ideas:
            checks.append(ValidationCheck(
                check_name='action_ideas_count',
                passed=False,
                message=f'Too few action idea sections ({len(action_ideas)} < {self.min_action_ideas})',
                severity='warning'
            ))
        
        return checks
    
    def _validate_format(self, formatted_report: Dict) -> List[ValidationCheck]:
        """Validate format of formatted report"""
        checks = []
        
        content = formatted_report.get('content', '')
        
        # Check content length
        if not content:
            checks.append(ValidationCheck(
                check_name='content_exists',
                passed=False,
                message='Report content is empty',
                severity='error'
            ))
            return checks
        
        # Check required sections
        required_sections = self.format_config.get('required_sections', [])
        for section in required_sections:
            section_lower = section.lower().replace('_', ' ')
            if section_lower not in content.lower():
                checks.append(ValidationCheck(
                    check_name=f'required_section_{section}',
                    passed=False,
                    message=f'Required section "{section}" not found in report',
                    severity='error'
                ))
        
        # Check format-specific validation
        format_type = formatted_report.get('format_type', 'html')
        if format_type == 'html':
            if not content.startswith('<!DOCTYPE html>') and not content.startswith('<html'):
                checks.append(ValidationCheck(
                    check_name='html_structure',
                    passed=False,
                    message='HTML document missing proper doctype or html tag',
                    severity='warning'
                ))
        
        return checks
    
    def _calculate_readability_score(self, narrative_result: Dict) -> float:
        """Calculate readability score based on text analysis"""
        try:
            score = 1.0
            total_sentences = 0
            long_sentences = 0
            
            # Analyze executive summary
            executive_summary = narrative_result.get('executive_summary', '')
            sentences = re.split(r'[.!?]+', executive_summary)
            total_sentences += len(sentences)
            long_sentences += sum(1 for s in sentences if len(s.split()) > self.max_sentence_length)
            
            # Analyze theme descriptions
            for theme in narrative_result.get('themes', []):
                content = theme.get('content', '')
                sentences = re.split(r'[.!?]+', content)
                total_sentences += len(sentences)
                long_sentences += sum(1 for s in sentences if len(s.split()) > self.max_sentence_length)
            
            # Calculate penalty for long sentences
            if total_sentences > 0:
                long_sentence_ratio = long_sentences / total_sentences
                score -= long_sentence_ratio * 0.3
            
            # Ensure score is within bounds
            score = max(0.0, min(1.0, score))
            
            return score
            
        except Exception as e:
            logger.error(f"Failed to calculate readability score: {e}")
            return 0.5
    
    def _calculate_completeness_score(self, narrative_result: Dict) -> float:
        """Calculate completeness score based on required elements"""
        try:
            score = 0.0
            total_requirements = 0
            
            # Check executive summary
            total_requirements += 1
            if narrative_result.get('executive_summary'):
                score += 1
            
            # Check themes
            total_requirements += 1
            if narrative_result.get('themes') and len(narrative_result.get('themes', [])) > 0:
                score += 1
            
            # Check quotes
            total_requirements += 1
            if narrative_result.get('quotes') and len(narrative_result.get('quotes', [])) > 0:
                score += 1
            
            # Check action ideas
            total_requirements += 1
            if narrative_result.get('action_ideas') and len(narrative_result.get('action_ideas', [])) > 0:
                score += 1
            
            # Check impact analysis
            total_requirements += 1
            if narrative_result.get('impact_analysis'):
                score += 1
            
            return score / total_requirements if total_requirements > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate completeness score: {e}")
            return 0.5
    
    def _calculate_overall_score(self, content_checks: List[ValidationCheck],
                                 format_checks: List[ValidationCheck],
                                 readability_score: float,
                                 completeness_score: float) -> float:
        """Calculate overall quality score"""
        try:
            # Content score (40%)
            content_passed = sum(1 for c in content_checks if c.passed)
            content_score = (content_passed / len(content_checks)) if content_checks else 1.0
            
            # Format score (30%)
            format_passed = sum(1 for c in format_checks if c.passed)
            format_score = (format_passed / len(format_checks)) if format_checks else 1.0
            
            # Overall score
            overall_score = (
                0.4 * content_score +
                0.3 * format_score +
                0.15 * readability_score +
                0.15 * completeness_score
            )
            
            return overall_score
            
        except Exception as e:
            logger.error(f"Failed to calculate overall score: {e}")
            return 0.5
    
    def validate_single_section(self, section_name: str, content: str) -> List[ValidationCheck]:
        """Validate a single section of the report"""
        checks = []
        
        # Check section length
        if len(content) < 10:
            checks.append(ValidationCheck(
                check_name=f'{section_name}_length',
                passed=False,
                message=f'Section "{section_name}" is too short',
                severity='error'
            ))
        
        # Check for placeholder text
        placeholders = ['placeholder', 'no description', 'no summary', 'to be filled']
        if any(ph in content.lower() for ph in placeholders):
            checks.append(ValidationCheck(
                check_name=f'{section_name}_placeholder',
                passed=False,
                message=f'Section "{section_name}" contains placeholder text',
                severity='warning'
            ))
        
        return checks


# Factory function
def create_quality_assurance(config: dict) -> QualityAssurance:
    """Create QualityAssurance instance"""
    return QualityAssurance(config)
