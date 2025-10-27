import os
import uuid
import requests
from datetime import datetime, timezone
from typing import Optional, List
from google.cloud import bigquery, storage


# --- Upload helper (to your GCS bucket) ---
def upload_to_gcs(local_path: str, bucket_name: str = "agent4good-report-attachments") -> str:
    """Uploads an image/file to GCS and returns the public URL."""
    try:
        print(f"[DEBUG] Received media_file_path: {local_path}")

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob_name = f"reports/{uuid.uuid4()}-{os.path.basename(local_path)}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        blob.make_public()
        print(f"[INFO] Uploaded to GCS: {blob.public_url}")
        return blob.public_url
    except Exception as e:
        print(f"[WARN] Upload failed: {e}")
        return None


# --- Severity inference helper ---
def infer_severity(description: Optional[str]) -> str:
    """Infer severity level from description text."""
    if not description:
        return "unknown"
    desc = description.lower()
    if any(w in desc for w in ["can't breathe", "barely see", "smoke", "fire", "urgent", "serious", "severe", "panic", "collapse"]):
        return "severe"
    if any(w in desc for w in ["moderate", "concern", "some", "visible", "noticeable", "uncomfortable"]):
        return "moderate"
    if any(w in desc for w in ["minor", "small", "slight", "mild", "a little", "light"]):
        return "low"
    return "moderate"


# --- Location inference helper ---
def infer_location_from_text(location_text: Optional[str]):
    """Use OpenStreetMap (Nominatim) to infer structured location data (US only)."""
    if not location_text:
        return None, None, None, None, None, None

    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": location_text,
                "format": "json",
                "addressdetails": 1,
                "limit": 1,
                "countrycodes": "us"  # Restrict to United States only
            },
            headers={"User-Agent": "crowdsourcing-agent"}
        )
        data = resp.json()
        if not data:
            return None, None, None, None, None, None

        result = data[0]
        address = result.get("address", {})
        
        # Verify it's actually in the US (double-check)
        country = address.get("country")
        country_code = address.get("country_code")
        if country_code and country_code.lower() != "us":
            print(f"[WARN] Location '{location_text}' resolved to {country}, skipping non-US location")
            return None, None, None, None, None, None

        city = address.get("city") or address.get("town") or address.get("village")
        state = address.get("state")
        county = address.get("county")
        zip_code = address.get("postcode")
        lat = float(result.get("lat", 0))
        lon = float(result.get("lon", 0))
        
        print(f"[INFO] Location resolved: {city}, {state} (US)")
        return city, state, zip_code, county, lat, lon

    except Exception as e:
        print(f"[WARN] Location inference failed: {e}")
        return None, None, None, None, None, None


# --- Main BigQuery insert function ---
def report_to_bq(
    report_type: Optional[str] = None,
    severity: Optional[str] = None,
    specific_type: Optional[str] = None,
    description: Optional[str] = None,
    location_text: Optional[str] = None,
    address: Optional[str] = None,
    people_affected: Optional[str] = None,
    timeframe: Optional[str] = None,
    is_anonymous: bool = True,
    contact_name: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    media_file_path: Optional[str] = None,
    ai_media_summary: Optional[str] = None,
    ai_overall_summary: Optional[str] = None,
    manual_tags: Optional[List[str]] = None,
):
    """
    Inserts a new report into CrowdsourceData.CrowdSourceData
    with full schema mapping and GCS upload support.
    """

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
    dataset_id = "CrowdsourceData"
    table_id = "CrowdSourceData"

    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    # --- Infer severity if missing ---
    inferred_severity = severity or infer_severity(description)

    # --- Infer location details ---
    city, state, zip_code, county, latitude, longitude = (None, None, None, None, None, None)
    if location_text:
        city, state, zip_code, county, latitude, longitude = infer_location_from_text(location_text)

    # --- Handle anonymity ---
    if is_anonymous:
        contact_name = None
        contact_email = None
        contact_phone = None

    # --- Upload media if provided ---
    media_urls = []
    attachment_urls = []
    media_count = 0
    if media_file_path and os.path.exists(media_file_path):
        gcs_url = upload_to_gcs(media_file_path)
        if gcs_url:
            media_urls.append(gcs_url)
            attachment_urls.append(gcs_url)
            media_count = 1

    report_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    zip_code = zip_code or None
    if isinstance(zip_code, str):
        zip_code = zip_code.strip()
        if not zip_code:
            zip_code = None


    row = {
        "report_id": report_id,
        "report_type": report_type or "health",
        "timestamp": timestamp,
        "address": address,
        "zip_code": zip_code,
        "city": city,
        "state": state,
        "severity": inferred_severity,
        "specific_type": specific_type or "unspecified",
        "description": description,
        "people_affected": people_affected or "unknown",
        "timeframe": timeframe or "unspecified",
        "contact_name": contact_name,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
        "is_anonymous": is_anonymous,
        "media_urls": media_urls,
        "media_count": media_count,
        "ai_media_summary": ai_media_summary,
        "ai_overall_summary": ai_overall_summary,
        "status": "pending",
        "reviewed_by": None,
        "reviewed_at": None,
        "notes": None,
        "latitude": latitude,
        "longitude": longitude,
        "county": county,
        "ai_tags": None,
        "ai_confidence": None,
        "ai_analyzed_at": None,
        "attachment_urls": ", ".join(attachment_urls) if attachment_urls else None,
        "exclude_from_analysis": False,
        "exclusion_reason": None,
        "manual_tags": ", ".join(manual_tags) if manual_tags else None,
    }

    errors = client.insert_rows_json(table_ref, [row])
    if errors:
        print(f"[ERROR] Insert failed: {errors}")
        return f"⚠️ Error inserting report: {errors}"

    return f"✅ Report logged successfully (ID: {report_id}) — Severity: {inferred_severity.title()}"
