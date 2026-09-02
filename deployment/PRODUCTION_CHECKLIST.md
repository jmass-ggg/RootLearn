# Production Deployment Checklist

Use this checklist before deploying RootLearn to production.

## Pre-Deployment

### Environment Configuration

- [ ] `.env.production` file created from `.env.production.example`
- [ ] `POSTGRES_PASSWORD` set to strong password (32+ characters)
- [ ] `SECRET_KEY` generated using `openssl rand -hex 32`
- [ ] AI provider API key configured (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`)
- [ ] `AI_PROVIDER` set to correct provider (openai, anthropic, or gemini)
- [ ] `ALLOWED_ORIGINS` set to actual domain(s) (no wildcards)
- [ ] `NEXT_PUBLIC_API_URL` points to production backend URL
- [ ] `ENVIRONMENT` set to `production`
- [ ] `LOG_LEVEL` set to `INFO` or `WARNING`

### Security Configuration

- [ ] `SESSION_COOKIE_SECURE` set to `true`
- [ ] `SESSION_COOKIE_HTTPONLY` set to `true`
- [ ] `SESSION_COOKIE_SAMESITE` set to `strict`
- [ ] `CSRF_ENABLED` set to `true`
- [ ] `RATE_LIMIT_ENABLED` set to `true`
- [ ] SSL certificates obtained and configured
- [ ] Firewall rules configured
- [ ] Database password is strong and unique
- [ ] All secrets are environment variables (not in code)
- [ ] `.env.production` is in `.gitignore`

### Infrastructure

- [ ] Domain name registered and DNS configured
- [ ] SSL certificates installed (Let's Encrypt or commercial)
- [ ] Server meets minimum requirements (2GB RAM, 20GB disk)
- [ ] Docker and Docker Compose installed
- [ ] Postgres 16+ installed (or using Docker)
- [ ] Backup storage configured (local + S3)
- [ ] Monitoring endpoints accessible

### Database

- [ ] Database connection tested
- [ ] Initial migration reviewed: `alembic history`
- [ ] Backup strategy configured
- [ ] Database retention policy set (default: 30 days)
- [ ] Database credentials secured

### Monitoring and Alerting

- [ ] Sentry DSN configured (optional but recommended)
- [ ] New Relic license key set (optional)
- [ ] Prometheus scraping configured
- [ ] Grafana dashboards imported
- [ ] AlertManager notification channels configured
- [ ] PagerDuty integration set up for critical alerts
- [ ] Slack webhooks configured
- [ ] Email notifications configured

## Deployment

### Initial Deployment

- [ ] All environment variables verified
- [ ] Docker images pulled: `docker-compose -f docker-compose.prod.yml pull`
- [ ] Database started: `docker-compose -f docker-compose.prod.yml up -d postgres`
- [ ] Database health verified: `docker-compose -f docker-compose.prod.yml exec postgres pg_isready`
- [ ] Migrations executed: `docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head`
- [ ] All services started: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Backend health check passed: `curl http://localhost:8000/health`
- [ ] Frontend health check passed: `curl http://localhost:3000`
- [ ] Smoke tests passed: `./deployment/scripts/smoke-tests.sh`

### Subsequent Deployments

- [ ] Pre-deployment backup created: `./deployment/scripts/backup-database.sh`
- [ ] Pending migrations reviewed: `docker-compose exec backend alembic history`
- [ ] Deployment script executed: `./deployment/scripts/deploy.sh`
- [ ] Health checks passed
- [ ] Smoke tests passed
- [ ] No error alerts firing

## Post-Deployment

### Verification

- [ ] All services running: `docker-compose -f docker-compose.prod.yml ps`
- [ ] Backend responds: `curl http://localhost:8000/health/detailed`
- [ ] Frontend loads in browser
- [ ] API documentation accessible: `http://localhost:8000/docs`
- [ ] Metrics endpoint working: `curl http://localhost:8000/metrics`
- [ ] Session creation works (test via API or UI)
- [ ] AI provider connectivity verified
- [ ] Database queries working

### Monitoring

- [ ] Prometheus scraping backend: http://localhost:9090/targets
- [ ] Grafana dashboards displaying data
- [ ] Logs flowing to aggregation system
- [ ] Error tracking working (Sentry)
- [ ] Alerts configured and tested
- [ ] No critical alerts firing

### Performance

- [ ] API response time < 1s (p95)
- [ ] Frontend loads < 3s
- [ ] Database queries < 100ms (p95)
- [ ] Memory usage < 70%
- [ ] CPU usage < 60%
- [ ] Disk usage < 80%

### Security

- [ ] HTTPS working and certificate valid
- [ ] HTTP redirects to HTTPS
- [ ] Security headers present (check with securityheaders.com)
- [ ] CORS working correctly (only allowed origins)
- [ ] Rate limiting working (test by exceeding limits)
- [ ] CSRF protection enabled
- [ ] No secrets in logs
- [ ] No sensitive data in error responses

## Ongoing Operations

### Daily

- [ ] Check error rates in monitoring dashboard
- [ ] Review critical/warning alerts
- [ ] Verify backup completion
- [ ] Check AI provider costs
- [ ] Review application logs for errors

### Weekly

- [ ] Review session completion trends
- [ ] Analyze slow database queries
- [ ] Check disk space usage
- [ ] Review session abandonment rate
- [ ] Update alert thresholds if needed

### Monthly

- [ ] Review and update dependencies
- [ ] Test backup restore procedure
- [ ] Review security patches
- [ ] Analyze cost trends
- [ ] Review SLA compliance
- [ ] Update documentation
- [ ] Review and prune old logs

### Quarterly

- [ ] Disaster recovery drill
- [ ] Security audit
- [ ] Performance review
- [ ] Capacity planning
- [ ] Review and update runbooks

## Rollback Plan

If deployment fails:

### Immediate Actions

- [ ] Check logs: `docker-compose -f docker-compose.prod.yml logs --tail=100 backend`
- [ ] Check health: `curl http://localhost:8000/health/detailed`
- [ ] Review alerts in monitoring system

### Database Issues

- [ ] Stop application: `docker-compose -f docker-compose.prod.yml stop backend frontend`
- [ ] Restore from backup: `./deployment/scripts/restore-database.sh <backup_file>`
- [ ] Verify restore: `docker-compose -f docker-compose.prod.yml exec postgres psql -U rootlearn -c "SELECT COUNT(*) FROM learning_sessions"`
- [ ] Restart application: `docker-compose -f docker-compose.prod.yml up -d`

### Application Issues

- [ ] Roll back to previous Docker image tag
- [ ] Downgrade database migration if needed: `alembic downgrade -1`
- [ ] Restart services
- [ ] Verify health checks

### Communication

- [ ] Notify team of deployment status
- [ ] Update status page if public-facing
- [ ] Document issue in incident log
- [ ] Schedule post-mortem if needed

## Documentation

- [ ] Deployment documented in change log
- [ ] New features documented in user guide
- [ ] API changes documented
- [ ] Runbooks updated if procedures changed
- [ ] Known issues documented

## Compliance (if applicable)

- [ ] Data privacy requirements met (GDPR, CCPA)
- [ ] Audit logging enabled
- [ ] Data retention policies configured
- [ ] Terms of service updated
- [ ] Privacy policy updated

## Emergency Contacts

- On-call engineer: _________________
- Database admin: _________________
- Infrastructure lead: _________________
- PagerDuty: _________________
- Slack channel: #rootlearn-incidents

## Useful Commands

```bash
# Quick health check
curl http://localhost:8000/health/detailed

# View recent logs
docker-compose -f docker-compose.prod.yml logs --tail=50 backend

# Check service status
docker-compose -f docker-compose.prod.yml ps

# Create backup
./deployment/scripts/backup-database.sh

# Restore backup
./deployment/scripts/restore-database.sh <file>

# Restart service
docker-compose -f docker-compose.prod.yml restart backend

# View metrics
curl http://localhost:8000/metrics
```

## Sign-off

- [ ] Deployment lead: _________________ Date: _______
- [ ] Technical reviewer: _________________ Date: _______
- [ ] Security reviewer: _________________ Date: _______

---

**Note**: Check all items before considering deployment complete. If any item cannot be completed, document the reason and mitigation plan.
