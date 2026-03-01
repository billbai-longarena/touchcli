#!/bin/bash
# Database Backup Script for TouchCLI
# Purpose: Create PostgreSQL database backups
# Usage: ./scripts/backup-db.sh [--local|--s3] [--compress] [--upload]

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
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="touchcli_postgres"
ENV_FILE="${PROJECT_ROOT}/.env"

# Default options
COMPRESS=false
UPLOAD_TO_S3=false
BACKUP_TYPE="local"

# Load environment
if [ -f "${ENV_FILE}" ]; then
  export $(cat "${ENV_FILE}" | grep -v '^#' | xargs)
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

log_debug() {
  echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --local)
      BACKUP_TYPE="local"
      shift
      ;;
    --s3)
      BACKUP_TYPE="s3"
      shift
      ;;
    --compress)
      COMPRESS=true
      shift
      ;;
    --upload)
      UPLOAD_TO_S3=true
      shift
      ;;
    *)
      log_error "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check database connectivity
check_db() {
  log_info "Checking database connectivity..."

  if docker ps | grep -q "${DB_CONTAINER}"; then
    log_info "✓ Database container found: ${DB_CONTAINER}"
  else
    log_warn "Database container not found, assuming remote database"
  fi
}

# Perform backup
backup_database() {
  local db_name="${POSTGRES_DB:-touchcli_db}"
  local db_user="${POSTGRES_USER:-postgres}"
  local db_host="${DB_HOST:-postgres}"
  local backup_file="${BACKUP_DIR}/touchcli_${TIMESTAMP}.sql"

  log_info "Creating database backup..."
  log_debug "Database: ${db_name}"
  log_debug "User: ${db_user}"
  log_debug "Host: ${db_host}"

  if docker ps | grep -q "${DB_CONTAINER}"; then
    # Backup from Docker container
    log_debug "Using Docker container backup"

    if docker exec "${DB_CONTAINER}" pg_dump \
      -U "${db_user}" \
      -d "${db_name}" \
      --no-password \
      > "${backup_file}"; then
      log_info "✓ Backup created: ${backup_file}"
      log_debug "Backup size: $(du -h "${backup_file}" | cut -f1)"
    else
      log_error "Database backup failed"
      return 1
    fi
  else
    # Backup from remote database
    log_debug "Using remote database backup"

    if pg_dump \
      -h "${db_host}" \
      -U "${db_user}" \
      -d "${db_name}" \
      > "${backup_file}"; then
      log_info "✓ Backup created: ${backup_file}"
      log_debug "Backup size: $(du -h "${backup_file}" | cut -f1)"
    else
      log_error "Database backup failed"
      return 1
    fi
  fi

  # Compress if requested
  if [ "${COMPRESS}" = true ]; then
    log_info "Compressing backup..."
    gzip "${backup_file}"
    backup_file="${backup_file}.gz"
    log_info "✓ Compressed: $(du -h "${backup_file}" | cut -f1)"
  fi

  echo "${backup_file}"
}

# Upload to S3
upload_to_s3() {
  local backup_file=$1
  local s3_bucket="${BACKUP_S3_BUCKET:-touchcli-backups}"
  local s3_path="s3://${s3_bucket}/$(basename ${backup_file})"

  log_info "Uploading to S3: ${s3_path}"

  if command -v aws &> /dev/null; then
    if aws s3 cp "${backup_file}" "${s3_path}"; then
      log_info "✓ Uploaded to S3"

      # Check file size
      local file_size=$(ls -lh "${backup_file}" | awk '{print $5}')
      log_info "  File size: ${file_size}"

      # Display S3 metadata
      aws s3api head-object --bucket "${s3_bucket}" --key "$(basename ${backup_file})" \
        --query '{Size: ContentLength, LastModified: LastModified}' \
        --output table
    else
      log_error "S3 upload failed"
      return 1
    fi
  else
    log_error "AWS CLI not found"
    return 1
  fi
}

# Cleanup old backups
cleanup_old_backups() {
  local retention_days="${BACKUP_RETENTION_DAYS:-30}"
  local cutoff_date=$(date -d "${retention_days} days ago" +%s)

  log_info "Cleaning up backups older than ${retention_days} days..."

  local count=0
  find "${BACKUP_DIR}" -name "touchcli_*.sql*" -type f | while read -r file; do
    local file_date=$(stat -f%m "${file}" 2>/dev/null || stat -c %Y "${file}")
    if [ "${file_date}" -lt "${cutoff_date}" ]; then
      rm "${file}"
      ((count++))
      log_debug "Deleted: $(basename ${file})"
    fi
  done

  if [ "${count}" -gt 0 ]; then
    log_info "✓ Deleted ${count} old backup(s)"
  else
    log_info "No old backups to delete"
  fi
}

# Verify backup
verify_backup() {
  local backup_file=$1

  log_info "Verifying backup integrity..."

  if file "${backup_file}" | grep -q "SQL"; then
    log_info "✓ Backup file verified (SQL format)"
  elif file "${backup_file}" | grep -q "gzip"; then
    log_info "✓ Backup file verified (gzip compressed)"
  else
    log_warn "Could not verify backup format"
  fi

  # Show header lines
  if [[ "${backup_file}" == *.gz ]]; then
    log_debug "First 5 lines:"
    zcat "${backup_file}" | head -5 | sed 's/^/  /'
  else
    log_debug "First 5 lines:"
    head -5 "${backup_file}" | sed 's/^/  /'
  fi
}

# Display backup information
display_info() {
  local backup_file=$1

  echo ""
  echo -e "${BLUE}════════════════════════════════════════${NC}"
  echo -e "${BLUE}Backup Information${NC}"
  echo -e "${BLUE}════════════════════════════════════════${NC}"
  echo "Backup File: $(basename ${backup_file})"
  echo "Location:    ${backup_file}"
  echo "Size:        $(du -h "${backup_file}" | cut -f1)"
  echo "Timestamp:   ${TIMESTAMP}"
  echo "Type:        ${BACKUP_TYPE}"

  if [ "${UPLOAD_TO_S3}" = true ]; then
    echo "S3 Backup:   Yes"
  fi

  echo -e "${BLUE}════════════════════════════════════════${NC}"
  echo ""
}

# Retention policy
show_retention_policy() {
  local retention_days="${BACKUP_RETENTION_DAYS:-30}"
  local rotation_time="${BACKUP_ROTATION_TIME:-daily}"

  log_info "Backup Retention Policy:"
  log_info "  Rotation:   ${rotation_time}"
  log_info "  Retention:  ${retention_days} days"
  log_info "  Old backups will be automatically deleted"
}

# Main execution
main() {
  log_info "TouchCLI Database Backup Tool"
  log_info "=============================="
  echo ""

  # Check prerequisites
  check_db

  # Perform backup
  local backup_file=$(backup_database)

  if [ -z "${backup_file}" ]; then
    log_error "Backup creation failed"
    exit 1
  fi

  # Verify backup
  verify_backup "${backup_file}"

  # Upload to S3 if requested
  if [ "${BACKUP_TYPE}" = "s3" ] || [ "${UPLOAD_TO_S3}" = true ]; then
    upload_to_s3 "${backup_file}"
  fi

  # Cleanup old backups
  cleanup_old_backups

  # Display information
  display_info "${backup_file}"

  # Show retention policy
  show_retention_policy

  log_info "✓ Backup completed successfully"
  log_info "To restore: ./scripts/restore-db.sh ${backup_file}"
}

# Run main
main "$@"
