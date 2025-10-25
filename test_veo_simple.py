"""
Simple Veo 3 Test - Following Google's Documentation Pattern
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Ensure API key is set
api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if api_key:
    os.environ['GOOGLE_API_KEY'] = api_key

print("=" * 80)
print("SIMPLE VEO 3 TEST (Following Google Docs)")
print("=" * 80)
print()

# Initialize client
print("[1] Initializing Veo 3 client...")
client = genai.Client()  # Will use GOOGLE_API_KEY from environment
print("  Client initialized")
print()

# Simple prompt for health PSA
prompt = """Create an 8-second, silent, vertical (1080x1920) vector-style PSA infographic.
Visual style: flat, friendly, rounded shapes, soft sky-blue gradient background.

On-screen text (show for full duration, in rounded banner at bottom):
"Wear a mask outside."

Scene:
- Center: simple person bust puts on blue surgical mask
- 0-6s: Mask slides on, green checkmark appears
- 6-8s: Hold final frame with text"""

print(f"[2] Generating video with Veo 3...")
print(f"  Prompt: {len(prompt)} characters")
print()

# Call Veo 3
operation = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt=prompt,
    config=genai.types.GenerateVideosConfig(
        aspect_ratio="9:16",
    ),
)

print(f"  Operation started: {operation.name}")
print(f"  Waiting for completion...")
print()

# Poll until done
poll_count = 0
while not operation.done:
    time.sleep(15)
    operation = client.operations.get(operation)
    poll_count += 1
    print(f"  Poll {poll_count}: Still generating...")

print()
print("[3] Video generation complete!")
print()

# Get the video
if operation.response:
    video = operation.result.generated_videos[0].video
    
    # Check what we have
    print(f"  Video object attributes:")
    print(f"    - mime_type: {video.mime_type}")
    print(f"    - has video_bytes: {hasattr(video, 'video_bytes')}")
    print(f"    - video_bytes length: {len(video.video_bytes) if hasattr(video, 'video_bytes') and video.video_bytes else 0}")
    print(f"    - has uri: {hasattr(video, 'uri')}")
    print(f"    - uri value: {video.uri if hasattr(video, 'uri') else None}")
    
    # Try video_bytes FIRST (preferred method)
    print()
    print("  Checking for video_bytes...")
    if hasattr(video, 'video_bytes') and video.video_bytes:
        # Save video bytes to file
        output_file = "psa_video.mp4"
        with open(output_file, 'wb') as f:
            f.write(video.video_bytes)
        print()
        print(f"[SUCCESS] Video saved to: {output_file}")
        print(f"  Size: {len(video.video_bytes):,} bytes")
        print()
        print(f"Open the video:")
        print(f"  Start-Process {output_file}")
        print()
        
        # Also show URI if available
        if hasattr(video, 'uri') and video.uri:
            print(f"  (Also available at: {video.uri})")
        
    elif hasattr(video, 'uri') and video.uri:
        print()
        print(f"  Video URI: {video.uri}")
        print(f"  (This is a Google internal URL - has bytes: {hasattr(video, 'video_bytes')})")
        
else:
    print("[ERROR] No response from operation")
    if operation.error:
        print(f"  Error: {operation.error.message}")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

