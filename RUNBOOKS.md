# TouchCLI Incident Response Runbooks

**Version**: 1.0
**Last Updated**: 2026-03-02
**Audience**: On-call engineers, DevOps team

---

## Table of Contents

1. [Pod Crash Recovery](#1-pod-crash-recovery)
2. [Database Connection Failure](#2-database-connection-failure)
3. [Memory/Disk Pressure Response](#3-memorydisk-pressure-response)
4. [High Error Rate Response](#4-high-error-rate-response)
5. [Performance Degradation Investigation](#5-performance-degradation-investigation)
6. [WebSocket Connection Issues](#6-websocket-connection-issues)
7. [Complete Service Outage](#7-complete-service-outage)
8. [Data Corruption/Loss](#8-data-corruptionloss)

---

## 1. Pod Crash Recovery

### Symptom Detection

```
- Pod status: CrashLoopBackOff or Error
- Error in kubectl: "Container failed to start"
- Repeated restart attempts visible
```

### Quick Diagnosis (First 2 minutes)

```bash
# 1. Check pod status
kubectl describe pod <pod-name> -n touchcli
# Look for: Events → Last State → Reason → Message

# 2. View crash logs
kubectl logs <pod-name> --previous -n touchcli
# This shows logs from BEFORE the crash

# 3. Check recent changes
kubectl rollout history deployment/backend -n touchcli
kubectl diff -f k8s/backend-deployment.yaml
```

### Common Causes & Fixes

#### Cause: Out of Memory (OOMKilled)

**Symptoms**:
```
Status: OOMKilled
Memory: Exceeded limits
```

**Fix**:

```bash
# Option 1: Increase memory limit
kubectl set resources deployment/backend -n touchcli \
  --limits=memory=1Gi

# Option 2: Rollback to previous version
kubectl rollout undo deployment/backend -n touchcli

# Option 3: Quick restart with fresh memory
kubectl rollout restart deployment/backend -n touchcli

# Monitor recovery
kubectl get pod <pod-name> -n touchcli --watch
```

**Prevention**:
- Add memory profiling to CI/CD
- Set resource requests=limits for predictable behavior
- Monitor memory growth in Grafana

#### Cause: Readiness Probe Failing

**Symptoms**:
```
Status: CrashLoopBackOff
Reason: Readiness probe failed
Message: Get http://10.0.0.5:8000/health: no such host
```

**Fix**:

```bash
# 1. Check if service is actually running
kubectl exec -it <pod-name> -n touchcli -- curl localhost:8000/health

# 2. Check database connectivity
kubectl exec -it <pod-name> -n touchcli -- python -c "
import psycopg2
conn = psycopg2.connect('dbname=touchcli user=touchcli_user host=postgres')
print('Database connected!')
"

# 3. Check environment variables
kubectl exec -it <pod-name> -n touchcli -- env | grep DATABASE_URL

# 4. If environment wrong:
kubectl set env deployment/backend DATABASE_URL=postgresql://... -n touchcli
kubectl rollout restart deployment/backend -n touchcli
```

**Prevention**:
- Increase initialDelaySeconds (30s instead of 10s)
- Increase timeoutSeconds (5s instead of 1s)
- Add liveness probe (separate from readiness)

#### Cause: Image Pull Error

**Symptoms**:
```
Status: ImagePullBackOff
Reason: ErrImagePull
Message: unknown image "myregistry/backend:typo"
```

**Fix**:

```bash
# 1. Check image name in deployment
kubectl get deployment backend -n touchcli -o yaml | grep image

# 2. Verify image exists in registry
docker images | grep backend
docker pull myregistry/backend:latest

# 3. Fix deployment
kubectl set image deployment/backend backend=myregistry/backend:v1.0.0 -n touchcli

# 4. If credentials issue:
kubectl create secret docker-registry regcred \
  --docker-server=myregistry.io \
  --docker-username=user \
  --docker-password=pass \
  -n touchcli

# Update deployment to use secret
kubectl patch serviceaccount default -n touchcli \
  -p '{"imagePullSecrets": [{"name": "regcred"}]}'
```

### Recovery Validation

```bash
# 1. Pod should be Running
kubectl get pod <pod-name> -n touchcli
# Status: Running, Ready: 1/1

# 2. Service should be accessible
kubectl exec -it <frontend-pod> -n touchcli -- \
  curl -s http://backend:8000/health | jq .

# 3. Metrics should show traffic
kubectl logs -f deployment/backend -n touchcli | head -20
```

### Escalation (If Above Steps Fail)

```
1. Declare SEV-1 incident (total service outage)
2. Call backup engineer
3. Prepare rollback to previous stable version:
   kubectl rollout undo deployment/backend -n touchcli
4. If still failing: Scale down, investigate offline:
   kubectl scale deployment/backend --replicas=0 -n touchcli
5. Root cause analysis after emergency fixed
```

---

## 2. Database Connection Failure

### Symptom Detection

```
- Error: "psycopg2.OperationalError: could not connect to server"
- Error: "connection pool is exhausted"
- Error: "FATAL: remaining connection slots reserved for non-replication superuser connections"
```

### Quick Diagnosis (First 5 minutes)

```bash
# 1. Check database pod status
kubectl get pod postgres -n touchcli
kubectl describe pod postgres -n touchcli

# 2. Check database is listening
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "SELECT 1;"

# 3. Check active connections
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"

# 4. Check connection pool
kubectl logs -f deployment/backend -n touchcli | grep -i "pool"
```

### Common Causes & Fixes

#### Cause: Database Pod Not Running

**Symptoms**:
```
Pod Status: Pending, CrashLoopBackOff, or Error
No pods responding to queries
```

**Fix**:

```bash
# 1. Check pod events
kubectl describe pod postgres -n touchcli

# 2. If PVC missing:
kubectl get pvc -n touchcli
# If postgres-data not listed:
kubectl create pvc -f k8s/postgres-pvc.yaml -n touchcli

# 3. Restart pod
kubectl delete pod postgres -n touchcli
kubectl wait --for=condition=ready pod -l app=postgres -n touchcli --timeout=300s

# 4. Verify recovery
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "SELECT COUNT(*) FROM users;"
```

#### Cause: Connection Pool Exhausted

**Symptoms**:
```
Error: "Too many connections"
Backend pod shows: [pool_size reached]
```

**Fix**:

```bash
# 1. Check current connections
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -c "SELECT COUNT(*) FROM pg_stat_activity;"

# 2. Kill idle connections (if safe)
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE datname = 'touchcli'
  AND state = 'idle'
  AND query_start < now() - interval '30 minutes';"

# 3. Increase pool size (if frequent)
kubectl set env deployment/backend \
  -p DB_POOL_SIZE=30,DB_MAX_OVERFLOW=60 -n touchcli
kubectl rollout restart deployment/backend -n touchcli

# 4. Monitor recovery
kubectl logs -f deployment/backend -n touchcli | grep connection
```

#### Cause: Database Disk Full

**Symptoms**:
```
Error: "could not create relation"
psql: FATAL: remaining connection slots...
PostgreSQL log: ERROR: write failed
```

**Fix**:

```bash
# 1. Check disk usage
kubectl exec -it postgres -n touchcli -- \
  df -h /var/lib/postgresql/data

# 2. Check table sizes
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"

# 3. Expand volume
kubectl patch pvc postgres-data -n touchcli -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# 4. Clean up old logs (if needed)
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "
  DELETE FROM logs WHERE created_at < now() - interval '90 days';"

# 5. Vacuum to reclaim space
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "VACUUM FULL ANALYZE;"

# 6. Monitor recovery
kubectl exec -it postgres -n touchcli -- \
  df -h /var/lib/postgresql/data
```

#### Cause: Corrupted Data or Indices

**Symptoms**:
```
Error: "ERROR: unexpected zero page in block..."
Error: "ERROR: invalid ctid in tuple..."
```

**Fix**:

```bash
# 1. Check for corruption
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "
  SELECT schemaname, tablename
  FROM pg_tables
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema');"

# 2. Reindex affected table
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "REINDEX TABLE conversations;"

# 3. If still failing: Restore from backup
#    See: Database Backup & Restore in OPERATIONS_GUIDE.md

# 4. Verify data integrity
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "SELECT COUNT(*) FROM users;"
```

### Recovery Validation

```bash
# 1. Database responding to queries
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "SELECT 1;"
# Output: 1

# 2. Backend can connect
kubectl exec -it <backend-pod> -n touchcli -- \
  python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://...')
conn = engine.connect()
print('Success!')
"

# 3. API returning data
kubectl exec -it <frontend-pod> -n touchcli -- \
  curl -s http://backend:8000/customers | jq '.[] | .id' | head -3
```

---

## 3. Memory/Disk Pressure Response

### Symptom Detection

```
- Kubernetes eviction notices
- Pod OOMKilled
- Disk usage >85%
- Memory usage >90%
- Node reports "MemoryPressure" or "DiskPressure"
```

### Quick Diagnosis (First 3 minutes)

```bash
# 1. Check node status
kubectl get nodes -o wide
kubectl describe node <node-name> | grep -A 5 "Conditions:"

# 2. Check resource usage by pod
kubectl top pods -n touchcli --no-headers | sort -k3 -rn | head -10

# 3. Check resource usage by node
kubectl top nodes

# 4. Check disk usage
kubectl exec -it <pod> -n touchcli -- df -h

# 5. Check if pods are being evicted
kubectl get events -n touchcli | grep -i "evicted\|pressure"
```

### Memory Pressure Response

**Symptoms**:
```
Node condition: MemoryPressure=True
Pods with status: Evicted
```

**Steps**:

```bash
# Step 1: Identify high-memory pods (immediate)
kubectl top pods -n touchcli --no-headers | sort -k3 -rn

# Step 2: Scale down low-priority workloads (immediate)
# Stop jobs, reduce replicas
kubectl scale deployment/backend --replicas=1 -n touchcli

# Step 3: Check for memory leaks
kubectl logs <memory-heavy-pod> -n touchcli | tail -50

# Step 4: Increase node capacity (within 30 min)
# Option A: Add new node to cluster
kubectl scale nodepool default --num-nodes=4

# Option B: Upgrade node to larger size
# (Requires cluster-specific commands)

# Step 5: Add memory requests/limits (for future)
kubectl set resources deployment/backend \
  --requests=memory=512Mi \
  --limits=memory=1Gi -n touchcli

# Step 6: Enable memory monitoring
# (Ensure metrics-server is running)
kubectl get deployment metrics-server -n kube-system
```

### Disk Pressure Response

**Symptoms**:
```
Node condition: DiskPressure=True
Pods with status: Evicted
No new pods can be scheduled
```

**Steps**:

```bash
# Step 1: Check disk usage
kubectl exec -it <pod> -n touchcli -- \
  du -sh /var/lib/postgresql/data
kubectl exec -it <pod> -n touchcli -- \
  du -sh /var/log

# Step 2: Clean up container logs (immediate)
for pod in $(kubectl get pods -n touchcli -o name); do
  kubectl exec -it $pod -n touchcli -- \
    rm -f /var/log/*.log
done

# Step 3: Clean up old data (if safe)
# PostgreSQL: Delete old logs/audit data
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "DELETE FROM agent_responses WHERE created_at < now() - interval '90 days';"

# Step 4: Increase node disk (within 30 min)
# Option A: Add new node
kubectl scale nodepool default --num-nodes=4

# Option B: Expand volume
kubectl patch pvc <pvc-name> -n touchcli \
  -p '{"spec":{"resources":{"requests":{"storage":"500Gi"}}}}'

# Step 5: Re-enable pod scheduling
kubectl uncordon <node-name>

# Step 6: Drain and reboot node (if necessary)
kubectl cordon <node-name>
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
# Then reboot the node
```

### Prevention & Monitoring

```bash
# 1. Set resource limits for all pods
kubectl set resources deployment/backend \
  --requests=memory=256Mi,cpu=250m \
  --limits=memory=512Mi,cpu=500m -n touchcli

# 2. Enable pod disruption budgets
kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: backend-pdb
  namespace: touchcli
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: backend
EOF

# 3. Monitor with Grafana alerts
# Create alert:
# - Memory usage > 80% of limit
# - Disk usage > 80% of capacity
# - MemoryPressure or DiskPressure on node
```

---

## 4. High Error Rate Response

### Symptom Detection

```
- Error rate >5% (or your threshold)
- Sentry alerts firing
- Prometheus query: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
```

### Quick Diagnosis (First 3 minutes)

```bash
# 1. Check error rate by endpoint
kubectl logs -f deployment/backend -n touchcli | grep "ERROR\|500"

# 2. Check Sentry for patterns
# Visit: https://sentry.io/dashboard
# Look for: same error repeated? New error type?

# 3. Check recent deployments
kubectl rollout history deployment/backend -n touchcli

# 4. Check database health
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "SELECT 1;"

# 5. Check Redis health
kubectl exec -it redis -n touchcli -- \
  redis-cli ping
```

### Common Causes & Fixes

#### Cause: Recent Bad Deployment

**Symptoms**:
```
Error rate spiked after deployment
Same error in all instances
Logs show: same traceback repeated
```

**Fix**:

```bash
# 1. Immediate: Rollback (usually sufficient)
kubectl rollout undo deployment/backend -n touchcli

# 2. Monitor error rate drop
kubectl logs -f deployment/backend -n touchcli | grep ERROR

# 3. Verify service recovers
# (Should take 1-2 minutes)

# 4. Root cause analysis (after emergency resolved)
# - Review what changed in deployment
# - Check logs from failed version
# - Add test case to prevent regression

# Prevention:
# - Enable canary deployments (deploy to 1 pod first)
# - Add smoke tests after deployment
# - Monitor error rate for 5 minutes post-deploy
```

#### Cause: Database Timeout/Slowness

**Symptoms**:
```
Error: "database connection timeout"
Error: "query exceeded max_execution_time"
```

**Fix**:

```bash
# 1. Check database response time
kubectl exec -it postgres -n touchcli -- \
  time psql -U postgres -d touchcli -c "SELECT COUNT(*) FROM customers;" > /dev/null

# 2. Check for slow queries
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 5;"

# 3. Kill long-running queries (if necessary)
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -c \
  "SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE query_start < now() - interval '5 minutes';"

# 4. Run VACUUM ANALYZE
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "VACUUM ANALYZE;"

# 5. Restart database if stuck
kubectl rollout restart statefulset/postgres -n touchcli

# 6. Increase connection timeout in backend
kubectl set env deployment/backend \
  DB_TIMEOUT=10 -n touchcli
kubectl rollout restart deployment/backend -n touchcli
```

#### Cause: External Dependency Failure

**Symptoms**:
```
Error: "Connection refused" or "Timeout"
Affects specific endpoint (e.g., email service)
```

**Fix**:

```bash
# 1. Identify which dependency is failing
kubectl logs -f deployment/backend -n touchcli | grep ERROR | head -5

# 2. Check if it's critical
# If optional (e.g., email): Graceful degradation acceptable
# If critical (e.g., database): Declare SEV-1

# 3. Implement circuit breaker (if not present)
# Fail fast instead of retrying eternally
# Example: After 3 failures, return cached data

# 4. Increase timeout and retry logic
# If transient failure, retry with backoff
# If persistent, page engineer to investigate external service

# 5. Deploy fallback
# Use cached/stale data instead of live calls

# 6. Monitor recovery
# Once external service restored, should recover automatically
```

### Recovery Validation

```bash
# 1. Error rate should drop to <1%
# Check: rate(http_requests_total{status=~"5.."}[5m])

# 2. No new errors in Sentry
# Visit: https://sentry.io and verify no new issues

# 3. API responding normally
curl -s http://localhost:8080/health | jq .

# 4. Check availability (uptime/SLO)
# If <99.9%: Incident impacts SLO
# Requires root cause + action items
```

---

## 5. Performance Degradation Investigation

### Symptom Detection

```
- API latency: p95 > 500ms (normal <500ms)
- Database query: p95 > 50ms (normal <50ms)
- WebSocket latency: RTT > 100ms (normal <100ms)
- Customer reports slow UI
```

### Quick Diagnosis (First 5 minutes)

```bash
# 1. Check dashboard in Grafana
# Graph: HTTP Request Duration (p95)
# Graph: Database Query Duration (p95)

# 2. Check resource utilization
kubectl top pods -n touchcli
kubectl top nodes

# 3. Check active queries
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "SELECT query, query_start, wait_event
   FROM pg_stat_activity
   ORDER BY query_start;"

# 4. Check if traffic increased
# Compare current vs baseline in Prometheus:
rate(http_requests_total[5m])

# 5. Check for new slow queries
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "SELECT query, calls, mean_time FROM pg_stat_statements
   ORDER BY mean_time DESC LIMIT 10;"
```

### Investigation Path

#### Path A: Database Slow (Most Common)

```bash
# 1. Identify slow query
SELECT query, calls, mean_time, max_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 1;

# 2. Analyze query plan
EXPLAIN ANALYZE SELECT ... [the slow query];
# Look for: Sequential Scans, high cost, missing indexes

# 3. Fix options:
# A) Add index
CREATE INDEX idx_name ON table(column);

# B) Update statistics
ANALYZE table;

# C) Rewrite query
# Simplify/optimize logic

# 4) Verify improvement
# Run query again, check new timing
EXPLAIN ANALYZE SELECT ...;

# 5) Monitor in Grafana
# Latency should drop
```

#### Path B: High CPU/Memory

```bash
# 1. Identify high-resource pod
kubectl top pods -n touchcli --no-headers | sort -k2 -rn | head -1

# 2. Check if memory leak
kubectl top pods -n touchcli --watch
# Watch same pod for 5 minutes
# If steadily increasing: Memory leak

# 3) Fix memory leak
# Option A: Restart pod (temporary)
kubectl rollout restart deployment/backend -n touchcli

# Option B: Code fix (permanent)
# Review recent commits
# Add memory profiling: python -m memory_profiler

# Option C: Increase resources (if legitimately needed)
kubectl set resources deployment/backend \
  --limits=memory=1Gi,cpu=1000m -n touchcli
```

#### Path C: Network/I/O Bottleneck

```bash
# 1. Check network latency
kubectl exec -it <pod> -n touchcli -- \
  ping -c 4 postgres

# 2. Check I/O performance
kubectl exec -it <pod> -n touchcli -- \
  iostat -x 1 5

# 3. If network high latency:
# Check: Pod and database in same node/zone?
# Fix: Add node affinity to keep together

# 4) If I/O high:
# Check: Disk type (SSD vs HDD)?
# Fix: Use SSD for database
```

#### Path D: No Resource Bottleneck

```bash
# 1. Check application logs for slow operations
kubectl logs -f deployment/backend -n touchcli | grep "slow\|duration"

# 2. Check if specific endpoint slow
# Use: curl -w "@curl-format.txt" http://endpoint

# 3) Profile code
# Python: py-spy, cProfile
# Node: clinic.js

# 4) Identify bottleneck
# If: I/O slow → Optimize queries
# If: CPU slow → Optimize algorithm
# If: External API slow → Add timeout/cache

# 5) Implement fix
# Deploy optimized code
# Monitor: Latency should drop
```

### Prevention & Monitoring

```bash
# 1. Set performance SLOs
SLO: p95 latency < 500ms, p99 < 1s

# 2. Add monitoring alerts
# Alert if p95 > 500ms
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: backend-latency-alert
  namespace: touchcli
spec:
  groups:
  - name: backend
    interval: 30s
    rules:
    - alert: HighLatency
      expr: |
        histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
      for: 5m
      annotations:
        summary: High API latency detected
EOF

# 3. Load testing before production
# Use: locust, k6, or Apache Bench
# Target: 1000 concurrent users
# Verify: p95 latency acceptable

# 4) Continuous monitoring
# Weekly: Review slow query logs
# Monthly: Capacity planning
# Quarterly: Performance optimization
```

---

## 6. WebSocket Connection Issues

### Symptom Detection

```
- Real-time messages not updating
- WebSocket connection failing
- Error: "WebSocket is closed"
- Error: "CORS policy blocked"
```

### Quick Diagnosis

```bash
# 1. Check WebSocket endpoint accessible
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  http://localhost:8080/ws

# 2. Check gateway logs
kubectl logs -f deployment/gateway -n touchcli | grep -i "websocket\|upgrade"

# 3. Check backend logs for connection details
kubectl logs -f deployment/backend -n touchcli | grep -i "ws\|websocket"

# 4. Check CORS configuration
kubectl get deployment gateway -n touchcli -o yaml | grep -i cors

# 5. Check firewall/network policies
kubectl get networkpolicy -n touchcli
```

### Common Causes & Fixes

#### Cause: CORS Policy Blocked

**Symptoms**:
```
Error: "Access to XMLHttpRequest blocked by CORS policy"
Or: "The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*'"
```

**Fix**:

```bash
# 1. Check gateway CORS configuration
kubectl get configmap -n touchcli gateway-config -o yaml | grep -i cors

# 2. Verify frontend origin allowed
# Should include: localhost:3000, yourdomain.com

# 3. If missing, update gateway
# Edit /backend/go/main.go:
CORS_ALLOWED_ORIGINS := []string{
  "http://localhost:3000",
  "http://localhost:8000",
  "https://touchcli.example.com",
}

# 4) Rebuild and redeploy
docker build -t myregistry/gateway:v2 ./backend/go
docker push myregistry/gateway:v2
kubectl set image deployment/gateway gateway=myregistry/gateway:v2 -n touchcli
```

#### Cause: Connection Timeout

**Symptoms**:
```
WebSocket hangs for 30+ seconds
Then disconnects
```

**Fix**:

```bash
# 1. Check gateway logs for timeout errors
kubectl logs -f deployment/gateway -n touchcli

# 2. Increase timeouts (if legitimate)
# Edit gateway configuration:
writeWait = 30 * time.Second    # Wait for write to complete
pongWait = 60 * time.Second     # Wait for pong response

# 3. Restart gateway
kubectl rollout restart deployment/gateway -n touchcli

# 4. Test connection
# Frontend should connect successfully
```

#### Cause: Message Queue Overflow

**Symptoms**:
```
WebSocket connected but messages delayed
Backend has high memory/CPU
Error: "queue full" or "buffer exceeded"
```

**Fix**:

```bash
# 1. Check message queue size
kubectl exec -it redis -n touchcli -- \
  redis-cli LLEN "queue:messages"

# 2. Identify backlog
# If >10000 messages queued: Processing is slow

# 3. Scale up backend
kubectl scale deployment/backend --replicas=5 -n touchcli

# 4) Or restart to flush queue
kubectl rollout restart deployment/backend -n touchcli

# 5) Monitor recovery
# Latency should drop as queue clears
```

---

## 7. Complete Service Outage

### Severity: SEV-1 (Critical)

### Initial Response (First 2 minutes)

```bash
# 1. Page all engineers immediately
# PagerDuty: Trigger SEV-1 incident

# 2. Verify outage is real
curl -s http://localhost:3000 | head -10
curl -s http://localhost:8080/health | jq .

# 3. Check system status
kubectl get pods -n touchcli
kubectl get nodes

# 4. Start war room
# Slack: #incidents channel
# Zoom: Join emergency bridge

# 5. Assign roles:
# - Incident Commander: Drives timeline + decisions
# - Engineer 1: Investigates root cause
# - Engineer 2: Monitors metrics + health
# - Communications: Updates status page + customers
```

### Parallel Investigation Tracks

**Track A: Application Health**

```bash
# Check each service
kubectl describe deployment backend -n touchcli
kubectl describe deployment frontend -n touchcli
kubectl describe deployment gateway -n touchcli

# Check recent events
kubectl get events -n touchcli --sort-by='.lastTimestamp' | tail -20

# Check for errors
kubectl logs -f deployment/backend -n touchcli
```

**Track B: Infrastructure Health**

```bash
# Check node status
kubectl get nodes
kubectl top nodes
kubectl describe node <node-name> | grep Conditions

# Check PVC/storage
kubectl get pvc -n touchcli
kubectl get pv

# Check networking
kubectl get service -n touchcli
kubectl get ingress -n touchcli
```

**Track C: External Dependencies**

```bash
# Check database
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -c "SELECT 1;"

# Check Redis
kubectl exec -it redis -n touchcli -- \
  redis-cli ping

# Check external APIs (if used)
curl -s https://external-api.example.com/health
```

### Recovery Steps (Priority Order)

**Option 1: Restart Service** (Time: 2-5 min)

```bash
kubectl rollout restart deployment/backend -n touchcli
kubectl rollout restart deployment/frontend -n touchcli
kubectl rollout restart deployment/gateway -n touchcli

# Monitor for recovery
kubectl get pods -n touchcli --watch
```

**Option 2: Rollback Deployment** (Time: 2-5 min)

```bash
# If recent deployment is suspect
kubectl rollout undo deployment/backend -n touchcli
kubectl rollout undo deployment/frontend -n touchcli

# Monitor for recovery
kubectl rollout status deployment/backend -n touchcli
```

**Option 3: Scale Down & Recover** (Time: 5-10 min)

```bash
# Hard reset: Kill all pods, restart fresh
kubectl scale deployment/backend --replicas=0 -n touchcli
sleep 30
kubectl scale deployment/backend --replicas=2 -n touchcli

# Monitor recovery
kubectl get pods -n touchcli --watch
```

**Option 4: Drain Node** (Time: 10-15 min, Last resort)

```bash
# If node is stuck
kubectl cordon <node-name>
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Kubernetes reschedules pods on healthy nodes
# Monitor recovery
kubectl get pods -n touchcli --watch
```

### Recovery Validation

```bash
# 1. Service responding to requests
curl -s http://localhost:3000 | grep -q "<!DOCTYPE"
echo "Frontend OK"

curl -s http://localhost:8080/health | grep -q "healthy"
echo "Gateway OK"

# 2) Database connected
kubectl exec -it postgres -n touchcli -- \
  psql -U postgres -d touchcli -c "SELECT COUNT(*) FROM users;"
echo "Database OK"

# 3) WebSocket working
# (Use browser console)
# ws = new WebSocket('ws://localhost:8080/ws')
# ws.onopen = () => console.log('WebSocket OK')

# 4) Declare service recovered
# - Service status page: OPERATIONAL
# - Notify stakeholders
# - Begin incident review
```

### Post-Incident (After Service Recovers)

```
1. Root Cause Analysis (RCA)
   - What failed?
   - Why did it fail?
   - When did we detect?
   - How long until recovery?

2. Action Items
   - Prevent recurrence
   - Improve detection
   - Improve response time

3. Timeline
   - 00:00 - Incident started
   - 00:05 - Detected
   - 00:07 - Incident commander assigned
   - 00:10 - Root cause identified
   - 00:15 - Service recovered
   - 00:20 - Status page updated

4) Document & Share
   - Post to: #incidents channel
   - Invite: all engineers to review
   - Action items assigned with due dates
```

---

## 8. Data Corruption/Loss

### Severity: SEV-1 (Critical)

### Immediate Actions (First 2 minutes)

```bash
# 1. STOP all write operations
kubectl scale deployment/backend --replicas=0 -n touchcli
# This prevents further corruption

# 2. Take database offline for inspection
kubectl scale statefulset/postgres --replicas=0 -n touchcli

# 3. Page all engineers + database admin
# PagerDuty: Trigger SEV-1 incident

# 4. Do NOT attempt fixes yet
# Corruption investigation required
```

### Diagnosis

```bash
# 1. Check database integrity (offline)
kubectl scale statefulset/postgres --replicas=1 -n touchcli
kubectl wait --for=condition=ready pod postgres-0 -n touchcli

# 2) Run database check
kubectl exec -it postgres-0 -n touchcli -- \
  psql -U postgres -d touchcli -c "
  SELECT schemaname, tablename, n_live_tup
  FROM pg_stat_user_tables
  WHERE n_live_tup > 1000000;" | head -20

# 3) Check replication status (if using replication)
kubectl exec -it postgres-0 -n touchcli -- \
  psql -U postgres -c "
  SELECT slot_name, restart_lsn, confirmed_flush_lsn
  FROM pg_replication_slots;"

# 4) Check WAL (Write-Ahead Logs)
ls -la /var/lib/postgresql/data/pg_wal/ | tail -20
```

### Recovery Path

**Path A: Restore from Backup** (Recommended if possible)

```bash
# 1. List available backups
ls -lh /backups/ | head -10

# 2. Restore to point-before-corruption
# Determine when corruption started:
gunzip -c /backups/touchcli-2026-03-01-020000.sql.gz | \
  psql -U postgres -d touchcli

# 3. Verify data after restore
kubectl exec -it postgres-0 -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "SELECT COUNT(*) FROM users;"

# 4. Rebuild indexes
kubectl exec -it postgres-0 -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "REINDEX DATABASE touchcli;"

# 5. Bring service back online
kubectl scale deployment/backend --replicas=2 -n touchcli

# 6. Declare recovery complete
```

**Path B: Partial Recovery** (If backup unavailable)

```bash
# 1. Export uncorrupted tables
kubectl exec -it postgres-0 -n touchcli -- \
  pg_dump -U postgres -d touchcli -t "uncorrupted_table" > export.sql

# 2. Drop corrupted table
kubectl exec -it postgres-0 -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "DROP TABLE corrupted_table CASCADE;"

# 3. Restore from backup (full)
# Then restore specific tables from export

# 4. Verify data integrity
kubectl exec -it postgres-0 -n touchcli -- \
  psql -U postgres -d touchcli -c \
  "SELECT COUNT(*) FROM restored_table;"

# 5) Bring service online
```

### Post-Recovery

```
1. Notify affected users
   - When corruption happened
   - What data lost
   - Steps being taken

2. Audit changes made during recovery
   - What was restored?
   - What was lost?
   - Any manual edits needed?

3. Implement fixes
   - Add database integrity checks (PRAGMA)
   - Increase backup frequency
   - Implement point-in-time recovery (PITR)

4) Update runbooks
   - Document what worked
   - Update recovery procedures
   - Share lessons learned
```

---

## Incident Severity Matrix

| Severity | Symptoms | Response Time | Escalation |
|----------|----------|----------------|------------|
| **SEV-4** | Minor bug, cosmetic issue | Next business day | Engineer |
| **SEV-3** | Feature broken, workaround available | 4 hours | Team Lead |
| **SEV-2** | Service degradation, some users affected | 1 hour | Manager + Team Lead |
| **SEV-1** | Service outage, all users affected | 15 minutes | VP + All Engineers |

---

## Quick Command Reference

```bash
# Service Health
kubectl get pods -n touchcli
kubectl get nodes
kubectl top nodes
kubectl top pods -n touchcli

# Logs
kubectl logs -f deployment/backend -n touchcli
kubectl logs <pod-name> --previous -n touchcli
docker-compose logs -f

# Restarts
kubectl rollout restart deployment/backend -n touchcli
docker-compose restart backend

# Rollback
kubectl rollout undo deployment/backend -n touchcli
kubectl rollout rollback deployment/backend -n touchcli

# Database
kubectl exec -it postgres-0 -n touchcli -- psql -U postgres -d touchcli
psql -h localhost -U touchcli_user -d touchcli

# Backup/Restore
./scripts/database-backup.sh
psql touchcli < /backups/touchcli-TIMESTAMP.sql

# Scaling
kubectl scale deployment/backend --replicas=5 -n touchcli

# Secrets
kubectl get secrets -n touchcli
kubectl describe secret sealed-secrets -n touchcli
```

---

## Incident Command System (ICS)

**During Major Incidents**:

- **Incident Commander**: Makes decisions, drives timeline
- **Deputy IC**: Backfill for IC if needed
- **Technical Lead**: Deep investigates root cause
- **Communications**: Updates stakeholders, status page
- **Scribe**: Documents timeline, decisions, action items

**Incident Channel**: #incidents in Slack
**Bridge**: Zoom or war room
**Duration**: Continues until recovery + RCA complete

---

## Conclusion

These runbooks provide step-by-step guidance for the most common incident scenarios. Key principles:

1. **First 5 minutes**: Diagnose and stabilize
2. **Next 15 minutes**: Implement recovery
3. **Next hour**: Validate recovery and prevent recurrence
4. **Next day**: RCA and action items

Always: **Document**, **communicate**, **automate**, **prevent**

For additional operational procedures, see **OPERATIONS_GUIDE.md**.
