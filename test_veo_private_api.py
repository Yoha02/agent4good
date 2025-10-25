"""
Test Veo 3 using Private Vertex AI API
This returns video bytes directly without needing GCS!
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time

print("=" * 80)
print("TESTING VEO 3 PRIVATE API (Returns video bytes!)")
print("=" * 80)
print()

from multi_tool_agent_bquery_tools.integrations.veo3_private_api import get_veo3_private_client

# Initialize
client = get_veo3_private_client()
print()

# Create prompt
prompt = """Create an 8-second, silent, vertical (1080x1920) health PSA.
Visual: flat vector style, sky-blue background, rounded shapes.
Text banner at bottom: "Wear a mask outside."
Scene: Person puts on blue surgical mask, green checkmark appears."""

print(f"[1] Generating video...")
print(f"  Prompt: {len(prompt)} characters")
print()

# Generate video
result = client.generate_video(prompt, resolution="720p")

if result['status'] == 'error':
    print(f"[ERROR] {result['error_message']}")
    exit(1)

operation_name = result['operation_name']
print(f"  Operation: {operation_name}")
print()

# Poll for completion
print(f"[2] Waiting for video generation...")
print(f"  This takes 60-120 seconds...")
print()

max_polls = 24
for i in range(max_polls):
    time.sleep(15)  # Poll every 15 seconds
    
    status = client.check_status(operation_name)
    
    print(f"  Poll {i+1}: {status.get('status')}")
    
    if status['status'] == 'complete':
        print()
        print("=" * 80)
        print("[SUCCESS] VIDEO GENERATION COMPLETE!")
        print("=" * 80)
        print()
        
        # Check what we got
        if 'video_bytes' in status:
            # We got the video as bytes!
            video_bytes = status['video_bytes']
            video_size = status['video_size']
            
            # Save to file
            output_file = "psa_video_final.mp4"
            with open(output_file, 'wb') as f:
                f.write(video_bytes)
            
            print(f"Video saved to: {output_file}")
            print(f"Size: {video_size:,} bytes")
            print()
            print("Watch the video:")
            print(f"  Start-Process {output_file}")
            print()
            
        elif 'video_uri' in status:
            print(f"Video URI: {status['video_uri']}")
            print("(Video stored in GCS)")
        
        break
        
    elif status['status'] == 'error':
        print(f"\n[ERROR] {status['error_message']}")
        break

else:
    print("\n[TIMEOUT] Video generation took too long")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

