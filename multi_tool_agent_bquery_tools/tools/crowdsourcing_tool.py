
from datetime import datetime, timezone
from typing import Optional, List
from google.cloud import bigquery, storage
from google import generativeai as genai

import os, uuid, tempfile, requests
from google.cloud import storage

# Try to import ADK io, but make it optional
try:
    from google.adk import io as adk_io
    ADK_IO_AVAILABLE = True
except ImportError:
    print("[WARNING] google.adk.io not available - image handling will be limited")
    adk_io = None
    ADK_IO_AVAILABLE = False

# --- Text summarizer (Gemini) ---
def generate_text_summary(description: str, media_summary: str = None) -> Optional[str]:
    """Use Gemini to create a concise, plain-text overall issue summary."""
    if not description and not media_summary:
        return None

    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        prompt = f"""
        You are a public health summarizer.
        Given the following report description and media summary,
        generate a concise 2-3 sentence overview suitable for a public health dashboard.

        Description:
        {description or 'No description'}

        Media Summary:
        {media_summary or 'No image analysis'}

        Only return the plain text summary, no formatting or headers.
        """
        resp = model.generate_content(prompt)
        return resp.text.strip() if resp and resp.text else None
    except Exception as e:
        print(f"[ERROR] Text summary generation failed: {e}")
        return None



def upload_to_gcs(local_path_or_url: Optional[str] = None,
                  referenced_image_ids: Optional[List[str]] = None,
                  bucket_name: str = "agent4good-report-attachments") -> str:
    """
    Uploads image to GCS (supports both ADK image bytes and external URLs).
    """
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        source = None

        # --- 1️⃣ If ADK gave us in-memory images ---
        if referenced_image_ids:
            print(f"[INFO] Received ADK image references: {referenced_image_ids}")
            if not ADK_IO_AVAILABLE or adk_io is None:
                print(f"[WARNING] ADK io not available - cannot process image references")
            else:
                for image_id in referenced_image_ids:
                    try:
                        img_bytes = adk_io.get_image_bytes(image_id)
                        if img_bytes:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                                tmp.write(img_bytes)
                                source = tmp.name
                                print(f"[INFO] Saved ADK image to temp: {source}")
                                break
                    except Exception as e:
                        print(f"[WARN] Could not extract ADK image bytes: {e}")

        # --- 2️⃣ Otherwise, handle external/local path ---
        if not source:
            if local_path_or_url and local_path_or_url.startswith("http"):
                print(f"[INFO] Downloading from remote URL: {local_path_or_url}")
                resp = requests.get(local_path_or_url, stream=True, timeout=10)
                resp.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    for chunk in resp.iter_content(8192):
                        tmp.write(chunk)
                    source = tmp.name
            elif local_path_or_url and os.path.exists(local_path_or_url):
                source = local_path_or_url

        if not source:
            print("[ERROR] No valid source to upload.")
            return None

        # --- 3️⃣ Upload to GCS ---
        blob_name = f"reports/{uuid.uuid4()}/{os.path.basename(source)}"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(source)
        blob.make_public()

        print(f"[INFO] ✅ Uploaded to GCS: {blob.public_url}")
        return blob.public_url

    except Exception as e:
        print(f"[ERROR] GCS upload failed: {e}")
        return None


# --- Severity inference helper ---
def infer_severity(description: Optional[str]) -> str:
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
    """Infer city/state/ZIP from text using OpenStreetMap."""
    if not location_text:
        return None, None, None, None, None, None

    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location_text, "format": "json", "addressdetails": 1, "limit": 1, "countrycodes": "us"},
            headers={"User-Agent": "crowdsourcing-agent"},
        )
        data = resp.json()
        if not data:
            return None, None, None, None, None, None

        result = data[0]
        address = result.get("address", {})
        if address.get("country_code", "").lower() != "us":
            return None, None, None, None, None, None

        city = address.get("city") or address.get("town") or address.get("village")
        state = address.get("state")
        county = address.get("county")
        zip_code = address.get("postcode")
        lat, lon = float(result.get("lat", 0)), float(result.get("lon", 0))
        print(f"[INFO] Location resolved: {city}, {state} (US)")
        return city, state, zip_code, county, lat, lon
    except Exception as e:
        print(f"[WARN] Location inference failed: {e}")
        return None, None, None, None, None, None


# --- Main BigQuery insert ---
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
    """Insert a report with location + media + AI summaries into BigQuery."""

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
    dataset_id, table_id = "CrowdsourceData", "CrowdSourceData"
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    inferred_severity = severity or infer_severity(description)

    # --- Location details ---
    city, state, zip_code, county, latitude, longitude = infer_location_from_text(location_text) if location_text else (None, None, None, None, None, None)

    # --- Privacy handling ---
    if is_anonymous:
        contact_name = contact_email = contact_phone = None

    # --- Upload media ---
    media_urls, attachment_urls, media_count = [], [], 0
    if media_file_path:
        gcs_url = upload_to_gcs(media_file_path)
        if gcs_url:
            media_urls.append(gcs_url)
            attachment_urls.append(gcs_url)
            media_count = 1

    # --- Generate overall summary ---
    ai_overall_summary = ai_overall_summary or generate_text_summary(description, ai_media_summary)

    # --- Compose row ---
    report_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

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

    try:
        errors = client.insert_rows_json(table_ref, [row])
        if errors:
            print(f"[ERROR] Insert failed: {errors}")
            return f"⚠️ Error inserting report: {errors}"
        return f"✅ Report logged successfully (ID: {report_id}) — Severity: {inferred_severity.title()}"
    except Exception as e:
        print(f"[ERROR] BigQuery insert failed: {e}")
        return f"⚠️ BigQuery insert error: {e}"
