"""
Google Play Store Review Ingestor for Phase 1
Collects reviews using web scraping with proxy rotation
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import time
import random
import logging
from database import Review, Product, IngestionLog

logger = logging.getLogger(__name__)


class GooglePlayIngestor:
    """Ingests reviews from Google Play Store using web scraping"""
    
    def __init__(self, config: dict):
        self.config = config['google_play']
        self.max_reviews = self.config['max_reviews']
        self.timeout = self.config['request_timeout']
        self.retry_attempts = self.config['retry_attempts']
        self.retry_delay = self.config['retry_delay']
        self.proxy_rotation = self.config['proxy_rotation']
        self.proxy_list = [p for p in self.config['proxy_list'] if p and p != '${PROXY_1}']
        self.user_agents = self.config['user_agents']
        self.effective_reviews_only = self.config.get('effective_reviews_only', False)
    
    def _get_session(self) -> requests.Session:
        """Create a requests session with random user agent"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        return session
    
    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the list"""
        if not self.proxy_rotation or not self.proxy_list:
            return None
        proxy = random.choice(self.proxy_list)
        return {'http': proxy, 'https': proxy}
    
    def fetch_reviews(self, package_name: str, days_back: int = 84) -> List[Dict]:
        """Fetch reviews from Google Play Store for a specific app"""
        all_reviews = []
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Use play-scraper library if available, otherwise fallback to manual scraping
        try:
            from play_scraper import reviews as play_reviews
            logger.info(f"Using play-scraper for {package_name}")
            
            for attempt in range(self.retry_attempts):
                try:
                    # Fetch reviews using play-scraper
                    scraped_reviews = play_reviews(
                        package_name,
                        count=self.max_reviews,
                        sort=2,  # Sort by newest
                        filter_score_with=5,  # All ratings
                        filter_device_with=5 if self.effective_reviews_only else None  # Effective reviews only if enabled
                    )
                    
                    # Parse and filter reviews
                    for review in scraped_reviews:
                        review_data = self._parse_review(review, cutoff_date)
                        if review_data:
                            all_reviews.append(review_data)
                    
                    logger.info(f"Collected {len(all_reviews)} reviews using play-scraper")
                    break
                    
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed with play-scraper: {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                    else:
                        logger.warning("play-scraper failed, falling back to manual scraping")
                        all_reviews = self._manual_scrape(package_name, cutoff_date)
                        
        except ImportError:
            logger.warning("play-scraper not available, using manual scraping")
            all_reviews = self._manual_scrape(package_name, cutoff_date)
        
        logger.info(f"Total reviews collected: {len(all_reviews)}")
        return all_reviews
    
    def _manual_scrape(self, package_name: str, cutoff_date: datetime) -> List[Dict]:
        """Manual scraping fallback using requests and BeautifulSoup"""
        all_reviews = []
        url = f"https://play.google.com/store/apps/details?id={package_name}&showAllReviews=true"
        
        for attempt in range(self.retry_attempts):
            try:
                session = self._get_session()
                proxy = self._get_proxy()
                
                logger.info(f"Manual scraping attempt {attempt + 1} for {package_name}")
                response = session.get(url, timeout=self.timeout, proxies=proxy)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse review elements (this is a simplified implementation)
                # In production, you'd need to handle Google's dynamic content
                review_elements = soup.find_all('div', class_='review-card')
                
                for element in review_elements:
                    try:
                        review_data = self._parse_html_element(element, cutoff_date)
                        if review_data:
                            all_reviews.append(review_data)
                    except Exception as e:
                        logger.error(f"Error parsing review element: {e}")
                        continue
                
                logger.info(f"Manual scraping collected {len(all_reviews)} reviews")
                break
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Manual scraping attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Manual scraping failed after {self.retry_attempts} attempts")
        
        return all_reviews
    
    def _parse_review(self, review: Dict, cutoff_date: datetime) -> Optional[Dict]:
        """Parse review from play-scraper output"""
        try:
            review_date = self._parse_date_string(review.get('at'))
            
            # Skip if review is too old
            if review_date and review_date < cutoff_date:
                return None
            
            return {
                'external_review_id': review.get('id', ''),
                'title': review.get('title', ''),
                'review_text': review.get('body', ''),
                'author_name': review.get('userName', ''),
                'rating': review.get('score'),
                'review_date': review_date or datetime.utcnow(),
                'review_url': f"https://play.google.com/store/apps/details?id={review.get('appId')}",
                'version': review.get('version')
            }
        except Exception as e:
            logger.error(f"Error parsing review: {e}")
            return None
    
    def _parse_html_element(self, element: BeautifulSoup, cutoff_date: datetime) -> Optional[Dict]:
        """Parse review from HTML element (manual scraping)"""
        try:
            # This is a simplified parser - production would need more robust parsing
            review_id = element.get('data-review-id', '')
            title = element.find('span', class_='review-title')
            text = element.find('div', class_='review-body')
            author = element.find('span', class_='author-name')
            rating = element.find('div', class_='rating')
            date = element.find('span', class_='review-date')
            
            review_date = self._parse_date_string(date.get_text()) if date else None
            
            if review_date and review_date < cutoff_date:
                return None
            
            return {
                'external_review_id': review_id,
                'title': title.get_text() if title else '',
                'review_text': text.get_text() if text else '',
                'author_name': author.get_text() if author else '',
                'rating': self._extract_rating_from_html(rating) if rating else None,
                'review_date': review_date or datetime.utcnow(),
                'review_url': '',
                'version': None
            }
        except Exception as e:
            logger.error(f"Error parsing HTML element: {e}")
            return None
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse date string from Google Play format"""
        try:
            # Google Play uses relative dates like "2 days ago"
            # This is a simplified implementation
            if 'ago' in date_str.lower():
                return datetime.utcnow()  # Fallback to current time
            return datetime.strptime(date_str, '%B %d, %Y')
        except (ValueError, TypeError):
            return None
    
    def _extract_rating_from_html(self, rating_element: BeautifulSoup) -> Optional[int]:
        """Extract rating from HTML element"""
        try:
            # Look for aria-label attribute which often contains rating
            aria_label = rating_element.get('aria-label', '')
            if 'Rated' in aria_label:
                return int(aria_label.split('stars')[0].split()[-1])
        except (ValueError, AttributeError):
            pass
        return None
    
    def save_reviews(self, reviews: List[Dict], product_id: int, db: Session) -> int:
        """Save reviews to database with deduplication"""
        saved_count = 0
        
        for review_data in reviews:
            try:
                # Check if review already exists
                existing = db.query(Review).filter(
                    Review.product_id == product_id,
                    Review.source == 'google_play',
                    Review.external_review_id == review_data['external_review_id']
                ).first()
                
                if existing:
                    logger.debug(f"Review {review_data['external_review_id']} already exists, skipping")
                    continue
                
                # Create new review
                review = Review(
                    product_id=product_id,
                    source='google_play',
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
            source='google_play',
            status='in_progress',
            started_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        
        try:
            # Extract package name from URL
            package_name = product.play_store_url.split('id=')[-1]
            logger.info(f"Starting ingestion for {product.name} from Google Play")
            
            # Fetch reviews
            reviews = self.fetch_reviews(package_name)
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
