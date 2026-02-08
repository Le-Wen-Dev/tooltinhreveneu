# Setup Guide - Revenue Share Data System

## Overview

This system provides:
- **Data Fetching**: Automated daily scraping of revenue share data
- **Database Storage**: PostgreSQL database for raw and computed data
- **Formula Engine**: Custom formula calculation system
- **Admin Panel**: Web interface for managing formulas
- **REST API**: Endpoints for accessing data and computed metrics

## Prerequisites

### 1. Database Setup

**Database Type**: PostgreSQL (recommended) or MySQL

**PostgreSQL Installation**:
```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Create Database**:
```sql
CREATE DATABASE revenue_db;
CREATE USER revenue_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE revenue_db TO revenue_user;
```

**Initialize Schema**:
```bash
psql -U revenue_user -d revenue_db -f database_schema.sql
```

### 2. Python Environment

**Python Version**: 3.8+

**Create Virtual Environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install Dependencies**:
```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Scraper dependencies (if not already installed)
pip install -r requirements.txt
```

### 3. Environment Configuration

**Create `.env` file**:
```bash
cd backend
cp .env.example .env
```

**Edit `.env` with your settings**:
```env
DATABASE_URL=postgresql://revenue_user:your_password@localhost:5432/revenue_db
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud
API_HOST=0.0.0.0
API_PORT=8000
```

## System Architecture

### Database Schema

1. **raw_revenue_data**: Stores scraped data
   - Fields: channel, slot, time_unit, revenue metrics
   - Indexed by: fetch_date, channel, time_unit

2. **formulas**: Stores formula definitions
   - Fields: name, formula_expression, formula_type
   - Supports: row-level and aggregated formulas

3. **computed_metrics**: Stores computed results per row
   - Links: raw_data_id, formula_id

4. **aggregated_metrics**: Stores aggregated results
   - Groups by: channel, time_unit, fetch_date

5. **fetch_logs**: Tracks data fetching operations

### Formula Types

- **rpm**: Revenue per mille calculations
- **revenue**: Revenue aggregations
- **custom**: User-defined formulas
- **irpm**: If available in source data

### Default Formulas

1. **rpm_combined**: `sum(net_revenue_usd) / sum(total_player_impr) * 1000`
2. **rpm_per_1000_players**: `(net_revenue_usd / total_player_impr) * 1000`
3. **total_net_revenue**: `sum(net_revenue_usd)`
4. **total_gross_revenue**: `sum(gross_revenue_usd)`

## Running the System

### 1. Start API Server

```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at: `http://localhost:8000`

### 2. Access Admin Panel

Open browser: `http://localhost:8000/admin`

### 3. Test Data Fetch

**Manual fetch (first page only)**:
```bash
python backend/data_fetcher.py --first-page-only
```

**Manual fetch (all pages)**:
```bash
python backend/data_fetcher.py --date 2026-01-26
```

**Scheduled fetch (runs daily at 2 AM)**:
```bash
python backend/data_fetcher.py --schedule
```

### 4. Test API Endpoints

**Get raw data**:
```bash
curl http://localhost:8000/api/raw-data?fetch_date=2026-01-26
```

**Get formulas**:
```bash
curl http://localhost:8000/api/formulas
```

**Get computed metrics**:
```bash
curl http://localhost:8000/api/computed-metrics?metric_name=rpm_per_1000_players
```

**Get aggregated metrics**:
```bash
curl http://localhost:8000/api/aggregated-metrics?channel=maxvaluemedia_spotpariz
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Production Deployment

### 1. Database Hosting

**Options**:
- **AWS RDS**: Managed PostgreSQL
- **Google Cloud SQL**: Managed database
- **DigitalOcean**: Managed databases
- **Self-hosted**: Your own server

**Requirements**:
- PostgreSQL 12+ or MySQL 8+
- At least 10GB storage (grows with data)
- Regular backups recommended

### 2. Application Hosting

**Options**:
- **Heroku**: Easy deployment
- **AWS EC2/ECS**: Scalable
- **Google Cloud Run**: Serverless
- **DigitalOcean App Platform**: Simple deployment
- **Docker**: Containerized deployment

### 3. Environment Variables (Production)

```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SCRAPER_USERNAME=your_username
SCRAPER_PASSWORD=your_password
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Scheduled Tasks

**Option 1: Cron Job** (Linux/Mac):
```bash
# Add to crontab: crontab -e
0 2 * * * cd /path/to/project && /path/to/venv/bin/python backend/data_fetcher.py
```

**Option 2: Systemd Service** (Linux):
Create `/etc/systemd/system/revenue-fetcher.service`:
```ini
[Unit]
Description=Revenue Data Fetcher
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python backend/data_fetcher.py --schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

**Option 3: Cloud Scheduler** (AWS/GCP):
- AWS EventBridge
- Google Cloud Scheduler
- Azure Logic Apps

## Monitoring & Maintenance

### Logs

Check fetch logs:
```sql
SELECT * FROM fetch_logs ORDER BY started_at DESC LIMIT 10;
```

### Data Growth

Monitor database size:
```sql
SELECT pg_size_pretty(pg_database_size('revenue_db'));
```

### Performance

- Indexes are created on frequently queried fields
- Consider partitioning `raw_revenue_data` by `fetch_date` for large datasets
- Regular VACUUM and ANALYZE recommended

## Troubleshooting

### Login Issues

If scraper login fails:
1. Verify credentials in `.env`
2. Check if website structure changed
3. Review `scraper.py` login logic

### Database Connection

If database connection fails:
1. Verify `DATABASE_URL` in `.env`
2. Check database is running: `pg_isready`
3. Verify user permissions

### Formula Computation

If formulas don't compute:
1. Check formula syntax
2. Verify data exists for the date range
3. Check formula is active
4. Review `formula_engine.py` logs

## Security Considerations

1. **Database**: Use strong passwords, restrict network access
2. **API**: Add authentication for production (JWT tokens)
3. **Admin Panel**: Add login/authentication
4. **Credentials**: Never commit `.env` file
5. **HTTPS**: Use SSL/TLS in production

## Next Steps

1. Test the system with first page fetch
2. Verify database schema is created
3. Test API endpoints
4. Create custom formulas via admin panel
5. Set up scheduled fetching
6. Monitor data quality

## Support

For issues or questions:
1. Check logs in `fetch_logs` table
2. Review API documentation at `/docs`
3. Test individual components separately
