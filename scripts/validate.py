"""
Validation script for ETL pipeline.
Runs data quality checks and generates a summary report.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils import get_conn

def run_validation():
    """Run validation queries and print results."""
    print("=" * 60)
    print("ETL Validation Report")
    print("=" * 60)
    
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        
        # Check 1: Raw records count
        print("\n[Check 1] Raw Records Staging")
        print("-" * 60)
        cur.execute("SELECT COUNT(*) AS count FROM stg_properties_raw")
        raw_count = cur.fetchone()["count"]
        print(f"  Raw records in staging: {raw_count}")
        
        # Check 2: Dimension counts
        print("\n[Check 2] Dimension Table Counts")
        print("-" * 60)
        dimensions = [
            "dim_property",
            "dim_address",
            "dim_hoa",
            "dim_valuation",
            "dim_rehab",
            "dim_tax"
        ]
        dim_counts = {}
        for dim in dimensions:
            cur.execute(f"SELECT COUNT(*) AS count FROM {dim}")
            count = cur.fetchone()["count"]
            dim_counts[dim] = count
            print(f"  {dim}: {count} records")
        
        # Check 3: Fact table count
        print("\n[Check 3] Fact Table")
        print("-" * 60)
        cur.execute("SELECT COUNT(*) AS count FROM fact_property_snapshot")
        fact_count = cur.fetchone()["count"]
        print(f"  Fact records: {fact_count}")
        
        # Check 4: Data integrity - orphaned records
        print("\n[Check 4] Data Integrity Checks")
        print("-" * 60)
        
        # Check for missing addresses
        cur.execute("""
            SELECT COUNT(*) AS count 
            FROM fact_property_snapshot 
            WHERE address_sk IS NULL
        """)
        bad_addr = cur.fetchone()["count"]
        print(f"  Missing addresses: {bad_addr} (should be 0)")
        
        # Check for missing properties
        cur.execute("""
            SELECT COUNT(*) AS count 
            FROM fact_property_snapshot fps
            LEFT JOIN dim_property p ON p.property_sk = fps.property_sk
            WHERE p.property_sk IS NULL
        """)
        bad_prop = cur.fetchone()["count"]
        print(f"  Missing properties: {bad_prop} (should be 0)")
        
        # Check valuation integrity
        cur.execute("""
            SELECT COUNT(*) AS count
            FROM fact_property_snapshot fps
            LEFT JOIN dim_valuation v ON v.valuation_sk = fps.valuation_sk
            WHERE (fps.valuation_sk IS NOT NULL) AND (v.provider IS NULL)
        """)
        val_mismatch = cur.fetchone()["count"]
        print(f"  Valuation mismatches: {val_mismatch} (should be 0)")
        
        # Check 5: Sample data preview
        print("\n[Check 5] Sample Data Preview")
        print("-" * 60)
        cur.execute("""
            SELECT 
                p.property_type,
                p.square_feet,
                a.city,
                a.state,
                v.estimate AS valuation,
                t.tax_amount
            FROM fact_property_snapshot fps
            JOIN dim_property p ON p.property_sk = fps.property_sk
            JOIN dim_address a ON a.address_sk = fps.address_sk
            LEFT JOIN dim_valuation v ON v.valuation_sk = fps.valuation_sk
            LEFT JOIN dim_tax t ON t.tax_sk = fps.tax_sk
            LIMIT 5
        """)
        samples = cur.fetchall()
        for i, sample in enumerate(samples, 1):
            print(f"\n  Sample {i}:")
            print(f"    Type: {sample['property_type']}")
            print(f"    Square Feet: {sample['square_feet']}")
            print(f"    Location: {sample['city']}, {sample['state']}")
            print(f"    Valuation: ${sample['valuation']:,.2f}" if sample['valuation'] else "    Valuation: N/A")
            print(f"    Tax: ${sample['tax_amount']:,.2f}" if sample['tax_amount'] else "    Tax: N/A")
        
        # Check 6: Summary statistics
        print("\n[Check 6] Summary Statistics")
        print("-" * 60)
        
        # Properties by type
        cur.execute("""
            SELECT property_type, COUNT(*) AS count
            FROM dim_property
            WHERE property_type IS NOT NULL
            GROUP BY property_type
            ORDER BY count DESC
        """)
        prop_types = cur.fetchall()
        print("\n  Properties by Type:")
        for pt in prop_types:
            print(f"    {pt['property_type']}: {pt['count']}")
        
        # States represented
        cur.execute("""
            SELECT state, COUNT(*) AS count
            FROM dim_address
            WHERE state IS NOT NULL
            GROUP BY state
            ORDER BY count DESC
            LIMIT 10
        """)
        states = cur.fetchall()
        print("\n  Top 10 States by Property Count:")
        for state in states:
            print(f"    {state['state']}: {state['count']}")
        
        # Valuation statistics
        cur.execute("""
            SELECT 
                COUNT(*) AS count,
                AVG(estimate) AS avg_estimate,
                MIN(estimate) AS min_estimate,
                MAX(estimate) AS max_estimate
            FROM dim_valuation
            WHERE estimate IS NOT NULL
        """)
        val_stats = cur.fetchone()
        if val_stats['count'] > 0:
            print("\n  Valuation Statistics:")
            print(f"    Count: {val_stats['count']}")
            print(f"    Average: ${val_stats['avg_estimate']:,.2f}")
            print(f"    Min: ${val_stats['min_estimate']:,.2f}")
            print(f"    Max: ${val_stats['max_estimate']:,.2f}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("Validation Summary")
        print("=" * 60)
        
        issues = []
        if raw_count == 0:
            issues.append("No raw records found in staging table")
        if fact_count == 0:
            issues.append("No fact records found")
        if bad_addr > 0:
            issues.append(f"{bad_addr} fact records with missing addresses")
        if bad_prop > 0:
            issues.append(f"{bad_prop} fact records with missing properties")
        if val_mismatch > 0:
            issues.append(f"{val_mismatch} valuation foreign key mismatches")
        
        if issues:
            print("\nIssues Found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\nAll validation checks passed!")
            print(f"\nSuccessfully processed {raw_count} raw records into {fact_count} fact records.")
            print(f"Created {sum(dim_counts.values())} dimension records across {len(dim_counts)} tables.")
        
        print("=" * 60)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\nValidation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_validation()

