"""
Data Quality Pipeline for Phase 2
Handles validation, quality metrics, and anomaly detection for review data
"""

import logging
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
import re
from enum import Enum

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality levels for reviews"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    VERY_POOR = "very_poor"


class AnomalyType(Enum):
    """Types of anomalies to detect"""
    RATING_SPIKE = "rating_spike"
    TEXT_LENGTH_ANOMALY = "text_length_anomaly"
    SENTIMENT_ANOMALY = "sentiment_anomaly"
    DUPLICATE_PATTERN = "duplicate_pattern"
    SPAM_PATTERN = "spam_pattern"
    BOT_PATTERN = "bot_pattern"


@dataclass
class QualityMetrics:
    """Quality metrics for a batch of reviews"""
    total_reviews: int
    processed_reviews: int
    success_rate: float
    average_quality_score: float
    quality_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    rating_distribution: Dict[int, int]
    sentiment_distribution: Dict[str, int]
    text_length_stats: Dict[str, float]
    word_count_stats: Dict[str, float]
    duplicate_rate: float
    spam_rate: float
    anomaly_count: int
    processing_time: float


@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    description: str
    affected_reviews: List[str]
    confidence: float
    detected_at: datetime
    recommendations: List[str]


class DataQualityPipeline:
    """Pipeline for data quality assessment and anomaly detection"""
    
    def __init__(self, config: dict):
        self.config = config.get('quality_pipeline', {})
        self.quality_thresholds = self.config.get('quality_thresholds', {
            'excellent': 0.8,
            'good': 0.6,
            'acceptable': 0.4,
            'poor': 0.2
        })
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = self.config.get('anomaly_thresholds', {
            'rating_spike_threshold': 3.0,  # Standard deviations
            'text_length_min': 10,
            'text_length_max': 2000,
            'sentiment_threshold': 0.8,
            'duplicate_similarity_threshold': 0.9,
            'spam_keywords_threshold': 0.3,
            'bot_pattern_threshold': 0.7
        })
        
        # Spam detection patterns
        self.spam_patterns = [
            r'click here',
            r'buy now',
            r'free money',
            r'get rich',
            r'guaranteed',
            r'limited time',
            r'act now',
            r'!!!{3,}',  # Multiple exclamation marks
            r'\${2,}',    # Multiple dollar signs
            r'http[s]?://',  # URLs
        ]
        
        # Bot detection patterns
        self.bot_patterns = [
            r'^[A-Z][a-z]+[0-9]+$',  # Generic username with numbers
            r'^user[0-9]+',          # Generic user prefix
            r'^test[0-9]+',          # Test user pattern
            r'^guest[0-9]+',         # Guest user pattern
        ]
        
        # Compile regex patterns
        self.spam_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.spam_patterns]
        self.bot_regex = [re.compile(pattern) for pattern in self.bot_patterns]
        
        logger.info("DataQualityPipeline initialized")
    
    def calculate_quality_score(self, review: Dict) -> float:
        """Calculate quality score for a single review"""
        score = 0.0
        max_score = 10.0
        
        # Text length factor (0-2 points)
        text_length = len(review.get('cleaned_text', ''))
        if 50 <= text_length <= 500:
            score += 2.0
        elif 20 <= text_length < 50 or 500 < text_length <= 1000:
            score += 1.5
        elif 10 <= text_length < 20 or 1000 < text_length <= 2000:
            score += 1.0
        elif text_length >= 10:
            score += 0.5
        
        # Word count factor (0-1.5 points)
        word_count = review.get('word_count', 0)
        if 10 <= word_count <= 100:
            score += 1.5
        elif 5 <= word_count < 10 or 100 < word_count <= 200:
            score += 1.0
        elif word_count >= 5:
            score += 0.5
        
        # Language factor (0-1 point)
        if review.get('language') == 'en':
            score += 1.0
        
        # Sentiment consistency (0-1 point)
        rating = review.get('rating', 0)
        sentiment = review.get('sentiment_score', 0)
        if rating >= 4 and sentiment > 0.5:
            score += 1.0
        elif rating <= 2 and sentiment < -0.5:
            score += 1.0
        elif rating == 3 and -0.2 <= sentiment <= 0.2:
            score += 1.0
        elif sentiment is not None:
            score += 0.5
        
        # Content diversity (0-1 point)
        text = review.get('cleaned_text', '')
        if text:
            unique_words = len(set(text.lower().split()))
            total_words = len(text.split())
            if total_words > 0:
                diversity = unique_words / total_words
                score += diversity
        
        # No spam indicators (0-1.5 points)
        spam_score = self.detect_spam_indicators(text)
        score += max(0, 1.5 - spam_score)
        
        # No bot indicators (0-1 point)
        bot_score = self.detect_bot_indicators(review.get('author_name', ''))
        score += max(0, 1.0 - bot_score)
        
        # Rating reasonableness (0-1 point)
        if 1 <= rating <= 5:
            score += 1.0
        
        return min(score / max_score, 1.0)
    
    def detect_spam_indicators(self, text: str) -> float:
        """Detect spam indicators in text (0-1 scale)"""
        if not text:
            return 0.0
        
        spam_score = 0.0
        text_lower = text.lower()
        
        # Check for spam patterns
        pattern_matches = 0
        for pattern in self.spam_regex:
            if pattern.search(text_lower):
                pattern_matches += 1
        
        # Calculate spam score based on pattern matches
        if pattern_matches > 0:
            spam_score += min(pattern_matches * 0.2, 0.6)
        
        # Check for excessive capitalization
        upper_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
        if upper_ratio > 0.3:
            spam_score += 0.3
        
        # Check for repetitive characters
        if re.search(r'(.)\1{3,}', text):
            spam_score += 0.1
        
        return min(spam_score, 1.0)
    
    def detect_bot_indicators(self, author_name: str) -> float:
        """Detect bot indicators in author name (0-1 scale)"""
        if not author_name:
            return 0.0
        
        bot_score = 0.0
        
        # Check for bot patterns
        for pattern in self.bot_regex:
            if pattern.match(author_name):
                bot_score += 0.3
        
        # Check for generic patterns
        if re.match(r'^[A-Za-z]+\d+$', author_name):
            bot_score += 0.4
        
        # Check for all lowercase or all uppercase
        if author_name.islower() or author_name.isupper():
            bot_score += 0.2
        
        return min(bot_score, 1.0)
    
    def get_quality_level(self, score: float) -> QualityLevel:
        """Get quality level from score"""
        if score >= self.quality_thresholds['excellent']:
            return QualityLevel.EXCELLENT
        elif score >= self.quality_thresholds['good']:
            return QualityLevel.GOOD
        elif score >= self.quality_thresholds['acceptable']:
            return QualityLevel.ACCEPTABLE
        elif score >= self.quality_thresholds['poor']:
            return QualityLevel.POOR
        else:
            return QualityLevel.VERY_POOR
    
    def detect_rating_anomalies(self, reviews: List[Dict]) -> List[AnomalyDetection]:
        """Detect rating anomalies"""
        anomalies = []
        
        if len(reviews) < 10:
            return anomalies
        
        ratings = [r.get('rating', 0) for r in reviews if r.get('rating')]
        if len(ratings) < 5:
            return anomalies
        
        # Calculate statistics
        mean_rating = statistics.mean(ratings)
        std_rating = statistics.stdev(ratings) if len(ratings) > 1 else 0
        
        # Detect spikes
        threshold = self.anomaly_thresholds['rating_spike_threshold']
        for review in reviews:
            rating = review.get('rating', 0)
            if rating > 0:
                z_score = abs(rating - mean_rating) / std_rating if std_rating > 0 else 0
                if z_score > threshold:
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.RATING_SPIKE,
                        severity="high" if z_score > threshold * 1.5 else "medium",
                        description=f"Rating {rating} is {z_score:.1f} standard deviations from mean",
                        affected_reviews=[review.get('external_review_id', '')],
                        confidence=min(z_score / threshold, 1.0),
                        detected_at=datetime.utcnow(),
                        recommendations=["Review this review for authenticity", "Check for review manipulation"]
                    ))
        
        return anomalies
    
    def detect_text_length_anomalies(self, reviews: List[Dict]) -> List[AnomalyDetection]:
        """Detect text length anomalies"""
        anomalies = []
        
        min_length = self.anomaly_thresholds['text_length_min']
        max_length = self.anomaly_thresholds['text_length_max']
        
        for review in reviews:
            text_length = len(review.get('cleaned_text', ''))
            
            if text_length < min_length:
                anomalies.append(AnomalyDetection(
                    anomaly_type=AnomalyType.TEXT_LENGTH_ANOMALY,
                    severity="medium",
                    description=f"Text too short: {text_length} characters",
                    affected_reviews=[review.get('external_review_id', '')],
                    confidence=0.8,
                    detected_at=datetime.utcnow(),
                    recommendations=["Consider filtering very short reviews", "May indicate low-quality content"]
                ))
            elif text_length > max_length:
                anomalies.append(AnomalyDetection(
                    anomaly_type=AnomalyType.TEXT_LENGTH_ANOMALY,
                    severity="low",
                    description=f"Text unusually long: {text_length} characters",
                    affected_reviews=[review.get('external_review_id', '')],
                    confidence=0.6,
                    detected_at=datetime.utcnow(),
                    recommendations=["Review for potential spam", "Check for automated content"]
                ))
        
        return anomalies
    
    def detect_sentiment_anomalies(self, reviews: List[Dict]) -> List[AnomalyDetection]:
        """Detect sentiment anomalies"""
        anomalies = []
        
        threshold = self.anomaly_thresholds['sentiment_threshold']
        
        for review in reviews:
            rating = review.get('rating', 0)
            sentiment = review.get('sentiment_score')
            
            if sentiment is not None and rating > 0:
                # Check for rating-sentiment mismatch
                if rating >= 4 and sentiment < -threshold:
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.SENTIMENT_ANOMALY,
                        severity="medium",
                        description=f"High rating ({rating}) with negative sentiment ({sentiment:.2f})",
                        affected_reviews=[review.get('external_review_id', '')],
                        confidence=abs(sentiment),
                        detected_at=datetime.utcnow(),
                        recommendations=["Review for sarcasm or irony", "Check sentiment analysis accuracy"]
                    ))
                elif rating <= 2 and sentiment > threshold:
                    anomalies.append(AnomalyDetection(
                        anomaly_type=AnomalyType.SENTIMENT_ANOMALY,
                        severity="medium",
                        description=f"Low rating ({rating}) with positive sentiment ({sentiment:.2f})",
                        affected_reviews=[review.get('external_review_id', '')],
                        confidence=sentiment,
                        detected_at=datetime.utcnow(),
                        recommendations=["Review for complex sentiment", "Check for mixed feelings"]
                    ))
        
        return anomalies
    
    def detect_spam_patterns(self, reviews: List[Dict]) -> List[AnomalyDetection]:
        """Detect spam patterns"""
        anomalies = []
        
        spam_reviews = []
        for review in reviews:
            spam_score = self.detect_spam_indicators(review.get('cleaned_text', ''))
            if spam_score > self.anomaly_thresholds['spam_keywords_threshold']:
                spam_reviews.append(review.get('external_review_id', ''))
        
        if spam_reviews:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.SPAM_PATTERN,
                severity="high",
                description=f"Detected {len(spam_reviews)} potentially spam reviews",
                affected_reviews=spam_reviews,
                confidence=0.8,
                detected_at=datetime.utcnow(),
                recommendations=["Remove spam reviews", "Implement stronger spam filters"]
            ))
        
        return anomalies
    
    def detect_bot_patterns(self, reviews: List[Dict]) -> List[AnomalyDetection]:
        """Detect bot patterns"""
        anomalies = []
        
        bot_reviews = []
        for review in reviews:
            bot_score = self.detect_bot_indicators(review.get('author_name', ''))
            if bot_score > self.anomaly_thresholds['bot_pattern_threshold']:
                bot_reviews.append(review.get('external_review_id', ''))
        
        if bot_reviews:
            anomalies.append(AnomalyDetection(
                anomaly_type=AnomalyType.BOT_PATTERN,
                severity="medium",
                description=f"Detected {len(bot_reviews)} potentially bot-generated reviews",
                affected_reviews=bot_reviews,
                confidence=0.7,
                detected_at=datetime.utcnow(),
                recommendations=["Review bot accounts", "Implement CAPTCHA verification"]
            ))
        
        return anomalies
    
    def calculate_batch_metrics(self, reviews: List[Dict]) -> QualityMetrics:
        """Calculate quality metrics for a batch of reviews"""
        start_time = datetime.utcnow()
        
        total_reviews = len(reviews)
        processed_reviews = [r for r in reviews if r.get('status') == 'success']
        
        # Calculate quality scores
        quality_scores = []
        quality_distribution = defaultdict(int)
        
        for review in processed_reviews:
            score = self.calculate_quality_score(review)
            quality_scores.append(score)
            level = self.get_quality_level(score)
            quality_distribution[level.value] += 1
        
        # Calculate distributions
        language_distribution = Counter(r.get('language', 'unknown') for r in processed_reviews)
        rating_distribution = Counter(r.get('rating', 0) for r in processed_reviews)
        
        sentiment_distribution = defaultdict(int)
        for review in processed_reviews:
            sentiment = review.get('sentiment_score')
            if sentiment is not None:
                if sentiment > 0.2:
                    sentiment_distribution['positive'] += 1
                elif sentiment < -0.2:
                    sentiment_distribution['negative'] += 1
                else:
                    sentiment_distribution['neutral'] += 1
            else:
                sentiment_distribution['unknown'] += 1
        
        # Text length statistics
        text_lengths = [len(r.get('cleaned_text', '')) for r in processed_reviews]
        text_length_stats = {}
        if text_lengths:
            text_length_stats = {
                'mean': statistics.mean(text_lengths),
                'median': statistics.median(text_lengths),
                'min': min(text_lengths),
                'max': max(text_lengths),
                'std': statistics.stdev(text_lengths) if len(text_lengths) > 1 else 0
            }
        
        # Word count statistics
        word_counts = [r.get('word_count', 0) for r in processed_reviews]
        word_count_stats = {}
        if word_counts:
            word_count_stats = {
                'mean': statistics.mean(word_counts),
                'median': statistics.median(word_counts),
                'min': min(word_counts),
                'max': max(word_counts),
                'std': statistics.stdev(word_counts) if len(word_counts) > 1 else 0
            }
        
        # Calculate rates
        success_rate = (len(processed_reviews) / total_reviews) * 100 if total_reviews > 0 else 0
        avg_quality_score = statistics.mean(quality_scores) if quality_scores else 0
        
        # Count spam and duplicates
        spam_count = sum(1 for r in processed_reviews 
                       if self.detect_spam_indicators(r.get('cleaned_text', '')) > 0.5)
        duplicate_count = sum(1 for r in processed_reviews 
                           if r.get('status') == 'filtered_duplicate')
        
        spam_rate = (spam_count / len(processed_reviews)) * 100 if processed_reviews else 0
        duplicate_rate = (duplicate_count / total_reviews) * 100 if total_reviews > 0 else 0
        
        # Detect anomalies
        all_anomalies = []
        all_anomalies.extend(self.detect_rating_anomalies(processed_reviews))
        all_anomalies.extend(self.detect_text_length_anomalies(processed_reviews))
        all_anomalies.extend(self.detect_sentiment_anomalies(processed_reviews))
        all_anomalies.extend(self.detect_spam_patterns(processed_reviews))
        all_anomalies.extend(self.detect_bot_patterns(processed_reviews))
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return QualityMetrics(
            total_reviews=total_reviews,
            processed_reviews=len(processed_reviews),
            success_rate=success_rate,
            average_quality_score=avg_quality_score,
            quality_distribution=dict(quality_distribution),
            language_distribution=dict(language_distribution),
            rating_distribution=dict(rating_distribution),
            sentiment_distribution=dict(sentiment_distribution),
            text_length_stats=text_length_stats,
            word_count_stats=word_count_stats,
            duplicate_rate=duplicate_rate,
            spam_rate=spam_rate,
            anomaly_count=len(all_anomalies),
            processing_time=processing_time
        )
    
    def generate_quality_report(self, reviews: List[Dict]) -> Dict:
        """Generate comprehensive quality report"""
        metrics = self.calculate_batch_metrics(reviews)
        
        # Detect all anomalies
        anomalies = []
        anomalies.extend(self.detect_rating_anomalies(reviews))
        anomalies.extend(self.detect_text_length_anomalies(reviews))
        anomalies.extend(self.detect_sentiment_anomalies(reviews))
        anomalies.extend(self.detect_spam_patterns(reviews))
        anomalies.extend(self.detect_bot_patterns(reviews))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, anomalies)
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': asdict(metrics),
            'anomalies': [asdict(anomaly) for anomaly in anomalies],
            'recommendations': recommendations,
            'quality_summary': {
                'overall_grade': self._calculate_overall_grade(metrics),
                'key_issues': self._identify_key_issues(anomalies),
                'improvement_areas': self._identify_improvement_areas(metrics)
            }
        }
        
        return report
    
    def _generate_recommendations(self, metrics: QualityMetrics, anomalies: List[AnomalyDetection]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Quality-based recommendations
        if metrics.average_quality_score < 0.6:
            recommendations.append("Improve data collection quality filters")
            recommendations.append("Review preprocessing pipeline")
        
        # Anomaly-based recommendations
        anomaly_types = set(a.anomaly_type for a in anomalies)
        
        if AnomalyType.SPAM_PATTERN in anomaly_types:
            recommendations.append("Implement stronger spam detection")
        
        if AnomalyType.BOT_PATTERN in anomaly_types:
            recommendations.append("Add bot detection mechanisms")
        
        if AnomalyType.RATING_SPIKE in anomaly_types:
            recommendations.append("Review for review manipulation")
        
        # Rate-based recommendations
        if metrics.spam_rate > 10:
            recommendations.append("Reduce spam content through better filters")
        
        if metrics.duplicate_rate > 5:
            recommendations.append("Improve duplicate detection algorithms")
        
        if metrics.success_rate < 90:
            recommendations.append("Improve data processing pipeline reliability")
        
        return recommendations
    
    def _calculate_overall_grade(self, metrics: QualityMetrics) -> str:
        """Calculate overall quality grade"""
        score = 0
        
        # Success rate (30%)
        score += (metrics.success_rate / 100) * 0.3
        
        # Quality score (30%)
        score += metrics.average_quality_score * 0.3
        
        # Low spam rate (20%)
        score += max(0, (100 - metrics.spam_rate) / 100) * 0.2
        
        # Low duplicate rate (10%)
        score += max(0, (100 - metrics.duplicate_rate) / 100) * 0.1
        
        # Low anomaly rate (10%)
        anomaly_penalty = min(metrics.anomaly_count / 10, 1.0)
        score += (1 - anomaly_penalty) * 0.1
        
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _identify_key_issues(self, anomalies: List[AnomalyDetection]) -> List[str]:
        """Identify key issues from anomalies"""
        issues = []
        
        anomaly_counts = Counter(a.anomaly_type.value for a in anomalies)
        
        for anomaly_type, count in anomaly_counts.most_common(3):
            if anomaly_type == "spam_pattern":
                issues.append(f"High spam content detected ({count} reviews)")
            elif anomaly_type == "bot_pattern":
                issues.append(f"Bot-generated reviews detected ({count} reviews)")
            elif anomaly_type == "rating_spike":
                issues.append(f"Rating anomalies detected ({count} reviews)")
            elif anomaly_type == "sentiment_anomaly":
                issues.append(f"Sentiment inconsistencies ({count} reviews)")
            elif anomaly_type == "text_length_anomaly":
                issues.append(f"Text length issues ({count} reviews)")
        
        return issues
    
    def _identify_improvement_areas(self, metrics: QualityMetrics) -> List[str]:
        """Identify areas for improvement"""
        areas = []
        
        if metrics.success_rate < 95:
            areas.append("Data processing reliability")
        
        if metrics.average_quality_score < 0.7:
            areas.append("Review content quality")
        
        if metrics.spam_rate > 5:
            areas.append("Spam detection and filtering")
        
        if metrics.duplicate_rate > 2:
            areas.append("Duplicate detection accuracy")
        
        if metrics.anomaly_count > 10:
            areas.append("Anomaly detection and prevention")
        
        return areas


# Factory function
def create_quality_pipeline(config: dict) -> DataQualityPipeline:
    """Create DataQualityPipeline instance"""
    return DataQualityPipeline(config)
