"""
Async Video Generation Manager - Modular background task handler
Separate module for managing video generation tasks without blocking chat
"""
from threading import Thread
from typing import Dict, Optional
import uuid
import os


class VideoGenerationManager:
    """Manages async video generation tasks"""
    
    def __init__(self):
        self.tasks = {}  # In production, use Redis
        print("[VIDEO_MANAGER] Initialized")
    
    def create_task(self, location: str, data_type: str = 'air_quality') -> str:
        """
        Create a new video generation task
        
        Args:
            location: State/county name
            data_type: 'air_quality' or 'disease'
        
        Returns:
            str: Unique task ID
        """
        task_id = str(uuid.uuid4())[:8]  # Short ID
        
        self.tasks[task_id] = {
            'status': 'initializing',
            'progress': 0,
            'location': location,
            'data_type': data_type,
            'created_at': __import__('time').time()
        }
        
        print(f"[VIDEO_MANAGER] Task created: {task_id}")
        return task_id
    
    def update_task(self, task_id: str, updates: Dict):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            print(f"[VIDEO_MANAGER] Task {task_id} updated: {updates.get('status')}")
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task status"""
        return self.tasks.get(task_id)
    
    def start_video_generation(self, task_id: str, health_data: Dict, 
                               veo_client, action_line_func, veo_prompt_func):
        """
        Start async video generation in background thread
        
        Args:
            task_id: Task identifier
            health_data: Current health metrics
            veo_client: Veo3Client instance
            action_line_func: Function to generate action line
            veo_prompt_func: Function to create Veo prompt
        """
        def generate_in_background():
            try:
                # Step 1: Generate action line
                self.update_task(task_id, {
                    'status': 'generating_action_line',
                    'progress': 10
                })
                
                action_result = action_line_func(health_data)
                action_line = action_result['action_line']
                
                # Step 2: Create Veo prompt
                self.update_task(task_id, {
                    'status': 'creating_prompt',
                    'progress': 20,
                    'action_line': action_line
                })
                
                veo_result = veo_prompt_func(
                    action_line=action_line,
                    icon_hint=action_result.get('icon_hint', ''),
                    severity=health_data.get('severity', 'moderate')
                )
                
                # Step 3: Generate video
                self.update_task(task_id, {
                    'status': 'generating_video',
                    'progress': 30
                })
                
                video_gen_result = veo_client.generate_video(
                    prompt=veo_result['veo_prompt'],
                    output_filename=f"psa-{health_data.get('location', 'health')}-{task_id}.mp4"
                )
                
                if video_gen_result.get('status') == 'error':
                    self.update_task(task_id, {
                        'status': 'error',
                        'error': video_gen_result.get('error_message')
                    })
                    return
                
                # Step 4: Poll until complete (auto downloads/uploads)
                operation = video_gen_result.get('operation')
                if not operation:
                    self.update_task(task_id, {
                        'status': 'error',
                        'error': 'No operation returned'
                    })
                    return
                
                # Poll with progress updates
                import time
                max_polls = 24  # 2 minutes max
                for i in range(max_polls):
                    time.sleep(5)
                    
                    progress = 30 + (i * 3)  # 30% to 100%
                    self.update_task(task_id, {
                        'status': 'generating_video',
                        'progress': min(progress, 95)
                    })
                    
                    status = veo_client.check_operation_status(operation)
                    
                    if status.get('status') == 'complete':
                        # Video ready with public URL!
                        self.update_task(task_id, {
                            'status': 'complete',
                            'progress': 100,
                            'video_url': status.get('video_url'),
                            'gcs_uri': status.get('gcs_uri'),
                            'action_line': action_line,
                            'video_size': status.get('video_size'),
                            'message': status.get('message', 'Video ready')
                        })
                        return
                    elif status.get('status') == 'error':
                        self.update_task(task_id, {
                            'status': 'error',
                            'error': status.get('error_message', 'Unknown error')
                        })
                        return
                
                # Timeout
                self.update_task(task_id, {
                    'status': 'error',
                    'error': 'Video generation timeout'
                })
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.update_task(task_id, {
                    'status': 'error',
                    'error': str(e)
                })
        
        # Start background thread
        thread = Thread(target=generate_in_background)
        thread.daemon = True
        thread.start()
        
        print(f"[VIDEO_MANAGER] Started background generation for task {task_id}")


# Singleton instance
_video_manager = None

def get_video_manager() -> VideoGenerationManager:
    """Get or create VideoGenerationManager singleton"""
    global _video_manager
    if _video_manager is None:
        _video_manager = VideoGenerationManager()
    return _video_manager

