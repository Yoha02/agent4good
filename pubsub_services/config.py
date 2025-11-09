"""
Pub/Sub configuration
Centralized settings for topics, subscriptions, and retry policies
"""
import os
from typing import Dict, Any

# Project configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-4a7d408c735c')
REGION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

# Feature flag - ONLY affects report submission, nothing else
USE_PUBSUB = os.getenv('USE_PUBSUB', 'false').lower() == 'true'

# Topic configuration
TOPICS = {
    'REPORTS_SUBMITTED': 'community-reports-submitted',
}

# Subscription configuration
SUBSCRIPTIONS = {
    'BIGQUERY_WRITER': 'bigquery-writer-sub',
}

# Retry and timeout settings
PUBSUB_SETTINGS = {
    'publish_timeout': 10.0,  # seconds
    'ack_deadline': 60,       # seconds
    'max_retries': 3,
    'retry_delay': 5,         # seconds
}

def get_topic_path(topic_key: str) -> str:
    """Get fully qualified topic path"""
    topic_name = TOPICS.get(topic_key)
    return f"projects/{PROJECT_ID}/topics/{topic_name}"

def get_subscription_path(sub_key: str) -> str:
    """Get fully qualified subscription path"""
    sub_name = SUBSCRIPTIONS.get(sub_key)
    return f"projects/{PROJECT_ID}/subscriptions/{sub_name}"

