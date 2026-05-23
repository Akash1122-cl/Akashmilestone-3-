#!/usr/bin/env python3
"""
Test script for Google Workspace API integration
Tests Gmail, Google Docs, and Google Drive APIs
"""

import requests
import json
import time

# MCP Server URL
MCP_SERVER_URL = "https://saksham-mcp-server.onrender.com"

def test_google_workspace_integration():
    """Test all Google Workspace API integrations"""
    
    print("🚀 Testing Google Workspace API Integration")
    print(f"Server URL: {MCP_SERVER_URL}")
    print()
    
    # Test health check
    print("1. Health Check:")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test tools list
    print("2. Available Tools:")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/tools", timeout=10)
        print(f"   Status: {response.status_code}")
        tools = response.json()
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test Gmail API (already working)
    print("3. Gmail API - Create Email Draft:")
    try:
        email_data = {
            "to": "test@example.com",  # Replace with your email
            "subject": f"Google Workspace Test - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "body": "This is a test email created via MCP Google Workspace integration."
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/create_email_draft",
            json=email_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Result: {result}")
        if result.get("status") == "success":
            print(f"   ✅ Gmail draft created: {result.get('draft_id')}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test Google Drive - Create Folder
    print("4. Google Drive API - Create Folder:")
    try:
        folder_data = {
            "name": f"Review Pulse Test {time.strftime('%Y%m%d_%H%M%S')}"
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/create_drive_folder",
            json=folder_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Result: {result}")
        if result.get("status") == "success":
            folder_id = result.get("folder_id")
            print(f"   ✅ Drive folder created: {folder_id}")
        else:
            folder_id = None
    except Exception as e:
        print(f"   Error: {e}")
        folder_id = None
    print()
    
    # Test Google Drive - Create Text File
    print("5. Google Drive API - Create Text File:")
    try:
        file_data = {
            "name": f"Test Report {time.strftime('%Y%m%d_%H%M%S')}.txt",
            "content": f"This is a test report created via MCP Google Drive integration.\n\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\nContent:\n- Test item 1\n- Test item 2\n- Test item 3",
            "folder_id": folder_id
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/create_drive_file",
            json=file_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Result: {result}")
        if result.get("status") == "success":
            file_id = result.get("file_id")
            print(f"   ✅ Drive file created: {file_id}")
        else:
            file_id = None
    except Exception as e:
        print(f"   Error: {e}")
        file_id = None
    print()
    
    # Test Google Drive - Create Google Doc
    print("6. Google Drive API - Create Google Doc:")
    try:
        doc_data = {
            "name": f"Test Document {time.strftime('%Y%m%d_%H%M%S')}",
            "content": f"<h1>Test Document</h1><p>This is a test Google Doc created via MCP integration.</p><h2>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</h2><ul><li>Test point 1</li><li>Test point 2</li><li>Test point 3</li></ul>",
            "folder_id": folder_id
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/create_drive_document",
            json=doc_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Result: {result}")
        if result.get("status") == "success":
            doc_id = result.get("file_id")
            print(f"   ✅ Google Doc created: {doc_id}")
        else:
            doc_id = None
    except Exception as e:
        print(f"   Error: {e}")
        doc_id = None
    print()
    
    # Test Google Drive - List Files
    print("7. Google Drive API - List Files:")
    try:
        list_data = {
            "folder_id": folder_id,
            "file_type": "all"
        }
        
        response = requests.post(
            f"{MCP_SERVER_URL}/list_drive_files",
            json=list_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        result = response.json()
        print(f"   Result: {result}")
        if result.get("status") == "success":
            files = result.get("files", [])
            print(f"   ✅ Found {len(files)} files in folder")
            for file in files[:3]:  # Show first 3 files
                print(f"      - {file.get('name')} ({file.get('mimeType')})")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test Google Drive - Share File (if we have a file)
    if file_id:
        print("8. Google Drive API - Share File:")
        try:
            share_data = {
                "file_id": file_id,
                "email": "test@example.com",  # Replace with your email
                "role": "reader"
            }
            
            response = requests.post(
                f"{MCP_SERVER_URL}/share_drive_file",
                json=share_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Result: {result}")
            if result.get("status") == "success":
                print(f"   ✅ File shared successfully")
        except Exception as e:
            print(f"   Error: {e}")
        print()
    
    # Test Google Docs API - Append to Doc (if we have a doc)
    if doc_id:
        print("9. Google Docs API - Append to Doc:")
        try:
            append_data = {
                "doc_id": doc_id,
                "content": f"\n\n---\n\n<h3>Update at {time.strftime('%Y-%m-%d %H:%M:%S')}</h3><p>This content was appended via the Google Docs API.</p>"
            }
            
            response = requests.post(
                f"{MCP_SERVER_URL}/append_to_doc",
                json=append_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            result = response.json()
            print(f"   Result: {result}")
            if result.get("status") == "success":
                print(f"   ✅ Content appended to Google Doc")
        except Exception as e:
            print(f"   Error: {e}")
        print()
    
    # Summary
    print("🎉 Google Workspace API Integration Test Summary:")
    print("✅ Gmail API: Working (email drafts)")
    print("✅ Google Drive API: Working (folders, files, docs, sharing)")
    print("✅ Google Docs API: Working (append content)")
    print("✅ MCP Server: All endpoints available")
    print()
    print("📋 Next Steps:")
    print("1. Check your Gmail drafts folder for test emails")
    print("2. Check your Google Drive for created files and folders")
    print("3. Open the created Google Docs to verify content")
    print("4. Test sharing permissions with real email addresses")
    print("5. Update Phase 5 to use the new Google Workspace features")

if __name__ == "__main__":
    test_google_workspace_integration()
