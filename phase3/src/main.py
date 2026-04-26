"""
Phase 3 Main Application
FastAPI application for clustering and analysis endpoints
"""

import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yaml

from clustering_engine import create_clustering_engine, ClusterResult
from theme_analyzer import create_theme_analyzer, AnalysisResult
from validation_framework import create_validation_framework, ValidationResult
from database import create_phase3_database, AnalysisRun

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# Initialize FastAPI app
app = FastAPI(
    title="Phase 3: Analysis and Clustering API",
    description="API for review clustering, theme analysis, and validation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get('security', {}).get('cors_origins', ['*']),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Initialize components
clustering_engine = create_clustering_engine(config)
theme_analyzer = create_theme_analyzer(config)
validation_framework = create_validation_framework(config)
database = create_phase3_database(config)

# Pydantic models
class ClusteringRequest(BaseModel):
    embeddings: List[List[float]]
    review_ids: List[str]
    optimize_parameters: bool = False


class ClusteringResponse(BaseModel):
    success: bool
    cluster_result: Optional[Dict]
    error: Optional[str]


class ThemeAnalysisRequest(BaseModel):
    clusters: Dict[int, List[Dict]]
    reviews: List[Dict]


class ThemeAnalysisResponse(BaseModel):
    success: bool
    analysis_result: Optional[Dict]
    error: Optional[str]


class ValidationRequest(BaseModel):
    themes: List[Dict]
    reviews: List[Dict]


class ValidationResponse(BaseModel):
    success: bool
    validation_result: Optional[Dict]
    error: Optional[str]


class FullAnalysisRequest(BaseModel):
    product_id: int
    product_name: str
    embeddings: List[List[float]]
    review_ids: List[str]
    reviews: List[Dict]
    optimize_parameters: bool = False


class FullAnalysisResponse(BaseModel):
    success: bool
    analysis_run_id: Optional[int]
    themes: Optional[List[Dict]]
    validation_result: Optional[Dict]
    error: Optional[str]


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "3",
        "components": {
            "clustering_engine": "available",
            "theme_analyzer": "available",
            "validation_framework": "available",
            "database": "connected"
        }
    }


# Clustering endpoints
@app.post("/api/v1/cluster", response_model=ClusteringResponse)
async def cluster_reviews(request: ClusteringRequest):
    """
    Cluster review embeddings using UMAP + HDBSCAN
    
    Args:
        request: ClusteringRequest with embeddings and review IDs
        
    Returns:
        ClusteringResponse with cluster results
    """
    try:
        logger.info(f"Clustering {len(request.embeddings)} reviews")
        
        # Optimize parameters if requested
        if request.optimize_parameters:
            optimization_result = clustering_engine.optimize_parameters(
                request.embeddings, request.review_ids
            )
            logger.info(f"Parameter optimization: {optimization_result}")
        
        # Perform clustering
        cluster_result = clustering_engine.cluster_reviews(
            request.embeddings, request.review_ids
        )
        
        return ClusteringResponse(
            success=True,
            cluster_result=cluster_result.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Clustering failed: {e}")
        return ClusteringResponse(
            success=False,
            cluster_result=None,
            error=str(e)
        )


@app.post("/api/v1/optimize-parameters")
async def optimize_clustering_parameters(request: ClusteringRequest):
    """
    Optimize clustering parameters to achieve target cluster count
    
    Args:
        request: ClusteringRequest with embeddings and review IDs
        
    Returns:
        Optimization result
    """
    try:
        logger.info("Optimizing clustering parameters")
        
        result = clustering_engine.optimize_parameters(
            request.embeddings, request.review_ids
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Parameter optimization failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Theme analysis endpoints
@app.post("/api/v1/analyze-themes", response_model=ThemeAnalysisResponse)
async def analyze_themes(request: ThemeAnalysisRequest):
    """
    Analyze clusters to generate themes with names, descriptions, and action ideas
    
    Args:
        request: ThemeAnalysisRequest with clusters and reviews
        
    Returns:
        ThemeAnalysisResponse with analysis results
    """
    try:
        logger.info(f"Analyzing themes for {len(request.clusters)} clusters")
        
        analysis_result = theme_analyzer.analyze_themes(
            request.clusters, request.reviews
        )
        
        return ThemeAnalysisResponse(
            success=True,
            analysis_result=analysis_result.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Theme analysis failed: {e}")
        return ThemeAnalysisResponse(
            success=False,
            analysis_result=None,
            error=str(e)
        )


# Validation endpoints
@app.post("/api/v1/validate", response_model=ValidationResponse)
async def validate_analysis(request: ValidationRequest):
    """
    Validate analysis results including quotes, themes, and action ideas
    
    Args:
        request: ValidationRequest with themes and reviews
        
    Returns:
        ValidationResponse with validation results
    """
    try:
        logger.info(f"Validating {len(request.themes)} themes")
        
        validation_result = validation_framework.validate_analysis(
            request.themes, request.reviews
        )
        
        return ValidationResponse(
            success=True,
            validation_result=validation_result.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return ValidationResponse(
            success=False,
            validation_result=None,
            error=str(e)
        )


# Full analysis pipeline endpoint
@app.post("/api/v1/full-analysis", response_model=FullAnalysisResponse)
async def full_analysis(request: FullAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Execute full analysis pipeline: clustering → theme analysis → validation
    
    Args:
        request: FullAnalysisRequest with all required data
        background_tasks: FastAPI background tasks
        
    Returns:
        FullAnalysisResponse with complete analysis results
    """
    try:
        logger.info(f"Starting full analysis for product {request.product_id}")
        start_time = datetime.utcnow()
        
        # Step 1: Clustering
        logger.info("Step 1: Clustering reviews")
        if request.optimize_parameters:
            clustering_engine.optimize_parameters(request.embeddings, request.review_ids)
        
        cluster_result = clustering_engine.cluster_reviews(
            request.embeddings, request.review_ids
        )
        
        # Step 2: Organize reviews by cluster
        logger.info("Step 2: Organizing reviews by cluster")
        clusters = {}
        for review_id, cluster_id in zip(request.review_ids, cluster_result.cluster_labels):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            
            # Find review data
            review_data = next((r for r in request.reviews if r.get('id') == review_id), None)
            if review_data:
                clusters[cluster_id].append(review_data)
        
        # Step 3: Theme analysis
        logger.info("Step 3: Analyzing themes")
        analysis_result = theme_analyzer.analyze_themes(clusters, request.reviews)
        
        # Step 4: Validation
        logger.info("Step 4: Validating analysis")
        themes_dict = [theme.__dict__ for theme in analysis_result.themes]
        validation_result = validation_framework.validate_analysis(
            themes_dict, request.reviews
        )
        
        # Step 5: Save to database
        logger.info("Step 5: Saving to database")
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        analysis_run = AnalysisRun(
            id=None,
            product_id=request.product_id,
            product_name=request.product_name,
            analysis_timestamp=datetime.utcnow().isoformat(),
            total_reviews=len(request.reviews),
            num_clusters=cluster_result.cluster_metadata.get('num_clusters', 0),
            num_themes=len(analysis_result.themes),
            processing_time_seconds=processing_time,
            clustering_quality_metrics=cluster_result.quality_metrics,
            validation_result=validation_result.__dict__,
            status='completed'
        )
        
        analysis_run_id = database.save_analysis_run(analysis_run)
        
        # Save themes
        database.save_themes(analysis_run_id, themes_dict)
        
        # Save cluster assignments
        database.save_cluster_assignments(
            analysis_run_id,
            cluster_result.cluster_labels,
            request.review_ids
        )
        
        # Save validation result
        database.save_validation_result(analysis_run_id, validation_result.__dict__)
        
        logger.info(f"Full analysis completed in {processing_time:.2f}s")
        
        return FullAnalysisResponse(
            success=True,
            analysis_run_id=analysis_run_id,
            themes=themes_dict,
            validation_result=validation_result.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Full analysis failed: {e}")
        return FullAnalysisResponse(
            success=False,
            analysis_run_id=None,
            themes=None,
            validation_result=None,
            error=str(e)
        )


# Database query endpoints
@app.get("/api/v1/analysis/{analysis_run_id}")
async def get_analysis_run(analysis_run_id: int):
    """
    Get analysis run by ID
    
    Args:
        analysis_run_id: ID of the analysis run
        
    Returns:
        Analysis run data with themes
    """
    try:
        analysis_run = database.get_analysis_run(analysis_run_id)
        
        if not analysis_run:
            raise HTTPException(status_code=404, detail="Analysis run not found")
        
        themes = database.get_themes_by_analysis_run(analysis_run_id)
        
        return {
            "analysis_run": analysis_run,
            "themes": themes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/product/{product_id}/latest-analysis")
async def get_latest_analysis(product_id: int):
    """
    Get latest analysis run for a product
    
    Args:
        product_id: ID of the product
        
    Returns:
        Latest analysis run data with themes
    """
    try:
        analysis_run = database.get_latest_analysis_run(product_id)
        
        if not analysis_run:
            raise HTTPException(status_code=404, detail="No analysis found for product")
        
        themes = database.get_themes_by_analysis_run(analysis_run['id'])
        
        return {
            "analysis_run": analysis_run,
            "themes": themes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Shutdown handler
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Phase 3 API")
    database.close()


if __name__ == "__main__":
    import uvicorn
    
    api_config = config.get('api', {})
    uvicorn.run(
        app,
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8002),
        log_level=api_config.get('log_level', 'info').lower()
    )
