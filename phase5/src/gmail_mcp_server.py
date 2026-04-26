"""
Google Gmail MCP Server Implementation for Phase 5
Handles email composition, delivery, and tracking via MCP protocol
"""

import logging
import asyncio
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

from mcp_base import MCPServerBase, MCPError


@dataclass
class EmailRequest:
    """Request structure for email sending"""
    to: List[str]
    subject: str
    content: str
    content_type: str = 'html'  # html, plain
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    reply_to: Optional[str] = None


@dataclass
class EmailResponse:
    """Response structure for email operations"""
    message_id: str
    thread_id: str
    sent_at: datetime
    status: str
    recipients: List[str]


class GmailMCPServer(MCPServerBase):
    """Google Gmail MCP Server"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.config.update({
            'service_name': 'Gmail MCP',
            'scopes': [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.readonly'
            ]
        })
        
        # Initialize Gmail service
        self.gmail_service = None
    
    async def _handle_mcp_method(self, message):
        """Handle MCP methods for Gmail"""
        method = message.method
        
        if method == 'gmail.send':
            return await self._send_email(message.params)
        elif method == 'gmail.draft':
            return await self._create_draft(message.params)
        elif method == 'gmail.get':
            return await self._get_message(message.params)
        elif method == 'gmail.list':
            return await self._list_messages(message.params)
        elif method == 'gmail.thread':
            return await self._get_thread(message.params)
        elif method == 'gmail.search':
            return await self._search_messages(message.params)
        else:
            raise MCPError(f"Unknown method: {method}", 400)
    
    async def _ensure_services(self):
        """Ensure Gmail service is initialized"""
        if not await self._ensure_authenticated():
            raise MCPError("Not authenticated", 401)
        
        if not self.gmail_service:
            self.gmail_service = await self._get_google_service('gmail', 'v1')
    
    async def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Gmail"""
        try:
            await self._ensure_services()
            
            # Parse email request
            to = params.get('to', [])
            subject = params.get('subject', 'No Subject')
            content = params.get('content', '')
            content_type = params.get('content_type', 'html')
            cc = params.get('cc', [])
            bcc = params.get('bcc', [])
            attachments = params.get('attachments', [])
            reply_to = params.get('reply_to')
            
            if not to:
                raise MCPError("Recipients (to) are required", 400)
            
            if not content:
                raise MCPError("Email content is required", 400)
            
            # Create message
            message = self._create_email_message(
                to=to,
                subject=subject,
                content=content,
                content_type=content_type,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                reply_to=reply_to
            )
            
            # Send message
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            response = EmailResponse(
                message_id=sent_message.get('id'),
                thread_id=sent_message.get('threadId'),
                sent_at=datetime.now(),
                status='sent',
                recipients=to + (cc or []) + (bcc or [])
            )
            
            return self._format_mcp_response({
                'message_id': response.message_id,
                'thread_id': response.thread_id,
                'sent_at': response.sent_at.isoformat(),
                'status': response.status,
                'recipients': response.recipients
            })
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise MCPError(f"Failed to send email: {e}", 500)
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            raise MCPError(f"Internal error: {e}", 500)
    
    def _create_email_message(self, to: List[str], subject: str, content: str,
                            content_type: str, cc: Optional[List[str]] = None,
                            bcc: Optional[List[str]] = None,
                            attachments: Optional[List[Dict[str, Any]]] = None,
                            reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Create Gmail message from email components"""
        
        # Create message container
        if attachments:
            msg = MIMEMultipart()
        else:
            msg = MIMEText(content, content_type)
        
        # Set headers
        msg['To'] = ', '.join(to)
        msg['Subject'] = subject
        
        if cc:
            msg['Cc'] = ', '.join(cc)
        
        if reply_to:
            msg['Reply-To'] = reply_to
        
        # Add content for multipart messages
        if attachments:
            msg.attach(MIMEText(content, content_type))
            
            # Add attachments
            for attachment in attachments:
                self._add_attachment(msg, attachment)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return {'raw': raw_message}
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            filename = attachment.get('filename', 'attachment')
            content = attachment.get('content', '')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            # Create attachment part
            part = MIMEBase(*content_type.split('/', 1))
            part.set_payload(content)
            
            # Encode attachment
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Failed to add attachment: {e}")
            raise MCPError(f"Failed to process attachment: {e}", 400)
    
    async def _create_draft(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create email draft"""
        try:
            await self._ensure_services()
            
            # Parse email request (same as send_email)
            to = params.get('to', [])
            subject = params.get('subject', 'No Subject')
            content = params.get('content', '')
            content_type = params.get('content_type', 'html')
            cc = params.get('cc', [])
            bcc = params.get('bcc', [])
            attachments = params.get('attachments', [])
            reply_to = params.get('reply_to')
            
            if not to:
                raise MCPError("Recipients (to) are required", 400)
            
            # Create message
            message = self._create_email_message(
                to=to,
                subject=subject,
                content=content,
                content_type=content_type,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                reply_to=reply_to
            )
            
            # Create draft
            draft = self.gmail_service.users().drafts().create(
                userId='me',
                body={'message': message}
            ).execute()
            
            return self._format_mcp_response({
                'draft_id': draft.get('id'),
                'message_id': draft.get('message', {}).get('id'),
                'created_at': datetime.now().isoformat(),
                'status': 'draft'
            })
            
        except HttpError as e:
            logger.error(f"Create draft error: {e}")
            raise MCPError(f"Failed to create draft: {e}", 500)
    
    async def _get_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get email message details"""
        try:
            await self._ensure_services()
            
            message_id = params.get('message_id')
            if not message_id:
                raise MCPError("message_id is required", 400)
            
            # Get message
            message = self.gmail_service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._format_mcp_response({
                'message_id': message.get('id'),
                'thread_id': message.get('threadId'),
                'snippet': message.get('snippet'),
                'payload': message.get('payload'),
                'internal_date': message.get('internalDate'),
                'label_ids': message.get('labelIds', [])
            })
            
        except HttpError as e:
            logger.error(f"Get message error: {e}")
            raise MCPError(f"Failed to get message: {e}", 500)
    
    async def _list_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List email messages"""
        try:
            await self._ensure_services()
            
            query = params.get('query', '')
            page_size = params.get('page_size', 10)
            label_ids = params.get('label_ids', [])
            
            # Build query parameters
            list_params = {'userId': 'me', 'maxResults': page_size}
            if query:
                list_params['q'] = query
            if label_ids:
                list_params['labelIds'] = label_ids
            
            # List messages
            result = self.gmail_service.users().messages().list(**list_params).execute()
            messages = result.get('messages', [])
            
            # Get details for each message
            message_details = []
            for msg in messages:
                try:
                    detail = self.gmail_service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
                    ).execute()
                    
                    message_details.append({
                        'message_id': detail.get('id'),
                        'thread_id': detail.get('threadId'),
                        'snippet': detail.get('snippet'),
                        'headers': self._extract_headers(detail.get('payload', {})),
                        'date': detail.get('internalDate')
                    })
                except Exception as e:
                    logger.error(f"Failed to get message details: {e}")
                    continue
            
            return self._format_mcp_response({
                'messages': message_details,
                'total': len(message_details),
                'next_page_token': result.get('nextPageToken')
            })
            
        except HttpError as e:
            logger.error(f"List messages error: {e}")
            raise MCPError(f"Failed to list messages: {e}", 500)
    
    def _extract_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """Extract email headers from payload"""
        headers = {}
        for header in payload.get('headers', []):
            name = header.get('name', '').lower()
            value = header.get('value', '')
            if name and value:
                headers[name] = value
        return headers
    
    async def _get_thread(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get email thread"""
        try:
            await self._ensure_services()
            
            thread_id = params.get('thread_id')
            if not thread_id:
                raise MCPError("thread_id is required", 400)
            
            # Get thread
            thread = self.gmail_service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            return self._format_mcp_response({
                'thread_id': thread.get('id'),
                'messages': thread.get('messages', []),
                'snippet': thread.get('snippet'),
                'history_id': thread.get('historyId')
            })
            
        except HttpError as e:
            logger.error(f"Get thread error: {e}")
            raise MCPError(f"Failed to get thread: {e}", 500)
    
    async def _search_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search messages with query"""
        try:
            await self._ensure_services()
            
            query = params.get('query', '')
            if not query:
                raise MCPError("Search query is required", 400)
            
            # Search messages
            result = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=params.get('max_results', 10)
            ).execute()
            
            messages = result.get('messages', [])
            
            # Get message details
            message_details = []
            for msg in messages:
                try:
                    detail = self.gmail_service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'To', 'Subject', 'Date']
                    ).execute()
                    
                    message_details.append({
                        'message_id': detail.get('id'),
                        'thread_id': detail.get('threadId'),
                        'snippet': detail.get('snippet'),
                        'headers': self._extract_headers(detail.get('payload', {}))
                    })
                except Exception as e:
                    logger.error(f"Failed to get search result details: {e}")
                    continue
            
            return self._format_mcp_response({
                'query': query,
                'messages': message_details,
                'total': len(message_details)
            })
            
        except HttpError as e:
            logger.error(f"Search messages error: {e}")
            raise MCPError(f"Failed to search messages: {e}", 500)


# Server factory function
def create_gmail_mcp_server(config: Dict[str, Any]) -> GmailMCPServer:
    """Create Gmail MCP server instance"""
    return GmailMCPServer(config)
