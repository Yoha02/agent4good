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
        self.gcs_bucket = os.getenv('GCS_VIDEO_BUCKET', 'qwiklabs-gcp-00-4a7d408c735c-psa-videos')
        self.gcs_prefix = os.getenv('GCS_VIDEO_PREFIX', 'psa-videos/')
        
        # Will be initialized when actually implementing
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Veo 3 client - Uses Google AI API (proven to work!)"""
        try:
            from google import genai
            
            # Use Google AI API mode (uses API key - works in all environments)
            self.client = genai.Client()  # Uses GOOGLE_API_KEY from environment
            self.client_mode = "google_ai"
            print(f"[VEO3] Client initialized with Google AI API")
            print(f"[VEO3] Mode: {self.client_mode}")
            print(f"[VEO3] Project: {self.project_id}, Location: {self.location}")
            
        except Exception as e:
            print(f"[VEO3] Warning: Could not initialize client: {e}")
            print(f"[VEO3] Falling back to simulation mode")
            self.client = None
            self.client_mode = "simulation"
    
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
            
            # Call Veo 3.0 Fast (rate limit available!)
            from google.genai import types
            
            print(f"[VEO3] Calling Veo 2.0 API (switching due to rate limits)...")
            print(f"[VEO3] Prompt length: {len(prompt)} characters")
            
            # Use Veo 2.0 model - different rate limits
            operation = self.client.models.generate_videos(
                model="veo-2.0-generate-001",
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",
                    number_of_videos=1,
                    duration_seconds=8,
                    resolution="720p",
                ),
            )
            
            print(f"[VEO3] Video generation started!")
            print(f"[VEO3] Operation: {operation.name}")
            
            # Store the operation object itself, not just the name
            # We'll need to poll it later
            self._current_operation = operation
            self._current_output_uri = output_gcs_uri
            
            return {
                "operation": operation,  # Return the operation object for polling
                "operation_id": operation.name,
                "status": "processing",
                "output_gcs_uri": output_gcs_uri if self.client_mode == "vertex_ai" else None,
                "estimated_seconds": 90,
                "message": "Video generation in progress",
                "note": "Poll this operation with check_operation_status()"
            }
            
        except Exception as e:
            print(f"[VEO3] Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "error_message": f"Veo 3 generation error: {str(e)}"
            }
    
    def check_operation_status(self, operation_or_id) -> Dict:
        """
        Check status of video generation operation
        
        Args:
            operation_or_id: Either the operation object or operation ID string
        
        Returns:
            dict: {
                "status": "processing" | "complete" | "error",
                "progress": 0-100,
                "video_uri": "gs://..." or video bytes (if complete)
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
            
            # If we have a string ID, try to get the operation
            if isinstance(operation_or_id, str):
                # Use stored operation if checking same one
                if hasattr(self, '_current_operation') and self._current_operation.name == operation_or_id:
                    operation = self._current_operation
                    # Refresh the operation status
                    operation = self.client.operations.get(operation)
                else:
                    print(f"[VEO3] Getting operation by ID: {operation_or_id}")
                    operation = self.client.operations.get(operation_or_id)
            else:
                # Already an operation object, refresh it
                operation = self.client.operations.get(operation_or_id)
            
            if operation.done:
                # Operation completed
                if operation.error:
                    print(f"[VEO3] Generation failed: {operation.error.message}")
                    return {
                        "status": "error",
                        "error_message": operation.error.message
                    }
                
                # Success - extract video
                generated_video = operation.result.generated_videos[0].video
                
                # Get video URI (Google AI API always returns URI)
                if hasattr(generated_video, 'uri') and generated_video.uri:
                    video_uri = generated_video.uri
                    print(f"[VEO3] Video generation complete!")
                    print(f"[VEO3] Video URI: {video_uri}")
                    
                    # AUTOMATIC WORKFLOW: Download and upload to GCS
                    api_key = os.getenv('GOOGLE_API_KEY')
                    if api_key:
                        print(f"[VEO3] Starting automatic download and GCS upload...")
                        
                        # Download video
                        video_bytes = self.download_video_from_uri(video_uri, api_key)
                        
                        if video_bytes:
                            # Upload to GCS
                            gcs_result = self.upload_to_gcs(video_bytes)
                            
                            if gcs_result['status'] == 'success':
                                # Return GCS URL (ready for UI and Twitter!)
                                return {
                                    "status": "complete",
                                    "video_url": gcs_result['public_url'],  # For UI embedding
                                    "gcs_uri": gcs_result['gcs_uri'],       # For Twitter upload
                                    "video_size": gcs_result['video_size'],
                                    "original_uri": video_uri,
                                    "progress": 100,
                                    "message": "Video ready and uploaded to GCS"
                                }
                    
                    # Fallback if download/upload fails
                    return {
                        "status": "complete",
                        "video_uri": video_uri,
                        "progress": 100,
                        "note": "Video generated but not uploaded to GCS"
                    }
                    
                elif hasattr(generated_video, 'video_bytes') and generated_video.video_bytes:
                    # Unlikely with Google AI API, but handle it
                    video_data = generated_video.video_bytes
                    gcs_result = self.upload_to_gcs(video_data)
                    
                    return {
                        "status": "complete",
                        "video_url": gcs_result['public_url'],
                        "gcs_uri": gcs_result['gcs_uri'],
                        "video_size": len(video_data),
                        "progress": 100
                    }
                else:
                    print(f"[VEO3] Video complete but no URI or bytes found")
                    return {
                        "status": "error",
                        "error_message": "Video generated but format unknown"
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
    
    def download_video_from_uri(self, video_uri: str, api_key: str) -> bytes:
        """
        Download video from Google's URI using API key
        
        Args:
            video_uri: URI like https://generativelanguage.googleapis.com/v1beta/files/...
            api_key: Your Google API key
        
        Returns:
            bytes: Video data
        """
        try:
            import requests
            
            headers = {'X-goog-api-key': api_key}
            response = requests.get(video_uri, headers=headers)
            
            if response.status_code == 200:
                print(f"[VEO3] Video downloaded: {len(response.content):,} bytes")
                return response.content
            else:
                print(f"[VEO3] Download failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[VEO3] Download error: {e}")
            return None
    
    def upload_to_gcs(self, video_bytes: bytes, filename: str = None) -> dict:
        """
        Upload video bytes to GCS bucket
        
        Args:
            video_bytes: Video data as bytes
            filename: Optional custom filename
        
        Returns:
            dict with gcs_uri and public_url
        """
        try:
            from google.cloud import storage
            import time
            
            storage_client = storage.Client()
            bucket = storage_client.bucket(self.gcs_bucket)
            
            if not filename:
                filename = f"{self.gcs_prefix}psa-{int(time.time())}.mp4"
            
            blob = bucket.blob(filename)
            blob.upload_from_string(video_bytes, content_type='video/mp4')
            blob.make_public()
            
            gcs_uri = f"gs://{self.gcs_bucket}/{filename}"
            public_url = blob.public_url
            
            print(f"[VEO3] Uploaded to GCS: {gcs_uri}")
            print(f"[VEO3] Public URL: {public_url}")
            
            return {
                "status": "success",
                "gcs_uri": gcs_uri,
                "public_url": public_url,
                "video_size": len(video_bytes)
            }
            
        except Exception as e:
            print(f"[VEO3] Upload error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }


# Singleton instance
_veo3_client = None

def get_veo3_client() -> Veo3Client:
    """Get or create Veo3Client singleton"""
    global _veo3_client
    if _veo3_client is None:
        _veo3_client = Veo3Client()
    return _veo3_client

