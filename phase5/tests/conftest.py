"""
Pytest configuration for Phase 5 testing
"""

import pytest
import sys
import os
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock Google libraries for testing
sys.modules['google'] = Mock()
sys.modules['google.oauth2'] = Mock()
sys.modules['google.oauth2.credentials'] = Mock()
sys.modules['google.auth'] = Mock()
sys.modules['google.auth.transport'] = Mock()
sys.modules['google.auth.transport.requests'] = Mock()
sys.modules['google_auth_oauthlib'] = Mock()
sys.modules['google_auth_oauthlib.flow'] = Mock()
sys.modules['googleapiclient'] = Mock()
sys.modules['googleapiclient.discovery'] = Mock()
sys.modules['googleapiclient.errors'] = Mock()

# Mock MCP library
sys.modules['mcp'] = Mock()

# Mock other dependencies
sys.modules['aiohttp'] = Mock()
sys.modules['aiofiles'] = Mock()
sys.modules['aiosmtplib'] = Mock()
sys.modules['prometheus_client'] = Mock()
sys.modules['structlog'] = Mock()
sys.modules['email_validator'] = Mock()

# Mock FastAPI related
mock_fastapi = Mock()
mock_fastapi.responses = Mock()
mock_fastapi.responses.JSONResponse = Mock()
mock_fastapi.responses.RedirectResponse = Mock()
mock_fastapi.Request = Mock()
mock_fastapi.HTTPException = Mock()
sys.modules['fastapi'] = mock_fastapi
sys.modules['fastapi.responses'] = mock_fastapi.responses
sys.modules['uvicorn'] = Mock()
sys.modules['pydantic'] = Mock()
sys.modules['python_multipart'] = Mock()

# Create mock classes for testing
class MockCredentials:
    def __init__(self):
        self.valid = True
        self.expired = False
        self.refresh_token = "mock_refresh_token"
        self.expiry = None
    
    def refresh(self, request):
        self.valid = True
        self.expired = False

class MockFlow:
    @staticmethod
    def from_client_config(config, scopes, redirect_uri=None, state=None):
        flow = MockFlow()
        flow.client_config = config
        flow.scopes = scopes
        flow.redirect_uri = redirect_uri
        flow.state = state
        return flow
    
    def authorization_url(self, access_type='offline', include_granted_scopes='true', state=None):
        return ("https://accounts.google.com/o/oauth2/auth?", state)
    
    def fetch_token(self, code):
        self.credentials = MockCredentials()
        return self.credentials

# Apply mocks
sys.modules['google.oauth2.credentials'].Credentials = MockCredentials
sys.modules['google_auth_oauthlib.flow'].InstalledAppFlow = MockFlow
