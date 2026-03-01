# Kubernetes Deployment Manifests

This directory contains Kubernetes manifests for deploying TouchCLI to a Kubernetes cluster.

## Files

- **namespace.yaml** - Kubernetes namespace (touchcli)
- **configmap.yaml** - Non-sensitive configuration data
- **secrets.yaml** - Sensitive data (update with real values!)
- **frontend-deployment.yaml** - Frontend (React SPA) deployment and service
- **backend-deployment.yaml** - Backend (Agent Service) deployment and service
- **gateway-deployment.yaml** - Gateway (WebSocket proxy) deployment and service
- **ingress.yaml** - Ingress configuration for HTTPS routing

## Prerequisites

1. **Kubernetes Cluster** (v1.24+)
   ```bash
   # Install kubectl
   # Configure kubeconfig for your cluster
   kubectl cluster-info
   ```

2. **Ingress Controller** (Nginx)
   ```bash
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm install nginx-ingress ingress-nginx/ingress-nginx
   ```

3. **Certificate Manager** (Let's Encrypt)
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
   ```

4. **Database & Redis** (managed services or deployed separately)
   - PostgreSQL 15+
   - Redis 7+

5. **Container Registry** (push images there)
   - Docker Hub, ECR, GCR, etc.

## Deployment Steps

### 1. Prepare Environment

```bash
# Build and push Docker images
docker build -t yourregistry/frontend:latest -f ../frontend/Dockerfile ..
docker build -t yourregistry/agent-service:latest -f ../backend/python/Dockerfile ..
docker build -t yourregistry/gateway:latest -f ../backend/go/Dockerfile ..

docker push yourregistry/frontend:latest
docker push yourregistry/agent-service:latest
docker push yourregistry/gateway:latest
```

### 2. Update Secrets

Edit `secrets.yaml` with real values:
```yaml
DATABASE_URL: "postgresql://user:password@postgres.example.com:5432/db"
REDIS_URL: "redis://redis.example.com:6379"
JWT_SECRET: "your-secure-jwt-secret-here"
```

For production, use sealed-secrets or Vault:
```bash
kubectl create secret generic touchcli-secrets \
  --from-literal=DATABASE_URL='...' \
  --dry-run=client \
  -o yaml | kubeseal -f - > secrets-sealed.yaml
```

### 3. Deploy Services

```bash
# Use the deployment script
../scripts/deploy-kubernetes.sh

# Or deploy manually
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f gateway-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml
```

### 4. Verify Deployment

```bash
# Check all resources created
kubectl get all -n touchcli

# Check pod status
kubectl get pods -n touchcli -o wide

# Check services
kubectl get svc -n touchcli

# Check ingress
kubectl get ingress -n touchcli

# View logs
kubectl logs deployment/agent-service -n touchcli -f
```

## Configuration

### Environment Variables

Variables are loaded from:
1. **ConfigMap** (configmap.yaml) - Non-sensitive config
2. **Secrets** (secrets.yaml) - Sensitive data

Example adding new variable:
```yaml
# In configmap.yaml
data:
  NEW_VAR: "value"

# Or for secrets
stringData:
  NEW_SECRET: "sensitive-value"
```

Then reference in deployment:
```yaml
envFrom:
- configMapRef:
    name: touchcli-config
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: touchcli-secrets
      key: DATABASE_URL
```

## Scaling

### Manual Scaling

```bash
# Scale frontend to 5 replicas
kubectl scale deployment frontend --replicas=5 -n touchcli

# Scale backend to 3 replicas
kubectl scale deployment agent-service --replicas=3 -n touchcli
```

### Autoscaling

```bash
# Create HorizontalPodAutoscaler
kubectl autoscale deployment agent-service \
  --min=2 --max=10 \
  --cpu-percent=80 \
  -n touchcli

# View autoscaler status
kubectl get hpa -n touchcli
```

## Upgrades

### Rolling Update

```bash
# Update image for new version
kubectl set image deployment/frontend \
  frontend=yourregistry/frontend:v2 \
  -n touchcli

# Watch the rollout
kubectl rollout status deployment/frontend -n touchcli

# Rollback if needed
kubectl rollout undo deployment/frontend -n touchcli
```

## Monitoring

### Health Checks

Kubernetes automatically manages health using:
- **livenessProbe** - Restarts unhealthy pods
- **readinessProbe** - Removes from load balancer if not ready
- **startupProbe** - Waits for pod to start

### View Metrics

```bash
# Pod resource usage
kubectl top pods -n touchcli

# Node resource usage
kubectl top nodes

# Custom metrics (requires metrics-server)
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/touchcli/pods
```

### Logs

```bash
# Pod logs
kubectl logs pod/<pod-name> -n touchcli

# Deployment logs (all pods)
kubectl logs -l app=agent-service -n touchcli

# Follow logs
kubectl logs -f deployment/agent-service -n touchcli

# Multiple pod logs
kubectl logs -l app=gateway -n touchcli --all-containers=true
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod <pod-name> -n touchcli

# Check pod logs
kubectl logs <pod-name> -n touchcli

# Check resource requests
kubectl describe node
```

### Database Connection Issues

```bash
# Test database connectivity from pod
kubectl exec <pod-name> -n touchcli -- \
  psql -h postgres.example.com -U user -d database -c "SELECT 1"

# Check environment variables
kubectl exec <pod-name> -n touchcli -- env | grep DATABASE
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress touchcli-ingress -n touchcli

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/nginx-ingress-ingress-nginx-controller

# Test ingress
curl -v -H "Host: touchcli.io" http://ingress-ip/
```

## Security Considerations

1. **Secrets Management**
   - ❌ Don't commit secrets.yaml with real values
   - ✅ Use sealed-secrets or Vault
   - ✅ Use Kubernetes RBAC for access control
   - ✅ Enable encryption at rest

2. **Network Policies**
   - Restrict pod-to-pod communication
   - Only allow necessary ingress/egress
   - Use network policies for zero-trust

3. **Pod Security**
   - Run as non-root user
   - Use read-only root filesystem
   - Disable privileged containers

4. **Image Security**
   - Use specific image tags (not `latest`)
   - Scan images for vulnerabilities
   - Use private registry for sensitive images

## Backup & Disaster Recovery

### Database Backups

```bash
# Manual backup
kubectl exec <postgres-pod> -- \
  pg_dump -U user database > backup.sql

# Restore from backup
kubectl exec -i <postgres-pod> -- \
  psql -U user database < backup.sql
```

### etcd Backup (cluster config)

```bash
# Backup etcd
kubectl get --all-namespaces -o json all > cluster-backup.json

# Restore from backup
kubectl apply -f cluster-backup.json
```

## Performance Optimization

1. **Resource Limits**
   - Set appropriate CPU/memory limits
   - Use LimitRanges for namespace defaults

2. **Caching**
   - Redis for application cache
   - CDN for static assets

3. **Horizontal Scaling**
   - Use HPA for autoscaling
   - Monitor and adjust replica counts

4. **Database**
   - Use managed PostgreSQL with backups
   - Enable connection pooling
   - Index frequently queried columns

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Ingress Nginx](https://kubernetes.github.io/ingress-nginx/)
- [Cert Manager](https://cert-manager.io/)
- [PostgreSQL Kubernetes](https://www.postgresql.org/docs/current/)

## Support

See `../DEPLOYMENT.md` for detailed deployment guide.
