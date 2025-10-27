import requests

print("Fetching data from CDC API...")
data = requests.get('https://data.cdc.gov/resource/kvib-3txy.json', 
                   params={'$limit': 50000}, 
                   timeout=60).json()

print(f"Total records fetched: {len(data)}")

# Check for October 2025 data
oct_2025_data = [r for r in data if '2025-10' in str(r.get('_weekenddate', ''))]
print(f"October 2025 records: {len(oct_2025_data)}")

# Get all 2025 dates
dates_2025 = sorted(set([r.get('_weekenddate') for r in data if '2025' in str(r.get('_weekenddate', ''))]))
print(f"\n2025 dates found: {len(dates_2025)}")
print("Latest 5 dates:")
for date in dates_2025[-5:]:
    count = len([r for r in data if r.get('_weekenddate') == date])
    print(f"  {date}: {count} records")

# Check year distribution
years = {}
for r in data:
    year = str(r.get('mmwr_year', '')).split('.')[0]
    years[year] = years.get(year, 0) + 1

print("\nYear distribution:")
for year in sorted(years.keys(), reverse=True):
    print(f"  {year}: {years[year]} records")
