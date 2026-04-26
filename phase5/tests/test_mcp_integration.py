"""
Test MCP Integration for Phase 5
Tests Docs and Gmail MCP servers with mock Google APIs
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_base import MCPServerBase, MCPMessage
from docs_mcp_server import DocsMCPServer, create_docs_mcp_server
from gmail_mcp_server import GmailMCPServer, create_gmail_mcp_server
from delivery_service import DeliveryService, DeliveryRequest, create_delivery_service
from stakeholder_manager import StakeholderManager, Stakeholder, DeliveryFrequency


class TestMCPServerBase:
    """Test base MCP server functionality"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'redirect_uri': 'http://localhost:8000/oauth/callback',
            'service_name': 'Test MCP Server'
        }
    
    @pytest.fixture
    def mcp_server(self, mock_config):
        return MCPServerBase(mock_config)
    
    def test_server_initialization(self, mcp_server, mock_config):
        """Test MCP server initialization"""
        assert mcp_server.config == mock_config
        assert mcp_server.credentials is None
        assert mcp_server.oauth_state is None
    
    def test_generate_state(self, mcp_server):
        """Test state token generation"""
        state1 = mcp_server._generate_state()
        state2 = mcp_server._generate_state()
        
        assert state1 != state2
        assert len(state1) >= 32
        assert len(state2) >= 32
    
    def test_format_mcp_response(self, mcp_server):
        """Test MCP response formatting"""
        data = {'test': 'value'}
        response = mcp_server._format_mcp_response(data)
        
        assert 'timestamp' in response
        assert 'data' in response
        assert response['data'] == data
        assert response['service'] == 'Test MCP Server'


class TestDocsMCPServer:
    """Test Google Docs MCP server"""
    
    @pytest.fixture
    def docs_config(self):
        return {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'redirect_uri': 'http://localhost:8000/oauth/callback',
            'service_name': 'Google Docs MCP'
        }
    
    @pytest.fixture
    def docs_server(self, docs_config):
        return DocsMCPServer(docs_config)
    
    @pytest.mark.asyncio
    async def test_create_document(self, docs_server):
        """Test document creation"""
        # Mock Google services
        with patch.object(docs_server, '_ensure_services') as mock_ensure:
            mock_ensure.return_value = True
            
            # Mock Drive service
            mock_drive = Mock()
            mock_drive.files.return_value.create.return_value.execute.return_value = {
                'id': 'doc123',
                'name': 'Test Document'
            }
            
            # Mock Docs service
            mock_docs = Mock()
            mock_docs.documents.return_value.batchUpdate.return_value.execute.return_value = {}
            
            docs_server.drive_service = mock_drive
            docs_server.docs_service = mock_docs
            
            # Test document creation
            params = {
                'title': 'Test Document',
                'content': '<h1>Test Content</h1>',
                'format': 'html'
            }
            
            message = MCPMessage(
                id='test1',
                method='docs.create',
                params=params,
                timestamp=datetime.now()
            )
            
            result = await docs_server._handle_mcp_method(message)
            
            assert result['data']['document_id'] == 'doc123'
            assert result['data']['title'] == 'Test Document'
            assert result['data']['status'] == 'created'
    
    @pytest.mark.asyncio
    async def test_get_document(self, docs_server):
        """Test getting document content"""
        with patch.object(docs_server, '_ensure_services') as mock_ensure:
            mock_ensure.return_value = True
            
            # Mock services
            mock_docs = Mock()
            mock_docs.documents.return_value.get.return_value.execute.return_value = {
                'documentId': 'doc123',
                'title': 'Test Document',
                'body': {'content': []}
            }
            
            mock_drive = Mock()
            mock_drive.files.return_value.get.return_value.execute.return_value = {
                'name': 'Test Document',
                'webViewLink': 'https://docs.google.com/document/d/doc123'
            }
            
            docs_server.docs_service = mock_docs
            docs_server.drive_service = mock_drive
            
            params = {'document_id': 'doc123'}
            message = MCPMessage(
                id='test2',
                method='docs.get',
                params=params,
                timestamp=datetime.now()
            )
            
            result = await docs_server._handle_mcp_method(message)
            
            assert result['data']['document_id'] == 'doc123'
            assert result['data']['title'] == 'Test Document'
    
    def test_html_to_docs_requests(self, docs_server):
        """Test HTML to Google Docs conversion"""
        html_content = '<h1>Test Title</h1><p>Test paragraph</p>'
        requests = docs_server._html_to_docs_requests(html_content)
        
        assert len(requests) > 0
        assert any('insertText' in req for req in requests)
        assert any('updateTextStyle' in req for req in requests)
    
    def test_markdown_to_docs_requests(self, docs_server):
        """Test Markdown to Google Docs conversion"""
        md_content = '# Test Title\n\nTest paragraph'
        requests = docs_server._markdown_to_docs_requests(md_content)
        
        assert len(requests) > 0
        assert any('insertText' in req for req in requests)


class TestGmailMCPServer:
    """Test Gmail MCP server"""
    
    @pytest.fixture
    def gmail_config(self):
        return {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'redirect_uri': 'http://localhost:8000/oauth/callback',
            'service_name': 'Gmail MCP'
        }
    
    @pytest.fixture
    def gmail_server(self, gmail_config):
        return GmailMCPServer(gmail_config)
    
    @pytest.mark.asyncio
    async def test_send_email(self, gmail_server):
        """Test email sending"""
        with patch.object(gmail_server, '_ensure_services') as mock_ensure:
            mock_ensure.return_value = True
            
            # Mock Gmail service
            mock_gmail = Mock()
            mock_gmail.users.return_value.messages.return_value.send.return_value.execute.return_value = {
                'id': 'msg123',
                'threadId': 'thread123'
            }
            
            gmail_server.gmail_service = mock_gmail
            
            params = {
                'to': ['test@example.com'],
                'subject': 'Test Email',
                'content': '<p>Test content</p>',
                'content_type': 'html'
            }
            
            message = MCPMessage(
                id='test3',
                method='gmail.send',
                params=params,
                timestamp=datetime.now()
            )
            
            result = await gmail_server._handle_mcp_method(message)
            
            assert result['data']['message_id'] == 'msg123'
            assert result['data']['thread_id'] == 'thread123'
            assert result['data']['status'] == 'sent'
    
    @pytest.mark.asyncio
    async def test_create_draft(self, gmail_server):
        """Test creating email draft"""
        with patch.object(gmail_server, '_ensure_services') as mock_ensure:
            mock_ensure.return_value = True
            
            mock_gmail = Mock()
            mock_gmail.users.return_value.drafts.return_value.create.return_value.execute.return_value = {
                'id': 'draft123',
                'message': {'id': 'msg123'}
            }
            
            gmail_server.gmail_service = mock_gmail
            
            params = {
                'to': ['test@example.com'],
                'subject': 'Test Draft',
                'content': 'Test content'
            }
            
            message = MCPMessage(
                id='test4',
                method='gmail.draft',
                params=params,
                timestamp=datetime.now()
            )
            
            result = await gmail_server._handle_mcp_method(message)
            
            assert result['data']['draft_id'] == 'draft123'
            assert result['data']['status'] == 'draft'
    
    def test_create_email_message(self, gmail_server):
        """Test email message creation"""
        message = gmail_server._create_email_message(
            to=['test@example.com'],
            subject='Test Subject',
            content='Test content',
            content_type='plain'
        )
        
        assert 'raw' in message
        assert isinstance(message['raw'], str)
    
    def test_add_attachment(self, gmail_server):
        """Test adding attachments to email"""
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        attachment = {
            'filename': 'test.txt',
            'content': 'Test file content',
            'content_type': 'text/plain'
        }
        
        gmail_server._add_attachment(msg, attachment)
        
        assert len(msg.get_payload()) > 1


class TestStakeholderManager:
    """Test stakeholder management"""
    
    @pytest.fixture
    def mock_config(self):
        return {'test': 'config'}
    
    @pytest.fixture
    def stakeholder_manager(self, mock_config):
        return StakeholderManager(mock_config)
    
    def test_add_stakeholder(self, stakeholder_manager):
        """Test adding new stakeholder"""
        stakeholder = Stakeholder(
            email='new@example.com',
            name='New User',
            role='manager',
            products=['TestApp'],
            frequency=DeliveryFrequency.WEEKLY
        )
        
        result = stakeholder_manager.add_stakeholder(stakeholder)
        
        assert result is True
        assert 'new@example.com' in stakeholder_manager.stakeholders
    
    def test_remove_stakeholder(self, stakeholder_manager):
        """Test removing stakeholder"""
        # First add a stakeholder
        stakeholder = Stakeholder(
            email='remove@example.com',
            name='Remove User',
            role='manager',
            products=['TestApp'],
            frequency=DeliveryFrequency.WEEKLY
        )
        stakeholder_manager.add_stakeholder(stakeholder)
        
        # Then remove
        result = stakeholder_manager.remove_stakeholder('remove@example.com')
        
        assert result is True
        assert not stakeholder_manager.stakeholders['remove@example.com'].active
    
    def test_get_stakeholders_for_product(self, stakeholder_manager):
        """Test getting stakeholders for product"""
        stakeholders = stakeholder_manager.get_stakeholders_for_product('TestApp')
        
        assert isinstance(stakeholders, list)
        assert all(isinstance(s, Stakeholder) for s in stakeholders)
    
    def test_get_pending_deliveries(self, stakeholder_manager):
        """Test getting pending deliveries"""
        pending = stakeholder_manager.get_pending_deliveries('TestApp')
        
        assert isinstance(pending, list)
        assert all(isinstance(s, Stakeholder) for s in pending)
    
    def test_delivery_statistics(self, stakeholder_manager):
        """Test delivery statistics"""
        stats = stakeholder_manager.get_delivery_statistics()
        
        assert 'total_sent' in stats
        assert 'total_delivered' in stats
        assert 'delivery_rate' in stats
        assert isinstance(stats['delivery_rate'], float)


class TestDeliveryService:
    """Test delivery service orchestration"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'redirect_uri': 'http://localhost:8000/oauth/callback'
        }
    
    @pytest.fixture
    def delivery_service(self, mock_config):
        return DeliveryService(mock_config)
    
    @pytest.mark.asyncio
    async def test_deliver_report_success(self, delivery_service):
        """Test successful report delivery"""
        # Mock the MCP servers
        with patch.object(delivery_service.docs_server, '_handle_mcp_method') as mock_docs, \
             patch.object(delivery_service.gmail_server, '_handle_mcp_method') as mock_gmail:
            
            # Mock document creation
            mock_docs.return_value = {
                'data': {'document_id': 'doc123'}
            }
            
            # Mock email sending
            mock_gmail.return_value = {
                'data': {
                    'message_id': 'msg123',
                    'thread_id': 'thread123',
                    'sent_at': datetime.now().isoformat()
                }
            }
            
            request = DeliveryRequest(
                product_id='TestApp',
                report_content='<h1>Test Report</h1>',
                report_format='html',
                subject='Weekly Report'
            )
            
            result = await delivery_service.deliver_report(request)
            
            assert result.product_id == 'TestApp'
            assert result.document_id == 'doc123'
            assert result.successful_deliveries > 0
    
    @pytest.mark.asyncio
    async def test_deliver_report_no_recipients(self, delivery_service):
        """Test delivery with no recipients"""
        request = DeliveryRequest(
            product_id='UnknownApp',
            report_content='Test content',
            report_format='html'
        )
        
        with pytest.raises(Exception) as exc_info:
            await delivery_service.deliver_report(request)
        
        assert 'No recipients found' in str(exc_info.value)
    
    def test_generate_document_title(self, delivery_service):
        """Test document title generation"""
        title = delivery_service._generate_document_title('TestApp')
        
        assert 'TestApp' in title
        assert 'Weekly Review Report' in title
        assert 'Week' in title
    
    def test_generate_email_subject(self, delivery_service):
        """Test email subject generation"""
        subject = delivery_service._generate_email_subject('TestApp')
        
        assert 'TestApp' in subject
        assert 'Weekly Review Report' in subject
        assert '📊' in subject
    
    def test_generate_email_content(self, delivery_service):
        """Test email content generation"""
        content = delivery_service._generate_email_content('TestApp', 'doc123')
        
        assert 'TestApp' in content
        assert 'doc123' in content
        assert '<html>' in content
        assert 'Weekly Review Report' in content


class TestMCPIntegration:
    """Test end-to-end MCP integration"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'redirect_uri': 'http://localhost:8000/oauth/callback'
        }
    
    @pytest.mark.asyncio
    async def test_full_delivery_pipeline(self, mock_config):
        """Test complete delivery pipeline"""
        delivery_service = create_delivery_service(mock_config)
        
        # Mock both MCP servers
        with patch.object(delivery_service.docs_server, '_handle_mcp_method') as mock_docs, \
             patch.object(delivery_service.gmail_server, '_handle_mcp_method') as mock_gmail:
            
            # Setup mocks
            mock_docs.return_value = {
                'data': {'document_id': 'doc123'}
            }
            
            mock_gmail.return_value = {
                'data': {
                    'message_id': 'msg123',
                    'thread_id': 'thread123',
                    'sent_at': datetime.now().isoformat()
                }
            }
            
            # Create delivery request
            request = DeliveryRequest(
                product_id='TestApp',
                report_content='<h1>Test Report</h1><p>Content here...</p>',
                report_format='html',
                subject='Test Weekly Report'
            )
            
            # Execute delivery
            result = await delivery_service.deliver_report(request)
            
            # Verify results
            assert result.product_id == 'TestApp'
            assert result.document_id == 'doc123'
            assert result.successful_deliveries > 0
            assert result.total_recipients > 0
            
            # Verify MCP calls were made
            assert mock_docs.called
            assert mock_gmail.called
    
    @pytest.mark.asyncio
    async def test_delivery_with_attachments(self, mock_config):
        """Test delivery with file attachments"""
        delivery_service = create_delivery_service(mock_config)
        
        with patch.object(delivery_service.docs_server, '_handle_mcp_method') as mock_docs, \
             patch.object(delivery_service.gmail_server, '_handle_mcp_method') as mock_gmail:
            
            mock_docs.return_value = {'data': {'document_id': 'doc123'}}
            mock_gmail.return_value = {
                'data': {
                    'message_id': 'msg123',
                    'thread_id': 'thread123',
                    'sent_at': datetime.now().isoformat()
                }
            }
            
            attachments = [
                {
                    'filename': 'report.pdf',
                    'content': b'PDF content here',
                    'content_type': 'application/pdf'
                }
            ]
            
            request = DeliveryRequest(
                product_id='TestApp',
                report_content='Test content',
                report_format='html',
                attachments=attachments
            )
            
            result = await delivery_service.deliver_report(request)
            
            assert result.successful_deliveries > 0
            
            # Verify attachment handling
            call_args = mock_gmail.call_args
            if call_args:
                params = call_args[0][0]['params']
                assert 'attachments' in params
                assert len(params['attachments']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
