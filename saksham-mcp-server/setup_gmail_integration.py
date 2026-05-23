#!/usr/bin/env python3
"""
Gmail API Setup Script for MCP Server
This script helps you set up Gmail API integration with your MCP server
"""

import os
import json
import webbrowser
import time
import requests
import auth
from pathlib import Path

def check_prerequisites():
    """Check if prerequisites are met"""
    print("🔍 Checking prerequisites...")
    
    # Check if credentials.json exists
    if Path("credentials.json").exists():
        print("✅ credentials.json found")
        return True
    else:
        print("❌ credentials.json not found")
        print("\n📋 To create credentials.json:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Select project: mile-stone-3")
        print("3. Go to: APIs & Services → Credentials")
        print("4. Click 'Create Credentials' → 'OAuth client ID'")
        print("5. Select 'Desktop application'")
        print("6. Download the JSON file and save as 'credentials.json'")
        return False

def validate_credentials():
    """Validate credentials.json format"""
    try:
        with open("credentials.json", 'r') as f:
            creds = json.load(f)
        
        required_fields = ["client_id", "client_secret", "auth_uri", "token_uri"]
        if "installed" in creds:
            for field in required_fields:
                if field not in creds["installed"]:
                    print(f"❌ Missing required field: {field}")
                    return False
        else:
            print("❌ Invalid credentials format (missing 'installed' key)")
            return False
        
        print("✅ credentials.json format is valid")
        return True
        
    except json.JSONDecodeError:
        print("❌ credentials.json is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials.json: {e}")
        return False

def generate_env_variables():
    """Generate environment variables for Render deployment"""
    try:
        with open("credentials.json", 'r') as f:
            creds = json.load(f)
        
        # Generate credentials environment variable
        creds_env = f"GOOGLE_CREDENTIALS_JSON='{json.dumps(creds)}'"
        
        print("\n📧 Environment Variables for Render:")
        print("=" * 50)
        print("1. GOOGLE_CREDENTIALS_JSON:")
        print(creds_env)
        print("\n2. GOOGLE_TOKEN_JSON:")
        print("(Will be generated after authentication)")
        print("=" * 50)
        
        # Save to file for easy copy-paste
        with open("render_env_vars.txt", 'w') as f:
            f.write("GOOGLE_CREDENTIALS_JSON=")
            json.dump(creds, f)
            f.write("\nGOOGLE_TOKEN_JSON=<will_be_generated_after_auth>\n")
        
        print("💾 Saved to: render_env_vars.txt")
        return True
        
    except Exception as e:
        print(f"❌ Error generating environment variables: {e}")
        return False

def run_authentication():
    """Run the authentication flow"""
    print("\n🔐 Starting authentication flow...")
    
    try:
        # Check if token.json already exists
        if Path("token.json").exists():
            print("⚠️  token.json already exists")
            choice = input("Do you want to regenerate it? (y/n): ").lower()
            if choice != 'y':
                return True
        
        creds = auth.get_creds()
        
        if creds and creds.valid:
            print("✅ Authentication successful!")
            
            # Generate token environment variable
            token_data = creds.to_json()
            token_env = f"GOOGLE_TOKEN_JSON='{token_data}'"
            
            print("\n📧 Token Environment Variable:")
            print("=" * 50)
            print(token_env)
            print("=" * 50)
            
            # Update render_env_vars.txt
            with open("render_env_vars.txt", 'r') as f:
                content = f.read()
            
            content = content.replace("GOOGLE_TOKEN_JSON=<will_be_generated_after_auth>", 
                                  f"GOOGLE_TOKEN_JSON='{token_data}'")
            
            with open("render_env_vars.txt", 'w') as f:
                f.write(content)
            
            print("💾 Updated render_env_vars.txt with token")
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return False

def test_mcp_server():
    """Test the MCP server with Gmail integration"""
    print("\n🧪 Testing MCP server...")
    
    try:
        # Test health
        response = requests.get("http://localhost:8080/", timeout=5)
        if response.status_code == 200:
            print("✅ MCP server is running locally")
        else:
            print("❌ MCP server health check failed")
            return False
        
        # Test Gmail draft creation
        test_email = {
            "to": "test@example.com",  # Replace with your email
            "subject": f"Test from MCP Server - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "body": "This is a test email created via MCP Gmail integration."
        }
        
        response = requests.post(
            "http://localhost:8080/create_email_draft",
            json=test_email,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(f"✅ Gmail draft created successfully!")
                print(f"📧 Draft ID: {result.get('draft_id')}")
                print(f"📧 Check your Gmail drafts folder")
                return True
            else:
                print(f"❌ Gmail draft creation failed: {result}")
                return False
        else:
            print(f"❌ MCP server error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ MCP server is not running locally")
        print("💡 Start it with: uvicorn server:app --reload --port 8080")
        return False
    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

def test_production_server():
    """Test the production MCP server"""
    print("\n🌐 Testing production MCP server...")
    
    try:
        # Test health
        response = requests.get("https://saksham-mcp-server.onrender.com/", timeout=10)
        if response.status_code == 200:
            print("✅ Production MCP server is running")
        else:
            print("❌ Production MCP server health check failed")
            return False
        
        # Test Gmail draft creation
        test_email = {
            "to": "test@example.com",  # Replace with your email
            "subject": f"Production Test - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "body": "This is a test from the production MCP server."
        }
        
        response = requests.post(
            "https://saksham-mcp-server.onrender.com/create_email_draft",
            json=test_email,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(f"✅ Production Gmail draft created!")
                print(f"📧 Draft ID: {result.get('draft_id')}")
                print(f"📧 Check your Gmail drafts folder")
                return True
            else:
                print(f"❌ Production Gmail draft failed: {result}")
                return False
        else:
            print(f"❌ Production MCP server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing production server: {e}")
        return False

def main():
    """Main setup process"""
    print("🚀 Gmail API Integration Setup for MCP Server")
    print("=" * 50)
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        return
    
    # Step 2: Validate credentials
    if not validate_credentials():
        return
    
    # Step 3: Generate environment variables
    if not generate_env_variables():
        return
    
    # Step 4: Run authentication
    if not run_authentication():
        return
    
    # Step 5: Test local server
    print("\n📝 Note: Make sure your MCP server is running locally")
    print("   Run: uvicorn server:app --reload --port 8080")
    
    choice = input("Do you want to test the local server? (y/n): ").lower()
    if choice == 'y':
        test_mcp_server()
    
    # Step 6: Test production server
    choice = input("Do you want to test the production server? (y/n): ").lower()
    if choice == 'y':
        test_production_server()
    
    print("\n🎉 Gmail API integration setup completed!")
    print("\n📋 Next Steps:")
    print("1. Copy environment variables from render_env_vars.txt")
    print("2. Add them to your Render service environment")
    print("3. Redeploy the MCP server on Render")
    print("4. Test with Phase 5 integration")

if __name__ == "__main__":
    main()
