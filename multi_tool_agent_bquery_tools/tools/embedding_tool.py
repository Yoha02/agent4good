# ./tools/embedding_tool.py
from google.cloud import bigquery
import requests, json, os


def generate_report_embeddings(limit: int = 50) -> str:
    """
    Generates and stores text embeddings for new reports from CrowdSourceData
    into ReportEmbeddings table using Gemini text-embedding-004 API.
    """
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    BQ_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
    DATASET = "CrowdsourceData"
    SOURCE = f"{BQ_PROJECT}.{DATASET}.CrowdSourceData"
    DEST = f"{BQ_PROJECT}.{DATASET}.ReportEmbeddings"

    bq = bigquery.Client(project=BQ_PROJECT)

    def get_embedding(text: str):
        url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY}
        payload = {"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}}
        r = requests.post(url, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()["embedding"]["values"]

    # 1️⃣ Fetch unembedded reports
    query = f"""
    SELECT report_id, city, state, county, description, severity, report_type,
        timestamp, contact_name, contact_email, contact_phone, is_anonymous
    FROM `{SOURCE}`
    WHERE report_id NOT IN (SELECT report_id FROM `{DEST}`)

    LIMIT {limit}
    """

    rows = bq.query(query).result()

    rows_to_insert = []
    success, failed = 0, 0

    for r in rows:
        try:
            emb = get_embedding(r.description or "")
            rows_to_insert.append({
            "report_id": r.report_id,
            "city": r.city,
            "state": r.state,
            "county": r.county,
            "description": r.description,
            "severity": r.severity,
            "report_type": r.report_type,
            "timestamp": r.timestamp.isoformat(),
            "contact_name": r.contact_name,
            "contact_email": r.contact_email,
            "contact_phone": r.contact_phone,
            "is_anonymous": r.is_anonymous,
            "description_embedding": emb,
        })

            success += 1
        except Exception as e:
            failed += 1
            print(f"⚠️ failed {r.report_id}: {e}")

    # 2️⃣ Insert embeddings into destination table
    if rows_to_insert:
        errors = bq.insert_rows_json(DEST, rows_to_insert)
        if errors:
            return f"⚠️ Insert errors: {errors}"
    else:
        return "No new reports to embed."

    return f"✅ Generated embeddings for {success} reports, {failed} failed."
