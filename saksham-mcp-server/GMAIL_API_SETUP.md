# Gmail API Integration with MCP Server

## 🚀 Complete Setup Guide for mile-stone-3 Project

This guide will help you integrate your Gmail API with the MCP server to access your system.

## 📋 Prerequisites

- Google Cloud Project: `mile-stone-3`
- Gmail API enabled
- MCP server cloned and ready
- Access to your Google account

## 🔧 Step 1: Configure OAuth 2.0 Credentials

### 1.1 Access Google Cloud Console
1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account
3. Select project: `mile-stone-3`

### 1.2 Enable Gmail API (if not already enabled)
1. Navigate to: APIs & Services → Library
2. Search for "Gmail API"
3. Click "Enable" if not already enabled

### 1.3 Configure OAuth Consent Screen
1. Go to: APIs & Services → OAuth consent screen
2. Choose "External" (for testing)
3. Fill in required fields:
   - **App name**: Review Pulse MCP Server
   - **User support email**: your-email@gmail.com
   - **Developer contact**: your-email@gmail.com
4. Add scopes:
   - `https://www.googleapis.com/auth/gmail.compose`
   - `https://www.googleapis.com/auth/documents`
5. Add test users (your email address)
6. Save and continue

### 1.4 Create OAuth 2.0 Credentials
1. Go to: APIs & Services → Credentials
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Desktop application"
4. Give it a name: "MCP Server Credentials"
5. Click "Create"
6. **Download the JSON file** - this is your `credentials.json`

## 🔑 Step 2: Generate Authentication Token

### 2.1 Setup Local Environment
```bash
# Navigate to MCP server directory
cd saksham-mcp-server

# Place credentials.json in the project root
# (The JSON file you downloaded from Google Cloud)
```

### 2.2 Run Authentication Flow
```bash
# Install dependencies if not already done
pip install -r requirements.txt

# Run authentication script
python auth.py
```

### 2.3 Complete OAuth Flow
1. This will open a browser window
2. Sign in with your Google account
3. Grant permissions for Gmail and Google Docs access
4. The script will generate `token.json`
5. **Save the token.json file** - this contains your access tokens

## 🚀 Step 3: Update MCP Server for Production

### 3.1 Prepare Credentials for Render
You have two options:

**Option A: Environment Variables (Recommended)**
```bash
# Convert credentials.json to environment variable
# Copy the content of credentials.json (without formatting)
GOOGLE_CREDENTIALS_JSON='{"installed":{"client_id":"your_client_id","project_id":"mile-stone-3","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"your_client_secret","redirect_uris":["http://localhost:8080"]}}'

# Convert token.json to environment variable
# Copy the content of token.json (without formatting)
GOOGLE_TOKEN_JSON='{"token":"your_access_token","refresh_token":"your_refresh_token","token_uri":"https://oauth2.googleapis.com/token","client_id":"your_client_id","client_secret":"your_client_secret","scopes":["https://www.googleapis.com/auth/gmail.compose","https://www.googleapis.com/auth/documents"],"expiry_date":1234567890}'
```

**Option B: File-based (for local testing)**
- Keep `credentials.json` and `token.json` in the project root
- These files are already in `.gitignore` and won't be committed

### 3.2 Update Render Environment Variables
1. Go to your Render dashboard: https://dashboard.render.com/
2. Navigate to your MCP service
3. Go to "Environment" tab
4. Add these environment variables:
   - `GOOGLE_CREDENTIALS_JSON`: Paste your credentials.json content
   - `GOOGLE_TOKEN_JSON`: Paste your token.json content
   - `AUTO_APPROVE`: "true" (already set)
5. Click "Save Changes"
6. Trigger a new deployment

## 🧪 Step 4: Test Gmail API Integration

### 4.1 Test Local MCP Server
```bash
# Start local server
uvicorn server:app --reload

# Test Gmail endpoint
curl -X POST http://localhost:8000/create_email_draft \
  -H "Content-Type: application/json" \
  -d '{
    "to": "your-email@gmail.com",
    "subject": "Test from MCP Server",
    "body": "This is a test email created via MCP integration"
  }'
```

### 4.2 Test Production MCP Server
```bash
# Test deployed server
curl -X POST https://saksham-mcp-server.onrender.com/create_email_draft \
  -H "Content-Type: application/json" \
  -d '{
    "to": "your-email@gmail.com",
    "subject": "Test from Production MCP",
    "body": "This is a test from the deployed MCP server"
  }'
```

### 4.3 Test Google Docs Integration
```bash
# Test Google Docs (you'll need a real Google Doc ID)
curl -X POST https://saksham-mcp-server.onrender.com/append_to_doc \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "YOUR_GOOGLE_DOC_ID",
    "content": "Test content from MCP server integration"
  }'
```

## 🔗 Step 5: Integrate with Phase 5

### 5.1 Update Phase 5 Configuration
Create/update `.env` in Phase 5:
```bash
# Phase 5 Environment Variables
MCP_SERVER_URL=https://saksham-mcp-server.onrender.com
USE_EXTERNAL_MCP=true
GOOGLE_INTEGRATION_ENABLED=true
```

### 5.2 Test Phase 5 Integration
```bash
# Test Phase 5 with external MCP
cd phase5
python test_external_mcp.py
```

## 📊 Step 6: Monitor and Verify

### 6.1 Check Gmail API Usage
1. Go to: https://console.cloud.google.com/apis/api/gmail.googleapis.com/metrics
2. Monitor API usage and quotas
3. Check for any errors or rate limits

### 6.2 Verify Email Drafts
1. Check your Gmail drafts folder
2. Look for emails created by MCP server
3. Verify content and formatting

### 6.3 Check Google Docs
1. Open the Google Docs you updated
2. Verify content was appended correctly
3. Check for proper formatting

## 🚨 Troubleshooting

### Common Issues:

**1. "Invalid Credentials" Error**
- Verify credentials.json is correct
- Check that OAuth consent screen is configured
- Ensure test users are added

**2. "Token Expired" Error**
- Run `python auth.py` again to refresh token
- Update GOOGLE_TOKEN_JSON on Render
- Redeploy MCP service

**3. "Insufficient Permissions" Error**
- Verify correct scopes are added to OAuth consent screen
- Check that Gmail API is enabled
- Ensure user has granted necessary permissions

**4. "Doc Not Found" Error**
- Verify you have edit access to the Google Doc
- Check that doc_id is correct
- Ensure doc is shared with the service account

### Debug Commands:
```bash
# Check MCP server health
curl https://saksham-mcp-server.onrender.com/

# Check available tools
curl https://saksham-mcp-server.onrender.com/tools

# Test with verbose logging
uvicorn server:app --reload --log-level debug
```

## 📈 Success Indicators

✅ **MCP Server Health**: Returns 200 OK
✅ **Email Draft Creation**: Returns draft ID
✅ **Google Docs Update**: Content appended successfully
✅ **Phase 5 Integration**: External MCP status shows "connected"
✅ **Gmail API Metrics**: Show usage in Google Cloud Console

## 🔄 Maintenance

### Regular Tasks:
1. **Token Refresh**: Run `python auth.py` if tokens expire
2. **Monitor Usage**: Check Gmail API quotas monthly
3. **Update Credentials**: Rotate credentials if needed
4. **Backup Configs**: Keep secure backups of credentials

### Automation:
- Set up alerts for API quota limits
- Monitor MCP server health
- Automate token refresh process

## 📞 Support

If you encounter issues:
1. Check Google Cloud Console logs
2. Verify MCP server logs on Render
3. Test with local MCP server first
4. Check Phase 5 integration status

Your Gmail API integration with MCP server will be fully functional once these steps are completed!
