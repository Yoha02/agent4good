"""
Direct query to count rows in cdc_covid_hospitalizations table
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

def check_table():
    table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.cdc_covid_hospitalizations"
    
    # Method 1: Direct count query
    query = f"""
    SELECT COUNT(*) as row_count
    FROM `{table_id}`
    """
    
    logger.info("Running direct COUNT query...")
    results = bq_client.query(query).result()
    
    for row in results:
        logger.info(f"Total rows via COUNT(*): {row.row_count:,}")
    
    # Method 2: Check table metadata
    table = bq_client.get_table(table_id)
    logger.info(f"Table metadata num_rows: {table.num_rows:,}")
    
    # Method 3: Sample some actual rows
    sample_query = f"""
    SELECT 
        weekenddate,
        state,
        agecategory,
        sex,
        weeklyrate,
        cumulativerate
    FROM `{table_id}`
    ORDER BY weekenddate DESC
    LIMIT 10
    """
    
    logger.info("\nSample of actual data rows:")
    sample_results = bq_client.query(sample_query).result()
    
    count = 0
    for row in sample_results:
        count += 1
        logger.info(f"  {row.weekenddate} | {row.state:15s} | {row.agecategory:25s} | Weekly: {row.weeklyrate} | Cumulative: {row.cumulativerate}")
    
    logger.info(f"\nTotal sample rows returned: {count}")
    
    # Check for unique dates
    dates_query = f"""
    SELECT DISTINCT weekenddate
    FROM `{table_id}`
    ORDER BY weekenddate DESC
    LIMIT 20
    """
    
    logger.info("\nUnique dates in table:")
    dates_results = bq_client.query(dates_query).result()
    
    for row in dates_results:
        logger.info(f"  {row.weekenddate}")

if __name__ == "__main__":
    check_table()
