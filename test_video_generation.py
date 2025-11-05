"""
Test Video Generation - Verify error handling works correctly
"""
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

print("=" * 60)
print("VIDEO GENERATION TEST")
print("=" * 60)

# Test 1: Check environment variables
print("\n[TEST 1] Checking environment variables...")
google_api_key = os.getenv('GOOGLE_API_KEY')
google_project = os.getenv('GOOGLE_CLOUD_PROJECT')
gcs_bucket = os.getenv('GCS_VIDEO_BUCKET')

if google_api_key:
    print(f"✅ GOOGLE_API_KEY: {google_api_key[:20]}...")
else:
    print("❌ GOOGLE_API_KEY: NOT FOUND")
    
if google_project:
    print(f"✅ GOOGLE_CLOUD_PROJECT: {google_project}")
else:
    print("❌ GOOGLE_CLOUD_PROJECT: NOT FOUND")
    
if gcs_bucket:
    print(f"✅ GCS_VIDEO_BUCKET: {gcs_bucket}")
else:
    print("❌ GCS_VIDEO_BUCKET: NOT FOUND")

# Test 2: Initialize Veo3 Client
print("\n[TEST 2] Initializing Veo3 Client...")
try:
    from multi_tool_agent_bquery_tools.integrations.veo3_client import get_veo3_client
    
    veo_client = get_veo3_client()
    print(f"✅ Veo3 Client initialized")
    print(f"   Mode: {veo_client.client_mode}")
    print(f"   Client: {veo_client.client is not None}")
    
except Exception as e:
    print(f"❌ Error initializing client: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Generate a simple video (will likely hit quota/error)
print("\n[TEST 3] Testing video generation...")
print("⚠️ This will likely fail with 'Internal error' due to API limits")
print("   We're testing that the error is handled gracefully")

try:
    # Simple test prompt
    test_prompt = """8-second PSA video.
Text overlay: 'Air quality is good. Enjoy outdoors!'
Scene: Sunny park with clear blue sky.
Style: Clean, professional PSA format."""
    
    print(f"\n[VEO3 TEST] Calling generate_video()...")
    result = veo_client.generate_video(
        prompt=test_prompt,
        output_filename="test-psa.mp4"
    )
    
    print(f"\n[RESULT] Status: {result.get('status')}")
    
    if result.get('status') == 'error':
        print(f"❌ Error (EXPECTED): {result.get('error_message')}")
        print(f"\n✅ ERROR HANDLING WORKS - Error was caught and formatted correctly!")
        print(f"   No AttributeError or crash occurred.")
    elif result.get('status') == 'processing':
        print(f"✅ Video generation started!")
        print(f"   Operation: {result.get('operation_id')}")
        
        # Test 4: Poll for status (will likely error)
        print(f"\n[TEST 4] Checking operation status...")
        operation = result.get('operation')
        if operation:
            import time
            max_checks = 5
            for i in range(max_checks):
                print(f"\n[POLL {i+1}/{max_checks}] Checking status...")
                time.sleep(3)
                
                status = veo_client.check_operation_status(operation)
                print(f"   Status: {status.get('status')}")
                
                if status.get('status') == 'error':
                    print(f"❌ Error: {status.get('error_message')}")
                    print(f"\n✅ ERROR HANDLING WORKS in check_operation_status()!")
                    break
                elif status.get('status') == 'complete':
                    print(f"✅ Video complete!")
                    print(f"   URL: {status.get('video_url')}")
                    break
                else:
                    print(f"   Still processing...")
            else:
                print(f"⚠️ Stopped polling after {max_checks} attempts")
        else:
            print(f"⚠️ No operation object to poll")
    
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    print(f"   This should NOT happen - error should be caught!")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\n📋 SUMMARY:")
print("  - If you see 'Internal error' → ✅ Error handling works")
print("  - If you see AttributeError → ❌ Error handling broken")
print("  - If video completes → 🎉 Everything works!")
print("\n" + "=" * 60)

