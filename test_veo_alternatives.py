"""
Test Veo 3 with different parameters to find what works
"""
import os
import sys
import time
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

print("=" * 60)
print("VEO 3 ALTERNATIVE PARAMETERS TEST")
print("=" * 60)

from multi_tool_agent_bquery_tools.integrations.veo3_client import get_veo3_client

client = get_veo3_client()

# Test configurations
test_cases = [
    {
        "name": "Minimal prompt, 6 seconds",
        "prompt": "A sunny park",
        "duration": 6,
        "resolution": "480p"
    },
    {
        "name": "Simple prompt, 8 seconds, lower resolution",
        "prompt": "Outdoor scene with blue sky",
        "duration": 8,
        "resolution": "480p"
    },
    {
        "name": "Medium prompt, 6 seconds",
        "prompt": "A sunny park with clear blue sky. Text overlay: Air quality is good.",
        "duration": 6,
        "resolution": "720p"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}: {test['name']}")
    print(f"{'='*60}")
    print(f"Prompt: {test['prompt']}")
    print(f"Duration: {test['duration']}s, Resolution: {test['resolution']}")
    
    try:
        from google.genai import types
        
        # Manual call with custom parameters
        print(f"\n[TEST] Calling Veo 3 API...")
        operation = client.client.models.generate_videos(
            model="veo-3.0-fast-generate-001",
            prompt=test['prompt'],
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                number_of_videos=1,
                duration_seconds=test['duration'],
                resolution=test['resolution'],
            ),
        )
        
        print(f"✅ Video generation started!")
        print(f"   Operation: {operation.name}")
        
        # Poll for 30 seconds
        print(f"\n[TEST] Polling for 30 seconds...")
        for check in range(6):
            time.sleep(5)
            status_result = client.check_operation_status(operation)
            
            if status_result.get('status') == 'error':
                print(f"❌ FAILED: {status_result.get('error_message')}")
                break
            elif status_result.get('status') == 'complete':
                print(f"✅ SUCCESS! Video completed!")
                print(f"   URL: {status_result.get('video_url')}")
                print(f"\n🎉 SOLUTION FOUND: Use these parameters!")
                print(f"   Prompt style: {test['name']}")
                print(f"   Duration: {test['duration']}s")
                print(f"   Resolution: {test['resolution']}")
                sys.exit(0)
            else:
                print(f"   Check {check+1}/6: Still processing...")
        
        print(f"⏰ Still processing after 30s (may succeed later)")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n⏰ Waiting 60 seconds before next test...")
    time.sleep(60)

print(f"\n{'='*60}")
print("ALL TESTS COMPLETE")
print(f"{'='*60}")
print("\n📋 RESULTS:")
print("  If all failed with 'Internal error' → Google service issue")
print("  If some succeeded → Use those parameters")
print("  If quota errors → Need higher limits")

