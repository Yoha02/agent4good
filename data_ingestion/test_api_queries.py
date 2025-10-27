import requests

# Test different query approaches
print("Test 1: Using $order parameter with DESC")
url = 'https://data.cdc.gov/resource/kvib-3txy.json'
params = {
    '$limit': 1000,
    '$order': '_weekenddate DESC'
}

try:
    response = requests.get(url, params=params, timeout=30)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Records: {len(data)}")
        if data:
            print(f"  Latest date: {data[0].get('_weekenddate')}")
            print(f"  Earliest date: {data[-1].get('_weekenddate')}")
    else:
        print(f"  Error: {response.text[:200]}")
except Exception as e:
    print(f"  Exception: {e}")

print("\nTest 2: Using $where for year filtering")
params2 = {
    '$limit': 15000,
    '$where': 'mmwr_year >= 2025'
}

try:
    response = requests.get(url, params=params2, timeout=30)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  Records: {len(data)}")
        dates = sorted(set([r.get('_weekenddate') for r in data]))
        print(f"  Latest date: {dates[-1]}")
        print(f"  Earliest date: {dates[0]}")
    else:
        print(f"  Error: {response.text[:200]}")
except Exception as e:
    print(f"  Exception: {e}")
