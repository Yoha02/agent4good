"""
Check GCS bucket contents and show how to access images
"""
from google.cloud import storage
import os
from dotenv import load_dotenv

load_dotenv()

GCS_BUCKET_NAME = 'agent4good-report-attachments'
GCP_PROJECT_ID = 'qwiklabs-gcp-00-4a7d408c735c'

try:
    # Initialize GCS client
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    bucket = storage_client.get_bucket(GCS_BUCKET_NAME)
    
    print("=" * 80)
    print(f"GCS BUCKET: {GCS_BUCKET_NAME}")
    print("=" * 80)
    print(f"Project: {GCP_PROJECT_ID}")
    print(f"Bucket URL: https://console.cloud.google.com/storage/browser/{GCS_BUCKET_NAME}")
    print(f"Location: {bucket.location}")
    print(f"Storage Class: {bucket.storage_class}")
    print("\n" + "=" * 80)
    print("BUCKET CONTENTS:")
    print("=" * 80)
    
    # List all blobs in bucket
    blobs = list(bucket.list_blobs())
    
    if not blobs:
        print("\n  ⚠️  Bucket is empty - no files uploaded yet")
        print("\n  To upload files, submit a report through the form at:")
        print("  http://localhost:8080")
    else:
        print(f"\n  Total files: {len(blobs)}\n")
        for blob in blobs:
            print(f"  📁 {blob.name}")
            print(f"     Size: {blob.size} bytes")
            print(f"     Content Type: {blob.content_type}")
            print(f"     Public URL: {blob.public_url}")
            print(f"     Created: {blob.time_created}")
            print()
    
    print("=" * 80)
    print("HOW TO ACCESS IMAGES:")
    print("=" * 80)
    print("\n1. Via Google Cloud Console:")
    print(f"   https://console.cloud.google.com/storage/browser/{GCS_BUCKET_NAME}")
    print("\n2. Via Public URL (if blob is public):")
    print(f"   https://storage.googleapis.com/{GCS_BUCKET_NAME}/reports/REPORT_ID/filename.jpg")
    print("\n3. Via Signed URL (temporary access):")
    print("   Generated programmatically with expiration time")
    
except Exception as e:
    print(f"[ERROR] {e}")
    print("\nMake sure:")
    print("  1. You have access to the GCP project")
    print("  2. GCS API is enabled")
    print("  3. Service account has Storage Object Viewer role")
