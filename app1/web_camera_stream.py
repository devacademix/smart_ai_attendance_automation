# -*- coding: utf-8 -*-
import cv2
import threading
import time
import numpy as np
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from django.utils.timezone import now as timezone_now
from datetime import timedelta
from .models import Student, Attendance, Settings, Teacher, AssignedClass, CameraConfiguration
from .views import detect_faces, extract_face_patch, encode_face_patch, encode_uploaded_images

class CameraFrameGenerator:
    """Generates MJPEG frames for a single camera with face recognition."""
    
    _models_loaded = False
    known_face_encodings = []
    known_face_names = []
    known_face_ids = []

    def __init__(self, cam_config, eligible_student_ids, students_in_class, threshold=0.75):
        self.cam_config = cam_config
        self.eligible_student_ids = eligible_student_ids
        self.students_in_class = students_in_class
        self.threshold = threshold
        self.running = False
        self.cap = None
        self.frame_buffer = None
        self.lock = threading.Lock()
        self.capture_thread = None
        
        # Load models once
        if not CameraFrameGenerator._models_loaded:
            print(f"[INFO] Initializing face models for {cam_config.name}...")
            encs, names, ids = encode_uploaded_images(eligible_student_ids, include_ids=True)
            CameraFrameGenerator.known_face_encodings = encs
            CameraFrameGenerator.known_face_names = names
            CameraFrameGenerator.known_face_ids = ids
            CameraFrameGenerator._models_loaded = True

        self.students_map = {
            student.id: student 
            for student in self.students_in_class.filter(id__in=self.eligible_student_ids)
        }

    def _open_camera(self):
        try:
            source = str(self.cam_config.camera_source).strip()
            if source.isdigit():
                self.cap = cv2.VideoCapture(int(source))
            else:
                if not any(source.startswith(p) for p in ['http', 'rtsp', 'rtmp']):
                    source = 'http://' + source
                self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                
            if self.cap is None or not self.cap.isOpened():
                print(f"[ERROR] Connection failed: {source}")
                return False
            
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            print(f"[SUCCESS] Connected to {source}")
            return True
        except Exception as e:
            print(f"[ERROR] Camera open error: {e}")
            return False

    def _capture_loop(self):
        self.running = True
        frame_count = 0
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                if not self._open_camera():
                    time.sleep(2)
                    continue

            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = None
                continue

            frame_count += 1
            # Skip frames to keep up with real-time on VPS
            if frame_count % 2 == 0:
                processed_frame = self._process_frame(frame)
                with self.lock:
                    self.frame_buffer = processed_frame

    def _process_frame(self, frame):
        # Resize for faster processing
        small_frame = cv2.resize(frame, (640, 360))
        
        # Draw placeholder or recognition logic here
        # For now, just return the frame as JPEG
        _, buffer = cv2.imencode('.jpg', small_frame)
        return buffer.tobytes()

    def start(self):
        if not self.capture_thread or not self.capture_thread.is_alive():
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()

    def get_frame(self):
        with self.lock:
            return self.frame_buffer

def teacher_camera_stream_view(request, class_id):
    assigned_class = get_object_or_404(AssignedClass, id=class_id)
    cam_configs = CameraConfiguration.objects.all() # Or filtered
    
    # Simple single camera logic for now to test connection
    if not cam_configs.exists():
        return StreamingHttpResponse("No cameras configured", status=400)
    
    gen = CameraFrameGenerator(cam_configs[0], [], assigned_class.students.all())
    gen.start()

    def stream():
        try:
            while True:
                frame = gen.get_frame()
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.05)
        finally:
            gen.stop()

    return StreamingHttpResponse(stream(), content_type='multipart/x-mixed-replace; boundary=frame')
