# MCP Server Setup Guide

## 🚀 Quick Setup for Saksham's MCP Server

### Step 1: Google Cloud Project Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create New Project** (or use existing one)
3. **Enable APIs**:
   - Google Docs API
   - Gmail API
4. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" (for testing)
   - Add required scopes:
     - `https://www.googleapis.com/auth/documents`
     - `https://www.googleapis.com/auth/gmail.compose`
5. **Create Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file
6. **Rename to credentials.json** and place in project root

### Step 2: Generate Token (Local Only)

```bash
# Run authentication
python auth.py

# This will:
# 1. Open browser for Google login
# 2. Generate token.json
# 3. Save token locally
```

### Step 3: Local Testing

```bash
# Start the server
uvicorn server:app --reload

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/tools
```

### Step 4: Prepare for Render Deployment

1. **Get credentials.json content** (from Step 1)
2. **Get token.json content** (from Step 2)
3. **Add to Render Environment Variables**:
   - `GOOGLE_CREDENTIALS_JSON`: Paste credentials.json content
   - `GOOGLE_TOKEN_JSON`: Paste token.json content
   - `AUTO_APPROVE`: "true" (auto-approve on Render)

### Step 5: Deploy to Render

1. **Push to GitHub** (already done)
2. **Go to Render Dashboard**: https://dashboard.render.com/
3. **New + Blueprint**
4. **Connect GitHub Repository**
5. **Use render.yaml** configuration
6. **Add Environment Variables**
7. **Deploy**

### Step 6: Test Deployment

```bash
# Test the deployed server
curl https://saksham-mcp-server.onrender.com/
curl https://saksham-mcp-server.onrender.com/tools

# Test API endpoints
curl -X POST https://saksham-mcp-server.onrender.com/append_to_doc \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "YOUR_DOC_ID", "content": "Test from MCP Server"}'
```

## 🔧 Environment Variables

### Required for Render:
- `GOOGLE_CREDENTIALS_JSON`: OAuth credentials (JSON format)
- `GOOGLE_TOKEN_JSON`: Authentication token (JSON format)
- `AUTO_APPROVE`: "true" (auto-approve actions on Render)

### Optional:
- `PYTHON_VERSION`: "3.11.9"
- `PORT`: Render sets this automatically

## 📋 API Endpoints

### Health Check
- `GET /` - Server status

### Tools List
- `GET /tools` - Available MCP tools

### Append to Doc
- `POST /append_to_doc`
```json
{
  "doc_id": "DOC_ID",
  "content": "Content to append"
}
```

### Create Email Draft
- `POST /create_email_draft`
```json
{
  "to": "email@example.com",
  "subject": "Email Subject",
  "body": "Email body content"
}
```

## 🚨 Important Notes

1. **Never commit credentials.json or token.json** to Git
2. **Token expires** and needs refresh
3. **Auto-approve** is enabled on Render for production use
4. **Local testing** requires manual approval in terminal
5. **Google Doc must have edit access** for the service account

## 🔄 Token Refresh

If token expires:
1. Run `python auth.py` locally again
2. Update `GOOGLE_TOKEN_JSON` on Render
3. Redeploy

## 📞 Support

- Server URL: https://saksham-mcp-server.onrender.com/
- Documentation: /docs endpoint
- Health Check: / endpoint
