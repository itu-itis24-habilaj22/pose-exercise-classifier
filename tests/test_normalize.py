import numpy as np
import pytest

from features import LEFT_HIP, LEFT_SHOULDER, RIGHT_HIP, RIGHT_SHOULDER, normalize_keypoints


def make_pose(offset, scale):
    """A simple standing pose, moved by `offset` and scaled by `scale`."""
    pose = np.zeros((1, 33, 4))
    pose[0, :, 3] = 1.0  # visibility
    pose[0, LEFT_HIP, :2] = [-0.05, 0.0]
    pose[0, RIGHT_HIP, :2] = [0.05, 0.0]
    pose[0, LEFT_SHOULDER, :2] = [-0.07, -0.3]
    pose[0, RIGHT_SHOULDER, :2] = [0.07, -0.3]
    pose[0, :, :2] = pose[0, :, :2] * scale + offset
    return pose


def test_same_pose_anywhere_gives_same_result():
    near_left = normalize_keypoints(make_pose(offset=[0.3, 0.6], scale=2.0))
    far_right = normalize_keypoints(make_pose(offset=[0.7, 0.4], scale=0.5))
    np.testing.assert_allclose(near_left, far_right)


def test_hips_centered_and_torso_is_one_unit():
    result = normalize_keypoints(make_pose(offset=[0.5, 0.5], scale=1.0))
    hip_center = (result[0, LEFT_HIP, :3] + result[0, RIGHT_HIP, :3]) / 2
    shoulder_center = (result[0, LEFT_SHOULDER, :3] + result[0, RIGHT_SHOULDER, :3]) / 2
    np.testing.assert_allclose(hip_center, 0, atol=1e-12)
    assert np.linalg.norm(shoulder_center[:2]) == pytest.approx(1.0)


def test_missing_frames_stay_missing():
    keypoints = np.full((2, 33, 4), np.nan)
    assert np.isnan(normalize_keypoints(keypoints)).all()
