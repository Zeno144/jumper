"""A lawnmower sweep over `scenes/dirty_floor`'s field, as a command script.

    python scripts/play.py --task jumper.tripod --scene dirty_floor --headless \\
        --backend native --device cpu --steps 1750 \\
        --command-script tools/sweep.py --video sweep.mp4

**Use the native backend for this scene.** With one environment and
`dirty_floor`'s 120 free crumbs, warp replays at 1.2 frames a second against 17
on native (200 steps: 178 s against 23 s, RTX 5060 Ti, 2026-10-19), so the
whole sweep takes about 110 s on native and 18 min on warp. The contact budget
is not the cause: a smaller `njmax` was slower still, and overflowed.

Three lanes along +x, joined by turns on the spot, so the brush on the robot's
head always leads -- walking a lane backwards would drag it behind the body,
where the legs have already been. The robot starts at the origin facing +x,
which `dirty_floor` pins; the lanes are spaced to the field's width there.

The script is **open loop**: it is a function of time and nothing else, so the
robot's actual heading after a turn is whatever the policy delivered. The turns
therefore stay inside the yaw rate the checkpoint was trained on (`jumper.tripod`
saved +/-0.75 rad/s at its top curriculum rung) rather than near its edge, where
tracking is loosest and the error would carry into every lane after it.

Each segment is `(seconds, vx, vy, yaw_rate)` in the body frame, and the command
eases between segments over `RAMP` seconds rather than stepping, because a step
in the command is a jolt in the gait that the camera sees.
"""

from __future__ import annotations

import math

#: Forward speed along a lane and between lanes, m/s.
LANE_SPEED = 0.30
LINK_SPEED = 0.25
#: Turn rate on the spot, rad/s, and the time a quarter turn takes at it.
#: The heading keeps moving for about a second after a turn command ends, so
#: each turn is followed by `SETTLE`, and `TURN_GAIN` trims the 2-3 degrees each
#: turn still overshot (92.4, 89.7, 92.7, 92.5 at gain 1.0). Over three seeds at
#: 0.975 (`jumper.tripod` model_10099 on `dirty_floor`, native backend,
#: 2026-10-19) lane 3 ran at -5.0, +2.7 and +2.1 degrees: the replay's own
#: randomisation moves each turn by about 4 degrees, so this is the centre of
#: that spread, not a value that lands on 90 every run.
TURN_RATE = 0.60
TURN_GAIN = 0.975
QUARTER = TURN_GAIN * (math.pi / 2) / TURN_RATE

#: Lane length and spacing, metres. The field runs x 0.25..1.60 and y +/-0.35;
#: the brush sits about 0.15 m ahead of the body origin.
LANE = 1.35
SPACING = 0.25

#: Seconds over which the command blends from one segment into the next.
RAMP = 0.4
#: Seconds stood still after each turn, so the heading settles before walking.
SETTLE = 1.0
#: Seconds added to each link walk for the robot getting up to speed from a
#: stand: without it the links covered 0.19 of 0.25 m and 0.44 of 0.50 m.
LINK_LAG = 0.24

_FORWARD = LANE / LANE_SPEED
_LINK = SPACING / LINK_SPEED + LINK_LAG

#: Lane 1 out along y = 0, a left U to lane 2 back along y = +SPACING, then a
#: left U across both to lane 3 out along y = -SPACING.
SEGMENTS: tuple[tuple[float, float, float, float], ...] = (
    (1.0, 0.0, 0.0, 0.0),                     # settle
    (_FORWARD, LANE_SPEED, 0.0, 0.0),          # lane 1, +x
    (QUARTER, 0.0, 0.0, TURN_RATE),            # face +y
    (SETTLE, 0.0, 0.0, 0.0),
    (_LINK, LINK_SPEED, 0.0, 0.0),
    (QUARTER, 0.0, 0.0, TURN_RATE),            # face -x
    (SETTLE, 0.0, 0.0, 0.0),
    (_FORWARD, LANE_SPEED, 0.0, 0.0),          # lane 2, -x
    (QUARTER, 0.0, 0.0, TURN_RATE),            # face -y
    (SETTLE, 0.0, 0.0, 0.0),
    (2 * _LINK, LINK_SPEED, 0.0, 0.0),
    (QUARTER, 0.0, 0.0, TURN_RATE),            # face +x
    (SETTLE, 0.0, 0.0, 0.0),
    (_FORWARD, LANE_SPEED, 0.0, 0.0),          # lane 3, +x
    (60.0, 0.0, 0.0, 0.0),                     # stand
)

DURATION = sum(s[0] for s in SEGMENTS[:-1])


def _at(t: float) -> tuple[float, float, float]:
    start = 0.0
    for seconds, *command in SEGMENTS:
        if t < start + seconds:
            return tuple(command)
        start += seconds
    return tuple(SEGMENTS[-1][1:])


def script(t: float) -> dict[str, list[float]]:
    """`play.py --command-script` calls this with seconds since the replay began."""
    # Blend over the window that ends at t: a moving average of the step
    # function, which is a linear ramp across every boundary.
    n = 8
    samples = [_at(max(0.0, t - RAMP * k / (n - 1))) for k in range(n)]
    return {"twist": [sum(c[i] for c in samples) / n for i in range(3)]}
