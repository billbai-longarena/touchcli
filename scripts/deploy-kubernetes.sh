#!/bin/bash
# Kubernetes deployment script
# Deploys TouchCLI to Kubernetes cluster

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NAMESPACE="touchcli"
REGISTRY="${DOCKER_REGISTRY:-docker.io}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Functions
print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
print_header "Checking prerequisites"

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not installed"
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    print_error "Not connected to Kubernetes cluster"
    exit 1
fi

print_success "kubectl found and connected to cluster"

# Create namespace
print_header "Creating namespace"
kubectl apply -f k8s/namespace.yaml
print_success "Namespace created"

# Create ConfigMap
print_header "Deploying ConfigMap"
kubectl apply -f k8s/configmap.yaml
print_success "ConfigMap deployed"

# Create/update Secrets
print_header "Deploying Secrets"
print_warning "Update k8s/secrets.yaml with actual values before deployment"
kubectl apply -f k8s/secrets.yaml
print_success "Secrets deployed (remember to update with real values!)"

# Deploy services
print_header "Deploying services"

echo "Deploying Agent Service..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl rollout status deployment/agent-service -n $NAMESPACE --timeout=300s
print_success "Agent Service deployed"

echo "Deploying Gateway..."
kubectl apply -f k8s/gateway-deployment.yaml
kubectl rollout status deployment/gateway -n $NAMESPACE --timeout=300s
print_success "Gateway deployed"

echo "Deploying Frontend..."
kubectl apply -f k8s/frontend-deployment.yaml
kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=300s
print_success "Frontend deployed"

# Deploy Ingress
print_header "Deploying Ingress"
kubectl apply -f k8s/ingress.yaml
print_success "Ingress deployed"

# Print deployment status
print_header "Deployment Status"
echo ""
echo "Pods:"
kubectl get pods -n $NAMESPACE -o wide

echo ""
echo "Services:"
kubectl get svc -n $NAMESPACE

echo ""
echo "Ingress:"
kubectl get ingress -n $NAMESPACE

echo ""
print_header "Deployment Complete!"
echo ""
echo "Next steps:"
echo "1. Update k8s/secrets.yaml with real values"
echo "2. Verify all pods are running: kubectl get pods -n $NAMESPACE"
echo "3. Check ingress status: kubectl get ingress -n $NAMESPACE"
echo "4. Test endpoints: curl https://touchcli.io"
echo ""
echo "Useful commands:"
echo "  kubectl logs deployment/agent-service -n $NAMESPACE -f"
echo "  kubectl describe pod <pod-name> -n $NAMESPACE"
echo "  kubectl port-forward svc/agent-service 8000:8000 -n $NAMESPACE"
