"""
Fix date formatting in BigQuery nrevss_respiratory_data table
This script adds a new column with properly formatted ISO date strings
"""

from google.cloud import bigquery
import os

# Configuration
GCP_PROJECT_ID = 'qwiklabs-gcp-00-4a7d408c735c'
DATASET_ID = 'CrowdsourceData'
TABLE_ID = 'nrevss_respiratory_data'
FULL_TABLE_ID = f'{GCP_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}'

def fix_dates_in_table():
    """Add a date_string column with properly formatted ISO dates"""
    
    print("=" * 80)
    print("🔧 FIXING DATES IN BIGQUERY TABLE")
    print("=" * 80)
    
    # Initialize BigQuery client
    client = bigquery.Client(project=GCP_PROJECT_ID)
    
    # Step 1: Check if date_string column already exists
    print("\n[1/4] Checking current table schema...")
    table = client.get_table(FULL_TABLE_ID)
    existing_fields = [field.name for field in table.schema]
    print(f"Current columns: {existing_fields}")
    
    if 'date_string' in existing_fields:
        print("⚠️  date_string column already exists. Updating values...")
    else:
        print("✓ date_string column doesn't exist. Will add it.")
        
        # Step 2: Add the new column
        print("\n[2/4] Adding date_string column...")
        alter_query = f"""
        ALTER TABLE `{FULL_TABLE_ID}`
        ADD COLUMN IF NOT EXISTS date_string STRING
        """
        client.query(alter_query).result()
        print("✓ Column added successfully")
    
    # Step 3: Check what's actually in repweekdate
    print("\n[3/4] Checking actual data in repweekdate column...")
    check_query = f"""
    SELECT 
        repweekdate,
        LENGTH(repweekdate) as date_length,
        testtype,
        rsvpos
    FROM `{FULL_TABLE_ID}`
    WHERE repweekdate IS NOT NULL
    LIMIT 10
    """
    
    results = client.query(check_query).result()
    print("\n📊 Sample data showing repweekdate values:")
    print("-" * 80)
    for i, row in enumerate(results, 1):
        print(f"{i}. repweekdate: '{row.repweekdate}' (length: {row.date_length})")
        print(f"   testtype: {row.testtype}, positives: {row.rsvpos}")
    
    # Step 4: Update based on actual format
    print("\n[4/4] Converting string dates to ISO format...")
    
    # The dates are in format like "10JUL2010", convert to "2010-07-10"
    update_query = f"""
    UPDATE `{FULL_TABLE_ID}`
    SET date_string = FORMAT_DATE('%Y-%m-%d', PARSE_DATE('%d%b%Y', repweekdate))
    WHERE repweekdate IS NOT NULL AND LENGTH(repweekdate) > 4
    """
    
    job = client.query(update_query)
    result = job.result()
    print(f"✓ Updated {job.num_dml_affected_rows} rows")
    
    # Step 5: Verify the results
    print("\n[5/5] Verifying results...")
    verify_query = f"""
    SELECT 
        repweekdate,
        date_string,
        testtype,
        rsvpos,
        rsvtest
    FROM `{FULL_TABLE_ID}`
    WHERE repweekdate IS NOT NULL
    ORDER BY repweekdate DESC
    LIMIT 5
    """
    
    results = client.query(verify_query).result()
    
    print("\n📊 Sample data (first 5 rows):")
    print("-" * 80)
    for i, row in enumerate(results, 1):
        print(f"{i}. repweekdate: {row.repweekdate} → date_string: '{row.date_string}'")
        print(f"   testtype: {row.testtype}, positives: {row.rsvpos}, tests: {row.rsvtest}")
    
    print("\n" + "=" * 80)
    print("✅ DATE FIX COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Update app_local.py to use 'date_string' instead of 'repweekdate'")
    print("2. Restart Flask server")
    print("3. Refresh browser - dates should now display correctly!")

if __name__ == "__main__":
    fix_dates_in_table()
