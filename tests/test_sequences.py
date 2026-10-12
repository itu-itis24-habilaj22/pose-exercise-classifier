import numpy as np

from make_sequences import fill_short_gaps, make_windows


def test_short_gap_is_interpolated():
    features = np.arange(10, dtype=float).reshape(10, 1)
    features[3:5] = np.nan
    np.testing.assert_allclose(fill_short_gaps(features, max_gap=5)[:, 0], np.arange(10))


def test_long_gap_and_edge_gaps_stay_missing():
    features = np.arange(20, dtype=float).reshape(20, 1)
    features[0] = np.nan       # at the start: nothing before it
    features[5:12] = np.nan    # 7 frames: too long
    features[19] = np.nan      # at the end: nothing after it
    filled = fill_short_gaps(features, max_gap=5)
    assert np.isnan(filled[[0, 5, 11, 19], 0]).all()
    assert filled[4, 0] == 4 and filled[12, 0] == 12


def test_window_count_and_shape():
    features = np.arange(100 * 2, dtype=float).reshape(100, 2)
    windows = make_windows(features, length=30, stride=15)
    # starts at 0, 15, 30, 45, 60 (75 would end past frame 100)
    assert windows.shape == (5, 30, 2)
    assert windows[1, 0, 0] == features[15, 0]


def test_windows_with_missing_frames_are_skipped():
    features = np.zeros((60, 2))
    features[5] = np.nan  # only in the first window (frames 0-29)
    windows = make_windows(features, length=30, stride=15)
    assert len(windows) == 2  # starts 15 and 30 survive, 0 is dropped


def test_video_shorter_than_one_window():
    windows = make_windows(np.zeros((10, 2)), length=30, stride=15)
    assert windows.shape == (0, 30, 2)
