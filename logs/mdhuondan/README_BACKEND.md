# Revenue Share Data System - Complete Backend

## 🎯 System Overview

A complete backend system for fetching, storing, and computing revenue share data with:
- **Automated Data Fetching**: Daily scraping of revenue data
- **Database Storage**: PostgreSQL for raw and computed data
- **Formula Engine**: Custom formula calculation system
- **Admin Panel**: Web interface for formula management
- **REST API**: Real-time access to data and metrics

## 📁 Project Structure

```
toolgetdata/
├── scraper.py                 # Web scraper (original)
├── test_crawl.py              # Test script (first page only)
├── database_schema.sql        # Database schema
├── SETUP_GUIDE.md            # Detailed setup instructions
├── DEPLOYMENT_REQUIREMENTS.md # Deployment checklist
│
├── backend/
│   ├── app.py                 # FastAPI main application
│   ├── formula_engine.py     # Formula calculation engine
│   ├── data_fetcher.py       # Scheduled data fetching service
│   ├── admin_panel.py        # Admin panel routes
│   ├── requirements.txt      # Python dependencies
│   │
│   └── templates/            # HTML templates for admin panel
│       ├── admin_dashboard.html
│       ├── formulas_list.html
│       └── formula_form.html
```

## 🚀 Quick Start

### 1. Database Setup

**PostgreSQL** (recommended):
```bash
# Install PostgreSQL
brew install postgresql  # macOS
# or
sudo apt-get install postgresql  # Linux

# Create database
createdb revenue_db
psql revenue_db < database_schema.sql
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment

Create `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/revenue_db
SCRAPER_USERNAME=maxvaluemedia
SCRAPER_PASSWORD=gliacloud
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Run the System

**Start API Server**:
```bash
cd backend
uvicorn app:app --reload
```

**Test Data Fetch** (first page only):
```bash
python backend/data_fetcher.py --first-page-only
```

**Access Admin Panel**:
Open: `http://localhost:8000/admin`

## 📊 Key Features

### 1. Data Fetching

- **Automated**: Daily scheduled fetching at 2 AM
- **Manual**: Trigger via command line
- **First Page Only**: Quick test mode
- **Full Crawl**: All pages with pagination

**Usage**:
```bash
# Test (first page only)
python backend/data_fetcher.py --first-page-only

# Fetch specific date
python backend/data_fetcher.py --date 2026-01-26

# Scheduled service
python backend/data_fetcher.py --schedule
```

### 2. Formula Engine

**Default Formulas**:

1. **RPM Combined** (Mobile + Desktop):
   ```
   sum(net_revenue_usd) / sum(total_player_impr) * 1000
   ```

2. **RPM per 1000 Players**:
   ```
   (net_revenue_usd / total_player_impr) * 1000
   ```

3. **Total Net Revenue**:
   ```
   sum(net_revenue_usd)
   ```

**Custom Formulas**: Create via admin panel at `/admin/formulas`

### 3. API Endpoints

**Raw Data**:
- `GET /api/raw-data` - List raw data (with filters)
- `GET /api/raw-data/{id}` - Get specific record
- `POST /api/raw-data` - Create record
- `POST /api/raw-data/bulk` - Bulk create

**Formulas**:
- `GET /api/formulas` - List all formulas
- `GET /api/formulas/{id}` - Get formula
- `POST /api/formulas` - Create formula
- `PUT /api/formulas/{id}` - Update formula
- `DELETE /api/formulas/{id}` - Delete formula

**Computed Metrics**:
- `GET /api/computed-metrics` - Get computed metrics
- `GET /api/aggregated-metrics` - Get aggregated metrics
- `POST /api/compute/{formula_id}` - Trigger computation

**Documentation**:
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

### 4. Admin Panel

Access at: `http://localhost:8000/admin`

**Features**:
- View all formulas
- Create/edit/delete formulas
- Trigger formula computation
- View dashboard stats

## 🔧 Formula System

### Formula Types

- **rpm**: Revenue per mille calculations
- **revenue**: Revenue aggregations  
- **custom**: User-defined formulas
- **irpm**: If available in source data

### Available Fields

In formulas, you can use:
- `total_player_impr` - Total player impressions
- `total_ad_impr` - Total ad impressions
- `rpm` - RPM from source
- `gross_revenue_usd` - Gross revenue
- `net_revenue_usd` - Net revenue (primary focus)

### Formula Examples

**Row-level** (computed per row):
```
(net_revenue_usd / total_player_impr) * 1000
```

**Aggregated** (computed across rows):
```
sum(net_revenue_usd for all rows)
```

**Complex**:
```
(net_revenue_usd / total_player_impr) * 1000 * 1.2
```

## 📈 Data Flow

1. **Fetch**: Scraper fetches data from website
2. **Store**: Raw data saved to `raw_revenue_data` table
3. **Compute**: Formula engine processes formulas
4. **Store Results**: Computed metrics saved to `computed_metrics` or `aggregated_metrics`
5. **API**: Results exposed via REST API

## 🗄️ Database Schema

### Main Tables

1. **raw_revenue_data**: Scraped revenue data
   - Fields: channel, slot, time_unit, revenue metrics
   - Indexed by: fetch_date, channel

2. **formulas**: Formula definitions
   - Fields: name, formula_expression, formula_type
   - Supports: row-level and aggregated

3. **computed_metrics**: Row-level computed results
   - Links: raw_data_id, formula_id

4. **aggregated_metrics**: Aggregated results
   - Groups by: channel, time_unit, fetch_date

5. **fetch_logs**: Fetch operation tracking

See `database_schema.sql` for full schema.

## 🔐 Security Notes

**Current State**: Basic setup (no authentication)

**For Production**:
- Add JWT authentication to API
- Add login to admin panel
- Use HTTPS
- Restrict database access
- Use environment variables for secrets

## 📝 API Usage Examples

### Get Raw Data
```bash
curl "http://localhost:8000/api/raw-data?fetch_date=2026-01-26&limit=10"
```

### Get Formulas
```bash
curl "http://localhost:8000/api/formulas"
```

### Get Computed Metrics
```bash
curl "http://localhost:8000/api/computed-metrics?metric_name=rpm_per_1000_players"
```

### Create Formula
```bash
curl -X POST "http://localhost:8000/api/formulas" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom_rpm",
    "formula_expression": "(net_revenue_usd / total_player_impr) * 1000",
    "formula_type": "rpm",
    "description": "Custom RPM calculation"
  }'
```

### Trigger Computation
```bash
curl -X POST "http://localhost:8000/api/compute/1"
```

## 🐛 Troubleshooting

### Database Connection Issues
- Verify `DATABASE_URL` in `.env`
- Check PostgreSQL is running: `pg_isready`
- Verify database exists and user has permissions

### Scraper Login Fails
- Verify credentials in `.env`
- Check if website structure changed
- Review scraper logs

### Formulas Don't Compute
- Check formula syntax
- Verify data exists for date range
- Check formula is active
- Review formula_engine.py

### API Not Responding
- Check server is running: `curl http://localhost:8000/health`
- Check logs for errors
- Verify database connection

## 📚 Documentation

- **Setup Guide**: `SETUP_GUIDE.md` - Detailed setup instructions
- **Deployment**: `DEPLOYMENT_REQUIREMENTS.md` - Production deployment
- **API Docs**: `http://localhost:8000/docs` - Interactive API documentation

## 🎯 Next Steps

1. **Test System**:
   ```bash
   python test_crawl.py  # Test scraper
   python backend/data_fetcher.py --first-page-only  # Test fetch
   ```

2. **Verify Database**:
   ```sql
   SELECT COUNT(*) FROM raw_revenue_data;
   SELECT * FROM formulas;
   ```

3. **Test API**:
   - Visit `http://localhost:8000/docs`
   - Try endpoints interactively

4. **Create Custom Formulas**:
   - Visit `http://localhost:8000/admin`
   - Create formulas via web interface

5. **Set Up Scheduled Fetching**:
   - Configure cron or systemd service
   - See `SETUP_GUIDE.md` for details

## 💡 Key Design Decisions

1. **Net Revenue Focus**: System prioritizes Net Revenue over Gross
2. **Flexible Formulas**: Admin can define custom formulas
3. **Real-time API**: Data available immediately after fetch
4. **Scalable**: Database schema supports large datasets
5. **Extensible**: Easy to add new formula types

## 📞 Support

For issues:
1. Check `SETUP_GUIDE.md`
2. Review API docs at `/docs`
3. Check `fetch_logs` table
4. Review application logs

---

**System Status**: ✅ Ready for testing and deployment
