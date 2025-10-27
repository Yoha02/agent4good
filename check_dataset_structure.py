import requests
import json

# Check the structure of the 6jg4-xsqq dataset
url = "https://data.cdc.gov/resource/6jg4-xsqq.json"
params = {
    '$limit': 2
}

response = requests.get(url, params=params)
print("Status:", response.status_code)
print("\nSample records:")
data = response.json()
for record in data:
    print(json.dumps(record, indent=2))
    break

print("\nFields available:")
if data:
    print(list(data[0].keys()))
