#!/bin/bash
# Database backup script
# Creates a backup of the PostgreSQL database

set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Load environment variables
if [ -f .env ]; then
    set -a && source .env && set +a
fi

# Check if database URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "💾 Creating database backup..."
echo "   Backup file: $BACKUP_FILE"

# Extract database connection details from DATABASE_URL
# Format: postgresql://user:password@host:port/database
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    PGUSER="${BASH_REMATCH[1]}"
    PGPASSWORD="${BASH_REMATCH[2]}"
    PGHOST="${BASH_REMATCH[3]}"
    PGPORT="${BASH_REMATCH[4]}"
    PGDATABASE="${BASH_REMATCH[5]}"

    # Perform backup
    PGPASSWORD="$PGPASSWORD" pg_dump \
        -h "$PGHOST" \
        -p "$PGPORT" \
        -U "$PGUSER" \
        -d "$PGDATABASE" \
        --no-password \
        > "$BACKUP_FILE"

    # Compress backup
    gzip "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.gz"

    echo "✅ Backup created successfully!"
    echo "   Location: $BACKUP_FILE"
    echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    echo "❌ Invalid DATABASE_URL format"
    exit 1
fi

# Cleanup old backups (keep last 7 days)
echo ""
echo "🧹 Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete
echo "✅ Cleanup complete"
