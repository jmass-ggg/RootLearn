# RootLearn Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Database Migration Strategy](#database-migration-strategy)
4. [Deployment Steps](#deployment-steps)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Backup and Recovery](#backup-and-recovery)
7. [Scaling](#scaling)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Docker 24.0+ and Docker Compose 2.20+
- PostgreSQL 16+ (if not using Docker)
- Node.js 20+ (for local frontend builds)
- Python 3.11+ (for local backend development)
- Minimum 2GB RAM, 20GB disk space
- SSL certificate (for production HTTPS)

### Required Accounts
- AI Provider API key (OpenAI, Anthropic, or Google Gemini)
- (Optional) Monitoring service account (Sentry, New Relic, etc.)
- (Optional) Cloud storage for backups (AWS S3, etc.)

## Environment Configuration

### 1. Create Production Environment File

Copy the example environment file and configure it:

```bash
cp .env.production.example .env.production
```

### 2. Configure Required Variables

**Critical variables that MUST be set:**

```bash
# Database
POSTGRES_PASSWORD=<generate-secure-password>
DATABASE_URL=postgresql+asyncpg://rootlearn:<password>@postgres:5432/rootlearn

# AI Provider (choose one)
AI_PROVIDER=openai
OPENAI_API_KEY=<your-openai-key>

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 3. Generate Secure Secrets

```bash
# Generate secret key
openssl rand -hex 32

# Generate postgres password
openssl rand -base64 32
```

### 4. Environment Variable Reference

See [Environment Variables Documentation](./ENVIRONMENT_VARIABLES.md) for complete reference.

## Database Migration Strategy

### Migration Philosophy

RootLearn uses Alembic for database schema management with a **forward-only** migration strategy:
- Migrations are versioned and applied sequentially
- Never modify existing migrations in production
- Use blue-green deployment for zero-downtime schema changes

### Pre-Deployment: Migration Review

**Before deploying**, review pending migrations:

```bash
# Check current database version
docker-compose -f docker-compose.prod.yml exec backend alembic current

# Check pending migrations
docker-compose -f docker-compose.prod.yml exec backend alembic history

# Review migration SQL (dry run)
docker-compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head --sql > migration_preview.sql
```

### Initial Deployment (Fresh Database)

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d postgres

# Wait for postgres to be ready
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_isready -U rootlearn

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic upgrade head

# Start remaining services
docker-compose -f docker-compose.prod.yml up -d
```

### Subsequent Deployments (Existing Database)

#### Option 1: Simple Update (Downtime Acceptable)

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down backend frontend

# Backup database
./deployment/scripts/backup-database.sh

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic upgrade head

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

#### Option 2: Blue-Green Deployment (Zero Downtime)

```bash
# 1. Deploy new version in parallel
docker-compose -f docker-compose.prod.yml up -d --scale backend=2

# 2. Run migrations (must be backward compatible)
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic upgrade head

# 3. Health check new instances
curl http://localhost:8000/health

# 4. Switch traffic (update load balancer)
# Update nginx or load balancer to route to new instances

# 5. Drain old instances
# Wait for active requests to complete

# 6. Stop old instances
docker-compose -f docker-compose.prod.yml stop backend
```

### Migration Best Practices

1. **Test migrations in staging first**
   ```bash
   # Staging environment
   docker-compose -f docker-compose.staging.yml run --rm backend \
     alembic upgrade head
   ```

2. **Backup before migration**
   ```bash
   ./deployment/scripts/backup-database.sh
   ```

3. **Rollback capability**
   ```bash
   # Rollback one version
   docker-compose -f docker-compose.prod.yml run --rm backend \
     alembic downgrade -1
   
   # Rollback to specific version
   docker-compose -f docker-compose.prod.yml run --rm backend \
     alembic downgrade <revision_id>
   ```

4. **Monitor migration progress**
   ```bash
   # Check logs during migration
   docker-compose -f docker-compose.prod.yml logs -f backend
   ```

### Creating New Migrations

```bash
# Generate migration from model changes
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic revision --autogenerate -m "description_of_change"

# Review generated migration
cat backend/alembic/versions/<new_revision>.py

# Test migration
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic upgrade head

# Test rollback
docker-compose -f docker-compose.prod.yml run --rm backend \
  alembic downgrade -1
```

### Breaking Changes

For schema changes that break backward compatibility:

1. **Add new column** (nullable or with default)
2. **Deploy code** that writes to both old and new
3. **Backfill data** from old to new column
4. **Deploy code** that reads from new column
5. **Remove old column** in separate migration

## Deployment Steps

### Production Deployment

#### 1. Pre-Deployment Checklist

- [ ] Environment variables configured in `.env.production`
- [ ] SSL certificates in place
- [ ] Database backup completed
- [ ] Migrations reviewed and tested in staging
- [ ] Health check endpoints verified
- [ ] Monitoring alerts configured

#### 2. Deploy with Docker Compose

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check service health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f

# Verify health endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```

#### 3. Post-Deployment Verification

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.database import engine; print('DB OK')"

# Check AI provider connectivity
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.ai.factory import get_ai_provider; print('AI OK')"

# Run smoke tests
./deployment/scripts/smoke-tests.sh
```

### Cloud Platform Deployments

#### AWS ECS

See [AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md) for detailed AWS deployment guide.

#### Google Cloud Run

See [GCP_DEPLOYMENT.md](./GCP_DEPLOYMENT.md) for detailed GCP deployment guide.

#### Azure Container Instances

See [AZURE_DEPLOYMENT.md](./AZURE_DEPLOYMENT.md) for detailed Azure deployment guide.

## Monitoring and Alerting

### Health Checks

RootLearn provides several health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health with dependencies
curl http://localhost:8000/health/detailed

# Ready check (for load balancers)
curl http://localhost:8000/ready
```

### Logging

#### Log Collection

All services log to stdout/stderr in JSON format with structured fields:

```json
{
  "timestamp": "2026-09-02T10:00:00Z",
  "level": "INFO",
  "service": "rootlearn-backend",
  "request_id": "abc123",
  "user_id": "user-uuid",
  "message": "Session created",
  "session_id": "session-uuid"
}
```

#### Log Aggregation

Configure log shipping to your preferred service:

**Option 1: Docker log driver**
```yaml
# docker-compose.prod.yml
services:
  backend:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: localhost:24224
        tag: rootlearn.backend
```

**Option 2: Sidecar container**
```yaml
services:
  log-shipper:
    image: fluent/fluentd:v1.16
    volumes:
      - ./deployment/fluentd/fluent.conf:/fluentd/etc/fluent.conf
```

### Metrics

#### Application Metrics

RootLearn exposes Prometheus-compatible metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

**Key metrics:**
- `rootlearn_sessions_created_total` - Total sessions created
- `rootlearn_sessions_completed_total` - Total sessions completed
- `rootlearn_diagnostic_questions_total` - Total diagnostic questions asked
- `rootlearn_ai_requests_total` - Total AI API requests
- `rootlearn_ai_request_duration_seconds` - AI request latency
- `rootlearn_api_request_duration_seconds` - API endpoint latency
- `rootlearn_mastery_score_average` - Average mastery score

#### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rootlearn-backend'
    static_configs:
      - targets: ['backend:9090']
    scrape_interval: 15s
```

#### Grafana Dashboards

Import pre-built dashboards from `deployment/grafana/`:
- `rootlearn-overview.json` - System overview
- `rootlearn-ai-performance.json` - AI provider metrics
- `rootlearn-learning-analytics.json` - Learning metrics

### Alerting Rules

#### Critical Alerts

```yaml
# alertmanager/rules.yml
groups:
  - name: rootlearn_critical
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(rootlearn_api_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"

      - alert: AIProviderFailure
        expr: rate(rootlearn_ai_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High AI provider error rate"
```

#### Warning Alerts

```yaml
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rootlearn_api_request_duration_seconds) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
          description: "95th percentile is {{ $value }}s"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name="rootlearn-backend"} / container_spec_memory_limit_bytes{name="rootlearn-backend"} > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on backend"
```

### Error Tracking

#### Sentry Integration

Configure Sentry in `.env.production`:

```bash
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

Sentry will automatically capture:
- Unhandled exceptions
- API errors
- AI provider failures
- Performance traces (sampled)

## Backup and Recovery

### Automated Database Backups

```bash
# Run backup script
./deployment/scripts/backup-database.sh

# Schedule with cron (daily at 2 AM)
0 2 * * * /path/to/deployment/scripts/backup-database.sh
```

### Manual Backup

```bash
# Backup to file
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U rootlearn rootlearn > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U rootlearn rootlearn | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore from Backup

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down backend frontend

# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U rootlearn rootlearn < backup.sql

# Or restore from compressed
gunzip -c backup.sql.gz | docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U rootlearn rootlearn

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Disaster Recovery

1. **Database failure**: Restore from latest backup
2. **Complete system failure**: Redeploy from Docker images and restore database
3. **Data corruption**: Restore from point-in-time backup

**Recovery Time Objective (RTO)**: < 1 hour
**Recovery Point Objective (RPO)**: < 24 hours (daily backups)

## Scaling

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=4

# Scale with load balancer
# Add nginx upstream configuration
```

### Vertical Scaling

Update resource limits in `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Database Scaling

- **Read replicas**: Configure PostgreSQL streaming replication
- **Connection pooling**: Use PgBouncer
- **Partitioning**: Partition large tables by session_id or created_at

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Check environment variables
docker-compose -f docker-compose.prod.yml config

# Check port conflicts
netstat -tuln | grep -E ':(3000|8000|5432)'
```

#### Database Connection Errors

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_isready -U rootlearn

# Check connection string
docker-compose -f docker-compose.prod.yml exec backend \
  env | grep DATABASE_URL

# Reset database connections
docker-compose -f docker-compose.prod.yml restart postgres
```

#### AI Provider Errors

```bash
# Verify API key
docker-compose -f docker-compose.prod.yml exec backend \
  env | grep -E '(OPENAI|ANTHROPIC|GOOGLE)_API_KEY'

# Test AI provider
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.ai.factory import get_ai_provider; provider = get_ai_provider(); print('OK')"
```

#### High Memory Usage

```bash
# Check container stats
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart backend

# Check for memory leaks in logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i "memory"
```

### Debug Mode

Enable debug logging temporarily:

```bash
# Set LOG_LEVEL=DEBUG
docker-compose -f docker-compose.prod.yml exec backend \
  env LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Support Resources

- Documentation: https://docs.rootlearn.com
- Issue Tracker: https://github.com/your-org/rootlearn/issues
- Slack: #rootlearn-support
