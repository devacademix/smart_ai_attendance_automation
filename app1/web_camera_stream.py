# -*- coding: utf-8 -*-
import time
from datetime import timedelta

import cv2
import numpy as np
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now as timezone_now

from .models import Attendance, AssignedClass, CameraConfiguration, Settings, Student, Teacher
from .views import (
    _closest_face_distance,
    _safe_student_checkout_threshold,
    detect_faces,
    encode_face_patch,
    encode_uploaded_images,
    extract_face_patch,
    resolve_face_match_threshold,
)


FRAME_WIDTH = 1280
FRAME_HEIGHT = 720


def _open_camera_source(camera_source):
    source = str(camera_source).strip()
    if source.isdigit():
        return cv2.VideoCapture(int(source))

    if not any(source.startswith(prefix) for prefix in ("http://", "https://", "rtsp://", "rtmp://")):
        source = f"http://{source}"

    return cv2.VideoCapture(source, cv2.CAP_FFMPEG)


def _encode_mjpeg_frame(frame):
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        return None
    return (
        b"--frame\r\n"
        b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
    )


def _error_frame(message):
    frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    cv2.putText(
        frame,
        "Camera Stream Error",
        (40, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (0, 0, 255),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        message,
        (40, 160),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return frame


def generate_mjpeg_stream(request, class_id, camera_id):
    """
    Browser-safe MJPEG stream with live face recognition and attendance marking.
    """
    teacher = get_object_or_404(Teacher, user=request.user)
    assigned_class = get_object_or_404(AssignedClass, id=class_id, teacher=teacher)
    cam_config = get_object_or_404(
        CameraConfiguration,
        id=camera_id,
        assigned_classes=assigned_class,
    )

    students_in_class = Student.objects.filter(
        courses=assigned_class.course,
        department=assigned_class.department,
        semester=assigned_class.semester,
    ).distinct()
    eligible_student_ids = list(
        students_in_class.filter(authorized=True, face_embedding__isnull=False)
        .values_list("id", flat=True)
        .distinct()
    )

    if not eligible_student_ids:
        def no_profiles_stream():
            frame = _error_frame("No authorized student face profiles found for this class.")
            while True:
                payload = _encode_mjpeg_frame(frame)
                if payload:
                    yield payload
                time.sleep(0.5)

        return StreamingHttpResponse(
            no_profiles_stream(),
            content_type="multipart/x-mixed-replace; boundary=frame",
        )

    known_face_encodings, known_face_names, known_face_ids = encode_uploaded_images(
        eligible_student_ids,
        include_ids=True,
    )

    if not known_face_encodings:
        def no_embeddings_stream():
            frame = _error_frame("Face embeddings are missing or unreadable for this class.")
            while True:
                payload = _encode_mjpeg_frame(frame)
                if payload:
                    yield payload
                time.sleep(0.5)

        return StreamingHttpResponse(
            no_embeddings_stream(),
            content_type="multipart/x-mixed-replace; boundary=frame",
        )

    known_face_matrix = np.asarray(known_face_encodings, dtype=np.float32)
    students_map = {
        student.id: student for student in students_in_class.filter(id__in=known_face_ids)
    }

    global_settings = Settings.objects.filter(student__isnull=True).first() or Settings.objects.first()
    global_check_out_threshold_seconds = global_settings.check_out_time_threshold if global_settings else 28800
    threshold = resolve_face_match_threshold(cam_config.threshold)

    def stream():
        cap = None
        try:
            cap = _open_camera_source(cam_config.camera_source)
            while True:
                if cap is None or not cap.isOpened():
                    if cap is not None:
                        cap.release()
                    cap = _open_camera_source(cam_config.camera_source)
                    if cap is None or not cap.isOpened():
                        frame = _error_frame("Unable to connect camera. Retrying...")
                        payload = _encode_mjpeg_frame(frame)
                        if payload:
                            yield payload
                        time.sleep(1.0)
                        continue

                ret, frame = cap.read()
                if not ret or frame is None:
                    frame = _error_frame("No frame received from camera. Reconnecting...")
                    payload = _encode_mjpeg_frame(frame)
                    if payload:
                        yield payload
                    cap.release()
                    cap = None
                    time.sleep(0.5)
                    continue

                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                boxes = detect_faces(frame_rgb)

                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                        face_patch = extract_face_patch(frame_rgb, box)
                        if face_patch is None:
                            continue

                        test_face_encoding = encode_face_patch(face_patch)
                        min_distance_idx, min_distance = _closest_face_distance(
                            known_face_matrix,
                            test_face_encoding,
                        )

                        label = f"Unknown d={min_distance:.2f}"
                        label_color = (0, 0, 255)

                        if min_distance <= threshold:
                            student_id = known_face_ids[min_distance_idx]
                            student = students_map.get(student_id)
                            name = known_face_names[min_distance_idx]

                            if student:
                                check_out_threshold_seconds = _safe_student_checkout_threshold(
                                    student,
                                    global_check_out_threshold_seconds,
                                )
                                attendance, _ = Attendance.objects.get_or_create(
                                    student=student,
                                    date=timezone_now().date(),
                                    course=assigned_class.course,
                                )

                                if attendance.check_in_time is None:
                                    attendance.mark_checked_in()
                                    label = f"{name}, checked in"
                                    label_color = (0, 255, 0)
                                elif attendance.check_out_time is None:
                                    if timezone_now() >= attendance.check_in_time + timedelta(
                                        seconds=check_out_threshold_seconds
                                    ):
                                        attendance.mark_checked_out()
                                        label = f"{name}, checked out"
                                        label_color = (0, 255, 0)
                                    else:
                                        label = f"{name}, already checked in"
                                        label_color = (0, 215, 255)
                                else:
                                    label = f"{name}, already checked out"
                                    label_color = (0, 215, 255)

                        cv2.putText(
                            frame,
                            label,
                            (x1, max(y1 - 10, 24)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            label_color,
                            2,
                            cv2.LINE_AA,
                        )

                cv2.putText(
                    frame,
                    f"{cam_config.name} | threshold={threshold:.2f}",
                    (16, 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

                payload = _encode_mjpeg_frame(frame)
                if payload:
                    yield payload

                time.sleep(0.03)

        finally:
            if cap is not None:
                cap.release()

    return StreamingHttpResponse(
        stream(),
        content_type="multipart/x-mixed-replace; boundary=frame",
    )
