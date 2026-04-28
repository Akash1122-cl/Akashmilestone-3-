# Review Pulse Backend API Gateway

A unified backend API gateway that orchestrates all Review Pulse phases and provides a single entry point for the frontend application.

## 🚀 Architecture Overview

The backend API gateway serves as the central coordinator for all Review Pulse phases, providing:
- **Unified API**: Single entry point for all frontend requests
- **Phase Orchestration**: Coordinates between all 5 phases
- **Authentication & Authorization**: JWT-based security
- **Rate Limiting**: Prevents API abuse
- **Caching**: Redis-based caching for performance
- **Monitoring**: Comprehensive metrics and health checks

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React SPA)   │
└────────┬────────┘
         │ HTTPS/WSS
         ▼
┌─────────────────┐
│   API Gateway   │
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│ Phase 1 │ │ Phase 2 │
│ 8000    │ │ 8001    │
└─────────┘ └─────────┘
    │         │
    ▼         ▼
┌─────────┐ ┌─────────┐
│ Phase 3 │ │ Phase 4 │
│ 8002    │ │ 8003    │
└─────────┘ └─────────┘
         │
         ▼
┌─────────────────┐
│   Phase 5       │
│   8005          │
└─────────────────┘
```

## 🛠️ Technology Stack

### Core Framework
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation and serialization
- **SQLAlchemy**: ORM for database operations

### Security
- **JWT**: Token-based authentication
- **bcrypt**: Password hashing
- **OAuth2**: Third-party authentication
- **CORS**: Cross-origin resource sharing

### Performance
- **Redis**: Caching and session storage
- **Background Tasks**: Celery with Redis broker
- **Connection Pooling**: Database connection management
- **Async/Await**: Non-blocking I/O

### Monitoring
- **Prometheus**: Metrics collection
- **Structlog**: Structured logging
- **Health Checks**: Service health monitoring
- **Performance Profiling**: Request timing

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Node.js 18+ (for frontend)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/Akash1122-cl/Akashmilestone-3-.git
cd Akashmilestone-3-/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 9000
```

### Environment Variables

```bash
# Application
APP_NAME=Review Pulse API Gateway
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/review_pulse
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password
REDIS_MAX_CONNECTIONS=100

# Authentication
SECRET_KEY=your_super_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Phase Services
PHASE1_URL=http://localhost:8000
PHASE2_URL=http://localhost:8001
PHASE3_URL=http://localhost:8002
PHASE4_URL=http://localhost:8003
PHASE5_URL=http://localhost:8005

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=200

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO
```

## 📚 API Documentation

### Base URL
- **Development**: `http://localhost:9000`
- **Staging**: `https://api-staging.reviewpulse.dev`
- **Production**: `https://api.reviewpulse.dev`

### Authentication

All API endpoints require authentication except for health checks:

```bash
# Login
curl -X POST "http://localhost:9000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password"}'

# Use token
curl -X GET "http://localhost:9000/api/v1/dashboard" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Core Endpoints

#### Authentication
```bash
POST /api/v1/auth/login          # User login
POST /api/v1/auth/register       # User registration
POST /api/v1/auth/refresh        # Refresh token
POST /api/v1/auth/logout         # User logout
GET  /api/v1/auth/me             # Current user info
```

#### Dashboard
```bash
GET  /api/v1/dashboard/metrics   # Dashboard metrics
GET  /api/v1/dashboard/health    # System health
GET  /api/v1/dashboard/activity   # Recent activity
```

#### Reviews
```bash
GET    /api/v1/reviews           # List reviews
GET    /api/v1/reviews/{id}      # Get review details
POST   /api/v1/reviews           # Create review
PUT    /api/v1/reviews/{id}      # Update review
DELETE /api/v1/reviews/{id}      # Delete review
GET    /api/v1/reviews/search    # Search reviews
```

#### Analysis
```bash
POST   /api/v1/analysis/run       # Run analysis
GET    /api/v1/analysis/{id}      # Get analysis results
GET    /api/v1/analysis/themes    # Get themes
GET    /api/v1/analysis/clusters  # Get clusters
```

#### Reports
```bash
GET    /api/v1/reports            # List reports
POST   /api/v1/reports/generate   # Generate report
GET    /api/v1/reports/{id}       # Get report
GET    /api/v1/reports/{id}/download # Download report
```

#### Stakeholders
```bash
GET    /api/v1/stakeholders       # List stakeholders
POST   /api/v1/stakeholders       # Add stakeholder
PUT    /api/v1/stakeholders/{id}  # Update stakeholder
DELETE /api/v1/stakeholders/{id}  # Remove stakeholder
```

### WebSocket Endpoints

```bash
# Real-time updates
WS /ws/dashboard                # Dashboard updates
WS /ws/reviews                  # Review updates
WS /ws/analysis                 # Analysis progress
```

## 🧩 Core Components

### API Gateway Service

```python
# src/services/gateway.py
class APIGateway:
    """Central API gateway for coordinating all phases"""
    
    def __init__(self):
        self.phase_clients = {
            'phase1': Phase1Client(PHASE1_URL),
            'phase2': Phase2Client(PHASE2_URL),
            'phase3': Phase3Client(PHASE3_URL),
            'phase4': Phase4Client(PHASE4_URL),
            'phase5': Phase5Client(PHASE5_URL)
        }
    
    async def process_reviews(self, product_id: str):
        """Orchestrate end-to-end review processing"""
        # Phase 1: Ingest reviews
        reviews = await self.phase_clients['phase1'].ingest_reviews(product_id)
        
        # Phase 2: Process and embed
        processed = await self.phase_clients['phase2'].process_reviews(reviews)
        
        # Phase 3: Analyze and cluster
        analysis = await self.phase_clients['phase3'].analyze_reviews(processed)
        
        # Phase 4: Generate report
        report = await self.phase_clients['phase4'].generate_report(analysis)
        
        # Phase 5: Deliver to stakeholders
        delivery = await self.phase_clients['phase5'].deliver_report(report)
        
        return {
            'reviews': len(reviews),
            'analysis_id': analysis.id,
            'report_id': report.id,
            'delivery_status': delivery.status
        }
```

### Authentication Service

```python
# src/services/auth.py
class AuthService:
    """JWT-based authentication service"""
    
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    async def authenticate_user(self, email: str, password: str):
        """Authenticate user credentials"""
        user = await self.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return False
        return user
    
    def create_access_token(self, data: dict):
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    async def get_current_user(self, token: str):
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=401, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await self.get_user_by_email(email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
```

### Caching Service

```python
# src/services/cache.py
class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis = Redis.from_url(REDIS_URL)
        self.default_ttl = 300  # 5 minutes
    
    async def get(self, key: str):
        """Get cached value"""
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: any, ttl: int = None):
        """Set cached value"""
        ttl = ttl or self.default_ttl
        await self.redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        """Delete cached value"""
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Delete keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

## 🔄 Request Flow

### Typical API Request

```python
# Example: Get dashboard metrics
async def get_dashboard_metrics(current_user: User):
    # 1. Check cache
    cache_key = f"dashboard:{current_user.id}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # 2. Gather data from phases
    metrics = {}
    
    # Phase 1: Review counts
    metrics['reviews'] = await phase1_client.get_review_counts()
    
    # Phase 2: Processing status
    metrics['processing'] = await phase2_client.get_processing_status()
    
    # Phase 3: Analysis results
    metrics['analysis'] = await phase3_client.get_latest_analysis()
    
    # Phase 4: Report status
    metrics['reports'] = await phase4_client.get_report_status()
    
    # Phase 5: Delivery status
    metrics['delivery'] = await phase5_client.get_delivery_status()
    
    # 3. Cache results
    await cache_service.set(cache_key, metrics, ttl=60)
    
    return metrics
```

### Background Task Processing

```python
# src/tasks.py
@celery.task
async def process_product_reviews(product_id: str):
    """Background task for processing reviews"""
    try:
        # Update status
        await cache_service.set(f"processing:{product_id}", {
            'status': 'processing',
            'started_at': datetime.utcnow()
        })
        
        # Process through phases
        gateway = APIGateway()
        result = await gateway.process_reviews(product_id)
        
        # Update final status
        await cache_service.set(f"processing:{product_id}", {
            'status': 'completed',
            'completed_at': datetime.utcnow(),
            'result': result
        })
        
        # Send notification
        await notification_service.send_completion_notification(product_id, result)
        
    except Exception as e:
        # Handle errors
        await cache_service.set(f"processing:{product_id}", {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.utcnow()
        })
        raise
```

## 📊 Monitoring and Metrics

### Prometheus Metrics

```python
# src/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Business metrics
REVIEWS_PROCESSED = Counter('reviews_processed_total', 'Total reviews processed')
ANALYSIS_COMPLETED = Counter('analysis_completed_total', 'Total analysis completed')
REPORTS_GENERATED = Counter('reports_generated_total', 'Total reports generated')

# System metrics
ACTIVE_USERS = Gauge('active_users_total', 'Total active users')
CACHE_HIT_RATE = Gauge('cache_hit_rate', 'Cache hit rate percentage')
```

### Health Checks

```python
# src/health.py
class HealthChecker:
    """Comprehensive health checking"""
    
    async def check_health(self):
        """Check overall system health"""
        checks = {
            'database': await self.check_database(),
            'redis': await self.check_redis(),
            'phases': await self.check_phases(),
            'external_apis': await self.check_external_apis()
        }
        
        overall_status = 'healthy' if all(
            check['status'] == 'healthy' for check in checks.values()
        ) else 'unhealthy'
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }
    
    async def check_phases(self):
        """Check all phase services"""
        phase_status = {}
        for phase_name, client in gateway.phase_clients.items():
            try:
                response = await client.health_check()
                phase_status[phase_name] = {
                    'status': 'healthy' if response['status'] == 'healthy' else 'unhealthy',
                    'response_time': response.get('response_time')
                }
            except Exception as e:
                phase_status[phase_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
        return phase_status
```

## 🧪 Testing

### Unit Tests

```python
# tests/test_gateway.py
@pytest.mark.asyncio
async def test_process_reviews():
    """Test end-to-end review processing"""
    gateway = APIGateway()
    
    # Mock phase clients
    with patch.object(gateway.phase_clients['phase1'], 'ingest_reviews') as mock_phase1, \
         patch.object(gateway.phase_clients['phase2'], 'process_reviews') as mock_phase2, \
         patch.object(gateway.phase_clients['phase3'], 'analyze_reviews') as mock_phase3, \
         patch.object(gateway.phase_clients['phase4'], 'generate_report') as mock_phase4, \
         patch.object(gateway.phase_clients['phase5'], 'deliver_report') as mock_phase5:
        
        # Setup mocks
        mock_phase1.return_value = [{'id': '1', 'text': 'Great app'}]
        mock_phase2.return_value = [{'id': '1', 'text': 'Great app', 'processed': True}]
        mock_phase3.return_value = AnalysisResult(id='analysis_1')
        mock_phase4.return_value = Report(id='report_1')
        mock_phase5.return_value = DeliveryResult(status='sent')
        
        # Test
        result = await gateway.process_reviews('test_product')
        
        # Assertions
        assert result['reviews'] == 1
        assert result['analysis_id'] == 'analysis_1'
        assert result['report_id'] == 'report_1'
        assert result['delivery_status'] == 'sent'
```

### Integration Tests

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_full_api_flow():
    """Test complete API flow"""
    # Create test user
    user_data = {
        'email': 'test@example.com',
        'password': 'testpassword'
    }
    response = await client.post('/api/v1/auth/register', json=user_data)
    assert response.status_code == 201
    
    # Login
    login_response = await client.post('/api/v1/auth/login', json=user_data)
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Get dashboard
    dashboard_response = await client.get('/api/v1/dashboard/metrics', headers=headers)
    assert dashboard_response.status_code == 200
    assert 'reviews' in dashboard_response.json()
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 9000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "9000"]
```

### Kubernetes Deployment

```yaml
# k8s/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: review-pulse-api-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: review-pulse-api-gateway
  template:
    metadata:
      labels:
        app: review-pulse-api-gateway
    spec:
      containers:
      - name: api-gateway
        image: reviewpulse/api-gateway:latest
        ports:
        - containerPort: 9000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: review-pulse-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: review-pulse-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 📈 Performance Optimization

### Database Optimization

```python
# Connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30

# Query optimization
async def get_reviews_with_pagination(
    page: int = 1,
    size: int = 50,
    filters: ReviewFilters = None
):
    """Optimized review listing with pagination"""
    query = select(Review).options(
        selectinload(Review.product),
        selectinload(Review.sentiment_analysis)
    )
    
    if filters:
        if filters.product_id:
            query = query.where(Review.product_id == filters.product_id)
        if filters.rating:
            query = query.where(Review.rating == filters.rating)
        if filters.date_range:
            query = query.where(
                Review.created_at.between(filters.date_range.start, filters.date_range.end)
            )
    
    # Pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    result = await db.execute(query)
    return result.scalars().all()
```

### Caching Strategy

```python
# Multi-level caching
async def get_analysis_results(analysis_id: str):
    """Get analysis results with multi-level caching"""
    # L1: Memory cache (short-term)
    if analysis_id in memory_cache:
        return memory_cache[analysis_id]
    
    # L2: Redis cache (medium-term)
    cached = await cache_service.get(f"analysis:{analysis_id}")
    if cached:
        memory_cache[analysis_id] = cached
        return cached
    
    # L3: Database (long-term)
    analysis = await db.get(Analysis, analysis_id)
    if analysis:
        # Cache in both levels
        await cache_service.set(f"analysis:{analysis_id}", analysis, ttl=3600)
        memory_cache[analysis_id] = analysis
    
    return analysis
```

## 🔒 Security Best Practices

### Input Validation

```python
# Pydantic models for validation
class ReviewCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    rating: int = Field(..., ge=1, le=5)
    product_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Great app, love the new features!",
                "rating": 5,
                "product_id": "test_app"
            }
        }
```

### Rate Limiting

```python
# Rate limiting middleware
class RateLimitMiddleware:
    def __init__(self, app, calls: int, period: int):
        self.app = app
        self.calls = calls
        self.period = period
        self.redis = Redis.from_url(REDIS_URL)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            client_ip = scope["client"][0]
            key = f"rate_limit:{client_ip}"
            
            current = await self.redis.get(key)
            if current and int(current) >= self.calls:
                response = Response(
                    content={"error": "Rate limit exceeded"},
                    status_code=429
                )
                await response(scope, receive, send)
                return
            
            await self.redis.incr(key)
            await self.redis.expire(key, self.period)
        
        await self.app(scope, receive, send)
```

## 📞 Support and Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL configuration
   - Verify database is running
   - Check connection pool settings

2. **Redis Connection Errors**
   - Verify Redis is running
   - Check REDIS_URL configuration
   - Validate password

3. **Phase Service Unavailable**
   - Check individual phase services
   - Verify network connectivity
   - Check service health endpoints

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Run with hot reload
uvicorn src.main:app --reload --log-level debug
```

### Health Check Endpoints

```bash
# Overall health
curl http://localhost:9000/health

# Database health
curl http://localhost:9000/health/database

# Phase services health
curl http://localhost:9000/health/phases

# Metrics
curl http://localhost:9000/metrics
```

The backend API gateway provides a robust, scalable foundation for the Review Pulse system with comprehensive security, monitoring, and performance optimization.
