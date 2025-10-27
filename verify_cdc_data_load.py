"""
Verify CDC data loaded properly into BigQuery
"""
import os
from google.cloud import bigquery
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

bq_client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
DATASET = os.getenv('BIGQUERY_DATASET', 'CrowdsourceData')

def verify_table(table_name, date_column):
    """Verify a table has data loaded"""
    table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{table_name}"
    
    try:
        # Check if table exists
        table = bq_client.get_table(table_id)
        logger.info(f"\n✓ Table {table_name} exists")
        logger.info(f"  Description: {table.description}")
        
        # Query record count and date range
        query = f"""
        SELECT 
            COUNT(*) as total_records,
            MIN({date_column}) as earliest_date,
            MAX({date_column}) as latest_date
        FROM `{table_id}`
        """
        
        results = bq_client.query(query).result()
        
        for row in results:
            logger.info(f"  Total Records: {row.total_records:,}")
            logger.info(f"  Date Range: {row.earliest_date} to {row.latest_date}")
            
            # Check if latest date is within past 60 days
            from datetime import datetime, timedelta, date
            
            if isinstance(row.latest_date, datetime):
                latest = row.latest_date.date()
            elif isinstance(row.latest_date, date):
                latest = row.latest_date
            else:
                latest = datetime.fromisoformat(str(row.latest_date)).date()
            
            today = date(2025, 10, 27)  # Current date
            days_old = (today - latest).days
            
            if days_old <= 30:
                logger.info(f"  ✓ Data is CURRENT ({days_old} days old)")
            elif days_old <= 60:
                logger.info(f"  ⚠ Data is somewhat old ({days_old} days old)")
            else:
                logger.info(f"  ✗ Data is TOO OLD ({days_old} days old)")
        
        # Show sample records
        sample_query = f"""
        SELECT *
        FROM `{table_id}`
        ORDER BY {date_column} DESC
        LIMIT 3
        """
        
        logger.info(f"  Sample Records (most recent 3):")
        sample_results = bq_client.query(sample_query).result()
        
        for idx, row in enumerate(sample_results, 1):
            logger.info(f"    Record {idx}: {dict(row)}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error verifying {table_name}: {e}")
        return False

def main():
    logger.info("=" * 80)
    logger.info("VERIFYING CDC DATA IN BIGQUERY")
    logger.info("=" * 80)
    
    tables = [
        ('respiratory_disease_rates', 'weekenddate'),
        ('nrevss_respiratory_data', 'mmwrweek_end'),
        ('cdc_covid_hospitalizations', 'weekenddate')
    ]
    
    success_count = 0
    for table_name, date_column in tables:
        if verify_table(table_name, date_column):
            success_count += 1
    
    logger.info("\n" + "=" * 80)
    logger.info(f"VERIFICATION COMPLETE: {success_count}/{len(tables)} tables verified successfully")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
