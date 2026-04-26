"""
Phase 2 FastAPI Application - Data Processing Pipeline
Provides endpoints for review preprocessing, embedding generation, and quality analysis
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

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

# Initialize FastAPI app
app = FastAPI(
    title="Review Pulse - Phase 2",
    description="Data Processing Pipeline for Review Analysis",
    version="2.0.0"
)

# Global components
preprocessor = None
embedding_service = None
quality_pipeline = None
vector_db = None
config = None


# Pydantic models
class ReviewInput(BaseModel):
    """Input model for single review"""
    external_review_id: str
    title: str
    review_text: str
    author_name: str
    rating: int = Field(ge=1, le=5)
    review_date: str
    review_url: str
    version: str
    source: str
    product_id: int


class BatchReviewInput(BaseModel):
    """Input model for batch of reviews"""
    reviews: List[ReviewInput]


class ProcessingRequest(BaseModel):
    """Request for processing reviews"""
    reviews: List[Dict]
    options: Optional[Dict[str, Any]] = {}


class EmbeddingRequest(BaseModel):
    """Request for embedding generation"""
    text: str
    use_cache: bool = True


class SimilaritySearchRequest(BaseModel):
    """Request for similarity search"""
    query_text: Optional[str] = None
    query_vector: Optional[List[float]] = None
    top_k: int = 10
    filter_dict: Optional[Dict[str, Any]] = None


class QualityAnalysisRequest(BaseModel):
    """Request for quality analysis"""
    reviews: List[Dict]
    include_anomalies: bool = True


# Dependency functions
def get_preprocessor() -> ReviewPreprocessor:
    """Get preprocessor instance"""
    global preprocessor
    if preprocessor is None:
        raise HTTPException(status_code=503, detail="Preprocessor not initialized")
    return preprocessor


def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance"""
    global embedding_service
    if embedding_service is None:
        raise HTTPException(status_code=503, detail="Embedding service not initialized")
    return embedding_service


def get_quality_pipeline() -> DataQualityPipeline:
    """Get quality pipeline instance"""
    global quality_pipeline
    if quality_pipeline is None:
        raise HTTPException(status_code=503, detail="Quality pipeline not initialized")
    return quality_pipeline


def get_vector_db() -> VectorDatabase:
    """Get vector database instance"""
    global vector_db
    if vector_db is None:
        raise HTTPException(status_code=503, detail="Vector database not initialized")
    return vector_db


@app.on_event("startup")
async def startup_event():
    """Initialize Phase 2 components"""
    global preprocessor, embedding_service, quality_pipeline, vector_db, config
    
    logger.info("Starting Phase 2 Data Processing Pipeline")
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize components
        preprocessor = create_preprocessor(config)
        embedding_service = create_embedding_service(config)
        quality_pipeline = create_quality_pipeline(config)
        vector_db = create_vector_database(config)
        
        logger.info("Phase 2 components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Phase 2 components: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Phase 2 application")
    
    try:
        # Cleanup components
        if embedding_service:
            embedding_service.clear_cache()
        
        logger.info("Phase 2 shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def load_config() -> dict:
    """Load configuration"""
    import os
    import yaml
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Review Pulse - Phase 2",
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "preprocessor": preprocessor is not None,
            "embedding_service": embedding_service is not None,
            "quality_pipeline": quality_pipeline is not None,
            "vector_database": vector_db is not None
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check preprocessor
    try:
        health_status["checks"]["preprocessor"] = "healthy"
    except Exception as e:
        health_status["checks"]["preprocessor"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check embedding service
    try:
        if embedding_service:
            stats = embedding_service.get_statistics()
            health_status["checks"]["embedding_service"] = "healthy"
            health_status["checks"]["embedding_stats"] = stats
        else:
            health_status["checks"]["embedding_service"] = "not initialized"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["embedding_service"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check quality pipeline
    try:
        health_status["checks"]["quality_pipeline"] = "healthy"
    except Exception as e:
        health_status["checks"]["quality_pipeline"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check vector database
    try:
        if vector_db:
            stats = vector_db.get_index_stats()
            health_status["checks"]["vector_database"] = "healthy"
            health_status["checks"]["vector_stats"] = asdict(stats)
        else:
            health_status["checks"]["vector_database"] = "not initialized"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["vector_database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


# Preprocessing endpoints
@app.post("/preprocess/single")
async def preprocess_single_review(
    review: ReviewInput,
    preprocessor: ReviewPreprocessor = Depends(get_preprocessor)
):
    """Preprocess a single review"""
    try:
        review_dict = review.dict()
        processed_review = preprocessor.process_review(review_dict)
        
        return {
            "status": "success",
            "processed_review": {
                "external_review_id": processed_review.external_review_id,
                "title": processed_review.title,
                "cleaned_text": processed_review.cleaned_text,
                "author_name": processed_review.author_name,
                "rating": processed_review.rating,
                "language": processed_review.language,
                "sentiment_score": processed_review.sentiment_score,
                "text_length": processed_review.text_length,
                "word_count": processed_review.word_count,
                "quality_score": processed_review.quality_score,
                "status": processed_review.status.value,
                "filter_reason": processed_review.filter_reason,
                "processed_at": processed_review.processed_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error preprocessing review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/preprocess/batch")
async def preprocess_batch_reviews(
    batch: BatchReviewInput,
    preprocessor: ReviewPreprocessor = Depends(get_preprocessor)
):
    """Preprocess a batch of reviews"""
    try:
        reviews_dict = [review.dict() for review in batch.reviews]
        processed_reviews = preprocessor.process_batch(reviews_dict)
        
        # Generate statistics
        stats = preprocessor.get_processing_stats(processed_reviews)
        
        # Convert processed reviews to dict format
        processed_dicts = []
        for review in processed_reviews:
            processed_dicts.append({
                "external_review_id": review.external_review_id,
                "title": review.title,
                "cleaned_text": review.cleaned_text,
                "author_name": review.author_name,
                "rating": review.rating,
                "language": review.language,
                "sentiment_score": review.sentiment_score,
                "text_length": review.text_length,
                "word_count": review.word_count,
                "quality_score": review.quality_score,
                "status": review.status.value,
                "filter_reason": review.filter_reason,
                "processed_at": review.processed_at.isoformat()
            })
        
        return {
            "status": "success",
            "statistics": stats,
            "processed_reviews": processed_dicts
        }
        
    except Exception as e:
        logger.error(f"Error preprocessing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Embedding endpoints
@app.post("/embeddings/generate")
async def generate_embedding(
    request: EmbeddingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Generate embedding for text"""
    try:
        result = embedding_service.generate_single_embedding(request.text)
        
        if result.success:
            return {
                "status": "success",
                "embedding_id": result.embedding_id,
                "embedding": result.embedding,
                "model_used": result.model_used,
                "processing_time": result.processing_time,
                "token_count": result.token_count
            }
        else:
            return {
                "status": "error",
                "error": result.error_message
            }
            
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embeddings/batch")
async def generate_batch_embeddings(
    texts: List[str],
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Generate embeddings for batch of texts"""
    try:
        results = embedding_service.generate_batch_embeddings(texts)
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        return {
            "status": "success",
            "total": len(results),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "embeddings": [
                {
                    "text": result.text,
                    "embedding_id": result.embedding_id,
                    "embedding": result.embedding,
                    "model_used": result.model_used,
                    "processing_time": result.processing_time,
                    "token_count": result.token_count
                }
                for result in successful_results
            ],
            "errors": [
                {
                    "text": result.text,
                    "error": result.error_message
                }
                for result in failed_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/embeddings/stats")
async def get_embedding_stats(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Get embedding service statistics"""
    try:
        stats = embedding_service.get_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Quality analysis endpoints
@app.post("/quality/analyze")
async def analyze_quality(
    request: QualityAnalysisRequest,
    quality_pipeline: DataQualityPipeline = Depends(get_quality_pipeline)
):
    """Analyze quality of reviews"""
    try:
        quality_report = quality_pipeline.generate_quality_report(request.reviews)
        
        return {
            "status": "success",
            "report": quality_report
        }
        
    except Exception as e:
        logger.error(f"Error analyzing quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/quality/metrics")
async def get_quality_metrics(
    reviews: List[Dict],
    quality_pipeline: DataQualityPipeline = Depends(get_quality_pipeline)
):
    """Get quality metrics for reviews"""
    try:
        metrics = quality_pipeline.calculate_batch_metrics(reviews)
        
        return {
            "status": "success",
            "metrics": asdict(metrics)
        }
        
    except Exception as e:
        logger.error(f"Error getting quality metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Vector database endpoints
@app.post("/vectors/index")
async def create_vector_index(
    reviews: List[Dict],
    vector_db: VectorDatabase = Depends(get_vector_db)
):
    """Create vector index from reviews"""
    try:
        success = vector_db.create_index_from_reviews(reviews)
        
        if success:
            stats = vector_db.get_index_stats()
            return {
                "status": "success",
                "message": f"Vector index created with {len(reviews)} reviews",
                "statistics": asdict(stats)
            }
        else:
            return {
                "status": "error",
                "message": "Failed to create vector index"
            }
            
    except Exception as e:
        logger.error(f"Error creating vector index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vectors/search")
async def search_similar_vectors(
    request: SimilaritySearchRequest,
    vector_db: VectorDatabase = Depends(get_vector_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """Search for similar vectors"""
    try:
        # Get query vector
        if request.query_text:
            # Generate embedding from text
            embedding_result = embedding_service.generate_single_embedding(request.query_text)
            if not embedding_result.success:
                raise HTTPException(status_code=400, detail="Failed to generate embedding for query text")
            query_vector = embedding_result.embedding
        elif request.query_vector:
            query_vector = request.query_vector
        else:
            raise HTTPException(status_code=400, detail="Either query_text or query_vector must be provided")
        
        # Search for similar vectors
        results = vector_db.search_similar(query_vector, request.top_k, request.filter_dict)
        
        return {
            "status": "success",
            "query": {
                "text": request.query_text,
                "top_k": request.top_k,
                "filter": request.filter_dict
            },
            "results": [
                {
                    "id": result.id,
                    "score": result.score,
                    "metadata": result.metadata
                }
                for result in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Error searching vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vectors/stats")
async def get_vector_stats(
    vector_db: VectorDatabase = Depends(get_vector_db)
):
    """Get vector database statistics"""
    try:
        stats = vector_db.get_index_stats()
        
        return {
            "status": "success",
            "statistics": asdict(stats)
        }
        
    except Exception as e:
        logger.error(f"Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Complete processing pipeline
@app.post("/process/complete")
async def complete_processing_pipeline(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    preprocessor: ReviewPreprocessor = Depends(get_preprocessor),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    quality_pipeline: DataQualityPipeline = Depends(get_quality_pipeline),
    vector_db: VectorDatabase = Depends(get_vector_db)
):
    """Complete processing pipeline: preprocess -> embed -> analyze -> index"""
    try:
        logger.info(f"Starting complete processing pipeline for {len(request.reviews)} reviews")
        
        # Step 1: Preprocess reviews
        processed_reviews = preprocessor.process_batch(request.reviews)
        
        # Step 2: Generate embeddings
        reviews_with_embeddings = embedding_service.process_reviews_embeddings(processed_reviews)
        
        # Step 3: Quality analysis
        quality_report = quality_pipeline.generate_quality_report(reviews_with_embeddings)
        
        # Step 4: Create vector index (async)
        def create_index():
            try:
                vector_db.create_index_from_reviews(reviews_with_embeddings)
                logger.info("Vector index creation completed")
            except Exception as e:
                logger.error(f"Vector index creation failed: {e}")
        
        background_tasks.add_task(create_index)
        
        # Generate processing statistics
        processing_stats = {
            "total_reviews": len(request.reviews),
            "processed_reviews": len(processed_reviews),
            "embedded_reviews": len([r for r in reviews_with_embeddings if r.get('embedding')]),
            "processing_time": datetime.utcnow().isoformat(),
            "quality_grade": quality_report.get('quality_summary', {}).get('overall_grade', 'N/A')
        }
        
        return {
            "status": "success",
            "processing_stats": processing_stats,
            "quality_report": quality_report,
            "message": "Processing pipeline completed successfully. Vector index creation in progress."
        }
        
    except Exception as e:
        logger.error(f"Error in complete processing pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics and monitoring
@app.get("/stats/overview")
async def get_overview_stats():
    """Get overview statistics for all components"""
    try:
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        # Preprocessor stats
        if preprocessor:
            stats["components"]["preprocessor"] = "initialized"
        
        # Embedding service stats
        if embedding_service:
            stats["components"]["embedding_service"] = embedding_service.get_statistics()
        
        # Vector database stats
        if vector_db:
            stats["components"]["vector_database"] = asdict(vector_db.get_index_stats())
        
        return {
            "status": "success",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting overview stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    api_config = config.get('api', {}) if config else {}
    uvicorn.run(
        "main:app",
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8001),  # Different port for Phase 2
        reload=api_config.get('debug', False)
    )
