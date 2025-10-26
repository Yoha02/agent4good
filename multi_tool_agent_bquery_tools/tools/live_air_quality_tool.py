import os
import requests

def get_live_air_quality(location: str):
    """
    Fetches current air quality data from AirNow API.
    - ZIP → AirNow ZIP endpoint.
    - City/County → geocode to lat/long then AirNow lat/long endpoint.
    """
    api_key = os.environ.get("AIRNOW_API_KEY")
    if not api_key:
        return "Error: AIRNOW_API_KEY environment variable not set."

    try:
        # 1️⃣ ZIP check
        is_zip = location.isdigit() and len(location) == 5
        if is_zip:
            url = "https://www.airnowapi.org/aq/observation/zipCode/current/"
            params = {
                "format": "application/json",
                "zipCode": location,
                "distance": 25,
                "API_KEY": api_key,
            }
        else:
            # 2️⃣ Geocode for city/county
            geo_resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": location, "format": "json", "addressdetails": 1, "limit": 1},
                headers={"User-Agent": "air-quality-agent"},
                timeout=10,
            )
            geo_data = geo_resp.json()
            if not geo_data:
                return f"❌ Could not resolve '{location}' to coordinates."

            lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
            url = "https://www.airnowapi.org/aq/observation/latLong/current/"
            params = {
                "format": "application/json",
                "latitude": lat,
                "longitude": lon,
                "distance": 25,
                "API_KEY": api_key,
            }

        # 3️⃣ Query AirNow
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return f"No air quality data found for '{location}'."

        # 4️⃣ Format output
        lines = []
        for entry in data:
            pollutant = entry.get("ParameterName")
            aqi = entry.get("AQI")
            cat = entry.get("Category", {}).get("Name")
            area = entry.get("ReportingArea")
            lines.append(f"{pollutant}: {cat} (AQI {aqi}) in {area}")

        return f"🌤 Live Air Quality near {location}:\n" + "\n".join(lines)

    except Exception as e:
        return f"Error fetching live air quality data: {e}"
