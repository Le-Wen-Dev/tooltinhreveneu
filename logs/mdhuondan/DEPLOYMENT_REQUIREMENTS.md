# Deployment Requirements & Checklist

## Database Requirements

### Type: PostgreSQL (Recommended) or MySQL 8+

### PostgreSQL Setup Details

**Minimum Requirements**:
- PostgreSQL 12+ 
- 10GB storage (grows with daily data)
- 2GB RAM minimum
- CPU: 2 cores minimum

**Connection String Format**:
```
postgresql://username:password@host:port/database_name
```

**Example**:
```
postgresql://revenue_user:SecurePass123@db.example.com:5432/revenue_db
```

### Database Schema

The system requires these tables:
1. `raw_revenue_data` - Stores scraped revenue data
2. `formulas` - Stores formula definitions
3. `computed_metrics` - Stores computed row-level metrics
4. `aggregated_metrics` - Stores aggregated metrics
5. `fetch_logs` - Tracks data fetching operations
6. `admin_users` - Admin panel users (optional)

**Schema File**: `database_schema.sql`

**To Initialize**:
```bash
psql -U username -d database_name -f database_schema.sql
```

### Database Credentials

You need to provide:
- **Host**: Database server address
- **Port**: Usually 5432 for PostgreSQL
- **Database Name**: e.g., `revenue_db`
- **Username**: Database user
- **Password**: Database password

**Store in**: `backend/.env` as `DATABASE_URL`

---

## Application Hosting

### Server Requirements

**Minimum**:
- 2 CPU cores
- 4GB RAM
- 20GB disk space
- Python 3.8+

**Recommended**:
- 4 CPU cores
- 8GB RAM
- 50GB+ disk space
- Python 3.10+

### Environment Variables

Create `backend/.env` file with:

```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Scraper Credentials
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Optional: Admin Panel Security
ADMIN_SECRET_KEY=generate-a-random-secret-key-here
```

### Python Dependencies

Install from: `backend/requirements.txt`

```bash
pip install -r backend/requirements.txt
```

**Key Dependencies**:
- FastAPI (web framework)
- SQLAlchemy (database ORM)
- psycopg2-binary (PostgreSQL driver)
- uvicorn (ASGI server)
- requests, beautifulsoup4 (scraping)

---

## Hosting Options

### Option 1: Cloud Platforms (Easiest)

**Heroku**:
- Free tier available
- Easy PostgreSQL addon
- Automatic deployments
- **Cost**: $7-25/month

**DigitalOcean App Platform**:
- Managed PostgreSQL available
- Simple deployment
- **Cost**: $12-25/month

**Railway**:
- PostgreSQL included
- Simple setup
- **Cost**: $5-20/month

### Option 2: VPS (More Control)

**DigitalOcean Droplet**:
- Ubuntu 22.04 LTS
- 4GB RAM / 2 vCPU
- **Cost**: $24/month

**AWS EC2**:
- t3.medium instance
- **Cost**: ~$30/month

**Google Cloud Compute**:
- e2-medium instance
- **Cost**: ~$25/month

### Option 3: Container (Docker)

**Requirements**:
- Docker & Docker Compose
- PostgreSQL container or external DB

**Dockerfile provided**: Can be created if needed

---

## Scheduled Tasks Setup

### Option 1: Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 2 AM)
0 2 * * * cd /path/to/project && /path/to/venv/bin/python backend/data_fetcher.py
```

### Option 2: Systemd Service (Linux)

Create `/etc/systemd/system/revenue-fetcher.service`:

```ini
[Unit]
Description=Revenue Data Fetcher Service
After=network.target postgresql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/toolgetdata
Environment="PATH=/path/to/venv/bin"
EnvironmentFile=/path/to/toolgetdata/backend/.env
ExecStart=/path/to/venv/bin/python backend/data_fetcher.py --schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable revenue-fetcher
sudo systemctl start revenue-fetcher
```

### Option 3: Cloud Schedulers

**AWS EventBridge**:
- Create rule: Schedule expression `cron(0 2 * * ? *)`
- Target: Lambda function or ECS task

**Google Cloud Scheduler**:
- Create job with HTTP target
- Schedule: `0 2 * * *`

**Azure Logic Apps**:
- Recurrence trigger
- HTTP action to your API

---

## Security Checklist

### Database Security
- [ ] Use strong database passwords (16+ characters)
- [ ] Restrict database access to application server only
- [ ] Enable SSL/TLS for database connections
- [ ] Regular backups (daily recommended)
- [ ] Use connection pooling

### Application Security
- [ ] Never commit `.env` file to git
- [ ] Use environment variables for all secrets
- [ ] Enable HTTPS (SSL certificate)
- [ ] Add API authentication (JWT tokens)
- [ ] Add admin panel login
- [ ] Rate limiting on API endpoints
- [ ] Input validation on all endpoints

### Network Security
- [ ] Firewall rules (only allow necessary ports)
- [ ] Use VPN or private networks for database
- [ ] Regular security updates
- [ ] Monitor access logs

---

## Monitoring & Maintenance

### Health Checks

**API Health Endpoint**: `GET /health`

**Database Health**:
```sql
SELECT COUNT(*) FROM raw_revenue_data;
SELECT * FROM fetch_logs ORDER BY started_at DESC LIMIT 5;
```

### Logs

**Application Logs**: Check uvicorn output
**Fetch Logs**: Query `fetch_logs` table
**Error Logs**: Monitor application stderr

### Backup Strategy

**Database Backups**:
```bash
# Daily backup
pg_dump -U username revenue_db > backup_$(date +%Y%m%d).sql

# Automated backup script (run via cron)
0 3 * * * pg_dump -U username revenue_db | gzip > /backups/revenue_db_$(date +\%Y\%m\%d).sql.gz
```

**Retention**: Keep 30 days of backups minimum

### Performance Monitoring

**Database Size**:
```sql
SELECT pg_size_pretty(pg_database_size('revenue_db'));
```

**Table Sizes**:
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Quick Start Checklist

1. **Database Setup**
   - [ ] Install PostgreSQL
   - [ ] Create database and user
   - [ ] Run `database_schema.sql`
   - [ ] Test connection

2. **Application Setup**
   - [ ] Install Python 3.8+
   - [ ] Create virtual environment
   - [ ] Install dependencies
   - [ ] Create `.env` file
   - [ ] Test API server starts

3. **Initial Test**
   - [ ] Run test crawl: `python test_crawl.py`
   - [ ] Test data fetch: `python backend/data_fetcher.py --first-page-only`
   - [ ] Verify data in database
   - [ ] Test API endpoints

4. **Production Setup**
   - [ ] Configure production database
   - [ ] Set up scheduled fetching
   - [ ] Configure reverse proxy (nginx)
   - [ ] Set up SSL certificate
   - [ ] Configure monitoring
   - [ ] Set up backups

---

## Support & Troubleshooting

### Common Issues

**Database Connection Failed**:
- Check `DATABASE_URL` format
- Verify database is running
- Check firewall rules
- Verify credentials

**Scraper Login Failed**:
- Verify credentials in `.env`
- Check if website structure changed
- Review scraper logs

**Formula Computation Errors**:
- Check formula syntax
- Verify data exists
- Review formula_engine.py logs

### Getting Help

1. Check `SETUP_GUIDE.md` for detailed instructions
2. Review API docs at `/docs` endpoint
3. Check `fetch_logs` table for errors
4. Review application logs

---

## Cost Estimation

### Minimum Setup (Development)
- Database: Free (local PostgreSQL)
- Hosting: Free (local development)
- **Total**: $0/month

### Small Production
- Database: $5-10/month (managed DB)
- Hosting: $5-10/month (small VPS)
- **Total**: $10-20/month

### Medium Production
- Database: $15-25/month
- Hosting: $25-50/month
- **Total**: $40-75/month

### Large Production
- Database: $50-100/month
- Hosting: $100-200/month
- Monitoring: $20-50/month
- **Total**: $170-350/month
