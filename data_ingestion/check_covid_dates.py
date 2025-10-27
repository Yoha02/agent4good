import requests

url = "https://data.cdc.gov/resource/6jg4-xsqq.json"
params = {
    '$limit': 10,
    '$order': '_weekenddate DESC'
}

response = requests.get(url, params=params, timeout=30)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    print(f"Total records: {len(data)}\n")
    print("Most recent dates:")
    for d in data:
        print(f"  Date: {d.get('_weekenddate')}, State: {d.get('state')}, Season: {d.get('season')}")
