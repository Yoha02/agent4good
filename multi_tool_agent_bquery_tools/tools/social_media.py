"""
Social Media Tools - Twitter/X Integration
Isolated module for posting health PSAs to social media
"""
from typing import Optional, List, Dict
import os


def post_to_twitter(video_uri: str, message: str, hashtags: Optional[List[str]] = None, location: Optional[str] = None) -> dict:
    """
    Posts video and message to Twitter/X.
    
    Args:
        video_uri: GCS URI of the video (e.g., "gs://bucket/video.mp4")
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
        
        # Format tweet text
        hashtag_string = ' '.join([f'#{tag}' for tag in hashtags])
        tweet_text = f"{message}\n\n{hashtag_string}"
        
        # Ensure within Twitter's 280 character limit
        if len(tweet_text) > 280:
            # Trim message if needed
            available_chars = 280 - len(hashtag_string) - 3  # -3 for \n\n
            message = message[:available_chars] + "..."
            tweet_text = f"{message}\n\n{hashtag_string}"
        
        # TODO: Implement actual Twitter API posting
        # This requires:
        # 1. Twitter API credentials (API key, secret, tokens)
        # 2. tweepy library
        # 3. Download video from GCS
        # 4. Upload video to Twitter
        # 5. Post tweet with video
        
        # Placeholder implementation
        print(f"[TWITTER] Would post tweet:")
        print(f"[TWITTER] Text: {tweet_text}")
        print(f"[TWITTER] Video: {video_uri}")
        
        # Simulated response
        import time
        tweet_id = f"{int(time.time())}"
        
        return {
            "status": "success",
            "tweet_url": f"https://twitter.com/CommunityHealthAlerts/status/{tweet_id}",
            "tweet_id": tweet_id,
            "tweet_text": tweet_text,
            "message": "Tweet posted successfully (simulation mode)",
            "note": "To enable real Twitter posting, add Twitter API credentials"
        }
        
    except Exception as e:
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

