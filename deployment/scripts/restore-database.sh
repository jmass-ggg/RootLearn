#!/bin/bash

# RootLearn Database Restore Script
# Restores a PostgreSQL backup from file

set -e

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
POSTGRES_USER="${POSTGRES_USER:-rootlearn}"
POSTGRES_DB="${POSTGRES_DB:-rootlearn}"

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Example: $0 ./backups/rootlearn_backup_20260902_100000.sql.gz"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/rootlearn_backup_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "==================================="
echo "RootLearn Database Restore"
echo "==================================="
echo "Timestamp: $(date)"
echo "Backup file: ${BACKUP_FILE}"
echo ""

# Warning
echo "⚠️  WARNING: This will REPLACE the current database!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop backend and frontend services
echo "Stopping application services..."
docker-compose -f "${COMPOSE_FILE}" stop backend frontend
echo "✓ Services stopped"

# Check if PostgreSQL is running
echo ""
echo "Checking database connectivity..."
if ! docker-compose -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U "${POSTGRES_USER}" > /dev/null 2>&1; then
    echo "ERROR: Database is not accessible"
    echo "Starting PostgreSQL..."
    docker-compose -f "${COMPOSE_FILE}" up -d postgres
    sleep 5
fi
echo "✓ Database is accessible"

# Create backup of current state before restore
echo ""
echo "Creating safety backup of current database..."
SAFETY_BACKUP="./backups/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
mkdir -p ./backups
docker-compose -f "${COMPOSE_FILE}" exec -T postgres \
    pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
    | gzip > "${SAFETY_BACKUP}"
echo "✓ Safety backup created: ${SAFETY_BACKUP}"

# Restore database
echo ""
echo "Restoring database from backup..."
gunzip -c "${BACKUP_FILE}" | docker-compose -f "${COMPOSE_FILE}" exec -T postgres \
    psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" > /dev/null

if [ $? -eq 0 ]; then
    echo "✓ Database restored successfully"
else
    echo "ERROR: Database restore failed"
    echo "You can restore the safety backup: ${SAFETY_BACKUP}"
    exit 1
fi

# Start services
echo ""
echo "Starting application services..."
docker-compose -f "${COMPOSE_FILE}" up -d
echo "✓ Services started"

# Verify services
echo ""
echo "Verifying services..."
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is healthy"
else
    echo "⚠️  Backend health check failed"
fi

echo ""
echo "==================================="
echo "Restore completed!"
echo "==================================="
echo "Backup file used: ${BACKUP_FILE}"
echo "Safety backup: ${SAFETY_BACKUP}"
echo ""
