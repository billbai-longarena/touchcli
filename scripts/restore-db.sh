#!/bin/bash
# Database Restore Script for TouchCLI
# Purpose: Restore PostgreSQL database from backup
# Usage: ./scripts/restore-db.sh <backup_file> [--confirm]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DB_CONTAINER="touchcli_postgres"
ENV_FILE="${PROJECT_ROOT}/.env"

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

log_debug() {
  echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Load environment
if [ -f "${ENV_FILE}" ]; then
  export $(cat "${ENV_FILE}" | grep -v '^#' | xargs)
fi

# Check arguments
if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup_file> [--confirm]"
  echo ""
  echo "Available backups:"
  ls -lh "${BACKUP_DIR}"/touchcli_*.sql* 2>/dev/null | awk '{print "  " $9}' || echo "  No backups found"
  exit 1
fi

BACKUP_FILE="$1"
CONFIRM="${2:-}"

# Verify backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
  log_error "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

log_info "Backup file: $(basename ${BACKUP_FILE})"
log_info "File size: $(du -h "${BACKUP_FILE}" | cut -f1)"

# Confirm restore (destructive operation)
if [ "${CONFIRM}" != "--confirm" ]; then
  log_warn "⚠️  WARNING: This will OVERWRITE the current database!"
  log_warn "This operation cannot be undone."
  echo ""
  echo "Backup file: $(basename ${BACKUP_FILE})"
  echo "Database: ${POSTGRES_DB}"
  echo ""
  read -p "Type 'yes' to confirm restore: " response

  if [ "$response" != "yes" ]; then
    log_warn "Restore cancelled"
    exit 0
  fi
fi

# Check database connectivity
check_db() {
  log_info "Checking database connectivity..."

  if docker ps | grep -q "${DB_CONTAINER}"; then
    log_info "✓ Database container found: ${DB_CONTAINER}"
    return 0
  else
    log_warn "Database container not found, assuming remote database"
    return 1
  fi
}

# Drop existing database connections
drop_connections() {
  local db_name="${POSTGRES_DB}"
  local db_user="${POSTGRES_USER:-postgres}"
  local db_host="${DB_HOST:-postgres}"

  log_info "Terminating existing connections..."

  if docker ps | grep -q "${DB_CONTAINER}"; then
    docker exec "${DB_CONTAINER}" psql \
      -U "${db_user}" \
      -d postgres \
      --no-password \
      -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${db_name}' AND pid <> pg_backend_pid();" \
      > /dev/null 2>&1 || true
  else
    psql \
      -h "${db_host}" \
      -U "${db_user}" \
      -d postgres \
      -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${db_name}' AND pid <> pg_backend_pid();" \
      > /dev/null 2>&1 || true
  fi

  sleep 2
}

# Drop and recreate database
drop_and_recreate_db() {
  local db_name="${POSTGRES_DB}"
  local db_user="${POSTGRES_USER:-postgres}"
  local db_host="${DB_HOST:-postgres}"

  log_info "Dropping and recreating database..."

  if docker ps | grep -q "${DB_CONTAINER}"; then
    docker exec "${DB_CONTAINER}" psql \
      -U "${db_user}" \
      -d postgres \
      --no-password \
      -c "DROP DATABASE IF EXISTS \"${db_name}\" WITH (FORCE);"

    docker exec "${DB_CONTAINER}" psql \
      -U "${db_user}" \
      -d postgres \
      --no-password \
      -c "CREATE DATABASE \"${db_name}\";"
  else
    psql \
      -h "${db_host}" \
      -U "${db_user}" \
      -d postgres \
      -c "DROP DATABASE IF EXISTS \"${db_name}\" WITH (FORCE);"

    psql \
      -h "${db_host}" \
      -U "${db_user}" \
      -d postgres \
      -c "CREATE DATABASE \"${db_name}\";"
  fi

  log_info "✓ Database recreated"
}

# Restore from backup
restore_backup() {
  local backup_file=$1
  local db_name="${POSTGRES_DB}"
  local db_user="${POSTGRES_USER:-postgres}"
  local db_host="${DB_HOST:-postgres}"

  log_info "Restoring from backup..."

  # Detect if compressed
  if [[ "${backup_file}" == *.gz ]]; then
    log_debug "Detected gzip compression"

    if docker ps | grep -q "${DB_CONTAINER}"; then
      gunzip -c "${backup_file}" | docker exec -i "${DB_CONTAINER}" psql \
        -U "${db_user}" \
        -d "${db_name}" \
        --no-password
    else
      gunzip -c "${backup_file}" | psql \
        -h "${db_host}" \
        -U "${db_user}" \
        -d "${db_name}"
    fi
  else
    log_debug "Detected uncompressed SQL"

    if docker ps | grep -q "${DB_CONTAINER}"; then
      docker exec -i "${DB_CONTAINER}" psql \
        -U "${db_user}" \
        -d "${db_name}" \
        --no-password \
        < "${backup_file}"
    else
      psql \
        -h "${db_host}" \
        -U "${db_user}" \
        -d "${db_name}" \
        < "${backup_file}"
    fi
  fi

  if [ $? -eq 0 ]; then
    log_info "✓ Restore completed successfully"
  else
    log_error "Restore failed"
    return 1
  fi
}

# Verify restore
verify_restore() {
  local db_name="${POSTGRES_DB}"
  local db_user="${POSTGRES_USER:-postgres}"
  local db_host="${DB_HOST:-postgres}"

  log_info "Verifying restore..."

  if docker ps | grep -q "${DB_CONTAINER}"; then
    local table_count=$(docker exec "${DB_CONTAINER}" psql \
      -U "${db_user}" \
      -d "${db_name}" \
      --no-password \
      --tuples-only \
      -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
  else
    local table_count=$(psql \
      -h "${db_host}" \
      -U "${db_user}" \
      -d "${db_name}" \
      --tuples-only \
      -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')
  fi

  log_info "✓ Database restored with ${table_count} table(s)"
}

# Show summary
show_summary() {
  echo ""
  echo -e "${BLUE}════════════════════════════════════════${NC}"
  echo -e "${BLUE}Restore Completed${NC}"
  echo -e "${BLUE}════════════════════════════════════════${NC}"
  echo "Backup File:  $(basename ${BACKUP_FILE})"
  echo "Database:     ${POSTGRES_DB}"
  echo "Status:       ✓ Restored Successfully"
  echo ""
  echo "Next steps:"
  echo "  1. Verify data integrity"
  echo "  2. Run migrations: ./scripts/migrate-db.sh"
  echo "  3. Test the application"
  echo -e "${BLUE}════════════════════════════════════════${NC}"
  echo ""
}

# Main execution
main() {
  log_info "TouchCLI Database Restore Tool"
  log_info "=============================="
  echo ""

  # Create backup directory if needed
  mkdir -p "${BACKUP_DIR}"

  # Check prerequisites
  check_db

  # Restore process
  drop_connections
  drop_and_recreate_db

  if restore_backup "${BACKUP_FILE}"; then
    verify_restore
    show_summary
    log_info "✓ Restore completed successfully"
  else
    log_error "Restore failed - database may be in inconsistent state"
    exit 1
  fi
}

# Run main
main "$@"
