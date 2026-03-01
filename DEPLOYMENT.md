# Deployment Guide - TouchCLI

Complete deployment procedures for TouchCLI across different environments (development, staging, production).

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Local Development (Docker Compose)](#local-development-docker-compose)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment (Kubernetes)](#production-deployment-kubernetes)
5. [Environment Configuration](#environment-configuration)
6. [Database Management](#database-management)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Components

1. **Frontend** - React SPA served by Nginx
   - Port: 80/443
   - Handles client-side routing
   - Proxies API requests to Gateway
   - WebSocket connections through Gateway

2. **Gateway** - HTTP & WebSocket proxy (Go)
   - Port: 8080
   - Routes requests to Agent Service
   - Manages WebSocket connections
   - Health checks and monitoring

3. **Agent Service** - FastAPI backend
   - Port: 8000
   - REST API endpoints
   - Database operations
   - Task processing (Celery)

4. **PostgreSQL** - Primary database
   - Port: 5432
   - Persistent storage
   - Automated backups
   - Replication (production)

5. **Redis** - Cache & message broker
   - Port: 6379
   - Session cache
   - Celery task queue
   - Pub/Sub for real-time updates

### Communication Flow

```
User Browser
    ↓
Frontend (Nginx) :80
    ↓
Gateway (Go) :8080
    ↓
Agent Service (FastAPI) :8000
    ↓
PostgreSQL :5432
```

---

## Local Development (Docker Compose)

### Quick Start

```bash
# Clone repository
git clone <repo> && cd touchcli

# Setup Husky hooks
.husky/setup.sh

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Services Running

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **Gateway**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Database Initialization

```bash
# Run migrations
docker-compose exec agent_service alembic upgrade head

# Seed demo data
docker-compose exec agent_service python -m agent_service.seeds

# Verify database
docker-compose exec postgres psql -U touchcli_user -d touchcli_dev -c "SELECT COUNT(*) FROM customers;"
```

### Development Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes (auto-reloaded)
# - Frontend: npm run dev (watch mode)
# - Backend: uvicorn --reload

# Run tests
npm --prefix frontend run test:run
docker-compose exec agent_service pytest tests/

# Commit (pre-commit hooks run linting)
git commit -m "feat: my feature"

# Push (pre-push hooks run tests)
git push origin feature/my-feature

# Create PR on GitHub
```

---

## Staging Deployment

### Prerequisites

- Docker & Docker Registry
- Database hosting (AWS RDS, Google Cloud SQL, etc.)
- Redis hosting (ElastiCache, Redis Cloud, etc.)
- GitHub Secrets configured

### GitHub Secrets Required

```
STAGING_DB_PASSWORD          # Database password
STAGING_DB_HOST              # Database hostname
JWT_SECRET_STAGING           # JWT signing key
OPENAI_API_KEY_STAGING       # OpenAI API key
LANGGRAPH_API_KEY_STAGING    # LangGraph API key
SENTRY_DSN_STAGING           # Error tracking
DOCKER_REGISTRY_USERNAME     # Docker registry credentials
DOCKER_REGISTRY_PASSWORD     # Docker registry credentials
```

### Automated Deployment (GitHub Actions)

```bash
# Push to develop branch
git push origin develop

# GitHub Actions automatically:
# 1. Runs all tests
# 2. Builds Docker images
# 3. Pushes to registry
# 4. Deploys to staging
# 5. Runs migrations
# 6. Sends Slack notification
```

### Manual Deployment

```bash
# Build Docker images
docker build -t touchcli/frontend:latest -f frontend/Dockerfile .
docker build -t touchcli/agent-service:latest -f backend/python/Dockerfile .
docker build -t touchcli/gateway:latest -f backend/go/Dockerfile .

# Push to registry
docker push touchcli/frontend:latest
docker push touchcli/agent-service:latest
docker push touchcli/gateway:latest

# Deploy to staging environment
# (varies by hosting provider)
```

### Verify Staging

```bash
# Check services are running
curl https://staging.touchcli.io/health

# Run smoke tests
npm --prefix frontend run test:e2e

# Monitor logs
docker logs <container_id>
```

---

## Production Deployment (Kubernetes)

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker images pushed to registry
- Persistent storage (AWS EBS, GCP Persistent Disks, etc.)
- Ingress controller (Nginx recommended)
- Certificate manager (cert-manager for Let's Encrypt)

### Setup Checklist

- [ ] Kubernetes cluster created
- [ ] Storage classes configured
- [ ] Ingress controller installed
- [ ] Certificate manager installed
- [ ] Registry credentials configured
- [ ] GitHub Secrets setup
- [ ] Domain DNS pointing to cluster

### Secrets & ConfigMaps

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create ConfigMap (non-sensitive data)
kubectl apply -f k8s/configmap.yaml

# Create Secrets (sensitive data)
# IMPORTANT: Use sealed-secrets or similar for production
kubectl create secret generic touchcli-secrets \
  --from-literal=DATABASE_URL='postgresql://...' \
  --from-literal=REDIS_URL='redis://...' \
  --from-literal=JWT_SECRET='...' \
  -n touchcli
```

### Deploy Services

```bash
# Deploy database (if not using managed service)
# kubectl apply -f k8s/postgres.yaml

# Deploy backend
kubectl apply -f k8s/backend-deployment.yaml

# Deploy gateway
kubectl apply -f k8s/gateway-deployment.yaml

# Deploy frontend
kubectl apply -f k8s/frontend-deployment.yaml

# Deploy ingress
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl rollout status deployment/agent-service -n touchcli
kubectl rollout status deployment/gateway -n touchcli
kubectl rollout status deployment/frontend -n touchcli
```

### Verify Production Deployment

```bash
# Check pods are running
kubectl get pods -n touchcli

# Check services
kubectl get svc -n touchcli

# Check ingress
kubectl get ingress -n touchcli

# View logs
kubectl logs -f deployment/agent-service -n touchcli

# Test endpoints
curl https://touchcli.io/
curl https://api.touchcli.io/health
```

### Scale Services

```bash
# Scale frontend
kubectl scale deployment frontend --replicas=5 -n touchcli

# Scale backend
kubectl scale deployment agent-service --replicas=3 -n touchcli

# Auto-scaling (requires metrics-server)
# kubectl autoscale deployment agent-service --min=2 --max=10 -n touchcli
```

### Rolling Updates

```bash
# Update image
kubectl set image deployment/frontend frontend=touchcli/frontend:v2 -n touchcli

# Watch rollout
kubectl rollout status deployment/frontend -n touchcli

# Rollback if needed
kubectl rollout undo deployment/frontend -n touchcli
```

---

## Environment Configuration

### Development (.env.development)

```bash
# Local database
DATABASE_URL=postgresql://touchcli_user:dev_password@localhost:5432/touchcli_dev

# Local Redis
REDIS_URL=redis://localhost:6379

# Frontend URLs
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8080/ws

# Log level
LOG_LEVEL=DEBUG
```

### Staging (.env.staging)

```bash
# Staging database
DATABASE_URL=postgresql://touchcli_user:${STAGING_DB_PASSWORD}@postgres-staging.internal:5432/touchcli_staging

# Staging Redis
REDIS_URL=redis://redis-staging.internal:6379

# Frontend URLs
VITE_API_URL=https://staging-api.touchcli.io
VITE_WS_URL=wss://staging-api.touchcli.io/ws

# Log level
LOG_LEVEL=INFO
```

### Production (.env.production)

```bash
# Production database (managed service)
DATABASE_URL=postgresql://touchcli_user:${PROD_DB_PASSWORD}@rds.amazonaws.com:5432/touchcli_prod

# Production Redis (managed service)
REDIS_URL=redis://:${REDIS_PASSWORD}@redis.example.com:6379

# Frontend URLs
VITE_API_URL=https://api.touchcli.io
VITE_WS_URL=wss://api.touchcli.io/ws

# Log level (WARN in production)
LOG_LEVEL=WARN
```

### Loading Environment Variables

```bash
# Docker
docker run --env-file .env.production touchcli/agent-service

# Kubernetes
kubectl create secret generic touchcli-secrets --from-env-file=.env.production

# Local development
set -a && source .env.development && set +a
```

---

## Database Management

### Migrations

```bash
# Create new migration
docker-compose exec agent_service alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec agent_service alembic upgrade head

# Rollback last migration
docker-compose exec agent_service alembic downgrade -1

# Check migration status
docker-compose exec agent_service alembic current
```

### Backups

```bash
# Manual backup
docker-compose exec postgres pg_dump \
  -U touchcli_user touchcli_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup (production)
# Use RDS automated backups or set up cron job
```

### Restore from Backup

```bash
# Create new database
docker-compose exec postgres createdb -U touchcli_user touchcli_restore

# Restore from backup
docker-compose exec postgres psql -U touchcli_user touchcli_restore < backup.sql

# Verify data
docker-compose exec postgres psql -U touchcli_user touchcli_restore -c "SELECT COUNT(*) FROM customers;"
```

### Database Maintenance

```bash
# Vacuum and analyze
docker-compose exec postgres vacuumdb -U touchcli_user -d touchcli_dev -z

# Check disk usage
docker-compose exec postgres du -sh /var/lib/postgresql/data

# Monitor connections
docker-compose exec postgres psql -U touchcli_user -d touchcli_dev -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

---

## Monitoring & Health Checks

### Health Endpoints

```bash
# Frontend health
curl http://localhost:3000/health

# API health
curl http://localhost:8000/health

# Gateway health
curl http://localhost:8080/health
```

### Health Check Response

```json
{
  "status": "ok",
  "timestamp": "2026-03-02T10:00:00Z",
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 5
    },
    "redis": {
      "status": "ok",
      "latency_ms": 2
    }
  }
}
```

### Kubernetes Health Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 30
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

### Monitoring Services

Recommended tools:
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **ELK Stack** - Log aggregation
- **Sentry** - Error tracking
- **DataDog** - APM and monitoring

---

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs agent_service
docker-compose logs gateway
docker-compose logs frontend

# Check port availability
lsof -i :8000  # Agent Service
lsof -i :8080  # Gateway
lsof -i :3000  # Frontend

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Verify connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check PostgreSQL status
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Issues

```bash
# Test connection
redis-cli -u $REDIS_URL PING

# Check Redis status
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### API Errors

```bash
# Check API logs
docker-compose logs -f agent_service

# Test API endpoint
curl -v http://localhost:8000/health

# Check database
docker-compose exec postgres psql -U touchcli_user -d touchcli_dev -c "\dt"
```

### WebSocket Issues

```bash
# Check gateway logs
docker-compose logs -f gateway

# Test WebSocket connection
websocat ws://localhost:8080/ws

# Check port forwarding
netstat -an | grep 8080
```

### Kubernetes Troubleshooting

```bash
# Check pod status
kubectl get pods -n touchcli -o wide

# Describe failed pod
kubectl describe pod <pod-name> -n touchcli

# View pod logs
kubectl logs <pod-name> -n touchcli

# Port forward for debugging
kubectl port-forward svc/agent-service 8000:8000 -n touchcli

# Check resource usage
kubectl top nodes
kubectl top pods -n touchcli

# Debug pod
kubectl exec -it <pod-name> -n touchcli -- /bin/bash
```

---

## Performance Optimization

### Frontend

- Enable gzip compression in Nginx ✅
- Cache static assets (images, CSS, JS) ✅
- Lazy load components
- Optimize bundle size

### Backend

- Database indexing on frequently queried columns
- Connection pooling (configured in SQLAlchemy)
- Redis caching for hot data
- Async task processing with Celery

### Infrastructure

- Kubernetes resource limits and requests
- Horizontal Pod Autoscaling
- Vertical Pod Autoscaling
- Regular cleanup of old resources

---

## Disaster Recovery

### Backup Strategy

1. **Daily automated backups** (AWS RDS, Google Cloud SQL)
2. **Weekly archive backups** (S3, Google Cloud Storage)
3. **Transaction logs** (continuous replication)
4. **Test restores** (monthly validation)

### Recovery Procedures

```bash
# From automated backup
# Use managed database service restore feature

# From manual backup
psql -d touchcli_restored < backup_20260302.sql

# From transaction logs
# Use pg_waldump and pg_rewind

# Verify data integrity
SELECT COUNT(*) FROM customers;
SELECT MAX(updated_at) FROM conversations;
```

### Failover Plan

1. Detect database failure (health checks)
2. Failover to replica (multi-region setup)
3. Update connection strings
4. Verify data consistency
5. Scale up services
6. Monitor for issues

---

## Support

### Documentation

- **DEVELOPER_SETUP.md** - Developer onboarding
- **CI_CD_SETUP.md** - CI/CD configuration
- **PROJECT_STATUS.md** - Project overview

### Getting Help

1. Check logs: `docker-compose logs`
2. Check health: `curl http://localhost:8000/health`
3. Review troubleshooting section above
4. Check GitHub issues
5. Contact DevOps team

---

**Last Updated**: 2026-03-02
**Maintained By**: Claude Worker
**Status**: Production Ready
