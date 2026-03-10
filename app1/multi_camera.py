# -*- coding: utf-8 -*-
"""
app1/multi_camera.py
====================
Multi-camera monitoring for Smart AI Attendance System.

Features:
  * Each camera stream runs in its own thread (non-blocking).
  * Frames are resized to 640×480 for uniform grid tiling.
  * Grid layout adapts automatically:  2 cams → 1×2, 4 → 2×2, 6 → 2×3, etc.
  * Each cell shows an overlay with Room Name + Camera ID.
  * If a stream drops → shows a red "Camera Offline" frame (no crash).
  * Press  Q  to close the monitor window.

Usage from a Django view or management command:
    from app1.multi_camera import launch_multi_camera_monitor
    launch_multi_camera_monitor()   # blocks until user presses Q
"""

import cv2
import threading
import time
import math
import numpy as np
from typing import List, Tuple, Optional

# ── Cell dimensions ─────────────────────────────────────────────────────────
CELL_W, CELL_H = 640, 480

# ───────────────────────────────────────────────────────────────────────────
# 1. CameraStream  –  one thread per camera source
# ───────────────────────────────────────────────────────────────────────────

class CameraStream:
    """
    Wraps a single video source.
    Background thread reads frames continuously and stores the latest one.
    Thread-safe via a lock; reconnects automatically on stream failure.
    """

    def __init__(self, url, cam_id: int, room_name: str):
        """
        url       – int (webcam index) or str (RTSP / HTTP URL)
        cam_id    – numeric identifier shown in the overlay
        room_name – label shown in the overlay (e.g. "Room 101")
        """
        self.url = url
        self.cam_id = cam_id
        self.room_name = room_name
        self._lock = threading.Lock()
        self._frame = self._offline_frame()
        self._online = False
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ── blank / offline frame ────────────────────────────────────────────────
    def _offline_frame(self) -> np.ndarray:
        frame = np.zeros((CELL_H, CELL_W, 3), dtype=np.uint8)   # solid black
        cv2.putText(frame, "Camera Offline", (30, CELL_H // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 220), 2, cv2.LINE_AA)
        cv2.putText(frame, f"[{self.room_name} · Cam {self.cam_id}]",
                    (30, CELL_H // 2 + 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (180, 180, 180), 1, cv2.LINE_AA)
        return frame

    # ── lifecycle ────────────────────────────────────────────────────────────
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"cam-{self.cam_id}")
        self._thread.start()

    def stop(self):
        self._running = False

    # ── capture loop (runs in background thread) ─────────────────────────────
    def _run(self):
        cap = None
        while self._running:
            # (re)connect
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(self.url)
                if not cap.isOpened():
                    with self._lock:
                        self._frame = self._offline_frame()
                        self._online = False
                    time.sleep(2)          # wait before retry
                    continue

            ret, raw = cap.read()
            if not ret or raw is None:
                with self._lock:
                    self._frame = self._offline_frame()
                    self._online = False
                cap.release()
                cap = None
                time.sleep(1)
                continue

            frame = cv2.resize(raw, (CELL_W, CELL_H))
            with self._lock:
                self._frame = frame
                self._online = True

        if cap:
            cap.release()

    # ── public read ─────────────────────────────────────────────────────────
    def read(self) -> np.ndarray:
        with self._lock:
            return self._frame.copy()

    @property
    def is_online(self) -> bool:
        with self._lock:
            return self._online


# ───────────────────────────────────────────────────────────────────────────
# 2. Face-recognition pipeline hook
# ───────────────────────────────────────────────────────────────────────────

def _run_recognition_pipeline(frame: np.ndarray, cam_id: int, room_name: str) -> np.ndarray:
    """
    Call the existing AI pipeline (detect → encode → match → mark attendance).
    Returns the annotated frame.

    We do a lazy import here to avoid circular imports and to keep this module
    importable even when Django hasn't finished starting up yet.
    """
    try:
        from app1.views import detect_and_encode, encode_uploaded_images, recognize_faces
        from app1.models import Student, Attendance
        from django.utils import timezone

        today = timezone.now().date()
        known_encodings, known_names = encode_uploaded_images()
        if not known_encodings:
            return frame

        known_encodings_np = __import__('numpy').array(known_encodings)
        test_encodings = detect_and_encode(frame)
        if not test_encodings:
            return frame

        names = recognize_faces(known_encodings_np, known_names, test_encodings)
        for name in names:
            if name == 'Not Recognized':
                continue
            try:
                student = Student.objects.get(name=name, authorized=True)
                attendance, created = Attendance.objects.get_or_create(
                    student=student, date=today,
                    defaults={'status': 'Present', 'check_in_time': timezone.now()}
                )
                if not created and attendance.check_out_time is None:
                    attendance.check_out_time = timezone.now()
                    attendance.save()
            except Student.DoesNotExist:
                pass

            # Draw name on frame
            cv2.putText(frame, name, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
    except Exception as err:
        # Never crash the display loop on a pipeline error
        cv2.putText(frame, f"Pipeline err: {err}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 80, 255), 1, cv2.LINE_AA)

    return frame


# ───────────────────────────────────────────────────────────────────────────
# 3. MultiCameraMonitor  –  grid compositor + display loop
# ───────────────────────────────────────────────────────────────────────────

class MultiCameraMonitor:
    """
    Starts all CameraStream threads, composites their frames into a grid,
    runs the face-recognition pipeline on each, and shows one OpenCV window.
    """

    WINDOW_TITLE = "Smart AI Attendance – Multi Camera Monitor"

    def __init__(self, camera_cfg: List[Tuple[str, object]]):
        """
        camera_cfg  –  list of (room_name, stream_url_or_index)
                       e.g. [("Room 101", 0), ("Room 102", "http://...")]
        """
        self.streams = [
            CameraStream(url, idx + 1, room)
            for idx, (room, url) in enumerate(camera_cfg)
        ]

    @staticmethod
    def _grid_shape(n: int) -> Tuple[int, int]:
        """Return (rows, cols) for n cameras."""
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        return rows, cols

    @staticmethod
    def _add_label(frame: np.ndarray, room: str, cam_id: int) -> np.ndarray:
        label = f"{room}  |  Camera {cam_id}"
        # Semi-transparent background strip
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (CELL_W, 42), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
        cv2.putText(frame, label, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 230, 0), 2, cv2.LINE_AA)
        return frame

    def run(self, run_ai: bool = True):
        """
        Main display loop.
        run_ai – set False to show raw feeds only (faster, for testing).
        """
        for s in self.streams:
            s.start()

        cv2.namedWindow(self.WINDOW_TITLE, cv2.WINDOW_NORMAL)
        print(f"[MultiCam] Started {len(self.streams)} stream(s). Press  Q  to quit.")

        try:
            while True:
                frames = []
                for stream in self.streams:
                    frame = stream.read()

                    if run_ai and stream.is_online:
                        frame = _run_recognition_pipeline(frame, stream.cam_id, stream.room_name)

                    frame = self._add_label(frame, stream.room_name, stream.cam_id)
                    frames.append(frame)

                # ── build grid ──────────────────────────────────────────────
                rows, cols = self._grid_shape(len(frames))

                # Pad so that rows*cols == len(frames)
                blank = np.zeros((CELL_H, CELL_W, 3), dtype=np.uint8)
                while len(frames) < rows * cols:
                    frames.append(blank)

                row_imgs = [
                    cv2.hconcat(frames[r * cols: (r + 1) * cols])
                    for r in range(rows)
                ]
                grid = cv2.vconcat(row_imgs)

                cv2.imshow(self.WINDOW_TITLE, grid)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    print("[MultiCam] Q pressed – exiting.")
                    break

        finally:
            for s in self.streams:
                s.stop()
            cv2.destroyAllWindows()


# ───────────────────────────────────────────────────────────────────────────
# 4. Convenience launcher (called from Django view)
# ───────────────────────────────────────────────────────────────────────────

def launch_multi_camera_monitor(camera_cfg: Optional[List[Tuple[str, object]]] = None):
    """
    camera_cfg – list of (room_name, stream_url_or_index)

    If None, the function tries to load cameras from the DB
    (app1.models.CameraConfiguration).  Falls back to local webcam 0.
    """
    if camera_cfg is None:
        camera_cfg = _load_cameras_from_db()

    if not camera_cfg:
        print("[MultiCam] No cameras found. Using local webcam 0 as fallback.")
        camera_cfg = [("Local Webcam", 0)]

    monitor = MultiCameraMonitor(camera_cfg)
    monitor.run(run_ai=True)


def _load_cameras_from_db() -> List[Tuple[str, object]]:
    """Load enabled CameraConfiguration records from the database."""
    cfg = []
    try:
        from app1.models import CameraConfiguration
        for cam in CameraConfiguration.objects.all():
            # camera_source can be an int (webcam index) or a URL string
            src = cam.camera_source
            try:
                src = int(src)
            except (ValueError, TypeError):
                pass
            cfg.append((cam.name, src))
    except Exception as err:
        print(f"[MultiCam] Could not load cameras from DB: {err}")
    return cfg
