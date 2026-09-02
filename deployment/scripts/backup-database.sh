#!/bin/bash

# RootLearn Database Backup Script
# Creates a compressed PostgreSQL backup with timestamp

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
POSTGRES_USER="${POSTGRES_USER:-rootlearn}"
POSTGRES_DB="${POSTGRES_DB:-rootlearn}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/rootlearn_backup_${TIMESTAMP}.sql.gz"

echo "==================================="
echo "RootLearn Database Backup"
echo "==================================="
echo "Timestamp: $(date)"
echo "Backup file: ${BACKUP_FILE}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Check if PostgreSQL is running
echo "Checking database connectivity..."
if ! docker-compose -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U "${POSTGRES_USER}" > /dev/null 2>&1; then
    echo "ERROR: Database is not accessible"
    exit 1
fi
echo "✓ Database is accessible"

# Create backup
echo ""
echo "Creating backup..."
docker-compose -f "${COMPOSE_FILE}" exec -T postgres \
    pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
    --no-owner --no-acl --clean --if-exists \
    | gzip > "${BACKUP_FILE}"

# Verify backup was created
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file was not created"
    exit 1
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "✓ Backup created successfully (${BACKUP_SIZE})"

# Clean up old backups
echo ""
echo "Cleaning up old backups (keeping last ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "rootlearn_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
REMAINING_BACKUPS=$(find "${BACKUP_DIR}" -name "rootlearn_backup_*.sql.gz" -type f | wc -l)
echo "✓ ${REMAINING_BACKUPS} backups remaining"

# Optional: Upload to S3
if [ -n "${BACKUP_S3_BUCKET}" ]; then
    echo ""
    echo "Uploading to S3..."
    aws s3 cp "${BACKUP_FILE}" "s3://${BACKUP_S3_BUCKET}/backups/" \
        --region "${BACKUP_S3_REGION:-us-east-1}" \
        --storage-class STANDARD_IA
    echo "✓ Uploaded to S3"
fi

echo ""
echo "==================================="
echo "Backup completed successfully!"
echo "==================================="
echo "Backup location: ${BACKUP_FILE}"
echo "Backup size: ${BACKUP_SIZE}"
echo ""
