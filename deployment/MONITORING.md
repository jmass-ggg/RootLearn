# Monitoring and Alerting Setup

## Overview

RootLearn implements comprehensive monitoring and observability through:
- Structured JSON logging with correlation IDs
- Prometheus metrics for application and system health
- Health check endpoints for load balancers
- Error tracking with Sentry (optional)
- Performance monitoring with APM tools (optional)

**Requirements**: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8

## Architecture

```
┌─────────────────┐
│   Application   │
│                 │
│  - Logs (JSON)  │────┐
│  - Metrics      │───┐│
│  - Traces       │──┐││
└─────────────────┘  │││
                     │││
        ┌────────────┘││
        │  ┌──────────┘│
        │  │  ┌────────┘
        ▼  ▼  ▼
┌────────────────────────────┐
│   Observability Stack      │
│                            │
│  ┌──────────────────────┐  │
│  │  Loki / ELK          │  │  Log Aggregation
│  │  (Log Storage)       │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │  Prometheus          │  │  Metrics Storage
│  │  (Time Series DB)    │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │  Jaeger / Zipkin     │  │  Distributed Tracing
│  │  (Trace Storage)     │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │  Grafana             │  │  Visualization
│  │  (Dashboards)        │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │  AlertManager        │  │  Alerting
│  │  (Alert Routing)     │  │
│  └──────────────────────┘  │
└────────────────────────────┘
```

## Structured Logging

### Log Format

All services emit structured JSON logs to stdout/stderr:

```json
{
  "timestamp": "2026-09-02T10:00:00.000Z",
  "level": "INFO",
  "service": "rootlearn-backend",
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user-uuid-here",
  "session_id": "session-uuid-here",
  "message": "Session created successfully",
  "duration_ms": 45,
  "endpoint": "/api/v1/sessions",
  "method": "POST",
  "status_code": 201
}
```

### Log Levels

- **DEBUG**: Detailed diagnostic information (development only)
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors requiring immediate attention

### Correlation IDs

**Requirement**: 20.1

Every request gets a unique correlation ID (`request_id`) that:
- Is generated at API entry point
- Propagates through all services
- Appears in all log lines for that request
- Is returned in API responses via `X-Request-ID` header

**Usage**:
```python
# Backend automatically adds request_id to all logs
logger.info("Operation completed", extra={
    "operation": "graph_generation",
    "concept_count": 8
})
```

### Key Log Events

**Requirement**: 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8

#### API Request Logging
```json
{
  "level": "INFO",
  "message": "API request completed",
  "endpoint": "/api/v1/sessions",
  "method": "POST",
  "status_code": 201,
  "latency_ms": 145,
  "request_id": "..."
}
```

#### AI Operation Logging
```json
{
  "level": "INFO",
  "message": "AI request completed",
  "provider": "openai",
  "model": "gpt-4-turbo-preview",
  "purpose": "generate_diagnostic_question",
  "prompt_tokens": 450,
  "completion_tokens": 120,
  "latency_ms": 2340,
  "success": true,
  "cost_usd": 0.0234,
  "request_id": "..."
}
```

#### AI Failure Logging
```json
{
  "level": "ERROR",
  "message": "AI request failed",
  "provider": "openai",
  "error_code": "rate_limit_exceeded",
  "error_message": "Rate limit exceeded",
  "retry_attempt": 2,
  "request_id": "..."
}
```

#### Session Lifecycle
```json
{
  "level": "INFO",
  "message": "Session completed",
  "session_id": "...",
  "user_id": "...",
  "completion_status": "completed",
  "total_duration_minutes": 18,
  "diagnostic_questions": 4,
  "concepts_mastered": 3,
  "mastery_improvement": 0.42
}
```

## Prometheus Metrics

### Metrics Endpoint

**Requirement**: 20.1

Metrics are exposed at `/metrics` in Prometheus format:

```bash
curl http://localhost:8000/metrics
```

### Application Metrics

#### Session Metrics

**Requirement**: 20.6

```prometheus
# Total sessions created
rootlearn_sessions_created_total{status="analyzing|diagnosing|tutoring|teachback|completed|abandoned"}

# Session completion rate
rootlearn_sessions_completed_total
rootlearn_sessions_abandoned_total

# Session duration
rootlearn_session_duration_seconds{status="completed|abandoned"}
```

**Usage**:
```promql
# Completion rate
rate(rootlearn_sessions_completed_total[5m]) / 
rate(rootlearn_sessions_created_total[5m])

# Average session duration
rate(rootlearn_session_duration_seconds_sum[5m]) /
rate(rootlearn_session_duration_seconds_count[5m])
```

#### Diagnostic Metrics

**Requirement**: 20.5

```prometheus
# Diagnostic questions asked
rootlearn_diagnostic_questions_total{concept="...",difficulty="..."}

# Diagnostic questions per session
rootlearn_diagnostic_questions_per_session
```

**Usage**:
```promql
# Average questions per session
rate(rootlearn_diagnostic_questions_total[5m]) /
rate(rootlearn_sessions_created_total[5m])
```

#### Mastery Metrics

**Requirement**: 20.7

```prometheus
# Mastery score changes
rootlearn_mastery_score_average{concept="..."}
rootlearn_mastery_score_improvement{concept="..."}

# Mastery events
rootlearn_mastery_events_total{source_type="diagnostic|tutoring|teachback"}
```

**Usage**:
```promql
# Average mastery improvement
avg(rootlearn_mastery_score_improvement)

# Mastery changes by source
rate(rootlearn_mastery_events_total[5m])
```

#### AI Provider Metrics

**Requirement**: 20.3, 20.8

```prometheus
# AI requests
rootlearn_ai_requests_total{provider="openai|anthropic|gemini",purpose="...",status="success|failure"}

# AI request duration
rootlearn_ai_request_duration_seconds{provider="...",purpose="..."}

# AI token usage
rootlearn_ai_tokens_total{provider="...",token_type="prompt|completion"}

# AI costs
rootlearn_ai_cost_usd_total{provider="..."}

# AI errors
rootlearn_ai_errors_total{provider="...",error_code="..."}
```

**Usage**:
```promql
# AI error rate
rate(rootlearn_ai_errors_total[5m]) /
rate(rootlearn_ai_requests_total[5m])

# Average AI latency
histogram_quantile(0.95, 
  rate(rootlearn_ai_request_duration_seconds_bucket[5m]))

# Total AI cost
sum(rate(rootlearn_ai_cost_usd_total[1h]))
```

#### API Metrics

**Requirement**: 20.3

```prometheus
# API requests
rootlearn_api_requests_total{method="GET|POST|DELETE",endpoint="...",status_code="..."}

# API request duration
rootlearn_api_request_duration_seconds{method="...",endpoint="..."}

# API errors
rootlearn_api_errors_total{endpoint="...",error_type="..."}
```

**Usage**:
```promql
# API error rate
rate(rootlearn_api_errors_total[5m]) /
rate(rootlearn_api_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95,
  rate(rootlearn_api_request_duration_seconds_bucket[5m]))
```

#### System Metrics

```prometheus
# Database connections
rootlearn_db_connections_active
rootlearn_db_connections_idle
rootlearn_db_pool_size

# Database query duration
rootlearn_db_query_duration_seconds{operation="..."}
```

### Custom Metrics in Code

```python
from prometheus_client import Counter, Histogram, Gauge

# Counter
sessions_created = Counter(
    'rootlearn_sessions_created_total',
    'Total sessions created',
    ['status']
)
sessions_created.labels(status='analyzing').inc()

# Histogram
api_latency = Histogram(
    'rootlearn_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)
with api_latency.labels(method='POST', endpoint='/api/v1/sessions').time():
    # Execute request
    pass

# Gauge
active_sessions = Gauge(
    'rootlearn_active_sessions',
    'Number of active sessions'
)
active_sessions.set(42)
```

## Health Checks

### Endpoints

#### Basic Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-09-02T10:00:00Z"
}
```

#### Detailed Health Check
```bash
GET /health/detailed
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-09-02T10:00:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 5
    },
    "ai_provider": {
      "status": "healthy",
      "provider": "openai",
      "latency_ms": 234
    },
    "redis": {
      "status": "degraded",
      "latency_ms": 1500
    }
  }
}
```

#### Readiness Check
```bash
GET /ready
```

Returns 200 if ready to serve traffic, 503 otherwise.

### Load Balancer Configuration

**AWS ALB**:
```hcl
health_check {
  path                = "/health"
  interval            = 30
  timeout             = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3
  matcher             = "200"
}
```

**Kubernetes**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

## Dashboards

### Grafana Setup

#### Install Grafana

```bash
# Docker
docker run -d -p 3001:3000 --name=grafana grafana/grafana

# Or add to docker-compose.prod.yml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana_data:/var/lib/grafana
    - ./deployment/grafana/dashboards:/etc/grafana/provisioning/dashboards
    - ./deployment/grafana/datasources:/etc/grafana/provisioning/datasources
```

#### Configure Prometheus Data Source

Create `deployment/grafana/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

### Pre-Built Dashboards

#### 1. System Overview Dashboard

**Metrics**:
- Sessions created (rate)
- Session completion rate
- Active sessions
- API request rate
- API error rate
- AI request rate
- AI error rate

#### 2. AI Performance Dashboard

**Metrics**:
- AI latency by provider (p50, p95, p99)
- AI error rate by provider
- Token usage by provider
- Cost per session
- Total AI spend

#### 3. Learning Analytics Dashboard

**Metrics**:
- Diagnostic questions per session
- Average mastery improvement
- Concepts mastered per session
- Session duration distribution
- Abandonment reasons

#### 4. System Health Dashboard

**Metrics**:
- CPU usage
- Memory usage
- Database connections
- Database query latency
- HTTP response times
- Error rates by endpoint

### Sample Grafana Queries

```promql
# API request rate
rate(rootlearn_api_requests_total[5m])

# Error rate percentage
100 * (
  rate(rootlearn_api_errors_total[5m]) /
  rate(rootlearn_api_requests_total[5m])
)

# 95th percentile API latency
histogram_quantile(0.95,
  rate(rootlearn_api_request_duration_seconds_bucket[5m])
)

# AI cost per hour
sum(rate(rootlearn_ai_cost_usd_total[1h])) * 3600

# Session completion rate
rate(rootlearn_sessions_completed_total[5m]) /
rate(rootlearn_sessions_created_total[5m])
```

## Alerting

### AlertManager Setup

#### Install AlertManager

```bash
# Docker
docker run -d -p 9093:9093 \
  -v ./deployment/alertmanager/config.yml:/etc/alertmanager/config.yml \
  prom/alertmanager
```

#### Configure AlertManager

`deployment/alertmanager/config.yml`:

```yaml
global:
  resolve_timeout: 5m
  
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'team-notifications'
  
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'team-notifications'
    email_configs:
      - to: 'team@rootlearn.com'
        from: 'alerts@rootlearn.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@rootlearn.com'
        auth_password: '${SMTP_PASSWORD}'
  
  - name: 'slack'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#rootlearn-alerts'
        title: 'RootLearn Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'
  
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
```

### Alert Rules

`deployment/prometheus/rules.yml`:

```yaml
groups:
  - name: rootlearn_critical
    interval: 1m
    rules:
      - alert: HighAPIErrorRate
        expr: |
          (
            rate(rootlearn_api_errors_total[5m]) /
            rate(rootlearn_api_requests_total[5m])
          ) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate"
          description: "API error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
      
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is unreachable"
          description: "PostgreSQL database has been down for 1 minute"
      
      - alert: AIProviderFailure
        expr: |
          (
            rate(rootlearn_ai_errors_total[5m]) /
            rate(rootlearn_ai_requests_total[5m])
          ) > 0.10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High AI provider error rate"
          description: "AI error rate is {{ $value | humanizePercentage }} for {{ $labels.provider }}"
      
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(rootlearn_api_request_duration_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is {{ $value }}s (threshold: 2s)"
      
      - alert: HighMemoryUsage
        expr: |
          (
            container_memory_usage_bytes{name="rootlearn-backend"} /
            container_spec_memory_limit_bytes{name="rootlearn-backend"}
          ) > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"
      
      - alert: HighSessionAbandonmentRate
        expr: |
          (
            rate(rootlearn_sessions_abandoned_total[1h]) /
            rate(rootlearn_sessions_created_total[1h])
          ) > 0.30
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High session abandonment rate"
          description: "{{ $value | humanizePercentage }} of sessions are being abandoned"
      
      - alert: AIBudgetExceeded
        expr: |
          sum(rate(rootlearn_ai_cost_usd_total[1h])) * 24 > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "AI daily budget on track to exceed $100"
          description: "Current rate: ${{ $value }}/day"
```

### Notification Channels

#### Slack Integration

1. Create Slack Incoming Webhook
2. Add to AlertManager config:

```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#rootlearn-alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: |
      {{ range .Alerts }}
      *Alert:* {{ .Annotations.summary }}
      *Description:* {{ .Annotations.description }}
      *Severity:* {{ .Labels.severity }}
      {{ end }}
```

#### PagerDuty Integration

1. Create PagerDuty service
2. Get integration key
3. Add to AlertManager config

#### Email Alerts

Configure SMTP in AlertManager for email notifications.

## Error Tracking with Sentry

### Setup

```bash
# Install Sentry SDK
pip install sentry-sdk

# Configure in app
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
)
```

### Captured Events

- Unhandled exceptions
- AI provider errors
- Database connection errors
- Validation failures
- Performance transactions (sampled)

### Custom Context

```python
from sentry_sdk import set_context, set_user

# Add user context
set_user({"id": user_id, "email": user_email})

# Add custom context
set_context("session", {
    "session_id": session_id,
    "status": session_status,
    "concepts": concept_count
})
```

## Performance Monitoring

### Application Performance Monitoring (APM)

Options:
- **Sentry Performance**: Built-in with Sentry
- **New Relic APM**: Comprehensive monitoring
- **Datadog APM**: Full-stack observability
- **OpenTelemetry**: Vendor-neutral instrumentation

### Key Performance Indicators

1. **API Latency**: p50, p95, p99 response times
2. **AI Latency**: Time for AI operations
3. **Database Latency**: Query execution time
4. **Session Duration**: Time to complete learning session
5. **Error Rates**: API, AI, database errors
6. **Throughput**: Requests per second

## Maintenance Tasks

### Daily
- Review error rates and critical alerts
- Check AI provider costs
- Verify backup completion

### Weekly
- Review session completion trends
- Analyze slow queries
- Check disk space usage
- Review abandonment reasons

### Monthly
- Review and update alert thresholds
- Analyze cost trends
- Update dashboards
- Review SLA compliance

## Troubleshooting

### High Error Rate

1. Check AlertManager for active alerts
2. Review error logs: `docker-compose logs backend | grep ERROR`
3. Check Sentry for exception details
4. Verify external dependencies (database, AI provider)

### High Latency

1. Check API latency metrics in Grafana
2. Identify slow endpoints
3. Review database query performance
4. Check AI provider latency
5. Verify resource utilization (CPU, memory)

### Missing Metrics

1. Verify Prometheus is scraping: `http://localhost:9090/targets`
2. Check application `/metrics` endpoint
3. Review Prometheus logs
4. Verify network connectivity

## Best Practices

1. **Alert Fatigue Prevention**
   - Set appropriate thresholds
   - Use `for` clauses to avoid flapping
   - Group related alerts
   - Route by severity

2. **Dashboard Design**
   - Focus on actionable metrics
   - Use consistent time ranges
   - Include baseline comparisons
   - Add annotations for deployments

3. **Log Management**
   - Use structured logging
   - Include correlation IDs
   - Set appropriate log levels
   - Implement log rotation

4. **Cost Management**
   - Monitor AI usage and costs
   - Set budget alerts
   - Review and optimize queries
   - Archive old logs
