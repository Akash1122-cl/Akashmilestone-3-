#!/bin/bash

# Review Pulse Deployment Script
# Usage: ./scripts/deploy.sh [environment] [tag]

set -e

# Default values
ENVIRONMENT=${1:-staging}
TAG=${2:-latest}
PROJECT_NAME="review-pulse"
DOCKER_REGISTRY="reviewpulse"

echo "🚀 Deploying Review Pulse to $ENVIRONMENT with tag $TAG"

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl is required but not installed." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ docker is required but not installed." >&2; exit 1; }

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $DOCKER_REGISTRY/$PROJECT_NAME:$TAG .
docker push $DOCKER_REGISTRY/$PROJECT_NAME:$TAG

# Set namespace
NAMESPACE="review-pulse"
if [ "$ENVIRONMENT" = "production" ]; then
    NAMESPACE="review-pulse-prod"
fi

echo "🔧 Using namespace: $NAMESPACE"

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets
echo "🔐 Applying secrets..."
kubectl apply -f k8s/$ENVIRONMENT/secrets.yaml -n $NAMESPACE

# Apply configmaps
echo "📝 Applying configmaps..."
kubectl apply -f k8s/$ENVIRONMENT/configmaps.yaml -n $NAMESPACE

# Apply database migrations
echo "🗄️ Applying database migrations..."
kubectl apply -f k8s/$ENVIRONMENT/postgres.yaml -n $NAMESPACE

# Apply Redis
echo "💾 Applying Redis..."
kubectl apply -f k8s/$ENVIRONMENT/redis.yaml -n $NAMESPACE

# Apply main deployment
echo "🚀 Deploying application..."
sed "s|image: $DOCKER_REGISTRY/$PROJECT_NAME:.*|image: $DOCKER_REGISTRY/$PROJECT_NAME:$TAG|g" k8s/$ENVIRONMENT/deployment.yaml | kubectl apply -f - -n $NAMESPACE

# Apply services
echo "🌐 Applying services..."
kubectl apply -f k8s/$ENVIRONMENT/services.yaml -n $NAMESPACE

# Apply ingress
echo "🌍 Applying ingress..."
kubectl apply -f k8s/$ENVIRONMENT/ingress.yaml -n $NAMESPACE

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/review-pulse-$ENVIRONMENT -n $NAMESPACE --timeout=600s

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -l app=review-pulse-$ENVIRONMENT -n $NAMESPACE

# Get service URLs
echo "🌐 Service URLs:"
kubectl get ingress -n $NAMESPACE

# Run health checks
echo "🏥 Running health checks..."
for port in 8000 8001 8002 8003 8005; do
    echo "Checking port $port..."
    kubectl port-forward svc/review-pulse-$ENVIRONMENT $port:$port -n $NAMESPACE &
    PF_PID=$!
    sleep 5
    
    if curl -f http://localhost:$port/health >/dev/null 2>&1; then
        echo "✅ Port $port healthy"
    else
        echo "❌ Port $port unhealthy"
    fi
    
    kill $PF_PID 2>/dev/null || true
done

echo "🎉 Deployment completed successfully!"
echo "📊 Monitoring: https://grafana.yourdomain.com"
echo "📈 Metrics: https://prometheus.yourdomain.com"

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🔔 Production deployment detected - sending notifications..."
    # Add notification logic here
fi
