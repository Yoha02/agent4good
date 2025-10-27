import requests
import csv
from io import StringIO
import os

print("Testing CDC COVID data endpoint...")
base_url = "https://data.cdc.gov/api/v3/views/6jg4-xsqq/query.csv"

print("\n1. Without authentication:")
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    # Some APIs work without token if you look like a browser
    response = requests.get(base_url, headers=headers, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        rows = list(reader)
        print(f"   ✓ SUCCESS! Total rows: {len(rows)}")
        if rows:
            print(f"   Columns: {list(rows[0].keys())[:5]}...")
            print(f"   First row sample: {dict(list(rows[0].items())[:3])}")
            print(f"   Last row sample: {dict(list(rows[-1].items())[:3])}")
    else:
        print(f"   Error: {response.text[:300]}")
except Exception as e:
    print(f"   Exception: {e}")

print("\n2. Try the regular Socrata endpoint (6jg4-xsqq):")
try:
    # Standard Socrata API format
    url2 = "https://data.cdc.gov/resource/6jg4-xsqq.json"
    params = {
        '$limit': 10,
        '$order': ':id DESC'
    }
    response = requests.get(url2, params=params, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ SUCCESS! Records: {len(data)}")
        if data:
            print(f"   Columns: {list(data[0].keys())[:5]}...")
            print(f"   Latest record: {dict(list(data[0].items())[:3])}")
    else:
        print(f"   Error: {response.text[:300]}")
except Exception as e:
    print(f"   Exception: {e}")
