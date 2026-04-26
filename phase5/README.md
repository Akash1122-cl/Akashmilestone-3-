# Phase 5: MCP Integration and Delivery

This phase implements Google Workspace MCP servers for automated report delivery to stakeholders.

## Overview

Phase 5 builds on the report generation from Phase 4 to:
- Create Google Docs via MCP protocol
- Send automated emails via Gmail API
- Manage stakeholder lists and delivery rules
- Track delivery status and statistics

## Components

### 1. Docs MCP Server (`src/docs_mcp_server.py`)
- **Google Docs API Integration** - Document creation and management
- **MCP Protocol** - Standardized interface for document operations
- **Content Formatting** - HTML/Markdown to Google Docs conversion
- **Document Sharing** - Automatic sharing with stakeholders

### 2. Gmail MCP Server (`src/gmail_mcp_server.py`)
- **Gmail API Integration** - Email composition and delivery
- **MCP Protocol** - Standardized interface for email operations
- **Attachment Support** - File attachments in emails
- **Delivery Tracking** - Message and thread tracking

### 3. Stakeholder Manager (`src/stakeholder_manager.py`)
- **Recipient Management** - Add/remove stakeholders
- **Delivery Rules** - Frequency and scheduling configuration
- **Delivery History** - Track sent emails and status
- **Statistics** - Delivery rates and analytics

### 4. Delivery Service (`src/delivery_service.py`)
- **Orchestration** - Coordinates between MCP servers
- **Report Delivery** - End-to-end delivery pipeline
- **Error Handling** - Retry failed deliveries
- **Status Tracking** - Real-time delivery monitoring

### 5. API Server (`src/main.py`)
- FastAPI endpoints for delivery operations
- OAuth authentication handling
- Stakeholder management APIs
- Statistics and monitoring endpoints

## Installation

### Prerequisites
- Python 3.11+
- Google Cloud Project with enabled APIs
- OAuth 2.0 credentials
- PostgreSQL 14+
- Redis 6+

### Google Cloud Setup

1. **Create Google Cloud Project**
   ```bash
   # Go to https://console.cloud.google.com/
   # Create project: review-pulse-mcp
   ```

2. **Enable Required APIs**
   - Google Docs API
   - Gmail API
   - Google Drive API
   - OAuth 2.0 API

3. **Configure OAuth 2.0**
   - Set up consent screen
   - Add required scopes
   - Create OAuth client ID
   - Download credentials.json

### Dependencies

```bash
pip install -r requirements.txt
```

### Required Packages
- `mcp` - MCP protocol implementation
- `google-api-python-client` - Google APIs
- `fastapi` - API framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

## Configuration

### Environment Variables

Edit `.env` file:
```bash
# Google API Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback

# Email Configuration
DEFAULT_SENDER_EMAIL=your-email@example.com
EMAIL_SUBJECT_PREFIX=Review Pulse Report

# Security
OAUTH_STATE_SECRET=your_random_secret_string
TOKEN_ENCRYPTION_KEY=your_32_char_encryption_key
JWT_SECRET=your_jwt_secret

# Database
DB_PASSWORD=your_db_password
REDIS_PASSWORD=your_redis_password
```

### Configuration File

Edit `config/config.yaml`:
```yaml
google_api:
  client_id: ${GOOGLE_CLIENT_ID}
  client_secret: ${GOOGLE_CLIENT_SECRET}
  redirect_uri: ${GOOGLE_REDIRECT_URI}

mcp_servers:
  docs:
    port: 8001
    host: localhost
  gmail:
    port: 8002
    host: localhost

email:
  default_sender: ${DEFAULT_SENDER_EMAIL}
  rate_limit_per_minute: 50
```

## Running the Application

### Development Mode

```bash
cd phase5
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python src/main.py
```

The API will be available at `http://localhost:8005`

### Production Mode

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8005 --workers 4
```

## API Endpoints

### Authentication
```
GET /auth/docs          # Start Google Docs OAuth
GET /auth/gmail         # Start Gmail OAuth
GET /oauth/callback     # OAuth callback handler
```

### Report Delivery
```
POST /api/v1/deliver-report
Content-Type: application/json

{
  "product_id": "TestApp",
  "report_content": "<html>...</html>",
  "report_format": "html",
  "subject": "Weekly Report - TestApp"
}
```

### Stakeholder Management
```
GET /api/v1/stakeholders
POST /api/v1/stakeholders
DELETE /api/v1/stakeholders/{email}
GET /api/v1/stakeholders/product/{product_id}
```

### Delivery Status
```
GET /api/v1/delivery-status/{product_id}
POST /api/v1/retry-delivery/{product_id}
GET /api/v1/statistics/delivery
```

### MCP Direct Access
```
POST /mcp/docs           # Direct Docs MCP access
POST /mcp/gmail          # Direct Gmail MCP access
```

## Usage Examples

### Deliver a Report

```python
import requests

# Deliver report to stakeholders
response = requests.post('http://localhost:8005/api/v1/deliver-report', json={
    "product_id": "TestApp",
    "report_content": "<h1>Weekly Report</h1><p>Analysis content...</p>",
    "report_format": "html",
    "subject": "Weekly Review Report - TestApp"
})

result = response.json()
print(f"Delivered to {result['result']['successful_deliveries']} recipients")
```

### Add Stakeholder

```python
# Add new stakeholder
response = requests.post('http://localhost:8005/api/v1/stakeholders', json={
    "email": "new.stakeholder@company.com",
    "name": "New Stakeholder",
    "role": "manager",
    "products": ["TestApp"],
    "frequency": "weekly"
})
```

### Check Delivery Status

```python
# Get delivery status
response = requests.get('http://localhost:8005/api/v1/delivery-status/TestApp')
status = response.json()
print(f"Status: {status['delivery_result']['successful_deliveries']}/{status['delivery_result']['total_recipients']} delivered")
```

## Testing

Run unit tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Architecture

```
┌─────────────────┐
│  Report Content │
│  (from Phase 4) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Delivery        │
│ Service         │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│ Docs    │ │ Gmail   │
│ MCP     │ │ MCP     │
│ Server  │ │ Server  │
└─────────┘ └─────────┘
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│ Stakeholders    │
│ Manager         │
└─────────────────┘
```

## MCP Protocol

The Model Context Protocol (MCP) provides a standardized interface for:

### Docs MCP Methods
- `docs.create` - Create new document
- `docs.get` - Get document content
- `docs.update` - Update document
- `docs.list` - List documents
- `docs.delete` - Delete document
- `docs.share` - Share document with users

### Gmail MCP Methods
- `gmail.send` - Send email
- `gmail.draft` - Create draft
- `gmail.get` - Get message
- `gmail.list` - List messages
- `gmail.thread` - Get thread
- `gmail.search` - Search messages

## Security Considerations

### OAuth 2.0 Security
- Use HTTPS in production
- Validate state tokens
- Store tokens securely
- Implement token refresh

### Data Protection
- Encrypt sensitive data
- Validate email addresses
- Rate limit API calls
- Monitor for abuse

## Troubleshooting

### Common Issues

1. **OAuth redirect_uri mismatch**
   - Check redirect URI in Google Console matches exactly
   - Include protocol (http/https) and port

2. **Insufficient permissions**
   - Verify all required scopes are added
   - Re-authenticate after scope changes

3. **API quota exceeded**
   - Monitor usage in Google Console
   - Implement exponential backoff
   - Consider paid tier for higher limits

4. **Email delivery failures**
   - Check Gmail API quota (100 emails/day free)
   - Verify sender email is authenticated
   - Check recipient email addresses

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python src/main.py
```

## Monitoring

### Metrics Available
- Delivery success rate
- API response times
- Authentication status
- Error rates by endpoint

### Health Checks
- `/health` - Service health
- `/auth/status` - Authentication status
- `/api/v1/statistics/delivery` - Delivery statistics

## Next Steps

- Phase 6: Production Deployment
- Kubernetes deployment
- Monitoring and alerting
- Disaster recovery procedures
