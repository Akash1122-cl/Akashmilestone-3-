"""
Main FastAPI application for Phase 1
Provides health check endpoints and ingestion API
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime
import yaml

from database import get_db, Product, IngestionLog, init_database
from config_manager import init_config
from redis_cache import init_redis_cache
from appstore_ingestor import AppStoreIngestor
from googleplay_ingestor import GooglePlayIngestor

# Initialize components
config = init_config()
db_manager = init_database()
redis_cache = init_redis_cache(config.config)

# Setup logging
logging_config = config.get_logging_config()
log_level = getattr(logging, logging_config.get('level', 'INFO'))
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Review Pulse - Phase 1",
    description="Data Ingestion Foundation for Weekly Product Review Pulse",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    logger.info("Starting application")
    try:
        db_manager.create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")
    try:
        db_manager.close()
        redis_cache.close()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Review Pulse - Phase 1",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        redis_cache.client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis stats
    try:
        stats = redis_cache.get_stats()
        health_status["checks"]["redis_stats"] = stats
    except Exception as e:
        health_status["checks"]["redis_stats"] = f"error: {str(e)}"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@app.get("/products")
async def get_products(db: Session = Depends(get_db)):
    """Get all products"""
    products = db.query(Product).all()
    return {
        "count": len(products),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "app_store_id": p.app_store_id,
                "play_store_url": p.play_store_url
            }
            for p in products
        ]
    }


@app.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "id": product.id,
        "name": product.name,
        "app_store_id": product.app_store_id,
        "play_store_url": product.play_store_url,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }


@app.get("/ingestion/logs")
async def get_ingestion_logs(
    product_id: int = None,
    source: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get ingestion logs"""
    query = db.query(IngestionLog)
    
    if product_id:
        query = query.filter(IngestionLog.product_id == product_id)
    
    if source:
        query = query.filter(IngestionLog.source == source)
    
    logs = query.order_by(IngestionLog.started_at.desc()).limit(limit).all()
    
    return {
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "product_id": log.product_id,
                "source": log.source,
                "status": log.status,
                "reviews_collected": log.reviews_collected,
                "reviews_processed": log.reviews_processed,
                "error_message": log.error_message,
                "started_at": log.started_at.isoformat(),
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "duration_seconds": log.duration_seconds
            }
            for log in logs
        ]
    }


@app.post("/ingest/app-store/{product_id}")
async def ingest_app_store(product_id: int, db: Session = Depends(get_db)):
    """Trigger App Store ingestion for a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.app_store_id:
        raise HTTPException(status_code=400, detail="Product has no App Store ID")
    
    # Check if App Store source is enabled for this product
    products = config.get_products()
    product_config = next((p for p in products if p.get('name') == product.name), None)
    if product_config and not product_config.get('sources', {}).get('app_store', True):
        raise HTTPException(status_code=400, detail="App Store ingestion is disabled for this product")
    
    try:
        ingestor = AppStoreIngestor(config.config)
        log = ingestor.ingest_product(product, db)
        
        return {
            "status": "completed",
            "log_id": log.id,
            "product": product.name,
            "source": "app_store",
            "reviews_collected": log.reviews_collected,
            "reviews_processed": log.reviews_processed,
            "duration_seconds": log.duration_seconds,
            "error": log.error_message
        }
    except Exception as e:
        logger.error(f"Error during App Store ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/google-play/{product_id}")
async def ingest_google_play(product_id: int, db: Session = Depends(get_db)):
    """Trigger Google Play ingestion for a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.play_store_url:
        raise HTTPException(status_code=400, detail="Product has no Play Store URL")
    
    # Check if Google Play source is enabled for this product
    products = config.get_products()
    product_config = next((p for p in products if p.get('name') == product.name), None)
    if product_config and not product_config.get('sources', {}).get('google_play', True):
        raise HTTPException(status_code=400, detail="Google Play ingestion is disabled for this product")
    
    try:
        ingestor = GooglePlayIngestor(config.config)
        log = ingestor.ingest_product(product, db)
        
        return {
            "status": "completed",
            "log_id": log.id,
            "product": product.name,
            "source": "google_play",
            "reviews_collected": log.reviews_collected,
            "reviews_processed": log.reviews_processed,
            "duration_seconds": log.duration_seconds,
            "error": log.error_message
        }
    except Exception as e:
        logger.error(f"Error during Google Play ingestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/all")
async def ingest_all_products(db: Session = Depends(get_db)):
    """Trigger ingestion for all enabled products"""
    products = db.query(Product).all()
    results = []
    
    for product in products:
        # Get product configuration to check enabled sources
        products_config = config.get_products()
        product_config = next((p for p in products_config if p.get('name') == product.name), None)
        sources = product_config.get('sources', {}) if product_config else {}
        
        try:
            # App Store ingestion
            if product.app_store_id and sources.get('app_store', True):
                app_store_ingestor = AppStoreIngestor(config.config)
                app_store_log = app_store_ingestor.ingest_product(product, db)
                results.append({
                    "product": product.name,
                    "source": "app_store",
                    "status": app_store_log.status,
                    "reviews_processed": app_store_log.reviews_processed
                })
            
            # Google Play ingestion
            if product.play_store_url and sources.get('google_play', True):
                google_play_ingestor = GooglePlayIngestor(config.config)
                google_play_log = google_play_ingestor.ingest_product(product, db)
                results.append({
                    "product": product.name,
                    "source": "google_play",
                    "status": google_play_log.status,
                    "reviews_processed": google_play_log.reviews_processed
                })
                
        except Exception as e:
            logger.error(f"Error ingesting {product.name}: {e}")
            results.append({
                "product": product.name,
                "source": "error",
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "total_products": len(products),
        "results": results
    }


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    from database import Review
    
    # Product count
    product_count = db.query(Product).count()
    
    # Review count by source
    app_store_reviews = db.query(Review).filter(Review.source == 'app_store').count()
    google_play_reviews = db.query(Review).filter(Review.source == 'google_play').count()
    total_reviews = app_store_reviews + google_play_reviews
    
    # Recent ingestion logs
    recent_logs = db.query(IngestionLog).order_by(
        IngestionLog.started_at.desc()
    ).limit(10).all()
    
    # Redis stats
    redis_stats = redis_cache.get_stats()
    
    return {
        "products": product_count,
        "reviews": {
            "total": total_reviews,
            "app_store": app_store_reviews,
            "google_play": google_play_reviews
        },
        "redis": redis_stats,
        "recent_ingestion": [
            {
                "product_id": log.product_id,
                "source": log.source,
                "status": log.status,
                "reviews_processed": log.reviews_processed,
                "started_at": log.started_at.isoformat()
            }
            for log in recent_logs
        ]
    }


if __name__ == "__main__":
    import uvicorn
    api_config = config.get_api_config()
    uvicorn.run(
        "main:app",
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8000),
        reload=api_config.get('debug', False)
    )
