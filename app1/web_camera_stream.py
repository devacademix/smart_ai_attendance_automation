# -*- coding: utf-8 -*-
"""
app1/web_camera_stream.py
==========================
Web-based camera streaming for VPS/headless servers.

This module streams camera feeds directly to web browsers using MJPEG over HTTP,
bypassing the need for OpenCV GUI windows (cv2.imshow).

Features:
  * Works on headless VPS servers (no X11/display required)
  * Streams video via browser instead of OpenCV windows
  * Real-time face recognition with attendance marking
  * Supports multiple cameras simultaneously
  * Automatic reconnection for dropped streams

Usage in Django view:
    from app1.web_camera_stream import CameraStreamHandler
    
    handler = CameraStreamHandler(camera_config)
    return handler.generate_stream(request)
"""

import cv2
import threading
import time
import numpy as np
from django.shortcuts import get_object_or_404
from django.http import StreamingHttpResponse
from django.utils.timezone import now as timezone_now
from datetime import timedelta
import pygame
from .models import Student, Attendance, Settings, Teacher, AssignedClass, CameraConfiguration
from .views import detect_faces, extract_face_patch, encode_face_patch, encode_uploaded_images


class CameraFrameGenerator:
    """Generates MJPEG frames for a single camera with face recognition."""
    
    def __init__(self, cam_config, eligible_student_ids, students_in_class, threshold=0.75):
        self.cam_config = cam_config
        self.eligible_student_ids = eligible_student_ids
        self.students_in_class = students_in_class
        self.threshold = threshold
        self.cap = None
        self.running = False
        self.frame_queue = []
        self.lock = threading.Lock()
        
        # Initialize face recognition data
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.students_map = {}
        
        # Load known faces
        self._load_known_faces()
        
    def _load_known_faces(self):
        """Load authorized student face encodings."""
        try:
            self.known_face_encodings, self.known_face_names, self.known_face_ids = encode_uploaded_images(
                self.eligible_student_ids, include_ids=True
            )
            print(f"[{self.cam_config.name}] Loaded {len(self.known_face_encodings)} authorized faces for recognition.")
            if self.known_face_encodings:
                self.students_map = {
                    student.id: student 
                    for student in self.students_in_class.filter(id__in=self.eligible_student_ids)
                }
            else:
                print(f"[{self.cam_config.name}] Warning: No known faces found for this class.")
        except Exception as e:
            print(f"[{self.cam_config.name}] Error loading known faces: {e}")
            
    def _open_camera(self):
        """Open camera connection."""
        try:
            source = self.cam_config.camera_source
            if source.isdigit():
                print(f"Connecting to camera source: {source}")
                # Use CAP_FFMPEG for better performance on Linux VPS
                self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                
            if not self.cap.isOpened():
                print(f"[ERROR] [{self.cam_config.name}] Remote VPS cannot reach source: {source}")
                print(f"[TIP] Make sure your VPS can ping this IP or if using Tailscale, that the VPS is logged in.")
                return False
            
            print(f"[SUCCESS] [{self.cam_config.name}] Connected to stream at {source}")
                
            # Set camera properties for better detection quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            return True
        except Exception as e:
            print(f"Camera error ({self.cam_config.name}): {e}")
            return False
            
    def _process_frame(self, frame):
        """Process frame with face recognition and draw annotations."""
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            boxes = detect_faces(frame_rgb)
            
            if boxes is not None:
                # If we have no known faces, we can only detect but not recognize
                if not self.known_face_encodings:
                    for box in boxes:
                        pt1 = (int(box[0]), int(box[1]))
                        pt2 = (int(box[2]), int(box[3]))
                        cv2.rectangle(frame, pt1, pt2, (255, 255, 0), 2)  # Yellow for detection only
                        cv2.putText(frame, "Face Detected (Need Authorized Students)", (pt1[0], pt2[1] + 20), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    return frame

                for box in boxes:
                    pt1 = (int(box[0]), int(box[1]))
                    pt2 = (int(box[2]), int(box[3]))
                    cv2.rectangle(frame, pt1, pt2, (255, 0, 0), 2)
                    
                    face = extract_face_patch(frame_rgb, box)
                    if face is None:
                        continue
                    
                    # Optional: Add a "Processing" indicator
                    cv2.putText(frame, "Analyzing...", (pt1[0], pt1[1] - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    test_face_encoding = encode_face_patch(face)
                    distances = np.linalg.norm(
                        np.asarray(self.known_face_encodings, dtype=np.float32) - test_face_encoding, 
                        axis=1
                    )
                    min_distance_idx = int(np.argmin(distances))
                    min_distance = float(distances[min_distance_idx])
                    
                    text_y = int(box[3]) + 20
                    text_x = int(box[0])
                    
                    if min_distance <= self.threshold:
                        student_id = self.known_face_ids[min_distance_idx]
                        name = self.known_face_names[min_distance_idx]
                        student = self.students_map.get(student_id)
                        
                        if student:
                            # We now pass the course from assigned_class to mark attendance correctly
                            from .models import Course
                            course = getattr(self.cam_config, 'current_course', None)
                            self._mark_attendance(student, name, frame, pt1, pt2)
                        else:
                            cv2.putText(frame, f"{name} (Not in Class)", (text_x, text_y), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2, cv2.LINE_AA)
                    else:
                        cv2.putText(frame, f"Unknown ({min_distance:.2f})", (text_x, text_y), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
            
            # Add camera label
            cv2.putText(frame, f"{self.cam_config.name} - {self.cam_config.location}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            
            return frame
        except Exception as e:
            print(f"Frame processing error: {e}")
            cv2.putText(frame, f"Error: {str(e)}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
            return frame
            
    def _mark_attendance(self, student, name, frame, pt1, pt2):
        """Mark attendance for recognized student."""
        try:
            global_settings = Settings.objects.filter(student__isnull=True).first() or Settings.objects.first()
            check_out_threshold = global_settings.check_out_time_threshold if global_settings else 28800
            
            attendance, created = Attendance.objects.get_or_create(
                student=student, 
                course=self.cam_config.assigned_course, # Pass the course from cam_config
                date=timezone_now().date()
            )
            
            color = (0, 255, 0)
            status_text = ""
            
            if attendance.check_in_time is None:
                attendance.mark_checked_in()
                status_text = f"{name} - Checked In"
            elif attendance.check_out_time is None:
                if timezone_now() >= attendance.check_in_time + timedelta(seconds=check_out_threshold):
                    attendance.mark_checked_out()
                    status_text = f"{name} - Checked Out"
                else:
                    status_text = f"{name} - Already In"
                    color = (0, 255, 255)
            else:
                status_text = f"{name} - Already Out"
                color = (255, 0, 0)
            
            attendance.save()
            cv2.putText(frame, status_text, (pt1[0], pt1[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)
        except Exception as e:
            print(f"Attendance marking error: {e}")
            
    def _capture_loop(self):
        """Background thread to capture and process frames."""
        frame_count = 0
        last_processed_frame = None
        
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                if not self._open_camera():
                    time.sleep(2)
                    continue
            
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = None
                time.sleep(1)
                continue
            
            # Process recognition only every alternate frame for better FPS
            # while keeping the video feed buttery smooth
            if frame_count % 2 == 0:
                last_processed_frame = self._process_frame(frame)
                processed_frame = last_processed_frame
            else:
                processed_frame = last_processed_frame if last_processed_frame is not None else frame
            
            frame_count += 1
            
            # Encode as JPEG
            _, jpeg = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = jpeg.tobytes()
            
            # Add to queue
            with self.lock:
                self.frame_queue.append(frame_bytes)
                if len(self.frame_queue) > 5:  # Keep only latest 5 frames
                    self.frame_queue.pop(0)
                    
            time.sleep(0.03)  # ~30 FPS
            
    def start(self):
        """Start the camera stream."""
        self.running = True
        self._open_camera()
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
    def stop(self):
        """Stop the camera stream."""
        self.running = False
        if self.cap:
            self.cap.release()
            
    def get_frame(self):
        """Get the latest frame."""
        with self.lock:
            if self.frame_queue:
                return self.frame_queue.pop(0)
        return None


def generate_mjpeg_stream(request, class_id, camera_id=None):
    """
    Generate MJPEG stream for teacher's assigned class cameras.
    
    If camera_id is provided, only that camera is streamed.
    Otherwise, cycles through all assigned cameras (default behavior).
    """
    # Verify teacher access
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return StreamingHttpResponse(
            b"<h1>Unauthorized</h1>", 
            content_type='text/html', 
            status=403
        )
    
    assigned_class = get_object_or_404(AssignedClass, id=class_id, teacher=teacher)
    
    if camera_id:
        cam_configs = assigned_class.cameras.filter(id=camera_id)
    else:
        cam_configs = assigned_class.cameras.all()
    
    if not cam_configs.exists():
        return StreamingHttpResponse(
            b"<h1>No cameras assigned</h1>", 
            content_type='text/html', 
            status=404
        )
    
    # Get eligible students
    students_in_class = Student.objects.filter(
        courses=assigned_class.course,
        department=assigned_class.department,
        semester=assigned_class.semester
    ).distinct()
    
    eligible_student_ids = list(
        students_in_class.filter(authorized=True, face_embedding__isnull=False)
        .values_list('id', flat=True)
        .distinct()
    )
    
    # We continue even if no students are authorized, so the teacher can at least see the feed
    
    # Create frame generators for each camera
    generators = []
    for cam_config in cam_configs:
        # Attach course context for attendance marking
        cam_config.assigned_course = assigned_class.course
        
        gen = CameraFrameGenerator(
            cam_config, 
            eligible_student_ids, 
            students_in_class,
            threshold=cam_config.threshold or 0.75
        )
        gen.start()
        generators.append(gen)
    
    def event_stream():
        """Generate MJPEG stream by cycling through cameras."""
        frame_index = 0
        try:
            while True:
                for gen in generators:
                    frame = gen.get_frame()
                    if frame:
                        yield (b'--frame\r\n'
                              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                        frame_index += 1
                    else:
                        # Yield a "Searching/Error" frame if no data is coming
                        if frame_index % 30 == 0: # Print every 30 iterations to avoid log spam
                             print(f"Status: Waiting for frames from {gen.cam_config.name}...")
                        
                    time.sleep(0.01) # Faster polling for snappier response
        except GeneratorExit:
            # Clean up when client disconnects
            for gen in generators:
                gen.stop()
    
    response = StreamingHttpResponse(event_stream(), content_type='multipart/x-mixed-replace; boundary=frame')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
