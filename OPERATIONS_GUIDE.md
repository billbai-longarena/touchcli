# TouchCLI Operations Guide

**Version**: 1.0
**Last Updated**: 2026-03-02
**Audience**: DevOps engineers, Site Reliability Engineers, Operations team

---

## Quick Reference

### Critical Commands

```bash
# Check system health
./scripts/health-check.sh

# View logs in real-time
docker-compose logs -f                    # Development
kubectl logs -f deployment/backend -n touchcli  # Production

# Restart services
docker-compose restart                    # Development
kubectl rollout restart deployment/backend -n touchcli  # Production

# Database backup
./scripts/database-backup.sh

# Database restore
psql touchcli < /backups/touchcli-<timestamp>.sql

# Run migrations
./scripts/migrate-db.sh
```

---

## 1. Daily Operations Checklist

### Morning (Start of Shift)

**Time**: 8:00 AM
**Frequency**: Daily

```
□ Check system status dashboard (Grafana)
□ Review alerts from overnight (PagerDuty/Slack)
□ Verify all pods are running:
  kubectl get pods -n touchcli
□ Check database size and growth:
  du -sh /var/lib/postgresql/data
□ Review error rate from Sentry:
  - Check error threshold not exceeded
  - Triage new errors
□ Verify backup completed:
  ls -lht /backups/ | head -1
□ Check disk space:
  df -h
□ Review resource utilization:
  kubectl top nodes
  kubectl top pods -n touchcli
```

### Hourly (Automated)

**Frequency**: Every hour (automated via cron)

```
□ Prometheus scrapes metrics (every 15s)
□ Disk space check (automatic alert if >80%)
□ Pod health checks (automatic restart if unhealthy)
□ Load balancer health probes
□ Redis memory check
□ Database connection pool health
```

### Daily (EOD)

**Time**: 6:00 PM
**Frequency**: Daily

```
□ Review error logs for patterns
□ Check backup completion
□ Verify no pending deployments
□ Document any incidents
□ Update on-call runbook
□ Verify database replication lag (if applicable)
```

### Weekly

**Day**: Friday
**Time**: 5:00 PM
**Frequency**: Weekly

```
□ Database maintenance:
  - VACUUM ANALYZE
  - Check for unused indexes
  - Update table statistics
□ Log rotation
  - Archive old logs
  - Verify compression
  - Remove logs >30 days old
□ Certificate expiration check:
  openssl x509 -in cert.pem -noout -dates
□ Security patches applied:
  docker images --format "{{.Repository}}:{{.Tag}}" | sort -u
□ Disaster recovery drill:
  - Test backup restore procedure
  - Verify restore time
  - Document any gaps
□ Capacity planning review:
  - Review growth trends
  - Forecast resource needs
  - Schedule upgrades if needed
```

---

## 2. Starting & Stopping Services

### Development (Docker Compose)

**Start All Services**:

```bash
cd /Users/bingbingbai/Desktop/touchcli
docker-compose up -d

# Verify all services
docker-compose ps

# Expected output:
# NAME             STATUS
# frontend         Up (healthy)
# backend          Up (healthy)
# gateway          Up (healthy)
# postgres         Up (healthy)
# redis            Up (healthy)
```

**Stop All Services**:

```bash
docker-compose down

# To also remove data volumes
docker-compose down -v
```

**Restart Specific Service**:

```bash
# Restart backend only
docker-compose restart backend

# View logs immediately after
docker-compose logs backend --tail 20
```

### Production (Kubernetes)

**Deploy Latest Version**:

```bash
# Automated by GitHub Actions on push to main
# Or manual deployment:
./scripts/deploy-kubernetes.sh

# This will:
# 1. Build and push Docker images
# 2. Update ConfigMaps
# 3. Apply sealed secrets
# 4. Deploy/update pods
# 5. Verify health checks
```

**Restart Deployment**:

```bash
# Full restart (rolling update)
kubectl rollout restart deployment/backend -n touchcli

# Verify rollout
kubectl rollout status deployment/backend -n touchcli

# Scale up/down
kubectl scale deployment/backend --replicas=3 -n touchcli
```

**Stop Application**:

```bash
# Scale down to zero replicas (keeps history)
kubectl scale deployment/backend --replicas=0 -n touchcli

# Full namespace teardown
kubectl delete namespace touchcli
```

---

## 3. Monitoring & Observability

### 3.1 Grafana Dashboards

**Access**: http://localhost:3001 (dev) or https://monitoring.touchcli.example.com (prod)

**Default Login**:
- Username: `admin`
- Password: See Kubernetes secrets or `.env.production`

**Key Dashboards**:

1. **System Overview**
   - Node CPU/Memory usage
   - Disk space available
   - Network throughput
   - Pod status

2. **Application Performance**
   - HTTP request rate
   - Request latency (p50/p95/p99)
   - Error rate by endpoint
   - Database query latency

3. **Database Health**
   - Connection pool utilization
   - Query count and latency
   - Table sizes
   - Replication lag (if applicable)

4. **Agent Health**
   - Agent response time
   - Agent error rate
   - Processing queue depth
   - Task completion rate

### 3.2 Prometheus Metrics

**Access**: http://localhost:9090/graph

**Key Metrics to Monitor**:

```promql
# Request Rate
rate(http_requests_total[5m])

# Error Rate
rate(http_requests_total{status=~"5.."}[5m])

# Latency (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Database Connections
pg_stat_activity_count

# Redis Memory
redis_memory_used_bytes

# Pod CPU
sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)

# Pod Memory
sum(container_memory_working_set_bytes) by (pod)
```

### 3.3 Sentry Error Tracking

**Access**: https://sentry.io or self-hosted instance

**Critical Alerts**:
- Python exceptions
- Uncaught errors
- Performance degradation
- Release regressions

**Actions**:
1. Error occurs → Sentry captures
2. Team notified (Slack/email)
3. Engineer investigates
4. Root cause documented
5. Fix deployed and verified

### 3.4 Logging

**Development**:

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# Specific service
docker-compose logs -f backend --tail 100
```

**Production (Kubernetes)**:

```bash
# View pod logs
kubectl logs <pod-name> -n touchcli

# Follow logs in real-time
kubectl logs -f <pod-name> -n touchcli

# View previous logs (if pod crashed)
kubectl logs <pod-name> --previous -n touchcli

# View logs from all pods in deployment
kubectl logs -f -l app=backend -n touchcli
```

**Log Format**:

```json
{
  "timestamp": "2026-03-02T10:30:00Z",
  "level": "INFO",
  "message": "User login successful",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "ip": "192.168.1.100",
  "duration_ms": 150
}
```

---

## 4. Database Management

### 4.1 Backup & Restore

**Automated Backup**:

```bash
# Runs daily at 02:00 UTC
./scripts/database-backup.sh

# Location: /backups/touchcli-YYYY-MM-DD-HH.sql
# Compressed: gzip (.sql.gz)
# Retention: 30 days
```

**Manual Backup**:

```bash
# Create backup
pg_dump -h localhost -U touchcli_user touchcli | gzip > backup-$(date +%Y%m%d-%H%M).sql.gz

# Verify backup
gunzip -c backup-20260302-1000.sql.gz | head -20
```

**Restore from Backup**:

```bash
# From compressed backup
gunzip -c /backups/touchcli-2026-03-02-020000.sql.gz | psql -h localhost -U touchcli_user touchcli

# Verify restore
psql -h localhost -U touchcli_user touchcli -c "SELECT COUNT(*) FROM customers;"

# Expected: Row count should match source
```

**Backup Verification** (Weekly):

```bash
# Test restore on separate database
createdb -h localhost -U touchcli_user touchcli_test
gunzip -c /backups/touchcli-2026-03-02-020000.sql.gz | psql -h localhost -U touchcli_user touchcli_test

# Validate data integrity
psql -h localhost -U touchcli_user touchcli_test -c "SELECT COUNT(*) FROM users;"
psql -h localhost -U touchcli_user touchcli_test -c "SELECT COUNT(*) FROM conversations;"

# Drop test database
dropdb -h localhost -U touchcli_user touchcli_test
```

### 4.2 Migrations

**List Applied Migrations**:

```bash
# Using Alembic
alembic current

# Using SQL
SELECT version FROM alembic_version;
```

**Apply New Migration**:

```bash
# Automatic on container startup
# Or manual:
alembic upgrade head
```

**Rollback Migration**:

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade 001_initial_schema

# View migration history
alembic history
```

### 4.3 Database Maintenance

**Vacuum & Analyze** (Weekly):

```bash
# Full vacuum (blocks writes, use during maintenance window)
vacuumdb -h localhost -U touchcli_user -d touchcli --full --analyze

# Or concurrent vacuum (no locking, recommended)
vacuumdb -h localhost -U touchcli_user -d touchcli --analyze --jobs=4
```

**Index Management**:

```bash
# Find unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(idx) DESC;

# Drop unused index
DROP INDEX IF EXISTS unused_index_name;

# Reindex (if corrupted)
REINDEX INDEX index_name;
```

**Connection Check**:

```bash
# See active connections
SELECT datname, usename, state, query
FROM pg_stat_activity
WHERE datname = 'touchcli';

# Kill hung query (if necessary)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'touchcli' AND state = 'idle';
```

---

## 5. Network & Routing

### 5.1 Ingress Management

**Check Ingress Status** (Kubernetes):

```bash
kubectl get ingress -n touchcli
kubectl describe ingress touchcli-ingress -n touchcli

# Expected output:
# Name: touchcli-ingress
# Rules:
#   Host    Path  Backends
#   ----    ----  --------
#   touchcli.example.com  /  frontend:80
```

**Update Ingress** (add domain):

```bash
# Edit ingress manifest
kubectl edit ingress touchcli-ingress -n touchcli

# Or apply from file
kubectl apply -f k8s/ingress.yaml -n touchcli

# Verify
kubectl get ingress -n touchcli -o yaml | grep host
```

### 5.2 SSL/TLS Certificates

**Check Certificate Expiration**:

```bash
# Using Let's Encrypt (cert-manager)
kubectl get certificate -n touchcli

# Manual check
echo | openssl s_client -connect touchcli.example.com:443 -noout | openssl x509 -noout -dates

# Output should show:
# notBefore=Mar  2 00:00:00 2026 GMT
# notAfter=Mar  1 23:59:59 2027 GMT
```

**Renew Certificate** (if using cert-manager):

```bash
# Automatic renewal happens every 30 days before expiration
# Manual trigger if needed:
kubectl delete secret -n touchcli touchcli-tls
kubectl delete certificaterequest -n touchcli touchcli-tls-request
```

**Self-signed Certificate** (development only):

```bash
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Configure in Kubernetes
kubectl create secret tls touchcli-tls --cert=cert.pem --key=key.pem -n touchcli
```

---

## 6. Performance Tuning

### 6.1 Application-Level Tuning

**Backend Connection Pool**:

```python
# backend/python/agent_service/main.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Minimum connections
    max_overflow=40,        # Additional connections allowed
    pool_pre_ping=True,     # Verify connection before use
    pool_recycle=3600,      # Recycle connections after 1 hour
)
```

**Redis Connection Pool**:

```python
# backend/python/redis_client.py
redis_client = redis.from_url(
    REDIS_URL,
    encoding='utf-8',
    decode_responses=True,
    max_connections=50,
    socket_connect_timeout=5,
    socket_keepalive=True,
)
```

**Nginx Worker Processes** (Frontend):

```nginx
# frontend/nginx.conf
worker_processes auto;  # Use available CPU cores
worker_connections 10000;  # Max connections per worker
```

### 6.2 Database Tuning

**PostgreSQL Configuration**:

```sql
-- View current settings
SHOW work_mem;  -- Memory for operations (default 4MB)
SHOW shared_buffers;  -- Shared memory buffer (default 128MB)
SHOW effective_cache_size;  -- Total cache (default 1GB)

-- Recommended for TouchCLI:
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
ALTER SYSTEM SET random_page_cost = 1.1;  -- For SSD

-- Reload configuration
SELECT pg_reload_conf();
```

**Connection Pooling** (PgBouncer):

```ini
# pgbouncer.ini
[databases]
touchcli = host=postgres dbname=touchcli

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
```

### 6.3 Kubernetes Resource Optimization

**Right-sizing Pod Resources**:

```yaml
# backend-deployment.yaml
resources:
  requests:
    memory: "256Mi"    # Minimum guaranteed
    cpu: "250m"        # 0.25 CPU core
  limits:
    memory: "512Mi"    # Maximum allowed
    cpu: "500m"        # 0.5 CPU core

# Frontend resources (lighter)
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"
```

**Horizontal Pod Autoscaling**:

```yaml
# Define HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
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
```

---

## 7. Security Operations

### 7.1 Secret Management

**Rotate Secrets**:

```bash
# 1. Generate new secret value
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update in .env.production
sed -i "s/OLD_SECRET=.*/OLD_SECRET=$NEW_SECRET/" .env.production

# 3. Seal the new secret
./scripts/seal-secrets.sh --interactive

# 4. Apply to cluster
kubectl apply -f k8s/sealed-secrets-touchcli.yaml -n touchcli

# 5. Restart pods to load new secret
kubectl rollout restart deployment/backend -n touchcli

# 6. Verify new secret is loaded
kubectl exec -it <pod-name> -n touchcli env | grep SECRET
```

**JWT Secret Rotation**:

```bash
# 1. Generate new JWT_SECRET
JWT_SECRET=$(openssl rand -base64 32)

# 2. Create temporary dual-key setup
# Old tokens still validate, new tokens use new key
# (Implement in code if needed)

# 3. Update secret
kubectl set env deployment/backend JWT_SECRET=$JWT_SECRET -n touchcli

# 4. Restart to apply
kubectl rollout restart deployment/backend -n touchcli

# 5. Force logout all users (invalidate old tokens in Redis)
redis-cli FLUSHDB  # Development only!
# Production: iterate through users and invalidate sessions
```

### 7.2 Access Control

**Kubernetes RBAC**:

```bash
# View role bindings
kubectl get rolebindings -n touchcli
kubectl describe rolebinding touchcli-role -n touchcli

# Add new user to role
kubectl create rolebinding user-admin --clusterrole=admin --user=newuser@example.com -n touchcli

# Verify access
kubectl auth can-i get pods --as=newuser@example.com -n touchcli
```

**Container Access**:

```bash
# Execute command in pod
kubectl exec -it <pod-name> -n touchcli -- bash

# Copy files from pod
kubectl cp touchcli/<pod-name>:/path/to/file ./local-file

# Copy files to pod
kubectl cp ./local-file touchcli/<pod-name>:/path/to/file
```

---

## 8. Incident Response

### 8.1 Service Down Response

**Detection**: Alerting system triggers (Prometheus/PagerDuty)

**Response Steps** (First 5 minutes):

```
1. Acknowledge alert (PagerDuty)
   - Sets expectation with team
   - Starts incident timer

2. Check service status
   docker-compose ps         (Development)
   kubectl get pods -n touchcli  (Production)

3. Check recent logs for errors
   docker-compose logs -f backend --tail 100
   kubectl logs -f deployment/backend -n touchcli

4. Check Sentry for exception patterns
   - Any new errors in last 5 minutes?
   - Are errors repeating?

5. Check database connectivity
   psql -h localhost -U touchcli_user -d touchcli -c "SELECT 1;"

6. Check Redis connectivity
   redis-cli ping

7. Determine impact
   - Is it all users or subset?
   - How many services affected?
   - What's the blast radius?
```

**Mitigation** (5-15 minutes):

```
Option A: Restart Service
  kubectl rollout restart deployment/backend -n touchcli
  kubectl rollout status deployment/backend -n touchcli

  → If service recovers: Monitor for 15 minutes, declare resolved

Option B: Rollback Previous Version
  kubectl rollout undo deployment/backend -n touchcli
  kubectl rollout status deployment/backend -n touchcli

  → If service recovers: Investigate what caused failure

Option C: Scale Down & Back Up
  kubectl scale deployment/backend --replicas=0 -n touchcli
  sleep 30
  kubectl scale deployment/backend --replicas=2 -n touchcli

  → Hard reset, clears stuck connections
```

### 8.2 Database Issue Response

**Detection**: Database query latency alert fires

**Response Steps**:

```
1. Check database health
   kubectl exec -it postgres-0 -n touchcli -- psql -U postgres -d touchcli -c "SELECT pg_stat_database;"

2. Check active connections
   SELECT datname, usename, state, query
   FROM pg_stat_activity
   WHERE datname = 'touchcli'
   ORDER BY query_start;

3. Identify slow queries
   SELECT query, calls, mean_time FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 10;

4. Kill hung query (if necessary)
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = 'touchcli'
   AND state = 'idle in transaction'
   AND query_start < now() - interval '5 minutes';

5. Check table locks
   SELECT * FROM pg_locks;

6. If critical: Restart database pod
   kubectl delete pod postgres-0 -n touchcli
   # Kubernetes will recreate it

7. Monitor recovery
   kubectl logs -f postgres-0 -n touchcli
```

### 8.3 Memory Leak Response

**Detection**: Pod memory usage gradually increasing

**Response Steps**:

```
1. Monitor memory growth
   kubectl top pods -n touchcli --watch

2. Check for memory leaks in logs
   kubectl logs <pod-name> -n touchcli | grep -i memory

3. Generate heap dump (if applicable)
   kubectl exec <pod-name> -n touchcli -- python -m cProfile -o heap.prof app.py

4. If memory exceeds limit:
   - Pod will be killed by kubelet
   - Kubernetes restarts pod automatically
   - Check for immediate recovery

5. If pattern repeats:
   - Scale down pod
   - Force garbage collection
   - Deploy code fix
   - Gradual rollout to verify fix

6. Long-term solution:
   - Add memory profiling to CI/CD
   - Implement memory limits
   - Regular heap analysis
```

### 8.4 High Error Rate Response

**Detection**: Error rate >5% (threshold configurable)

**Response Steps**:

```
1. Check Sentry for error patterns
   - What's the error type?
   - Which endpoint is affected?
   - When did it start?

2. Check recent deployments
   kubectl rollout history deployment/backend -n touchcli

3. If deployment is new:
   - Rollback to previous version
   - kubectl rollout undo deployment/backend -n touchcli

4. Investigate root cause
   - Check logs for stack traces
   - Review code changes
   - Check dependencies updated?

5. If not recent deployment:
   - Check external dependencies (database, Redis, APIs)
   - Review recent traffic patterns
   - Check for DDoS attacks

6. Communicate status
   - Update status page
   - Send Slack notification
   - Provide ETA for fix
```

---

## 9. Scaling Operations

### 9.1 Horizontal Scaling

**Manual Scale Up**:

```bash
# Scale backend to 5 replicas
kubectl scale deployment/backend --replicas=5 -n touchcli

# Verify scaling
kubectl get pods -n touchcli
kubectl rollout status deployment/backend -n touchcli

# Monitor resource usage during scaling
kubectl top pods -n touchcli --watch
```

**Auto-scaling Configuration**:

```bash
# Check HPA status
kubectl get hpa -n touchcli
kubectl describe hpa backend-hpa -n touchcli

# If not auto-scaling:
# 1. Verify metrics-server is installed
kubectl get deployment metrics-server -n kube-system

# 2. Check HPA target metrics
kubectl get hpa backend-hpa -n touchcli -o json | jq '.status'

# 3. If metrics unavailable:
#    - Wait 2-3 minutes for metrics to accumulate
#    - Restart metrics-server if needed
```

### 9.2 Vertical Scaling

**Increase Pod Resources**:

```yaml
# Edit deployment
kubectl edit deployment/backend -n touchcli

# Update resources section:
resources:
  requests:
    memory: "512Mi"    # Increased from 256Mi
    cpu: "500m"        # Increased from 250m
  limits:
    memory: "1Gi"      # Increased from 512Mi
    cpu: "1000m"       # Increased from 500m

# Rolling update automatically triggered
```

**Scale Database Resources**:

```bash
# Scale database volume
# Create larger PV
kubectl patch pvc postgres-data -n touchcli -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Or manually expand volume:
# 1. Create new volume
# 2. Dump database
# 3. Restore to new volume
# 4. Update PVC
```

---

## 10. Compliance & Audit

### 10.1 Audit Logging

**Enable Kubernetes Audit Logging**:

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all at RequestResponse level
- level: RequestResponse
  omitStages:
  - RequestReceived

# Exclude certain high-volume APIs
- level: RequestResponse
  verbs: ["get", "list"]
  resources:
  - group: ""
    resources: ["events"]
```

**Configure API Server**:

```bash
# Add to kube-apiserver startup flags
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--audit-log-path=/var/log/kubernetes/audit.log
--audit-log-maxage=30
--audit-log-maxbackup=10
```

### 10.2 Compliance Checks

**HIPAA Compliance** (if applicable):

```bash
# 1. Verify encryption in transit
kubectl get ingress -n touchcli -o json | jq '.items[].spec.tls'

# 2. Verify encryption at rest
kubectl get pv -o json | jq '.items[].spec'

# 3. Verify access controls
kubectl get rolebindings -n touchcli

# 4. Verify audit logging enabled
kubectl get nodes -o json | jq '.items[].spec'

# 5. Verify backup policies
ls -la /backups/ | tail -10
```

**PCI-DSS Compliance** (if processing payments):

```bash
# 1. Verify TLS 1.2+ only
kubectl describe ingress touchcli-ingress -n touchcli | grep "TLS Version"

# 2. Verify firewall rules
kubectl get networkpolicy -n touchcli

# 3. Verify no default credentials
kubectl get secrets -n touchcli -o json | grep -i password

# 4. Verify logging enabled
kubectl logs deployment/backend -n touchcli | grep audit

# 5. Verify vulnerability scanning
docker scan <image-id>
```

---

## 11. Cost Optimization

### 11.1 Resource Optimization

**Analyze Resource Usage**:

```bash
# Get actual vs requested
kubectl get pods -n touchcli \
  -o json | jq '.items[] | {name: .metadata.name, requests: .spec.containers[].resources.requests, usage: .}'

# Identify over-provisioned pods
kubectl top pods -n touchcli --no-headers | awk '{print $1, $2, $3}' | sort -k2 -rn

# Identify under-utilized nodes
kubectl top nodes
```

**Right-size Requests/Limits**:

```bash
# Gather metrics over 2 weeks
# Compare actual usage vs requests
# Adjust if actual usage <50% of request

# Example: Reduce backend from 256Mi → 128Mi
kubectl set resources deployment/backend -n touchcli \
  --requests=memory=128Mi,cpu=100m \
  --limits=memory=256Mi,cpu=200m
```

### 11.2 Cost Monitoring

**Cloud Cost Analysis**:

```bash
# AWS: Check EC2 costs
aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId, InstanceType, State.Name]'

# Azure: Check resource group costs
az cost management query --scope /subscriptions/{subscription-id} --timeframe ActualLastMonth

# GCP: Check project usage
gcloud billing accounts list
gcloud compute instances list
```

---

## 12. Quick Reference: Common Operations

| Task | Command | Duration |
|------|---------|----------|
| Check system health | `./scripts/health-check.sh` | <1 min |
| View real-time logs | `docker-compose logs -f` | - |
| Restart backend | `kubectl rollout restart deployment/backend -n touchcli` | 2-5 min |
| Database backup | `./scripts/database-backup.sh` | 5-15 min |
| Database restore | `psql touchcli < backup.sql` | 10-30 min |
| Run migrations | `alembic upgrade head` | 1-5 min |
| Scale deployment | `kubectl scale deployment/backend --replicas=5 -n touchcli` | 2-10 min |
| Check certificate expiration | `openssl s_client -connect domain:443 -noout` | <1 min |
| View Grafana dashboards | http://localhost:3001 | - |
| View Prometheus metrics | http://localhost:9090 | - |
| Check pod status | `kubectl get pods -n touchcli` | <1 min |
| View pod logs | `kubectl logs <pod-name> -n touchcli` | <1 min |
| Execute in pod | `kubectl exec -it <pod-name> bash -n touchcli` | - |
| Deploy new version | `./scripts/deploy-kubernetes.sh` | 5-10 min |
| Rollback version | `kubectl rollout undo deployment/backend -n touchcli` | 2-5 min |

---

## Conclusion

This operations guide covers the daily, weekly, and monthly tasks needed to maintain TouchCLI in production. Key principles:

1. **Automate everything** - Kubernetes handles most restarts/scaling
2. **Monitor continuously** - Prometheus + Grafana + Sentry provide visibility
3. **Plan for failure** - Health checks + auto-restart + backups
4. **Document incidents** - Record root causes for continuous improvement
5. **Test procedures** - Regularly test backup restore, disaster recovery, etc.

For specific troubleshooting steps, see **TROUBLESHOOTING.md**.
For incident response procedures, see **RUNBOOKS.md**.
