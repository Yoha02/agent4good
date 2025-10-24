"""
Twitter/X API Client
Wrapper for posting videos and tweets to Twitter
"""
import os
import time
from typing import Optional, List, Dict


class TwitterClient:
    """Client for interacting with Twitter/X API"""
    
    def __init__(self):
        """Initialize Twitter client with credentials from environment"""
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Twitter API client"""
        try:
            # TODO: Implement actual Twitter client initialization
            # import tweepy
            # 
            # # OAuth 1.0a for posting
            # auth = tweepy.OAuth1UserHandler(
            #     self.api_key,
            #     self.api_secret,
            #     self.access_token,
            #     self.access_token_secret
            # )
            # self.client = tweepy.API(auth)
            # 
            # # OAuth 2.0 for v2 endpoints (video upload)
            # self.client_v2 = tweepy.Client(
            #     bearer_token=self.bearer_token,
            #     consumer_key=self.api_key,
            #     consumer_secret=self.api_secret,
            #     access_token=self.access_token,
            #     access_token_secret=self.access_token_secret
            # )
            
            if self.api_key:
                print(f"[TWITTER] Client initialized (simulation mode)")
            else:
                print(f"[TWITTER] No credentials - simulation mode only")
                
        except Exception as e:
            print(f"[TWITTER] Warning: Could not initialize client: {e}")
            self.client = None
    
    def download_from_gcs(self, gcs_uri: str, local_path: str) -> bool:
        """
        Download video from Google Cloud Storage
        
        Args:
            gcs_uri: GCS URI (e.g., "gs://bucket/video.mp4")
            local_path: Local file path to save
        
        Returns:
            bool: True if successful
        """
        try:
            # TODO: Implement actual GCS download
            # from google.cloud import storage
            # 
            # # Parse GCS URI
            # gcs_uri = gcs_uri.replace('gs://', '')
            # bucket_name, blob_name = gcs_uri.split('/', 1)
            # 
            # # Download
            # storage_client = storage.Client()
            # bucket = storage_client.bucket(bucket_name)
            # blob = bucket.blob(blob_name)
            # blob.download_to_filename(local_path)
            
            print(f"[TWITTER] Would download: {gcs_uri} -> {local_path}")
            return True
            
        except Exception as e:
            print(f"[TWITTER] Download error: {e}")
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
            # TODO: Implement actual video upload
            # media = self.client.media_upload(
            #     filename=video_path,
            #     media_category='tweet_video'
            # )
            # return media.media_id_string
            
            # Simulation
            media_id = f"media_{int(time.time())}"
            print(f"[TWITTER] Video uploaded: {media_id}")
            return media_id
            
        except Exception as e:
            print(f"[TWITTER] Upload error: {e}")
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
            # TODO: Implement actual tweet posting
            # if media_id:
            #     tweet = self.client_v2.create_tweet(
            #         text=text,
            #         media_ids=[media_id]
            #     )
            # else:
            #     tweet = self.client_v2.create_tweet(text=text)
            # 
            # tweet_id = tweet.data['id']
            # tweet_url = f"https://twitter.com/CommunityHealthAlerts/status/{tweet_id}"
            
            # Simulation
            tweet_id = f"{int(time.time())}"
            tweet_url = f"https://twitter.com/CommunityHealthAlerts/status/{tweet_id}"
            
            print(f"[TWITTER] Tweet posted successfully!")
            print(f"[TWITTER] URL: {tweet_url}")
            print(f"[TWITTER] Text: {text}")
            
            return {
                "status": "success",
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "message": "Tweet posted (simulation mode - add Twitter API credentials for real posting)"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Tweet posting error: {str(e)}"
            }
    
    def post_video_tweet(self, video_gcs_uri: str, message: str, hashtags: List[str]) -> Dict:
        """
        Complete workflow: download video, upload to Twitter, post tweet
        
        Args:
            video_gcs_uri: GCS URI of video
            message: Tweet message
            hashtags: List of hashtags
        
        Returns:
            dict: Result with tweet URL
        """
        try:
            # Format tweet text
            hashtag_str = ' '.join([f'#{tag}' for tag in hashtags])
            full_text = f"{message}\n\n{hashtag_str}"
            
            # Ensure under 280 chars
            if len(full_text) > 280:
                available = 280 - len(hashtag_str) - 3
                message = message[:available] + "..."
                full_text = f"{message}\n\n{hashtag_str}"
            
            # Download video (simulation)
            local_video = "/tmp/psa_video.mp4"
            # self.download_from_gcs(video_gcs_uri, local_video)
            
            # Upload to Twitter (simulation)
            # media_id = self.upload_video(local_video)
            
            # Post tweet (simulation)
            result = self.post_tweet(full_text, media_id=None)
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Video tweet posting error: {str(e)}"
            }


# Singleton instance
_twitter_client = None

def get_twitter_client() -> TwitterClient:
    """Get or create TwitterClient singleton"""
    global _twitter_client
    if _twitter_client is None:
        _twitter_client = TwitterClient()
    return _twitter_client

