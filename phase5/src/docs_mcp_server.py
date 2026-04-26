"""
Google Docs MCP Server Implementation for Phase 5
Handles document creation, formatting, and management via MCP protocol
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build

from mcp_base import MCPServerBase, MCPError


@dataclass
class DocumentRequest:
    """Request structure for document creation"""
    title: str
    content: str
    format: str = 'html'  # html, markdown, plain
    folder_id: Optional[str] = None


@dataclass
class DocumentResponse:
    """Response structure for document operations"""
    document_id: str
    title: str
    url: str
    created_at: datetime
    status: str


class DocsMCPServer(MCPServerBase):
    """Google Docs MCP Server"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.config.update({
            'service_name': 'Google Docs MCP',
            'scopes': [
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/drive'
            ]
        })
        
        # Initialize Google Docs service
        self.docs_service = None
        self.drive_service = None
    
    async def _handle_mcp_method(self, message):
        """Handle MCP methods for Google Docs"""
        method = message.method
        
        if method == 'docs.create':
            return await self._create_document(message.params)
        elif method == 'docs.get':
            return await self._get_document(message.params)
        elif method == 'docs.update':
            return await self._update_document(message.params)
        elif method == 'docs.list':
            return await self._list_documents(message.params)
        elif method == 'docs.delete':
            return await self._delete_document(message.params)
        elif method == 'docs.share':
            return await self._share_document(message.params)
        else:
            raise MCPError(f"Unknown method: {method}", 400)
    
    async def _ensure_services(self):
        """Ensure Google services are initialized"""
        if not await self._ensure_authenticated():
            raise MCPError("Not authenticated", 401)
        
        if not self.docs_service:
            self.docs_service = await self._get_google_service('docs', 'v1')
        
        if not self.drive_service:
            self.drive_service = await self._get_google_service('drive', 'v3')
    
    async def _create_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Google Doc"""
        try:
            await self._ensure_services()
            
            # Parse request
            title = params.get('title', 'Untitled Document')
            content = params.get('content', '')
            format_type = params.get('format', 'html')
            folder_id = params.get('folder_id')
            
            # Create document in Drive first
            doc_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            if folder_id:
                doc_metadata['parents'] = [folder_id]
            
            drive_response = self.drive_service.files().create(
                body=doc_metadata,
                fields='id,name'
            ).execute()
            
            document_id = drive_response.get('id')
            
            # Add content to document
            if content:
                await self._add_content_to_document(document_id, content, format_type)
            
            # Get document URL
            document_url = f"https://docs.google.com/document/d/{document_id}"
            
            response = DocumentResponse(
                document_id=document_id,
                title=title,
                url=document_url,
                created_at=datetime.now(),
                status='created'
            )
            
            return self._format_mcp_response({
                'document_id': response.document_id,
                'title': response.title,
                'url': response.url,
                'created_at': response.created_at.isoformat(),
                'status': response.status
            })
            
        except HttpError as e:
            logger.error(f"Google Docs API error: {e}")
            raise MCPError(f"Failed to create document: {e}", 500)
        except Exception as e:
            logger.error(f"Document creation error: {e}")
            raise MCPError(f"Internal error: {e}", 500)
    
    async def _add_content_to_document(self, document_id: str, content: str, format_type: str):
        """Add content to Google Doc"""
        try:
            if format_type == 'html':
                # Convert HTML to Google Docs structure
                requests = self._html_to_docs_requests(content)
            elif format_type == 'markdown':
                # Convert Markdown to Google Docs structure
                requests = self._markdown_to_docs_requests(content)
            else:
                # Plain text
                requests = [
                    {
                        'insertText': {
                            'location': {'index': 1},
                            'text': content
                        }
                    }
                ]
            
            if requests:
                self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
                
        except Exception as e:
            logger.error(f"Failed to add content: {e}")
            raise
    
    def _html_to_docs_requests(self, html_content: str) -> List[Dict[str, Any]]:
        """Convert HTML to Google Docs batch update requests"""
        # Simplified HTML parsing - in production, use proper HTML parser
        requests = []
        
        # Basic HTML to Google Docs conversion
        if '<h1>' in html_content:
            # Extract h1 content
            import re
            h1_match = re.search(r'<h1>(.*?)</h1>', html_content, re.DOTALL)
            if h1_match:
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': h1_match.group(1) + '\n'
                    }
                })
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': 1, 'endIndex': len(h1_match.group(1)) + 1},
                        'textStyle': {
                            'bold': True,
                            'fontSize': {'magnitude': 24, 'unit': 'PT'}
                        }
                    }
                })
        
        # Add paragraph content
        import re
        paragraphs = re.findall(r'<p>(.*?)</p>', html_content, re.DOTALL)
        for i, paragraph in enumerate(paragraphs):
            start_index = len(requests) * 100 + 1  # Simplified index calculation
            requests.append({
                'insertText': {
                    'location': {'index': start_index},
                    'text': paragraph + '\n'
                }
            })
        
        return requests
    
    def _markdown_to_docs_requests(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Convert Markdown to Google Docs batch update requests"""
        requests = []
        lines = markdown_content.split('\n')
        
        current_index = 1
        for line in lines:
            if line.startswith('# '):
                # H1
                text = line[2:] + '\n'
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text
                    }
                })
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': current_index, 'endIndex': current_index + len(text)},
                        'textStyle': {
                            'bold': True,
                            'fontSize': {'magnitude': 24, 'unit': 'PT'}
                        }
                    }
                })
                current_index += len(text)
            elif line.startswith('## '):
                # H2
                text = line[3:] + '\n'
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text
                    }
                })
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': current_index, 'endIndex': current_index + len(text)},
                        'textStyle': {
                            'bold': True,
                            'fontSize': {'magnitude': 18, 'unit': 'PT'}
                        }
                    }
                })
                current_index += len(text)
            elif line.strip():
                # Regular paragraph
                text = line + '\n'
                requests.append({
                    'insertText': {
                        'location': {'index': current_index},
                        'text': text
                    }
                })
                current_index += len(text)
        
        return requests
    
    async def _get_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get document content"""
        try:
            await self._ensure_services()
            
            document_id = params.get('document_id')
            if not document_id:
                raise MCPError("document_id is required", 400)
            
            # Get document content
            doc = self.docs_service.documents().get(
                documentId=document_id
            ).execute()
            
            # Get file metadata
            file = self.drive_service.files().get(
                fileId=document_id,
                fields='name,webViewLink'
            ).execute()
            
            return self._format_mcp_response({
                'document_id': document_id,
                'title': file.get('name'),
                'url': file.get('webViewLink'),
                'content': doc.get('body', {}).get('content', []),
                'document': doc
            })
            
        except HttpError as e:
            logger.error(f"Get document error: {e}")
            raise MCPError(f"Failed to get document: {e}", 500)
    
    async def _list_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List user's documents"""
        try:
            await self._ensure_services()
            
            query = "mimeType='application/vnd.google-apps.document'"
            page_size = params.get('page_size', 10)
            
            results = self.drive_service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, webViewLink, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            
            documents = []
            for file in files:
                documents.append({
                    'document_id': file.get('id'),
                    'title': file.get('name'),
                    'url': file.get('webViewLink'),
                    'created_at': file.get('createdTime')
                })
            
            return self._format_mcp_response({
                'documents': documents,
                'total': len(documents)
            })
            
        except HttpError as e:
            logger.error(f"List documents error: {e}")
            raise MCPError(f"Failed to list documents: {e}", 500)
    
    async def _update_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update document content"""
        try:
            await self._ensure_services()
            
            document_id = params.get('document_id')
            content = params.get('content', '')
            format_type = params.get('format', 'html')
            
            if not document_id:
                raise MCPError("document_id is required", 400)
            
            # Clear existing content and add new content
            requests = [{'deleteContent': {'range': {'startIndex': 1, 'endIndex': -1}}}]
            requests.extend(self._html_to_docs_requests(content) if format_type == 'html' 
                           else self._markdown_to_docs_requests(content))
            
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return self._format_mcp_response({
                'document_id': document_id,
                'status': 'updated',
                'updated_at': datetime.now().isoformat()
            })
            
        except HttpError as e:
            logger.error(f"Update document error: {e}")
            raise MCPError(f"Failed to update document: {e}", 500)
    
    async def _delete_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete document"""
        try:
            await self._ensure_services()
            
            document_id = params.get('document_id')
            if not document_id:
                raise MCPError("document_id is required", 400)
            
            self.drive_service.files().delete(fileId=document_id).execute()
            
            return self._format_mcp_response({
                'document_id': document_id,
                'status': 'deleted',
                'deleted_at': datetime.now().isoformat()
            })
            
        except HttpError as e:
            logger.error(f"Delete document error: {e}")
            raise MCPError(f"Failed to delete document: {e}", 500)
    
    async def _share_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Share document with stakeholders"""
        try:
            await self._ensure_services()
            
            document_id = params.get('document_id')
            email = params.get('email')
            role = params.get('role', 'reader')  # reader, writer, commenter
            
            if not document_id or not email:
                raise MCPError("document_id and email are required", 400)
            
            # Share document
            self.drive_service.permissions().create(
                fileId=document_id,
                body={
                    'type': 'user',
                    'role': role,
                    'emailAddress': email
                }
            ).execute()
            
            return self._format_mcp_response({
                'document_id': document_id,
                'shared_with': email,
                'role': role,
                'shared_at': datetime.now().isoformat()
            })
            
        except HttpError as e:
            logger.error(f"Share document error: {e}")
            raise MCPError(f"Failed to share document: {e}", 500)


# Server factory function
def create_docs_mcp_server(config: Dict[str, Any]) -> DocsMCPServer:
    """Create Docs MCP server instance"""
    return DocsMCPServer(config)
