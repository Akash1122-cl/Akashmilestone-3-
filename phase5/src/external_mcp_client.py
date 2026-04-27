"""
External MCP Client for Phase 5
Integrates with Saksham's MCP Server deployed on Render
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ExternalMCPClient:
    """Client for interacting with external MCP server"""
    
    def __init__(self, base_url: str = "https://saksham-mcp-server.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MCP server health"""
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Health check failed: {response.status}")
        except Exception as e:
            logger.error(f"MCP server health check failed: {e}")
            raise
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        try:
            async with self.session.get(f"{self.base_url}/tools") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get tools: {response.status}")
        except Exception as e:
            logger.error(f"Failed to get MCP tools: {e}")
            raise
    
    async def append_to_doc(self, doc_id: str, content: str) -> Dict[str, Any]:
        """Append content to Google Doc"""
        try:
            payload = {
                "doc_id": doc_id,
                "content": content
            }
            
            async with self.session.post(
                f"{self.base_url}/append_to_doc",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"Successfully appended to doc {doc_id}")
                    return result
                else:
                    logger.error(f"Failed to append to doc: {result}")
                    raise Exception(f"Append to doc failed: {result}")
                    
        except Exception as e:
            logger.error(f"Error appending to doc {doc_id}: {e}")
            raise
    
    async def create_email_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create Gmail draft"""
        try:
            payload = {
                "to": to,
                "subject": subject,
                "body": body
            }
            
            async with self.session.post(
                f"{self.base_url}/create_email_draft",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"Successfully created email draft for {to}")
                    return result
                else:
                    logger.error(f"Failed to create email draft: {result}")
                    raise Exception(f"Create email draft failed: {result}")
                    
        except Exception as e:
            logger.error(f"Error creating email draft for {to}: {e}")
            raise

class ExternalMCPDeliveryService:
    """Delivery service using external MCP server"""
    
    def __init__(self, mcp_url: str = "https://saksham-mcp-server.onrender.com"):
        self.mcp_url = mcp_url
        self.client = ExternalMCPClient(mcp_url)
        
    async def deliver_report_to_docs(self, doc_id: str, report_content: str) -> Dict[str, Any]:
        """Deliver report content to Google Doc"""
        try:
            async with self.client as mcp:
                # First check if server is healthy
                await mcp.health_check()
                
                # Append content to doc
                result = await mcp.append_to_doc(doc_id, report_content)
                
                return {
                    "status": "success",
                    "doc_id": doc_id,
                    "message": "Report delivered to Google Doc",
                    "mcp_result": result,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to deliver report to docs: {e}")
            return {
                "status": "error",
                "doc_id": doc_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_email_notification(self, to_email: str, subject: str, body: str, doc_link: str = None) -> Dict[str, Any]:
        """Send email notification using Gmail draft"""
        try:
            # Add doc link to email body if provided
            if doc_link:
                body += f"\n\nView the full report here: {doc_link}"
            
            async with self.client as mcp:
                # First check if server is healthy
                await mcp.health_check()
                
                # Create email draft
                result = await mcp.create_email_draft(to_email, subject, body)
                
                return {
                    "status": "success",
                    "to": to_email,
                    "message": "Email draft created",
                    "draft_id": result.get("draft_id"),
                    "mcp_result": result,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return {
                "status": "error",
                "to": to_email,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP server status and available tools"""
        try:
            async with self.client as mcp:
                health = await mcp.health_check()
                tools = await mcp.get_available_tools()
                
                return {
                    "status": "connected",
                    "server_url": self.mcp_url,
                    "health": health,
                    "available_tools": tools,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get MCP status: {e}")
            return {
                "status": "error",
                "server_url": self.mcp_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Factory function
def create_external_mcp_service(mcp_url: str = "https://saksham-mcp-server.onrender.com") -> ExternalMCPDeliveryService:
    """Create external MCP delivery service"""
    return ExternalMCPDeliveryService(mcp_url)
