# Monitoring Configuration Guide

## Overview

NEXORUX ERP has built-in health check endpoints and scripts for external monitoring. This guide explains how to set up external monitoring services.

## Health Check Endpoints

### Primary Health Check
- **Endpoint:** `/health`
- **Method:** GET
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### API Health Check
- **Endpoint:** `/api/v1/health/`
- **Method:** GET
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "nexorux-erp-api",
  "version": "0.1.0"
}
```

## Local Health Check Scripts

### Usage

```bash
# Check local health endpoint
./scripts/check_health.sh

# Check public URL
HEALTH_URL=https://erp.example.com/health ./scripts/check_health.sh

# PowerShell (Windows)
.\scripts\check_health.ps1
```

### Script Behavior

The scripts:
1. Check primary health endpoint (5s timeout, 10s max)
2. If primary fails, check fallback endpoint
3. Return HTTP 200 on success, non-zero on failure
4. Output response body on success

## External Monitoring Services

### Option 1: UptimeRobot (Recommended)

**Setup Steps:**

1. Go to https://uptimerobot.com/
2. Create account (free tier available)
3. Add New Monitor:
   - **Monitor Type:** HTTPS
   - **URL:** `https://your-domain.com/health`
   - **Monitoring Interval:** 5 minutes (free) or 1 minute (paid)
   - **Alert Contacts:** Add email/SMS
   - **Monitor Type:** Keyword Existence
   - **Keyword:** `healthy`

**Configuration:**
```
URL: https://your-domain.com/health
Check Interval: 5 minutes
Alert Timeout: 30 seconds
Keyword: healthy
```

### Option 2: Pingdom

**Setup Steps:**

1. Go to https://www.pingdom.com/
2. Create account
3. Add Uptime Check:
   - **Name:** NEXORUX ERP Health
   - **URL:** `https://your-domain.com/health`
   - **Check Interval:** 5 minutes
   - **Alerts:** Configure email/SMS

### Option 3: StatusCake

**Setup Steps:**

1. Go to https://www.statuscake.com/
2. Create account
3. Add Uptime Test:
   - **Name:** NEXORUX ERP
   - **URL:** `https://your-domain.com/health`
   - **Check Rate:** 300 seconds (5 minutes)
   - **Test Type:** HTTP

### Option 4: Better Uptime (Free & Open Source)

**Setup Steps:**

1. Go to https://betteruptime.com/
2. Create account
3. Add Monitor:
   - **Name:** NEXORUX ERP
   - **URL:** `https://your-domain.com/health`
   - **Check Interval:** 60 seconds
   - **Regions:** Select multiple regions

### Option 5: Uptime Kuma (Self-Hosted)

**Setup Steps:**

1. Deploy Uptime Kuma using Docker:
```bash
docker run -d --restart=always -p 3001:3001 -v uptime-kuma:/app/data --name uptime-kuma louislam/uptime-kuma:1
```

2. Access UI at `http://your-server:3001`
3. Create Monitor:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** NEXORUX ERP Health
   - **URL:** `https://your-domain.com/health`
   - **Heartbeat Interval:** 60 seconds
   - **Retry Interval:** 20 seconds

## Advanced Monitoring Configuration

### Multiple Endpoints

Monitor both endpoints for redundancy:

1. **Primary:** `https://your-domain.com/health`
2. **Secondary:** `https://your-domain.com/api/v1/health/`

### Database Health

Consider adding database health checks:

```bash
# Check PostgreSQL connection
docker exec nexorux-postgres pg_isready -U nexorux

# Check Redis connection
docker exec nexorux-redis redis-cli ping
```

### Application Metrics

For advanced metrics, consider:
- **Prometheus** + **Grafana** (self-hosted)
- **Datadog** (commercial)
- **New Relic** (commercial)

## Alert Configuration

### Recommended Alerts

1. **Critical (SMS + Email):**
   - Health check fails for > 2 consecutive checks
   - Error rate > 5%
   - Response time > 5 seconds

2. **Warning (Email only):**
   - Health check fails for 1 check
   - Response time > 2 seconds
   - Database connection high latency

3. **Info (Email daily):**
   - Daily uptime report
   - Weekly performance summary

### Maintenance Windows

Configure monitoring to pause during scheduled maintenance:

- **UptimeRobot:** Use "Maintenance Windows" feature
- **Pingdom:** Configure "Pause Monitoring" during maintenance
- **StatusCake:** Use "Maintenance Mode"

## Integration with Incident Management

### PagerDuty Integration

1. Create PagerDuty service
2. Add UptimeRobot/Pingdom as integration
3. Configure escalation policies
4. Set up on-call schedules

### Slack Integration

Most monitoring services support Slack webhooks:

```bash
# Example Slack webhook for UptimeRobot
Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
Channel: #alerts
Username: NEXORUX Monitor
```

## Testing Monitoring Configuration

### Verify Health Endpoint

```bash
# Test local
curl http://localhost:8000/health

# Test production
curl https://your-domain.com/health

# Test with script
./scripts/check_health.sh
```

### Simulate Failure

```bash
# Stop backend service
docker-compose stop backend

# Verify monitoring detects failure
# Check monitoring service dashboard

# Restart service
docker-compose start backend
```

## Maintenance

### Update Monitoring URLs

When changing domains:

1. Update monitoring service URLs
2. Update HEALTH_URL in scripts
3. Test new configuration
4. Verify alerts work correctly

### Review Monitoring Configuration

**Monthly Review:**
- Check alert thresholds
- Verify contact information
- Review uptime reports
- Update maintenance windows

**Quarterly Review:**
- Evaluate monitoring service performance
- Consider alternative services if needed
- Review costs and optimize

## Troubleshooting

### Health Check Returns 500

**Possible Causes:**
- Database connection failed
- Redis connection failed
- Application error
- Configuration issue

**Debug Steps:**
```bash
# Check backend logs
docker-compose logs backend

# Check database connection
docker-compose exec postgres pg_isready -U nexorux

# Check Redis connection
docker-compose exec redis redis-cli ping

# Check environment variables
docker-compose exec backend env | grep DATABASE_URL
```

### Monitoring False Positives

**Solutions:**
- Increase timeout threshold
- Add retry logic in monitoring service
- Configure maintenance windows for planned downtime
- Use keyword matching to validate response

### Alerts Not Received

**Check:**
- Alert contact configuration
- Email spam filters
- SMS provider status
- Monitoring service outage

## Security Considerations

### Health Endpoint Security

The `/health` endpoint is public by design for monitoring. To secure it:

```python
# Option 1: Add rate limiting
from slowapi import Limiter, _rate_limit_exceeded
limiter = Limiter(key_func=get_remote_address)

@app.get("/health")
@limiter.limit("10/minute")
async def health_check():
    # ... existing code
```

```python
# Option 2: Add basic auth (not recommended for external monitoring)
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.get("/health")
async def health_check(credentials: HTTPBasicCredentials = Depends(security)):
    # ... existing code
```

### Monitoring Service Credentials

- Use strong passwords for monitoring service accounts
- Enable 2FA where available
- Rotate credentials regularly
- Use API keys with minimal permissions

## Compliance

### Data Privacy

Health check endpoints:
- Do not expose sensitive data
- Return minimal information
- Comply with data protection regulations

### Audit Trail

Log health check access:

```python
import structlog

logger = structlog.get_logger(__name__)

@app.get("/health")
async def health_check(request: Request):
    logger.info(
        "health_check_called",
        client_ip=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    # ... existing code
```

## Costs

### Free Tier Comparison

| Service | Free Tier | Alerts | Check Interval | Notes |
|---------|-----------|--------|----------------|-------|
| UptimeRobot | 50 monitors | Email | 5 min | SMS paid |
| Pingdom | 10 monitors | Email | 1 min | SMS paid |
| StatusCake | 10 monitors | Email | 5 min | SMS paid |
| Better Uptime | 10 monitors | Email | 1 min | SMS paid |
| Uptime Kuma | Unlimited | Self-hosted | Custom | Self-hosted |

### Recommended Setup

**Free tier:**
- **Primary:** UptimeRobot (50 monitors, email alerts)
- **Backup:** Better Uptime (1 min checks, email alerts)

**Paid tier (for production):**
- **Primary:** Pingdom Pro (1 min checks, SMS alerts)
- **Backup:** UptimeRobot Pro (1 min checks, SMS alerts)

## Next Steps

1. Choose monitoring service based on requirements
2. Configure health check monitors
3. Set up alert contacts
4. Test alert delivery
5. Document monitoring configuration
6. Schedule regular reviews

## Related Documentation

- [PRODUCTION.md](./PRODUCTION.md) - Production deployment guide
- [EMAIL.md](./EMAIL.md) - Email configuration
- [check_health.sh](../scripts/check_health.sh) - Health check script
- [check_health.ps1](../scripts/check_health.ps1) - Windows health check script

---

**Last Updated:** 2026-08-13
