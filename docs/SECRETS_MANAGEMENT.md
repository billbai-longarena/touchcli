# TouchCLI Secrets Management with Sealed Secrets

## Overview

TouchCLI uses **Sealed Secrets** for secure secret management in Kubernetes. Sealed Secrets encrypts secrets at the cluster level, allowing safe storage of encrypted secrets in Git repositories while maintaining strong security guarantees.

## Architecture

### How Sealed Secrets Works

```
┌─────────────────────────────────────────────────────────────────┐
│ Developer Laptop                                                │
│                                                                 │
│  .env.production (plaintext, NEVER committed)                 │
│         ↓ (kubeseal encrypts)                                 │
│  sealed-secrets-touchcli.yaml (encrypted, SAFE to commit)   │
└────────────────────────────────────────────────────────────────┘
                               ↓
┌────────────────────────────────────────────────────────────────┐
│ Kubernetes Cluster                                             │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ sealed-secrets namespace                                │ │
│  │                                                          │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │ Sealed Secrets Controller                          │ │ │
│  │  │ - Manages encryption/decryption                   │ │ │
│  │  │ - Watches for SealedSecret CRD                    │ │ │
│  │  │ - Automatically creates Secret resources          │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                               ↓                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ touchcli namespace                                       │ │
│  │                                                          │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │ SealedSecret: touchcli-secrets (encrypted)         │ │ │
│  │  │   - Stored in etcd (encrypted)                    │ │ │
│  │  │   - Only Sealed Secrets controller can decrypt    │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │ Secret: touchcli-secrets (decrypted)              │ │ │
│  │  │   - Created by controller                         │ │ │
│  │  │   - Used by Pod                                   │ │ │
│  │  │   - Exists only in memory                         │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │ Pod: touchcli-backend                             │ │ │
│  │  │   - Mounts secret as environment variables        │ │ │
│  │  │   - Uses: DATABASE_URL, REDIS_URL, etc.          │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## Installation

### Step 1: Install kubeseal CLI

**macOS (Homebrew)**:
```bash
brew install kubeseal
```

**Linux**:
```bash
curl -L -o kubeseal.tar.gz \
  https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/kubeseal-0.18.0-linux-amd64.tar.gz
tar xfz kubeseal.tar.gz
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

**Verify Installation**:
```bash
kubeseal --version
```

### Step 2: Deploy Sealed Secrets Controller to Cluster

```bash
# First, ensure you're connected to your cluster
kubectl cluster-info

# Deploy the controller
kubectl apply -f k8s/sealed-secrets-controller.yaml

# Verify deployment
kubectl get deployment -n sealed-secrets sealed-secrets-controller
kubectl logs -n sealed-secrets -l app.kubernetes.io/name=sealed-secrets
```

### Step 3: Verify Controller is Ready

```bash
# Wait for controller to be ready
kubectl wait --for=condition=available --timeout=300s \
  deployment/sealed-secrets-controller -n sealed-secrets

# Test sealing capability
kubeseal --fetch-cert -n sealed-secrets
```

## Creating Sealed Secrets

### Option 1: Interactive Setup (Recommended)

```bash
./scripts/seal-secrets.sh --interactive
```

This will:
1. Verify all dependencies
2. Check cluster connection
3. Ensure Sealed Secrets controller is running
4. Guide you through the sealing process
5. Create the sealed secret file

### Option 2: Manual Command

```bash
# 1. Create environment file with actual values
cp .env.production .env.production.local

# Edit with actual secrets
nano .env.production.local

# 2. Create temporary secret manifest
cat > /tmp/secret.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: touchcli-secrets
  namespace: touchcli
type: Opaque
stringData:
$(grep -v '^#' .env.production.local | grep -v '^$' | sed 's/=/: "/' | sed 's/"$/""/')
EOF

# 3. Seal the secret
kubeseal -f /tmp/secret.yaml -w k8s/sealed-secrets-touchcli.yaml \
  --scope namespace -n touchcli

# 4. Clean up plaintext
rm /tmp/secret.yaml .env.production.local
```

### Option 3: From Environment File

```bash
./scripts/seal-secrets.sh --seal .env.production k8s/sealed-secrets-touchcli.yaml
```

## Deploying Sealed Secrets

### Apply to Cluster

```bash
# Verify the sealed secret first
./scripts/seal-secrets.sh --verify k8s/sealed-secrets-touchcli.yaml

# Apply to cluster
./scripts/seal-secrets.sh --apply k8s/sealed-secrets-touchcli.yaml

# Or manually:
kubectl apply -f k8s/sealed-secrets-touchcli.yaml
```

### Verify Decryption

```bash
# Check if secret was created
kubectl get secret touchcli-secrets -n touchcli

# View secret keys (not values)
kubectl get secret touchcli-secrets -n touchcli -o jsonpath='{.data}' | jq 'keys'

# Test that secret is accessible
kubectl run -it --rm debug --image=ubuntu:latest --restart=Never -- \
  sh -c 'echo $DATABASE_URL' < /dev/null 2>&1 | grep -v "Pod \"debug\" does not exist"
```

## Referencing Secrets in Deployments

### Environment Variables

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: touchcli-backend
  namespace: touchcli
spec:
  template:
    spec:
      containers:
      - name: backend
        image: touchcli-backend:latest
        env:
        # From Secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: touchcli-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: touchcli-secrets
              key: REDIS_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: touchcli-secrets
              key: JWT_SECRET
        # From ConfigMap
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: touchcli-config
              key: LOG_LEVEL
```

### Volume Mount

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: touchcli-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        volumeMounts:
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true
      volumes:
      - name: secrets
        secret:
          secretName: touchcli-secrets
          defaultMode: 0400
```

## Security Considerations

### Best Practices

1. **Never commit plaintext secrets**
   - Use `.env.production` in `.gitignore`
   - Only commit encrypted `sealed-secrets-*.yaml` files

2. **Rotate secrets regularly**
   - Update sealed secrets monthly
   - Keep encryption keys backed up

3. **Use namespace scoping**
   - Sealed Secrets are scoped to namespace by default
   - Cannot be decrypted in different namespaces

4. **Limit RBAC access**
   - Only necessary pods should mount secrets
   - Use least privilege principle

5. **Enable audit logging**
   - Monitor secret access in Kubernetes audit logs
   - Review controller logs regularly

### Secret Encryption Keys

- Located in: `sealed-secrets` namespace
- Backed by: Kubernetes ETCD encryption (if enabled)
- Default rotation: 30 days
- Can be manually rotated with controller restart

### Backup Considerations

```bash
# Backup encryption key
kubectl get secret -n sealed-secrets -l sealedsecrets.bitnami.com/managed=true \
  -o yaml > sealed-secrets-backup.yaml

# Store backup securely (e.g., encrypted USB drive, secure vault)
# Required for disaster recovery
```

## Troubleshooting

### Controller Not Running

```bash
# Check pod logs
kubectl logs -n sealed-secrets -l app.kubernetes.io/name=sealed-secrets

# Common issues:
# 1. Insufficient resources - check node capacity
# 2. CRD not installed - verify sealed-secrets-controller.yaml applied
# 3. RBAC issues - ensure ServiceAccount has permissions
```

### Cannot Seal Secret

```bash
# Fetch public key from controller
kubeseal --fetch-cert -n sealed-secrets > my-key.crt

# If key not available:
# 1. Controller might not be ready - wait 30-60 seconds
# 2. Network connectivity issue
# 3. Wrong namespace specified
```

### Secret Not Decrypting

```bash
# Check sealed secret status
kubectl describe sealedsecret touchcli-secrets -n touchcli

# Check controller events
kubectl get events -n sealed-secrets --sort-by='.lastTimestamp'

# Verify secret was created
kubectl get secret touchcli-secrets -n touchcli -o yaml

# Check pod environment
kubectl exec -it <pod-name> -n touchcli -- env | grep DATABASE_URL
```

### Sealed Secret in Wrong Namespace

Sealed Secrets are scoped to namespace. To reseal for different namespace:

```bash
# Original namespace
kubeseal -f secret.yaml -w sealed-secret-ns1.yaml \
  --scope namespace -n namespace1

# Different namespace
kubeseal -f secret.yaml -w sealed-secret-ns2.yaml \
  --scope namespace -n namespace2
```

## GitOps Workflow

### Example: Flux CD Integration

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: touchcli
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/your-org/touchcli
  ref:
    branch: main

---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: touchcli
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: touchcli
  path: ./k8s
  # Sealed Secrets will decrypt automatically
  decryption:
    provider: sops
```

## CLI Reference

### Setup

```bash
# Interactive setup
./scripts/seal-secrets.sh --interactive

# Check prerequisites
./scripts/seal-secrets.sh --check
```

### Creating Secrets

```bash
# From environment file
./scripts/seal-secrets.sh --seal .env.production k8s/sealed-secrets-touchcli.yaml

# Manual kubeseal
kubeseal -f secret.yaml -w sealed-secret.yaml --scope namespace
```

### Deployment

```bash
# Verify before applying
./scripts/seal-secrets.sh --verify k8s/sealed-secrets-touchcli.yaml

# Apply to cluster
./scripts/seal-secrets.sh --apply k8s/sealed-secrets-touchcli.yaml
```

## Migration Path

For existing deployments using plaintext secrets:

### Step 1: Install Sealed Secrets Controller

```bash
kubectl apply -f k8s/sealed-secrets-controller.yaml
```

### Step 2: Export Existing Secrets

```bash
# Extract current secrets
kubectl get secret touchcli-secrets -n touchcli -o yaml > /tmp/plaintext-secret.yaml
```

### Step 3: Seal and Replace

```bash
# Seal the secret
kubeseal -f /tmp/plaintext-secret.yaml -w k8s/sealed-secrets-touchcli.yaml \
  --scope namespace -n touchcli

# Apply sealed version
kubectl apply -f k8s/sealed-secrets-touchcli.yaml

# Remove plaintext version
kubectl delete secret touchcli-secrets -n touchcli
```

### Step 4: Update Deployments

Deployments automatically pick up the new secret created by Sealed Secrets controller.

## Additional Resources

- [Sealed Secrets GitHub](https://github.com/bitnami-labs/sealed-secrets)
- [Kubernetes Secrets Best Practices](https://kubernetes.io/docs/concepts/configuration/secret/)
- [OWASP Secrets Management](https://owasp.org/www-community/Secrets_Management)
- [HashiCorp Vault Alternative](https://www.vaultproject.io/)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review controller logs: `kubectl logs -n sealed-secrets ...`
3. Refer to [Sealed Secrets documentation](https://github.com/bitnami-labs/sealed-secrets)
