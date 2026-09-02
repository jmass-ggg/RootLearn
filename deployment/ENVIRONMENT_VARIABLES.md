# Environment Variables Reference

Complete reference for all environment variables used in RootLearn.

## Table of Contents
1. [Database Configuration](#database-configuration)
2. [AI Provider Configuration](#ai-provider-configuration)
3. [Application Configuration](#application-configuration)
4. [Security Configuration](#security-configuration)
5. [Rate Limiting](#rate-limiting)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Performance Tuning](#performance-tuning)
8. [Feature Flags](#feature-flags)

---

## Database Configuration

### `DATABASE_URL`
**Required**: Yes  
**Type**: String (Connection URL)  
**Default**: None  
**Example**: `postgresql+asyncpg://rootlearn:password@localhost:5432/rootlearn`

Full PostgreSQL connection URL using asyncpg driver.

**Format**: `postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE`

### `POSTGRES_USER`
**Required**: Yes (for Docker)  
**Type**: String  
**Default**: `rootlearn`  
**Example**: `rootlearn`

PostgreSQL database username.

### `POSTGRES_PASSWORD`
**Required**: Yes (for Docker)  
**Type**: String  
**Default**: None  
**Example**: `super_secure_password_123`

PostgreSQL database password. **Must be secure in production.**

**Security**: Generate with `openssl rand -base64 32`

### `POSTGRES_DB`
**Required**: Yes (for Docker)  
**Type**: String  
**Default**: `rootlearn`  
**Example**: `rootlearn`

PostgreSQL database name.

### `POSTGRES_PORT`
**Required**: No  
**Type**: Integer  
**Default**: `5432`  
**Example**: `5432`

PostgreSQL port number.

---

## AI Provider Configuration

### `AI_PROVIDER`
**Required**: Yes  
**Type**: Enum  
**Default**: `openai`  
**Options**: `openai`, `anthropic`, `gemini`  
**Example**: `openai`

Which AI provider to use for semantic tasks.

### OpenAI Configuration

#### `OPENAI_API_KEY`
**Required**: If using OpenAI  
**Type**: String (API Key)  
**Default**: None  
**Example**: `sk-proj-abc123...`

OpenAI API key. Get from: https://platform.openai.com/api-keys

**Security**: Never commit to version control. Use environment variables or secrets manager.

#### `OPENAI_MODEL`
**Required**: No  
**Type**: String  
**Default**: `gpt-4-turbo-preview`  
**Example**: `gpt-4-turbo-preview`

OpenAI model to use.

**Options**:
- `gpt-4-turbo-preview` - Most capable, higher cost
- `gpt-4` - Previous generation
- `gpt-3.5-turbo` - Faster, lower cost

#### `OPENAI_MAX_TOKENS`
**Required**: No  
**Type**: Integer  
**Default**: `4096`  
**Example**: `4096`

Maximum tokens per AI request.

#### `OPENAI_TEMPERATURE`
**Required**: No  
**Type**: Float (0.0 - 2.0)  
**Default**: `0.7`  
**Example**: `0.7`

Sampling temperature for AI responses.

### Anthropic Configuration

#### `ANTHROPIC_API_KEY`
**Required**: If using Anthropic  
**Type**: String (API Key)  
**Default**: None  
**Example**: `sk-ant-abc123...`

Anthropic API key. Get from: https://console.anthropic.com/

#### `ANTHROPIC_MODEL`
**Required**: No  
**Type**: String  
**Default**: `claude-3-sonnet-20240229`  
**Example**: `claude-3-sonnet-20240229`

Anthropic model to use.

**Options**:
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fastest, lowest cost

#### `ANTHROPIC_MAX_TOKENS`
**Required**: No  
**Type**: Integer  
**Default**: `4096`  
**Example**: `4096`

Maximum tokens per AI request.

### Google Gemini Configuration

#### `GOOGLE_API_KEY`
**Required**: If using Gemini  
**Type**: String (API Key)  
**Default**: None  
**Example**: `AIzaSy...`

Google API key. Get from: https://makersuite.google.com/app/apikey

#### `GOOGLE_MODEL`
**Required**: No  
**Type**: String  
**Default**: `gemini-pro`  
**Example**: `gemini-pro`

Google model to use.

---

## Application Configuration

### `ENVIRONMENT`
**Required**: Yes  
**Type**: Enum  
**Default**: `development`  
**Options**: `development`, `staging`, `production`  
**Example**: `production`

Application environment. Affects logging, error handling, and security features.

### `LOG_LEVEL`
**Required**: No  
**Type**: Enum  
**Default**: `INFO`  
**Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`  
**Example**: `INFO`

Logging verbosity level.

**Recommendations**:
- Development: `DEBUG`
- Staging: `INFO`
- Production: `INFO` or `WARNING`

### `LOG_FORMAT`
**Required**: No  
**Type**: Enum  
**Default**: `json`  
**Options**: `json`, `text`  
**Example**: `json`

Log output format. Use `json` for production (better for log aggregation).

### `API_V1_PREFIX`
**Required**: No  
**Type**: String  
**Default**: `/api/v1`  
**Example**: `/api/v1`

API URL prefix for versioning.

### `API_TITLE`
**Required**: No  
**Type**: String  
**Default**: `RootLearn API`  
**Example**: `RootLearn API`

API title (shown in docs).

### `API_VERSION`
**Required**: No  
**Type**: String  
**Default**: `1.0.0`  
**Example**: `1.0.0`

API version number.

### `BACKEND_PORT`
**Required**: No  
**Type**: Integer  
**Default**: `8000`  
**Example**: `8000`

Backend server port.

### `FRONTEND_PORT`
**Required**: No  
**Type**: Integer  
**Default**: `3000`  
**Example**: `3000`

Frontend server port.

### `ALLOWED_ORIGINS`
**Required**: Yes  
**Type**: String (comma-separated)  
**Default**: `http://localhost:3000`  
**Example**: `https://app.rootlearn.com,https://www.app.rootlearn.com`

CORS allowed origins. **Critical for security.**

**Format**: Comma-separated list of full URLs (including protocol)

**Development**: `http://localhost:3000`  
**Production**: `https://yourdomain.com,https://www.yourdomain.com`

---

## Security Configuration

### `SECRET_KEY`
**Required**: Yes  
**Type**: String  
**Default**: None  
**Example**: `a1b2c3d4e5f6...` (32+ bytes hex)

Secret key for cryptographic operations (JWT, sessions, etc.).

**Security**: Generate with `openssl rand -hex 32`  
**Important**: Different for each environment. Never reuse or commit to git.

### `SESSION_COOKIE_SECURE`
**Required**: No  
**Type**: Boolean  
**Default**: `true` (production), `false` (development)  
**Example**: `true`

Enable secure flag on session cookies (HTTPS only).

**Must be `true` in production.**

### `SESSION_COOKIE_HTTPONLY`
**Required**: No  
**Type**: Boolean  
**Default**: `true`  
**Example**: `true`

Enable HTTP-only flag on session cookies (prevents XSS).

**Must be `true` in production.**

### `SESSION_COOKIE_SAMESITE`
**Required**: No  
**Type**: Enum  
**Default**: `strict`  
**Options**: `strict`, `lax`, `none`  
**Example**: `strict`

SameSite cookie attribute (CSRF protection).

### `SESSION_MAX_AGE`
**Required**: No  
**Type**: Integer (seconds)  
**Default**: `86400` (24 hours)  
**Example**: `86400`

Session cookie max age.

### `CSRF_ENABLED`
**Required**: No  
**Type**: Boolean  
**Default**: `true`  
**Example**: `true`

Enable CSRF protection.

**Must be `true` in production.**

---

## Rate Limiting

### `RATE_LIMIT_ENABLED`
**Required**: No  
**Type**: Boolean  
**Default**: `true`  
**Example**: `true`

Enable rate limiting. **Should be `true` in production.**

### `RATE_LIMIT_SESSION_CREATION`
**Required**: No  
**Type**: Integer  
**Default**: `20`  
**Example**: `20`

Maximum session creations per user per hour.

**Requirement**: 17.1

### `RATE_LIMIT_TUTOR_TURNS`
**Required**: No  
**Type**: Integer  
**Default**: `120`  
**Example**: `120`

Maximum tutor turns per user per hour.

**Requirement**: 17.2

### `RATE_LIMIT_TEACHBACK`
**Required**: No  
**Type**: Integer  
**Default**: `40`  
**Example**: `40`

Maximum teach-back evaluations per user per hour.

**Requirement**: 17.3

### `RATE_LIMIT_AI_PER_SESSION`
**Required**: No  
**Type**: Integer  
**Default**: `30`  
**Example**: `30`

Maximum AI calls per learning session.

**Requirement**: 17.4

---

## Monitoring and Observability

### `ENABLE_METRICS`
**Required**: No  
**Type**: Boolean  
**Default**: `true`  
**Example**: `true`

Enable Prometheus metrics endpoint at `/metrics`.

**Requirement**: 20.1

### `METRICS_PORT`
**Required**: No  
**Type**: Integer  
**Default**: `9090`  
**Example**: `9090`

Port for metrics endpoint.

### `ENABLE_TRACING`
**Required**: No  
**Type**: Boolean  
**Default**: `false`  
**Example**: `true`

Enable distributed tracing.

### `TRACING_SERVICE_NAME`
**Required**: If tracing enabled  
**Type**: String  
**Default**: `rootlearn-backend`  
**Example**: `rootlearn-backend`

Service name for distributed traces.

### Sentry Configuration

#### `SENTRY_DSN`
**Required**: If using Sentry  
**Type**: String (DSN URL)  
**Default**: None  
**Example**: `https://abc123@o123.ingest.sentry.io/456`

Sentry Data Source Name for error tracking.

#### `SENTRY_ENVIRONMENT`
**Required**: If using Sentry  
**Type**: String  
**Default**: Same as `ENVIRONMENT`  
**Example**: `production`

Environment tag for Sentry events.

#### `SENTRY_TRACES_SAMPLE_RATE`
**Required**: No  
**Type**: Float (0.0 - 1.0)  
**Default**: `0.1`  
**Example**: `0.1`

Percentage of transactions to trace (performance monitoring).

**Recommendation**: 
- Development: `1.0` (100%)
- Production: `0.1` (10%)

### New Relic Configuration

#### `NEW_RELIC_LICENSE_KEY`
**Required**: If using New Relic  
**Type**: String  
**Default**: None  
**Example**: `abc123...`

New Relic license key.

#### `NEW_RELIC_APP_NAME`
**Required**: If using New Relic  
**Type**: String  
**Default**: `RootLearn`  
**Example**: `RootLearn`

Application name in New Relic.

---

## Performance Tuning

### `DB_POOL_SIZE`
**Required**: No  
**Type**: Integer  
**Default**: `20`  
**Example**: `20`

Database connection pool size.

**Tuning**: 
- Low traffic: `10-20`
- High traffic: `50-100`
- Consider: (2 × CPU cores) + effective_spindle_count

### `DB_MAX_OVERFLOW`
**Required**: No  
**Type**: Integer  
**Default**: `10`  
**Example**: `10`

Additional connections beyond pool size.

### `DB_POOL_TIMEOUT`
**Required**: No  
**Type**: Integer (seconds)  
**Default**: `30`  
**Example**: `30`

Timeout waiting for connection from pool.

### `WORKERS`
**Required**: No  
**Type**: Integer  
**Default**: `4`  
**Example**: `4`

Number of Uvicorn worker processes.

**Tuning**: `(2 × CPU cores) + 1`

### `REQUEST_TIMEOUT`
**Required**: No  
**Type**: Integer (seconds)  
**Default**: `60`  
**Example**: `60`

Maximum request processing time.

### `MAX_REQUEST_SIZE`
**Required**: No  
**Type**: Integer (MB)  
**Default**: `10`  
**Example**: `10`

Maximum request body size.

---

## Feature Flags

### `FEATURE_TEACHBACK_ENABLED`
**Required**: No  
**Type**: Boolean  
**Default**: `true`  
**Example**: `true`

Enable teach-back verification feature.

### `FEATURE_GRAPH_VISUALIZATION`
**Required**: No  
**Type**: Boolean  
**Default**: `true`  
**Example**: `true`

Enable knowledge graph visualization.

### `FEATURE_DIAGNOSTIC_ASSESSMENT`
**Required**: No  
**Type**: Boolean  
**Default**: `true`  
**Example**: `true`

Enable diagnostic assessment feature.

---

## Frontend-Specific Variables

### `NEXT_PUBLIC_API_URL`
**Required**: Yes  
**Type**: String (URL)  
**Default**: `http://localhost:8000`  
**Example**: `https://api.rootlearn.com`

Backend API base URL. Accessible in browser (NEXT_PUBLIC_ prefix).

**Important**: Must be accessible from user's browser.

### `NEXT_PUBLIC_ANALYTICS_ID`
**Required**: No  
**Type**: String  
**Default**: None  
**Example**: `G-XXXXXXXXXX`

Google Analytics or similar tracking ID.

---

## Redis Configuration (Optional)

### `REDIS_HOST`
**Required**: If using Redis  
**Type**: String  
**Default**: `redis`  
**Example**: `redis`

Redis hostname.

### `REDIS_PORT`
**Required**: No  
**Type**: Integer  
**Default**: `6379`  
**Example**: `6379`

Redis port.

### `REDIS_PASSWORD`
**Required**: If Redis requires auth  
**Type**: String  
**Default**: None  
**Example**: `secure_redis_password`

Redis password.

### `REDIS_DB`
**Required**: No  
**Type**: Integer  
**Default**: `0`  
**Example**: `0`

Redis database number (0-15).

### `REDIS_URL`
**Required**: Alternative to individual Redis vars  
**Type**: String (Connection URL)  
**Default**: None  
**Example**: `redis://:password@redis:6379/0`

Complete Redis connection URL.

---

## Backup Configuration (Optional)

### `BACKUP_SCHEDULE`
**Required**: No  
**Type**: String (cron format)  
**Default**: `0 2 * * *` (2 AM daily)  
**Example**: `0 2 * * *`

Cron schedule for automated backups.

### `BACKUP_RETENTION_DAYS`
**Required**: No  
**Type**: Integer  
**Default**: `30`  
**Example**: `30`

Number of days to retain backups.

### `BACKUP_S3_BUCKET`
**Required**: If using S3 backups  
**Type**: String  
**Default**: None  
**Example**: `my-rootlearn-backups`

S3 bucket for backup storage.

### `BACKUP_S3_REGION`
**Required**: If using S3 backups  
**Type**: String  
**Default**: `us-east-1`  
**Example**: `us-east-1`

AWS region for S3 bucket.

---

## Email Configuration (Optional)

### `SMTP_HOST`
**Required**: If using email  
**Type**: String  
**Default**: None  
**Example**: `smtp.gmail.com`

SMTP server hostname.

### `SMTP_PORT`
**Required**: No  
**Type**: Integer  
**Default**: `587`  
**Example**: `587`

SMTP server port (587 for TLS, 465 for SSL).

### `SMTP_USER`
**Required**: If SMTP requires auth  
**Type**: String  
**Default**: None  
**Example**: `notifications@rootlearn.com`

SMTP username.

### `SMTP_PASSWORD`
**Required**: If SMTP requires auth  
**Type**: String  
**Default**: None  
**Example**: `smtp_password`

SMTP password or app-specific password.

### `SMTP_FROM`
**Required**: If using email  
**Type**: String (email address)  
**Default**: None  
**Example**: `noreply@rootlearn.com`

From address for outgoing emails.

---

## Environment-Specific Recommendations

### Development
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=http://localhost:3000
SESSION_COOKIE_SECURE=false
RATE_LIMIT_ENABLED=false
SENTRY_TRACES_SAMPLE_RATE=1.0
```

### Staging
```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://staging.rootlearn.com
SESSION_COOKIE_SECURE=true
RATE_LIMIT_ENABLED=true
SENTRY_TRACES_SAMPLE_RATE=0.5
```

### Production
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://rootlearn.com,https://www.rootlearn.com
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=strict
RATE_LIMIT_ENABLED=true
CSRF_ENABLED=true
SENTRY_TRACES_SAMPLE_RATE=0.1
```

---

## Security Checklist

Before deploying to production, verify:

- [ ] All `*_PASSWORD` and `*_API_KEY` variables are secure and unique
- [ ] `SECRET_KEY` is generated with cryptographic randomness
- [ ] `ALLOWED_ORIGINS` contains only your actual domains (no wildcards)
- [ ] `SESSION_COOKIE_SECURE=true`
- [ ] `SESSION_COOKIE_HTTPONLY=true`
- [ ] `SESSION_COOKIE_SAMESITE=strict`
- [ ] `CSRF_ENABLED=true`
- [ ] `RATE_LIMIT_ENABLED=true`
- [ ] `ENVIRONMENT=production`
- [ ] No sensitive values committed to version control
