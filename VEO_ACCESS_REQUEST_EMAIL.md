Subject: Request for Veo Video Generation API Access - Community Health PSA Feature

Dear Agents for Impact Team,

We're reaching out regarding our Community Health & Wellness platform project and a feature we've developed that requires access to Google's Veo video generation API.

---

## Project Context

We've built a comprehensive health monitoring application with:
- Multi-agent AI system using Google ADK
- Real-time EPA air quality data integration
- CDC infectious disease tracking
- Interactive web dashboard with visualizations

**Live Demo**: https://community-health-agent-776464277441.us-central1.run.app

---

## Feature We've Developed

**PSA Video Generation System**: An automated workflow that:

1. Analyzes current health data (air quality, disease outbreaks)
2. Uses AI to create actionable one-line health recommendations (e.g., "Wear a mask outside.")
3. Generates 8-second PSA videos using Veo
4. Prepares content for social media distribution

**Purpose**: Enable communities to quickly create and share visual health alerts on social media platforms.

---

## Current Issue

We've successfully implemented the complete PSA video generation framework, but we're encountering permission errors when trying to generate videos in our Qwiklabs environment.

### **Error Details**:

```
403 PERMISSION_DENIED
Permission 'aiplatform.endpoints.predict' denied on resource 
'//aiplatform.googleapis.com/projects/qwiklabs-gcp-00-4a7d408c735c/locations/us-central1/publishers/google/models/veo-2.0-generate-001'
```

### **What We've Tried**:

**Attempted Models**:
- ✓ `veo-3.0-generate-001` (Google AI SDK) - Generates but can't access video
- ✗ `veo-3.0-fast-generate-001` - Permission denied
- ✗ `veo-3.0-generate-preview` - Permission denied  
- ✗ `veo-3.1-generate-preview` - Permission denied
- ✗ `veo-3.1-fast-generate-preview` - Permission denied
- ✗ `veo-2.0-generate-001` - Permission denied

**IAM Roles Added**:
- ✓ `roles/aiplatform.user` (granted to our user account)
- ✓ Vertex AI API enabled (`aiplatform.googleapis.com`)

**APIs Enabled**:
- ✓ Vertex AI API
- ✓ Generative Language API
- ✓ Cloud Build, Cloud Run, BigQuery

### **Testing Results**:

Using the Google AI SDK (`veo-3.0-generate-001`), we **successfully generated videos**:
- Operation ID: `models/veo-3.0-generate-001/operations/uskq1tzplq9o`
- Status: Completed successfully
- Time: ~50 seconds per video

However, the generated videos are stored in Google's internal system and we cannot download them due to cross-project permission restrictions.

---

## What We Need

To complete and demonstrate this feature, we need one of the following:

### **Option 1: Vertex AI Veo Model Access** (Preferred)

Grant permission to use Veo models via Vertex AI in our project:
- **Project ID**: `qwiklabs-gcp-00-4a7d408c735c`
- **Location**: `us-central1`
- **Required Permission**: `aiplatform.endpoints.predict`
- **Required Models**: Any of:
  - `veo-2.0-generate-001` (standard)
  - `veo-3.0-generate-001` (preferred)

### **Option 2: Access to Generated Videos**

If Vertex AI access isn't available, enable download access for videos generated via the Google AI API.

Our API key already successfully generates videos, we just need permission to download them from:
`https://generativelanguage.googleapis.com/v1beta/files/[FILE_ID]:download`

### **Option 3: Alternative Testing Environment**

If Qwiklabs restrictions prevent Veo access, could you provide:
- A non-Qwiklabs Google Cloud project with Veo enabled, or
- Service account credentials with Veo permissions

---

## Technical Implementation Details

### **What's Already Built** (All Code Complete):

**Backend**:
- ✓ 3 specialized AI agents (ActionLine, VeoPrompt, Twitter)
- ✓ Veo 3 API integration with fallback modes
- ✓ Video generation workflow
- ✓ Flask endpoints for UI integration
- ✓ Modular architecture for team collaboration

**Architecture**:
```
Health Data → ActionLine Agent → "Wear a mask outside."
           ↓
VeoPrompt Agent → Detailed Veo prompt
           ↓
Veo API → 8-second PSA video
           ↓
Twitter Agent → Post to social media
```

**Testing Status**:
- ✓ ActionLine generation: Tested, working
- ✓ Veo prompt creation: Tested, working  
- ✓ Video API calls: Tested, videos generate successfully
- ✗ Video retrieval: Blocked by permissions
- ✓ Twitter integration: Ready (simulation mode)

### **Code Location**:

- **Repository**: https://github.com/Yoha02/agent4good
- **Branch**: `veo3-twitter`
- **Modules**:
  - `multi_tool_agent_bquery_tools/agents/psa_video.py` (3 agents)
  - `multi_tool_agent_bquery_tools/integrations/veo3_client.py` (API wrapper)
  - `multi_tool_agent_bquery_tools/tools/video_gen.py` (generation functions)

---

## Use Case & Impact

**Scenario**: Air quality reaches unhealthy levels in California (AQI 155)

**Our System**:
1. Detects elevated AQI from EPA data
2. Generates recommendation: "Wear a mask outside."
3. Creates 8-second animated PSA video showing person putting on mask
4. Posts to Twitter/X with: "Health Alert for California: Wear a mask outside. #HealthAlert #AirQuality #CA"

**Community Impact**: Rapid, visual, shareable health alerts for vulnerable populations.

---

## Request

Could you please either:
1. **Enable Veo API access** in our project `qwiklabs-gcp-00-4a7d408c735c`, or
2. **Provide guidance** on how to access Veo in Qwiklabs environments, or
3. **Grant temporary access** to a project with Veo enabled for demonstration

We'd love to showcase this feature as part of our Community Health & Wellness platform and demonstrate the complete workflow from health data to social media PSA distribution.

---

## Additional Information

**Current Working Features**:
- ✓ Web dashboard with real EPA air quality data
- ✓ Disease tracking from CDC BEAM data
- ✓ Multi-agent chat system
- ✓ State-based filtering and trend analysis
- ✓ Deployed and live on Cloud Run

**Technical Specifications for Veo**:
- Model: Veo 2 or Veo 3 (flexible)
- Duration: 8 seconds
- Aspect Ratio: 9:16 (vertical for social media)
- Resolution: 720p (acceptable) or 1080p (preferred)
- Audio: Silent
- Output: Base64 bytes or GCS URI

---

Thank you for organizing this impactful hackathon and for considering our request. We believe the PSA video generation feature would significantly enhance our platform's ability to serve communities with timely, accessible health information.

Please let us know if you need any additional technical details or if there's an alternative approach we should explore.

Best regards,  
Agents4Good Team

---

**Project Details**:
- **Project ID**: qwiklabs-gcp-00-4a7d408c735c
- **GitHub**: https://github.com/Yoha02/agent4good
- **Feature Branch**: veo3-twitter
- **Live App**: https://community-health-agent-776464277441.us-central1.run.app
- **Account**: student-00-d8f1dd6f8a5b@qwiklabs.net

