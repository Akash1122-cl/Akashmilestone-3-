"""
External Delivery Service for Phase 5
Uses Saksham's MCP Server for Google Docs and Gmail integration
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from external_mcp_client import ExternalMCPDeliveryService, create_external_mcp_service
from stakeholder_manager import StakeholderManager, DeliveryStatus, create_stakeholder_manager

logger = logging.getLogger(__name__)

@dataclass
class DeliveryRequest:
    """Request for report delivery using external MCP"""
    product_id: str
    report_content: str
    report_format: str  # html, markdown, plain
    subject: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    custom_recipients: Optional[List[str]] = None
    doc_id: Optional[str] = None  # Google Doc ID for updating existing doc

@dataclass
class DeliveryResult:
    """Result of delivery operation"""
    product_id: str
    total_recipients: int
    successful_deliveries: int
    failed_deliveries: int
    document_id: Optional[str]
    email_drafts: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    timestamp: datetime

class ExternalDeliveryService:
    """Delivery service using external MCP server"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mcp_url = config.get('mcp_url', 'https://saksham-mcp-server.onrender.com')
        self.stakeholder_manager = create_stakeholder_manager(config)
        self.mcp_service = create_external_mcp_service(self.mcp_url)
        
        logger.info("External delivery service initialized")
    
    async def deliver_report(self, request: DeliveryRequest) -> DeliveryResult:
        """Deliver report to stakeholders using external MCP server"""
        try:
            logger.info(f"Starting delivery for product: {request.product_id}")
            
            # Get stakeholders for this product
            if request.custom_recipients:
                stakeholders = request.custom_recipients
            else:
                stakeholders = self.stakeholder_manager.get_stakeholders_for_product(request.product_id)
                stakeholders = [s.email for s in stakeholders if s.active]
            
            if not stakeholders:
                raise ValueError("No recipients found for delivery")
            
            logger.info(f"Found {len(stakeholders)} recipients")
            
            # Initialize results
            successful_deliveries = 0
            failed_deliveries = 0
            errors = []
            email_drafts = []
            document_id = None
            
            # Step 1: Deliver to Google Docs
            if request.doc_id:
                # Update existing document
                try:
                    docs_result = await self.mcp_service.deliver_report_to_docs(
                        request.doc_id, 
                        request.report_content
                    )
                    
                    if docs_result['status'] == 'success':
                        document_id = request.doc_id
                        logger.info(f"Successfully updated Google Doc: {document_id}")
                    else:
                        errors.append({
                            "type": "docs_update",
                            "error": docs_result.get('error', 'Unknown error')
                        })
                        failed_deliveries += 1
                        
                except Exception as e:
                    errors.append({
                        "type": "docs_update",
                        "error": str(e)
                    })
                    failed_deliveries += 1
                    logger.error(f"Failed to update Google Doc: {e}")
            else:
                # Create new document (would need doc_id from user)
                logger.warning("No doc_id provided - skipping Google Docs delivery")
            
            # Step 2: Send email notifications
            doc_link = f"https://docs.google.com/document/d/{document_id}" if document_id else None
            
            for recipient in stakeholders:
                try:
                    # Generate email content
                    subject = request.subject or f"Weekly Review Report - {request.product_id}"
                    body = self._generate_email_body(request.product_id, request.report_content, doc_link)
                    
                    # Create email draft via MCP
                    email_result = await self.mcp_service.send_email_notification(
                        recipient, subject, body, doc_link
                    )
                    
                    if email_result['status'] == 'success':
                        successful_deliveries += 1
                        email_drafts.append({
                            "recipient": recipient,
                            "draft_id": email_result.get('draft_id'),
                            "status": "success"
                        })
                        logger.info(f"Created email draft for {recipient}")
                    else:
                        failed_deliveries += 1
                        errors.append({
                            "type": "email",
                            "recipient": recipient,
                            "error": email_result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    failed_deliveries += 1
                    errors.append({
                        "type": "email",
                        "recipient": recipient,
                        "error": str(e)
                    })
                    logger.error(f"Failed to create email draft for {recipient}: {e}")
            
            # Record delivery in stakeholder manager
            total_recipients = len(stakeholders)
            self.stakeholder_manager.record_delivery(
                request.product_id,
                successful_deliveries,
                failed_deliveries
            )
            
            # Create result
            result = DeliveryResult(
                product_id=request.product_id,
                total_recipients=total_recipients,
                successful_deliveries=successful_deliveries,
                failed_deliveries=failed_deliveries,
                document_id=document_id,
                email_drafts=email_drafts,
                errors=errors,
                timestamp=datetime.now()
            )
            
            logger.info(f"Delivery completed: {successful_deliveries}/{total_recipients} successful")
            return result
            
        except Exception as e:
            logger.error(f"Delivery failed for product {request.product_id}: {e}")
            raise
    
    def _generate_email_body(self, product_id: str, report_content: str, doc_link: str = None) -> str:
        """Generate email body content"""
        body = f"""
Hello,

Please find the weekly review report for {product_id}.

"""
        
        if doc_link:
            body += f"You can view the full report here: {doc_link}\n\n"
        
        body += f"""
Report Summary:
- Product: {product_id}
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Format: HTML Report

This report was generated using the Review Pulse system and delivered via our MCP integration.

Best regards,
Review Pulse Team
"""
        
        return body
    
    async def get_delivery_status(self, product_id: str) -> Dict[str, Any]:
        """Get delivery status for a product"""
        try:
            # Get statistics from stakeholder manager
            stats = self.stakeholder_manager.get_delivery_statistics(product_id)
            
            # Get MCP server status
            mcp_status = await self.mcp_service.get_mcp_status()
            
            return {
                "product_id": product_id,
                "statistics": stats,
                "mcp_server_status": mcp_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get delivery status for {product_id}: {e}")
            raise
    
    async def retry_failed_deliveries(self, product_id: str) -> DeliveryResult:
        """Retry failed deliveries for a product"""
        try:
            # Get failed delivery records
            failed_records = self.stakeholder_manager.get_failed_deliveries(product_id)
            
            if not failed_records:
                raise ValueError("No failed deliveries found for retry")
            
            logger.info(f"Retrying {len(failed_records)} failed deliveries for {product_id}")
            
            # For simplicity, we'll create a new delivery request
            # In a real implementation, you might retry specific failed deliveries
            # This is a simplified retry mechanism
            
            # Get the latest report content (placeholder)
            report_content = f"<h1>Retry Report for {product_id}</h1><p>This is a retry of failed deliveries.</p>"
            
            retry_request = DeliveryRequest(
                product_id=product_id,
                report_content=report_content,
                report_format="html",
                subject=f"RETRY: Weekly Review Report - {product_id}"
            )
            
            return await self.deliver_report(retry_request)
            
        except Exception as e:
            logger.error(f"Failed to retry deliveries for {product_id}: {e}")
            raise

# Factory function
def create_external_delivery_service(config: Dict[str, Any]) -> ExternalDeliveryService:
    """Create external delivery service"""
    return ExternalDeliveryService(config)
