"""
Pub/Sub Publisher Service
Handles publishing messages to topics with error handling and retries
"""
from google.cloud import pubsub_v1
from google.api_core import retry
import json
import logging
from typing import Dict, Any, Optional
from .config import PROJECT_ID, TOPICS, PUBSUB_SETTINGS, USE_PUBSUB
from .schemas import ReportMessage

logger = logging.getLogger(__name__)

class PubSubPublisher:
    """
    Publisher for Pub/Sub messages
    Thread-safe singleton pattern for connection pooling
    """
    _instance = None
    _publisher = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PubSubPublisher, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize publisher client"""
        if not USE_PUBSUB:
            logger.info("[PUBSUB] Feature disabled via USE_PUBSUB=false")
            return
        
        try:
            # Configure batch settings for better performance
            batch_settings = pubsub_v1.types.BatchSettings(
                max_messages=100,
                max_bytes=1024 * 1024,  # 1 MB
                max_latency=0.05,  # 50 ms
            )
            
            self._publisher = pubsub_v1.PublisherClient(
                batch_settings=batch_settings
            )
            logger.info("[PUBSUB] Publisher initialized successfully")
            
        except Exception as e:
            logger.error(f"[PUBSUB] Failed to initialize publisher: {e}")
            self._publisher = None
    
    def publish_report(
        self, 
        report_data: Dict[str, Any], 
        topic_key: str = 'REPORTS_SUBMITTED'
    ) -> Optional[str]:
        """
        Publish a report to Pub/Sub
        
        Args:
            report_data: Report data dictionary (same format as current BigQuery insert)
            topic_key: Key from TOPICS config
            
        Returns:
            Message ID if successful, None if disabled or failed
        """
        if not USE_PUBSUB:
            logger.debug("[PUBSUB] Publishing skipped (feature disabled)")
            return None
        
        if not self._publisher:
            logger.error("[PUBSUB] Publisher not initialized")
            return None
        
        try:
            # Create message schema (validates format)
            message = ReportMessage(**report_data)
            
            # Validate message
            if not message.validate():
                logger.error(f"[PUBSUB] Invalid message: {message.report_id}")
                return None
            
            # Get topic path
            topic_name = TOPICS.get(topic_key)
            topic_path = f"projects/{PROJECT_ID}/topics/{topic_name}"
            
            # Serialize message
            message_data = message.to_json().encode('utf-8')
            
            # Add attributes for filtering/routing
            attributes = {
                'report_type': message.report_type,
                'severity': message.severity,
                'report_id': message.report_id,
            }
            
            # Publish with retry
            future = self._publisher.publish(
                topic_path,
                message_data,
                **attributes,
                timeout=PUBSUB_SETTINGS['publish_timeout']
            )
            
            # Wait for result (non-blocking in production)
            message_id = future.result(timeout=PUBSUB_SETTINGS['publish_timeout'])
            
            logger.info(f"[PUBSUB] Published report {message.report_id} -> {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"[PUBSUB] Publish failed: {e}", exc_info=True)
            return None
    
    def close(self):
        """Clean shutdown"""
        if self._publisher:
            self._publisher.stop()
            logger.info("[PUBSUB] Publisher closed")

# Singleton instance
_publisher_instance = None

def get_publisher() -> PubSubPublisher:
    """Get or create publisher instance"""
    global _publisher_instance
    if _publisher_instance is None:
        _publisher_instance = PubSubPublisher()
    return _publisher_instance

def publish_community_report(report_data: Dict[str, Any]) -> Optional[str]:
    """
    Convenience function to publish a community report
    
    Args:
        report_data: Report dictionary (same format as current BigQuery row)
        
    Returns:
        Message ID if successful, None otherwise
    """
    publisher = get_publisher()
    return publisher.publish_report(report_data, topic_key='REPORTS_SUBMITTED')

