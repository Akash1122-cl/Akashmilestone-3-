"""
Review Pulse Backend API Gateway
Main FastAPI application entry point
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting Review Pulse API Gateway")
    
    # Initialize services
    await initialize_services()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Review Pulse API Gateway")
    await cleanup_services()


async def initialize_services():
    """Initialize all services"""
    try:
        # Database
        from src.database import engine
        from src.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized")
        
        # Redis
        from src.services.cache import cache_service
        await cache_service.ping()
        logger.info("Redis connection established")
        
        # Phase service clients
        from src.services.gateway import gateway_service
        await gateway_service.initialize_clients()
        logger.info("Phase service clients initialized")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise


async def cleanup_services():
    """Cleanup all services"""
    try:
        from src.services.cache import cache_service
        await cache_service.close()
        logger.info("Services cleaned up")
    except Exception as e:
        logger.error("Error during cleanup", error=str(e))


# Create FastAPI app
app = FastAPI(
    title="Review Pulse API Gateway",
    description="Unified API gateway for Review Pulse multi-phase system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://reviewpulse.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.reviewpulse.dev"]
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for all requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record metrics
    method = request.method
    path = request.url.path
    status_code = response.status_code
    
    REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    
    # Log request
    logger.info(
        "HTTP request",
        method=method,
        path=path,
        status_code=status_code,
        duration=time.time() - start_time
    )
    
    return response


# Include routers
from src.api.v1.auth import auth_router
from src.api.v1.dashboard import dashboard_router
from src.api.v1.reviews import reviews_router
from src.api.v1.analysis import analysis_router
from src.api.v1.reports import reports_router
from src.api.v1.stakeholders import stakeholders_router
from src.api.v1.websocket import websocket_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(reviews_router, prefix="/api/v1/reviews", tags=["Reviews"])
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(stakeholders_router, prefix="/api/v1/stakeholders", tags=["Stakeholders"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with all services"""
    from src.health import health_checker
    
    try:
        health_status = await health_checker.check_health()
        return health_status
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@app.get("/metrics", tags=["Health"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Review Pulse API Gateway",
        "version": "1.0.0",
        "description": "Unified API gateway for Review Pulse multi-phase system",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": time.time()
        }
    )


# Development server startup
if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 9000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info("Starting development server", host=host, port=port, debug=debug)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
