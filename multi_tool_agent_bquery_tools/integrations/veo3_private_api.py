"""
Veo 3 Private API Client - Using Vertex AI REST API directly
This bypasses the SDK and uses the private API which returns video bytes
"""
import os
import requests
import subprocess
import base64
import time
from typing import Dict, Optional


class Veo3PrivateAPIClient:
    """Client using Veo 3 private API (returns video bytes directly)"""
    
    def __init__(self, model="veo-2.0-generate-001"):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.base_url = f"https://{self.location}-aiplatform.googleapis.com/v1"
        self.model = model  # Default to Veo 2 (more widely available)
        
        print(f"[VEO_API] Initialized")
        print(f"[VEO_API] Project: {self.project_id}")
        print(f"[VEO_API] Model: {self.model}")
    
    def get_access_token(self) -> str:
        """Get access token using google.auth"""
        try:
            import google.auth
            import google.auth.transport.requests
            
            # Get default credentials
            credentials, project = google.auth.default()
            
            # Refresh to get access token
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            
            return credentials.token
        except Exception as e:
            print(f"[VEO_API] Error getting token: {e}")
            return None
    
    def generate_video(self, prompt: str, resolution: str = "720p") -> Dict:
        """
        Generate video using private Vertex AI API
        Returns video as base64 bytes directly (no GCS needed!)
        
        Args:
            prompt: Text description of video
            resolution: "720p" or "1080p"
        
        Returns:
            dict with operation_name for polling
        """
        try:
            token = self.get_access_token()
            if not token:
                return {"status": "error", "error_message": "Could not get access token"}
            
            url = f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model}:predictLongRunning"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # NO storageUri = video bytes returned directly!
            payload = {
                "instances": [
                    {
                        "prompt": prompt
                    }
                ],
                "parameters": {
                    "sampleCount": 1,
                    "resolution": resolution
                }
            }
            
            print(f"[VEO_API] Calling Veo 3 private API...")
            print(f"[VEO_API] Prompt: {len(prompt)} chars")
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                operation_name = result.get('name')
                print(f"[VEO_API] Video generation started!")
                print(f"[VEO_API] Operation: {operation_name}")
                
                return {
                    "status": "processing",
                    "operation_name": operation_name,
                    "message": "Video generation started (private API)"
                }
            else:
                print(f"[VEO_API] Error: {response.status_code}")
                print(f"[VEO_API] Response: {response.text}")
                return {
                    "status": "error",
                    "error_message": f"API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            print(f"[VEO_API] Exception: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def check_status(self, operation_name: str) -> Dict:
        """
        Check video generation status and get video bytes when done
        
        Returns:
            dict with status, and video_bytes (base64) when complete
        """
        try:
            token = self.get_access_token()
            if not token:
                return {"status": "error", "error_message": "Could not get access token"}
            
            url = f"{self.base_url}/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model}:fetchPredictOperation"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "operationName": operation_name
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('done'):
                    # Video is ready!
                    if 'response' in result and 'videos' in result['response']:
                        # Get video data
                        video = result['response']['videos'][0]
                        
                        # Check if we have gcsUri or bytesBase64Encoded
                        if 'gcsUri' in video:
                            print(f"[VEO_API] Video at: {video['gcsUri']}")
                            return {
                                "status": "complete",
                                "video_uri": video['gcsUri'],
                                "mime_type": video.get('mimeType', 'video/mp4')
                            }
                        elif 'bytesBase64Encoded' in video:
                            # Decode base64 video
                            video_b64 = video['bytesBase64Encoded']
                            video_bytes = base64.b64decode(video_b64)
                            print(f"[VEO_API] Video bytes received: {len(video_bytes):,} bytes")
                            
                            return {
                                "status": "complete",
                                "video_bytes": video_bytes,
                                "video_size": len(video_bytes),
                                "mime_type": video.get('mimeType', 'video/mp4')
                            }
                    
                    # Done but no video?
                    if 'error' in result:
                        return {
                            "status": "error",
                            "error_message": result['error'].get('message', 'Unknown error')
                        }
                else:
                    # Still processing
                    return {
                        "status": "processing",
                        "progress": 50
                    }
            else:
                return {
                    "status": "error",
                    "error_message": f"Status check failed: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }


# Singleton
_veo3_private_client = None

def get_veo3_private_client() -> Veo3PrivateAPIClient:
    global _veo3_private_client
    if _veo3_private_client is None:
        _veo3_private_client = Veo3PrivateAPIClient()
    return _veo3_private_client

