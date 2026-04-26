"""
App Store RSS Review Ingestor for Phase 1
Collects reviews from iTunes Customer Reviews RSS feed
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import time
import logging
from database import Review, Product, IngestionLog, get_db

logger = logging.getLogger(__name__)


class AppStoreIngestor:
    """Ingests reviews from Apple App Store RSS feeds"""
    
    def __init__(self, config: dict):
        self.config = config['app_store']
        self.rss_template = self.config['rss_feed_url_template']
        self.max_pages = self.config['max_pages']
        self.reviews_per_page = self.config['reviews_per_page']
        self.timeout = self.config['request_timeout']
        self.retry_attempts = self.config['retry_attempts']
        self.retry_delay = self.config['retry_delay']
        self.time_window_days = config.get('ingestion', {}).get('time_window_days', 84)
    
    def fetch_reviews(self, app_store_id: str, days_back: int = None) -> List[Dict]:
        """Fetch reviews from RSS feed for a specific app"""
        all_reviews = []
        # Use configured time window if days_back not provided
        if days_back is None:
            days_back = self.time_window_days
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        for page in range(1, self.max_pages + 1):
            url = self.rss_template.format(page=page, app_id=app_store_id)
            
            for attempt in range(self.retry_attempts):
                try:
                    logger.info(f"Fetching page {page} for app {app_store_id}")
                    response = requests.get(url, timeout=self.timeout)
                    response.raise_for_status()
                    
                    feed = feedparser.parse(response.content)
                    
                    if not feed.entries:
                        logger.info(f"No more reviews found on page {page}")
                        break
                    
                    page_reviews = self._parse_feed(feed, cutoff_date)
                    
                    if not page_reviews:
                        logger.info(f"No recent reviews on page {page}")
                        break
                    
                    all_reviews.extend(page_reviews)
                    logger.info(f"Collected {len(page_reviews)} reviews from page {page}")
                    
                    # Check if we've reached the cutoff date
                    if page_reviews[-1]['review_date'] < cutoff_date:
                        logger.info(f"Reached cutoff date on page {page}")
                        break
                    
                    time.sleep(1)  # Rate limiting
                    break
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Attempt {attempt + 1} failed for page {page}: {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.error(f"Failed to fetch page {page} after {self.retry_attempts} attempts")
        
        logger.info(f"Total reviews collected: {len(all_reviews)}")
        return all_reviews
    
    def _parse_feed(self, feed: feedparser.FeedParserDict, cutoff_date: datetime) -> List[Dict]:
        """Parse RSS feed entries into review dictionaries"""
        reviews = []
        
        for entry in feed.entries:
            try:
                # Extract review data from RSS entry
                review_id = entry.get('id', '').split('/')[-1]
                title = entry.get('title', '')
                content = entry.get('content', [{}])[0].get('value', '')
                author = entry.get('author', '')
                rating = self._extract_rating(entry)
                review_date = self._parse_date(entry.get('updated'))
                
                # Skip if review is too old
                if review_date and review_date < cutoff_date:
                    continue
                
                review = {
                    'external_review_id': review_id,
                    'title': title,
                    'review_text': content,
                    'author_name': author,
                    'rating': rating,
                    'review_date': review_date or datetime.utcnow(),
                    'review_url': entry.get('link', ''),
                    'version': self._extract_version(entry)
                }
                
                reviews.append(review)
                
            except Exception as e:
                logger.error(f"Error parsing review entry: {e}")
                continue
        
        return reviews
    
    def _extract_rating(self, entry: Dict) -> Optional[int]:
        """Extract rating from RSS entry"""
        try:
            # iTunes RSS stores rating in im:rating tag
            rating = entry.get('im_rating')
            if rating:
                return int(rating)
        except (ValueError, AttributeError):
            pass
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string from RSS feed"""
        try:
            return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        except (ValueError, TypeError):
            try:
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
            except (ValueError, TypeError):
                return None
    
    def _extract_version(self, entry: Dict) -> Optional[str]:
        """Extract app version from RSS entry"""
        try:
            return entry.get('im_version')
        except AttributeError:
            return None
    
    def save_reviews(self, reviews: List[Dict], product_id: int, db: Session) -> int:
        """Save reviews to database with deduplication"""
        saved_count = 0
        
        for review_data in reviews:
            try:
                # Check if review already exists
                existing = db.query(Review).filter(
                    Review.product_id == product_id,
                    Review.source == 'app_store',
                    Review.external_review_id == review_data['external_review_id']
                ).first()
                
                if existing:
                    logger.debug(f"Review {review_data['external_review_id']} already exists, skipping")
                    continue
                
                # Create new review
                review = Review(
                    product_id=product_id,
                    source='app_store',
                    external_review_id=review_data['external_review_id'],
                    review_text=review_data['review_text'],
                    rating=review_data['rating'],
                    author_name=review_data['author_name'],
                    review_date=review_data['review_date'],
                    review_url=review_data['review_url'],
                    version=review_data['version'],
                    title=review_data['title']
                )
                
                db.add(review)
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving review {review_data.get('external_review_id')}: {e}")
                continue
        
        db.commit()
        logger.info(f"Saved {saved_count} new reviews to database")
        return saved_count
    
    def ingest_product(self, product: Product, db: Session) -> IngestionLog:
        """Ingest reviews for a single product"""
        log = IngestionLog(
            product_id=product.id,
            source='app_store',
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        
        try:
            logger.info(f"Starting ingestion for {product.name} from App Store")
            
            # Fetch reviews
            reviews = self.fetch_reviews(product.app_store_id)
            log.reviews_collected = len(reviews)
            
            # Save to database
            saved_count = self.save_reviews(reviews, product.id, db)
            log.reviews_processed = saved_count
            
            log.status = 'success'
            log.completed_at = datetime.utcnow()
            log.duration_seconds = int((log.completed_at - log.started_at).total_seconds())
            
            logger.info(f"Successfully ingested {saved_count} reviews for {product.name}")
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            log.duration_seconds = int((log.completed_at - log.started_at).total_seconds())
            logger.error(f"Failed to ingest reviews for {product.name}: {e}")
            db.rollback()
        
        db.commit()
        return log
