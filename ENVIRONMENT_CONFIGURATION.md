# TouchCLI Environment Configuration Guide

**Last Updated**: 2026-03-02
**Status**: Complete
**Scope**: Development, Staging, and Production environments

---

## Overview

TouchCLI uses environment-specific configuration files to manage settings across different deployment environments. This guide documents all available configuration options and best practices for each environment.

---

## Environment Files

### 1. Development (`.env`)

**Purpose**: Local development with Docker Compose
**Location**: `/project-root/.env`
**Status**: ✅ Present (configuration template)

**Key Characteristics**:
- Local database (localhost:5432)
- Local Redis (localhost:6379)
- Debug logging enabled
- No HTTPS requirement
- WebSocket to localhost

**Example**:
```bash
ENVIRONMENT=development
POSTGRES_USER=touchcli_user
DATABASE_URL=postgresql://touchcli_user:touchcli_password@postgres:5432/touchcli_db
```

### 2. Staging (`.env.staging`)

**Purpose**: Pre-production testing environment
**Location**: `/project-root/.env.staging`
**Status**: ✅ Created (2026-03-02)

**Key Characteristics**:
- Remote database (staging infrastructure)
- Redis cluster (staging)
- INFO level logging (JSON formatted)
- HTTPS enabled
- Production-like settings
- Daily backups (30-day retention)

**Target Infrastructure**:
- Database: RDS or managed PostgreSQL
- Cache: ElastiCache or managed Redis
- Monitoring: CloudWatch or Datadog

### 3. Production (`.env.production`)

**Purpose**: Live production environment
**Location**: `/project-root/.env.production`
**Status**: ✅ Created (2026-03-02)

**Key Characteristics**:
- Production database with replicas
- High-availability Redis cluster
- WARNING level logging only
- HTTPS/TLS enforced
- Secrets from external vault
- Hourly backups (90-day retention)
- Full observability stack

**Target Infrastructure**:
- Database: Multi-region RDS with failover
- Cache: Redis Cluster with sentinel
- Monitoring: Datadog/NewRelic + ELK Stack

---

## Configuration Categories

### Database Configuration

```yaml
# Development
DATABASE_URL: postgresql://user:pass@localhost:5432/db

# Staging
DATABASE_URL: postgresql://user:pass@postgres.staging.internal:5432/db

# Production
DATABASE_URL: postgresql://user:pass@postgres.prod.internal:5432/db
DB_POOL_SIZE: 20
DB_POOL_TIMEOUT: 10
```

**Environment Variables**:
- `POSTGRES_USER`: Database user
- `POSTGRES_PASSWORD`: Database password
- `POSTGRES_DB`: Database name
- `DATABASE_URL`: Full connection string
- `DB_POOL_SIZE`: Connection pool size (default: 5)
- `DB_POOL_TIMEOUT`: Pool timeout in seconds (default: 30)
- `DB_POOL_RECYCLE`: Connection recycle interval (default: 3600)

### Redis Configuration

```yaml
# Development
REDIS_URL: redis://redis:6379/0

# Staging
REDIS_URL: redis://redis.staging.internal:6379/0
REDIS_PASSWORD: ${REDIS_PASSWORD}

# Production
REDIS_URL: ${REDIS_URL}
REDIS_PASSWORD: ${REDIS_PASSWORD}
REDIS_POOL_SIZE: 50
```

**Environment Variables**:
- `REDIS_URL`: Connection string
- `REDIS_PASSWORD`: Authentication password
- `CELERY_BROKER_URL`: Message broker URL
- `CELERY_RESULT_BACKEND`: Result backend URL
- `REDIS_POOL_SIZE`: Connection pool size
- `REDIS_SOCKET_KEEPALIVE`: Enable keepalive (true/false)

### Authentication

```yaml
# All environments
JWT_SECRET: ${JWT_SECRET}              # Min 32 characters
JWT_EXPIRY: 3600                       # 1 hour
REFRESH_TOKEN_EXPIRY: 2592000          # 30 days
```

**Environment Variables**:
- `JWT_SECRET`: Signing key for JWT tokens (CRITICAL - change per environment)
- `JWT_EXPIRY`: Token expiry in seconds
- `REFRESH_TOKEN_EXPIRY`: Refresh token expiry in seconds
- `SESSION_TIMEOUT`: Session timeout in seconds
- `SESSION_SECURE`: Enable secure cookies (true in production)
- `SESSION_HTTPONLY`: Prevent JS access to cookies (true in production)
- `SESSION_SAMESITE`: CSRF protection (Strict in production)

### API & Gateway Configuration

```yaml
# Development
API_URL: http://localhost:8000
VITE_API_URL: http://localhost:8000
VITE_WS_URL: ws://localhost:8080/ws
GATEWAY_PORT: 8080
GIN_MODE: debug

# Staging
API_URL: https://api.staging.example.com
VITE_API_URL: https://api.staging.example.com
VITE_WS_URL: wss://api.staging.example.com/ws
GATEWAY_PORT: 8080
GIN_MODE: release

# Production
API_URL: https://api.example.com
VITE_API_URL: https://api.example.com
VITE_WS_URL: wss://api.example.com/ws
GATEWAY_PORT: 8080
GIN_MODE: release
```

**Environment Variables**:
- `API_URL`: Backend API endpoint
- `VITE_API_URL`: Frontend API endpoint
- `VITE_WS_URL`: WebSocket endpoint
- `AGENT_SERVICE_URL`: Internal agent service URL
- `GATEWAY_PORT`: HTTP gateway port (default: 8080)
- `GIN_MODE`: Gin framework mode (debug/release)

### Logging Configuration

```yaml
# Development
LOG_LEVEL: DEBUG
LOG_FORMAT: text

# Staging
LOG_LEVEL: INFO
LOG_FORMAT: json

# Production
LOG_LEVEL: WARNING
LOG_FORMAT: json
```

**Environment Variables**:
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
- `LOG_FORMAT`: text or json (structured logging)
- `ENABLE_METRICS`: Enable metrics collection (true/false)
- `METRICS_PORT`: Prometheus metrics port (default: 9090)
- `ENABLE_TRACING`: Enable distributed tracing (true/false)

### Security Configuration

```yaml
# Production Only
ENABLE_HTTPS: true
ENABLE_HSTS: true
ENABLE_CSP: true
CSP_DEFAULT_SRC: 'self'
CSP_SCRIPT_SRC: 'self' 'unsafe-inline' https://cdn.example.com
ALLOWED_ORIGINS: https://app.example.com,https://admin.example.com
ALLOWED_METHODS: GET,POST,PUT,PATCH,DELETE,OPTIONS
ALLOWED_HEADERS: Content-Type,Authorization,X-Requested-With
```

**Environment Variables**:
- `ENABLE_HTTPS`: Enforce HTTPS (true in production)
- `ENABLE_HSTS`: HTTP Strict Transport Security (true in production)
- `ENABLE_CSP`: Content Security Policy (true in production)
- `CSP_*`: CSP directives
- `ALLOWED_ORIGINS`: CORS allowed origins (comma-separated)
- `ALLOWED_METHODS`: CORS allowed HTTP methods
- `ALLOWED_HEADERS`: CORS allowed headers

### LLM/AI Configuration

```yaml
# Development (optional)
OPENAI_API_KEY: ${OPENAI_API_KEY}
LANGGRAPH_API_KEY: ${LANGGRAPH_API_KEY}

# Staging & Production (from secrets)
OPENAI_API_KEY: ${OPENAI_API_KEY}
LANGGRAPH_API_KEY: ${LANGGRAPH_API_KEY}
```

**Environment Variables**:
- `OPENAI_API_KEY`: OpenAI API key (set via secrets)
- `LANGGRAPH_API_KEY`: LangGraph API key (set via secrets)
- `LLM_BASE_URL`: Optional custom LLM endpoint
- `LLM_TIMEOUT`: LLM request timeout in seconds

### Backup & Storage Configuration

```yaml
# Development
BACKUP_ENABLED: false

# Staging
BACKUP_ENABLED: true
BACKUP_SCHEDULE: "0 2 * * *"              # 2 AM UTC daily
BACKUP_RETENTION_DAYS: 30
BACKUP_STORAGE_TYPE: local

# Production
BACKUP_ENABLED: true
BACKUP_SCHEDULE: "0 3 * * *"              # 3 AM UTC daily
BACKUP_RETENTION_DAYS: 90
BACKUP_STORAGE_TYPE: s3
BACKUP_S3_BUCKET: touchcli-backups-prod
```

**Environment Variables**:
- `BACKUP_ENABLED`: Enable automated backups (true/false)
- `BACKUP_SCHEDULE`: Cron expression for backup schedule
- `BACKUP_RETENTION_DAYS`: Days to retain backups
- `BACKUP_STORAGE_TYPE`: local, s3, or gcs
- `BACKUP_S3_BUCKET`: S3 bucket for backups
- `UPLOAD_PATH`: Upload directory path
- `MAX_UPLOAD_SIZE`: Max upload size in bytes

### Monitoring & Observability

```yaml
# Staging
ENABLE_METRICS: true
METRICS_PORT: 9090
LOG_FORMAT: json

# Production
ENABLE_METRICS: true
METRICS_PORT: 9090
ENABLE_TRACING: true
JAEGER_AGENT_HOST: jaeger-agent.monitoring.svc.cluster.local
JAEGER_AGENT_PORT: 6831
ALERT_ENABLED: true
ALERT_SLACK_WEBHOOK: ${ALERT_SLACK_WEBHOOK}
ALERT_EMAIL: ops@example.com
ALERT_PAGERDUTY_KEY: ${ALERT_PAGERDUTY_KEY}
```

**Environment Variables**:
- `ENABLE_METRICS`: Prometheus metrics (true/false)
- `METRICS_PORT`: Metrics endpoint port
- `ENABLE_TRACING`: Distributed tracing (true/false)
- `JAEGER_AGENT_HOST`: Jaeger agent host
- `JAEGER_AGENT_PORT`: Jaeger agent port
- `ALERT_ENABLED`: Enable alerting (true/false)
- `ALERT_SLACK_WEBHOOK`: Slack webhook URL
- `ALERT_EMAIL`: Alert email address
- `ALERT_PAGERDUTY_KEY`: PagerDuty API key

---

## Setup Instructions

### Development Environment

```bash
# 1. Copy template to .env
cp .env.example .env

# 2. Start Docker Compose stack
docker-compose up -d

# 3. Run migrations
docker-compose exec agent_service alembic upgrade head

# 4. Seed data (optional)
docker-compose exec agent_service python -m agent_service.seeds

# 5. Access application
# Frontend: http://localhost:3000
# API: http://localhost:8080
```

### Staging Environment

```bash
# 1. Load staging configuration
export $(cat .env.staging | grep -v '^#' | xargs)

# 2. Build and push images
docker build -f frontend/Dockerfile -t registry/frontend:staging .
docker build -f backend/python/Dockerfile -t registry/agent-service:staging .
docker build -f backend/go/Dockerfile -t registry/gateway:staging .

# 3. Deploy with Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/agent-service.yaml
kubectl apply -f k8s/gateway.yaml
kubectl apply -f k8s/frontend.yaml

# 4. Run migrations
kubectl run -it --rm migration-runner \
  --image=registry/agent-service:staging \
  -- alembic upgrade head

# 5. Verify deployment
kubectl get pods -n touchcli
kubectl logs -n touchcli deployment/frontend
```

### Production Environment

```bash
# 1. Load production configuration
export $(cat .env.production | grep -v '^#' | xargs)

# 2. Ensure secrets are set
# Database credentials, JWT secret, API keys must be in:
# - AWS Secrets Manager, or
# - Vault, or
# - Kubernetes secrets

# 3. Build and push images with version tag
REGISTRY=prod-registry.example.com
VERSION=1.0.0

docker build -f frontend/Dockerfile \
  -t ${REGISTRY}/frontend:${VERSION} .
docker build -f backend/python/Dockerfile \
  -t ${REGISTRY}/agent-service:${VERSION} .
docker build -f backend/go/Dockerfile \
  -t ${REGISTRY}/gateway:${VERSION} .

docker push ${REGISTRY}/frontend:${VERSION}
docker push ${REGISTRY}/agent-service:${VERSION}
docker push ${REGISTRY}/gateway:${VERSION}

# 4. Deploy with Kubernetes (production cluster)
kubectl config use-context production-cluster
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/agent-service.yaml
kubectl apply -f k8s/gateway.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml

# 5. Run migrations in production
kubectl run -it --rm migration-runner \
  --image=${REGISTRY}/agent-service:${VERSION} \
  -- alembic upgrade head

# 6. Enable monitoring
kubectl apply -f k8s/monitoring.yaml

# 7. Verify deployment
kubectl rollout status deployment/frontend -n touchcli
kubectl logs -n touchcli deployment/frontend
```

---

## Secrets Management

### Development

```bash
# Use local .env file
# DO NOT commit to git (included in .gitignore)
```

### Staging & Production

**Option 1: GitHub Secrets (for CI/CD)**

```yaml
# Configure in GitHub repo settings
POSTGRES_USER: staging_user
POSTGRES_PASSWORD: <strong-random-password>
OPENAI_API_KEY: sk-...
LANGGRAPH_API_KEY: ...
JWT_SECRET: <strong-random-secret>
```

**Option 2: AWS Secrets Manager**

```bash
# Store secrets
aws secretsmanager create-secret \
  --name touchcli/staging/db \
  --secret-string '{"username":"user","password":"pass"}'

# Retrieve in pods via AWS SDK
```

**Option 3: Kubernetes Secrets**

```yaml
# Create secret from file
kubectl create secret generic touchcli-secrets \
  --from-file=.env.production \
  -n touchcli

# Reference in pod
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: touchcli-secrets
        key: DATABASE_URL
```

---

## Validation & Testing

### Validate Configuration

```bash
# Check syntax
source .env.staging
echo $DATABASE_URL  # Should output valid connection string

# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Test Redis connection
redis-cli -u $REDIS_URL ping  # Should return PONG
```

### Test Environment Variables

```bash
# Docker Compose
docker-compose config | grep -A 5 "environment:"

# Kubernetes
kubectl describe configmap touchcli-config -n touchcli
kubectl describe secret touchcli-secrets -n touchcli
```

---

## Migration Between Environments

### Promote Staging → Production

```bash
# 1. Verify staging is stable
# - All health checks pass
# - No critical errors in logs
# - Performance metrics normal

# 2. Backup production database
pg_dump production_db > backup_$(date +%Y%m%d).sql

# 3. Deploy to production with new version
kubectl set image deployment/frontend \
  frontend=registry/frontend:v1.0.0 \
  -n touchcli

# 4. Monitor rollout
kubectl rollout status deployment/frontend -n touchcli

# 5. Run smoke tests
# - Frontend loads
# - API responds
# - WebSocket connects
# - Database queries work

# 6. Monitor for 24 hours
# - Check error rates
# - Monitor latency
# - Verify backups work
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check connection string
echo $DATABASE_URL

# Test connection
psql -v ON_ERROR_STOP=1 $DATABASE_URL -c "SELECT 1"

# Check logs
docker logs touchcli_postgres
kubectl logs -n touchcli statefulset/postgres
```

### Redis Connection Issues

```bash
# Check Redis connection
redis-cli -u $REDIS_URL ping

# Check Redis logs
docker logs touchcli_redis
kubectl logs -n touchcli deployment/redis
```

### Environment Variable Not Found

```bash
# Verify in Docker
docker exec touchcli_frontend env | grep API_URL

# Verify in Kubernetes
kubectl exec -it pod/frontend-xxx -n touchcli -- env | grep API_URL

# Check ConfigMap
kubectl get configmap touchcli-config -n touchcli -o yaml
```

---

## Best Practices

### Security

✅ **DO**:
- Use strong, randomly-generated secrets (min 32 chars)
- Store secrets in external vault (not in git)
- Use separate credentials per environment
- Rotate secrets regularly (every 90 days)
- Encrypt secrets in transit (HTTPS only)
- Log security-relevant events only

❌ **DON'T**:
- Commit secrets to git
- Use same secret across environments
- Use weak passwords (< 12 characters)
- Log sensitive data (passwords, tokens)
- Hardcode credentials in code

### Configuration

✅ **DO**:
- Use `.env.example` as template
- Document all variables
- Validate configuration on startup
- Use sensible defaults
- Version control `.env.example`

❌ **DON'T**:
- Commit actual `.env` files
- Use environment variables for non-sensitive config
- Mix concerns in single file
- Duplicate configuration

### Monitoring

✅ **DO**:
- Enable structured logging (JSON)
- Monitor error rates
- Track performance metrics
- Alert on anomalies
- Keep audit logs

❌ **DON'T**:
- Log verbose output in production
- Ignore error rate spikes
- Skip monitoring alerts
- Delete audit logs

---

## References

- [Environment Variables Best Practices](https://12factor.net/config)
- [Secrets Management Guide](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Docker Compose Environment Files](https://docs.docker.com/compose/environment-variables/)
- [Kubernetes ConfigMaps and Secrets](https://kubernetes.io/docs/concepts/configuration/configmap/)

---

**Maintained By**: Claude Worker (Haiku 4.5)
**Last Updated**: 2026-03-02
**Status**: Complete and Ready for Use
