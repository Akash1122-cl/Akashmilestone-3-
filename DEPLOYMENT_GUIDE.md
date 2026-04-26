# GitHub Deployment Guide for Review Pulse

This guide walks you through deploying the Review Pulse system to GitHub with CI/CD, monitoring, and production-ready infrastructure.

## 🚀 Quick Start

### 1. Run the Setup Script

```bash
# Clone your repository
git clone https://github.com/yourusername/review-pulse.git
cd review-pulse

# Run the automated setup
chmod +x scripts/setup-github.sh
./scripts/setup-github.sh review-pulse yourusername
```

This script will:
- ✅ Create GitHub repository
- ✅ Set up CI/CD workflows  
- ✅ Configure branch protection
- ✅ Create setup issues
- ✅ Set up labels and project boards

### 2. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions and add:

#### Required Secrets
```bash
# Database
DB_PASSWORD=your_secure_postgres_password
REDIS_PASSWORD=your_secure_redis_password

# Docker Registry
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_access_token

# Google APIs (Phase 5)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
DEFAULT_SENDER_EMAIL=your_gmail_address
OAUTH_STATE_SECRET=openssl rand -base64 32
JWT_SECRET=openssl rand -base64 32

# Monitoring
GRAFANA_PASSWORD=your_grafana_password

# Notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url

# Kubernetes (production)
KUBE_CONFIG_STAGING=your_staging_kubeconfig
KUBE_CONFIG_PRODUCTION=your_production_kubeconfig
```

## 🏗️ Deployment Options

### Option 1: Local Development

```bash
# Using Docker Compose (easiest)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 2: Staging Deployment

```bash
# Deploy to staging
./scripts/deploy.sh staging latest

# Check deployment
kubectl get pods -n review-pulse-staging
```

### Option 3: Production Deployment

```bash
# Deploy to production (requires approval)
./scripts/deploy.sh production v1.0.0

# Or use GitHub Actions (automatic on tags)
git tag v1.0.0
git push origin v1.0.0
```

## 🔄 CI/CD Pipeline

### Continuous Integration (on every push)

1. **Tests**: Run all 203 tests across 5 phases
2. **Security**: Trivy vulnerability scanning
3. **Quality**: Code formatting and linting
4. **Coverage**: Generate coverage reports

### Continuous Deployment (on main branch)

1. **Build**: Create Docker image with multi-platform support
2. **Push**: Upload to Docker Hub
3. **Deploy**: Deploy to staging environment
4. **Verify**: Run smoke tests and health checks

### Production Deployment (on tags)

1. **Backup**: Create database backup
2. **Deploy**: Zero-downtime deployment
3. **Verify**: Comprehensive testing
4. **Monitor**: Set up alerts and dashboards

## 📊 Monitoring and Observability

### Prometheus Metrics

Access at: `http://your-domain.com:9090`

Key metrics:
- API response times by phase
- Error rates and status codes
- Database connection pool usage
- Redis memory usage
- Queue lengths and processing times

### Grafana Dashboards

Access at: `http://your-domain.com:3000`

Default dashboards:
- **System Overview**: CPU, memory, disk usage
- **API Performance**: Response times, error rates
- **Business Metrics**: Reviews processed, reports generated
- **Delivery Tracking**: Email success rates, stakeholder engagement

### Alerting Rules

Critical alerts:
- Service downtime (>5 minutes)
- High error rates (>5%)
- Database connection failures
- Disk space (>80% used)

Warning alerts:
- High response times (>2 seconds)
- Memory usage (>80%)
- Queue backlog (>1000 items)

## 🔒 Security Configuration

### Network Security

```yaml
# Kubernetes Network Policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: review-pulse-netpol
spec:
  podSelector:
    matchLabels:
      app: review-pulse-production
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  - from:
    - podSelector:
        matchLabels:
          app: review-pulse-production
    ports:
    - protocol: TCP
      port: 5432
```

### Secrets Management

```bash
# Encrypt secrets at rest
kubectl create secret generic review-pulse-secrets \
  --from-literal=db-password=$DB_PASSWORD \
  --from-literal=redis-password=$REDIS_PASSWORD \
  --dry-run=client -o yaml | kubectl apply -f -

# Rotate secrets regularly
./scripts/rotate-secrets.sh
```

### RBAC Configuration

```yaml
# Service account with minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: review-pulse-sa
  namespace: review-pulse
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: review-pulse-role
  namespace: review-pulse
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
```

## 🚦 Environment Management

### Development Environment

```bash
# Local development with hot reload
docker-compose -f docker-compose.dev.yml up
```

Features:
- Hot code reloading
- Debug endpoints enabled
- Verbose logging
- Mock external services

### Staging Environment

```bash
# Production-like environment
kubectl apply -f k8s/staging/
```

Features:
- Production configuration
- Reduced resources
- Staging database
- Public access

### Production Environment

```bash
# Full production deployment
kubectl apply -f k8s/production/
```

Features:
- High availability
- Auto-scaling
- Full monitoring
- Backup and recovery

## 📈 Performance Optimization

### Horizontal Scaling

```yaml
# HPA Configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: review-pulse-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: review-pulse-production
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Database Optimization

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
SELECT pg_reload_conf();
```

### Caching Strategy

```python
# Redis caching configuration
CACHE_CONFIG = {
    'default_timeout': 300,  # 5 minutes
    'embeddings_timeout': 3600,  # 1 hour
    'reports_timeout': 1800,  # 30 minutes
    'max_connections': 100
}
```

## 🔄 Backup and Recovery

### Database Backups

```bash
# Automated daily backups
kubectl create cronjob database-backup \
  --schedule="0 2 * * *" \
  --image=postgres:14 \
  -- ./scripts/backup-database.sh
```

### Disaster Recovery

1. **RTO**: 30 minutes (Recovery Time Objective)
2. **RPO**: 1 hour (Recovery Point Objective)
3. **Backup Retention**: 30 days
4. **Cross-region Replication**: Enabled

### Recovery Procedures

```bash
# Restore from backup
./scripts/restore-database.sh backup-2024-01-15.sql

# Failover to backup region
kubectl apply -f k8s/disaster-recovery/
```

## 🧪 Testing Strategy

### Unit Tests

```bash
# Run all phase tests
for phase in phase1 phase2 phase3 phase4 phase5; do
  cd $phase && python -m pytest tests/ -v --cov=src
done
```

### Integration Tests

```bash
# End-to-end testing
python -m pytest tests/integration/ -v --timeout=300
```

### Performance Tests

```bash
# Load testing
k6 run tests/performance/load-test.js

# Stress testing
k6 run tests/performance/stress-test.js
```

### Smoke Tests

```bash
# Production smoke tests
./scripts/smoke-tests.sh production
```

## 📋 Troubleshooting

### Common Issues

#### 1. Pod Crashing
```bash
# Check pod logs
kubectl logs -f deployment/review-pulse-production -n review-pulse

# Check events
kubectl describe pod <pod-name> -n review-pulse
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it deployment/postgres-production -- psql -U postgres -d review_pulse

# Check connection pool
kubectl exec -it deployment/review-pulse-production -- env | grep DB
```

#### 3. High Memory Usage
```bash
# Check resource usage
kubectl top pods -n review-pulse

# Scale up resources
kubectl patch deployment review-pulse-production -p '{"spec":{"template":{"spec":{"containers":[{"name":"app","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

#### 4. Slow API Response
```bash
# Check metrics
curl http://prometheus.yourdomain.com/api/v1/query?query=rate(http_request_duration_seconds_sum[5m])

# Check database queries
kubectl exec -it deployment/postgres-production -- psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### Emergency Procedures

#### Service Outage
1. Check status: `kubectl get pods -n review-pulse`
2. Restart services: `kubectl rollout restart deployment/review-pulse-production`
3. Scale up: `kubectl scale deployment review-pulse-production --replicas=5`
4. Monitor: `kubectl logs -f deployment/review-pulse-production`

#### Database Issues
1. Check connection: `kubectl exec -it postgres-production -- pg_isready`
2. Restart database: `kubectl rollout restart deployment/postgres-production`
3. Restore backup: `./scripts/emergency-restore.sh`

#### Security Incident
1. Isolate: `kubectl scale deployment review-pulse-production --replicas=0`
2. Investigate: Check logs and audit trails
3. Patch: Update affected components
4. Restore: Gradual rollout with monitoring

## 📚 Documentation

### API Documentation
- Swagger UI: `https://your-domain.com/docs`
- OpenAPI spec: `https://your-domain.com/openapi.json`

### Operational Documentation
- Runbooks: `docs/runbooks/`
- Architecture: `docs/architecture.md`
- Incident response: `docs/incident-response.md`

### Development Documentation
- Contributing guide: `CONTRIBUTING.md`
- Code style: `docs/style-guide.md`
- Testing guide: `docs/testing.md`

## 🔄 Maintenance Tasks

### Daily
- Monitor system health
- Check backup completion
- Review error logs
- Update security patches

### Weekly
- Review performance metrics
- Clean up old logs
- Update dependencies
- Test disaster recovery

### Monthly
- Security audit
- Capacity planning
- Cost optimization
- Documentation updates

### Quarterly
- Architecture review
- Performance tuning
- Security assessment
- Disaster recovery drill

## 📞 Support

### Get Help
- **Documentation**: [GitHub Wiki](https://github.com/yourusername/review-pulse/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/review-pulse/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/review-pulse/discussions)
- **Support**: support@reviewpulse.dev

### Escalation
1. **Level 1**: Check documentation and known issues
2. **Level 2**: Create GitHub issue with details
3. **Level 3**: Contact support team
4. **Emergency**: Use emergency contact procedures

---

## 🎯 Success Metrics

### Technical Metrics
- **Uptime**: >99.5%
- **Response Time**: <500ms (p95)
- **Error Rate**: <1%
- **Deployment Success**: >95%

### Business Metrics
- **Reviews Processed**: >10,000/week
- **Reports Generated**: >100/week
- **Stakeholder Engagement**: >80%
- **Customer Satisfaction**: >4.5/5

Your Review Pulse system is now ready for production deployment on GitHub! 🚀
