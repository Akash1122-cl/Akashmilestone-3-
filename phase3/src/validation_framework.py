"""
Validation Framework for Phase 3
Implements quote verification, theme consistency checking, and quality scoring
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

# Try to import fuzzy matching library
try:
    from rapidfuzz import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    logging.warning("RapidFuzz not available, using basic string matching")

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result from validation operation"""
    is_valid: bool
    quote_accuracy_score: float
    theme_coherence_score: float
    action_relevance_score: float
    overall_quality_score: float
    validation_errors: List[str]
    validation_warnings: List[str]
    metadata: Dict


class ValidationFramework:
    """Validation framework for ensuring analysis quality"""
    
    def __init__(self, config: dict):
        self.config = config.get('validation', {})
        self.quote_config = self.config.get('quote_verification', {})
        self.consistency_config = self.config.get('theme_consistency', {})
        self.quality_config = self.config.get('quality_scoring', {})
        
        self.fuzzy_threshold = self.quote_config.get('fuzzy_match_threshold', 0.85)
        self.max_quote_length = self.quote_config.get('max_quote_length', 200)
        self.min_similarity_threshold = self.consistency_config.get('min_similarity_threshold', 0.6)
        self.quality_weights = self.quality_config.get('weights', {
            'quote_accuracy': 0.4,
            'theme_coherence': 0.3,
            'action_relevance': 0.3
        })
        self.min_quality_score = self.quality_config.get('min_quality_score', 0.7)
    
    def validate_analysis(self, themes: List[Dict], 
                         reviews: List[Dict]) -> ValidationResult:
        """
        Validate complete analysis results
        
        Args:
            themes: List of theme dictionaries
            reviews: List of review data
            
        Returns:
            ValidationResult with validation scores and errors
        """
        try:
            logger.info(f"Validating {len(themes)} themes against {len(reviews)} reviews")
            
            validation_errors = []
            validation_warnings = []
            
            # Validate quotes
            quote_accuracy_score = self._validate_quotes(themes, reviews, validation_errors)
            
            # Validate theme consistency
            theme_coherence_score = self._validate_theme_consistency(
                themes, reviews, validation_warnings
            )
            
            # Validate action ideas
            action_relevance_score = self._validate_action_ideas(
                themes, validation_warnings
            )
            
            # Calculate overall quality score
            overall_quality_score = (
                self.quality_weights['quote_accuracy'] * quote_accuracy_score +
                self.quality_weights['theme_coherence'] * theme_coherence_score +
                self.quality_weights['action_relevance'] * action_relevance_score
            )
            
            is_valid = overall_quality_score >= self.min_quality_score
            
            if not is_valid:
                validation_errors.append(
                    f"Overall quality score {overall_quality_score:.2f} below threshold {self.min_quality_score}"
                )
            
            result = ValidationResult(
                is_valid=is_valid,
                quote_accuracy_score=quote_accuracy_score,
                theme_coherence_score=theme_coherence_score,
                action_relevance_score=action_relevance_score,
                overall_quality_score=overall_quality_score,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                metadata={
                    'validation_timestamp': datetime.utcnow().isoformat(),
                    'themes_validated': len(themes),
                    'reviews_validated': len(reviews)
                }
            )
            
            logger.info(f"Validation completed: valid={is_valid}, "
                       f"quality_score={overall_quality_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                quote_accuracy_score=0.0,
                theme_coherence_score=0.0,
                action_relevance_score=0.0,
                overall_quality_score=0.0,
                validation_errors=[f"Validation exception: {str(e)}"],
                validation_warnings=[],
                metadata={}
            )
    
    def _validate_quotes(self, themes: List[Dict], 
                        reviews: List[Dict],
                        errors: List[str]) -> float:
        """
        Validate that quotes appear in actual reviews
        
        Args:
            themes: List of theme dictionaries
            reviews: List of review data
            errors: List to append validation errors to
            
        Returns:
            Quote accuracy score (0-1)
        """
        if not self.quote_config.get('enabled', True):
            return 1.0
        
        try:
            total_quotes = 0
            verified_quotes = 0
            
            # Build review text index for fast lookup
            review_texts = [r.get('text', '') for r in reviews]
            
            for theme in themes:
                quotes = theme.get('representative_quotes', [])
                for quote in quotes:
                    total_quotes += 1
                    
                    # Check quote length
                    if len(quote) > self.max_quote_length:
                        errors.append(f"Quote too long ({len(quote)} chars): {quote[:50]}...")
                        continue
                    
                    # Verify quote exists in reviews
                    if self._verify_quote_in_reviews(quote, review_texts):
                        verified_quotes += 1
                    else:
                        errors.append(f"Quote not found in reviews: {quote[:50]}...")
            
            if total_quotes == 0:
                logger.warning("No quotes to validate")
                return 1.0
            
            accuracy_score = verified_quotes / total_quotes
            logger.info(f"Quote verification: {verified_quotes}/{total_quotes} verified "
                       f"({accuracy_score:.2%})")
            
            return accuracy_score
            
        except Exception as e:
            logger.error(f"Quote validation failed: {e}")
            errors.append(f"Quote validation exception: {str(e)}")
            return 0.0
    
    def _verify_quote_in_reviews(self, quote: str, 
                                 review_texts: List[str]) -> bool:
        """
        Verify that a quote appears in the review texts
        
        Args:
            quote: The quote to verify
            review_texts: List of review texts
            
        Returns:
            True if quote is found, False otherwise
        """
        try:
            # Normalize quote for comparison
            normalized_quote = self._normalize_text(quote)
            
            if FUZZY_AVAILABLE:
                # Use fuzzy matching
                for review_text in review_texts:
                    normalized_review = self._normalize_text(review_text)
                    
                    # Check if quote is a substring of review
                    if normalized_quote in normalized_review:
                        return True
                    
                    # Check fuzzy match for partial matches
                    if len(normalized_quote) > 20:
                        ratio = fuzz.partial_ratio(normalized_quote, normalized_review)
                        if ratio >= self.fuzzy_threshold * 100:
                            return True
            else:
                # Use basic substring matching
                for review_text in review_texts:
                    if normalized_quote in self._normalize_text(review_text):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Quote verification failed: {e}")
            return False
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters (keep letters, numbers, spaces)
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.strip()
    
    def _validate_theme_consistency(self, themes: List[Dict], 
                                    reviews: List[Dict],
                                    warnings: List[str]) -> float:
        """
        Validate theme consistency and coherence
        
        Args:
            themes: List of theme dictionaries
            reviews: List of review data
            warnings: List to append validation warnings to
            
        Returns:
            Theme coherence score (0-1)
        """
        if not self.consistency_config.get('enabled', True):
            return 1.0
        
        try:
            if len(themes) == 0:
                warnings.append("No themes to validate")
                return 0.0
            
            coherence_score = 0.0
            total_checks = 0
            
            # Check theme names are unique
            theme_names = [t.get('name', '') for t in themes]
            unique_names = set(theme_names)
            if len(theme_names) != len(unique_names):
                warnings.append(f"Duplicate theme names found")
                coherence_score -= 0.2
            total_checks += 1
            
            # Check each theme has required fields
            for theme in themes:
                if not theme.get('name'):
                    warnings.append(f"Theme missing name: {theme.get('theme_id', 'unknown')}")
                    coherence_score -= 0.1
                
                if not theme.get('description'):
                    warnings.append(f"Theme missing description: {theme.get('theme_id', 'unknown')}")
                    coherence_score -= 0.1
                
                if not theme.get('representative_quotes'):
                    warnings.append(f"Theme has no quotes: {theme.get('theme_id', 'unknown')}")
                    coherence_score -= 0.1
                
                total_checks += 1
            
            # Normalize score
            if total_checks > 0:
                coherence_score = max(0.0, min(1.0, coherence_score / total_checks + 0.5))
            
            logger.info(f"Theme coherence score: {coherence_score:.2f}")
            return coherence_score
            
        except Exception as e:
            logger.error(f"Theme consistency validation failed: {e}")
            warnings.append(f"Theme consistency validation exception: {str(e)}")
            return 0.0
    
    def _validate_action_ideas(self, themes: List[Dict], 
                              warnings: List[str]) -> float:
        """
        Validate action ideas relevance and quality
        
        Args:
            themes: List of theme dictionaries
            warnings: List to append validation warnings to
            
        Returns:
            Action relevance score (0-1)
        """
        try:
            if len(themes) == 0:
                return 1.0
            
            relevance_score = 0.0
            total_themes = len(themes)
            
            for theme in themes:
                action_ideas = theme.get('action_ideas', [])
                
                # Check if action ideas exist
                if not action_ideas:
                    warnings.append(f"Theme has no action ideas: {theme.get('theme_id', 'unknown')}")
                    continue
                
                # Check action idea quality
                valid_actions = 0
                for action in action_ideas:
                    if len(action) > 10 and len(action) < 200:
                        valid_actions += 1
                
                if valid_actions > 0:
                    relevance_score += valid_actions / len(action_ideas)
                else:
                    warnings.append(f"Theme has poor quality action ideas: {theme.get('theme_id', 'unknown')}")
            
            # Normalize score
            if total_themes > 0:
                relevance_score = relevance_score / total_themes
            
            logger.info(f"Action relevance score: {relevance_score:.2f}")
            return relevance_score
            
        except Exception as e:
            logger.error(f"Action idea validation failed: {e}")
            warnings.append(f"Action idea validation exception: {str(e)}")
            return 0.0
    
    def validate_single_theme(self, theme: Dict, 
                             cluster_reviews: List[Dict]) -> ValidationResult:
        """
        Validate a single theme against its cluster reviews
        
        Args:
            theme: Theme dictionary
            cluster_reviews: Reviews in the theme's cluster
            
        Returns:
            ValidationResult for the theme
        """
        try:
            validation_errors = []
            validation_warnings = []
            
            # Validate quotes
            quote_accuracy = self._validate_quotes([theme], cluster_reviews, validation_errors)
            
            # Basic theme validation
            theme_coherence = 1.0
            if not theme.get('name'):
                validation_errors.append("Theme missing name")
                theme_coherence -= 0.5
            
            if not theme.get('description'):
                validation_warnings.append("Theme missing description")
                theme_coherence -= 0.3
            
            # Validate action ideas
            action_relevance = self._validate_action_ideas([theme], validation_warnings)
            
            # Calculate overall score
            overall_score = (
                self.quality_weights['quote_accuracy'] * quote_accuracy +
                self.quality_weights['theme_coherence'] * theme_coherence +
                self.quality_weights['action_relevance'] * action_relevance
            )
            
            return ValidationResult(
                is_valid=overall_score >= self.min_quality_score,
                quote_accuracy_score=quote_accuracy,
                theme_coherence_score=theme_coherence,
                action_relevance_score=action_relevance,
                overall_quality_score=overall_score,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                metadata={'theme_id': theme.get('theme_id', 'unknown')}
            )
            
        except Exception as e:
            logger.error(f"Single theme validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                quote_accuracy_score=0.0,
                theme_coherence_score=0.0,
                action_relevance_score=0.0,
                overall_quality_score=0.0,
                validation_errors=[f"Validation exception: {str(e)}"],
                validation_warnings=[],
                metadata={}
            )


# Factory function
def create_validation_framework(config: dict) -> ValidationFramework:
    """Create ValidationFramework instance"""
    return ValidationFramework(config)
