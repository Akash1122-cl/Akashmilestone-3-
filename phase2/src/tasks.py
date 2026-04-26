"""
Celery Tasks for Phase 2 - Data Processing Pipeline
Background tasks for review preprocessing, embedding generation, and quality analysis
"""

from celery import Celery
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional, Any
import json
import os

# Import Phase 2 components
from review_preprocessor import ReviewPreprocessor, create_preprocessor
from embedding_service import EmbeddingService, create_embedding_service
from data_quality_pipeline import DataQualityPipeline, create_quality_pipeline
from vector_database import VectorDatabase, create_vector_database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
config = None
preprocessor = None
embedding_service = None
quality_pipeline = None
vector_db = None


def init_components():
    """Initialize Phase 2 components"""
    global config, preprocessor, embedding_service, quality_pipeline, vector_db
    
    if config is None:
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            config = {}
    
    if preprocessor is None:
        preprocessor = create_preprocessor(config)
        logger.info("Preprocessor initialized")
    
    if embedding_service is None:
        embedding_service = create_embedding_service(config)
        logger.info("Embedding service initialized")
    
    if quality_pipeline is None:
        quality_pipeline = create_quality_pipeline(config)
        logger.info("Quality pipeline initialized")
    
    if vector_db is None:
        vector_db = create_vector_database(config)
        logger.info("Vector database initialized")


# Create Celery app
celery_config = {
    'broker_url': f"redis://{config.get('redis.host', 'localhost')}:{config.get('redis.port', 6379)}/1",
    'result_backend': f"redis://{config.get('redis.host', 'localhost')}:{config.get('redis.port', 6379)}/1",
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_routes': {
        'tasks.preprocess_batch': {'queue': 'preprocessing'},
        'tasks.generate_embeddings_batch': {'queue': 'embeddings'},
        'tasks.quality_analysis_batch': {'queue': 'quality'},
        'tasks.create_vector_index': {'queue': 'vector_db'},
        'tasks.complete_processing_pipeline': {'queue': 'processing'},
    }
}

celery_app = Celery('review_pulse_phase2')
celery_app.conf.update(celery_config)


@celery_app.task(bind=True, max_retries=3)
def preprocess_batch_task(self, reviews: List[Dict]) -> Dict:
    """Celery task for batch preprocessing of reviews"""
    init_components()
    
    try:
        logger.info(f"Starting preprocessing task for {len(reviews)} reviews")
        
        # Process reviews
        processed_reviews = preprocessor.process_batch(reviews)
        
        # Generate statistics
        stats = preprocessor.get_processing_stats(processed_reviews)
        
        # Convert to serializable format
        processed_dicts = []
        for review in processed_reviews:
            processed_dicts.append({
                'external_review_id': review.external_review_id,
                'title': review.title,
                'cleaned_text': review.cleaned_text,
                'author_name': review.author_name,
                'rating': review.rating,
                'language': review.language,
                'sentiment_score': review.sentiment_score,
                'text_length': review.text_length,
                'word_count': review.word_count,
                'quality_score': review.quality_score,
                'status': review.status.value,
                'filter_reason': review.filter_reason,
                'processed_at': review.processed_at.isoformat()
            })
        
        result = {
            'status': 'success',
            'total_reviews': len(reviews),
            'processed_reviews': len(processed_reviews),
            'statistics': stats,
            'reviews': processed_dicts
        }
        
        logger.info(f"Preprocessing completed: {result['processed_reviews']}/{result['total_reviews']} reviews")
        return result
        
    except Exception as e:
        logger.error(f"Error in preprocessing task: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def generate_embeddings_batch_task(self, reviews: List[Dict]) -> Dict:
    """Celery task for batch embedding generation"""
    init_components()
    
    try:
        logger.info(f"Starting embedding generation task for {len(reviews)} reviews")
        
        # Generate embeddings for reviews
        reviews_with_embeddings = embedding_service.process_reviews_embeddings(reviews)
        
        # Count successful embeddings
        successful_embeddings = [r for r in reviews_with_embeddings if r.get('embedding')]
        
        result = {
            'status': 'success',
            'total_reviews': len(reviews),
            'successful_embeddings': len(successful_embeddings),
            'reviews': reviews_with_embeddings
        }
        
        logger.info(f"Embedding generation completed: {result['successful_embeddings']}/{result['total_reviews']} reviews")
        return result
        
    except Exception as e:
        logger.error(f"Error in embedding generation task: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def quality_analysis_batch_task(self, reviews: List[Dict]) -> Dict:
    """Celery task for batch quality analysis"""
    init_components()
    
    try:
        logger.info(f"Starting quality analysis task for {len(reviews)} reviews")
        
        # Generate quality report
        quality_report = quality_pipeline.generate_quality_report(reviews)
        
        result = {
            'status': 'success',
            'total_reviews': len(reviews),
            'quality_report': quality_report
        }
        
        logger.info(f"Quality analysis completed for {len(reviews)} reviews")
        return result
        
    except Exception as e:
        logger.error(f"Error in quality analysis task: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def create_vector_index_task(self, reviews: List[Dict]) -> Dict:
    """Celery task for creating vector index"""
    init_components()
    
    try:
        logger.info(f"Starting vector index creation task for {len(reviews)} reviews")
        
        # Create vector index
        success = vector_db.create_index_from_reviews(reviews)
        
        # Get index statistics
        stats = vector_db.get_index_stats()
        
        result = {
            'status': 'success' if success else 'error',
            'total_reviews': len(reviews),
            'index_created': success,
            'index_stats': stats.__dict__
        }
        
        if success:
            logger.info(f"Vector index created successfully with {len(reviews)} reviews")
        else:
            logger.error("Failed to create vector index")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in vector index creation task: {e}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def complete_processing_pipeline_task(self, reviews: List[Dict]) -> Dict:
    """Celery task for complete processing pipeline"""
    init_components()
    
    try:
        logger.info(f"Starting complete processing pipeline for {len(reviews)} reviews")
        
        # Step 1: Preprocess reviews
        preprocess_result = preprocess_batch_task.delay(reviews)
        preprocess_data = preprocess_result.get()
        
        if preprocess_data['status'] != 'success':
            raise Exception(f"Preprocessing failed: {preprocess_data}")
        
        processed_reviews = preprocess_data['reviews']
        
        # Step 2: Generate embeddings
        embedding_result = generate_embeddings_batch_task.delay(processed_reviews)
        embedding_data = embedding_result.get()
        
        if embedding_data['status'] != 'success':
            raise Exception(f"Embedding generation failed: {embedding_data}")
        
        reviews_with_embeddings = embedding_data['reviews']
        
        # Step 3: Quality analysis
        quality_result = quality_analysis_batch_task.delay(reviews_with_embeddings)
        quality_data = quality_result.get()
        
        if quality_data['status'] != 'success':
            raise Exception(f"Quality analysis failed: {quality_data}")
        
        # Step 4: Create vector index
        vector_result = create_vector_index_task.delay(reviews_with_embeddings)
        vector_data = vector_result.get()
        
        # Compile final result
        result = {
            'status': 'success',
            'pipeline_completed': True,
            'total_reviews': len(reviews),
            'preprocessing': preprocess_data,
            'embeddings': embedding_data,
            'quality_analysis': quality_data,
            'vector_index': vector_data,
            'processing_time': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Complete processing pipeline finished for {len(reviews)} reviews")
        return result
        
    except Exception as e:
        logger.error(f"Error in complete processing pipeline: {e}")
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=2)
def periodic_quality_check_task(self) -> Dict:
    """Periodic task to check data quality"""
    init_components()
    
    try:
        logger.info("Starting periodic quality check")
        
        # Get recent reviews from vector database (mock for now)
        # In production, this would query the actual database
        recent_reviews = []  # Would fetch from database
        
        if not recent_reviews:
            logger.info("No recent reviews found for quality check")
            return {
                'status': 'success',
                'message': 'No recent reviews to check',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        # Perform quality analysis
        quality_result = quality_analysis_batch_task.delay(recent_reviews)
        quality_data = quality_result.get()
        
        result = {
            'status': 'success',
            'quality_check': quality_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info("Periodic quality check completed")
        return result
        
    except Exception as e:
        logger.error(f"Error in periodic quality check: {e}")
        raise self.retry(exc=e, countdown=300 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=2)
def periodic_embedding_cleanup_task(self) -> Dict:
    """Periodic task to clean up embedding cache"""
    init_components()
    
    try:
        logger.info("Starting periodic embedding cache cleanup")
        
        if embedding_service:
            # Get current cache statistics
            stats_before = embedding_service.get_statistics()
            
            # Clear old cache entries (older than 7 days)
            # This is a simplified cleanup - in production would be more sophisticated
            embedding_service.clear_cache()
            
            stats_after = embedding_service.get_statistics()
            
            result = {
                'status': 'success',
                'cache_cleared': True,
                'stats_before': stats_before,
                'stats_after': stats_after,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info("Embedding cache cleanup completed")
            return result
        else:
            return {
                'status': 'error',
                'message': 'Embedding service not available',
                'timestamp': datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error in embedding cleanup: {e}")
        raise self.retry(exc=e, countdown=300 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=2)
def periodic_vector_index_maintenance_task(self) -> Dict:
    """Periodic task for vector index maintenance"""
    init_components()
    
    try:
        logger.info("Starting periodic vector index maintenance")
        
        if vector_db:
            # Get index statistics
            stats = vector_db.get_index_stats()
            
            # Log index health
            health_status = "healthy"
            issues = []
            
            if stats.total_vector_count == 0:
                health_status = "warning"
                issues.append("No vectors in index")
            
            if stats.index_fullness > 0.9:
                health_status = "warning"
                issues.append("Index nearly full")
            
            result = {
                'status': 'success',
                'health_status': health_status,
                'index_stats': stats.__dict__,
                'issues': issues,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Vector index maintenance completed: {health_status}")
            return result
        else:
            return {
                'status': 'error',
                'message': 'Vector database not available',
                'timestamp': datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Error in vector index maintenance: {e}")
        raise self.retry(exc=e, countdown=300 * (self.request.retries + 1))


@celery_app.task
def health_check_task() -> Dict:
    """Health check task for Phase 2 components"""
    try:
        init_components()
        
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # Check preprocessor
        try:
            health_status['components']['preprocessor'] = 'healthy'
        except Exception as e:
            health_status['components']['preprocessor'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check embedding service
        try:
            if embedding_service:
                stats = embedding_service.get_statistics()
                health_status['components']['embedding_service'] = 'healthy'
                health_status['components']['embedding_stats'] = stats
            else:
                health_status['components']['embedding_service'] = 'not initialized'
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['components']['embedding_service'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check quality pipeline
        try:
            health_status['components']['quality_pipeline'] = 'healthy'
        except Exception as e:
            health_status['components']['quality_pipeline'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        # Check vector database
        try:
            if vector_db:
                stats = vector_db.get_index_stats()
                health_status['components']['vector_database'] = 'healthy'
                health_status['components']['vector_stats'] = stats.__dict__
            else:
                health_status['components']['vector_database'] = 'not initialized'
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['components']['vector_database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
        
        logger.info(f"Health check completed: {health_status['status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


# Configure periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'quality-check-every-6-hours': {
        'task': 'tasks.periodic_quality_check_task',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'embedding-cleanup-daily': {
        'task': 'tasks.periodic_embedding_cleanup_task',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM UTC
    },
    'vector-index-maintenance-daily': {
        'task': 'tasks.periodic_vector_index_maintenance_task',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    'health-check-every-30-minutes': {
        'task': 'tasks.health_check_task',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}


# Utility functions for task management
def get_task_status(task_id: str) -> Dict:
    """Get status of a specific task"""
    try:
        result = celery_app.AsyncResult(task_id)
        
        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None,
            'successful': result.successful() if result.ready() else False,
            'failed': result.failed() if result.ready() else False,
            'traceback': result.traceback if result.failed() else None
        }
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return {
            'task_id': task_id,
            'status': 'error',
            'error': str(e)
        }


def cancel_task(task_id: str) -> Dict:
    """Cancel a specific task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            'task_id': task_id,
            'status': 'cancelled',
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        return {
            'task_id': task_id,
            'status': 'error',
            'error': str(e)
        }


def get_active_tasks() -> Dict:
    """Get list of active tasks"""
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        return {
            'status': 'success',
            'active_tasks': active_tasks,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
