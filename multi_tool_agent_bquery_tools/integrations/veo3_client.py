"""
Veo 3 API Client - Google Video Generation
Wrapper for Google's Veo 3 video generation API
"""
import os
import time
from typing import Optional, Dict


class Veo3Client:
    """Client for interacting with Google Veo 3 API"""
    
    def __init__(self):
        """Initialize Veo 3 client with credentials from environment"""
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.gcs_bucket = os.getenv('GCS_VIDEO_BUCKET', 'psa-videos')
        self.gcs_prefix = os.getenv('GCS_VIDEO_PREFIX', 'videos/')
        
        # Will be initialized when actually implementing
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Veo 3 client"""
        try:
            from google import genai
            
            # Initialize with Vertex AI
            self.client = genai.Client(
                vertexai=True,
                project=self.project_id,
                location=self.location
            )
            print(f"[VEO3] Client initialized successfully")
            print(f"[VEO3] Project: {self.project_id}, Location: {self.location}")
        except Exception as e:
            print(f"[VEO3] Warning: Could not initialize client: {e}")
            print(f"[VEO3] Falling back to simulation mode")
            self.client = None
    
    def generate_video(self, prompt: str, output_filename: Optional[str] = None) -> Dict:
        """
        Generate video using Veo 3 API
        
        Args:
            prompt: The detailed Veo 3 prompt
            output_filename: Optional custom filename (auto-generated if None)
        
        Returns:
            dict: {
                "operation_id": str,
                "status": "processing",
                "output_gcs_uri": "gs://bucket/path/video.mp4"
            }
        """
        try:
            # Generate unique filename if not provided
            if not output_filename:
                timestamp = int(time.time())
                output_filename = f"psa-video-{timestamp}.mp4"
            
            output_gcs_uri = f"gs://{self.gcs_bucket}/{self.gcs_prefix}{output_filename}"
            
            # Check if client is initialized
            if not self.client:
                print(f"[VEO3] Client not available, using simulation mode")
                operation_id = f"projects/{self.project_id}/operations/veo-sim-{int(time.time())}"
                return {
                    "operation_id": operation_id,
                    "status": "processing",
                    "output_gcs_uri": output_gcs_uri,
                    "estimated_seconds": 75,
                    "note": "Simulation mode - Veo 3 client not initialized"
                }
            
            # Call real Veo 3 API
            from google.genai.types import GenerateVideosConfig
            
            print(f"[VEO3] Calling Veo 3 API...")
            print(f"[VEO3] Prompt length: {len(prompt)} characters")
            print(f"[VEO3] Output URI: {output_gcs_uri}")
            
            operation = self.client.models.generate_videos(
                model="veo-3-fast-generate",  # Use fast model for 8-sec videos
                prompt=prompt,
                config=GenerateVideosConfig(
                    aspect_ratio="9:16",  # Vertical for social media (1080x1920)
                    output_gcs_uri=output_gcs_uri,
                ),
            )
            
            print(f"[VEO3] Video generation started!")
            print(f"[VEO3] Operation ID: {operation.name}")
            
            return {
                "operation_id": operation.name,
                "status": "processing",
                "output_gcs_uri": output_gcs_uri,
                "estimated_seconds": 90,  # Veo 3 typically takes 60-120 seconds
                "message": "Video generation in progress"
            }
            
        except Exception as e:
            print(f"[VEO3] Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "error_message": f"Veo 3 generation error: {str(e)}"
            }
    
    def check_operation_status(self, operation_id: str) -> Dict:
        """
        Check status of video generation operation
        
        Args:
            operation_id: The operation ID from generate_video
        
        Returns:
            dict: {
                "status": "processing" | "complete" | "error",
                "progress": 0-100,
                "video_uri": "gs://..." (if complete)
            }
        """
        try:
            if not self.client:
                # Simulation mode
                return {
                    "status": "processing",
                    "progress": 50,
                    "message": "Video generation in progress (simulation)"
                }
            
            # Get operation status from Veo 3
            operation = self.client.operations.get(operation_id)
            
            if operation.done:
                # Operation completed
                if operation.error:
                    print(f"[VEO3] Generation failed: {operation.error.message}")
                    return {
                        "status": "error",
                        "error_message": operation.error.message
                    }
                
                # Success - extract video URI
                video_uri = operation.result.generated_videos[0].video.uri
                print(f"[VEO3] Video generation complete!")
                print(f"[VEO3] Video URI: {video_uri}")
                
                return {
                    "status": "complete",
                    "video_uri": video_uri,
                    "preview_url": self.get_public_url(video_uri),
                    "progress": 100
                }
            else:
                # Still processing - estimate progress
                # Veo 3 typically takes 60-90 seconds
                print(f"[VEO3] Video still generating...")
                return {
                    "status": "processing",
                    "progress": 50,  # Could estimate based on elapsed time
                    "message": "Video generation in progress"
                }
            
        except Exception as e:
            print(f"[VEO3] Status check error: {e}")
            return {
                "status": "error",
                "error_message": f"Status check error: {str(e)}"
            }
    
    def get_public_url(self, gcs_uri: str) -> str:
        """
        Convert GCS URI to public HTTPS URL
        
        Args:
            gcs_uri: GCS URI like "gs://bucket/path/video.mp4"
        
        Returns:
            str: Public HTTPS URL
        """
        # Extract bucket and path from gs:// URI
        if gcs_uri.startswith('gs://'):
            gcs_uri = gcs_uri[5:]  # Remove 'gs://'
            parts = gcs_uri.split('/', 1)
            bucket = parts[0]
            path = parts[1] if len(parts) > 1 else ''
            return f"https://storage.googleapis.com/{bucket}/{path}"
        return gcs_uri


# Singleton instance
_veo3_client = None

def get_veo3_client() -> Veo3Client:
    """Get or create Veo3Client singleton"""
    global _veo3_client
    if _veo3_client is None:
        _veo3_client = Veo3Client()
    return _veo3_client

