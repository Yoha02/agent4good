"""
Test Real Veo 3 Video Generation
This will actually call the Veo 3 API and generate a video
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import time

print("=" * 80)
print("TESTING REAL VEO 3 VIDEO GENERATION")
print("=" * 80)
print()

# Step 1: Generate action line
print("[Step 1] Generating action line from health data...")
from multi_tool_agent_bquery_tools.tools.video_gen import generate_action_line

health_data = {
    'type': 'air_quality',
    'severity': 'unhealthy',
    'metric': 155,
    'location': 'California',
    'specific_concern': 'PM2.5'
}

action_result = generate_action_line(health_data)
print(f"  Health Data: AQI {health_data['metric']}, Severity: {health_data['severity']}")
print(f"  Action Line: {action_result['action_line']}")
print(f"  Icon Hint: {action_result['icon_hint']}")
print()

# Step 2: Create Veo prompt
print("[Step 2] Creating Veo 3 video prompt...")
from multi_tool_agent_bquery_tools.tools.video_gen import create_veo_prompt

veo_result = create_veo_prompt(
    action_line=action_result['action_line'],
    icon_hint=action_result['icon_hint'],
    severity=health_data['severity']
)
print(f"  Prompt created: {len(veo_result['veo_prompt'])} characters")
print(f"  Duration: {veo_result['duration']} seconds")
print(f"  Aspect: {veo_result['aspect_ratio']}")
print()
print("  Full Veo Prompt:")
print("  " + "-" * 76)
print("  " + veo_result['veo_prompt'].replace('\n', '\n  '))
print("  " + "-" * 76)
print()

# Step 3: Call Veo 3 API to generate video
print("[Step 3] Calling Veo 3 API to generate video...")
from multi_tool_agent_bquery_tools.tools.video_gen import generate_video_with_veo3

video_result = generate_video_with_veo3(
    veo_prompt=veo_result['veo_prompt'],
    location=health_data['location']
)

print(f"  Status: {video_result.get('status')}")
print(f"  Operation ID: {video_result.get('operation_id')}")
print(f"  Output URI: {video_result.get('output_gcs_uri')}")
print(f"  Est. Time: {video_result.get('estimated_seconds')} seconds")
print()

if video_result.get('status') == 'error':
    print(f"[ERROR] {video_result.get('error_message')}")
    print()
    print("Make sure:")
    print("  1. Vertex AI API is enabled")
    print("  2. GCS bucket exists: qwiklabs-gcp-00-4a7d408c735c-psa-videos")
    print("  3. GOOGLE_GENAI_USE_VERTEXAI=TRUE in .env")
    print("  4. You're authenticated: gcloud auth application-default login")
else:
    # Step 4: Poll for completion
    print("[Step 4] Waiting for video generation to complete...")
    print("  This typically takes 60-120 seconds...")
    print()
    
    from multi_tool_agent_bquery_tools.tools.video_gen import check_video_generation_status
    from multi_tool_agent_bquery_tools.integrations.veo3_client import get_veo3_client
    
    operation = video_result.get('operation')  # Get the operation object
    operation_id = video_result.get('operation_id')
    
    if not operation:
        print("[ERROR] No operation object returned")
        exit(1)
    
    max_polls = 24  # 24 polls x 10 seconds = 4 minutes max
    poll_interval = 10  # seconds
    
    # Get the veo client to check status
    veo_client = get_veo3_client()
    
    for i in range(max_polls):
        time.sleep(poll_interval)
        
        # Check status with the operation object
        status_result = veo_client.check_operation_status(operation)
        progress = status_result.get('progress', 0)
        status = status_result.get('status')
        
        print(f"  Poll {i+1}/{max_polls}: {status} - {progress}% complete")
        
        if status == 'complete':
            print()
            print("=" * 80)
            print("[SUCCESS] VIDEO GENERATION COMPLETE!")
            print("=" * 80)
            print()
            
            # Check if we have video bytes or URI
            if 'video_bytes' in status_result:
                video_bytes = status_result['video_bytes']
                video_size = status_result['video_size']
                print(f"Video received as bytes: {video_size:,} bytes")
                
                # Save to local file
                output_file = "psa_video_output2.mp4"
                veo_client.save_video_bytes(video_bytes, output_file)
                print(f"\nVideo saved to: {output_file}")
                print(f"You can now:")
                print(f"  1. Open {output_file} in your video player")
                print(f"  2. Upload to your GCS bucket")
                print(f"  3. Post to Twitter")
                
            elif 'video_uri' in status_result:
                video_uri = status_result['video_uri']
                preview_url = status_result['preview_url']
                print(f"Video URI: {video_uri}")
                print(f"Preview URL: {preview_url}")
                print()
                print("You can view the video at:")
                print(f"  {preview_url}")
            
            print()
            break
        elif status == 'error':
            print()
            print(f"[ERROR] Video generation failed: {status_result.get('error_message')}")
            break
    else:
        print()
        print("[TIMEOUT] Video generation took longer than expected")
        print(f"Operation ID: {operation_id}")
        print("You can check status later with check_video_generation_status()")

print()
print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

