"""
Phase 4 Main Application
FastAPI application for report generation endpoints
"""

import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yaml

from narrative_builder import create_narrative_builder, NarrativeResult
from report_formatter import create_report_formatter, FormattedReport
from quality_assurance import create_quality_assurance, QualityReport

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
    title="Phase 4: Report Generation API",
    description="API for narrative building, report formatting, and quality assurance",
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
narrative_builder = create_narrative_builder(config)
report_formatter = create_report_formatter(config)
quality_assurance = create_quality_assurance(config)

# Pydantic models
class NarrativeRequest(BaseModel):
    analysis_result: Dict
    themes: List[Dict]


class NarrativeResponse(BaseModel):
    success: bool
    narrative_result: Optional[Dict]
    error: Optional[str]


class FormatRequest(BaseModel):
    narrative_result: Dict
    output_format: str = 'html'


class FormatResponse(BaseModel):
    success: bool
    formatted_report: Optional[Dict]
    error: Optional[str]


class ValidationRequest(BaseModel):
    narrative_result: Dict
    formatted_report: Dict


class ValidationResponse(BaseModel):
    success: bool
    quality_report: Optional[Dict]
    error: Optional[str]


class FullReportRequest(BaseModel):
    analysis_result: Dict
    themes: List[Dict]
    output_format: str = 'html'


class FullReportResponse(BaseModel):
    success: bool
    narrative_result: Optional[Dict]
    formatted_report: Optional[Dict]
    quality_report: Optional[Dict]
    error: Optional[str]


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "4",
        "components": {
            "narrative_builder": "available",
            "report_formatter": "available",
            "quality_assurance": "available"
        }
    }


# Narrative builder endpoints
@app.post("/api/v1/build-narrative", response_model=NarrativeResponse)
async def build_narrative(request: NarrativeRequest):
    """
    Build narrative from analysis results and themes
    
    Args:
        request: NarrativeRequest with analysis result and themes
        
    Returns:
        NarrativeResponse with narrative result
    """
    try:
        logger.info(f"Building narrative for {len(request.themes)} themes")
        
        narrative_result = narrative_builder.build_narrative(
            request.analysis_result, request.themes
        )
        
        return NarrativeResponse(
            success=True,
            narrative_result=narrative_result.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Narrative building failed: {e}")
        return NarrativeResponse(
            success=False,
            narrative_result=None,
            error=str(e)
        )


# Report formatter endpoints
@app.post("/api/v1/format-report", response_model=FormatResponse)
async def format_report(request: FormatRequest):
    """
    Format narrative result into a complete report
    
    Args:
        request: FormatRequest with narrative result and output format
        
    Returns:
        FormatResponse with formatted report
    """
    try:
        logger.info(f"Formatting report in {request.output_format} format")
        
        formatted_report = report_formatter.format_report(
            request.narrative_result, request.output_format
        )
        
        return FormatResponse(
            success=True,
            formatted_report=formatted_report.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Report formatting failed: {e}")
        return FormatResponse(
            success=False,
            formatted_report=None,
            error=str(e)
        )


# Quality assurance endpoints
@app.post("/api/v1/validate-report", response_model=ValidationResponse)
async def validate_report(request: ValidationRequest):
    """
    Validate report for quality
    
    Args:
        request: ValidationRequest with narrative and formatted report
        
    Returns:
        ValidationResponse with quality report
    """
    try:
        logger.info("Starting report validation")
        
        quality_report = quality_assurance.validate_report(
            request.narrative_result, request.formatted_report
        )
        
        return ValidationResponse(
            success=True,
            quality_report=quality_report.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Report validation failed: {e}")
        return ValidationResponse(
            success=False,
            quality_report=None,
            error=str(e)
        )


# Full report pipeline endpoint
@app.post("/api/v1/generate-full-report", response_model=FullReportResponse)
async def generate_full_report(request: FullReportRequest):
    """
    Execute full report generation pipeline: narrative → format → validate
    
    Args:
        request: FullReportRequest with all required data
        
    Returns:
        FullReportResponse with complete report generation results
    """
    try:
        logger.info("Starting full report generation pipeline")
        
        # Step 1: Build narrative
        logger.info("Step 1: Building narrative")
        narrative_result = narrative_builder.build_narrative(
            request.analysis_result, request.themes
        )
        
        # Step 2: Format report
        logger.info("Step 2: Formatting report")
        formatted_report = report_formatter.format_report(
            narrative_result.__dict__, request.output_format
        )
        
        # Step 3: Validate report
        logger.info("Step 3: Validating report")
        quality_report = quality_assurance.validate_report(
            narrative_result.__dict__, formatted_report.__dict__
        )
        
        logger.info("Full report generation completed successfully")
        
        return FullReportResponse(
            success=True,
            narrative_result=narrative_result.__dict__,
            formatted_report=formatted_report.__dict__,
            quality_report=quality_report.__dict__,
            error=None
        )
        
    except Exception as e:
        logger.error(f"Full report generation failed: {e}")
        return FullReportResponse(
            success=False,
            narrative_result=None,
            formatted_report=None,
            quality_report=None,
            error=str(e)
        )


# Template rendering endpoint
@app.post("/api/v1/render-template")
async def render_template(template_name: str, context: Dict):
    """
    Render a Jinja2 template with context
    
    Args:
        template_name: Name of the template file
        context: Context dictionary for template rendering
        
    Returns:
        Rendered template content
    """
    try:
        logger.info(f"Rendering template: {template_name}")
        
        rendered = narrative_builder.render_template(template_name, context)
        
        return {
            "success": True,
            "rendered_content": rendered
        }
        
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Shutdown handler
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Phase 4 API")


if __name__ == "__main__":
    import uvicorn
    
    api_config = config.get('api', {})
    uvicorn.run(
        app,
        host=api_config.get('host', '0.0.0.0'),
        port=api_config.get('port', 8003),
        log_level=api_config.get('log_level', 'info').lower()
    )
