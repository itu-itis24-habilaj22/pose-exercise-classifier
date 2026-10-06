"""Turn pose landmarks into features such as joint angles."""

import numpy as np

# MediaPipe Pose landmark indices (33 in total).
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28

# Each joint angle is measured at the middle point of (a, b, c), for (left, right).
JOINTS = {
    "knee": ((LEFT_HIP, LEFT_KNEE, LEFT_ANKLE), (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE)),
    "elbow": ((LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST), (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST)),
    "hip": ((LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE), (RIGHT_SHOULDER, RIGHT_HIP, RIGHT_KNEE)),
    "shoulder": ((LEFT_HIP, LEFT_SHOULDER, LEFT_ELBOW), (RIGHT_HIP, RIGHT_SHOULDER, RIGHT_ELBOW)),
}


def calculate_angle(a, b, c):
    """Angle in degrees at point b, formed by the lines b->a and b->c (0 to 180)."""
    a, b, c = np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)
    ba, bc = a - b, c - b
    norm = np.linalg.norm(ba) * np.linalg.norm(bc)
    if norm == 0:
        return 0.0
    cosine = np.clip(np.dot(ba, bc) / norm, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def joint_angle(world_landmarks, image_landmarks, joint):
    """Angle of a joint ("knee", "elbow", ...) on the side most visible to the camera.

    The angle uses MediaPipe world landmarks (3D, in meters), so it doesn't depend
    on image size or distance from the camera. Visibility comes from the image
    landmarks. Returns (angle, visibility), where visibility is the lowest of the
    three points.
    """
    best = None
    for side in JOINTS[joint]:
        visibility = min(image_landmarks[i].visibility or 0 for i in side)
        if best is None or visibility > best[1]:
            points = [world_landmarks[i] for i in side]
            angle = calculate_angle(*[(p.x, p.y, p.z) for p in points])
            best = (angle, visibility)
    return best
