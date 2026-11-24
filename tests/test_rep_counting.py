import pytest

from features import (
    LEFT_HIP,
    LEFT_SHOULDER,
    LEFT_WRIST,
    RIGHT_HIP,
    RIGHT_SHOULDER,
    RIGHT_WRIST,
    calculate_angle,
    wrist_height,
)
from rep_counter import EXERCISES, RepCounter, make_counter


def test_right_angle():
    assert calculate_angle((1, 0), (0, 0), (0, 1)) == pytest.approx(90)


def test_straight_line():
    assert calculate_angle((-1, 0), (0, 0), (1, 0)) == pytest.approx(180)


def test_works_in_3d():
    assert calculate_angle((1, 0, 0), (0, 0, 0), (0, 0, 1)) == pytest.approx(90)


def test_counts_full_reps():
    counter = RepCounter(down_angle=100, up_angle=160)
    # Two squats: stand -> bottom -> stand, twice.
    for angle in [170, 140, 90, 85, 130, 170, 120, 95, 150, 175]:
        counter.update(angle)
    assert counter.count == 2


def test_half_rep_not_counted():
    counter = RepCounter(down_angle=100, up_angle=160)
    for angle in [170, 120, 110, 165]:  # never went below 100
        counter.update(angle)
    assert counter.count == 0


def test_wobble_at_bottom_counts_once():
    counter = RepCounter(down_angle=100, up_angle=160)
    for angle in [170, 95, 105, 95, 110, 98, 170]:
        counter.update(angle)
    assert counter.count == 1


def test_counted_at_the_top_for_rising_signal():
    # Curl wrist height: low -> top counts immediately, before the bar comes back down.
    counter = RepCounter(down_angle=0.3, up_angle=0.6)
    for height in [0.1, 0.4, 0.7]:
        counter.update(height)
    assert counter.count == 1


def test_auto_start_counts_rep_already_under_way():
    # Video starts with the bar half way up (0.5): that lift still counts.
    counter = RepCounter(down_angle=0.3, up_angle=0.6, auto_start=True)
    for height in [0.5, 0.8, 0.9]:
        counter.update(height)
    assert counter.count == 1


def test_auto_start_at_the_top_does_not_count():
    # Video starts with the bar already up: wait for it to come down first.
    counter = RepCounter(down_angle=0.3, up_angle=0.6, auto_start=True)
    for height in [0.9, 0.8, 0.1, 0.9]:
        counter.update(height)
    assert counter.count == 1


def test_reset_restarts_auto_start():
    counter = RepCounter(down_angle=0.3, up_angle=0.6, auto_start=True)
    for height in [0.1, 0.9]:
        counter.update(height)
    counter.reset()
    assert counter.count == 0 and counter.stage is None


def test_every_exercise_has_a_working_counter():
    for exercise in EXERCISES:
        assert make_counter(exercise).count == 0


class Point:
    def __init__(self, y, visibility=1.0):
        self.x, self.y, self.z, self.visibility = 0.5, y, 0.0, visibility


def make_landmarks(wrist_y, shoulder_y=0.3, hip_y=0.6):
    points = [Point(0.5) for _ in range(33)]
    for i in (LEFT_WRIST, RIGHT_WRIST):
        points[i] = Point(wrist_y)
    for i in (LEFT_SHOULDER, RIGHT_SHOULDER):
        points[i] = Point(shoulder_y)
    for i in (LEFT_HIP, RIGHT_HIP):
        points[i] = Point(hip_y)
    return points


def test_wrist_height_hips_is_0_shoulders_is_1():
    assert wrist_height(make_landmarks(wrist_y=0.6))[0] == pytest.approx(0)
    assert wrist_height(make_landmarks(wrist_y=0.3))[0] == pytest.approx(1)
    assert wrist_height(make_landmarks(wrist_y=0.45))[0] == pytest.approx(0.5)


def test_wrist_height_does_not_depend_on_distance():
    # Same pose, person twice as far away (half the size in the image).
    near = wrist_height(make_landmarks(wrist_y=0.4, shoulder_y=0.3, hip_y=0.6))[0]
    far = wrist_height(make_landmarks(wrist_y=0.45, shoulder_y=0.4, hip_y=0.55))[0]
    assert near == pytest.approx(far)
