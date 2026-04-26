"""
Main FastAPI application for Phase 5 MCP Integration and Delivery
Coordinates Docs MCP server, Gmail MCP server, and stakeholder management
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
import uvicorn

from delivery_service import DeliveryService, DeliveryRequest, create_delivery_service
from stakeholder_manager import Stakeholder, DeliveryFrequency, create_stakeholder_manager
from docs_mcp_server import create_docs_mcp_server
from gmail_mcp_server import create_gmail_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for API
class DeliveryRequestModel(BaseModel):
    product_id: str
    report_content: str
    report_format: str = 'html'
    subject: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    custom_recipients: Optional[List[EmailStr]] = None


class StakeholderModel(BaseModel):
    email: EmailStr
    name: str
    role: str
    products: List[str]
    frequency: str  # weekly, biweekly, monthly, on_demand
    active: bool = True
    preferred_format: str = 'html'
    timezone: str = 'UTC'


class DeliveryRuleModel(BaseModel):
    product_id: str
    stakeholders: List[EmailStr]
    frequency: str
    delivery_day: Optional[str] = None
    delivery_time: str = "09:00"
    include_attachments: bool = True
    custom_subject: Optional[str] = None


# Global variables
delivery_service: Optional[DeliveryService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global delivery_service
    
    # Load configuration
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    config = {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/oauth/callback'),
        'default_sender_email': os.getenv('DEFAULT_SENDER_EMAIL'),
        'email_subject_prefix': os.getenv('EMAIL_SUBJECT_PREFIX', 'Review Pulse Report'),
        'oauth_state_secret': os.getenv('OAUTH_STATE_SECRET'),
        'token_encryption_key': os.getenv('TOKEN_ENCRYPTION_KEY'),
        'jwt_secret': os.getenv('JWT_SECRET'),
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'debug': os.getenv('DEBUG', 'false').lower() == 'true'
    }
    
    # Initialize delivery service
    delivery_service = create_delivery_service(config)
    logger.info("Phase 5 MCP Delivery Service initialized")
    
    yield
    
    # Cleanup
    logger.info("Phase 5 MCP Delivery Service shutting down")


# Create FastAPI app
app = FastAPI(
    title="Phase 5: MCP Integration and Delivery",
    description="Google Workspace MCP servers for report delivery",
    version="1.0.0",
    lifespan=lifespan
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Phase 5 MCP Delivery",
        "timestamp": datetime.now().isoformat()
    }


# Authentication endpoints
@app.get("/auth/docs")
async def docs_auth():
    """Start Google Docs OAuth flow"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = await delivery_service.docs_server._handle_mcp_method({
            'id': 'docs_auth',
            'method': 'auth',
            'params': {}
        })
        return result
    except Exception as e:
        logger.error(f"Docs auth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/gmail")
async def gmail_auth():
    """Start Gmail OAuth flow"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = await delivery_service.gmail_server._handle_mcp_method({
            'id': 'gmail_auth',
            'method': 'auth',
            'params': {}
        })
        return result
    except Exception as e:
        logger.error(f"Gmail auth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback for both services"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Process callback
        return await delivery_service.docs_server.app(request.scope, request.receive, request.send)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Delivery endpoints
@app.post("/api/v1/deliver-report")
async def deliver_report(request: DeliveryRequestModel):
    """Deliver report to stakeholders"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        delivery_request = DeliveryRequest(
            product_id=request.product_id,
            report_content=request.report_content,
            report_format=request.report_format,
            subject=request.subject,
            attachments=request.attachments,
            custom_recipients=request.custom_recipients
        )
        
        result = await delivery_service.deliver_report(delivery_request)
        
        return {
            "success": True,
            "result": {
                "product_id": result.product_id,
                "total_recipients": result.total_recipients,
                "successful_deliveries": result.successful_deliveries,
                "failed_deliveries": result.failed_deliveries,
                "document_id": result.document_id,
                "timestamp": result.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Report delivery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/delivery-status/{product_id}")
async def get_delivery_status(product_id: str):
    """Get delivery status for a product"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        status = await delivery_service.get_delivery_status(product_id)
        return status
    except Exception as e:
        logger.error(f"Delivery status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/retry-delivery/{product_id}")
async def retry_delivery(product_id: str):
    """Retry failed deliveries for a product"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        result = await delivery_service.retry_failed_deliveries(product_id)
        
        return {
            "success": True,
            "result": {
                "product_id": result.product_id,
                "total_recipients": result.total_recipients,
                "successful_deliveries": result.successful_deliveries,
                "failed_deliveries": result.failed_deliveries,
                "timestamp": result.timestamp.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Retry delivery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Stakeholder management endpoints
@app.get("/api/v1/stakeholders")
async def get_stakeholders():
    """Get all stakeholders"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stakeholders = delivery_service.stakeholder_manager.export_stakeholders()
        return {"stakeholders": stakeholders}
    except Exception as e:
        logger.error(f"Get stakeholders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/stakeholders")
async def add_stakeholder(stakeholder: StakeholderModel):
    """Add new stakeholder"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Convert frequency string to enum
        frequency_map = {
            'weekly': DeliveryFrequency.WEEKLY,
            'biweekly': DeliveryFrequency.BIWEEKLY,
            'monthly': DeliveryFrequency.MONTHLY,
            'on_demand': DeliveryFrequency.ON_DEMAND
        }
        
        stakeholder_obj = Stakeholder(
            email=stakeholder.email,
            name=stakeholder.name,
            role=stakeholder.role,
            products=stakeholder.products,
            frequency=frequency_map.get(stakeholder.frequency, DeliveryFrequency.WEEKLY),
            active=stakeholder.active,
            preferred_format=stakeholder.preferred_format,
            timezone=stakeholder.timezone
        )
        
        success = delivery_service.stakeholder_manager.add_stakeholder(stakeholder_obj)
        
        if success:
            return {"success": True, "message": "Stakeholder added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add stakeholder")
            
    except Exception as e:
        logger.error(f"Add stakeholder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/stakeholders/{email}")
async def remove_stakeholder(email: str):
    """Remove stakeholder"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        success = delivery_service.stakeholder_manager.remove_stakeholder(email)
        
        if success:
            return {"success": True, "message": "Stakeholder removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Stakeholder not found")
            
    except Exception as e:
        logger.error(f"Remove stakeholder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stakeholders/product/{product_id}")
async def get_stakeholders_for_product(product_id: str):
    """Get stakeholders for a specific product"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stakeholders = delivery_service.stakeholder_manager.get_stakeholders_for_product(product_id)
        return {
            "product_id": product_id,
            "stakeholders": [
                {
                    "email": s.email,
                    "name": s.name,
                    "role": s.role,
                    "frequency": s.frequency.value,
                    "active": s.active,
                    "preferred_format": s.preferred_format,
                    "timezone": s.timezone
                }
                for s in stakeholders
            ]
        }
    except Exception as e:
        logger.error(f"Get product stakeholders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics endpoints
@app.get("/api/v1/statistics/delivery")
async def get_delivery_statistics(product_id: Optional[str] = None, days: int = 30):
    """Get delivery statistics"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        stats = delivery_service.stakeholder_manager.get_delivery_statistics(product_id, days)
        return stats
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MCP direct endpoints (for advanced usage)
@app.post("/mcp/docs")
async def docs_mcp_direct(request: Request):
    """Direct MCP endpoint for Docs server"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        message_data = await request.json()
        result = await delivery_service.docs_server._handle_mcp_method(message_data)
        return result
    except Exception as e:
        logger.error(f"Docs MCP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/gmail")
async def gmail_mcp_direct(request: Request):
    """Direct MCP endpoint for Gmail server"""
    if not delivery_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        message_data = await request.json()
        result = await delivery_service.gmail_server._handle_mcp_method(message_data)
        return result
    except Exception as e:
        logger.error(f"Gmail MCP error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": request.url.path}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
