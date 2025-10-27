"""
Twitter/X API Client
Wrapper for posting videos and tweets to Twitter

Requires: pip install tweepy google-cloud-storage requests
"""
import os
import time
import tempfile
import requests
from typing import Optional, List, Dict

# Try to import tweepy (will work in simulation mode without it)
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    print("[TWITTER] tweepy not installed. Install with: pip install tweepy")

# Try to import Google Cloud Storage
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("[TWITTER] google-cloud-storage not installed. Using public URL download instead.")


class TwitterClient:
    """Client for interacting with Twitter/X API"""
    
    def __init__(self):
        """Initialize Twitter client with credentials from environment"""
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        # Determine mode
        self.has_credentials = all([
            self.api_key, 
            self.api_secret, 
            self.access_token, 
            self.access_token_secret
        ])
        
        self.simulation_mode = not (self.has_credentials and TWEEPY_AVAILABLE)
        
        self.client = None
        self.client_v2 = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Twitter API client"""
        try:
            if not TWEEPY_AVAILABLE:
                print(f"[TWITTER] Running in simulation mode (tweepy not available)")
                return
            
            if not self.has_credentials:
                print(f"[TWITTER] Running in simulation mode (no credentials)")
                return
            
            # OAuth 1.0a for media upload (required for video)
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            self.client = tweepy.API(auth, wait_on_rate_limit=True)
            
            # OAuth 2.0 Client for v2 endpoints (tweet creation)
            self.client_v2 = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            print(f"[TWITTER] SUCCESS: Client initialized successfully!")
            print(f"[TWITTER] Ready to post tweets with videos")
                
        except Exception as e:
            print(f"[TWITTER] Warning: Could not initialize client: {e}")
            print(f"[TWITTER] Falling back to simulation mode")
            self.client = None
            self.client_v2 = None
            self.simulation_mode = True
    
    def download_video(self, video_url: str, local_path: str) -> bool:
        """
        Download video from public URL or GCS
        
        Args:
            video_url: Public URL (https://) or GCS URI (gs://)
            local_path: Local file path to save
        
        Returns:
            bool: True if successful
        """
        try:
            # If it's a public HTTPS URL, download directly
            if video_url.startswith('http'):
                print(f"[TWITTER] Downloading from public URL: {video_url[:50]}...")
                response = requests.get(video_url, stream=True, timeout=60)
                response.raise_for_status()
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"[TWITTER] SUCCESS: Downloaded to: {local_path}")
                return True
            
            # If it's a GCS URI and we have GCS library
            elif video_url.startswith('gs://') and GCS_AVAILABLE:
                print(f"[TWITTER] Downloading from GCS: {video_url}")
                
                # Parse GCS URI
                gcs_path = video_url.replace('gs://', '')
                bucket_name, blob_name = gcs_path.split('/', 1)
                
                # Download
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.download_to_filename(local_path)
                
                print(f"[TWITTER] SUCCESS: Downloaded from GCS to: {local_path}")
                return True
            
            else:
                print(f"[TWITTER] ERROR: Unsupported URL format: {video_url}")
                return False
            
        except Exception as e:
            print(f"[TWITTER] ERROR: Download error: {e}")
            return False
    
    def upload_video(self, video_path: str) -> Optional[str]:
        """
        Upload video to Twitter
        
        Args:
            video_path: Local path to video file
        
        Returns:
            str: Media ID for the uploaded video, or None if failed
        """
        try:
            if self.simulation_mode:
                # Simulation mode
                media_id = f"media_{int(time.time())}"
                print(f"[TWITTER] [SIMULATION] Video uploaded with ID: {media_id}")
                return media_id
            
            # Real upload using tweepy
            print(f"[TWITTER] Uploading video: {video_path}")
            
            # Check file size
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"[TWITTER] Video size: {file_size_mb:.2f} MB")
            
            # Twitter video limits: 512MB max, 140 seconds max
            if file_size_mb > 512:
                print(f"[TWITTER] ERROR: Video too large: {file_size_mb:.2f} MB (max 512 MB)")
                return None
            
            # Upload video with chunked upload (required for videos)
            media = self.client.media_upload(
                filename=video_path,
                media_category='tweet_video',
                chunked=True
            )
            
            media_id = media.media_id_string
            print(f"[TWITTER] SUCCESS: Video uploaded successfully! Media ID: {media_id}")
            
            # Wait for processing (Twitter needs to process video)
            print(f"[TWITTER] Waiting for Twitter to process video...")
            processing_info = media.processing_info
            
            while processing_info and processing_info.get('state') == 'pending':
                check_after_secs = processing_info.get('check_after_secs', 5)
                print(f"[TWITTER] Processing... checking again in {check_after_secs}s")
                time.sleep(check_after_secs)
                
                # Refresh processing status
                media = self.client.get_media_upload_status(media_id)
                processing_info = media.processing_info
            
            if processing_info and processing_info.get('state') == 'failed':
                error = processing_info.get('error', {})
                print(f"[TWITTER] ERROR: Video processing failed: {error}")
                return None
            
            print(f"[TWITTER] SUCCESS: Video processed and ready to tweet!")
            return media_id
            
        except Exception as e:
            print(f"[TWITTER] ERROR: Upload error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def post_tweet(self, text: str, media_id: Optional[str] = None) -> Dict:
        """
        Post a tweet with optional media
        
        Args:
            text: Tweet text
            media_id: Optional media ID from upload_video
        
        Returns:
            dict: {
                "status": "success" | "error",
                "tweet_id": str,
                "tweet_url": str
            }
        """
        try:
            if self.simulation_mode:
                # Simulation mode
                tweet_id = f"{int(time.time())}"
                tweet_url = f"https://twitter.com/CommunityHealthAlerts/status/{tweet_id}"
                
                print(f"[TWITTER] [SIMULATION] Tweet posted!")
                print(f"[TWITTER] URL: {tweet_url}")
                print(f"[TWITTER] Text: {text[:100]}...")
                if media_id:
                    print(f"[TWITTER] With video: {media_id}")
                
                return {
                    "status": "success",
                    "tweet_id": tweet_id,
                    "tweet_url": tweet_url,
                    "message": "Tweet posted in simulation mode (add Twitter API credentials for real posting)"
                }
            
            # Real tweet posting
            print(f"[TWITTER] Posting tweet...")
            print(f"[TWITTER] Text ({len(text)} chars): {text[:100]}...")
            
            if media_id:
                print(f"[TWITTER] With media ID: {media_id}")
                tweet_response = self.client_v2.create_tweet(
                    text=text,
                    media_ids=[media_id]
                )
            else:
                tweet_response = self.client_v2.create_tweet(text=text)
            
            tweet_id = tweet_response.data['id']
            
            # Get username from API (or use environment variable)
            twitter_username = os.getenv('TWITTER_USERNAME', 'CommunityHealthAlerts')
            tweet_url = f"https://twitter.com/{twitter_username}/status/{tweet_id}"
            
            print(f"[TWITTER] SUCCESS: Tweet posted successfully!")
            print(f"[TWITTER] URL: {tweet_url}")
            
            return {
                "status": "success",
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "message": "Tweet posted successfully!"
            }
            
        except Exception as e:
            print(f"[TWITTER] ERROR: Tweet posting error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_message": f"Tweet posting error: {str(e)}"
            }
    
    def post_video_tweet(self, video_url: str, message: str, hashtags: List[str] = None) -> Dict:
        """
        Complete workflow: download video, upload to Twitter, post tweet
        
        Args:
            video_url: Public URL or GCS URI of video
            message: Tweet message
            hashtags: List of hashtags (optional)
        
        Returns:
            dict: Result with tweet URL
        """
        temp_file = None
        try:
            print(f"\n[TWITTER] ===== Starting Video Tweet Workflow =====")
            
            # Format tweet text
            if hashtags:
                hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
                full_text = f"{message}\n\n{hashtag_str}"
            else:
                full_text = message
            
            # Ensure under 280 chars
            if len(full_text) > 280:
                if hashtags:
                    hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
                    available = 280 - len(hashtag_str) - 4  # Account for "\n\n" and "..."
                    message = message[:available] + "..."
                    full_text = f"{message}\n\n{hashtag_str}"
                else:
                    full_text = message[:277] + "..."
            
            print(f"[TWITTER] Tweet text ({len(full_text)} chars): {full_text[:100]}...")
            
            # Download video to temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                temp_file = tmp.name
            
            print(f"[TWITTER] Downloading video to: {temp_file}")
            download_success = self.download_video(video_url, temp_file)
            
            if not download_success:
                return {
                    "status": "error",
                    "error_message": "Failed to download video"
                }
            
            # Upload to Twitter with retry logic
            max_retries = 3
            retry_delay = 30  # Start with 30 seconds
            media_id = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    print(f"[TWITTER] Upload attempt {attempt + 1}/{max_retries}")
                    media_id = self.upload_video(temp_file)
                    
                    if media_id:
                        print(f"[TWITTER] Upload successful on attempt {attempt + 1}")
                        break  # Success!
                    
                    # If upload returns None (failure), retry
                    last_error = "Upload returned None"
                    if attempt < max_retries - 1:
                        print(f"[TWITTER] Upload failed, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        
                except Exception as e:
                    last_error = str(e)
                    error_str = str(e).lower()
                    
                    # Check if it's a connection error (rate limit or network issue)
                    if 'connection' in error_str or 'reset' in error_str or 'aborted' in error_str:
                        if attempt < max_retries - 1:
                            print(f"[TWITTER] Connection error on attempt {attempt + 1}, retrying in {retry_delay}s...")
                            print(f"[TWITTER] Error: {str(e)[:100]}")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff (30s, 60s, 120s)
                        else:
                            print(f"[TWITTER] Connection error after {max_retries} attempts")
                            raise
                    else:
                        # For other errors, raise immediately
                        raise
            
            if not media_id:
                return {
                    "status": "error",
                    "error_message": f"Failed to upload video to Twitter after {max_retries} attempts: {last_error}"
                }
            
            # Post tweet
            result = self.post_tweet(full_text, media_id=media_id)
            
            print(f"[TWITTER] ===== Workflow Complete =====\n")
            return result
            
        except Exception as e:
            print(f"[TWITTER] ERROR: Video tweet posting error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error_message": f"Video tweet posting error: {str(e)}"
            }
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"[TWITTER] Cleaned up temp file: {temp_file}")
                except:
                    pass


# Singleton instance
_twitter_client = None

def get_twitter_client() -> TwitterClient:
    """Get or create TwitterClient singleton"""
    global _twitter_client
    if _twitter_client is None:
        _twitter_client = TwitterClient()
    return _twitter_client

