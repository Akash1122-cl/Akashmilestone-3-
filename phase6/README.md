# Phase 6: Advanced Automation and Analytics

Phase 6 extends the Review Pulse system with advanced automation, analytics, and reporting capabilities using the external MCP server.

## 🚀 Features

### Advanced Automation
- **Scheduled Report Generation**: Automated weekly/biweekly/monthly reports
- **Smart Delivery Rules**: Conditional delivery based on metrics thresholds
- **Multi-channel Distribution**: Email, Google Docs, Slack, Teams integration
- **Batch Processing**: Handle multiple products simultaneously

### Enhanced Analytics
- **Trend Analysis**: Long-term sentiment and review trends
- **Competitive Intelligence**: Cross-product analysis and benchmarking
- **Predictive Insights**: ML-powered predictions for review volumes
- **Custom Dashboards**: Role-based analytics dashboards

### Advanced Reporting
- **Interactive Reports**: Dynamic, filterable reports
- **Executive Summaries**: AI-generated executive briefings
- **Custom Templates**: Branded report templates
- **Export Options**: PDF, Excel, PowerPoint, JSON formats

### Integration Features
- **External MCP Server**: Uses Saksham's MCP server for Google Workspace
- **API Gateway**: Unified API for all automation features
- **Webhook Support**: Real-time notifications and triggers
- **Third-party Integrations**: Salesforce, Jira, ServiceNow

## 🏗️ Architecture

```
Phase 6 API Gateway (FastAPI:8006)
├── Automation Engine
│   ├── Scheduler (Celery)
│   ├── Rule Engine
│   └── Batch Processor
├── Analytics Service
│   ├── Trend Analysis
│   ├── Predictive Models
│   └── Dashboard Builder
├── Reporting Service
│   ├── Template Engine
│   ├── Export Service
│   └── Distribution Manager
└── Integration Layer
    ├── External MCP Client
    ├── Webhook Manager
    └── Third-party APIs
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- Redis 6+
- PostgreSQL 14+
- Access to external MCP server

### Setup

```bash
# Clone and setup
cd phase6
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start services
redis-server
celery -A src.tasks worker --loglevel=info
uvicorn src.main:app --reload --host 0.0.0.0 --port 8006
```

## 🔧 Configuration

### Environment Variables

```bash
# Application
APP_NAME=Review Pulse Phase 6
APP_VERSION=6.0.0
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/review_pulse_phase6

# Redis
REDIS_URL=redis://localhost:6379/1

# External MCP Server
MCP_SERVER_URL=https://saksham-mcp-server.onrender.com
USE_EXTERNAL_MCP=true

# Analytics
ANALYTICS_DATA_RETENTION_DAYS=365
PREDICTIVE_MODEL_UPDATE_INTERVAL=daily

# Automation
SCHEDULER_ENABLED=true
MAX_CONCURRENT_REPORTS=10
BATCH_PROCESSING_CHUNK_SIZE=100

# Integrations
SLACK_WEBHOOK_URL=your_slack_webhook
TEAMS_WEBHOOK_URL=your_teams_webhook
SALESFORCE_API_URL=your_salesforce_url
```

## 📚 API Documentation

### Base URL
- **Development**: `http://localhost:8006`
- **Production**: `https://api.reviewpulse.dev/phase6`

### Core Endpoints

#### Automation
```bash
POST /api/v1/automation/schedules      # Create scheduled report
GET  /api/v1/automation/schedules      # List schedules
PUT  /api/v1/automation/schedules/{id}  # Update schedule
DELETE /api/v1/automation/schedules/{id} # Delete schedule

POST /api/v1/automation/rules          # Create automation rule
GET  /api/v1/automation/rules          # List rules
POST /api/v1/automation/batch-process   # Batch process products
```

#### Analytics
```bash
GET  /api/v1/analytics/trends/{product_id}     # Get trend analysis
GET  /api/v1/analytics/comparison             # Product comparison
GET  /api/v1/analytics/predictions/{product_id} # Get predictions
POST /api/v1/analytics/dashboard              # Create custom dashboard
```

#### Reporting
```bash
POST /api/v1/reports/generate                 # Generate advanced report
GET  /api/v1/reports/templates                # List templates
POST /api/v1/reports/custom                   # Create custom report
GET  /api/v1/reports/{id}/export              # Export report
```

#### Integration
```bash
POST /api/v1/integrations/webhooks            # Register webhook
GET  /api/v1/integrations/status              # Integration status
POST /api/v1/integrations/sync                # Sync with third-party
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific module
pytest tests/test_automation.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Integration Tests
```bash
# Test external MCP integration
pytest tests/test_mcp_integration.py -v

# Test analytics pipeline
pytest tests/test_analytics.py -v

# Test automation workflows
pytest tests/test_automation_workflows.py -v
```

## 🚀 Deployment

### Docker
```bash
# Build image
docker build -t reviewpulse/phase6 .

# Run container
docker run -p 8006:8006 reviewpulse/phase6
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/phase6/
```

## 📊 Usage Examples

### Create Scheduled Report
```python
import requests

schedule_data = {
    "name": "Weekly Product Report",
    "product_id": "product_123",
    "frequency": "weekly",
    "delivery_day": "monday",
    "delivery_time": "09:00",
    "recipients": ["manager@company.com", "team@company.com"],
    "report_template": "executive_summary",
    "delivery_methods": ["email", "google_docs"],
    "conditions": {
        "min_review_count": 10,
        "sentiment_threshold": 0.7
    }
}

response = requests.post(
    "http://localhost:8006/api/v1/automation/schedules",
    json=schedule_data
)
```

### Generate Trend Analysis
```python
trend_request = {
    "product_id": "product_123",
    "time_range": "90_days",
    "metrics": ["sentiment", "volume", "rating"],
    "compare_with": ["product_456", "product_789"],
    "include_predictions": True
}

response = requests.post(
    "http://localhost:8006/api/v1/analytics/trends/product_123",
    json=trend_request
)
```

### Create Custom Dashboard
```python
dashboard_config = {
    "name": "Executive Dashboard",
    "widgets": [
        {
            "type": "sentiment_trend",
            "product_id": "product_123",
            "time_range": "30_days"
        },
        {
            "type": "comparison_chart",
            "products": ["product_123", "product_456"],
            "metric": "rating"
        }
    ],
    "layout": "grid",
    "refresh_interval": "hourly"
}

response = requests.post(
    "http://localhost:8006/api/v1/analytics/dashboard",
    json=dashboard_config
)
```

## 🔒 Security

### Authentication
- JWT-based authentication
- API key management
- Role-based access control

### Data Protection
- Encrypted data storage
- Secure API communication
- Audit logging

### Compliance
- GDPR compliance
- Data retention policies
- Privacy controls

## 📈 Performance

### Optimization
- Redis caching for analytics data
- Database query optimization
- Async processing for reports

### Monitoring
- Prometheus metrics collection
- Custom performance dashboards
- Alerting for system health

## 🔄 Migration from Phase 5

Phase 6 is fully backward compatible with Phase 5. To migrate:

1. **Backup Phase 5 data**
2. **Install Phase 6 dependencies**
3. **Update environment variables**
4. **Run database migrations**
5. **Test external MCP integration**
6. **Migrate automation rules**
7. **Update API endpoints**

## 📞 Support

- **Documentation**: `/docs` endpoint
- **Health Check**: `/health` endpoint
- **Status**: `/api/v1/status` endpoint
- **Metrics**: `/metrics` endpoint

Phase 6 provides enterprise-grade automation and analytics capabilities while maintaining seamless integration with the existing Review Pulse ecosystem.
