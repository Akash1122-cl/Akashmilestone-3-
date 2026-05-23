# Google Workspace API Setup for MCP Server

## 🚀 Complete Setup Guide for mile-stone-3 Project

This guide will help you set up Google Docs API and Google Drive API for your MCP server to access your system.

## 📋 Current Status

✅ **Gmail API**: Already working (drafts created successfully)  
⚠️ **Google Docs API**: Needs configuration  
⚠️ **Google Drive API**: Needs configuration  

## 🔧 Step 1: Enable Google Workspace APIs

### 1.1 Google Docs API Setup
1. Go to: https://console.cloud.google.com/apis/api/docs.googleapis.com/metrics?project=mile-stone-3&authuser=2
2. If not enabled, click "Enable"
3. Verify API is active and check usage metrics

### 1.2 Google Drive API Setup
1. Go to: https://console.cloud.google.com/apis/api/drive.googleapis.com/metrics?project=mile-stone-3&authuser=2
2. If not enabled, click "Enable"
3. Verify API is active and check usage metrics

### 1.3 Verify All APIs
Go to: https://console.cloud.google.com/apis/library
Search and ensure these APIs are enabled:
- ✅ Gmail API
- ⚠️ Google Docs API
- ⚠️ Google Drive API

## 🔐 Step 2: Update OAuth 2.0 Configuration

### 2.1 Access OAuth Consent Screen
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select project: `mile-stone-3`
3. Edit your existing OAuth consent screen

### 2.2 Add Required Scopes
Add these scopes to your OAuth consent screen:

```
Required Scopes:
• https://www.googleapis.com/auth/gmail.compose
• https://www.googleapis.com/auth/documents
• https://www.googleapis.com/auth/drive
• https://www.googleapis.com/auth/drive.file
```

### 2.3 Update Test Users
- Ensure your email address is in the test users list
- Save and publish the consent screen

## 🔑 Step 3: Update Credentials

### 3.1 Existing Credentials
If you already have credentials.json, you can reuse them. The OAuth consent screen update will add the new scopes.

### 3.2 Create New Credentials (if needed)
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create "OAuth client ID" → "Desktop application"
3. Download as `credentials.json`

## 🚀 Step 4: Regenerate Authentication Token

### 4.1 Backup Existing Token
```bash
# Backup current token (if exists)
cp token.json token.json.backup
```

### 4.2 Run Authentication Flow
```bash
cd saksham-mcp-server
python auth.py
```

This will:
- Open browser for Google login
- Request permissions for Gmail, Docs, and Drive
- Generate new `token.json` with extended permissions

## 📝 Step 5: Update MCP Server for Google Workspace

### 5.1 Update Scopes in auth.py
The auth.py file should include all required scopes:

```python
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]
```

### 5.2 Add Google Drive Functions
Create new functions for Drive integration:

```python
# Add to gmail_tool.py or create drive_tool.py
async def create_drive_file(name: str, content: str, folder_id: str = None):
    """Create a new file in Google Drive"""
    # Implementation for Drive API
    pass

async def upload_to_drive(file_path: str, folder_id: str = None):
    """Upload file to Google Drive"""
    # Implementation for Drive upload
    pass
```

## 🧪 Step 6: Test Integration

### 6.1 Test Google Docs API
```bash
# Test with a real Google Doc ID
curl -X POST https://saksham-mcp-server.onrender.com/append_to_doc \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "YOUR_REAL_GOOGLE_DOC_ID",
    "content": "Test content from MCP server with Google Workspace integration"
  }'
```

### 6.2 Test Google Drive API (after implementation)
```bash
# Test Drive file creation (if implemented)
curl -X POST https://saksham-mcp-server.onrender.com/create_drive_file \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Document",
    "content": "Test content from MCP server",
    "folder_id": "YOUR_FOLDER_ID"
  }'
```

## 🔄 Step 7: Update Production Environment

### 7.1 Update Render Environment Variables
1. Go to your Render dashboard
2. Update `GOOGLE_TOKEN_JSON` with the new token
3. Redeploy the service

### 7.2 Verify Production Status
```bash
# Test production server
curl https://saksham-mcp-server.onrender.com/
curl https://saksham-mcp-server.onrender.com/tools
```

## 📊 Step 8: Monitor API Usage

### 8.1 Google Docs API Metrics
- Visit: https://console.cloud.google.com/apis/api/docs.googleapis.com/metrics?project=mile-stone-3
- Monitor usage and quotas
- Check for any errors

### 8.2 Google Drive API Metrics
- Visit: https://console.cloud.google.com/apis/api/drive.googleapis.com/metrics?project=mile-stone-3
- Monitor file operations
- Check storage usage

### 8.3 Gmail API Metrics
- Visit: https://console.cloud.google.com/apis/api/gmail.googleapis.com/metrics?project=mile-stone-3
- Monitor email operations
- Check rate limits

## 🔧 Enhanced MCP Server Features

With Google Workspace integration, your MCP server will support:

### Google Docs Features:
- ✅ Append content to existing documents
- ✅ Create new documents
- ✅ Format text and add structure
- ✅ Share documents with stakeholders

### Google Drive Features:
- 🆕 Create new documents in Drive
- 🆕 Upload files and folders
- 🆕 Organize reports in specific folders
- 🆕 Share files with team members

### Gmail Features:
- ✅ Create email drafts
- ✅ Send emails (if implemented)
- ✅ Attach Drive files to emails
- ✅ Manage email templates

## 📋 Implementation Checklist

### Phase 1: API Setup
- [ ] Enable Google Docs API
- [ ] Enable Google Drive API
- [ ] Verify API metrics dashboards

### Phase 2: OAuth Configuration
- [ ] Update OAuth consent screen
- [ ] Add required scopes
- [ ] Update test users

### Phase 3: Authentication
- [ ] Backup existing token.json
- [ ] Run authentication flow
- [ ] Generate new token with extended permissions

### Phase 4: MCP Server Update
- [ ] Update auth.py scopes
- [ ] Add Drive API functions
- [ ] Test all integrations

### Phase 5: Production Deployment
- [ ] Update Render environment
- [ ] Test production endpoints
- [ ] Monitor API usage

### Phase 6: Phase 5 Integration
- [ ] Update Phase 5 to use new features
- [ ] Test end-to-end workflows
- [ ] Document new capabilities

## 🚨 Troubleshooting

### Common Issues:

**1. "Insufficient Permissions" Error**
- Verify all scopes are added to OAuth consent screen
- Regenerate token after updating scopes
- Check that user is in test users list

**2. "API Not Enabled" Error**
- Verify APIs are enabled in Google Cloud Console
- Check correct project is selected
- Ensure APIs are not in "disabled" state

**3. "Quota Exceeded" Error**
- Monitor API usage metrics
- Implement rate limiting
- Consider upgrading to paid tier if needed

**4. "File Not Found" Error**
- Verify Google Doc ID is correct
- Check sharing permissions
- Ensure document exists and is accessible

### Debug Commands:
```bash
# Check token contents
python -c "import json; print(json.dumps(json.load(open('token.json')), indent=2))"

# Verify scopes in token
python -c "import json; token=json.load(open('token.json')); print('Scopes:', token.get('scopes', []))"

# Test authentication
python auth.py
```

## 📈 Success Metrics

✅ **API Status**: All APIs enabled and active  
✅ **Authentication**: Token includes all required scopes  
✅ **MCP Server**: All endpoints working  
✅ **Google Docs**: Content appended successfully  
✅ **Google Drive**: Files created and managed  
✅ **Gmail**: Drafts created with attachments  
✅ **Phase 5**: Full integration working  
✅ **Production**: Deployed and monitored  

## 🎯 Next Steps

After completing this setup:
1. Test all Google Workspace integrations
2. Update Phase 5 to use new Drive features
3. Implement automated report workflows
4. Set up monitoring and alerts
5. Document new capabilities for users

Your MCP server will have full Google Workspace integration, enabling comprehensive automation and document management capabilities!
