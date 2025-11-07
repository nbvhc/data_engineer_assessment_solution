# Data Engineering Assessment - Solution

## Overview

This project implements a complete ETL pipeline to normalize property data from a JSON file into a relational MySQL database. The solution follows dimensional modeling principles with star schema design, separating facts and dimensions for efficient querying and data integrity.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Project Structure](#project-structure)
4. [Setup Instructions](#setup-instructions)
5. [Running the ETL Pipeline](#running-the-etl-pipeline)
6. [Validation and Testing](#validation-and-testing)
7. [Database Schema Design](#database-schema-design)
8. [ETL Logic](#etl-logic)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
docker-compose -f docker-compose.initial.yml up --build -d
.\setup_env.ps1
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd scripts && python etl.py
python validate.py
```

---

## Prerequisites

- **Docker Desktop** - For MySQL database container
- **Python 3.8+** - For ETL scripts
- **Git** - Optional, for cloning repository

### System Requirements

- Windows 10/11, macOS, or Linux
- 4GB RAM minimum
- 2GB free disk space

---

## Project Structure

```
data_engineer_assessment/
├── data/
│   ├── fake_property_data_new.json
│   └── Field Config.xlsx
├── scripts/
│   ├── etl.py
│   ├── utils.py
│   ├── validate.py
│   └── etl_config.yaml
├── sql/
│   ├── 01_schema.sql
│   ├── 02_indexes.sql
│   └── 99_checks.sql
├── docs/
│   └── README.md
├── docker-compose.initial.yml
├── Dockerfile.initial_db
└── requirements.txt
```

---

## Setup Instructions

### Step 1: Start MySQL Database

```bash
docker-compose -f docker-compose.initial.yml up --build -d
```

Verify the container is running:
```bash
docker ps
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root with database connection details. The credentials must match those defined in `docker-compose.initial.yml`.

**Template:**
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=<database_name>
MYSQL_USER=<database_user>
MYSQL_PASSWORD=<database_password>
```

Or use the provided setup scripts:
- Windows: `.\setup_env.ps1`
- macOS/Linux: `./setup_env.sh`

### Step 3: Install Python Dependencies

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running the ETL Pipeline

Navigate to the scripts directory and run the ETL:

```bash
cd scripts
python etl.py
```

The ETL process will display progress updates and complete with a success message upon completion.

---

## Validation and Testing

### Method 1: Validation Script

```bash
cd scripts
python validate.py
```

### Method 2: SQL Queries

Connect to the database using credentials from your `.env` file:
```bash
docker exec -it mysql_ctn mysql -u <user> -p<password> <database>
```

Run validation queries:
```sql
SELECT COUNT(*) AS raw_rows FROM stg_properties_raw;
SELECT COUNT(*) AS properties FROM dim_property;
SELECT COUNT(*) AS facts FROM fact_property_snapshot;
SELECT COUNT(*) AS bad_addr FROM fact_property_snapshot WHERE address_sk IS NULL;
```

### Method 3: Validation SQL File

```bash
cat sql/99_checks.sql | docker exec -i mysql_ctn mysql -u <user> -p<password> <database>
```

---

## Database Schema Design

The schema follows dimensional modeling principles with a star schema design. Dimension tables store descriptive attributes, while the fact table links dimensions together for point-in-time snapshots. A staging table preserves raw data for audit and reprocessing.

### Schema Details

#### Staging Table
- **`stg_properties_raw`**: Raw JSON data for audit trail

#### Dimension Tables

**`dim_property`**
- Property characteristics (year built, type, square feet, bedrooms, bathrooms)
- Business key: `property_bk` (hash of address components)
- Surrogate key: `property_sk`

**`dim_address`**
- Location information (street, city, state, zip, coordinates)
- Unique key: Combination of address_line1, city, state, postal_code

**`dim_hoa`**
- HOA information (name, monthly fee, contact details, rules)
- Unique key: Combination of hoa_name and hoa_monthly_fee

**`dim_valuation`**
- Property valuations from various sources
- Aggregates multiple valuation sources with priority logic
- Unique key: Combination of provider, as_of_date, and estimate values

**`dim_rehab`**
- Rehabilitation cost estimates and component breakdowns
- Unique key: Combination of as_of_date and estimate values

**`dim_tax`**
- Tax information (year, assessed value, tax amount)
- Unique key: Combination of tax_year, assessed_value, tax_amount

#### Fact Table

**`fact_property_snapshot`**
- Links all dimensions together
- Represents a point-in-time snapshot of a property
- Foreign keys to all dimension tables
- Tracks `effective_date` for temporal analysis

### Design Decisions

- Normalization: Separated concerns into dimension tables to avoid data duplication
- Surrogate Keys: Auto-increment keys for improved join performance
- Business Keys: Hash-based keys for deduplication
- Staging Layer: Maintains raw data for reprocessing and audit
- Aggregation: Valuation prioritizes Redfin_Value > Zestimate > ARV > List_Price; HOA takes maximum fee; Rehab aggregates component scores

---

## ETL Logic

### Data Extraction

The pipeline reads JSON files (supports both JSON array and JSONL formats), validates file existence and structure, and loads raw data into a staging table for audit purposes.

### Data Transformation

Each dimension undergoes specific transformation logic:

- **Property**: Business key generated from address hash; numeric fields parsed with unit handling
- **Address**: Components normalized; coordinates extracted; default country applied
- **HOA**: Arrays aggregated to maximum monthly fee; existence flag set
- **Valuation**: Multiple sources prioritized (Redfin_Value > Zestimate > ARV > List_Price); FMR bands aggregated
- **Rehab**: Estimates aggregated with preference for Rehab_Calculation; component scores calculated from flags
- **Tax**: Amount extracted from single field; missing fields set to NULL

### Data Loading

The pipeline uses `INSERT ... ON DUPLICATE KEY UPDATE` for idempotent loading. Surrogate keys are retrieved after insert/update using unique business keys. The entire ETL process is wrapped in a single transaction with automatic rollback on error.

### Key Features

- Idempotent loading for safe re-execution
- Transaction-based error handling with automatic rollback
- Progress tracking and data validation
- Complete audit trail via staging table
- Configurable field mappings via YAML

### Known Limitations

- Valuation dates, tax year, and assessed value not available in source data
- Lot size and address line 2 not populated
- HOA contact information not in source data
- Business key assumes unique addresses within dataset

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker container won't start | Check if port 3306 is in use: `netstat -an \| findstr 3306` (Windows) or `lsof -i :3306` (macOS/Linux) |
| Python module not found | Activate virtual environment and run `pip install -r requirements.txt` |
| Database connection refused | Verify Docker container is running: `docker ps` |
| Access denied for user | Verify `.env` file credentials match `docker-compose.initial.yml` |
| File not found error | Ensure data file exists in `data/` directory |
| Foreign key constraint errors | Verify schema creation completed successfully |
| Zero rows in dims/fact | Confirm input data file exists and matches expected format |

---

## File Descriptions

**`scripts/etl.py`** - Main ETL orchestration script  
**`scripts/utils.py`** - Database connection and data parsing utilities  
**`scripts/validate.py`** - Data quality validation script  
**`scripts/etl_config.yaml`** - Field mapping configuration  

**`sql/01_schema.sql`** - Database schema definition  
**`sql/02_indexes.sql`** - Performance indexes  
**`sql/99_checks.sql`** - Validation queries

---

## Reproducibility

All steps are fully reproducible:
- Docker container ensures consistent database environment
- `requirements.txt` pins all Python packages
- YAML and `.env` files for configuration
- All SQL and Python code included
- Source JSON file included in repository

---

## License

This solution is provided for assessment purposes only.
