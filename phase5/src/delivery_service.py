"""
Report Delivery Service for Phase 5
Coordinates between MCP servers and stakeholder management
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from mcp_base import MCPError
from docs_mcp_server import DocsMCPServer, create_docs_mcp_server
from gmail_mcp_server import GmailMCPServer, create_gmail_mcp_server
from stakeholder_manager import StakeholderManager, DeliveryStatus, create_stakeholder_manager

logger = logging.getLogger(__name__)


@dataclass
class DeliveryRequest:
    """Request for report delivery"""
    product_id: str
    report_content: str
    report_format: str  # html, markdown, plain
    subject: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    custom_recipients: Optional[List[str]] = None


@dataclass
class DeliveryResult:
    """Result of delivery operation"""
    product_id: str
    total_recipients: int
    successful_deliveries: int
    failed_deliveries: int
    document_id: Optional[str] = None
    delivery_details: List[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.delivery_details is None:
            self.delivery_details = []
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DeliveryService:
    """Coordinates report delivery via MCP servers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.stakeholder_manager = create_stakeholder_manager(config)
        self.docs_server = create_docs_mcp_server(config)
        self.gmail_server = create_gmail_mcp_server(config)
        
        # Delivery tracking
        self.active_deliveries: Dict[str, DeliveryResult] = {}
        
        logger.info("Delivery service initialized")
    
    async def deliver_report(self, request: DeliveryRequest) -> DeliveryResult:
        """Deliver report to stakeholders"""
        try:
            logger.info(f"Starting delivery for product: {request.product_id}")
            
            # Get recipients
            if request.custom_recipients:
                # Custom recipients override stakeholder list
                recipients = request.custom_recipients
            else:
                # Get stakeholders from product
                stakeholders = self.stakeholder_manager.get_stakeholders_for_product(request.product_id)
                recipients = [s.email for s in stakeholders if s.active]
            
            if not recipients:
                raise MCPError("No recipients found for delivery", 400)
            
            # Create Google Doc with report content
            document_id = await self._create_document(request)
            
            # Share document with recipients
            await self._share_document(document_id, recipients)
            
            # Send email notifications
            delivery_details = await self._send_notifications(request, document_id, recipients)
            
            # Create delivery result
            result = DeliveryResult(
                product_id=request.product_id,
                total_recipients=len(recipients),
                successful_deliveries=len([d for d in delivery_details if d['status'] == 'sent']),
                failed_deliveries=len([d for d in delivery_details if d['status'] == 'failed']),
                document_id=document_id,
                delivery_details=delivery_details
            )
            
            # Track delivery
            self.active_deliveries[request.product_id] = result
            
            logger.info(f"Delivery completed for {request.product_id}: {result.successful_deliveries}/{result.total_recipients}")
            return result
            
        except Exception as e:
            logger.error(f"Delivery failed for {request.product_id}: {e}")
            raise MCPError(f"Delivery failed: {e}", 500)
    
    async def _create_document(self, request: DeliveryRequest) -> str:
        """Create Google Doc with report content"""
        try:
            # Generate document title
            title = self._generate_document_title(request.product_id)
            
            # Create document via MCP
            docs_params = {
                'title': title,
                'content': request.report_content,
                'format': request.report_format
            }
            
            docs_response = await self.docs_server._handle_mcp_method({
                'id': 'create_doc',
                'method': 'docs.create',
                'params': docs_params
            })
            
            document_id = docs_response['data']['document_id']
            logger.info(f"Created document: {document_id}")
            
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise MCPError(f"Document creation failed: {e}", 500)
    
    def _generate_document_title(self, product_id: str) -> str:
        """Generate document title"""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        
        # Determine week number
        week_number = now.isocalendar()[1]
        
        return f"Weekly Review Report - {product_id} - Week {week_number} ({date_str})"
    
    async def _share_document(self, document_id: str, recipients: List[str]):
        """Share document with recipients"""
        try:
            for recipient in recipients:
                share_params = {
                    'document_id': document_id,
                    'email': recipient,
                    'role': 'reader'  # Read-only access
                }
                
                await self.docs_server._handle_mcp_method({
                    'id': f'share_{recipient}',
                    'method': 'docs.share',
                    'params': share_params
                })
            
            logger.info(f"Shared document {document_id} with {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to share document: {e}")
            # Don't fail delivery if sharing fails, just log warning
            logger.warning("Document sharing failed, but email delivery will continue")
    
    async def _send_notifications(self, request: DeliveryRequest, document_id: str, 
                                 recipients: List[str]) -> List[Dict[str, Any]]:
        """Send email notifications to recipients"""
        delivery_details = []
        
        # Generate email content
        subject = request.subject or self._generate_email_subject(request.product_id)
        email_content = self._generate_email_content(request.product_id, document_id)
        
        for recipient in recipients:
            try:
                # Send email via MCP
                email_params = {
                    'to': [recipient],
                    'subject': subject,
                    'content': email_content,
                    'content_type': 'html',
                    'attachments': request.attachments or []
                }
                
                email_response = await self.gmail_server._handle_mcp_method({
                    'id': f'send_{recipient}',
                    'method': 'gmail.send',
                    'params': email_params
                })
                
                # Record successful delivery
                delivery_details.append({
                    'recipient': recipient,
                    'status': 'sent',
                    'message_id': email_response['data']['message_id'],
                    'thread_id': email_response['data']['thread_id'],
                    'sent_at': email_response['data']['sent_at']
                })
                
                # Record in stakeholder manager
                from stakeholder_manager import DeliveryRecord
                delivery_record = DeliveryRecord(
                    stakeholder_email=recipient,
                    product_id=request.product_id,
                    report_id=document_id,
                    message_id=email_response['data']['message_id'],
                    thread_id=email_response['data']['thread_id'],
                    sent_at=datetime.fromisoformat(email_response['data']['sent_at']),
                    status=DeliveryStatus.SENT
                )
                self.stakeholder_manager.record_delivery(delivery_record)
                
            except Exception as e:
                logger.error(f"Failed to send email to {recipient}: {e}")
                delivery_details.append({
                    'recipient': recipient,
                    'status': 'failed',
                    'error': str(e),
                    'sent_at': datetime.now().isoformat()
                })
        
        return delivery_details
    
    def _generate_email_subject(self, product_id: str) -> str:
        """Generate email subject"""
        now = datetime.now()
        date_str = now.strftime("%B %d, %Y")
        week_number = now.isocalendar()[1]
        
        return f"📊 Weekly Review Report - {product_id} - Week {week_number} ({date_str})"
    
    def _generate_email_content(self, product_id: str, document_id: str) -> str:
        """Generate email content"""
        document_url = f"https://docs.google.com/document/d/{document_id}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .button {{ display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Weekly Review Report</h1>
                <h2>{product_id}</h2>
            </div>
            
            <div class="content">
                <p>Hello,</p>
                <p>Your weekly product review report for <strong>{product_id}</strong> is now available.</p>
                
                <p>This report includes:</p>
                <ul>
                    <li>📈 Executive summary of key insights</li>
                    <li>🎯 Top themes and customer feedback</li>
                    <li>💬 Representative quotes from users</li>
                    <li>🔧 Actionable improvement ideas</li>
                    <li>📊 Impact analysis and trends</li>
                </ul>
                
                <p><a href="{document_url}" class="button">View Full Report</a></p>
                
                <p>The report is accessible via Google Docs, where you can:</p>
                <ul>
                    <li>View the complete analysis</li>
                    <li>Add comments and annotations</li>
                    <li>Share with team members</li>
                    <li>Export to PDF or other formats</li>
                </ul>
                
                <p>Best regards,<br>Review Pulse System</p>
            </div>
            
            <div class="footer">
                <p>This report was automatically generated by the Review Pulse system.</p>
                <p>If you have any questions or need to update your delivery preferences, please contact us.</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    async def get_delivery_status(self, product_id: str) -> Dict[str, Any]:
        """Get delivery status for a product"""
        if product_id not in self.active_deliveries:
            return {
                'product_id': product_id,
                'status': 'not_delivered',
                'message': 'No delivery record found'
            }
        
        result = self.active_deliveries[product_id]
        
        # Get detailed status from stakeholder manager
        stats = self.stakeholder_manager.get_delivery_statistics(product_id, days=7)
        
        return {
            'product_id': product_id,
            'delivery_result': {
                'total_recipients': result.total_recipients,
                'successful_deliveries': result.successful_deliveries,
                'failed_deliveries': result.failed_deliveries,
                'document_id': result.document_id,
                'timestamp': result.timestamp.isoformat()
            },
            'statistics': stats,
            'delivery_details': result.delivery_details
        }
    
    async def retry_failed_deliveries(self, product_id: str) -> DeliveryResult:
        """Retry failed deliveries for a product"""
        if product_id not in self.active_deliveries:
            raise MCPError("No previous delivery found to retry", 404)
        
        original_result = self.active_deliveries[product_id]
        failed_recipients = [
            d['recipient'] for d in original_result.delivery_details 
            if d['status'] == 'failed'
        ]
        
        if not failed_recipients:
            raise MCPError("No failed deliveries to retry", 400)
        
        logger.info(f"Retrying {len(failed_recipients)} failed deliveries for {product_id}")
        
        # Create new delivery request with failed recipients only
        # Note: In a real implementation, you'd need to reconstruct the original request
        # For now, we'll just mark them as retried
        
        for recipient in failed_recipients:
            # Update delivery status
            for detail in original_result.delivery_details:
                if detail['recipient'] == recipient:
                    detail['status'] = 'retrying'
                    break
        
        return original_result
    
    async def schedule_delivery(self, product_id: str, schedule_time: datetime):
        """Schedule delivery for future time"""
        # In a real implementation, this would integrate with a task queue
        # For now, we'll just log the scheduling request
        
        logger.info(f"Scheduled delivery for {product_id} at {schedule_time}")
        
        return {
            'product_id': product_id,
            'scheduled_time': schedule_time.isoformat(),
            'status': 'scheduled'
        }


# Factory function
def create_delivery_service(config: Dict[str, Any]) -> DeliveryService:
    """Create delivery service instance"""
    return DeliveryService(config)
