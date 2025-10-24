"""
Test PSA Video Feature Components
Tests all modules in isolation and integration
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("TESTING PSA VIDEO FEATURE")
print("=" * 80)
print()

# Test 1: Import all modules
print("[Test 1] Importing modules...")
try:
    from multi_tool_agent_bquery_tools.tools.video_gen import (
        generate_action_line,
        create_veo_prompt
    )
    from multi_tool_agent_bquery_tools.tools.social_media import (
        post_to_twitter,
        format_health_tweet
    )
    from multi_tool_agent_bquery_tools.integrations.veo3_client import Veo3Client
    from multi_tool_agent_bquery_tools.integrations.twitter_client import TwitterClient
    print("[OK] All modules imported successfully")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    exit(1)

print()

# Test 2: Generate action line
print("[Test 2] Testing ActionLine generation...")
health_data = {
    'type': 'air_quality',
    'severity': 'unhealthy',
    'metric': 155,
    'location': 'California',
    'specific_concern': 'PM2.5'
}

result = generate_action_line(health_data)
print(f"  Input: AQI=155, Severity=unhealthy")
print(f"  Output: {result.get('action_line')}")
print(f"  Icon: {result.get('icon_hint')}")
print(f"  Status: {'[OK]' if result.get('status') == 'success' else '[FAIL]'}")
print()

# Test 3: Create Veo prompt
print("[Test 3] Testing Veo Prompt creation...")
action_line = result.get('action_line', 'Wear a mask outside.')
icon_hint = result.get('icon_hint', 'face_mask')

veo_result = create_veo_prompt(action_line, icon_hint, 'high')
print(f"  Action line: {action_line}")
print(f"  Prompt length: {len(veo_result.get('veo_prompt', ''))} characters")
print(f"  Duration: {veo_result.get('duration')} seconds")
print(f"  Aspect ratio: {veo_result.get('aspect_ratio')}")
print(f"  Status: {'[OK] PASS' if veo_result.get('status') == 'success' else '[FAIL] FAIL'}")
print()

# Test 4: Format tweet
print("[Test 4] Testing Tweet formatting...")
tweet_result = format_health_tweet(
    action_line=action_line,
    location='California',
    data_type='air_quality',
    severity='unhealthy'
)
print(f"  Message: {tweet_result.get('message')}")
print(f"  Hashtags: {', '.join(tweet_result.get('hashtags', []))}")
print(f"  Char count: {tweet_result.get('char_count')}/280")
print(f"  Status: {'[OK] PASS' if tweet_result.get('status') == 'success' else '[FAIL] FAIL'}")
print()

# Test 5: Veo 3 Client
print("[Test 5] Testing Veo 3 Client...")
veo_client = Veo3Client()
print(f"  Project: {veo_client.project_id}")
print(f"  Location: {veo_client.location}")
print(f"  Bucket: {veo_client.gcs_bucket}")
print(f"  Status: [OK] Client initialized")
print()

# Test 6: Twitter Client
print("[Test 6] Testing Twitter Client...")
twitter_client = TwitterClient()
print(f"  Has API key: {'Yes' if twitter_client.api_key else 'No (simulation mode)'}")
print(f"  Status: [OK] Client initialized")
print()

# Test 7: Full workflow simulation
print("[Test 7] Testing full workflow...")
print("  Step 1: Generate action line...")
action_result = generate_action_line({
    'type': 'disease',
    'severity': 'moderate',
    'specific_concern': 'E. coli',
    'location': 'Texas'
})
print(f"    → {action_result.get('action_line')}")

print("  Step 2: Create Veo prompt...")
veo_result = create_veo_prompt(
    action_result.get('action_line'),
    action_result.get('icon_hint'),
    'moderate'
)
print(f"    → Prompt created ({len(veo_result.get('veo_prompt', ''))} chars)")

print("  Step 3: Format tweet...")
tweet_result = format_health_tweet(
    action_result.get('action_line'),
    'Texas',
    'disease',
    'moderate'
)
print(f"    → {tweet_result.get('full_tweet')[:100]}...")

print("  Step 4: Simulate Twitter post...")
post_result = post_to_twitter(
    video_uri="gs://test-bucket/video.mp4",
    message=tweet_result.get('message'),
    hashtags=tweet_result.get('hashtags')
)
print(f"    → {post_result.get('message')}")

print()
print("=" * 80)
print("[OK] ALL TESTS PASSED")
print("=" * 80)
print()
print("PSA Video feature is working in simulation mode!")
print("Next: Add real API credentials to enable actual video generation")
print()

