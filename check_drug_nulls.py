from google.cloud import bigquery

client = bigquery.Client(project='qwiklabs-gcp-00-4a7d408c735c')

query = """
SELECT 
    COUNT(*) as total,
    COUNTIF(drug_name IS NOT NULL) as with_drug_name,
    COUNTIF(status IS NOT NULL) as with_status,
    COUNTIF(manufacturer IS NOT NULL) as with_manufacturer
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.drug_availability`
"""

results = list(client.query(query).result())
for row in results:
    print(f"Total records: {row['total']}")
    print(f"Records with drug_name: {row['with_drug_name']}")
    print(f"Records with status: {row['with_status']}")
    print(f"Records with manufacturer: {row['with_manufacturer']}")

# Try to find records with actual data
query2 = """
SELECT *
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.drug_availability`
WHERE drug_name IS NOT NULL
LIMIT 5
"""

print("\nRecords with drug_name:")
results2 = list(client.query(query2).result())
print(f"Found {len(results2)} records")
if results2:
    for row in results2:
        d = dict(row)
        print(f"\nDrug: {d.get('drug_name')}")
        print(f"  Manufacturer: {d.get('manufacturer')}")
        print(f"  Status: {d.get('status')}")
        print(f"  Created: {d.get('created_at')}")
