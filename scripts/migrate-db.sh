#!/bin/bash
# Database Migration Script for TouchCLI
# Purpose: Run Alembic migrations to update database schema
# Usage: ./scripts/migrate-db.sh [--upgrade|--downgrade|--current|--heads]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend/python"
DB_CONTAINER="touchcli_agent_service"
ENV_FILE="${PROJECT_ROOT}/.env"

# Load environment
if [ -f "${ENV_FILE}" ]; then
  export $(cat "${ENV_FILE}" | grep -v '^#' | xargs)
else
  echo -e "${RED}Error: .env file not found at ${ENV_FILE}${NC}"
  exit 1
fi

# Logging functions
log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check if running in Docker
is_docker() {
  [ -f /.dockerenv ] || docker ps > /dev/null 2>&1
}

# Get migration command prefix
get_migration_cmd() {
  if is_docker; then
    # Running in Docker container
    echo "cd ${BACKEND_DIR} &&"
  else
    # Running on host, use docker-compose or direct python
    if docker ps | grep -q "${DB_CONTAINER}"; then
      echo "docker-compose exec agent_service"
    else
      echo "cd ${BACKEND_DIR} &&"
    fi
  fi
}

# Check database connection
check_db_connection() {
  log_info "Checking database connection..."

  if ! python3 -c "
import sys
try:
  import sqlalchemy
  from sqlalchemy import create_engine
  engine = create_engine('${DATABASE_URL}')
  connection = engine.connect()
  connection.close()
  print('✓ Database connection successful')
except Exception as e:
  print(f'✗ Database connection failed: {e}')
  sys.exit(1)
" 2>/dev/null; then
    log_error "Database connection failed"
    exit 1
  fi
}

# Display current migration status
show_status() {
  log_info "Current migration status:"
  alembic current
  echo ""
  log_info "Available migration heads:"
  alembic heads
}

# Upgrade to latest
upgrade_head() {
  log_info "Upgrading database to latest revision..."

  if alembic upgrade head; then
    log_info "✓ Database upgraded successfully"
    show_status
  else
    log_error "Database upgrade failed"
    exit 1
  fi
}

# Upgrade to specific revision
upgrade_revision() {
  local revision=$1
  log_info "Upgrading database to revision: ${revision}..."

  if alembic upgrade "${revision}"; then
    log_info "✓ Database upgraded to ${revision}"
    show_status
  else
    log_error "Database upgrade to ${revision} failed"
    exit 1
  fi
}

# Downgrade to specific revision
downgrade_revision() {
  local revision=$1
  log_warn "Downgrading database to revision: ${revision}..."
  log_warn "This may result in data loss. Continue? (yes/no)"
  read -r response

  if [ "$response" != "yes" ]; then
    log_warn "Downgrade cancelled"
    exit 0
  fi

  if alembic downgrade "${revision}"; then
    log_info "✓ Database downgraded to ${revision}"
    show_status
  else
    log_error "Database downgrade failed"
    exit 1
  fi
}

# Create new migration
create_migration() {
  local message=$1

  if [ -z "${message}" ]; then
    log_error "Migration message required"
    echo "Usage: $0 --create 'migration description'"
    exit 1
  fi

  log_info "Creating new migration: ${message}..."

  if alembic revision --autogenerate -m "${message}"; then
    log_info "✓ Migration created successfully"
    log_warn "Review the migration file before running upgrade"
  else
    log_error "Migration creation failed"
    exit 1
  fi
}

# Validate migrations
validate_migrations() {
  log_info "Validating migration history..."

  if alembic current && alembic heads; then
    log_info "✓ Migration validation successful"
  else
    log_error "Migration validation failed"
    exit 1
  fi
}

# Main script
main() {
  cd "${BACKEND_DIR}" || exit 1

  # Default action
  action="${1:-upgrade}"

  log_info "TouchCLI Database Migration Tool"
  log_info "=================================="

  case "${action}" in
    --upgrade|upgrade)
      check_db_connection
      upgrade_head
      ;;
    --downgrade|downgrade)
      check_db_connection
      downgrade_revision "${2}"
      ;;
    --revision)
      check_db_connection
      upgrade_revision "${2}"
      ;;
    --status|status)
      check_db_connection
      show_status
      ;;
    --current|current)
      check_db_connection
      alembic current
      ;;
    --heads|heads)
      alembic heads
      ;;
    --validate|validate)
      check_db_connection
      validate_migrations
      ;;
    --create|create)
      create_migration "${2}"
      ;;
    --history|history)
      alembic history
      ;;
    --help|help|-h)
      echo "Usage: $0 [COMMAND] [OPTIONS]"
      echo ""
      echo "Commands:"
      echo "  upgrade              Upgrade to latest migration (default)"
      echo "  downgrade REVISION   Downgrade to specific revision"
      echo "  revision REVISION    Upgrade to specific revision"
      echo "  status               Show current status and available heads"
      echo "  current              Show current revision"
      echo "  heads                Show available migration heads"
      echo "  validate             Validate migration history"
      echo "  create MESSAGE       Create new migration"
      echo "  history              Show migration history"
      echo "  help                 Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                   # Upgrade to latest"
      echo "  $0 status            # Show status"
      echo "  $0 create 'add users table'"
      echo "  $0 downgrade ae1027a21a6"
      ;;
    *)
      log_error "Unknown command: ${action}"
      echo "Use '$0 --help' for usage information"
      exit 1
      ;;
  esac
}

# Run main
main "$@"
