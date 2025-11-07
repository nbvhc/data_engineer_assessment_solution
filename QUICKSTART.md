# Quick Start Guide

This is a condensed guide to get you up and running quickly. For detailed documentation, see [README.md](README.md).

## Prerequisites Checklist

- [ ] Docker Desktop installed and running
- [ ] Python 3.8+ installed
- [ ] Git installed (optional)

## 5-Minute Setup

### Step 1: Start MySQL Database

```bash
docker-compose -f docker-compose.initial.yml up --build -d
```

Wait 10-20 seconds for MySQL to initialize. Verify it's running:
```bash
docker ps
```

### Step 2: Create Environment File

**Windows (PowerShell):**
```powershell
.\setup_env.ps1
```

**macOS/Linux:**
```bash
chmod +x setup_env.sh
./setup_env.sh
```

**Or manually create `.env` file:**
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=home_db
MYSQL_USER=db_user
MYSQL_PASSWORD=6equj5_db_user
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 4: Run ETL Pipeline

```bash
cd scripts
python etl.py
```

You should see progress output and a success message.

### Step 5: Validate Results

```bash
# Still in scripts directory
python validate.py
```

Or connect to the database and run queries:
```bash
docker exec -it mysql_ctn mysql -u db_user -p6equj5_db_user home_db
```

## Common Issues

**Problem:** `ModuleNotFoundError: No module named 'utils'`  
**Solution:** Make sure you're running the script from the `scripts/` directory, or check that `utils.py` is in the same directory.

**Problem:** `Can't connect to MySQL server`  
**Solution:** 
1. Check Docker is running: `docker ps`
2. Wait a bit longer for MySQL to fully start
3. Verify `.env` file has correct credentials

**Problem:** `Access denied for user`  
**Solution:** Check that your `.env` file matches the credentials in `docker-compose.initial.yml`

## What Gets Created

- **Staging Table**: `stg_properties_raw` - Raw JSON data
- **Dimension Tables**: 
  - `dim_property` - Property attributes
  - `dim_address` - Location data
  - `dim_hoa` - HOA information
  - `dim_valuation` - Property valuations
  - `dim_rehab` - Rehabilitation estimates
  - `dim_tax` - Tax information
- **Fact Table**: `fact_property_snapshot` - Links all dimensions

## Next Steps

- Review the [README.md](README.md) for detailed documentation
- Explore the database using SQL queries
- Check `sql/99_checks.sql` for validation queries
- Review the ETL code in `scripts/etl.py` to understand the transformation logic

## Need Help?

See the [Troubleshooting Guide](README.md#troubleshooting-guide) in the main README.

