"""
Message schemas for Pub/Sub
Defines the structure of messages for type safety and validation
Matches the existing BigQuery schema exactly
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import json

@dataclass
class ReportMessage:
    """
    Schema for community report messages
    Matches BigQuery CrowdsourceData.CrowdSourceData table schema
    """
    
    # Required fields
    report_id: str
    report_type: str
    timestamp: str
    description: str
    
    # Location
    address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    county: Optional[str] = None
    
    # Severity & classification
    severity: str = 'moderate'
    specific_type: str = 'unspecified'
    
    # Impact
    people_affected: str = 'unknown'
    timeframe: str = 'unspecified'
    
    # Contact (if not anonymous)
    is_anonymous: bool = True
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Media
    media_urls: Optional[List[str]] = None
    attachment_urls: Optional[str] = None
    media_count: int = 0
    
    # AI analysis (populated later by other services)
    ai_media_summary: Optional[str] = None
    ai_overall_summary: Optional[str] = None
    ai_tags: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_analyzed_at: Optional[str] = None
    
    # Status tracking
    status: str = 'pending'
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    notes: Optional[str] = None
    
    # Moderation
    exclude_from_analysis: bool = False
    exclusion_reason: Optional[str] = None
    manual_tags: Optional[str] = None
    
    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.media_urls is None:
            self.media_urls = []
    
    def to_json(self) -> str:
        """Serialize to JSON string"""
        data = asdict(self)
        return json.dumps(data, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ReportMessage':
        """Deserialize from JSON string"""
        data = json.loads(json_str)
        return cls(**data)
    
    def to_bigquery_row(self) -> Dict[str, Any]:
        """Convert to BigQuery row format (same as current implementation)"""
        return asdict(self)
    
    def validate(self) -> bool:
        """Validate required fields"""
        required = ['report_id', 'report_type', 'timestamp', 'description']
        return all(getattr(self, field) for field in required)

