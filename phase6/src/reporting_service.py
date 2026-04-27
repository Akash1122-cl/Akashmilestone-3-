"""
Phase 6 Reporting Service
Handles report generation, templates, and delivery automation
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import uuid
from jinja2 import Template

logger = logging.getLogger(__name__)

class ReportType(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    TREND_REPORT = "trend_report"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    CUSTOM = "custom"

class ReportFormat(Enum):
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"
    MARKDOWN = "markdown"

@dataclass
class ReportTemplate:
    """Report template definition"""
    id: str
    name: str
    description: str
    report_type: ReportType
    template_content: str
    variables: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class ReportRequest:
    """Report generation request"""
    product_id: str
    report_type: ReportType
    time_range: str
    format: ReportFormat
    template_id: Optional[str] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    recipients: Optional[List[str]] = None

@dataclass
class Report:
    """Generated report"""
    id: str
    request: ReportRequest
    title: str
    content: str
    metadata: Dict[str, Any]
    generated_at: datetime
    file_path: Optional[str] = None
    size_bytes: Optional[int] = None

class ReportingService:
    """Advanced reporting service for Phase 6"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.templates: Dict[str, ReportTemplate] = {}
        self.reports: Dict[str, Report] = {}
        
        # Service dependencies
        self.analytics_service = None
        self.mcp_service = None
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def register_services(self, analytics_service, mcp_service):
        """Register service dependencies"""
        self.analytics_service = analytics_service
        self.mcp_service = mcp_service
    
    async def generate_report(self, product_id: str, report_type: str = "executive_summary",
                            time_range: str = "30_days", template: str = None,
                            format: str = "html", custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a comprehensive report"""
        try:
            logger.info(f"Generating {report_type} report for {product_id}")
            
            # Create report request
            request = ReportRequest(
                product_id=product_id,
                report_type=ReportType(report_type),
                time_range=time_range,
                format=ReportFormat(format),
                custom_parameters=custom_parameters or {}
            )
            
            # Gather analytics data
            analytics_data = await self._gather_analytics_data(request)
            
            # Generate content
            content = await self._generate_report_content(request, analytics_data)
            
            # Create report object
            report = Report(
                id=str(uuid.uuid4()),
                request=request,
                title=self._generate_report_title(request),
                content=content,
                metadata={
                    "analytics_data": analytics_data,
                    "generation_time": datetime.now().isoformat(),
                    "template_used": template
                },
                generated_at=datetime.now()
            )
            
            # Store report
            self.reports[report.id] = report
            
            logger.info(f"Report generated: {report.id}")
            
            return {
                "report_id": report.id,
                "title": report.title,
                "content": report.content,
                "metadata": report.metadata,
                "generated_at": report.generated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    async def create_custom_template(self, name: str, description: str, 
                                    report_type: str, template_content: str,
                                    variables: List[str]) -> str:
        """Create a custom report template"""
        try:
            template = ReportTemplate(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                report_type=ReportType(report_type),
                template_content=template_content,
                variables=variables,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.templates[template.id] = template
            
            logger.info(f"Created template: {name} ({template.id})")
            return template.id
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get template details"""
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "report_type": template.report_type.value,
            "template_content": template.template_content,
            "variables": template.variables,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
    
    async def list_templates(self, report_type: str = None) -> List[Dict[str, Any]]:
        """List available templates"""
        templates = []
        
        for template in self.templates.values():
            if report_type is None or template.report_type.value == report_type:
                templates.append({
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "report_type": template.report_type.value,
                    "variables": template.variables,
                    "created_at": template.created_at.isoformat()
                })
        
        return templates
    
    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get generated report"""
        if report_id not in self.reports:
            raise ValueError(f"Report {report_id} not found")
        
        report = self.reports[report_id]
        
        return {
            "id": report.id,
            "title": report.title,
            "content": report.content,
            "metadata": report.metadata,
            "generated_at": report.generated_at.isoformat(),
            "file_path": report.file_path,
            "size_bytes": report.size_bytes
        }
    
    async def deliver_report(self, report_id: str, delivery_methods: List[str],
                           recipients: List[str]) -> Dict[str, Any]:
        """Deliver report via specified methods"""
        try:
            if report_id not in self.reports:
                raise ValueError(f"Report {report_id} not found")
            
            report = self.reports[report_id]
            results = []
            
            for method in delivery_methods:
                if method == "email":
                    result = await self._deliver_via_email(report, recipients)
                    results.append(result)
                
                elif method == "google_docs":
                    result = await self._deliver_via_google_docs(report, recipients)
                    results.append(result)
                
                elif method == "google_drive":
                    result = await self._deliver_via_google_drive(report, recipients)
                    results.append(result)
                
                else:
                    results.append({
                        "method": method,
                        "status": "error",
                        "error": f"Unknown delivery method: {method}"
                    })
            
            return {
                "report_id": report_id,
                "delivery_results": results,
                "delivered_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error delivering report: {e}")
            raise
    
    async def _gather_analytics_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Gather analytics data for report generation"""
        if not self.analytics_service:
            return self._generate_mock_data(request)
        
        try:
            # Get trend analysis
            trend_analysis = await self.analytics_service.generate_trend_analysis(
                product_id=request.product_id,
                time_range=request.time_range
            )
            
            # Get predictions if requested
            predictions = None
            if request.custom_parameters and request.custom_parameters.get("include_predictions"):
                predictions = await self.analytics_service.generate_predictions(
                    product_id=request.product_id
                )
            
            # Get competitive analysis if requested
            competitive = None
            if request.custom_parameters and request.custom_parameters.get("include_competitive"):
                compare_products = request.custom_parameters.get("compare_products", [])
                if compare_products:
                    competitive = await self.analytics_service.compare_products(
                        product_ids=[request.product_id] + compare_products,
                        time_range=request.time_range
                    )
            
            return {
                "trend_analysis": trend_analysis,
                "predictions": predictions,
                "competitive_analysis": competitive,
                "product_id": request.product_id,
                "time_range": request.time_range,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error gathering analytics data: {e}")
            return self._generate_mock_data(request)
    
    async def _generate_report_content(self, request: ReportRequest, 
                                     analytics_data: Dict[str, Any]) -> str:
        """Generate report content using template"""
        try:
            # Get template
            template = self._get_template_for_report_type(request.report_type)
            
            # Prepare template variables
            variables = self._prepare_template_variables(request, analytics_data)
            
            # Render template
            jinja_template = Template(template.template_content)
            content = jinja_template.render(**variables)
            
            return content
            
        except Exception as e:
            logger.error(f"Error generating report content: {e}")
            return self._generate_fallback_content(request, analytics_data)
    
    def _get_template_for_report_type(self, report_type: ReportType) -> ReportTemplate:
        """Get template for report type"""
        for template in self.templates.values():
            if template.report_type == report_type:
                return template
        
        # Create default template if not found
        return self._create_default_template(report_type)
    
    def _prepare_template_variables(self, request: ReportRequest, 
                                  analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare variables for template rendering"""
        variables = {
            "product_id": request.product_id,
            "report_type": request.report_type.value,
            "time_range": request.time_range,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analytics": analytics_data
        }
        
        # Add custom parameters
        if request.custom_parameters:
            variables.update(request.custom_parameters)
        
        # Extract key metrics
        if "trend_analysis" in analytics_data:
            trend = analytics_data["trend_analysis"]
            variables["current_sentiment"] = trend.get("analyses", {}).get("sentiment", {}).get("current_value", 0)
            variables["current_volume"] = trend.get("analyses", {}).get("volume", {}).get("current_value", 0)
            variables["current_rating"] = trend.get("analyses", {}).get("rating", {}).get("current_value", 0)
            variables["insights"] = trend.get("insights", [])
        
        return variables
    
    def _generate_report_title(self, request: ReportRequest) -> str:
        """Generate report title"""
        type_names = {
            ReportType.EXECUTIVE_SUMMARY: "Executive Summary",
            ReportType.DETAILED_ANALYSIS: "Detailed Analysis",
            ReportType.TREND_REPORT: "Trend Report",
            ReportType.COMPETITIVE_ANALYSIS: "Competitive Analysis"
        }
        
        type_name = type_names.get(request.report_type, "Report")
        return f"{type_name} - {request.product_id} ({request.time_range})"
    
    async def _deliver_via_email(self, report: Report, recipients: List[str]) -> Dict[str, Any]:
        """Deliver report via email"""
        if not self.mcp_service:
            return {
                "method": "email",
                "status": "error",
                "error": "MCP service not available"
            }
        
        results = []
        
        for recipient in recipients:
            try:
                result = await self.mcp_service.send_email_notification(
                    to=recipient,
                    subject=report.title,
                    body=report.content
                )
                
                results.append({
                    "recipient": recipient,
                    "status": "success",
                    "draft_id": result.get("draft_id")
                })
                
            except Exception as e:
                results.append({
                    "recipient": recipient,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "method": "email",
            "status": "completed",
            "results": results
        }
    
    async def _deliver_via_google_docs(self, report: Report, recipients: List[str]) -> Dict[str, Any]:
        """Deliver report via Google Docs"""
        if not self.mcp_service:
            return {
                "method": "google_docs",
                "status": "error",
                "error": "MCP service not available"
            }
        
        try:
            # Create Google Doc
            doc_name = f"{report.title}.doc"
            result = await self.mcp_service.deliver_report_to_docs(
                doc_id=doc_name,
                report_content=report.content
            )
            
            return {
                "method": "google_docs",
                "status": "success",
                "doc_id": result.get("doc_id"),
                "doc_name": doc_name
            }
            
        except Exception as e:
            return {
                "method": "google_docs",
                "status": "error",
                "error": str(e)
            }
    
    async def _deliver_via_google_drive(self, report: Report, recipients: List[str]) -> Dict[str, Any]:
        """Deliver report via Google Drive"""
        if not self.mcp_service:
            return {
                "method": "google_drive",
                "status": "error",
                "error": "MCP service not available"
            }
        
        try:
            # Create file in Drive
            file_name = f"{report.title}.txt"
            result = await self.mcp_service.deliver_report_to_docs(
                doc_id=file_name,
                report_content=report.content
            )
            
            return {
                "method": "google_drive",
                "status": "success",
                "file_id": result.get("doc_id"),
                "file_name": file_name
            }
            
        except Exception as e:
            return {
                "method": "google_drive",
                "status": "error",
                "error": str(e)
            }
    
    def _generate_mock_data(self, request: ReportRequest) -> Dict[str, Any]:
        """Generate mock analytics data for testing"""
        return {
            "trend_analysis": {
                "product_id": request.product_id,
                "time_range": request.time_range,
                "analyses": {
                    "sentiment": {
                        "current_value": 0.75,
                        "change_percent": 5.2,
                        "trend_direction": "increasing"
                    },
                    "volume": {
                        "current_value": 1250,
                        "change_percent": 12.1,
                        "trend_direction": "increasing"
                    },
                    "rating": {
                        "current_value": 4.2,
                        "change_percent": 3.8,
                        "trend_direction": "increasing"
                    }
                },
                "insights": [
                    "Customer sentiment is improving by 5.2%",
                    "Review volume is growing by 12.1%",
                    "Product rating is improving by 3.8%"
                ]
            },
            "predictions": {
                "predictions": {
                    "sentiment": {
                        "predicted_value": 0.78,
                        "confidence_score": 0.85
                    },
                    "volume": {
                        "predicted_value": 1350,
                        "confidence_score": 0.82
                    }
                }
            },
            "product_id": request.product_id,
            "time_range": request.time_range
        }
    
    def _generate_fallback_content(self, request: ReportRequest, analytics_data: Dict[str, Any]) -> str:
        """Generate fallback content if template fails"""
        return f"""
        <html>
        <head><title>{request.product_id} Report</title></head>
        <body>
            <h1>{request.report_type.value.title()} - {request.product_id}</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Time Range: {request.time_range}</p>
            
            <h2>Analytics Data</h2>
            <pre>{json.dumps(analytics_data, indent=2)}</pre>
        </body>
        </html>
        """
    
    def _initialize_default_templates(self):
        """Initialize default report templates"""
        # Executive Summary Template
        self.templates["executive_summary"] = ReportTemplate(
            id="executive_summary",
            name="Executive Summary",
            description="High-level overview for executives",
            report_type=ReportType.EXECUTIVE_SUMMARY,
            template_content="""
            <html>
            <head>
                <title>{{ product_id }} - Executive Summary</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { background: #f8f9fa; padding: 20px; border-radius: 5px; }
                    .metrics { display: flex; justify-content: space-between; margin: 20px 0; }
                    .metric { text-align: center; padding: 20px; background: #e9ecef; border-radius: 5px; }
                    .insights { margin: 30px 0; }
                    .insight { background: #d4edda; padding: 15px; margin: 10px 0; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Executive Summary - {{ product_id }}</h1>
                    <p>Generated: {{ generated_at }}</p>
                    <p>Time Range: {{ time_range }}</p>
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <h3>Sentiment</h3>
                        <h2>{{ "%.2f"|format(current_sentiment * 100) }}%</h2>
                        <p>Customer Satisfaction</p>
                    </div>
                    <div class="metric">
                        <h3>Volume</h3>
                        <h2>{{ current_volume|int }}</h2>
                        <p>Total Reviews</p>
                    </div>
                    <div class="metric">
                        <h3>Rating</h3>
                        <h2>{{ "%.1f"|format(current_rating) }}/5.0</h2>
                        <p>Average Rating</p>
                    </div>
                </div>
                
                <div class="insights">
                    <h2>Key Insights</h2>
                    {% for insight in insights %}
                    <div class="insight">{{ insight }}</div>
                    {% endfor %}
                </div>
                
                <h2>Recommendations</h2>
                <ul>
                    <li>Maintain current quality standards</li>
                    <li>Focus on improving customer engagement</li>
                    <li>Monitor emerging trends closely</li>
                </ul>
            </body>
            </html>
            """,
            variables=["product_id", "generated_at", "time_range", "current_sentiment", "current_volume", "current_rating", "insights"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def _create_default_template(self, report_type: ReportType) -> ReportTemplate:
        """Create default template for report type"""
        return ReportTemplate(
            id=f"default_{report_type.value}",
            name=f"Default {report_type.value.title()}",
            description=f"Default template for {report_type.value}",
            report_type=report_type,
            template_content = """
            <html>
            <head><title>{{ product_id }} - {{ report_type }}</title></head>
            <body>
                <h1>{{ report_type }} - {{ product_id }}</h1>
                <p>Generated: {{ generated_at }}</p>
                <p>Time Range: {{ time_range }}</p>
            </div>
            
            <div class="metrics">
                <div class="metric">
                    <h3>Sentiment</h3>
                    <h2>{{ "%.2f"|format(current_sentiment * 100) }}%</h2>
                    <p>Customer Satisfaction</p>
                </div>
                <div class="metric">
                    <h3>Volume</h3>
                    <h2>{{ current_volume|int }}</h2>
                    <p>Total Reviews</p>
                </div>
                <div class="metric">
                    <h3>Rating</h3>
                    <h2>{{ "%.1f"|format(current_rating) }}/5.0</h2>
                    <p>Average Rating</p>
                </div>
            </div>
            
            <div class="insights">
                <h2>Key Insights</h2>
                {% for insight in insights %}
                <div class="insight">{{ insight }}</div>
                {% endfor %}
            </div>
            
            <h2>Recommendations</h2>
            <ul>
                <li>Maintain current quality standards</li>
                <li>Focus on improving customer engagement</li>
                <li>Monitor emerging trends closely</li>
            </ul>
        </body>
        </html>
        """,
        variables=["product_id", "generated_at", "time_range", "current_sentiment", "current_volume", "current_rating", "insights"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

def _create_default_template(self, report_type: ReportType) -> ReportTemplate:
    """Create default template for report type"""
    template_html = """
        <html>
        <head><title>{{ product_id }} - {{ report_type }}</title></head>
        <body>
            <h1>{{ report_type }} - {{ product_id }}</h1>
            <p>Generated: {{ generated_at }}</p>
            <p>Time Range: {{ time_range }}</p>
            
            <h2>Analytics Data</h2>
            <pre>{{ analytics | tojson(indent=2) }}</pre>
        </body>
        </html>
        """
    
    return ReportTemplate(
        id=f"default_{report_type.value}",
        name=f"Default {report_type.value.title()}",
        description=f"Default template for {report_type.value}",
        report_type=report_type,
        template_content=template_html,
        variables=["product_id", "report_type", "generated_at", "time_range", "analytics"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

# Factory function
def create_reporting_service(config: Dict[str, Any]) -> ReportingService:
    """Create reporting service instance"""
    return ReportingService(config)
