#!/usr/bin/env python3
"""
Test client for Saksham's MCP Server
"""

import requests
import json
import time

# MCP Server URL
MCP_SERVER_URL = "https://saksham-mcp-server.onrender.com"

def test_mcp_server():
    """Test the MCP server endpoints"""
    
    print("🚀 Testing Saksham's MCP Server")
    print(f"Server URL: {MCP_SERVER_URL}")
    print()
    
    # Test health check
    print("1. Health Check:")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test tools list
    print("2. Available Tools:")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/tools")
        print(f"   Status: {response.status_code}")
        tools = response.json()
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test append to doc (you'll need a real doc_id)
    print("3. Test Append to Doc:")
    try:
        test_data = {
            "doc_id": "YOUR_DOC_ID_HERE",  # Replace with actual Google Doc ID
            "content": f"Test content from MCP client at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/append_to_doc",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test create email draft
    print("4. Test Create Email Draft:")
    try:
        test_email = {
            "to": "test@example.com",  # Replace with actual email
            "subject": f"Test Email from MCP Client - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "body": "This is a test email created via MCP server."
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/create_email_draft",
            json=test_email,
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    print()

if __name__ == "__main__":
    test_mcp_server()
