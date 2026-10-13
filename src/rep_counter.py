"""Count repetitions from a stream of joint angles."""

# For each exercise: which joint to track, and the angle thresholds.
# A rep = angle drops below `down_angle`, then rises back above `up_angle`.
EXERCISES = {
    "squat": {"joint": "knee", "down_angle": 100, "up_angle": 160},
    # Push-ups in the dataset often only reach 95-105 deg at the bottom; 110/140 counted
    # 30/30 reps on 5 test videos (90/150 counted 13).
    "pushup": {"joint": "elbow", "down_angle": 110, "up_angle": 140},
    "curl": {"joint": "elbow", "down_angle": 50, "up_angle": 150},
}


class RepCounter:
    """Counts reps using two thresholds so small wobbles aren't counted twice."""

    def __init__(self, down_angle, up_angle):
        if down_angle >= up_angle:
            raise ValueError("down_angle must be smaller than up_angle")
        self.down_angle = down_angle
        self.up_angle = up_angle
        self.count = 0
        self.stage = "up"

    def update(self, angle):
        """Feed the latest angle; returns True when a rep has just been completed."""
        if self.stage == "up" and angle < self.down_angle:
            self.stage = "down"
        elif self.stage == "down" and angle > self.up_angle:
            self.stage = "up"
            self.count += 1
            return True
        return False

    def reset(self):
        self.count = 0
        self.stage = "up"
