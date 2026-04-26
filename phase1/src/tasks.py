"""
Celery tasks for Phase 1
Background tasks for scheduled review ingestion
"""

from celery import Celery
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from config_manager import init_config
from database import init_database, get_db, Product
from appstore_ingestor import AppStoreIngestor
from googleplay_ingestor import GooglePlayIngestor

# Initialize components
config = init_config()
db_manager = init_database()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Celery app
celery_config = {
    'broker_url': f"redis://{config.get('redis.host')}:{config.get('redis.port')}/0",
    'result_backend': f"redis://{config.get('redis.host')}:{config.get('redis.port')}/0",
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
}

celery_app = Celery('review_pulse')
celery_app.conf.update(celery_config)


@celery_app.task(bind=True, max_retries=3)
def ingest_app_store_task(self, product_id: int):
    """Celery task for App Store ingestion"""
    db = db_manager.get_session()
    
    try:
        logger.info(f"Starting App Store ingestion task for product {product_id}")
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.error(f"Product {product_id} not found")
            return {"status": "error", "message": "Product not found"}
        
        if not product.app_store_id:
            logger.error(f"Product {product_id} has no App Store ID")
            return {"status": "error", "message": "No App Store ID"}
        
        ingestor = AppStoreIngestor(config.config)
        log = ingestor.ingest_product(product, db)
        
        result = {
            "status": log.status,
            "product_id": product_id,
            "product_name": product.name,
            "source": "app_store",
            "reviews_collected": log.reviews_collected,
            "reviews_processed": log.reviews_processed,
            "duration_seconds": log.duration_seconds,
            "error": log.error_message
        }
        
        logger.info(f"App Store ingestion completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in App Store ingestion task: {e}")
        db.rollback()
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def ingest_google_play_task(self, product_id: int):
    """Celery task for Google Play ingestion"""
    db = db_manager.get_session()
    
    try:
        logger.info(f"Starting Google Play ingestion task for product {product_id}")
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            logger.error(f"Product {product_id} not found")
            return {"status": "error", "message": "Product not found"}
        
        if not product.play_store_url:
            logger.error(f"Product {product_id} has no Play Store URL")
            return {"status": "error", "message": "No Play Store URL"}
        
        ingestor = GooglePlayIngestor(config.config)
        log = ingestor.ingest_product(product, db)
        
        result = {
            "status": log.status,
            "product_id": product_id,
            "product_name": product.name,
            "source": "google_play",
            "reviews_collected": log.reviews_collected,
            "reviews_processed": log.reviews_processed,
            "duration_seconds": log.duration_seconds,
            "error": log.error_message
        }
        
        logger.info(f"Google Play ingestion completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in Google Play ingestion task: {e}")
        db.rollback()
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
    finally:
        db.close()


@celery_app.task
def ingest_all_products_task():
    """Celery task to ingest all products"""
    db = db_manager.get_session()
    
    try:
        logger.info("Starting ingestion for all products")
        
        products = db.query(Product).all()
        results = []
        
        for product in products:
            # Get product configuration to check enabled sources
            products_config = config.get_products()
            product_config = next((p for p in products_config if p.get('name') == product.name), None)
            sources = product_config.get('sources', {}) if product_config else {}
            
            # Trigger App Store ingestion
            if product.app_store_id and sources.get('app_store', True):
                result = ingest_app_store_task.delay(product.id)
                results.append({
                    "product": product.name,
                    "source": "app_store",
                    "task_id": result.id
                })
            
            # Trigger Google Play ingestion
            if product.play_store_url and sources.get('google_play', True):
                result = ingest_google_play_task.delay(product.id)
                results.append({
                    "product": product.name,
                    "source": "google_play",
                    "task_id": result.id
                })
        
        logger.info(f"Triggered {len(results)} ingestion tasks")
        return {"status": "triggered", "tasks": results}
        
    except Exception as e:
        logger.error(f"Error in ingest all products task: {e}")
        return {"status": "error", "message": str(e)}
        
    finally:
        db.close()


@celery_app.task
def health_check_task():
    """Periodic health check task"""
    try:
        from redis_cache import init_redis_cache
        redis_cache = init_redis_cache(config.config)
        
        # Check Redis
        redis_cache.client.ping()
        
        # Check database
        db = db_manager.get_session()
        db.execute("SELECT 1")
        db.close()
        
        logger.info("Health check passed")
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


# Configure periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'ingest-all-products-daily': {
        'task': 'tasks.ingest_all_products_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM UTC
    },
    'health-check-every-5-minutes': {
        'task': 'tasks.health_check_task',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
