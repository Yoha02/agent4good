import feedparser
import requests

# Test different InciWeb URLs
urls = [
    'https://inciweb.nwcg.gov/feeds/rss/incidents/',
    'https://inciweb.nwcg.gov/incidents/rss.xml',
    'http://inciweb.nwcg.gov/feeds/rss/incidents/',
    'https://www.nifc.gov/rss/nifc_incidents.rss'
]

for url in urls:
    print(f"\nTesting URL: {url}")
    try:
        feed = feedparser.parse(url)
        print(f"Status: {feed.get('status', 'N/A')}")
        print(f"Entries: {len(feed.entries)}")
        if feed.entries:
            print(f"First entry title: {feed.entries[0].get('title', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")

# Also try direct HTTP request
print("\n\nDirect HTTP request to InciWeb:")
try:
    response = requests.get('https://inciweb.nwcg.gov/', timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response length: {len(response.text)}")
except Exception as e:
    print(f"Error: {e}")
