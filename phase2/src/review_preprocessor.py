"""
Review Preprocessor for Phase 2
Handles text cleaning, language detection, deduplication, and metadata enrichment
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json
from dataclasses import dataclass
from enum import Enum

# Try to import language detection library
try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    LANGUAGE_DETECTION_AVAILABLE = True
    DetectorFactory.seed = 0  # For consistent results
except ImportError:
    LANGUAGE_DETECTION_AVAILABLE = False
    logging.warning("langdetect not available, using fallback language detection")

# Try to import sentiment analysis
try:
    from textblob import TextBlob
    SENTIMENT_ANALYSIS_AVAILABLE = True
except ImportError:
    SENTIMENT_ANALYSIS_AVAILABLE = False
    logging.warning("textblob not available, sentiment analysis disabled")

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status of review processing"""
    SUCCESS = "success"
    FILTERED_LANGUAGE = "filtered_language"
    FILTERED_DUPLICATE = "filtered_duplicate"
    FILTERED_QUALITY = "filtered_quality"
    ERROR = "error"


@dataclass
class ProcessedReview:
    """Processed review with enhanced metadata"""
    external_review_id: str
    title: str
    review_text: str
    cleaned_text: str
    author_name: str
    rating: int
    review_date: datetime
    review_url: str
    version: str
    source: str
    product_id: int
    language: str
    sentiment_score: Optional[float]
    text_length: int
    word_count: int
    processed_at: datetime
    status: ProcessingStatus
    filter_reason: Optional[str] = None
    text_hash: Optional[str] = None
    quality_score: Optional[float] = None


class ReviewPreprocessor:
    """Preprocesses reviews for analysis pipeline"""
    
    def __init__(self, config: dict):
        self.config = config.get('preprocessing', {})
        self.target_language = self.config.get('target_language', 'en')
        self.min_text_length = self.config.get('min_text_length', 10)
        self.max_text_length = self.config.get('max_text_length', 5000)
        self.duplicate_threshold = self.config.get('duplicate_threshold', 0.9)
        self.quality_threshold = self.config.get('quality_threshold', 0.3)
        
        # Text cleaning patterns
        self.html_pattern = re.compile(r'<[^>]+>')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.excessive_whitespace = re.compile(r'\s+')
        self.special_chars = re.compile(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\]')
        
        # Track processed reviews for deduplication
        self.processed_hashes = set()
        
        logger.info(f"ReviewPreprocessor initialized with target_language={self.target_language}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Convert to lowercase for processing
        cleaned = text.lower()
        
        # Remove HTML tags
        cleaned = self.html_pattern.sub(' ', cleaned)
        
        # Remove URLs
        cleaned = self.url_pattern.sub(' ', cleaned)
        
        # Remove email addresses
        cleaned = self.email_pattern.sub(' ', cleaned)
        
        # Remove phone numbers
        cleaned = self.phone_pattern.sub(' ', cleaned)
        
        # Remove excessive whitespace
        cleaned = self.excessive_whitespace.sub(' ', cleaned)
        
        # Remove special characters but keep basic punctuation
        cleaned = self.special_chars.sub(' ', cleaned)
        
        # Final whitespace cleanup
        cleaned = cleaned.strip()
        
        # Limit length
        if len(cleaned) > self.max_text_length:
            cleaned = cleaned[:self.max_text_length].rsplit(' ', 1)[0] + '...'
        
        return cleaned
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        if not text or len(text) < 10:
            return 'unknown'
        
        if LANGUAGE_DETECTION_AVAILABLE:
            try:
                lang = detect(text)
                return lang
            except LangDetectException:
                logger.warning(f"Language detection failed for text: {text[:50]}...")
                return 'unknown'
        else:
            # Fallback: simple heuristic for English detection
            english_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')
            english_ratio = sum(1 for char in text if char in english_chars) / len(text)
            return 'en' if english_ratio > 0.8 else 'unknown'
    
    def analyze_sentiment(self, text: str) -> Optional[float]:
        """Analyze sentiment of text (-1 to 1 scale)"""
        if not text or not SENTIMENT_ANALYSIS_AVAILABLE:
            return None
        
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
            return float(sentiment)
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return None
    
    def calculate_quality_score(self, text: str, rating: int) -> float:
        """Calculate quality score for review (0 to 1 scale)"""
        if not text:
            return 0.0
        
        score = 0.0
        
        # Text length factor (prefer moderate length)
        length = len(text)
        if self.min_text_length <= length <= 500:
            score += 0.3
        elif 500 < length <= 1000:
            score += 0.2
        elif length > 1000:
            score += 0.1
        
        # Word count factor
        word_count = len(text.split())
        if 5 <= word_count <= 50:
            score += 0.3
        elif 50 < word_count <= 100:
            score += 0.2
        elif word_count > 100:
            score += 0.1
        
        # Rating consistency factor
        if rating >= 4:  # Positive reviews
            positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'perfect']
            score += sum(0.05 for word in positive_words if word in text.lower())
        elif rating <= 2:  # Negative reviews
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 'disappointed']
            score += sum(0.05 for word in negative_words if word in text.lower())
        
        # Diversity factor (different words)
        unique_words = len(set(text.lower().split()))
        total_words = len(text.split())
        if total_words > 0:
            diversity = unique_words / total_words
            score += diversity * 0.2
        
        return min(score, 1.0)
    
    def generate_text_hash(self, text: str) -> str:
        """Generate hash for text deduplication"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, text_hash: str, existing_hashes: set) -> bool:
        """Check if review is duplicate"""
        return text_hash in existing_hashes
    
    def process_review(self, review_data: dict) -> ProcessedReview:
        """Process a single review"""
        try:
            # Extract basic fields
            external_id = review_data.get('external_review_id')
            title = review_data.get('title', '')
            review_text = review_data.get('review_text', '')
            author_name = review_data.get('author_name', '')
            rating = review_data.get('rating', 0)
            review_date_str = review_data.get('review_date')
            review_url = review_data.get('review_url', '')
            version = review_data.get('version', '')
            source = review_data.get('source', '')
            product_id = review_data.get('product_id', 0)
            
            # Parse date
            try:
                if isinstance(review_date_str, str):
                    review_date = datetime.fromisoformat(review_date_str.replace('Z', '+00:00'))
                else:
                    review_date = datetime.utcnow()
            except:
                review_date = datetime.utcnow()
            
            # Basic validation
            if not external_id or not review_text:
                return ProcessedReview(
                    external_review_id=external_id or 'unknown',
                    title=title,
                    review_text=review_text,
                    cleaned_text='',
                    author_name=author_name,
                    rating=rating,
                    review_date=review_date,
                    review_url=review_url,
                    version=version,
                    source=source,
                    product_id=product_id,
                    language='unknown',
                    sentiment_score=None,
                    text_length=0,
                    word_count=0,
                    processed_at=datetime.utcnow(),
                    status=ProcessingStatus.ERROR,
                    filter_reason='Missing required fields'
                )
            
            # Clean text
            cleaned_text = self.clean_text(review_text)
            
            # Check text length
            if len(cleaned_text) < self.min_text_length:
                return ProcessedReview(
                    external_review_id=external_id,
                    title=title,
                    review_text=review_text,
                    cleaned_text=cleaned_text,
                    author_name=author_name,
                    rating=rating,
                    review_date=review_date,
                    review_url=review_url,
                    version=version,
                    source=source,
                    product_id=product_id,
                    language='unknown',
                    sentiment_score=None,
                    text_length=len(cleaned_text),
                    word_count=len(cleaned_text.split()),
                    processed_at=datetime.utcnow(),
                    status=ProcessingStatus.FILTERED_QUALITY,
                    filter_reason='Text too short'
                )
            
            # Detect language
            language = self.detect_language(cleaned_text)
            if language != self.target_language:
                return ProcessedReview(
                    external_review_id=external_id,
                    title=title,
                    review_text=review_text,
                    cleaned_text=cleaned_text,
                    author_name=author_name,
                    rating=rating,
                    review_date=review_date,
                    review_url=review_url,
                    version=version,
                    source=source,
                    product_id=product_id,
                    language=language,
                    sentiment_score=None,
                    text_length=len(cleaned_text),
                    word_count=len(cleaned_text.split()),
                    processed_at=datetime.utcnow(),
                    status=ProcessingStatus.FILTERED_LANGUAGE,
                    filter_reason=f'Language {language} not target {self.target_language}'
                )
            
            # Check for duplicates
            text_hash = self.generate_text_hash(cleaned_text)
            if self.is_duplicate(text_hash, self.processed_hashes):
                return ProcessedReview(
                    external_review_id=external_id,
                    title=title,
                    review_text=review_text,
                    cleaned_text=cleaned_text,
                    author_name=author_name,
                    rating=rating,
                    review_date=review_date,
                    review_url=review_url,
                    version=version,
                    source=source,
                    product_id=product_id,
                    language=language,
                    sentiment_score=None,
                    text_length=len(cleaned_text),
                    word_count=len(cleaned_text.split()),
                    processed_at=datetime.utcnow(),
                    status=ProcessingStatus.FILTERED_DUPLICATE,
                    filter_reason='Duplicate content'
                )
            
            # Add to processed hashes
            self.processed_hashes.add(text_hash)
            
            # Analyze sentiment
            sentiment_score = self.analyze_sentiment(cleaned_text)
            
            # Calculate quality score
            quality_score = self.calculate_quality_score(cleaned_text, rating)
            
            # Filter by quality
            if quality_score < self.quality_threshold:
                return ProcessedReview(
                    external_review_id=external_id,
                    title=title,
                    review_text=review_text,
                    cleaned_text=cleaned_text,
                    author_name=author_name,
                    rating=rating,
                    review_date=review_date,
                    review_url=review_url,
                    version=version,
                    source=source,
                    product_id=product_id,
                    language=language,
                    sentiment_score=sentiment_score,
                    text_length=len(cleaned_text),
                    word_count=len(cleaned_text.split()),
                    processed_at=datetime.utcnow(),
                    status=ProcessingStatus.FILTERED_QUALITY,
                    filter_reason=f'Quality score {quality_score:.2f} below threshold {self.quality_threshold}'
                )
            
            # Success case
            return ProcessedReview(
                external_review_id=external_id,
                title=title,
                review_text=review_text,
                cleaned_text=cleaned_text,
                author_name=author_name,
                rating=rating,
                review_date=review_date,
                review_url=review_url,
                version=version,
                source=source,
                product_id=product_id,
                language=language,
                sentiment_score=sentiment_score,
                text_length=len(cleaned_text),
                word_count=len(cleaned_text.split()),
                processed_at=datetime.utcnow(),
                status=ProcessingStatus.SUCCESS,
                text_hash=text_hash,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Error processing review {review_data.get('external_review_id', 'unknown')}: {e}")
            return ProcessedReview(
                external_review_id=review_data.get('external_review_id', 'unknown'),
                title=review_data.get('title', ''),
                review_text=review_data.get('review_text', ''),
                cleaned_text='',
                author_name=review_data.get('author_name', ''),
                rating=review_data.get('rating', 0),
                review_date=datetime.utcnow(),
                review_url=review_data.get('review_url', ''),
                version=review_data.get('version', ''),
                source=review_data.get('source', ''),
                product_id=review_data.get('product_id', 0),
                language='unknown',
                sentiment_score=None,
                text_length=0,
                word_count=0,
                processed_at=datetime.utcnow(),
                status=ProcessingStatus.ERROR,
                filter_reason=f'Processing error: {str(e)}'
            )
    
    def process_batch(self, reviews: List[dict]) -> List[ProcessedReview]:
        """Process a batch of reviews"""
        processed_reviews = []
        
        logger.info(f"Processing batch of {len(reviews)} reviews")
        
        for i, review_data in enumerate(reviews):
            try:
                processed = self.process_review(review_data)
                processed_reviews.append(processed)
                
                # Log progress every 100 reviews
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{len(reviews)} reviews")
                    
            except Exception as e:
                logger.error(f"Error processing review at index {i}: {e}")
                continue
        
        # Generate processing statistics
        stats = self.get_processing_stats(processed_reviews)
        logger.info(f"Batch processing completed: {stats}")
        
        return processed_reviews
    
    def get_processing_stats(self, processed_reviews: List[ProcessedReview]) -> dict:
        """Generate processing statistics"""
        total = len(processed_reviews)
        if total == 0:
            return {"total": 0}
        
        stats = {
            "total": total,
            "success": 0,
            "filtered_language": 0,
            "filtered_duplicate": 0,
            "filtered_quality": 0,
            "error": 0,
            "success_rate": 0.0,
            "avg_quality_score": 0.0,
            "avg_sentiment_score": 0.0,
            "languages": {},
            "avg_text_length": 0,
            "avg_word_count": 0
        }
        
        quality_scores = []
        sentiment_scores = []
        text_lengths = []
        word_counts = []
        
        for review in processed_reviews:
            stats[review.status.value] += 1
            
            if review.status == ProcessingStatus.SUCCESS:
                if review.quality_score:
                    quality_scores.append(review.quality_score)
                if review.sentiment_score:
                    sentiment_scores.append(review.sentiment_score)
                text_lengths.append(review.text_length)
                word_counts.append(review.word_count)
            
            # Track languages
            lang = review.language
            stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
        
        # Calculate averages
        if quality_scores:
            stats["avg_quality_score"] = sum(quality_scores) / len(quality_scores)
        if sentiment_scores:
            stats["avg_sentiment_score"] = sum(sentiment_scores) / len(sentiment_scores)
        if text_lengths:
            stats["avg_text_length"] = sum(text_lengths) / len(text_lengths)
        if word_counts:
            stats["avg_word_count"] = sum(word_counts) / len(word_counts)
        
        stats["success_rate"] = (stats["success"] / total) * 100
        
        return stats
    
    def reset_duplicate_tracking(self):
        """Reset duplicate tracking for new batch"""
        self.processed_hashes.clear()
        logger.info("Duplicate tracking reset")


# Factory function
def create_preprocessor(config: dict) -> ReviewPreprocessor:
    """Create ReviewPreprocessor instance"""
    return ReviewPreprocessor(config)
