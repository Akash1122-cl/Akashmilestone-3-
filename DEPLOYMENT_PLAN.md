# Backend and Frontend Deployment Plan with Basic UI

## 🎯 Overview

This deployment plan outlines the complete setup for the Review Pulse system with a modern React frontend and unified backend API gateway, including infrastructure, CI/CD, and monitoring.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │
│   (React SPA)   │◄──►│   (FastAPI)     │
│   Port: 3000    │    │   Port: 9000    │
└─────────────────┘    └─────────────────┘
         │                       │
         │ HTTPS/WSS             │ HTTP
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   API Gateway   │
│   (Reverse      │    │   (Orchestrates) │
│    Proxy)       │    │   All Phases)   │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │   Phase 1-5     │
│   (CDN)         │    │   Microservices │
└─────────────────┘    └─────────────────┘
```

## 📦 Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Query** for state management
- **Chart.js** for visualizations
- **Framer Motion** for animations

### Backend
- **FastAPI** with Python 3.11+
- **PostgreSQL** for primary database
- **Redis** for caching and sessions
- **Celery** for background tasks
- **Prometheus** for metrics
- **JWT** for authentication

### Infrastructure
- **Docker** for containerization
- **Kubernetes** for orchestration
- **Nginx** for reverse proxy
- **GitHub Actions** for CI/CD
- **AWS/GCP** for cloud hosting

## 🚀 Deployment Strategy

### Phase 1: Development Environment

#### Local Development Setup
```bash
# Frontend
cd frontend
npm install
npm run dev  # http://localhost:3000

# Backend
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload  # http://localhost:9000

# Phase Services
for phase in phase1 phase2 phase3 phase4 phase5; do
  cd $phase && python src/main.py &
done
```

#### Docker Compose Development
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:9000

  backend:
    build: ./backend
    ports:
      - "9000:9000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/review_pulse
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=review_pulse
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Phase 2: Staging Environment

#### Kubernetes Staging
```yaml
# k8s/staging/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: review-pulse-staging
---
# k8s/staging/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: review-pulse-config
  namespace: review-pulse-staging
data:
  ENVIRONMENT: "staging"
  DEBUG: "true"
  LOG_LEVEL: "INFO"
```

#### Frontend Deployment
```yaml
# k8s/staging/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: review-pulse-frontend
  namespace: review-pulse-staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: review-pulse-frontend
  template:
    metadata:
      labels:
        app: review-pulse-frontend
    spec:
      containers:
      - name: frontend
        image: reviewpulse/frontend:staging
        ports:
        - containerPort: 3000
        env:
        - name: VITE_API_URL
          value: "https://api-staging.reviewpulse.dev"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: review-pulse-frontend-svc
  namespace: review-pulse-staging
spec:
  selector:
    app: review-pulse-frontend
  ports:
  - port: 3000
    targetPort: 3000
```

#### Backend Deployment
```yaml
# k8s/staging/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: review-pulse-backend
  namespace: review-pulse-staging
spec:
  replicas: 3
  selector:
    matchLabels:
      app: review-pulse-backend
  template:
    metadata:
      labels:
        app: review-pulse-backend
    spec:
      containers:
      - name: backend
        image: reviewpulse/backend:staging
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
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
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
---
apiVersion: v1
kind: Service
metadata:
  name: review-pulse-backend-svc
  namespace: review-pulse-staging
spec:
  selector:
    app: review-pulse-backend
  ports:
  - port: 9000
    targetPort: 9000
```

### Phase 3: Production Environment

#### Production Infrastructure
```yaml
# k8s/production/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: review-pulse-prod
  labels:
    name: review-pulse-prod
---
# k8s/production/resource-quotas.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: review-pulse-quota
  namespace: review-pulse-prod
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    persistentvolumeclaims: "10"
    pods: "20"
    services: "10"
```

#### High Availability Setup
```yaml
# k8s/production/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: review-pulse-frontend-hpa
  namespace: review-pulse-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: review-pulse-frontend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: review-pulse-backend-hpa
  namespace: review-pulse-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: review-pulse-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔄 CI/CD Pipeline

### Frontend CI/CD
```yaml
# .github/workflows/frontend.yml
name: Frontend CI/CD

on:
  push:
    branches: [main, develop]
    paths: ['frontend/**']
  pull_request:
    branches: [main]
    paths: ['frontend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      working-directory: ./frontend
      run: npm ci
    
    - name: Run tests
      working-directory: ./frontend
      run: npm run test:coverage
    
    - name: Run E2E tests
      working-directory: ./frontend
      run: npm run test:e2e
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Build for production
      working-directory: ./frontend
      run: |
        npm ci
        npm run build
    
    - name: Build Docker image
      run: |
        docker build -t reviewpulse/frontend:${{ github.sha }} ./frontend
        docker tag reviewpulse/frontend:${{ github.sha }} reviewpulse/frontend:latest
    
    - name: Push to registry
      env:
        DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
        DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
      run: |
        echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
        docker push reviewpulse/frontend:${{ github.sha }}
        docker push reviewpulse/frontend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
    - uses: actions/checkout@v4
    - name: Deploy to staging
      run: |
        kubectl set image deployment/review-pulse-frontend \
          frontend=reviewpulse/frontend:${{ github.sha }} \
          -n review-pulse-staging
        kubectl rollout status deployment/review-pulse-frontend \
          -n review-pulse-staging
```

### Backend CI/CD
```yaml
# .github/workflows/backend.yml
name: Backend CI/CD

on:
  push:
    branches: [main, develop]
    paths: ['backend/**']
  pull_request:
    branches: [main]
    paths: ['backend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_review_pulse
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      working-directory: ./backend
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      working-directory: ./backend
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_review_pulse
        REDIS_URL: redis://localhost:6379
      run: pytest --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Run security scan
      uses: securecodewarrior/github-action-add-sarif@v1
      with:
        sarif-file: 'security-scan-results.sarif'
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v4
    - name: Build Docker image
      run: |
        docker build -t reviewpulse/backend:${{ github.sha }} ./backend
        docker tag reviewpulse/backend:${{ github.sha }} reviewpulse/backend:latest
    
    - name: Push to registry
      env:
        DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
        DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
      run: |
        echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
        docker push reviewpulse/backend:${{ github.sha }}
        docker push reviewpulse/backend:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
    - uses: actions/checkout@v4
    - name: Deploy to staging
      run: |
        kubectl set image deployment/review-pulse-backend \
          backend=reviewpulse/backend:${{ github.sha }} \
          -n review-pulse-staging
        kubectl rollout status deployment/review-pulse-backend \
          -n review-pulse-staging
```

## 🌐 Basic UI Components

### Dashboard Layout
```typescript
// frontend/src/components/layout/DashboardLayout.tsx
import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Footer } from './Footer';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="flex">
        <Sidebar />
        <div className="flex-1 flex flex-col">
          <Header />
          <main className="flex-1 overflow-auto">
            {children}
          </main>
          <Footer />
        </div>
      </div>
    </div>
  );
};
```

### Navigation Sidebar
```typescript
// frontend/src/components/layout/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  ChartBarIcon,
  DocumentTextIcon,
  CogIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: ChartBarIcon },
  { name: 'Reviews', href: '/reviews', icon: DocumentTextIcon },
  { name: 'Analysis', href: '/analysis', icon: ChartBarIcon },
  { name: 'Reports', href: '/reports', icon: DocumentTextIcon },
  { name: 'Stakeholders', href: '/stakeholders', icon: UserGroupIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
];

export const Sidebar: React.FC = () => {
  return (
    <div className="w-64 bg-white dark:bg-gray-800 shadow-md">
      <div className="p-6">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white">
          Review Pulse
        </h1>
      </div>
      <nav className="mt-6">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center px-6 py-3 text-sm font-medium ${
                isActive
                  ? 'bg-blue-50 border-r-4 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`
            }
          >
            <item.icon className="mr-3 h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>
    </div>
  );
};
```

### Metrics Dashboard
```typescript
// frontend/src/pages/Dashboard/Dashboard.tsx
import React from 'react';
import { MetricCard } from '@/components/ui/MetricCard';
import { ReviewsChart } from '@/components/charts/ReviewsChart';
import { SentimentChart } from '@/components/charts/SentimentChart';
import { RecentActivity } from '@/components/dashboard/RecentActivity';

export const Dashboard: React.FC = () => {
  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Overview of your review analytics and system performance
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <MetricCard
          title="Total Reviews"
          value="12,543"
          change="+12%"
          changeType="positive"
          icon="📊"
        />
        <MetricCard
          title="Active Products"
          value="8"
          change="+2"
          changeType="positive"
          icon="📱"
        />
        <MetricCard
          title="Avg. Sentiment"
          value="4.2"
          change="+0.3"
          changeType="positive"
          icon="😊"
        />
        <MetricCard
          title="Reports Generated"
          value="47"
          change="+8"
          changeType="positive"
          icon="📄"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ReviewsChart />
        <SentimentChart />
      </div>

      {/* Recent Activity */}
      <RecentActivity />
    </div>
  );
};
```

## 🔧 Configuration Files

### Environment Configuration
```bash
# frontend/.env.production
VITE_API_URL=https://api.reviewpulse.dev
VITE_WS_URL=wss://api.reviewpulse.dev/ws
VITE_SENTRY_DSN=your_sentry_dsn
VITE_ENABLE_ANALYTICS=true

# backend/.env.production
DATABASE_URL=postgresql://user:password@prod-db:5432/review_pulse
REDIS_URL=redis://prod-redis:6379
SECRET_KEY=your_super_secret_key
PHASE1_URL=http://phase1-service:8000
PHASE2_URL=http://phase2-service:8001
PHASE3_URL=http://phase3-service:8002
PHASE4_URL=http://phase4-service:8003
PHASE5_URL=http://phase5-service:8005
```

### Nginx Configuration
```nginx
# nginx.conf
upstream frontend {
    server review-pulse-frontend-svc:3000;
}

upstream backend {
    server review-pulse-backend-svc:9000;
}

server {
    listen 80;
    server_name reviewpulse.dev;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 📊 Monitoring and Observability

### Prometheus Metrics
```python
# backend/src/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration')

# Business metrics
REVIEWS_PROCESSED = Counter('reviews_processed_total', 'Total reviews processed')
ANALYSIS_COMPLETED = Counter('analysis_completed_total', 'Total analysis completed')
REPORTS_GENERATED = Counter('reports_generated_total', 'Total reports generated')

# System metrics
ACTIVE_USERS = Gauge('active_users_total', 'Total active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "Review Pulse Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Business Metrics",
        "type": "stat",
        "targets": [
          {
            "expr": "reviews_processed_total",
            "legendFormat": "Reviews Processed"
          }
        ]
      }
    ]
  }
}
```

## 🔒 Security Configuration

### Authentication Setup
```python
# backend/src/auth/jwt_handler.py
from datetime import datetime, timedelta
from jose import JWTError, jwt

class JWTHandler:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
```

### CORS Configuration
```python
# backend/src/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://reviewpulse.dev", "https://staging.reviewpulse.dev"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## 🚀 Deployment Steps

### 1. Prepare Infrastructure
```bash
# Create namespaces
kubectl create namespace review-pulse-staging
kubectl create namespace review-pulse-prod

# Create secrets
kubectl create secret generic review-pulse-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=redis-url="redis://..." \
  --from-literal=jwt-secret="your-secret-key" \
  -n review-pulse-staging
```

### 2. Deploy Databases
```bash
# Deploy PostgreSQL
kubectl apply -f k8s/staging/postgres.yaml -n review-pulse-staging

# Deploy Redis
kubectl apply -f k8s/staging/redis.yaml -n review-pulse-staging

# Wait for readiness
kubectl wait --for=condition=ready pod -l app=postgres -n review-pulse-staging --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n review-pulse-staging --timeout=300s
```

### 3. Deploy Phase Services
```bash
# Deploy all phase microservices
for phase in phase1 phase2 phase3 phase4 phase5; do
  kubectl apply -f k8s/staging/${phase}.yaml -n review-pulse-staging
  kubectl wait --for=condition=ready pod -l app=${phase} -n review-pulse-staging --timeout=300s
done
```

### 4. Deploy Backend API Gateway
```bash
# Deploy backend
kubectl apply -f k8s/staging/backend.yaml -n review-pulse-staging
kubectl wait --for=condition=ready pod -l app=review-pulse-backend -n review-pulse-staging --timeout=300s
```

### 5. Deploy Frontend
```bash
# Deploy frontend
kubectl apply -f k8s/staging/frontend.yaml -n review-pulse-staging
kubectl wait --for=condition=ready pod -l app=review-pulse-frontend -n review-pulse-staging --timeout=300s
```

### 6. Configure Ingress
```bash
# Deploy ingress
kubectl apply -f k8s/staging/ingress.yaml -n review-pulse-staging

# Get ingress IP
kubectl get ingress -n review-pulse-staging
```

### 7. Verify Deployment
```bash
# Check all pods
kubectl get pods -n review-pulse-staging

# Check services
kubectl get svc -n review-pulse-staging

# Test endpoints
curl https://staging.reviewpulse.dev/health
curl https://staging.reviewpulse.dev/api/v1/dashboard/metrics
```

## 📈 Performance Optimization

### Frontend Optimization
```typescript
// Code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Reviews = lazy(() => import('./pages/Reviews'));

// Bundle optimization
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['chart.js', 'd3'],
          ui: ['@headlessui/react', 'framer-motion']
        }
      }
    }
  }
});
```

### Backend Optimization
```python
# Connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30

# Caching
CACHE_TTL = {
    'dashboard_metrics': 60,  # 1 minute
    'reviews': 300,          # 5 minutes
    'analysis_results': 3600  # 1 hour
}

# Async processing
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)
```

## 🔧 Maintenance

### Health Checks
```bash
# System health
curl https://reviewpulse.dev/health/detailed

# Individual services
kubectl get pods -n review-pulse-prod
kubectl top pods -n review-pulse-prod
```

### Backup Procedures
```bash
# Database backup
kubectl exec -it postgres-prod-0 -- pg_dump review_pulse > backup-$(date +%Y%m%d).sql

# Redis backup
kubectl exec -it redis-prod-0 -- redis-cli BGSAVE
```

### Log Management
```bash
# View logs
kubectl logs -f deployment/review-pulse-frontend -n review-pulse-prod
kubectl logs -f deployment/review-pulse-backend -n review-pulse-prod

# Aggregate logs
kubectl logs -l app=review-pulse -n review-pulse-prod --since=1h
```

This deployment plan provides a comprehensive setup for the Review Pulse system with a modern React frontend and unified backend, complete with CI/CD, monitoring, and production-ready infrastructure.
