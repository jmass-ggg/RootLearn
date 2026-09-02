#!/bin/bash

# RootLearn Production Deployment Script
# Handles zero-downtime deployment with health checks

set -e

# Configuration
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
RUN_SMOKE_TESTS="${RUN_SMOKE_TESTS:-true}"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=2

echo "==================================="
echo "RootLearn Production Deployment"
echo "==================================="
echo "Timestamp: $(date)"
echo "Compose file: ${COMPOSE_FILE}"
echo ""

# Pre-deployment checks
echo "Pre-Deployment Checks:"
echo "---------------------"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "✗ ERROR: .env.production file not found"
    echo "Copy .env.production.example and configure it"
    exit 1
fi
echo "✓ Environment file exists"

# Check if docker-compose file exists
if [ ! -f "${COMPOSE_FILE}" ]; then
    echo "✗ ERROR: ${COMPOSE_FILE} not found"
    exit 1
fi
echo "✓ Compose file exists"

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "✗ ERROR: Docker is not running"
    exit 1
fi
echo "✓ Docker is running"

# Check required environment variables
if [ -z "${OPENAI_API_KEY}${ANTHROPIC_API_KEY}${GOOGLE_API_KEY}" ]; then
    echo "⚠️  WARNING: No AI provider API key found"
fi

echo ""

# Backup database
if [ "${BACKUP_BEFORE_DEPLOY}" = "true" ]; then
    echo "Creating pre-deployment backup..."
    ./deployment/scripts/backup-database.sh
    echo ""
fi

# Pull latest images
echo "Pulling latest Docker images..."
docker-compose -f "${COMPOSE_FILE}" pull
echo "✓ Images pulled"
echo ""

# Check pending migrations
echo "Checking database migrations..."
echo "Current migration:"
docker-compose -f "${COMPOSE_FILE}" exec -T backend alembic current 2>/dev/null || echo "No current migration"
echo ""
echo "Pending migrations:"
docker-compose -f "${COMPOSE_FILE}" exec -T backend alembic heads 2>/dev/null || echo "Unable to check"
echo ""

# Confirm deployment
read -p "Continue with deployment? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Run migrations
echo "Running database migrations..."
docker-compose -f "${COMPOSE_FILE}" run --rm backend alembic upgrade head
echo "✓ Migrations completed"
echo ""

# Deploy services
echo "Deploying services..."
docker-compose -f "${COMPOSE_FILE}" up -d
echo "✓ Services started"
echo ""

# Wait for services to be healthy
echo "Waiting for services to be healthy..."

# Check backend health
echo -n "Backend health check: "
for i in $(seq 1 ${HEALTH_CHECK_RETRIES}); do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✓ OK (attempt ${i})"
        break
    fi
    
    if [ $i -eq ${HEALTH_CHECK_RETRIES} ]; then
        echo "✗ FAILED after ${HEALTH_CHECK_RETRIES} attempts"
        echo ""
        echo "Backend logs:"
        docker-compose -f "${COMPOSE_FILE}" logs --tail=50 backend
        exit 1
    fi
    
    sleep ${HEALTH_CHECK_INTERVAL}
done

# Check frontend health
echo -n "Frontend health check: "
for i in $(seq 1 ${HEALTH_CHECK_RETRIES}); do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "✓ OK (attempt ${i})"
        break
    fi
    
    if [ $i -eq ${HEALTH_CHECK_RETRIES} ]; then
        echo "✗ FAILED after ${HEALTH_CHECK_RETRIES} attempts"
        echo ""
        echo "Frontend logs:"
        docker-compose -f "${COMPOSE_FILE}" logs --tail=50 frontend
        exit 1
    fi
    
    sleep ${HEALTH_CHECK_INTERVAL}
done

echo ""

# Run smoke tests
if [ "${RUN_SMOKE_TESTS}" = "true" ]; then
    echo "Running smoke tests..."
    ./deployment/scripts/smoke-tests.sh
    echo ""
fi

# Clean up old images
echo "Cleaning up old Docker images..."
docker image prune -f > /dev/null
echo "✓ Cleanup completed"
echo ""

# Display service status
echo "Service Status:"
echo "--------------"
docker-compose -f "${COMPOSE_FILE}" ps
echo ""

# Display recent logs
echo "Recent Logs:"
echo "-----------"
docker-compose -f "${COMPOSE_FILE}" logs --tail=20
echo ""

echo "==================================="
echo "✓ Deployment completed successfully!"
echo "==================================="
echo "Timestamp: $(date)"
echo ""
echo "Next steps:"
echo "  - Monitor logs: docker-compose -f ${COMPOSE_FILE} logs -f"
echo "  - View metrics: http://localhost:8000/metrics"
echo "  - Check health: http://localhost:8000/health"
echo ""
