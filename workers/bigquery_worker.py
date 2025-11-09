"""
BigQuery Worker for Cloud Run
Consumes messages from community-reports-submitted topic
Inserts reports into BigQuery (same table as current direct insert)
"""
import os
import sys
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from google.cloud import pubsub_v1, bigquery
from concurrent import futures
import signal
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configuration - EXACTLY matches current app_local.py configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-4a7d408c735c')
SUBSCRIPTION_NAME = os.getenv('SUBSCRIPTION_NAME', 'bigquery-writer-sub')
DATASET_ID = os.getenv('BIGQUERY_DATASET', 'CrowdsourceData')
TABLE_ID = os.getenv('BIGQUERY_TABLE_REPORTS', 'CrowdSourceData')

# Global clients
subscriber = None
bigquery_client = None
subscription_path = None
health_status = {"healthy": False, "messages_processed": 0}

# Simple HTTP health check server for Cloud Run
class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health checks"""
    
    def log_message(self, format, *args):
        """Suppress HTTP logs"""
        pass
    
    def do_GET(self):
        """Respond to GET requests"""
        if self.path in ['/', '/health', '/healthz']:
            if health_status["healthy"]:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = json.dumps({
                    "status": "healthy",
                    "messages_processed": health_status["messages_processed"]
                })
                self.wfile.write(response.encode())
            else:
                self.send_response(503)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"initializing"}')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_server():
    """Start HTTP health check server in background thread"""
    port = int(os.getenv('PORT', '8080'))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"[HEALTH] Starting health check server on port {port}")
    server.serve_forever()

def initialize_clients():
    """Initialize Pub/Sub subscriber and BigQuery client"""
    global subscriber, bigquery_client, subscription_path
    
    try:
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
        logger.info(f"[INIT] Subscriber initialized: {subscription_path}")
        
        bigquery_client = bigquery.Client(project=PROJECT_ID)
        logger.info(f"[INIT] BigQuery client initialized: {PROJECT_ID}")
        
        return True
        
    except Exception as e:
        logger.error(f"[INIT] Failed to initialize clients: {e}")
        return False

def insert_to_bigquery(report_data: dict) -> bool:
    """
    Insert report data to BigQuery
    Uses EXACT same method as current app_local.py direct insert
    
    Args:
        report_data: Report dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Same table reference as app_local.py line 2267
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        
        # Same insert method as app_local.py line 2270
        errors = bigquery_client.insert_rows_json(table_ref, [report_data])
        
        if errors:
            logger.error(f"[BIGQUERY] Insert errors: {errors}")
            return False
        
        logger.info(f"[BIGQUERY] Successfully inserted report {report_data['report_id']} into {table_ref}")
        return True
        
    except Exception as e:
        logger.error(f"[BIGQUERY] Insert failed: {e}", exc_info=True)
        return False

def process_message(message: pubsub_v1.subscriber.message.Message):
    """
    Process a single Pub/Sub message
    
    Args:
        message: Pub/Sub message object
    """
    start_time = time.time()
    report_id = None
    
    try:
        # Parse message data
        message_data = message.data.decode('utf-8')
        report_data = json.loads(message_data)
        report_id = report_data.get('report_id', 'unknown')
        
        logger.info(f"[WORKER] Processing report {report_id}")
        
        # Insert to BigQuery (same as app_local.py)
        success = insert_to_bigquery(report_data)
        
        if success:
            # Acknowledge message (will not be redelivered)
            message.ack()
            
            # Update health status
            health_status["messages_processed"] += 1
            
            elapsed = time.time() - start_time
            logger.info(f"[SUCCESS] Report {report_id} processed in {elapsed:.2f}s")
        else:
            # Nack message (will be redelivered)
            message.nack()
            logger.warning(f"[RETRY] Report {report_id} will be retried")
            
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] Invalid JSON in message: {e}")
        # Ack invalid messages to avoid infinite retry
        message.ack()
        
    except Exception as e:
        logger.error(f"[ERROR] Processing failed for {report_id}: {e}", exc_info=True)
        # Nack to retry
        message.nack()

def main():
    """Main worker loop"""
    logger.info("[WORKER] Starting BigQuery Worker")
    logger.info(f"[WORKER] Target: {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")
    
    # Start health check server in background thread
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Initialize clients
    if not initialize_clients():
        logger.error("[WORKER] Failed to initialize, exiting")
        sys.exit(1)
    
    # Mark as healthy
    health_status["healthy"] = True
    logger.info("[WORKER] Worker is healthy and ready")
    
    # Configure flow control
    flow_control = pubsub_v1.types.FlowControl(
        max_messages=10,  # Process 10 messages concurrently
        max_bytes=10 * 1024 * 1024,  # 10 MB
    )
    
    # Start subscriber
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=process_message,
        flow_control=flow_control
    )
    
    logger.info(f"[WORKER] Listening for messages on {subscription_path}")
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info("[WORKER] Received shutdown signal")
        streaming_pull_future.cancel()
        logger.info("[WORKER] Shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep worker running
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        logger.info("[WORKER] Interrupted by user")
        streaming_pull_future.cancel()
    except Exception as e:
        logger.error(f"[WORKER] Error: {e}", exc_info=True)
        streaming_pull_future.cancel()

if __name__ == '__main__':
    main()

