#!/bin/bash

# TouchCLI Sealed Secrets Utility Script
# =========================================
# This script helps manage sealed secrets for production Kubernetes deployments
#
# Usage:
#   ./scripts/seal-secrets.sh --env production --output k8s/sealed-secrets-touchcli.yaml
#   ./scripts/seal-secrets.sh --interactive

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"

# Functions
print_header() {
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_dependencies() {
    print_header "Checking Dependencies"

    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl."
        exit 1
    fi
    print_success "kubectl found"

    if ! command -v kubeseal &> /dev/null; then
        print_error "kubeseal not found. Please install kubeseal:"
        echo "  macOS:  brew install kubeseal"
        echo "  Linux:  https://github.com/bitnami-labs/sealed-secrets/releases"
        exit 1
    fi
    print_success "kubeseal found"
}

check_cluster_connection() {
    print_header "Checking Kubernetes Cluster Connection"

    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        echo "Please ensure you have:"
        echo "  1. kubectl installed and configured"
        echo "  2. A valid kubeconfig file"
        echo "  3. Network access to your cluster"
        exit 1
    fi

    CLUSTER_NAME=$(kubectl config current-context)
    print_success "Connected to cluster: $CLUSTER_NAME"
}

check_sealed_secrets_controller() {
    print_header "Checking Sealed Secrets Controller"

    if ! kubectl get deployment -n sealed-secrets sealed-secrets-controller &> /dev/null; then
        print_warning "Sealed Secrets controller not found in sealed-secrets namespace"
        read -p "Install Sealed Secrets controller now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Installing Sealed Secrets controller..."
            kubectl apply -f "$K8S_DIR/sealed-secrets-controller.yaml"
            echo "Waiting for controller to be ready..."
            kubectl wait --for=condition=available --timeout=300s \
                deployment/sealed-secrets-controller -n sealed-secrets 2>/dev/null || true
            print_success "Sealed Secrets controller installed"
        else
            print_error "Sealed Secrets controller is required. Exiting."
            exit 1
        fi
    else
        READY=$(kubectl get deployment -n sealed-secrets sealed-secrets-controller \
            -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        if [ "$READY" -gt 0 ]; then
            print_success "Sealed Secrets controller is running"
        else
            print_warning "Sealed Secrets controller is not ready yet"
        fi
    fi
}

create_secret_from_env() {
    local env_file=$1
    local output_file=$2
    local namespace=$3

    print_header "Creating Sealed Secret from Environment File"

    if [ ! -f "$env_file" ]; then
        print_error "Environment file not found: $env_file"
        exit 1
    fi

    # Create temporary secret file
    TEMP_SECRET=$(mktemp)
    trap "rm -f $TEMP_SECRET" EXIT

    cat > "$TEMP_SECRET" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: touchcli-secrets
  namespace: $namespace
type: Opaque
stringData:
EOF

    # Read env file and convert to secret format
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^[[:space:]]*# ]] && continue
        [[ -z "$key" ]] && continue

        # Skip non-secret keys
        case "$key" in
            NODE_ENV|LOG_LEVEL|PORT|WORKER_*|DEBUG|RATE_LIMIT_ENABLED)
                continue
                ;;
        esac

        # Add to secret
        echo "  $key: \"$value\"" >> "$TEMP_SECRET"
    done < "$env_file"

    # Seal the secret
    echo "Sealing secret with kubeseal..."
    kubeseal -f "$TEMP_SECRET" -w "$output_file" --scope namespace -n "$namespace"

    if [ -f "$output_file" ]; then
        print_success "Sealed secret created: $output_file"
        print_warning "Add this file to git. The encrypted data is safe to commit."
    fi
}

interactive_mode() {
    print_header "Interactive Sealed Secrets Setup"

    read -p "Enter namespace (default: touchcli): " NAMESPACE
    NAMESPACE=${NAMESPACE:-touchcli}

    read -p "Enter environment file path (default: .env.production): " ENV_FILE
    ENV_FILE=${ENV_FILE:-.env.production}

    read -p "Enter output file path (default: k8s/sealed-secrets-touchcli.yaml): " OUTPUT_FILE
    OUTPUT_FILE=${OUTPUT_FILE:-k8s/sealed-secrets-touchcli.yaml}

    # Make paths absolute if relative
    if [[ ! "$ENV_FILE" = /* ]]; then
        ENV_FILE="$PROJECT_ROOT/$ENV_FILE"
    fi
    if [[ ! "$OUTPUT_FILE" = /* ]]; then
        OUTPUT_FILE="$PROJECT_ROOT/$OUTPUT_FILE"
    fi

    print_header "Creating Sealed Secret"
    echo "  Namespace: $NAMESPACE"
    echo "  Environment File: $ENV_FILE"
    echo "  Output File: $OUTPUT_FILE"

    create_secret_from_env "$ENV_FILE" "$OUTPUT_FILE" "$NAMESPACE"
}

verify_sealed_secret() {
    local secret_file=$1

    print_header "Verifying Sealed Secret"

    if [ ! -f "$secret_file" ]; then
        print_error "Secret file not found: $secret_file"
        return 1
    fi

    # Check if file contains encrypted data
    if grep -q "encryptedData" "$secret_file"; then
        print_success "Sealed secret file is properly formatted"

        # Show metadata
        echo ""
        echo "Sealed Secret Metadata:"
        kubectl get --filename="$secret_file" -o yaml 2>/dev/null | grep -A 5 "metadata:" || true

        return 0
    else
        print_error "File does not appear to be a sealed secret"
        return 1
    fi
}

apply_sealed_secret() {
    local secret_file=$1

    print_header "Applying Sealed Secret to Cluster"

    if [ ! -f "$secret_file" ]; then
        print_error "Secret file not found: $secret_file"
        exit 1
    fi

    echo "Applying sealed secret: $secret_file"
    kubectl apply -f "$secret_file"

    # Verify decryption
    sleep 2
    DECRYPTED=$(kubectl get secret touchcli-secrets -n touchcli -o jsonpath='{.data}' 2>/dev/null || echo "")

    if [ -n "$DECRYPTED" ]; then
        print_success "Secret successfully decrypted by Sealed Secrets controller"
    else
        print_warning "Could not verify secret decryption. Check controller logs with:"
        echo "  kubectl logs -n sealed-secrets -l app.kubernetes.io/name=sealed-secrets"
    fi
}

# Main
main() {
    case "${1:-}" in
        --check)
            check_dependencies
            check_cluster_connection
            check_sealed_secrets_controller
            ;;
        --seal)
            if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
                echo "Usage: $0 --seal <env-file> <output-file>"
                exit 1
            fi
            check_dependencies
            check_cluster_connection
            check_sealed_secrets_controller
            create_secret_from_env "$2" "$3" "touchcli"
            ;;
        --apply)
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 --apply <secret-file>"
                exit 1
            fi
            check_dependencies
            check_cluster_connection
            check_sealed_secrets_controller
            verify_sealed_secret "$2"
            apply_sealed_secret "$2"
            ;;
        --verify)
            if [ -z "${2:-}" ]; then
                echo "Usage: $0 --verify <secret-file>"
                exit 1
            fi
            verify_sealed_secret "$2"
            ;;
        --interactive|-i)
            check_dependencies
            check_cluster_connection
            check_sealed_secrets_controller
            interactive_mode
            ;;
        --help|-h)
            cat <<EOF
TouchCLI Sealed Secrets Management Script

Usage:
  $0 [COMMAND] [OPTIONS]

Commands:
  --check                    Check dependencies and cluster connection
  --seal <env> <output>      Seal an environment file
  --apply <file>             Apply sealed secret to cluster
  --verify <file>            Verify sealed secret file
  --interactive, -i          Interactive mode
  --help, -h                 Show this help message

Examples:
  # Interactive setup
  $0 --interactive

  # Seal production environment
  $0 --seal .env.production k8s/sealed-secrets-touchcli.yaml

  # Apply to cluster
  $0 --apply k8s/sealed-secrets-touchcli.yaml

  # Verify before applying
  $0 --verify k8s/sealed-secrets-touchcli.yaml

Environment Variables:
  KUBECONFIG                 Path to kubeconfig file

Documentation:
  https://github.com/bitnami-labs/sealed-secrets

EOF
            ;;
        *)
            interactive_mode
            ;;
    esac
}

main "$@"
