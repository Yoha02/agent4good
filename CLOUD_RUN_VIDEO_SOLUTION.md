# Cloud Run Video Solution - Veo 3 PSA Feature

## ✅ What Works Locally (Proven):

1. Generate video with Veo 3.1 using Google AI SDK
2. Download video using `requests.get(video_uri, headers={'X-goog-api-key': api_key})`
3. Save to local file
4. Watch the video

## 🎯 Cloud Run Deployment Solution

For Cloud Run, we need to:
1. **Download video in backend** (same method)
2. **Upload to GCS** (for persistence)
3. **Serve to UI** via signed URL or direct bytes
4. **Post to Twitter** with downloaded video

---

## Implementation Strategy

### **Option 1: Stream Video Bytes to UI** (No GCS needed)

**Backend** (`app.py`):
```python
@app.route('/api/download-video', methods=['POST'])
def download_video():
    """Download generated video and return as bytes"""
    data = request.get_json()
    video_uri = data.get('video_uri')
    
    # Download video using API key
    api_key = os.getenv('GOOGLE_API_KEY')
    headers = {'X-goog-api-key': api_key}
    response = requests.get(video_uri, headers=headers)
    
    if response.status_code == 200:
        # Return video bytes directly to frontend
        return Response(
            response.content,
            mimetype='video/mp4',
            headers={
                'Content-Disposition': 'attachment; filename=psa_video.mp4',
                'Content-Length': len(response.content)
            }
        )
    else:
        return jsonify({'error': 'Failed to download video'}), 500
```

**Frontend**:
```javascript
async function loadGeneratedVideo(videoUri) {
    const response = await fetch('/api/download-video', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({video_uri: videoUri})
    });
    
    const videoBlob = await response.blob();
    const videoUrl = URL.createObjectURL(videoBlob);
    
    document.getElementById('videoPlayer').src = videoUrl;
}
```

**Pros**:
- ✅ No GCS bucket needed
- ✅ Direct streaming to UI
- ✅ Simple implementation

**Cons**:
- ❌ Video downloaded on every view
- ❌ Uses Cloud Run memory temporarily

---

### **Option 2: Upload to GCS, Serve from There** (Recommended)

**Backend**:
```python
from google.cloud import storage

@app.route('/api/save-video-to-gcs', methods=['POST'])
def save_video_to_gcs():
    """Download video and upload to GCS"""
    data = request.get_json()
    video_uri = data.get('video_uri')
    
    # 1. Download video
    api_key = os.getenv('GOOGLE_API_KEY')
    headers = {'X-goog-api-key': api_key}
    response = requests.get(video_uri, headers=headers)
    
    if response.status_code != 200:
        return jsonify({'error': 'Download failed'}), 500
    
    # 2. Upload to GCS
    bucket_name = os.getenv('GCS_VIDEO_BUCKET')
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Create unique filename
    import time
    filename = f"psa-videos/video-{int(time.time())}.mp4"
    blob = bucket.blob(filename)
    
    # Upload
    blob.upload_from_string(
        response.content,
        content_type='video/mp4'
    )
    
    # Make public or get signed URL
    blob.make_public()
    public_url = blob.public_url
    
    return jsonify({
        'success': True,
        'gcs_uri': f'gs://{bucket_name}/{filename}',
        'public_url': public_url,
        'video_size': len(response.content)
    })
```

**Frontend**:
```javascript
async function handleVideoGeneration(videoUri) {
    // Save to GCS
    const saveResponse = await fetch('/api/save-video-to-gcs', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({video_uri: videoUri})
    });
    
    const data = await saveResponse.json();
    
    // Display from GCS
    document.getElementById('videoPlayer').src = data.public_url;
}
```

**Pros**:
- ✅ Video stored permanently in your GCS
- ✅ Fast subsequent access
- ✅ Can share public URL
- ✅ Perfect for Twitter upload

**Cons**:
- Requires GCS bucket setup (already done!)

---

### **Option 3: Hybrid - Cache in GCS, Stream if Not Cached**

Best of both worlds:
1. Check if video already in GCS
2. If yes: serve from GCS
3. If no: download and upload to GCS
4. Return GCS public URL

---

## 🚀 Recommended Implementation

**Use Option 2** (Upload to GCS):

### **Updated Veo Client Method:**

```python
def download_and_save_video(self, video_uri: str, api_key: str, filename: str = None) -> dict:
    """
    Download video from Google's servers and save to GCS
    
    Args:
        video_uri: The URI from Veo generation
        api_key: Your Google API key
        filename: Optional custom filename
    
    Returns:
        dict with gcs_uri and public_url
    """
    try:
        # Download video
        headers = {'X-goog-api-key': api_key}
        response = requests.get(video_uri, headers=headers)
        
        if response.status_code != 200:
            return {
                "status": "error",
                "error_message": f"Download failed: {response.status_code}"
            }
        
        video_bytes = response.content
        
        # Upload to GCS
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.gcs_bucket)
        
        if not filename:
            import time
            filename = f"{self.gcs_prefix}psa-{int(time.time())}.mp4"
        
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type='video/mp4')
        blob.make_public()
        
        gcs_uri = f"gs://{self.gcs_bucket}/{filename}"
        public_url = blob.public_url
        
        print(f"[VEO3] Video saved to GCS: {gcs_uri}")
        print(f"[VEO3] Public URL: {public_url}")
        
        return {
            "status": "success",
            "gcs_uri": gcs_uri,
            "public_url": public_url,
            "video_size": len(video_bytes)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }
```

---

## 📱 For Twitter

When posting to Twitter, you'll need the video file:

```python
# 1. Download from GCS (or from original URI)
video_bytes = requests.get(public_url).content

# 2. Upload to Twitter
import tweepy
media = api.media_upload(filename='temp.mp4', file=BytesIO(video_bytes))

# 3. Post tweet with media
tweet = client.create_tweet(
    text="Health Alert for California: Wear a mask outside. #HealthAlert",
    media_ids=[media.media_id]
)
```

---

## 🎯 Complete Workflow for Cloud Run

```
User requests video
    ↓
1. Generate with Veo 3.1 (Google AI SDK)
    ↓
2. Get video URI from operation result
    ↓
3. Download video using requests + API key
    ↓
4. Upload to YOUR GCS bucket
    ↓
5. Return public GCS URL to UI
    ↓
6. UI displays video from GCS
    ↓
7. User approves
    ↓
8. Download from GCS, upload to Twitter
    ↓
9. Post tweet with video
```

---

## ✅ Benefits of This Approach

1. ✅ **Works with your API key** (proven!)
2. ✅ **Videos accessible** in your GCS bucket
3. ✅ **UI can display** videos from GCS
4. ✅ **Twitter can access** videos from GCS
5. ✅ **Permanent storage** of generated PSAs
6. ✅ **No permission issues** - all in your project

---

## 🔧 Next Steps

1. Update `veo3_client.py` with download method
2. Add GCS upload functionality
3. Update Flask endpoint to use this workflow
4. Test end-to-end in Cloud Run

**Want me to implement this solution?** 🚀

