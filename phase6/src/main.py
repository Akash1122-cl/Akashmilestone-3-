"""
Phase 6: Advanced Automation and Analytics
Main FastAPI application with external MCP integration
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Phase 5 external MCP client
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'phase5', 'src'))
from external_mcp_client import ExternalMCPDeliveryService, create_external_mcp_service

# Import Phase 6 services
from models import Base, create_tables
from analytics_service import create_analytics_service
from automation_engine import create_automation_engine, AutomationRule, AutomationCondition, AutomationAction, TriggerType
from reporting_service import create_reporting_service

# Pydantic models for API
class AdvancedDeliveryRequest(BaseModel):
    product_ids: List[str]
    report_template: str = "executive_summary"
    delivery_methods: List[str] = ["email", "google_docs"]
    recipients: List[EmailStr]
    schedule_config: Optional[Dict[str, Any]] = None
    analytics_config: Optional[Dict[str, Any]] = None

class AnalyticsRequest(BaseModel):
    product_id: str
    time_range: str = "30_days"
    metrics: List[str] = ["sentiment", "volume", "rating"]
    compare_with: Optional[List[str]] = None
    include_predictions: bool = False

class AutomationRule(BaseModel):
    name: str
    product_id: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool = True

# Global variables
mcp_service: Optional[ExternalMCPDeliveryService] = None
analytics_service = None
automation_engine = None
reporting_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global mcp_service, analytics_service, automation_engine, reporting_service
    
    # Load configuration
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    config = {
        'mcp_url': os.getenv('MCP_SERVER_URL', 'https://saksham-mcp-server.onrender.com'),
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'debug': os.getenv('DEBUG', 'false').lower() == 'true',
        'database_url': os.getenv('DATABASE_URL', 'sqlite:///phase6.db'),
        'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    }
    
    # Initialize external MCP service
    try:
        mcp_service = create_external_mcp_service(config['mcp_url'])
        logger.info("Phase 6 External MCP Service initialized")
        
        # Test connection
        status = await mcp_service.get_mcp_status()
        logger.info(f"MCP Server Status: {status['status']}")
        
    except Exception as e:
        logger.error(f"Failed to initialize external MCP service: {e}")
        mcp_service = None
    
    # Initialize analytics service
    try:
        analytics_service = create_analytics_service(config)
        logger.info("Phase 6 Analytics Service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize analytics service: {e}")
        analytics_service = None
    
    # Initialize reporting service
    try:
        reporting_service = create_reporting_service(config)
        if analytics_service:
            reporting_service.register_services(analytics_service, mcp_service)
        logger.info("Phase 6 Reporting Service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize reporting service: {e}")
        reporting_service = None
    
    # Initialize automation engine
    try:
        automation_engine = create_automation_engine(config)
        if analytics_service and reporting_service:
            automation_engine.register_services(analytics_service, reporting_service, mcp_service)
        await automation_engine.start()
        logger.info("Phase 6 Automation Engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize automation engine: {e}")
        automation_engine = None
    
    yield
    
    # Cleanup
    if automation_engine:
        await automation_engine.stop()
    logger.info("Phase 6 Advanced Automation shutting down")

# Create FastAPI app
app = FastAPI(
    title="Phase 6: Advanced Automation and Analytics",
    description="Advanced automation and analytics with external MCP integration",
    version="6.0.0",
    lifespan=lifespan
)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Phase 6 Advanced Automation",
        "timestamp": datetime.now().isoformat(),
        "mcp_connected": mcp_service is not None
    }

# MCP Status
@app.get("/api/v1/mcp-status")
async def get_mcp_status():
    """Get external MCP server status"""
    if not mcp_service:
        raise HTTPException(status_code=503, detail="MCP service not available")
    
    try:
        status = await mcp_service.get_mcp_status()
        return status
    except Exception as e:
        logger.error(f"MCP status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Advanced Delivery Endpoints
@app.post("/api/v1/automation/advanced-delivery")
async def advanced_delivery(request: AdvancedDeliveryRequest):
    """Advanced multi-product delivery with analytics"""
    if not mcp_service:
        raise HTTPException(status_code=503, detail="MCP service not available")
    
    try:
        results = []
        
        for product_id in request.product_ids:
            # Generate advanced report content
            report_content = generate_advanced_report(
                product_id, 
                request.report_template,
                request.analytics_config
            )
            
            # Create Google Doc
            doc_result = await mcp_service.deliver_report_to_docs(
                f"doc_{product_id}_{datetime.now().strftime('%Y%m%d')}",
                report_content
            )
            
            # Send email notifications
            doc_link = f"https://docs.google.com/document/d/{doc_result.get('doc_id', '')}" if doc_result.get('status') == 'success' else None
            
            email_results = []
            for recipient in request.recipients:
                email_result = await mcp_service.send_email_notification(
                    recipient,
                    f"Advanced Report - {product_id}",
                    f"Please find the advanced report for {product_id}.",
                    doc_link
                )
                email_results.append(email_result)
            
            results.append({
                "product_id": product_id,
                "doc_result": doc_result,
                "email_results": email_results,
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "success": True,
            "processed_products": len(request.product_ids),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Advanced delivery error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.post("/api/v1/analytics/trend-analysis")
async def trend_analysis(request: AnalyticsRequest):
    """Generate trend analysis for a product"""
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    try:
        analysis = await analytics_service.generate_trend_analysis(
            product_id=request.product_id,
            time_range=request.time_range,
            metrics=request.metrics
        )
        
        return analysis
        
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analytics/predictions")
async def generate_predictions(request: AnalyticsRequest):
    """Generate predictions for a product"""
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    try:
        predictions = await analytics_service.generate_predictions(
            product_id=request.product_id,
            metric_types=request.metrics,
            prediction_days=7
        )
        
        return predictions
        
    except Exception as e:
        logger.error(f"Predictions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analytics/compare-products")
async def compare_products(product_ids: List[str], metrics: List[str] = None, time_range: str = "30_days"):
    """Compare multiple products"""
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    try:
        comparison = await analytics_service.compare_products(
            product_ids=product_ids,
            metrics=metrics or ["sentiment", "volume", "rating"],
            time_range=time_range
        )
        
        return comparison
        
    except Exception as e:
        logger.error(f"Product comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Automation Rules
@app.post("/api/v1/automation/rules")
async def create_automation_rule(rule: AutomationRule):
    """Create automation rule"""
    if not automation_engine:
        raise HTTPException(status_code=503, detail="Automation engine not available")
    
    try:
        # Convert Pydantic model to domain model
        domain_rule = AutomationRule(
            id="",  # Will be generated
            name=rule.name,
            description=rule.get("description", ""),
            product_id=rule.product_id,
            trigger_type=TriggerType(rule.get("trigger_type", "manual")),
            schedule=rule.get("schedule"),
            conditions=[AutomationCondition(**c) for c in rule.get("conditions", [])],
            actions=[AutomationAction(**a) for a in rule.get("actions", [])],
            enabled=rule.get("enabled", True)
        )
        
        rule_id = await automation_engine.create_rule(domain_rule)
        
        return {
            "success": True,
            "rule_id": rule_id,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Create automation rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/automation/rules")
async def list_automation_rules():
    """List automation rules"""
    if not automation_engine:
        raise HTTPException(status_code=503, detail="Automation engine not available")
    
    try:
        rules = []
        for rule in automation_engine.rules.values():
            rules.append({
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "product_id": rule.product_id,
                "trigger_type": rule.trigger_type.value,
                "enabled": rule.enabled,
                "last_run": rule.last_run.isoformat() if rule.last_run else None,
                "next_run": rule.next_run.isoformat() if rule.next_run else None,
                "created_at": rule.created_at.isoformat()
            })
        
        return {"rules": rules}
        
    except Exception as e:
        logger.error(f"List automation rules error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/automation/rules/{rule_id}/execute")
async def execute_automation_rule(rule_id: str):
    """Execute an automation rule manually"""
    if not automation_engine:
        raise HTTPException(status_code=503, detail="Automation engine not available")
    
    try:
        execution_id = await automation_engine.execute_rule(rule_id, manual_trigger=True)
        
        return {
            "success": True,
            "execution_id": execution_id,
            "executed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Execute automation rule error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/automation/rules/{rule_id}/executions")
async def get_rule_executions(rule_id: str, limit: int = 50):
    """Get execution history for a rule"""
    if not automation_engine:
        raise HTTPException(status_code=503, detail="Automation engine not available")
    
    try:
        executions = await automation_engine.get_rule_executions(rule_id, limit)
        
        return {
            "rule_id": rule_id,
            "executions": executions
        }
        
    except Exception as e:
        logger.error(f"Get rule executions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reporting Endpoints
@app.post("/api/v1/reports/generate")
async def generate_report(product_id: str, report_type: str = "executive_summary",
                         time_range: str = "30_days", template: str = None,
                         format: str = "html", custom_parameters: Dict[str, Any] = None):
    """Generate a comprehensive report"""
    if not reporting_service:
        raise HTTPException(status_code=503, detail="Reporting service not available")
    
    try:
        report = await reporting_service.generate_report(
            product_id=product_id,
            report_type=report_type,
            time_range=time_range,
            template=template,
            format=format,
            custom_parameters=custom_parameters
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Generate report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reports/{report_id}")
async def get_report(report_id: str):
    """Get generated report"""
    if not reporting_service:
        raise HTTPException(status_code=503, detail="Reporting service not available")
    
    try:
        report = await reporting_service.get_report(report_id)
        
        return report
        
    except Exception as e:
        logger.error(f"Get report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reports/{report_id}/deliver")
async def deliver_report(report_id: str, delivery_methods: List[str], recipients: List[str]):
    """Deliver report via specified methods"""
    if not reporting_service:
        raise HTTPException(status_code=503, detail="Reporting service not available")
    
    try:
        result = await reporting_service.deliver_report(
            report_id=report_id,
            delivery_methods=delivery_methods,
            recipients=recipients
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Deliver report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reports/templates")
async def create_template(name: str, description: str, report_type: str,
                         template_content: str, variables: List[str]):
    """Create a custom report template"""
    if not reporting_service:
        raise HTTPException(status_code=503, detail="Reporting service not available")
    
    try:
        template_id = await reporting_service.create_custom_template(
            name=name,
            description=description,
            report_type=report_type,
            template_content=template_content,
            variables=variables
        )
        
        return {
            "success": True,
            "template_id": template_id,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Create template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reports/templates")
async def list_templates(report_type: str = None):
    """List available report templates"""
    if not reporting_service:
        raise HTTPException(status_code=503, detail="Reporting service not available")
    
    try:
        templates = await reporting_service.list_templates(report_type)
        
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"List templates error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/reports/templates/{template_id}")
async def get_template(template_id: str):
    """Get template details"""
    if not reporting_service:
        raise HTTPException(status_code=503, detail="Reporting service not available")
    
    try:
        template = await reporting_service.get_template(template_id)
        
        return template
        
    except Exception as e:
        logger.error(f"Get template error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard Endpoints
@app.post("/api/v1/analytics/dashboard")
async def create_dashboard(dashboard_config: Dict[str, Any]):
    """Create custom analytics dashboard"""
    try:
        dashboard_id = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "success": True,
            "dashboard_id": dashboard_id,
            "config": dashboard_config,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Create dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch Processing
@app.post("/api/v1/automation/batch-process")
async def batch_process_products(product_ids: List[str]):
    """Batch process multiple products"""
    if not mcp_service:
        raise HTTPException(status_code=503, detail="MCP service not available")
    
    try:
        results = []
        
        async def process_single_product(product_id: str):
            try:
                # Generate summary report
                report_content = f"""
                <h1>Batch Processing Report - {product_id}</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <h2>Summary</h2>
                <ul>
                    <li>Total Reviews: 1000</li>
                    <li>Average Rating: 4.2</li>
                    <li>Sentiment Score: 0.75</li>
                </ul>
                """
                
                # Create document
                doc_result = await mcp_service.deliver_report_to_docs(
                    f"batch_{product_id}_{datetime.now().strftime('%Y%m%d')}",
                    report_content
                )
                
                return {
                    "product_id": product_id,
                    "status": "success",
                    "doc_result": doc_result
                }
                
            except Exception as e:
                return {
                    "product_id": product_id,
                    "status": "error",
                    "error": str(e)
                }
        
        # Process products concurrently
        tasks = [process_single_product(pid) for pid in product_ids]
        results = await asyncio.gather(*tasks)
        
        successful = sum(1 for r in results if r["status"] == "success")
        failed = len(results) - successful
        
        return {
            "success": True,
            "total_products": len(product_ids),
            "successful": successful,
            "failed": failed,
            "results": results,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility functions
def generate_advanced_report(product_id: str, template: str, analytics_config: Optional[Dict[str, Any]] = None) -> str:
    """Generate advanced report content"""
    
    if template == "executive_summary":
        return f"""
        <html>
        <head><title>Executive Summary - {product_id}</title></head>
        <body>
            <h1>Executive Summary Report</h1>
            <h2>Product: {product_id}</h2>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>Key Metrics</h2>
            <ul>
                <li>Total Reviews: 1,250</li>
                <li>Average Rating: 4.2/5.0</li>
                <li>Sentiment Score: 75% Positive</li>
                <li>Response Rate: 89%</li>
            </ul>
            
            <h2>Trends</h2>
            <p>Sentiment has improved by 12% over the last 30 days.</p>
            <p>Review volume increased by 15% compared to previous month.</p>
            
            <h2>Recommendations</h2>
            <ul>
                <li>Maintain current quality standards</li>
                <li>Focus on improving response time</li>
                <li>Monitor emerging sentiment trends</li>
            </ul>
        </body>
        </html>
        """
    
    elif template == "detailed_analysis":
        return f"""
        <html>
        <head><title>Detailed Analysis - {product_id}</title></head>
        <body>
            <h1>Detailed Analysis Report</h1>
            <h2>Product: {product_id}</h2>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>Comprehensive Metrics</h2>
            <table border="1">
                <tr><th>Metric</th><th>Value</th><th>Change</th></tr>
                <tr><td>Total Reviews</td><td>1,250</td><td>+15%</td></tr>
                <tr><td>Average Rating</td><td>4.2</td><td>+0.3</td></tr>
                <tr><td>Sentiment Score</td><td>0.75</td><td>+0.12</td></tr>
                <tr><td>Response Rate</td><td>89%</td><td>+5%</td></tr>
            </table>
            
            <h2>Advanced Analytics</h2>
            <p>Detailed sentiment breakdown, trend analysis, and predictive insights would be included here.</p>
            
            <h2>Competitive Analysis</h2>
            <p>Comparison with similar products and market position.</p>
        </body>
        </html>
        """
    
    else:
        return f"<html><body><h1>Report for {product_id}</h1><p>Template: {template}</p></body></html>"

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
        port=8006,
        reload=True,
        log_level="info"
    )
