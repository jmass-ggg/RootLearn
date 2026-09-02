# RootLearn Deployment

This directory contains all deployment configuration, scripts, and documentation for RootLearn.

## Contents

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Complete deployment guide
- **[ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)** - Environment variable reference
- **[MONITORING.md](./MONITORING.md)** - Monitoring and alerting setup
- **scripts/** - Deployment automation scripts
- **nginx/** - Nginx reverse proxy configuration
- **grafana/** - Grafana dashboards (to be added)
- **prometheus/** - Prometheus configuration (to be added)
- **alertmanager/** - AlertManager configuration (to be added)

## Quick Start

### Development

```bash
# Start local development environment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# 1. Configure environment
cp .env.production.example .env.production
# Edit .env.production with your values

# 2. Deploy
./deployment/scripts/deploy.sh

# 3. Monitor
docker-compose -f docker-compose.prod.yml logs -f
```

## Documentation

### [DEPLOYMENT.md](./DEPLOYMENT.md)
Complete deployment guide covering:
- Prerequisites and system requirements
- Environment configuration
- Database migration strategy
- Step-by-step deployment instructions
- Backup and recovery procedures
- Scaling strategies
- Troubleshooting guide

### [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)
Comprehensive reference for all environment variables:
- Database configuration
- AI provider settings
- Security configuration
- Rate limiting
- Monitoring and observability
- Performance tuning
- Feature flags

### [MONITORING.md](./MONITORING.md)
Monitoring and alerting setup:
- Structured logging
- Prometheus metrics
- Health check endpoints
- Grafana dashboards
- Alert rules
- Error tracking with Sentry

## Scripts

All scripts are located in `scripts/` directory:

### backup-database.sh
Creates compressed PostgreSQL backup with timestamp.

```bash
./deployment/scripts/backup-database.sh
```

Features:
- Automatic timestamp
- Compression (gzip)
- Retention policy (default: 30 days)
- Optional S3 upload

### restore-database.sh
Restores database from backup file.

```bash
./deployment/scripts/restore-database.sh <backup_file.sql.gz>
```

Features:
- Safety backup before restore
- Service management (stop/start)
- Health verification

### deploy.sh
Complete deployment automation.

```bash
./deployment/scripts/deploy.sh
```

Features:
- Pre-deployment checks
- Automatic backup
- Database migrations
- Health checks
- Smoke tests
- Rollback on failure

### smoke-tests.sh
Quick validation of deployment.

```bash
./deployment/scripts/smoke-tests.sh
```

Tests:
- Backend health endpoint
- Frontend availability
- Database connectivity
- API functionality

## Configuration Files

### docker-compose.prod.yml
Production Docker Compose configuration with:
- PostgreSQL with health checks
- Backend with auto-restart
- Frontend with auto-restart
- Redis (optional)
- Nginx reverse proxy (optional)
- Proper networking and volumes
- Logging configuration

### .env.production.example
Template for production environment variables with:
- All required variables
- Secure defaults
- Documentation comments
- Security checklist

### nginx/nginx.conf
Production-ready Nginx configuration with:
- SSL/TLS termination
- HTTP to HTTPS redirect
- Reverse proxy to backend and frontend
- Rate limiting
- Security headers
- Static asset caching
- WebSocket support

## Security Checklist

Before deploying to production:

- [ ] Set strong passwords for all services
- [ ] Configure SSL certificates
- [ ] Set ALLOWED_ORIGINS to your domain only
- [ ] Enable all security headers
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerts
- [ ] Configure automated backups
- [ ] Test restore procedure
- [ ] Review and update firewall rules
- [ ] Enable CSRF protection
- [ ] Use secure session cookies
- [ ] Rotate secrets regularly

## Migration Strategy

### Initial Deployment
1. Start PostgreSQL
2. Run migrations: `alembic upgrade head`
3. Start application services

### Subsequent Deployments
1. Backup database
2. Pull latest images
3. Run migrations
4. Rolling restart services
5. Verify health checks
6. Run smoke tests

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed migration strategies.

## Monitoring

### Health Checks
- **Basic**: `GET /health` - Simple health check
- **Detailed**: `GET /health/detailed` - With dependencies
- **Ready**: `GET /ready` - Load balancer check

### Metrics
- **Application**: `/metrics` - Prometheus format
- **Dashboards**: Grafana (port 3001)
- **Logs**: JSON structured logs

### Alerts
Critical alerts configured:
- High API error rate
- Database connectivity
- AI provider failures
- High latency
- High memory usage

See [MONITORING.md](./MONITORING.md) for complete monitoring setup.

## Backup Strategy

### Automated Backups
```bash
# Configure cron job
0 2 * * * /path/to/deployment/scripts/backup-database.sh
```

### Manual Backups
```bash
./deployment/scripts/backup-database.sh
```

### Retention Policy
- Daily backups kept for 30 days
- Weekly backups kept for 90 days
- Monthly backups kept for 1 year

### Backup Locations
- Local: `./backups/`
- Remote: S3 bucket (optional)

## Disaster Recovery

### Recovery Time Objective (RTO)
< 1 hour

### Recovery Point Objective (RPO)
< 24 hours (daily backups)

### Recovery Procedure
1. Identify failure type
2. Stop affected services
3. Restore from latest backup
4. Verify data integrity
5. Start services
6. Run smoke tests

## Support

For issues or questions:
- **Documentation**: See docs in this directory
- **Logs**: `docker-compose logs -f`
- **Health**: `curl http://localhost:8000/health/detailed`
- **Metrics**: `curl http://localhost:8000/metrics`

## License

See main project LICENSE file.
