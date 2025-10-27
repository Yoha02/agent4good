# ./tools/semantic_query_tool.py
import os
import json
import requests
from typing import List
from google.cloud import bigquery


def get_gemini_embedding(text: str) -> List[float]:
    """
    Generates text embeddings using the Gemini API (text-embedding-004).
    Requires an API key with access to the Generative Language API.
    """
    GEMINI_KEY = os.getenv(
        "GEMINI_API_KEY", "AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk"
    )

    url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_KEY}
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        return data["embedding"]["values"]
    except Exception as e:
        raise RuntimeError(f"Error generating embedding via Gemini API: {e}")


def semantic_query_reports(user_query: str, top_k: int = 10) -> str:
    """
    Returns semantically similar reports from BigQuery using Gemini embeddings API.
    Works even without Vertex AI permissions.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
    dataset = "CrowdsourceData"
    table = "CrowdSourceData"
    client = bigquery.Client(project=project_id)

    # 1️⃣ Generate the embedding via Gemini API key
    try:
        qvec = get_gemini_embedding(user_query)
    except Exception as e:
        return f"⚠️ {e}"

    qvec_str = ", ".join(str(v) for v in qvec)  # convert Python list to comma-separated floats

    sql = f"""
    SELECT
      report_id,
      city,
      state,
      county,
      description,
      severity,
      report_type,
      timestamp,
      contact_name,
      contact_email,
      contact_phone,
      is_anonymous,
      (
        SELECT SUM(x * y)
        FROM UNNEST(description_embedding) AS x WITH OFFSET
        JOIN UNNEST([{qvec_str}]) AS y WITH OFFSET
        USING (offset)
      ) AS similarity
    FROM `{project_id}.{dataset}.ReportEmbeddings`
    ORDER BY similarity DESC
    LIMIT {top_k}
    """


    # 3️⃣ Query BigQuery
    try:
        results = client.query(sql).result()
        rows = [dict(row) for row in results]
    except Exception as e:
        return f"⚠️ Error running BigQuery vector search: {e}"

    # 4️⃣ Format output
    if not rows:
        return "No semantically similar reports found in the database."

    summary = f"🔍 Top {len(rows)} semantically similar reports:\n"
    for r in rows:
        city, state = r.get("city") or "Unknown", r.get("state") or ""
        desc = (r.get("description") or "").replace("\n", " ")
        summary += (
            f"- {r['timestamp']} | {city}, {state} "
            f"({r.get('severity','N/A')}): {desc[:140]}...\n"
        )

    if len(rows) == top_k:
        summary += f"⚙️ Showing top {top_k} most similar reports.\n"
    return summary
