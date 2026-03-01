# Phase 3.7 Plan: Deployment & Infrastructure

**Status**: Scout Reconnaissance
**Date**: 2026-03-02
**Previous Phase**: 3.6 Complete (176+ tests, production-ready)
**Progress**: Phase 3 at 86% (6/7 tasks), ready for final deployment

---

## Overview

**Phase 3.7: Deployment & Infrastructure Setup**
- Containerize frontend with Docker
- Complete backend Docker setup verification
- Create Kubernetes deployment manifests
- Set up environment configuration management
- Implement database migration system
- Configure monitoring and health checks
- Document deployment procedures

**Estimated Effort**: 2-3 days
**Complexity**: High (infrastructure, orchestration)
**Blocker Risk**: Low (all prerequisites ready)

---

## Current State Assessment

### ✅ What Exists

**Docker Infrastructure** (Partial):
- ✅ `docker-compose.yml` - Full local development stack
  - PostgreSQL 16 with volume persistence
  - Redis 7 with volume persistence
  - Python FastAPI service with health checks
  - Go Gateway with health checks
  - Network bridge for service communication

**Backend Dockerfiles**:
- ✅ `backend/python/Dockerfile` - FastAPI service
- ✅ `backend/go/Dockerfile` - Gateway service

**Environment Configuration**:
- ✅ `.env.example` - Template for environment variables
- ✅ `.env` - Current development environment

**CI/CD Pipeline**:
- ✅ GitHub Actions `test.yml` - Automated testing
- ✅ GitHub Actions `deploy.yml` - Staging deployment

### ❌ What's Missing

**Frontend**:
- ❌ `frontend/Dockerfile` - Multi-stage build for React app
- ❌ `frontend/.dockerignore` - Docker build optimization
- ❌ Nginx/HTTP server configuration for SPA

**Kubernetes** (Optional but Recommended):
- ❌ `k8s/namespace.yaml` - Kubernetes namespace
- ❌ `k8s/postgres.yaml` - PostgreSQL StatefulSet
- ❌ `k8s/redis.yaml` - Redis Deployment
- ❌ `k8s/agent-service.yaml` - FastAPI Service
- ❌ `k8s/gateway.yaml` - Go Gateway Service
- ❌ `k8s/frontend.yaml` - React Frontend Deployment
- ❌ `k8s/ingress.yaml` - Ingress controller config

**Database**:
- ❌ Migration tools setup (Alembic is ready, but scripts needed)
- ❌ Seed data scripts
- ❌ Backup/restore procedures

**Monitoring**:
- ❌ Prometheus configuration
- ❌ Grafana dashboards
- ❌ ELK/Loki for log aggregation

**Documentation**:
- ❌ Deployment runbook
- ❌ Troubleshooting guide
- ❌ Scaling guidelines

---

## Task 3.7 Implementation Plan

### Phase 3.7.1: Frontend Containerization (Half day)

**1.1 Create Frontend Dockerfile**

```dockerfile
# Multi-stage build for minimal production image
FROM node:18-alpine as builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY frontend/nginx.conf /etc/nginx/conf.d/
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**1.2 Create Nginx Configuration**

- Serve React SPA from `/usr/share/nginx/html`
- Proxy API requests to gateway service
- Enable gzip compression
- Set cache headers for static assets

**1.3 Create .dockerignore**

```
node_modules/
dist/
.git
.env
```

**1.4 Update docker-compose.yml**

Add frontend service:
```yaml
frontend:
  build:
    context: .
    dockerfile: frontend/Dockerfile
  ports:
    - "3000:80"
  depends_on:
    - gateway
  environment:
    VITE_API_URL: http://gateway:8080
```

---

### Phase 3.7.2: Environment Configuration (Half day)

**2.1 Create Environment Management**

Files to create:
- `.env.development` - Local development
- `.env.staging` - Staging environment
- `.env.production` - Production environment
- `scripts/load-env.sh` - Environment variable loader

**2.2 Document Environment Variables**

**Frontend**:
- `VITE_API_URL` - Backend API endpoint
- `VITE_LOG_LEVEL` - Logging level (debug/info/warn/error)

**Backend**:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `CELERY_BROKER_URL` - Celery message broker
- `OPENAI_API_KEY` - OpenAI API key
- `LANGGRAPH_API_KEY` - LangGraph API key
- `ENVIRONMENT` - Runtime environment
- `LOG_LEVEL` - Logging level
- `JWT_SECRET` - JWT signing key

**2.3 Create Secrets Management**

- Use Docker secrets or Kubernetes secrets for sensitive data
- Document how to manage secrets in different environments
- Create secret generator script for development

---

### Phase 3.7.3: Kubernetes Deployment (1 day, optional)

**3.1 Create Namespace**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: touchcli
```

**3.2 Create Service Manifests**

For each service:
- PostgreSQL StatefulSet (stateful, persistent storage)
- Redis Deployment (stateless, can scale)
- Agent Service Deployment (multiple replicas)
- Gateway Deployment (multiple replicas)
- Frontend Deployment (multiple replicas)

**3.3 Create Ingress**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: touchcli-ingress
  namespace: touchcli
spec:
  rules:
    - host: touchcli.example.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: gateway
                port:
                  number: 8080
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

**3.4 Create ConfigMaps & Secrets**

- ConfigMap for non-sensitive config
- Secrets for sensitive data (API keys, passwords)
- Service account for RBAC

---

### Phase 3.7.4: Database & Migrations (Half day)

**4.1 Database Migration Setup**

Using existing Alembic:
- Create migration scripts for all schema changes
- Document migration procedures
- Test migrations in staging

**4.2 Seed Data**

Create script to seed:
- Demo users
- Demo customers
- Demo conversations
- Demo opportunities

**4.3 Backup/Restore**

Document procedures for:
- Automated backups (daily)
- Point-in-time recovery
- Database restore procedures

---

### Phase 3.7.5: Monitoring & Observability (1 day, optional)

**5.1 Health Checks**

Already implemented:
- HTTP health endpoints
- Database connectivity checks
- Redis connectivity checks

Enhance:
- Readiness probes for Kubernetes
- Startup probes for slow startups

**5.2 Logging**

- Structured logging (JSON)
- Log aggregation (ELK stack recommended)
- Log retention policies

**5.3 Monitoring (Optional)**

- Prometheus metrics
- Grafana dashboards
- Alert rules

**5.4 Performance Monitoring**

- APM integration (DataDog/NewRelic optional)
- Request tracing
- Error tracking

---

## Deployment Architecture

### Development (docker-compose)

```
localhost:5432 (PostgreSQL)
localhost:6379 (Redis)
localhost:8000 (Agent Service)
localhost:8080 (Gateway)
localhost:3000 (Frontend)
```

### Staging/Production (Kubernetes)

```
LoadBalancer (Ingress)
  ↓
API (path=/api) → Gateway Service → Go Gateway Pod(s)
      ↓
  Agent Service Pod(s) → PostgreSQL Pod → PersistentVolume
      ↓
  Redis Pod → PersistentVolume

Frontend (path=/) → Frontend Service → React Pod(s)
```

---

## Deployment Procedures

### Local Development

```bash
# Start full stack
docker-compose up -d

# Run migrations
docker-compose exec agent_service \
  alembic upgrade head

# Seed data
docker-compose exec agent_service \
  python -m agent_service.seeds

# Check status
docker-compose ps
docker-compose logs -f
```

### Staging Deployment

```bash
# Build images
docker build -f backend/python/Dockerfile -t agent-service:latest .
docker build -f backend/go/Dockerfile -t gateway:latest .
docker build -f frontend/Dockerfile -t frontend:latest .

# Push to registry
docker push myregistry/agent-service:latest
docker push myregistry/gateway:latest
docker push myregistry/frontend:latest

# Deploy with Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/agent-service.yaml
kubectl apply -f k8s/gateway.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml
```

### Production Deployment

Same as staging, but:
- Use production docker registry
- Use production environment variables
- Enable SSL/TLS for ingress
- Configure backup retention
- Enable monitoring and logging

---

## Testing Deployment

**Pre-deployment Checks**:
- [ ] All tests pass
- [ ] Docker images build successfully
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Health checks passing

**Post-deployment Checks**:
- [ ] Frontend loads correctly
- [ ] API endpoints responding
- [ ] Database connectivity verified
- [ ] WebSocket connections working
- [ ] All services healthy

---

## Estimated Timeline

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 1 | Frontend Dockerfile | 0.5 day | Ready to start |
| 2 | Environment config | 0.5 day | Ready to start |
| 3 | Kubernetes (optional) | 1 day | Ready to start |
| 4 | Database setup | 0.5 day | Ready to start |
| 5 | Monitoring (optional) | 1 day | Ready to start |
| - | **TOTAL** | **2-3 days** | - |

**MVP Path (Essential)**: Phases 1, 2, 4 = 1-1.5 days
**Full Path (Recommended)**: All phases = 2-3 days

---

## Success Criteria

Phase 3.7 is complete when:
- ✅ Frontend containerized and builds without errors
- ✅ All services run in docker-compose
- ✅ docker-compose up starts full working stack
- ✅ Database migrations run automatically
- ✅ All health checks passing
- ✅ Environment configuration documented
- ✅ (Optional) Kubernetes manifests created and working
- ✅ Deployment runbook documented
- ✅ Zero unresolved deployment blockers

---

## Risk Assessment

**Low Risk** (MVP essentials):
- Frontend Dockerfile (straightforward Node → Nginx)
- Environment configuration (template-based)
- Database setup (using existing migrations)

**Medium Risk** (optional enhancements):
- Kubernetes deployment (requires cluster setup)
- Monitoring setup (third-party service integration)
- Performance optimization (profiling needed)

**Mitigation**:
- Docker-compose works locally first
- Test in staging before production
- Gradual rollout with canary deployment
- Monitor health checks closely

---

## File Checklist

### To Create
- [ ] `frontend/Dockerfile`
- [ ] `frontend/.dockerignore`
- [ ] `frontend/nginx.conf`
- [ ] `.env.staging`
- [ ] `.env.production`
- [ ] `scripts/load-env.sh`
- [ ] `scripts/seed-data.py`
- [ ] `scripts/backup-db.sh`
- [ ] `scripts/restore-db.sh`
- [ ] (Optional) `k8s/namespace.yaml`
- [ ] (Optional) `k8s/configmaps.yaml`
- [ ] (Optional) `k8s/postgres.yaml`
- [ ] (Optional) `k8s/redis.yaml`
- [ ] (Optional) `k8s/agent-service.yaml`
- [ ] (Optional) `k8s/gateway.yaml`
- [ ] (Optional) `k8s/frontend.yaml`
- [ ] (Optional) `k8s/ingress.yaml`
- [ ] `DEPLOYMENT_RUNBOOK.md`
- [ ] `TROUBLESHOOTING.md`

### To Modify
- [ ] `docker-compose.yml` - Add frontend service
- [ ] `.github/workflows/deploy.yml` - Update with new services
- [ ] `README.md` - Add deployment instructions

---

**Prepared by**: Scout Agent (Termite Protocol)
**Session Type**: Reconnaissance & Planning for Phase 3.7
**Confidence Level**: Very High (all prerequisites ready)
**Recommended Next Caste**: Worker (implementation)

---

*All backend services ready for containerization. Frontend containerization straightforward. MVP path clear and achievable in 1-1.5 days.*
