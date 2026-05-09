"""
recognition.py
--------------
Core face recognition logic:
- Enrolment: capture face from webcam, extract encoding, store encrypted
- Verification: compare live face against database with liveness detection
- Liveness detection: Eye Aspect Ratio (EAR) blink detection
"""

import logging
import time
from collections import deque

import cv2
import face_recognition
import numpy as np

from .database import (
    init_db, save_encoding, load_all_encodings, log_event
)

logger = logging.getLogger(__name__)

# --- Tunable constants ---
MATCH_TOLERANCE = 0.5          # Lower = stricter (0.4–0.6 recommended)
CAPTURE_COUNTDOWN = 3          # Seconds before auto-capture during enrolment
VERIFICATION_TIMEOUT = 15      # Seconds before verification fails
LIVENESS_BLINK_REQUIRED = 1    # Minimum blinks required to pass liveness
EAR_THRESHOLD = 0.25           # Eye Aspect Ratio below this = eye closed
EAR_CONSEC_FRAMES = 2          # Consecutive closed-eye frames to count as blink

# dlib facial landmark indices for left/right eyes
LEFT_EYE_IDX = list(range(36, 42))
RIGHT_EYE_IDX = list(range(42, 48))


def _eye_aspect_ratio(eye_points: np.ndarray) -> float:
    """Compute Eye Aspect Ratio (EAR) for blink detection."""
    A = np.linalg.norm(eye_points[1] - eye_points[5])
    B = np.linalg.norm(eye_points[2] - eye_points[4])
    C = np.linalg.norm(eye_points[0] - eye_points[3])
    return (A + B) / (2.0 * C)


def _draw_overlay(frame, text: str, color=(0, 255, 0), subtext: str = ""):
    """Draw status overlay on video frame."""
    h, w = frame.shape[:2]
    # Semi-transparent banner at bottom
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 80), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, text, (15, h - 45), cv2.FONT_HERSHEY_DUPLEX, 0.8, color, 2)
    if subtext:
        cv2.putText(frame, subtext, (15, h - 15), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1)
    return frame


def enroll(name: str) -> bool:
    """
    Open webcam, capture a clear face frame, extract encoding, store encrypted.
    Returns True on success, False on failure.
    """
    init_db()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open webcam.")
        return False

    print(f"\n  [*] Enrolling: {name}")
    print(f"  [*] Look at the camera. Auto-capturing in {CAPTURE_COUNTDOWN}s...")
    print("  [*] Press 'c' to capture manually, or 'q' to cancel.\n")

    start_time = time.time()
    captured_encoding = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")

            elapsed = time.time() - start_time
            remaining = max(0, CAPTURE_COUNTDOWN - int(elapsed))

            if len(locations) == 1:
                top, right, bottom, left = locations[0]
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 100), 2)
                status = f"Face detected — capturing in {remaining}s" if remaining > 0 else "Capturing..."
                frame = _draw_overlay(frame, status, color=(0, 255, 100),
                                      subtext="Press 'c' to capture now | 'q' to cancel")
            elif len(locations) == 0:
                frame = _draw_overlay(frame, "No face detected — please look at camera",
                                      color=(0, 100, 255))
            else:
                frame = _draw_overlay(frame, "Multiple faces detected — only one person please",
                                      color=(0, 100, 255))

            cv2.imshow(f"Enrolment — {name}", frame)
            key = cv2.waitKey(1) & 0xFF

            # Auto-capture after countdown, or manual capture
            auto_capture = elapsed >= CAPTURE_COUNTDOWN and len(locations) == 1
            manual_capture = key == ord('c') and len(locations) == 1

            if auto_capture or manual_capture:
                encodings = face_recognition.face_encodings(rgb, locations)
                if encodings:
                    captured_encoding = encodings[0]
                    break

            if key == ord('q'):
                print("  [!] Enrolment cancelled by user.")
                log_event("ENROLL_CANCELLED", user=name, success=False)
                return False

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if captured_encoding is None:
        print("  [!] Failed to extract face encoding.")
        log_event("ENROLL_FAILED", user=name, success=False, details="No encoding extracted")
        return False

    success = save_encoding(name, captured_encoding)
    if success:
        print(f"  [✓] '{name}' enrolled successfully.")
        log_event("ENROLL_SUCCESS", user=name, success=True)
    else:
        print(f"  [!] '{name}' already exists in the database.")
        log_event("ENROLL_DUPLICATE", user=name, success=False)

    return success


def verify(require_liveness: bool = True) -> tuple[bool, str]:
    """
    Open webcam, perform liveness check (blink detection), then match face.
    Returns (success: bool, name: str).
    """
    init_db()
    known = load_all_encodings()
    if not known:
        print("  [!] No users enrolled. Please enrol someone first.")
        return False, ""

    known_names = [k[0] for k in known]
    known_encodings = [k[1] for k in known]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logger.error("Cannot open webcam.")
        return False, ""

    print("\n  [*] Starting verification...")
    if require_liveness:
        print(f"  [*] Liveness check: please blink {LIVENESS_BLINK_REQUIRED} time(s).\n")
    else:
        print("  [!] Liveness check disabled.\n")

    blink_count = 0
    eye_closed_frames = 0
    liveness_passed = not require_liveness
    start_time = time.time()
    result_name = ""
    success = False

    # EAR history for smoothing
    ear_history = deque(maxlen=5)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            elapsed = time.time() - start_time
            if elapsed > VERIFICATION_TIMEOUT:
                print("  [!] Verification timed out.")
                log_event("VERIFY_TIMEOUT", success=False)
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")

            time_left = int(VERIFICATION_TIMEOUT - elapsed)

            if len(locations) == 1:
                top, right, bottom, left = locations[0]
                color = (0, 255, 100) if liveness_passed else (0, 200, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # --- Liveness: EAR blink detection ---
                if require_liveness and not liveness_passed:
                    # Use dlib landmarks via face_recognition
                    landmarks_list = face_recognition.face_landmarks(rgb, locations)
                    if landmarks_list:
                        lm = landmarks_list[0]
                        left_eye = np.array(lm.get("left_eye", []))
                        right_eye = np.array(lm.get("right_eye", []))

                        if len(left_eye) == 6 and len(right_eye) == 6:
                            ear = (_eye_aspect_ratio(left_eye) + _eye_aspect_ratio(right_eye)) / 2.0
                            ear_history.append(ear)
                            smooth_ear = np.mean(ear_history)

                            if smooth_ear < EAR_THRESHOLD:
                                eye_closed_frames += 1
                            else:
                                if eye_closed_frames >= EAR_CONSEC_FRAMES:
                                    blink_count += 1
                                    logger.debug("Blink detected. Total: %d", blink_count)
                                eye_closed_frames = 0

                            if blink_count >= LIVENESS_BLINK_REQUIRED:
                                liveness_passed = True
                                print("  [✓] Liveness check passed.")

                    subtext = f"Blinks: {blink_count}/{LIVENESS_BLINK_REQUIRED} | Time left: {time_left}s"
                    frame = _draw_overlay(frame, "Blink to prove liveness", color=(0, 200, 255),
                                         subtext=subtext)

                # --- Face matching (only after liveness) ---
                if liveness_passed:
                    encodings = face_recognition.face_encodings(rgb, locations)
                    if encodings:
                        distances = face_recognition.face_distance(known_encodings, encodings[0])
                        best_idx = int(np.argmin(distances))
                        best_dist = distances[best_idx]

                        if best_dist <= MATCH_TOLERANCE:
                            result_name = known_names[best_idx]
                            confidence = round((1 - best_dist) * 100, 1)
                            frame = _draw_overlay(
                                frame,
                                f"ACCESS GRANTED — {result_name}",
                                color=(0, 255, 100),
                                subtext=f"Confidence: {confidence}% | Match distance: {best_dist:.3f}"
                            )
                            cv2.imshow("Face Authentication", frame)
                            cv2.waitKey(1500)
                            success = True
                            log_event("VERIFY_SUCCESS", user=result_name, success=True,
                                      details=f"distance={best_dist:.3f}")
                            break
                        else:
                            frame = _draw_overlay(
                                frame, "ACCESS DENIED — face not recognised",
                                color=(0, 0, 255),
                                subtext=f"Time left: {time_left}s"
                            )

            elif len(locations) == 0:
                frame = _draw_overlay(frame, f"No face detected | Time left: {time_left}s",
                                      color=(100, 100, 255))
            else:
                frame = _draw_overlay(frame, "Multiple faces — only one person please",
                                      color=(0, 100, 255))

            cv2.imshow("Face Authentication", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                log_event("VERIFY_CANCELLED", success=False)
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if not success:
        if result_name == "":
            print("  [✗] Verification failed — face not recognised or timed out.")
            log_event("VERIFY_FAILED", success=False)

    return success, result_name
