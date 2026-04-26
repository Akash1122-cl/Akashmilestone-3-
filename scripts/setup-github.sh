#!/bin/bash

# GitHub Repository Setup Script for Review Pulse
# Usage: ./scripts/setup-github.sh [repo-name]

set -e

REPO_NAME=${1:-review-pulse}
GITHUB_USER=${2:-$(git config user.name)}

echo "🔧 Setting up GitHub repository: $GITHUB_USER/$REPO_NAME"

# Check prerequisites
command -v gh >/dev/null 2>&1 || { echo "❌ GitHub CLI (gh) is required but not installed." >&2; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ git is required but not installed." >&2; exit 1; }

# Initialize git repository if not already done
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Review Pulse multi-phase system"
fi

# Create GitHub repository
echo "🌐 Creating GitHub repository..."
gh repo create $GITHUB_USER/$REPO_NAME \
    --public \
    --description "Weekly Product Review Analysis System - Multi-phase automated review collection, analysis, clustering, and report generation with MCP-based delivery" \
    --source=. \
    --push \
    --homepage="https://github.com/$GITHUB_USER/$REPO_NAME"

# Set up GitHub secrets
echo "🔐 Setting up GitHub secrets..."

# Function to set secret if not exists
set_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    echo "Setting secret: $secret_name"
    echo "$secret_value" | gh secret set $secret_name --body - || echo "Secret $secret_name already exists"
}

# Database secrets
set_secret "DB_PASSWORD" "$(openssl rand -base64 32)" "PostgreSQL database password"
set_secret "REDIS_PASSWORD" "$(openssl rand -base64 32)" "Redis password"

# Google API secrets (user needs to set these manually)
echo "⚠️  Please set these secrets manually in GitHub repository settings:"
echo "   - GOOGLE_CLIENT_ID (from Google Cloud Console)"
echo "   - GOOGLE_CLIENT_SECRET (from Google Cloud Console)"
echo "   - DEFAULT_SENDER_EMAIL (Gmail address for sending reports)"
echo "   - OAUTH_STATE_SECRET (generate with: openssl rand -base64 32)"
echo "   - JWT_SECRET (generate with: openssl rand -base64 32)"

# Docker registry secrets
set_secret "DOCKER_USERNAME" "$(gh api user --jq '.login')" "Docker Hub username"
echo "⚠️  Set DOCKER_PASSWORD secret with your Docker Hub access token"

# Kubernetes secrets
echo "⚠️  Set KUBE_CONFIG_STAGING and KUBE_CONFIG_PRODUCTION secrets with your kubeconfig files"

# Monitoring secrets
set_secret "GRAFANA_PASSWORD" "$(openssl rand -base64 16)" "Grafana admin password"

# Notification secrets
echo "⚠️  Set SLACK_WEBHOOK_URL secret for deployment notifications"

# Create GitHub issues for setup tasks
echo "📋 Creating setup issues..."

# Issue 1: Google API Setup
gh issue create \
    --title "Setup Google APIs for Phase 5" \
    --body "## Google Cloud Setup Required

Phase 5 requires Google Workspace APIs for MCP integration:

### Required Tasks:
1. [ ] Create Google Cloud Project: `review-pulse-mcp`
2. [ ] Enable APIs:
   - Google Docs API
   - Gmail API  
   - Google Drive API
   - OAuth 2.0 API
3. [ ] Configure OAuth 2.0 Consent Screen
4. [ ] Create OAuth 2.0 Client ID (Web Application)
5. [ ] Add required scopes to OAuth consent screen
6. [ ] Download credentials.json
7. [ ] Set GitHub secrets:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `DEFAULT_SENDER_EMAIL`
   - `OAUTH_STATE_SECRET`

### References:
- [Google API Setup Guide](phase5/GOOGLE_API_SETUP.md)
- [Phase 5 Documentation](phase5/README.md)

### Notes:
- Use external user type for production
- Add redirect URI: `https://yourdomain.com/oauth/callback`
- Keep credentials.json secure (never commit)" \
    --label "setup,phase5,google-api"

# Issue 2: Production Deployment
gh issue create \
    --title "Setup Production Infrastructure" \
    --body "## Production Deployment Setup

### Required Infrastructure:
1. [ ] Kubernetes cluster (GKE/EKS/AKS)
2. [ ] PostgreSQL database
3. [ ] Redis cluster
4. [ ] Persistent storage
5. [ ] SSL certificates
6. [ ] Domain configuration

### DNS Records:
```
reviewpulse.yourdomain.com -> Load Balancer IP
grafana.yourdomain.com -> Load Balancer IP
prometheus.yourdomain.com -> Load Balancer IP
```

### Kubernetes Setup:
1. [ ] Install cert-manager for SSL
2. [ ] Configure nginx-ingress
3. [ ] Set up monitoring stack
4. [ ] Configure backup strategies

### Security:
1. [ ] Set up network policies
2. [ ] Configure RBAC
3. [ ] Enable audit logging
4. [ ] Set up secret management

### References:
- [Kubernetes manifests](k8s/)
- [Deployment script](scripts/deploy.sh)" \
    --label "setup,production,kubernetes"

# Issue 3: Monitoring and Alerting
gh issue create \
    --title "Configure Monitoring and Alerting" \
    --body "## Monitoring Setup Required

### Prometheus Configuration:
1. [ ] Configure service discovery
2. [ ] Set up alerting rules
3. [ ] Configure retention policies
4. [ ] Set up remote storage (optional)

### Grafana Dashboards:
1. [ ] Import dashboard templates
2. [ ] Configure data sources
3. [ ] Set up user authentication
4. [ ] Configure alert channels

### Alert Channels:
1. [ ] Slack notifications
2. [ ] Email alerts
3. [ ] PagerDuty integration (optional)

### Key Metrics to Monitor:
- API response times
- Error rates by phase
- Database performance
- Memory/CPU usage
- Queue lengths
- Delivery success rates

### References:
- [Monitoring configuration](monitoring/)
- [Alerting rules](monitoring/alerts/)" \
    --label "setup,monitoring,alerting"

# Create GitHub releases workflow
echo "🔄 Setting up release workflow..."
mkdir -p .github/workflows

# Create release template
cat > .github/RELEASE_TEMPLATE.md << 'EOF'
## Release Notes

### 🚀 New Features
- 

### 🐛 Bug Fixes
- 

### 🔧 Improvements
- 

### 📊 Performance
- 

### 🔒 Security
- 

### ⚠️ Breaking Changes
- 

### 📝 Documentation
- 

### 🧪 Testing
- 

### 📦 Dependencies
- 

### 🚀 Deployment
- 

## Installation
```bash
docker pull reviewpulse/review-pulse:vX.Y.Z
# Or use the deployment script
./scripts/deploy.sh production vX.Y.Z
```

## Verification
- [ ] All health checks pass
- [ ] Smoke tests pass
- [ ] Performance benchmarks met
- [ ] Security scans pass
EOF

# Enable GitHub Pages for documentation
echo "📚 Setting up GitHub Pages..."
gh api repos/:owner/:repo/pages -X POST -f source.branch=main -f source.path=/docs || echo "Pages already enabled"

# Create project boards
echo "📋 Creating project boards..."

# Kanban board for development
gh project create "Review Pulse Development" --format kanban || echo "Project already exists"

# Set up branch protection
echo "🔒 Setting up branch protection..."
gh api repos/:owner/:repo/branches/main/protection -X PUT \
  -f required_status_checks='{"strict":true,"contexts":["ci"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"required_approving_review_count":1}' \
  -f restrictions=null || echo "Branch protection already configured"

# Set up labels
echo "🏷️ Setting up labels..."
labels=(
    "bug:Bug reports and issues"
    "enhancement:Feature requests"
    "documentation:Documentation improvements"
    "setup:Setup and configuration"
    "deployment:Deployment related"
    "performance:Performance issues"
    "security:Security related"
    "phase1:Phase 1 - Data Ingestion"
    "phase2:Phase 2 - Data Processing"
    "phase3:Phase 3 - Analysis"
    "phase4:Phase 4 - Report Generation"
    "phase5:Phase 5 - MCP Integration"
    "phase6:Phase 6 - Production"
    "good first issue:Good for newcomers"
    "help wanted:Community help needed"
)

for label in "${labels[@]}"; do
    IFS=':' read -r name description <<< "$label"
    gh label create "$name" --color "0366d6" --description "$description" 2>/dev/null || echo "Label $name already exists"
done

# Create initial commit and push
echo "📤 Pushing to GitHub..."
git add .
git commit -m "feat: Add GitHub deployment configuration

- Add CI/CD workflows for testing and deployment
- Add Docker Compose configuration
- Add Kubernetes manifests for production
- Add deployment scripts
- Add comprehensive README
- Set up GitHub issues for setup tasks
- Configure branch protection and labels

This commit includes all infrastructure and deployment
configuration for the Review Pulse system." || echo "Already committed"

git push origin main

echo "✅ GitHub repository setup completed!"
echo ""
echo "🌐 Repository: https://github.com/$GITHUB_USER/$REPO_NAME"
echo "📋 Issues created:"
echo "   - Setup Google APIs for Phase 5"
echo "   - Setup Production Infrastructure"  
echo "   - Configure Monitoring and Alerting"
echo ""
echo "🔐 Next steps:"
echo "   1. Set the GitHub secrets listed above"
echo "   2. Complete the setup issues"
echo "   3. Test CI/CD pipeline"
echo "   4. Deploy to staging environment"
echo ""
echo "📖 Documentation: https://github.com/$GITHUB_USER/$REPO_NAME#readme"
