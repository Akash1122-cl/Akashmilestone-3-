# Google API Setup for MCP Servers (Phase 5)

## Step 1: Google Cloud Project Setup

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project: `review-pulse-mcp`
3. Enable billing (required for Google Workspace APIs)

### 2. Enable Required APIs
In your project, enable these APIs:

**Google Workspace APIs:**
- Google Docs API
- Gmail API
- Google Drive API (for file management)

**Authentication APIs:**
- OAuth 2.0 API
- Google Identity Platform

## Step 2: OAuth 2.0 Configuration

### 1. Configure OAuth Consent Screen
1. Go to APIs & Services → OAuth consent screen
2. Choose **External** (for production) or **Internal** (for testing)
3. Fill required fields:
   - App name: Review Pulse MCP
   - User support email: your-email@example.com
   - Developer contact: your-email@example.com

### 2. Add Scopes
Add these OAuth scopes:
```
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.compose
```

### 3. Create Credentials
1. Go to APIs & Services → Credentials
2. Create Credentials → OAuth 2.0 Client ID
3. Application type: **Web application**
4. Add authorized URIs:
   - `http://localhost:8000/oauth/callback` (for testing)
   - `https://your-domain.com/oauth/callback` (for production)

### 4. Download Credentials
Save the JSON file as `credentials.json` in your Phase 5 directory.

## Step 3: Install Required Libraries

```bash
# MCP Protocol libraries
pip install mcp

# Google API libraries
pip install google-api-python-client
pip install google-auth-httplib2
pip install google-auth-oauthlib
pip install google-auth

# Additional dependencies
pip install fastapi
pip install uvicorn
pip install python-multipart
pip install jinja2
pip install aiofiles
```

## Step 4: Test Google API Connection

Create a test script to verify setup:

```python
# test_google_api.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Test Gmail API
def test_gmail_api():
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().labels().list(userId='me').execute()
    print("Gmail API connected successfully!")
    return True

# Test Docs API
def test_docs_api():
    SCOPES = ['https://www.googleapis.com/auth/documents']
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    
    service = build('docs', 'v1', credentials=creds)
    print("Docs API connected successfully!")
    return True

if __name__ == '__main__':
    test_gmail_api()
    test_docs_api()
```

## Step 5: Environment Configuration

Create `.env` file:
```bash
# Google API Configuration
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback

# MCP Server Configuration
MCP_DOCS_PORT=8001
MCP_GMAIL_PORT=8002
MCP_HOST=localhost

# Email Configuration
DEFAULT_SENDER_EMAIL=your-email@example.com
EMAIL_SUBJECT_PREFIX=Review Pulse Report
```

## Step 6: Security Considerations

### 1. Store Credentials Securely
- Never commit `credentials.json` to version control
- Use environment variables for production
- Consider Google Secret Manager for production secrets

### 2. OAuth State Management
- Generate random state tokens
- Validate state on callback
- Store tokens securely (encrypted database)

### 3. Rate Limits
- Gmail API: 100 emails/day for free tier
- Docs API: 100 requests/minute
- Implement exponential backoff

## Step 7: Production Setup

### 1. Domain Verification
- Verify your domain in Google Cloud Console
- Add required DNS records
- Update OAuth redirect URI

### 2. Service Account (Alternative)
For server-to-server communication:
1. Create service account
2. Grant domain-wide delegation
3. Use service account keys instead of OAuth

### 3. Monitoring
- Track API usage
- Monitor token expiration
- Set up alerts for quota limits

## Troubleshooting

### Common Issues:
1. **"redirect_uri_mismatch"**: Check OAuth redirect URI matches exactly
2. **"access_denied"**: Verify all required scopes are added
3. **"invalid_client"**: Check client ID and secret are correct
4. **"quota_exceeded"**: Check API usage limits

### Debug Mode:
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

After setup is complete:
1. Implement MCP Docs server
2. Implement MCP Gmail server
3. Create stakeholder management
4. Test end-to-end delivery
