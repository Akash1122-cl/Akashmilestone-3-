"""
Base MCP Server Implementation for Phase 5
Provides common functionality for Google API integration
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import parse_qs

import aiohttp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


@dataclass
class MCPMessage:
    """MCP protocol message structure"""
    id: str
    method: str
    params: Dict[str, Any]
    timestamp: datetime


class MCPServerBase:
    """Base class for MCP servers with Google API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.credentials: Optional[Credentials] = None
        self.oauth_state: Optional[str] = None
        self.app = FastAPI(title=f"MCP {config.get('service_name', 'Server')}")
        
        # Setup OAuth flow
        self.scopes = config.get('scopes', [])
        self.client_config = {
            "web": {
                "client_id": config.get('client_id'),
                "client_secret": config.get('client_secret'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [config.get('redirect_uri', 'http://localhost:8000/oauth/callback')]
            }
        }
        
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "service": self.config.get('service_name')}
        
        @self.app.get("/auth")
        async def start_auth():
            """Start OAuth flow"""
            try:
                flow = Flow.from_client_config(
                    self.client_config,
                    scopes=self.scopes,
                    redirect_uri=self.config.get('redirect_uri')
                )
                
                # Generate state token
                self.oauth_state = self._generate_state()
                flow.state = self.oauth_state
                
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    state=self.oauth_state
                )
                
                return {"auth_url": auth_url, "state": self.oauth_state}
                
            except Exception as e:
                logger.error(f"Auth flow error: {e}")
                raise HTTPException(status_code=500, detail="Failed to start auth flow")
        
        @self.app.get("/oauth/callback")
        async def oauth_callback(request: Request):
            """Handle OAuth callback"""
            try:
                # Get authorization code
                code = request.query_params.get('code')
                state = request.query_params.get('state')
                error = request.query_params.get('error')
                
                if error:
                    raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
                
                if not code or not state:
                    raise HTTPException(status_code=400, detail="Missing code or state")
                
                # Validate state
                if state != self.oauth_state:
                    raise HTTPException(status_code=400, detail="Invalid state")
                
                # Exchange code for credentials
                flow = Flow.from_client_config(
                    self.client_config,
                    scopes=self.scopes,
                    redirect_uri=self.config.get('redirect_uri'),
                    state=state
                )
                
                flow.fetch_token(code=code)
                self.credentials = flow.credentials
                
                logger.info("OAuth authentication successful")
                return RedirectResponse(url="/auth/success")
                
            except Exception as e:
                logger.error(f"OAuth callback error: {e}")
                raise HTTPException(status_code=500, detail="OAuth callback failed")
        
        @self.app.get("/auth/success")
        async def auth_success():
            return {"message": "Authentication successful", "status": "authenticated"}
        
        @self.app.get("/auth/status")
        async def auth_status():
            """Check authentication status"""
            if self.credentials and self.credentials.valid:
                return {
                    "status": "authenticated",
                    "expires_at": self.credentials.expiry.isoformat() if self.credentials.expiry else None
                }
            else:
                return {"status": "not_authenticated"}
        
        @self.app.post("/mcp")
        async def handle_mcp_message(request: Request):
            """Handle MCP protocol messages"""
            try:
                message_data = await request.json()
                
                # Parse MCP message
                mcp_message = MCPMessage(
                    id=message_data.get('id', ''),
                    method=message_data.get('method', ''),
                    params=message_data.get('params', {}),
                    timestamp=datetime.now()
                )
                
                # Route to appropriate handler
                response = await self._handle_mcp_method(mcp_message)
                
                return {
                    "id": mcp_message.id,
                    "result": response,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"MCP message error: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"error": str(e), "timestamp": datetime.now().isoformat()}
                )
    
    def _generate_state(self) -> str:
        """Generate secure state token"""
        import secrets
        return secrets.token_urlsafe(32)
    
    async def _handle_mcp_method(self, message: MCPMessage) -> Dict[str, Any]:
        """Handle specific MCP methods - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement _handle_mcp_method")
    
    async def _ensure_authenticated(self):
        """Ensure user is authenticated"""
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                    return True
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    return False
            return False
        return True
    
    async def _get_google_service(self, service_name: str, version: str):
        """Get authenticated Google API service"""
        if not await self._ensure_authenticated():
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        try:
            service = build(service_name, version, credentials=self.credentials)
            return service
        except Exception as e:
            logger.error(f"Failed to build {service_name} service: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create {service_name} service")
    
    def _format_mcp_response(self, data: Any, error: Optional[str] = None) -> Dict[str, Any]:
        """Format MCP response"""
        response = {
            "timestamp": datetime.now().isoformat(),
            "service": self.config.get('service_name', 'MCP Server')
        }
        
        if error:
            response["error"] = error
        else:
            response["data"] = data
        
        return response


class MCPError(Exception):
    """Custom MCP error"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)
