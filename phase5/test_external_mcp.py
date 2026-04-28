#!/usr/bin/env python3
"""
Test script for Phase 5 External MCP Integration
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add src to path
sys.path.append('src')

# Load test environment
load_dotenv('.env.test')

async def test_external_mcp_integration():
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    print('Testing Phase 5 External MCP Integration...')
    
    # Test health endpoint
    response = client.get('/health')
    health_data = response.json()
    print(f'Health check: {response.status_code} - {health_data["status"]}')
    
    # Test MCP status endpoint
    response = client.get('/api/v1/mcp-status')
    print(f'MCP status endpoint: {response.status_code}')
    if response.status_code == 200:
        mcp_status = response.json()
        print(f'Internal MCP: {mcp_status["internal_mcp"]["status"]}')
        print(f'External MCP: {mcp_status["external_mcp"]["status"]}')
        if 'details' in mcp_status.get('external_mcp', {}):
            print(f'External MCP Server: {mcp_status["external_mcp"]["details"]["server_url"]}')
    
    # Test delivery with external MCP
    print('\nTesting delivery with external MCP...')
    delivery_request = {
        "product_id": "test_product",
        "report_content": "<h1>Test Report</h1><p>This is a test report from Phase 5.</p>",
        "report_format": "html",
        "subject": "Test Report from Phase 5",
        "custom_recipients": ["test@example.com"],
        "use_external_mcp": True
    }
    
    response = client.post('/api/v1/deliver-report', json=delivery_request)
    print(f'External delivery: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print(f'Service used: {result["service"]}')
        print(f'Success: {result["success"]}')
        if result["success"]:
            print(f'Recipients: {result["result"]["total_recipients"]}')
            print(f'Successful: {result["result"]["successful_deliveries"]}')
            print(f'Failed: {result["result"]["failed_deliveries"]}')
            if 'email_drafts' in result["result"]:
                for draft in result["result"]["email_drafts"]:
                    print(f'Email draft created: {draft["draft_id"]} for {draft["recipient"]}')
    else:
        print(f'Error: {response.json()}')
    
    print('\nPhase 5 External MCP Integration test completed!')

if __name__ == '__main__':
    asyncio.run(test_external_mcp_integration())
