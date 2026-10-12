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


def normalize_keypoints(keypoints, aspect_ratio=1.0):
    """Make poses comparable no matter where the person stands or how far away they are.

    keypoints: array of shape (frames, 33, 4) with x, y, z, visibility, where x and y
    are fractions of the image width and height (as saved by extract_poses.py).
    aspect_ratio: image width / height. x is a fraction of the width but y of the
    height, so on a non-square video they use different units; multiplying x by the
    aspect ratio puts both in "image heights" (z uses the same scale as x).

    Each frame is then centered on the middle of the hips and divided by the torso
    length (hips to shoulders), so the hip center is at (0, 0, 0) and the shoulders
    are about 1 unit away. Visibility is kept unchanged.

    The torso length is one value for the whole video (its 90th percentile), not one per
    frame: when the torso points at the camera (e.g. a push-up filmed from the front) it
    looks almost zero long in the image, and dividing by that would blow the pose up.
    """
    points = keypoints[..., :3].copy()
    points[..., 0] *= aspect_ratio
    points[..., 2] *= aspect_ratio

    hip_center = (points[:, LEFT_HIP] + points[:, RIGHT_HIP]) / 2
    shoulder_center = (points[:, LEFT_SHOULDER] + points[:, RIGHT_SHOULDER]) / 2
    # Torso length in the image plane only: z is a rough estimate.
    torso = np.linalg.norm((shoulder_center - hip_center)[:, :2], axis=1)
    scale = np.nanpercentile(torso, 90) if not np.isnan(torso).all() else np.nan
    if scale == 0:
        scale = np.nan  # avoid dividing by zero on a broken detection

    normalized = (points - hip_center[:, None, :]) / scale
    return np.concatenate([normalized, keypoints[..., 3:]], axis=-1)
