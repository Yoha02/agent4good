"""
Test Gemini API integration
"""
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

print(f"✓ API Key found: {GEMINI_API_KEY[:10]}...")
print("=" * 80)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Test text analysis
try:
    print("\nTesting Gemini 2.5 Flash (Text Analysis)...")
    print("-" * 80)
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """You are an AI assistant helping public health officials analyze environmental and health reports.

Analyze this report and provide:
1. A concise 2-3 sentence summary of the key issues and concerns
2. Relevant tags from this list ONLY: valid, urgent, moderate, inappropriate, needs_review, contact_required, false_alarm, monitoring_required
3. A confidence score (0.0 to 1.0) indicating how confident you are that this is a legitimate, valid report

Report Details:
- Type: water
- Severity Level: high
- When it occurred: today
- Description: There is a strong chemical smell coming from the tap water in our apartment building. Multiple neighbors have reported the same issue. The water also has a yellowish tint. This started this morning around 8am.

Guidelines:
- Mark as "urgent" if immediate action is needed (high severity, dangerous conditions, many people affected)
- Mark as "valid" if the report seems legitimate and verifiable
- Mark as "inappropriate" or "false_alarm" if the report is clearly spam, irrelevant, or not a real issue
- Mark as "needs_review" if you're uncertain or need human verification
- Mark as "contact_required" if officials should reach out to the reporter
- Confidence should be lower (0.3-0.6) for vague reports, higher (0.7-0.95) for detailed, specific reports

Return ONLY valid JSON (no markdown, no code blocks):
{"summary": "your 2-3 sentence summary here", "tags": ["tag1", "tag2"], "confidence": 0.85}"""
    
    response = model.generate_content(prompt)
    text = response.text.strip()
    
    print(f"Raw Response:\n{text}\n")
    
    # Clean up
    text = text.replace('```json', '').replace('```', '').strip()
    
    result = json.loads(text)
    
    print("✅ Parsed JSON Successfully!")
    print(f"\nSummary: {result['summary']}")
    print(f"Tags: {result['tags']}")
    print(f"Confidence: {result['confidence']}")
    
    print("\n" + "=" * 80)
    print("✅ Gemini API is working correctly!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
