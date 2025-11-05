"""
Social Media Tools - Twitter/X Integration
Isolated module for posting health PSAs to social media
"""
from typing import Optional, List, Dict
import os


def post_to_twitter(video_uri: str, message: str, hashtags: Optional[List[str]] = None, location: Optional[str] = None) -> dict:
    """
    Posts video and message to Twitter/X using the real Twitter client.
    
    Args:
        video_uri: GCS URI or public URL of the video (e.g., "gs://bucket/video.mp4" or "https://storage.googleapis.com/...")
        message: Tweet text (action line + context)
        hashtags: List of hashtags (e.g., ["HealthAlert", "AirQuality"])
        location: Location for location-specific hashtags (e.g., "California")
    
    Returns:
        dict: {
            "status": "success" | "error",
            "tweet_url": "https://twitter.com/.../status/...",
            "tweet_id": "1234567890",
            "tweet_text": "Final tweet text with hashtags"
        }
    """
    try:
        # Format hashtags
        if hashtags is None:
            hashtags = ["PublicHealth", "HealthAlert", "CommunityWellness"]
        
        # Add location-specific hashtag
        if location:
            # Convert "California" -> "California" or state abbreviation
            state_abbrevs = {
                'California': 'CA', 'Texas': 'TX', 'New York': 'NY',
                'Florida': 'FL', 'Illinois': 'IL'
            }
            loc_tag = state_abbrevs.get(location, location.replace(' ', ''))
            hashtags.append(loc_tag)
        
        # Convert GCS URI to public URL if needed
        video_url = video_uri
        if video_uri.startswith('gs://'):
            # Convert gs://bucket/path to https://storage.googleapis.com/bucket/path
            gcs_path = video_uri.replace('gs://', '')
            video_url = f"https://storage.googleapis.com/{gcs_path}"
        
        print(f"\n[TWITTER TOOL] ===== Real Twitter Posting =====")
        print(f"[TWITTER TOOL] Video URL: {video_url}")
        print(f"[TWITTER TOOL] Message: {message}")
        print(f"[TWITTER TOOL] Hashtags: {hashtags}")
        
        # Use the real Twitter client
        from multi_tool_agent_bquery_tools.integrations.twitter_client import get_twitter_client
        
        twitter_client = get_twitter_client()
        
        # Post the video tweet
        result = twitter_client.post_video_tweet(
            video_url=video_url,
            message=message,
            hashtags=hashtags
        )
        
        print(f"[TWITTER TOOL] Result: {result}")
        
        if result.get('status') == 'success':
            return {
                "status": "success",
                "tweet_url": result.get('tweet_url'),
                "tweet_id": result.get('tweet_id'),
                "tweet_text": result.get('tweet_text', message),
                "message": result.get('message', 'Tweet posted successfully!')
            }
        else:
            return {
                "status": "error",
                "error_message": result.get('error_message', 'Failed to post tweet')
            }
        
    except Exception as e:
        print(f"[TWITTER TOOL] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error_message": f"Error posting to Twitter: {str(e)}"
        }


def format_health_tweet(action_line: str, location: str, data_type: str, severity: str) -> dict:
    """
    Formats a health alert tweet with proper context and hashtags.
    
    Args:
        action_line: The actionable recommendation
        location: State or county
        data_type: "air_quality", "disease", etc.
        severity: "good", "moderate", "unhealthy", etc.
    
    Returns:
        dict: {
            "message": "Formatted tweet message",
            "hashtags": ["list", "of", "hashtags"],
            "char_count": total characters
        }
    """
    try:
        # Create alert level emoji/indicator (for message, not video)
        alert_indicators = {
            "good": "ℹ️",
            "moderate": "⚠️",
            "unhealthy": "🚨",
            "very unhealthy": "🚨",
            "hazardous": "🔴"
        }
        
        # Note: Don't use emojis in actual action line (per spec)
        # But can use in tweet context
        
        # Build message
        if data_type == "air_quality":
            message = f"Health Alert for {location}: {action_line}"
        elif data_type == "disease":
            message = f"Health Notice for {location}: {action_line}"
        else:
            message = f"Public Health Advisory - {location}: {action_line}"
        
        # Select appropriate hashtags
        base_tags = ["PublicHealth", "HealthAlert", "CommunityWellness"]
        
        if data_type == "air_quality":
            base_tags.extend(["AirQuality", "CleanAir", "PM25"])
        elif data_type == "disease":
            base_tags.extend(["InfectiousDisease", "HealthSafety"])
        
        # Add location tag
        if location:
            state_abbrevs = {
                'California': 'CA', 'Texas': 'TX', 'New York': 'NY',
                'Florida': 'FL', 'Illinois': 'IL', 'Arizona': 'AZ',
                'Pennsylvania': 'PA', 'Ohio': 'OH', 'Michigan': 'MI'
            }
            loc_tag = state_abbrevs.get(location, location.replace(' ', ''))
            base_tags.append(loc_tag)
        
        hashtag_string = ' '.join([f'#{tag}' for tag in base_tags[:6]])  # Limit to 6 hashtags
        full_tweet = f"{message}\n\n{hashtag_string}"
        
        return {
            "status": "success",
            "message": message,
            "hashtags": base_tags[:6],
            "full_tweet": full_tweet,
            "char_count": len(full_tweet)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error formatting tweet: {str(e)}"
        }

