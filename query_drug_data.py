from google.cloud import bigquery
import json

client = bigquery.Client(project='qwiklabs-gcp-00-4a7d408c735c')

query = """
SELECT drug_name, manufacturer, status, dosage_form, created_at 
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.drug_availability` 
ORDER BY created_at DESC 
LIMIT 5
"""

results = list(client.query(query).result())
print('Sample Data:')
for row in results:
    print(json.dumps(dict(row), indent=2, default=str))
