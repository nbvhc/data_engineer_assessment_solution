import os
import sys
import json
import yaml
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import get_conn, dict_get, coerce_date, hash_key, parse_number

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "fake_property_data_new.json")
CFG_PATH = os.path.join(BASE_DIR, "scripts", "etl_config.yaml")
SCHEMA_SQL = os.path.join(BASE_DIR, "sql", "01_schema.sql")

def load_config():
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def read_input_records(path):
    """Supports JSON array or JSONL (one object per line)."""
    with open(path, "r", encoding="utf-8") as f:
        first = f.read(1); f.seek(0)
        if first == "[":
            return json.load(f)
        else:
            return [json.loads(line) for line in f if line.strip()]

def best_valuation(val_list):
    """
    Select a single valuation per property.
    Priority: Redfin_Value > Zestimate > ARV > List_Price.
    """
    if not isinstance(val_list, list) or not val_list:
        return None
    priorities = ("Redfin_Value", "Zestimate", "ARV", "List_Price")

    def score(v):
        for key in priorities:
            if v.get(key) not in (None, "", " "):
                return (len(priorities) - priorities.index(key), parse_number(v.get(key)))
        return (0, 0.0)

    best = max(val_list, key=score)
    est = best.get("Redfin_Value") or best.get("Zestimate") or best.get("ARV") or best.get("List_Price")
    low = best.get("Low_FMR")
    high = best.get("High_FMR")
    return {
        "provider": "composite",
        "estimate": parse_number(est),
        "estimate_low": parse_number(low),
        "estimate_high": parse_number(high),
        "as_of_date": None,
    }

def aggregate_hoa(hoa_list):
    """Aggregate HOA data: use max fee and flag if any HOA exists."""
    if not isinstance(hoa_list, list) or not hoa_list:
        return None
    fees = [parse_number(h.get("HOA")) for h in hoa_list if h.get("HOA") not in (None, "", " ")]
    fee = max([f for f in fees if f is not None], default=None)
    any_yes = any(str(h.get("HOA_Flag","")).strip().lower() == "yes" for h in hoa_list)
    rules = {"any_hoa": any_yes} if any_yes is not None else None
    return {
        "hoa_name": None,
        "hoa_monthly_fee": fee,
        "hoa_phone": None,
        "hoa_email": None,
        "rules_json": json.dumps(rules) if rules else None,
    }

def aggregate_rehab(rehab_list):
    """
    Aggregate rehab estimates: prefer Rehab_Calculation, fallback to Underwriting_Rehab.
    Calculate component scores from Yes/No flags.
    """
    if not isinstance(rehab_list, list) or not rehab_list:
        return None
    totals = []
    exterior_score = 0.0
    interior_score = 0.0
    systems_score = 0.0
    for r in rehab_list:
        tot = r.get("Rehab_Calculation")
        if tot in (None, "", " "):
            tot = r.get("Underwriting_Rehab")
        totals.append(parse_number(tot))
        exterior_score += 1.0 if str(r.get("Roof_Flag", "")).strip().lower() == "yes" or str(r.get("Windows_Flag", "")).strip().lower() == "yes" else 0.0
        interior_score += 1.0 if str(r.get("Kitchen_Flag", "")).strip().lower() == "yes" or str(r.get("Bathroom_Flag", "")).strip().lower() == "yes" or str(r.get("Paint", "")).strip().lower() == "yes" else 0.0
        systems_score += 1.0 if str(r.get("HVAC_Flag", "")).strip().lower() == "yes" or str(r.get("Foundation_Flag", "")).strip().lower() == "yes" else 0.0

    total = max([t for t in totals if t is not None], default=None)
    return {
        "total_estimate": total,
        "exterior": exterior_score if exterior_score else None,
        "interior": interior_score if interior_score else None,
        "systems": systems_score if systems_score else None,
        "as_of_date": None
    }

def run_schema(conn):
    """Create database schema and indexes."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    schema_file = os.path.join(base_dir, "sql", "01_schema.sql")
    with open(schema_file, "r", encoding="utf-8") as f:
        sql = f.read()
    cur = conn.cursor()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                cur.execute(stmt)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"Warning: {str(e)}")
    cur.close()
    
    indexes_file = os.path.join(base_dir, "sql", "02_indexes.sql")
    if os.path.exists(indexes_file):
        with open(indexes_file, "r", encoding="utf-8") as f:
            sql = f.read()
        cur = conn.cursor()
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                try:
                    cur.execute(stmt)
                except Exception as e:
                    if "duplicate key" not in str(e).lower() and "already exists" not in str(e).lower():
                        print(f"Warning creating index: {str(e)}")
        cur.close()

def upsert(conn, table, data):
    """
    Insert or update record and return surrogate key.
    Uses ON DUPLICATE KEY UPDATE with lookup based on unique business keys.
    """
    cols = list(data.keys())
    placeholders = ",".join(["%s"] * len(cols))
    updates = ",".join([f"{c}=VALUES({c})" for c in cols])
    
    pk_col_name = None
    lookup_cols = None
    
    if table == "dim_property":
        pk_col_name = "property_sk"
        lookup_cols = {"property_bk": data.get("property_bk")}
    elif table == "dim_address":
        pk_col_name = "address_sk"
        lookup_cols = {
            "address_line1": data.get("address_line1"),
            "city": data.get("city"),
            "state": data.get("state"),
            "postal_code": data.get("postal_code")
        }
    elif table == "dim_hoa":
        pk_col_name = "hoa_sk"
        lookup_cols = {
            "hoa_name": data.get("hoa_name"),
            "hoa_monthly_fee": data.get("hoa_monthly_fee")
        }
    elif table == "dim_valuation":
        pk_col_name = "valuation_sk"
        lookup_cols = {
            "provider": data.get("provider"),
            "as_of_date": data.get("as_of_date"),
            "estimate": data.get("estimate"),
            "estimate_low": data.get("estimate_low"),
            "estimate_high": data.get("estimate_high")
        }
    elif table == "dim_rehab":
        pk_col_name = "rehab_sk"
        lookup_cols = {
            "as_of_date": data.get("as_of_date"),
            "total_estimate": data.get("total_estimate"),
            "exterior": data.get("exterior"),
            "interior": data.get("interior"),
            "systems": data.get("systems")
        }
    elif table == "dim_tax":
        pk_col_name = "tax_sk"
        lookup_cols = {
            "tax_year": data.get("tax_year"),
            "assessed_value": data.get("assessed_value"),
            "tax_amount": data.get("tax_amount")
        }
    
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
    cur = conn.cursor(buffered=True)
    cur.execute(sql, [data[c] for c in cols])
    try:
        cur.fetchall()
    except:
        pass
    cur.close()
    
    if pk_col_name and lookup_cols:
        cur = conn.cursor(dictionary=True, buffered=True)
        where_parts = []
        where_values = []
        for col, val in lookup_cols.items():
            if val is None:
                where_parts.append(f"{col} IS NULL")
            else:
                where_parts.append(f"{col} = %s")
                where_values.append(val)
        
        if where_parts:
            find_sql = f"SELECT {pk_col_name} FROM {table} WHERE {' AND '.join(where_parts)} LIMIT 1"
            cur.execute(find_sql, where_values)
            result = cur.fetchone()
            cur.close()
            if result:
                return result[pk_col_name]
        else:
            cur.close()
    
    cur = conn.cursor(dictionary=True, buffered=True)
    cur.execute("SELECT LAST_INSERT_ID() AS id")
    rid = cur.fetchone()["id"]
    cur.close()
    return rid

def main():
    """Main ETL function to extract, transform, and load property data."""
    print("=" * 60)
    print("Starting ETL Process")
    print("=" * 60)
    
    print("\n[Step 1] Loading configuration...")
    cfg = load_config()
    defaults = cfg.get("defaults") or {}
    country_default = defaults.get("country", "USA")
    print(f"  Default country: {country_default}")

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Input JSON not found at {DATA_PATH}")
    
    print(f"\n[Step 2] Reading input data from {DATA_PATH}...")
    records = read_input_records(DATA_PATH)
    if not records:
        print("No records found; nothing to do.")
        return
    print(f"  Found {len(records)} property records")

    print("\n[Step 3] Connecting to database...")
    conn = get_conn()
    try:
        print("  Connection established successfully")
        
        print("\n[Step 4] Creating/updating database schema...")
        run_schema(conn)
        print("  Schema created/updated successfully")

        print("\n[Step 5] Staging raw data...")
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE stg_properties_raw")
        cur.executemany("INSERT INTO stg_properties_raw (raw_json) VALUES (%s)",
                        [(json.dumps(r),) for r in records])
        cur.close()
        print(f"  Staged {len(records)} raw records")

        print("\n[Step 6] Transforming and loading data...")
        processed = 0
        for rec in records:
            bk_parts = [
                rec.get("Street_Address"),
                rec.get("City"),
                rec.get("State"),
                rec.get("Zip"),
            ]
            property_bk = hash_key(bk_parts)

            prop = {
                "property_bk": property_bk,
                "year_built": rec.get("Year_Built"),
                "property_type": rec.get("Property_Type"),
                "square_feet": parse_number(rec.get("SQFT_Total")),
                "bedrooms": parse_number(rec.get("Bed")),
                "bathrooms": parse_number(rec.get("Bath")),
                "lot_size_sqft": None,
            }

            addr = {
                "address_line1": rec.get("Street_Address"),
                "address_line2": None,
                "city": rec.get("City"),
                "state": rec.get("State"),
                "postal_code": rec.get("Zip"),
                "county": None,
                "country": country_default,
                "latitude": parse_number(rec.get("Latitude")),
                "longitude": parse_number(rec.get("Longitude")),
            }

            hoa = aggregate_hoa(rec.get("HOA"))
            val = best_valuation(rec.get("Valuation"))
            reh = aggregate_rehab(rec.get("Rehab"))

            tax = None
            if rec.get("Taxes") not in (None, "", " "):
                tax = {"tax_year": None, "assessed_value": None, "tax_amount": parse_number(rec.get("Taxes"))}

            prop_sk = upsert(conn, "dim_property", prop)
            addr_sk = upsert(conn, "dim_address", addr)
            hoa_sk = upsert(conn, "dim_hoa", hoa) if (hoa and any(v is not None for v in hoa.values())) else None
            val_sk = upsert(conn, "dim_valuation", val) if (val and any(v is not None for v in val.values())) else None
            reh_sk = upsert(conn, "dim_rehab", reh) if (reh and any(v is not None for v in reh.values())) else None
            tax_sk = upsert(conn, "dim_tax", tax) if (tax and any(v is not None for v in tax.values())) else None

            eff_date = (val or {}).get("as_of_date") or (reh or {}).get("as_of_date") or "1970-01-01"
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO fact_property_snapshot
                  (property_sk, address_sk, hoa_sk, valuation_sk, rehab_sk, tax_sk, effective_date, source_record_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (prop_sk, addr_sk, hoa_sk, val_sk, reh_sk, tax_sk, eff_date, None))
            cur.close()
            
            processed += 1
            if processed % 100 == 0:
                print(f"  Processed {processed}/{len(records)} records...")

        conn.commit()
        print(f"\n[Step 7] Committing transaction...")
        print(f"  Successfully processed {processed} records")
        print("\n" + "=" * 60)
        print("ETL completed successfully!")
        print("=" * 60)
    except Exception as e:
        conn.rollback()
        print(f"\nERROR: ETL failed with error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        raise
    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
