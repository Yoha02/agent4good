#!/usr/bin/env python3
"""
Test Twitter posting with existing video
Tests the Twitter integration without generating new videos

Usage:
    python test_twitter_post.py           # Interactive mode (asks for confirmation)
    python test_twitter_post.py --auto    # Auto mode (no confirmation)
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_twitter_post(auto_mode=False):
    """Test posting to Twitter with a static message and existing video"""
    
    print("=" * 60)
    print("Testing Twitter Posting to @AI_mmunity")
    print("=" * 60)
    
    # Import Twitter client
    from multi_tool_agent_bquery_tools.integrations.twitter_client import get_twitter_client
    
    # Initialize client
    twitter_client = get_twitter_client()
    
    # Check if we have credentials
    if twitter_client.simulation_mode:
        print("\n[WARNING] Running in SIMULATION mode")
        print("[INFO] Add Twitter credentials to .env for real posting")
    else:
        print("\n[SUCCESS] Twitter client initialized with real credentials!")
        print(f"[INFO] Will post to account: @{os.getenv('TWITTER_USERNAME', 'AI_mmunity')}")
    
    # Use an existing video URL from your GCS bucket
    # Using one of the recently generated PSA videos
    video_url = "https://storage.googleapis.com/qwiklabs-gcp-00-4a7d408c735c-psa-videos/psa-videos/psa-1761359078.mp4"
    
    # Test message
    message = "Air quality is good. Enjoy outdoors!"
    
    # Test hashtags
    hashtags = ["HealthAlert", "AirQuality", "PublicHealth"]
    
    print("\n" + "=" * 60)
    print("Test Parameters:")
    print("=" * 60)
    print(f"Video URL: {video_url[:60]}...")
    print(f"Message: {message}")
    print(f"Hashtags: {hashtags}")
    print(f"Account: @{os.getenv('TWITTER_USERNAME', 'AI_mmunity')}")
    
    # Ask for confirmation (unless in auto mode)
    if not auto_mode:
        print("\n" + "=" * 60)
        response = input("Proceed with Twitter post? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("\n[CANCELLED] Test cancelled by user")
            return
    else:
        print("\n[AUTO MODE] Skipping confirmation...")
    
    print("\n" + "=" * 60)
    print("Posting to Twitter...")
    print("=" * 60)
    
    # Post to Twitter
    result = twitter_client.post_video_tweet(
        video_url=video_url,
        message=message,
        hashtags=hashtags
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    
    if result['status'] == 'success':
        print("[SUCCESS] Tweet posted successfully!")
        print(f"Tweet ID: {result['tweet_id']}")
        print(f"Tweet URL: {result['tweet_url']}")
        print(f"Message: {result.get('message', 'Posted!')}")
        
        if twitter_client.simulation_mode:
            print("\n[NOTE] This was a SIMULATION")
            print("[NOTE] Add real Twitter credentials to .env for actual posting")
        else:
            print(f"\n[SUCCESS] Check your tweet at: {result['tweet_url']}")
            print(f"[SUCCESS] Or visit: https://twitter.com/{os.getenv('TWITTER_USERNAME', 'AI_mmunity')}")
    else:
        print("[ERROR] Tweet posting failed!")
        print(f"Error: {result.get('error_message', 'Unknown error')}")
    
    print("=" * 60)

if __name__ == "__main__":
    # Check for --auto flag
    auto_mode = '--auto' in sys.argv
    test_twitter_post(auto_mode=auto_mode)


