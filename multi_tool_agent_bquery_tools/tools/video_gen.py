"""
Video Generation Tools - ActionLine + Veo 3 Integration
Isolated module for PSA video generation feature
"""
from typing import Optional, Dict
import os


def generate_action_line(health_data: dict) -> dict:
    """
    Converts health data into a single actionable recommendation.
    
    Args:
        health_data: Dict with keys:
            - type: "air_quality" or "disease" or "general"
            - severity: "good", "moderate", "unhealthy", "hazardous"
            - location: state/county name
            - metric: AQI value or case count
            - details: additional context
            - specific_concern: e.g., "PM2.5", "E. coli", "heat"
    
    Returns:
        dict: {
            "status": "success",
            "action_line": "Single sentence recommendation (≤12 words)",
            "category": health_data type,
            "severity": severity level,
            "icon_hint": suggested icon for video
        }
    
    Examples:
        Input: {type: "air_quality", severity: "unhealthy", metric: 155}
        Output: {action_line: "Wear a mask outside.", icon_hint: "mask"}
        
        Input: {type: "disease", severity: "moderate", specific_concern: "E. coli"}
        Output: {action_line: "Boil tap water before use.", icon_hint: "boiling_pot"}
    """
    try:
        data_type = health_data.get('type', 'general')
        severity = health_data.get('severity', 'moderate').lower()
        metric = health_data.get('metric', 0)
        concern = health_data.get('specific_concern', '').lower()
        location = health_data.get('location', '')
        
        # ActionLine generation logic based on type and severity
        action_line = ""
        icon_hint = ""
        
        if data_type == "air_quality":
            if severity in ["unhealthy", "very unhealthy", "hazardous"]:
                if metric > 200:
                    action_line = "Avoid all outdoor activities today."
                    icon_hint = "house_person_inside"
                elif metric > 150:
                    action_line = "Wear a mask outside."
                    icon_hint = "face_mask"
                else:
                    action_line = "Limit outdoor exertion."
                    icon_hint = "person_resting"
            elif severity == "unhealthy for sensitive groups":
                action_line = "Sensitive groups: limit outdoor time."
                icon_hint = "elder_person_caution"
            else:
                action_line = "Air quality is good. Enjoy outdoors!"
                icon_hint = "person_walking_park"
                
        elif data_type == "disease":
            if "e. coli" in concern or "e.coli" in concern:
                action_line = "Boil tap water for one minute."
                icon_hint = "boiling_pot_steam"
            elif "salmonella" in concern:
                action_line = "Cook meat thoroughly before eating."
                icon_hint = "thermometer_meat"
            elif "norovirus" in concern:
                action_line = "Wash hands frequently with soap."
                icon_hint = "hands_washing_soap"
            elif "hepatitis" in concern:
                action_line = "Practice good hand hygiene."
                icon_hint = "hands_sanitizer"
            else:
                action_line = "Wash hands before eating."
                icon_hint = "hands_washing"
                
        elif data_type == "heat":
            action_line = "Drink water often and rest in shade."
            icon_hint = "water_bottle_tree"
            
        elif data_type == "cold":
            action_line = "Layer up and cover exposed skin."
            icon_hint = "person_winter_clothes"
            
        elif data_type == "water":
            action_line = "Boil tap water for one minute."
            icon_hint = "boiling_pot"
            
        else:
            # Generic fallback
            action_line = "Follow local health department guidance."
            icon_hint = "information_i"
        
        return {
            "status": "success",
            "action_line": action_line,
            "category": data_type,
            "severity": severity,
            "icon_hint": icon_hint,
            "location": location
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error generating action line: {str(e)}"
        }


def create_veo_prompt(action_line: str, icon_hint: str = "", severity: str = "moderate") -> dict:
    """
    Converts action line into Veo 3 video generation prompt.
    
    Args:
        action_line: The single-sentence recommendation (≤12 words)
        icon_hint: Suggested icon/scene (e.g., "mask", "boiling_pot")
        severity: "low", "moderate", "high", "critical" (affects check vs caution icon)
    
    Returns:
        dict: {
            "status": "success",
            "veo_prompt": "Complete Veo 3 prompt text",
            "duration": 8,
            "aspect_ratio": "1080x1920",
            "check_or_caution": "green_check" or "red_caution"
        }
    """
    try:
        # Determine if this is a "do" (green check) or "avoid" (red caution)
        avoid_keywords = ["avoid", "don't", "do not", "stay indoors", "limit", "reduce"]
        is_warning = any(keyword in action_line.lower() for keyword in avoid_keywords)
        
        check_or_caution = "red_caution" if is_warning else "green_check"
        
        # Map icon hints to visual descriptions
        icon_descriptions = {
            "face_mask": "simple person bust puts on a blue surgical mask; elastic straps slide behind ears",
            "boiling_pot_steam": "pot on stove with water boiling; steam rises in gentle curves",
            "hands_washing_soap": "hands under running water with soap bubbles forming and washing away",
            "house_person_inside": "house silhouette with person safely inside; outdoor particles bounce off walls",
            "person_resting": "person sitting on bench under tree; taking a rest",
            "water_bottle_tree": "water bottle being lifted to drink; tree providing shade in background",
            "thermometer_meat": "meat thermometer inserted into chicken showing safe temperature",
            "person_walking_park": "person walking happily in park with trees and sun",
        }
        
        icon_scene = icon_descriptions.get(
            icon_hint,
            f"simple icon showing the action described in the text; minimal, clear, friendly design"
        )
        
        # Build the complete Veo 3 prompt
        veo_prompt = f"""Create an 8-second, silent, vertical (1080×1920) vector-style PSA infographic.
Visual style: flat, friendly, rounded shapes, soft sky-blue gradient background, subtle drop shadows, high contrast, no photos, no logos, no extra text.

On-screen text (one line, show for full duration, centered in a rounded banner at the bottom):
"{action_line}"

Scene:
- Center: {icon_scene}
- Animate the action between 0–6s; at completion, a {"green checkmark pops above" if not is_warning else "red caution icon appears with"} the icon.
- 6–8s: hold final frame with gentle idle motion.

Accessibility: large readable font, strong color contrast, safe margins.
Keep composition simple and calm; focus attention on the icon and the single line of text.
"""
        
        return {
            "status": "success",
            "veo_prompt": veo_prompt,
            "duration": 8,
            "aspect_ratio": "1080x1920",
            "check_or_caution": check_or_caution,
            "action_line": action_line
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error creating Veo prompt: {str(e)}"
        }


def generate_video_with_veo3(veo_prompt: str, location: str = "California") -> dict:
    """
    Calls Google Veo 3 API to generate video.
    
    Args:
        veo_prompt: The formatted Veo prompt text
        location: Location name for filename
    
    Returns:
        dict: {
            "status": "success" | "processing" | "error",
            "operation_id": "projects/.../operations/...",
            "video_uri": "gs://bucket/path/video.mp4",
            "estimated_time": 60-90 seconds
        }
    """
    try:
        # Import and use the Veo3Client
        from ..integrations.veo3_client import get_veo3_client
        
        veo_client = get_veo3_client()
        
        # Generate filename based on location and timestamp
        import time
        timestamp = int(time.time())
        safe_location = location.replace(' ', '-').lower()
        output_filename = f"psa-{safe_location}-{timestamp}.mp4"
        
        # Call Veo 3 to generate video
        result = veo_client.generate_video(
            prompt=veo_prompt,
            output_filename=output_filename
        )
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "error_message": f"Error calling Veo 3 API: {str(e)}"
        }


def check_video_generation_status(operation_id: str) -> dict:
    """
    Checks the status of a Veo 3 video generation operation.
    
    Args:
        operation_id: The operation ID from generate_video_with_veo3
    
    Returns:
        dict: {
            "status": "processing" | "complete" | "error",
            "progress": 0-100,
            "video_uri": "gs://..." (if complete),
            "preview_url": "https://..." (if complete)
        }
    """
    try:
        # Use the Veo3Client to check status
        from ..integrations.veo3_client import get_veo3_client
        
        veo_client = get_veo3_client()
        result = veo_client.check_operation_status(operation_id)
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error checking video status: {str(e)}"
        }

