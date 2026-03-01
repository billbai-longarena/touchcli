# TouchCLI CI/CD Deployment Guide

## Overview

TouchCLI uses GitHub Actions for continuous integration and deployment. The deployment pipeline automates building Docker images, pushing to Docker Hub, and deploying to Kubernetes.

## Architecture

### Deployment Pipeline

```
┌─────────────────────┐
│  Git Push (main)    │
│   or Workflow       │
│   Dispatch          │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Build and Test                  │
│  - Frontend: npm build & test    │
│  - Backend: linting & type check │
│  - Go: compile gateway           │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Build and Push Docker Images    │
│  - touchcli-frontend             │
│  - touchcli-backend              │
│  - touchcli-gateway              │
│  (to Docker Hub)                 │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Deploy to Kubernetes            │
│  - Create sealed secrets         │
│  - Deploy backend, gateway       │
│  - Deploy frontend               │
│  - Wait for rollout              │
│  - Health checks                 │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Notifications                   │
│  - Slack webhook                 │
│  - GitHub issues (on failure)    │
└──────────────────────────────────┘
```

## Prerequisites

### Required Secrets

Configure these secrets in GitHub repository settings:

```
DOCKER_USERNAME          - Docker Hub username
DOCKER_PASSWORD          - Docker Hub personal access token
KUBE_CONFIG              - Base64-encoded kubeconfig file
SLACK_WEBHOOK_URL        - Slack webhook for notifications (optional)
```

### Required Services

- **GitHub Account**: For Actions CI/CD
- **Docker Hub Account**: For image registry
- **Kubernetes Cluster**: For deployment target
- **Slack Workspace** (Optional): For notifications

## Setting Up Secrets

### 1. Docker Hub

Create Personal Access Token:
1. Log in to Docker Hub
2. Go to Account Settings → Security
3. Create New Access Token
4. Copy the token

Add to GitHub:
```bash
# In GitHub repository settings → Secrets and variables → Actions
DOCKER_USERNAME=<your-docker-username>
DOCKER_PASSWORD=<paste-access-token>
```

### 2. Kubernetes Config

Export kubeconfig:
```bash
# Get current kubeconfig
cat $HOME/.kube/config | base64

# Or if using cloud provider
gke: gcloud container clusters get-credentials CLUSTER_NAME --zone ZONE
eks: aws eks update-kubeconfig --name CLUSTER_NAME
```

Add to GitHub:
```bash
KUBE_CONFIG=<base64-encoded-kubeconfig>
```

### 3. Slack Webhook (Optional)

Create Incoming Webhook:
1. Go to Slack App Directory
2. Create new Incoming Webhook
3. Select channel (e.g., #deployments)
4. Copy webhook URL

Add to GitHub:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Deployment Methods

### Method 1: Automatic (Main Branch Push)

```bash
# Push to main branch triggers deployment
git checkout main
git merge develop
git push origin main
```

The workflow automatically:
1. Builds and tests code
2. Builds Docker images
3. Pushes to Docker Hub
4. Deploys to staging environment
5. Sends Slack notification

### Method 2: Manual Workflow Dispatch

In GitHub UI:
1. Go to Actions → Deploy to Production
2. Click "Run workflow"
3. Select environment (staging/production)
4. Click "Run workflow"

Or via CLI:
```bash
# Requires GitHub CLI: https://cli.github.com
gh workflow run deploy.yml \
  -f environment=production \
  -r main
```

### Method 3: Git Tags for Production

```bash
# Tag a commit for production release
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# Automatically deploys to production
```

## Workflow Steps Explained

### Build and Test

**Frontend**:
- Install dependencies
- Build with Vite
- Run unit tests (Vitest)
- Run E2E tests (Playwright)

**Backend**:
- Install Python dependencies
- Lint with flake8
- Type check with mypy
- Prepare migrations

**Gateway**:
- Compile Go binary

### Build and Push Docker

For each service (frontend, backend, gateway):

1. **Extract Metadata**
   - Image name: `docker.io/username/touchcli-SERVICE`
   - Tags: branch, semver, SHA, latest

2. **Build and Push**
   - Multi-platform builds (linux/amd64, linux/arm64)
   - Layer caching for fast builds
   - Push to Docker Hub

3. **Image Tagging**
   ```
   v1.0.0          # Semantic version
   main-abc123def  # Branch + commit SHA
   latest          # Latest from main
   ```

### Deploy to Kubernetes

1. **Setup**
   - Configure kubectl
   - Verify cluster connection

2. **Secrets**
   - Deploy Sealed Secrets controller
   - Apply encrypted secrets
   - Wait for decryption

3. **Application**
   - Update image tags in manifests
   - Deploy backend, gateway, frontend
   - Wait for rollout (maxSurge/maxUnavailable)

4. **Verification**
   - Check pod status
   - Verify endpoints
   - Health check endpoints
   - Rollout status

### Notifications

**On Success**:
- Slack message with deployment details
- Links to Docker images
- Deployment timestamp

**On Failure**:
- Slack message with failure status
- Creates GitHub issue with details
- Links to failed workflow run

## Environment Variables

Populated from ConfigMap:

```yaml
LOG_LEVEL=INFO
NODE_ENV=production
AGENT_SERVICE_URL=http://agent-service:8000
GATEWAY_PORT=8080
CORS_ALLOWED_ORIGINS=https://example.com,https://app.example.com
RATE_LIMIT_ENABLED=true
```

## Database Migrations

The backend deployment automatically runs migrations:

```bash
# In backend initContainer
alembic upgrade head
```

If migrations fail:
1. Deployment pauses
2. Manual intervention required
3. Check migration logs:
   ```bash
   kubectl logs -n touchcli pod/agent-service-xxx -c migrate
   ```

## Health Checks

### Liveness Probe

Checks if container is alive:

```yaml
httpGet:
  path: /health
  port: 8000
initialDelaySeconds: 15
periodSeconds: 30
failureThreshold: 3
```

If fails 3 times (90 seconds), pod is restarted.

### Readiness Probe

Checks if container is ready for traffic:

```yaml
httpGet:
  path: /health
  port: 8000
initialDelaySeconds: 10
periodSeconds: 10
failureThreshold: 3
```

If fails, pod is removed from load balancer.

## Rollback Procedure

### Automatic Rollback (Readiness Failure)

If deployment fails health checks:
```bash
# Kubernetes automatically rolls back
kubectl rollout undo deployment/agent-service -n touchcli
```

### Manual Rollback

```bash
# View deployment history
kubectl rollout history deployment/agent-service -n touchcli

# Rollback to previous version
kubectl rollout undo deployment/agent-service -n touchcli

# Rollback to specific revision
kubectl rollout undo deployment/agent-service -n touchcli --to-revision=5

# Check rollout status
kubectl rollout status deployment/agent-service -n touchcli
```

## Troubleshooting

### Build Failures

**Docker build fails**:
```bash
# Check Docker buildx logs
docker buildx build -f frontend/Dockerfile --progress=plain .

# Check base image availability
docker pull node:18-alpine
```

**Backend tests fail**:
```bash
cd backend/python
pip install -r requirements.txt
pytest tests/
```

### Deployment Failures

**Cannot connect to cluster**:
```bash
# Verify kubeconfig
kubectl cluster-info

# Check authentication
kubectl auth can-i create deployments --namespace touchcli
```

**Image pull errors**:
```bash
# Check Docker Hub credentials
kubectl get secret regcred -n touchcli

# Verify image exists
docker pull docker.io/username/touchcli-backend:latest
```

**Pod not ready**:
```bash
# Check pod events
kubectl describe pod POD_NAME -n touchcli

# Check logs
kubectl logs POD_NAME -n touchcli

# Check readiness probe
kubectl get pod POD_NAME -n touchcli -o jsonpath='{.status.conditions[?(@.type=="Ready")]}'
```

### Secrets Issues

**Secret not decrypted**:
```bash
# Check Sealed Secrets controller
kubectl get pods -n sealed-secrets

# Verify secret
kubectl get sealedsecret touchcli-secrets -n touchcli

# Check controller logs
kubectl logs -n sealed-secrets -l app.kubernetes.io/name=sealed-secrets
```

## Monitoring Deployments

### Live Monitoring

```bash
# Watch deployment status
kubectl rollout status deployment/agent-service -n touchcli -w

# Watch pod events
kubectl get events -n touchcli --sort-by='.lastTimestamp'

# Stream logs
kubectl logs -f deployment/agent-service -n touchcli
```

### Post-Deployment Checks

```bash
# Verify all pods running
kubectl get pods -n touchcli

# Check service endpoints
kubectl get endpoints -n touchcli

# Test internal DNS
kubectl run -it --rm debug --image=ubuntu:latest --restart=Never -- \
  sh -c 'nslookup agent-service.touchcli.svc.cluster.local'

# Test health endpoint
kubectl port-forward svc/agent-service 8000:8000 -n touchcli
curl http://localhost:8000/health
```

## Advanced Configuration

### Custom Domain

Update ingress:
```yaml
spec:
  rules:
  - host: app.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### Rate Limiting Configuration

Update ConfigMap:
```yaml
RATE_LIMIT_ENABLED: "true"
RATE_LIMIT_REQUESTS: "100"
RATE_LIMIT_WINDOW: "60"
```

### Resource Limits

Adjust deployment specs:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Secrets Rotation

Sealed Secrets have built-in rotation:

```bash
# Update sealed secret
./scripts/seal-secrets.sh --seal .env.production k8s/sealed-secrets-touchcli.yaml

# Apply new version
kubectl apply -f k8s/sealed-secrets-touchcli.yaml

# Pods will automatically get new secrets on next restart
kubectl rollout restart deployment/agent-service -n touchcli
```

## Disaster Recovery

### Backup Database

```bash
# Export database
kubectl exec -it postgres-pod -- \
  pg_dump -U touchcli_user touchcli_prod | gzip > backup.sql.gz

# Restore from backup
cat backup.sql.gz | gunzip | kubectl exec -i postgres-pod -- \
  psql -U touchcli_user touchcli_prod
```

### Backup Kubernetes Secrets

```bash
# Backup all secrets
kubectl get secret -n touchcli -o yaml > secrets-backup.yaml

# Restore
kubectl apply -f secrets-backup.yaml
```

## Support

For issues:
1. Check workflow logs in GitHub Actions
2. Review pod logs: `kubectl logs -n touchcli ...`
3. Check events: `kubectl get events -n touchcli`
4. Consult [Kubernetes documentation](https://kubernetes.io/docs/)
