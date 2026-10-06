import pytest

from features import calculate_angle
from rep_counter import RepCounter


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
