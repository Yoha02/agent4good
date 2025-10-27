"""
Check drug availability table structure in BigQuery
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

table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.drug_availability"

# Check schema
table = bq_client.get_table(table_id)
logger.info(f"Table schema for drug_availability:")
for field in table.schema:
    logger.info(f"  {field.name}: {field.field_type} ({field.mode})")

# Get sample data
query = """
SELECT *
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.drug_availability`
ORDER BY updated_date DESC
LIMIT 5
"""

results = bq_client.query(query).result()
logger.info("\nSample records:")
for row in results:
    logger.info(dict(row))
