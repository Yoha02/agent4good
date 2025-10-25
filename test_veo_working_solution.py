"""
Working Veo 3 Solution - Downloads video successfully!
Uses Google AI SDK + requests download method
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import os
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if api_key:
    os.environ['GOOGLE_API_KEY'] = api_key

print("=" * 80)
print("COMPLETE VEO 3 PSA VIDEO TEST - WORKING SOLUTION")
print("=" * 80)
print()

# Step 1: Generate action line (use our existing function)
print("[Step 1] Creating health recommendation...")
from multi_tool_agent_bquery_tools.tools.video_gen import generate_action_line

health_data = {
    'type': 'air_quality',
    'severity': 'unhealthy',
    'metric': 155,
    'location': 'California',
    'specific_concern': 'PM2.5'
}

action_result = generate_action_line(health_data)
action_line = action_result['action_line']
print(f"  Action Line: {action_line}")
print()

# Step 2: Create Veo prompt (use our existing function)
print("[Step 2] Creating Veo 3 video prompt...")
from multi_tool_agent_bquery_tools.tools.video_gen import create_veo_prompt

veo_result = create_veo_prompt(
    action_line=action_line,
    icon_hint=action_result['icon_hint'],
    severity='unhealthy'
)
prompt = veo_result['veo_prompt']
print(f"  Prompt created: {len(prompt)} characters")
print()

# Step 3: Generate video with Veo 3
print("[Step 3] Generating video with Veo 3...")
print("  Initializing client...")
client = genai.Client()  # Uses GOOGLE_API_KEY from environment

print("  Calling Veo 3.1 Fast API...")
operation = client.models.generate_videos(
    model="veo-3.1-fast-generate-preview",  # Fast model - generates quicker
    prompt=prompt,
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",
        number_of_videos=1,
        duration_seconds=8,
        resolution="720p",
    ),
)

print(f"  Operation started: {operation.name}")
print("  Waiting for video generation (60-90 seconds)...")
print()

# Step 4: Poll for completion
poll_count = 0
while not operation.done:
    time.sleep(15)
    operation = client.operations.get(operation)
    poll_count += 1
    print(f"  Poll {poll_count}: Still generating...")

print()
print("[Step 4] Video generation complete!")
print()

# Step 5: Download the video
if operation.response:
    video_uri = operation.result.generated_videos[0].video.uri
    print(f"  Video URI: {video_uri}")
    print()
    
    print("[Step 5] Downloading video...")
    
    # Download using requests with API key
    headers = {'X-goog-api-key': api_key}
    response = requests.get(video_uri, headers=headers)
    
    if response.status_code == 200:
        # Save video
        output_file = "psa_video_complete.mp4"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        
        print()
        print("=" * 80)
        print("[SUCCESS] VIDEO DOWNLOADED!")
        print("=" * 80)
        print()
        print(f"File: {output_file}")
        print(f"Size: {len(response.content):,} bytes")
        print()
        
        # Step 5b: Upload to GCS for sharing
        print("[Step 5b] Uploading to GCS for UI/Twitter...")
        
        from google.cloud import storage
        
        bucket_name = os.getenv('GCS_VIDEO_BUCKET', 'qwiklabs-gcp-00-4a7d408c735c-psa-videos')
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Create unique filename
        gcs_filename = f"psa-videos/california-aqi155-{int(time.time())}.mp4"
        blob = bucket.blob(gcs_filename)
        
        # Upload
        blob.upload_from_string(response.content, content_type='video/mp4')
        
        # Make public
        blob.make_public()
        
        gcs_uri = f"gs://{bucket_name}/{gcs_filename}"
        public_url = blob.public_url
        
        print(f"  GCS URI: {gcs_uri}")
        print(f"  Public URL: {public_url}")
        print()
        print("  This URL can be used for:")
        print(f"    - UI video player: <video src='{public_url}'></video>")
        print(f"    - Twitter upload: Download from {public_url}")
        print(f"    - Direct sharing: {public_url}")
        print()
        
        # Step 6: Format for Twitter
        print("[Step 6] Formatting for Twitter...")
        from multi_tool_agent_bquery_tools.tools.social_media import format_health_tweet
        
        tweet_result = format_health_tweet(
            action_line=action_line,
            location=health_data['location'],
            data_type=health_data['type'],
            severity=health_data['severity']
        )
        
        print(f"  Tweet: {tweet_result['message']}")
        print(f"  Hashtags: {', '.join(['#' + tag for tag in tweet_result['hashtags']])}")
        print(f"  Length: {tweet_result['char_count']}/280 characters")
        print()
        
        print("=" * 80)
        print("COMPLETE WORKFLOW SUCCESSFUL!")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  1. Health Data: AQI {health_data['metric']} ({health_data['severity']})")
        print(f"  2. Action Line: {action_line}")
        print(f"  3. Video Generated: {output_file}")
        print(f"  4. Tweet Ready: {tweet_result['char_count']} chars")
        print()
        print("Next: Post to Twitter with the video!")
        
    else:
        print(f"[ERROR] Download failed: {response.status_code}")
        print(f"  {response.text}")
else:
    print("[ERROR] No video generated")
    if operation.error:
        print(f"  Error: {operation.error.message}")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

