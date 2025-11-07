# Data Engineering Assessment

Welcome!  
This exercise evaluates your core **data-engineering** skills:

| Competency | Focus                                                         |
| ---------- | ------------------------------------------------------------- |
| SQL        | relational modelling, normalisation, DDL/DML scripting        |
| Python ETL | data ingestion, cleaning, transformation, & loading (ELT/ETL) |

---

## 0 Prerequisites & Setup

> **Allowed technologies**

- **Python ≥ 3.8** – all ETL / data-processing code
- **MySQL 8** – the target relational database
- **Lightweight helper libraries only** (e.g. `pandas`, `mysql-connector-python`).  
  List every dependency in **`requirements.txt`** and justify anything unusual.
- **No ORMs / auto-migration tools** – write plain SQL by hand.

---

## 1 Clone the skeleton repo

```
git clone https://github.com/100x-Home-LLC/data_engineer_assessment.git
```

✏️ Note: Rename the repo after cloning and add your full name.

**Start the MySQL database in Docker:**

```
docker-compose -f docker-compose.initial.yml up --build -d
```

- Database is available on `localhost:3306`
- Credentials/configuration are in the Docker Compose file
- **Do not change** database name or credentials

For MySQL Docker image reference:
[MySQL Docker Hub](https://hub.docker.com/_/mysql)

---

### Problem

- You are provided with a raw JSON file containing property records is located in data/
- Each row relates to a property. Each row mixes many unrelated attributes (property details, HOA data, rehab estimates, valuations, etc.).
- There are multiple Columns related to this property.
- The database is not normalized and lacks relational structure.
- Use the supplied Field Config.xlsx (in data/) to understand business semantics.

### Task

- **Normalize the data:**

  - Develop a Python ETL script to read, clean, transform, and load data into your normalized MySQL tables.
  - Refer the field config document for the relation of business logic
  - Use primary keys and foreign keys to properly capture relationships

- **Deliverable:**
  - Write necessary python and sql scripts
  - Place your scripts in `sql/` and `scripts/`
  - The scripts should take the initial json to your final, normalized schema when executed
  - Clearly document how to run your script, dependencies, and how it integrates with your database.

**Tech Stack:**

- Python (include a `requirements.txt`)
  Use **MySQL** and SQL for all database work
- You may use any CLI or GUI for development, but the final changes must be submitted as python/ SQL scripts
- **Do not** use ORM migrations—write all SQL by hand

---

## Submission Guidelines

- Edit the section to the bottom of this README with your solutions and instructions for each section at the bottom.
- Place all scripts/code in their respective folders (`sql/`, `scripts/`, etc.)
- Ensure all steps are fully **reproducible** using your documentation
- Create a new private repo and invite the reviewer https://github.com/mantreshjain

---

**Good luck! We look forward to your submission.**

## Solutions and Instructions (Filed by Candidate)

**Please see the main README.md file in the root directory for complete solution documentation, including:**

- Detailed database schema design and normalization approach
- Step-by-step setup instructions
- ETL pipeline execution guide
- Validation and testing procedures
- Troubleshooting guide

**Quick Start:**

1. **Start MySQL Database:**
   ```bash
   docker-compose -f docker-compose.initial.yml up --build -d
   ```

2. **Setup Python Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_DB=home_db
   MYSQL_USER=db_user
   MYSQL_PASSWORD=6equj5_db_user
   ```

4. **Run ETL Pipeline:**
   ```bash
   cd scripts
   python etl.py
   ```

**Database Design Summary:**

The solution implements a **star schema** (dimensional model) with:

- **Dimension Tables**: `dim_property`, `dim_address`, `dim_hoa`, `dim_valuation`, `dim_rehab`, `dim_tax`
- **Fact Table**: `fact_property_snapshot` (links all dimensions)
- **Staging Table**: `stg_properties_raw` (stores raw JSON for audit)

**ETL Logic Summary:**

1. **Extract**: Reads JSON file and stages raw data
2. **Transform**: 
   - Normalizes property attributes
   - Aggregates HOA, Valuation, and Rehab arrays
   - Creates business keys for deduplication
   - Parses and cleans numeric fields
3. **Load**: 
   - Upserts dimension tables (with deduplication)
   - Creates fact table records linking dimensions
   - Uses transactions for data integrity

**Key Features:**
- Idempotent loading (can run multiple times safely)
- Comprehensive error handling with rollback
- Progress tracking during processing
- Data quality validation
- Full audit trail via staging table

For complete details, see the main **README.md** file.
