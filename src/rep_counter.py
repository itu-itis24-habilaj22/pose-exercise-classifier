"""Count repetitions from a stream of measurements (a joint angle or a body position)."""

# For each exercise: what to measure, and the two thresholds.
# signal "angle": the angle of `joint` in degrees. A rep = it drops below `down`, then
#   rises back above `up` (counted when you're back at the start, e.g. standing up).
# signal "wrist_height": wrists from 0 (hip level) to 1 (shoulder level), see
#   features.wrist_height. A rep = it rises above `up` (counted when the bar reaches the
#   top), after having been below `down`.
# `joint` is also the joint whose visibility check_quality.py checks.
EXERCISES = {
    "squat": {"signal": "angle", "joint": "knee", "down": 100, "up": 160},
    # Push-ups in the dataset often only reach 95-105 deg at the bottom; 110/140 counted
    # 30/30 reps on 5 test videos (90/150 counted 13).
    "pushup": {"signal": "angle", "joint": "elbow", "down": 110, "up": 140},
    # Curls are filmed from the front, where MediaPipe's depth guess is poor: the elbow
    # angle only reached 80-95 deg instead of ~40 (0/11 reps counted). Wrist height is a 2D
    # measurement and counted 11/11 on 5 test videos.
    "curl": {"signal": "wrist_height", "joint": "elbow", "down": 0.3, "up": 0.6,
             "auto_start": True},
}


class RepCounter:
    """Counts reps using two thresholds so small wobbles aren't counted twice.

    A rep is counted when the value rises above `up_angle` after having been below
    `down_angle`. The names come from joint angles, but any measurement works.

    auto_start: if True, the first value decides the starting stage, so a video that
    starts in the middle of a rep (e.g. bar half way up) still counts that rep. If False,
    the counter waits for the value to go below `down_angle` first.
    """

    def __init__(self, down_angle, up_angle, auto_start=False):
        if down_angle >= up_angle:
            raise ValueError("down_angle must be smaller than up_angle")
        self.down_angle = down_angle
        self.up_angle = up_angle
        self.auto_start = auto_start
        self.reset()

    def update(self, angle):
        """Feed the latest value; returns True when a rep has just been completed."""
        if self.stage is None:  # auto_start: first value
            self.stage = "down" if angle < self.up_angle else "up"
        if self.stage == "up" and angle < self.down_angle:
            self.stage = "down"
        elif self.stage == "down" and angle > self.up_angle:
            self.stage = "up"
            self.count += 1
            return True
        return False

    def reset(self):
        self.count = 0
        self.stage = None if self.auto_start else "up"


def make_counter(exercise):
    """A RepCounter set up for one of the EXERCISES."""
    config = EXERCISES[exercise]
    return RepCounter(config["down"], config["up"], config.get("auto_start", False))
