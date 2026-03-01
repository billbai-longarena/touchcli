# TouchCLI Observability Stack

## Overview

TouchCLI implements a production-grade observability stack with three pillars:

1. **Prometheus** - Metrics collection and time-series storage
2. **Grafana** - Metrics visualization and dashboards
3. **Sentry** - Error tracking and performance monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Applications                                                    │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ Backend (FastAPI)    │  │ Gateway (Go)         │            │
│  │                      │  │                      │            │
│  │ /metrics (Prometheus)│  │ /metrics (Prometheus)│            │
│  │ Sentry SDK           │  │                      │            │
│  └──────────┬───────────┘  └──────────┬───────────┘            │
│             │                         │                        │
└─────────────┼─────────────────────────┼────────────────────────┘
              │                         │
              ▼                         ▼
     ┌───────────────────────────────────────┐
     │   Prometheus Scraper                  │
     │   (Targets: :8000/metrics, :8080/m)   │
     │   Scrape interval: 15s                │
     │   15-day retention                    │
     └────────────────┬──────────────────────┘
                      │
                      ▼
     ┌───────────────────────────────────┐
     │  Prometheus Time-Series DB        │
     │  - http_requests_total            │
     │  - http_request_duration_seconds  │
     │  - db_query_duration_seconds      │
     │  - agent_responses_total          │
     │  - agent_response_time_seconds    │
     └──────────┬──────────────────────┬─┘
                │                      │
       ┌────────▼──────┐      ┌────────▼──────────────┐
       │               │      │                       │
       ▼               ▼      ▼                       ▼
    ┌──────┐      ┌────────┐ ┌──────┐          ┌───────────┐
    │Grafana      │Alerts  │ │Logs  │          │Sentry     │
    │Dashboard    │(Rules) │ │(ELK) │          │Errors     │
    └──────┘      └────────┘ └──────┘          └───────────┘

Sentry SDK (Async)
├─ Error Tracking
├─ Performance Monitoring
├─ Distributed Tracing
└─ User Context
```

## Installation

### Prerequisites

- Kubernetes cluster with persistent storage (for Prometheus)
- Sentry account (https://sentry.io or self-hosted)
- Docker images built with Prometheus metrics endpoints

### Step 1: Create Monitoring Namespace

```bash
kubectl apply -f k8s/monitoring-namespace.yaml
```

### Step 2: Deploy Prometheus

```bash
kubectl apply -f k8s/prometheus-config.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment/prometheus -n monitoring
```

### Step 3: Deploy Grafana

```bash
# First, create admin password secret
kubectl create secret generic grafana-admin \
  -n monitoring \
  --from-literal=password='your-secure-password'

# Deploy
kubectl apply -f k8s/grafana-config.yaml

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s \
  deployment/grafana -n monitoring
```

### Step 4: Add Sentry Configuration

```bash
# Add Sentry DSN to secrets
kubectl set env deployment/agent-service \
  -n touchcli \
  SENTRY_DSN='https://key@sentry.io/project-id'

# Optional: Configure sample rate
kubectl set env deployment/agent-service \
  -n touchcli \
  SENTRY_TRACES_SAMPLE_RATE='0.1'
```

## Prometheus Configuration

### Scrape Targets

Prometheus automatically discovers and scrapes these targets:

- **Backend**: `http://agent-service:8000/metrics`
  - Scrape interval: 15s
  - Port: 8000

- **Gateway**: `http://gateway:8080/metrics`
  - Scrape interval: 15s
  - Port: 8080

- **Kubernetes Nodes**: Auto-discovered
- **Kubernetes Pods**: Auto-discovered (with annotations)

### Metrics Collected

#### HTTP Request Metrics

```
# Total requests (counter)
http_requests_total{method="GET", endpoint="/health", status="200"}

# Request duration histogram
http_request_duration_seconds_bucket{method="POST", endpoint="/messages", le="0.1"}
http_request_duration_seconds_sum{method="POST", endpoint="/messages"}
http_request_duration_seconds_count{method="POST", endpoint="/messages"}
```

#### Database Metrics

```
# Query duration histogram
db_query_duration_seconds_bucket{operation="SELECT", le="0.01"}
db_query_duration_seconds_sum{operation="SELECT"}
db_query_duration_seconds_count{operation="SELECT"}
```

#### Agent Metrics

```
# Agent responses (counter)
agent_responses_total{status="success", confidence_level="high"}
agent_responses_total{status="failure", confidence_level="unknown"}

# Agent response time (histogram)
agent_response_time_seconds_bucket{le="1.0"}
agent_response_time_seconds_sum
agent_response_time_seconds_count
```

### Data Retention

- **Retention Period**: 30 days
- **Storage Location**: `/prometheus` (emptyDir)
- **For Production**: Use persistent volume

```yaml
# Update prometheus-config.yaml
volumes:
- name: prometheus-data
  persistentVolumeClaim:
    claimName: prometheus-pvc
```

## Grafana Dashboards

### Access Grafana

```bash
# Port-forward to local machine
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Open browser
open http://localhost:3000

# Default credentials
username: admin
password: (set during installation)
```

### Metrics Visualizations

#### API Performance Dashboard

```
Row 1: Request Rates
├─ Total requests per minute
├─ Requests by endpoint
└─ Requests by method

Row 2: Latency
├─ 95th percentile latency
├─ Average response time
└─ Max response time

Row 3: Error Rates
├─ 4xx errors per minute
├─ 5xx errors per minute
└─ Error rate % of total
```

#### Database Performance Dashboard

```
Row 1: Query Performance
├─ Average query time
├─ 95th percentile query time
└─ Slowest queries

Row 2: Query Volume
├─ Queries per second
├─ Queries by operation type
└─ Failed queries
```

#### Agent Health Dashboard

```
Row 1: Agent Responses
├─ Success vs failure rate
├─ Confidence levels
└─ Response time distribution

Row 2: Agent Performance
├─ P50, P95, P99 latency
├─ Throughput
└─ Error rate
```

### Creating Custom Dashboards

1. Log in to Grafana
2. Click "+" → "Dashboard"
3. Add panels with PromQL queries:

```promql
# Example: Request rate
rate(http_requests_total[5m])

# Example: P95 latency
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Example: Error rate
sum(rate(http_requests_total{status=~"5.."}[5m]))
```

## Sentry Error Tracking

### Configuration

Sentry is automatically initialized in the backend when `SENTRY_DSN` is set:

```python
sentry_sdk.init(
    dsn=sentry_dsn,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of requests
    environment="production",
    release="1.0.0"
)
```

### Setup Instructions

1. **Create Sentry Account**
   - Go to https://sentry.io/auth/register/
   - Create organization
   - Create project (select Python/FastAPI)

2. **Get DSN**
   - Project Settings → Client Keys (DSN)
   - Copy the DSN

3. **Add to Kubernetes Secret**
   ```bash
   kubectl set env deployment/agent-service \
     -n touchcli \
     SENTRY_DSN='https://key@sentry.io/project-id'
   ```

4. **Verify Integration**
   ```bash
   # Test error capture
   kubectl exec -it deployment/agent-service -n touchcli -- \
     python -c "import sentry_sdk; sentry_sdk.capture_exception(Exception('Test'))"
   ```

### Features

#### Automatic Error Capture

- Uncaught exceptions
- HTTP errors (5xx)
- Database errors
- Timeout errors

#### Distributed Tracing

- Request tracing across services
- Database query tracing
- External API calls

#### Performance Monitoring

- Slow HTTP requests
- Slow database queries
- Resource usage

#### Releases Tracking

- Deploy markers
- Release health
- Regression detection

### Viewing Errors

1. Log in to Sentry
2. Go to "Issues"
3. Click on error to view:
   - Stack trace
   - User context
   - Affected transactions
   - Related errors

### Alert Rules

Configure alerts in Sentry:

```
Condition 1: Error rate > 5% in last 5 minutes
Action: Send email + Slack notification

Condition 2: New issue appears
Action: Create GitHub issue + notify team

Condition 3: Regression detected
Action: Send email to on-call engineer
```

## Alerting

### Alert Rules

Configure Prometheus alert rules in `prometheus-config.yaml`:

```yaml
rule_files:
  - /etc/prometheus/alert-rules.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### Example Alert Rules

```yaml
groups:
- name: touchcli
  rules:
  # High error rate
  - alert: HighErrorRate
    expr: |
      (
        sum(rate(http_requests_total{status=~"5.."}[5m]))
        /
        sum(rate(http_requests_total[5m]))
      ) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"

  # High latency
  - alert: HighLatency
    expr: |
      histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1.0
    for: 10m
    annotations:
      summary: "High request latency detected"

  # Pod memory usage
  - alert: PodMemoryUsage
    expr: |
      container_memory_usage_bytes{pod=~"agent-service.*"} > 900000000
    for: 5m
    annotations:
      summary: "Pod memory usage above 900MB"
```

## Best Practices

### Metrics

1. **Use descriptive names**
   - `http_request_duration_seconds` (good)
   - `request_time` (poor)

2. **Include relevant labels**
   ```python
   Counter('requests_total', 'Total requests',
           ['method', 'endpoint', 'status'])
   ```

3. **Use appropriate metric types**
   - Counter: monotonically increasing (requests, errors)
   - Gauge: value that goes up/down (memory, connections)
   - Histogram: request duration, response size
   - Summary: percentiles (deprecated, use histogram)

4. **Set appropriate scrape intervals**
   - Default: 15 seconds
   - For high-frequency metrics: 5 seconds
   - For low-frequency metrics: 60 seconds

### Error Tracking

1. **Set environment context**
   ```python
   sentry_sdk.set_tag("deployment", "production")
   sentry_sdk.set_context("user", {"id": user_id})
   ```

2. **Use breadcrumbs for context**
   ```python
   sentry_sdk.add_breadcrumb(
       message="Database query executed",
       category="database",
       level="info"
   )
   ```

3. **Set appropriate sample rates**
   - Development: 100% (1.0)
   - Staging: 50% (0.5)
   - Production: 10% (0.1)

4. **Monitor sensitive operations**
   - Login attempts
   - Payment processing
   - Database migrations

### Dashboard Design

1. **Organize by use case**
   - API Performance
   - Database Health
   - Agent Health
   - Infrastructure

2. **Use consistent time ranges**
   - Last 6 hours for current operations
   - Last 7 days for trends
   - Last 30 days for capacity planning

3. **Set meaningful thresholds**
   - SLA targets (e.g., p99 < 500ms)
   - Error budgets (e.g., 99.9% uptime)
   - Resource limits (e.g., < 80% CPU)

## Troubleshooting

### Prometheus

**No metrics collected**:
```bash
# Verify targets
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
# Visit http://localhost:9090/targets

# Check scrape configs
kubectl get configmap prometheus-config -n monitoring -o yaml
```

**High disk usage**:
```bash
# Check retention
kubectl logs -n monitoring prometheus-0 | grep retention

# Reduce retention period
kubectl set env statefulset/prometheus \
  -n monitoring \
  RETENTION='7d'
```

### Grafana

**Can't connect to Prometheus**:
```bash
# Test connection
kubectl exec -it grafana-xxx -n monitoring -- \
  curl http://prometheus:9090/-/ready

# Check datasource configuration
kubectl get secret grafana-datasources -n monitoring -o yaml
```

**Dashboard not loading**:
```bash
# Check Grafana logs
kubectl logs -n monitoring deployment/grafana

# Restart Grafana
kubectl rollout restart deployment/grafana -n monitoring
```

### Sentry

**Errors not appearing**:
```bash
# Verify DSN
echo $SENTRY_DSN

# Test manually
python -c "import sentry_sdk; sentry_sdk.init('$SENTRY_DSN'); sentry_sdk.capture_exception(Exception('test'))"

# Check network connectivity
kubectl exec -it agent-service-xxx -n touchcli -- \
  curl https://sentry.io/api/0/
```

**High event volume**:
```bash
# Reduce sample rate
kubectl set env deployment/agent-service \
  -n touchcli \
  SENTRY_TRACES_SAMPLE_RATE='0.01'

# Filter errors
# In Sentry: Filters → Inbound Filters → Browser Extensions, etc.
```

## Maintenance

### Daily

- Review Grafana dashboards
- Check for alert notifications
- Monitor error rate in Sentry

### Weekly

- Review metrics trends
- Adjust alert thresholds if needed
- Check disk usage (Prometheus)

### Monthly

- Review Sentry performance
- Optimize slow queries
- Update dashboards with new metrics

## Integration with Incident Management

### PagerDuty Integration

1. In Sentry: Integrations → PagerDuty
2. Create incident when error rate > 10%
3. Auto-escalate if not resolved in 30 min

### Slack Notifications

```yaml
# In Sentry alert rules
Action: Send to Slack channel #alerts
Message: "{{error.title}} - {{count}} occurrences"
```

### GitHub Issue Creation

```yaml
# Auto-create issues for regressions
Condition: Regression detected
Action: Create GitHub issue with stack trace
Labels: bug, regression, severity-high
```

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Sentry Documentation](https://docs.sentry.io/)
- [OpenTelemetry](https://opentelemetry.io/)
