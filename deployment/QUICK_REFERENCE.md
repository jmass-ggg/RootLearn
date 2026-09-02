# RootLearn Deployment Quick Reference

## Common Commands

### Development

```bash
# Start local environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Production

```bash
# Deploy (automated)
./deployment/scripts/deploy.sh

# Manual deployment steps
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Database Operations

```bash
# Backup database
./deployment/scripts/backup-database.sh

# Restore database
./deployment/scripts/restore-database.sh <backup_file.sql.gz>

# Check migration status
docker-compose -f docker-compose.prod.yml exec backend alembic current

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Rollback one migration
docker-compose -f docker-compose.prod.yml exec backend alembic downgrade -1

# View migration history
docker-compose -f docker-compose.prod.yml exec backend alembic history
```

### Monitoring

```bash
# Health check
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed

# Metrics
curl http://localhost:8000/metrics

# Smoke tests
./deployment/scripts/smoke-tests.sh
```

### Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Follow with timestamps
docker-compose -f docker-compose.prod.yml logs -f -t backend
```

### Container Management

```bash
# Restart a service
docker-compose -f docker-compose.prod.yml restart backend

# Scale a service
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Execute command in container
docker-compose -f docker-compose.prod.yml exec backend bash

# View container stats
docker stats
```

### Troubleshooting

```bash
# Check container health
docker-compose -f docker-compose.prod.yml ps

# Inspect container
docker inspect rootlearn-backend-prod

# View container logs
docker logs rootlearn-backend-prod

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U rootlearn

# Test AI provider
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.ai.factory import get_ai_provider; print('OK')"

# Check environment variables
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE_URL
```

### Cleanup

```bash
# Remove stopped containers
docker-compose -f docker-compose.prod.yml rm

# Remove unused images
docker image prune -f

# Remove unused volumes (WARNING: deletes data)
docker volume prune -f

# Full cleanup (WARNING: removes everything)
docker-compose -f docker-compose.prod.yml down -v
docker system prune -a -f
```

## File Locations

```
.env.production              # Production environment config
docker-compose.prod.yml      # Production compose file
deployment/
  ├── DEPLOYMENT.md          # Full deployment guide
  ├── ENVIRONMENT_VARIABLES.md  # Variable reference
  ├── MONITORING.md          # Monitoring setup
  ├── scripts/
  │   ├── backup-database.sh    # Backup script
  │   ├── restore-database.sh   # Restore script
  │   ├── deploy.sh             # Deployment automation
  │   └── smoke-tests.sh        # Quick validation
  ├── nginx/
  │   └── nginx.conf            # Nginx config
  ├── prometheus/
  │   ├── prometheus.yml        # Prometheus config
  │   └── rules.yml             # Alert rules
  └── alertmanager/
      └── config.yml            # AlertManager config
```

## Emergency Procedures

### Service Won't Start

```bash
# 1. Check logs
docker-compose -f docker-compose.prod.yml logs backend

# 2. Check configuration
docker-compose -f docker-compose.prod.yml config

# 3. Restart service
docker-compose -f docker-compose.prod.yml restart backend

# 4. Rebuild if needed
docker-compose -f docker-compose.prod.yml up -d --build backend
```

### Database Connection Error

```bash
# 1. Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# 2. Check connectivity
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U rootlearn

# 3. Restart database
docker-compose -f docker-compose.prod.yml restart postgres

# 4. Check connection string
docker-compose -f docker-compose.prod.yml exec backend \
  env | grep DATABASE_URL
```

### High Memory Usage

```bash
# 1. Check stats
docker stats

# 2. Restart service
docker-compose -f docker-compose.prod.yml restart backend

# 3. Check for memory leaks in logs
docker-compose -f docker-compose.prod.yml logs backend | grep -i memory
```

### Restore from Backup

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down backend frontend

# 2. List available backups
ls -lh ./backups/

# 3. Restore
./deployment/scripts/restore-database.sh ./backups/rootlearn_backup_YYYYMMDD_HHMMSS.sql.gz

# 4. Verify
curl http://localhost:8000/health/detailed
```

## URLs

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Metrics: http://localhost:8000/metrics
- Health: http://localhost:8000/health
- Prometheus: http://localhost:9090 (if configured)
- Grafana: http://localhost:3001 (if configured)
- AlertManager: http://localhost:9093 (if configured)

## Environment Variables

See [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md) for complete reference.

### Critical Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# AI Provider
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Security
SECRET_KEY=...  # Generate with: openssl rand -hex 32
ALLOWED_ORIGINS=https://yourdomain.com

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Support

- Documentation: See deployment/*.md files
- Logs: `docker-compose logs -f`
- Health: `curl http://localhost:8000/health/detailed`
- Metrics: `curl http://localhost:8000/metrics`
