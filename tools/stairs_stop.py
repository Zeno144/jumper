"""Climb `dirty_stairs` and stop on the landing: a `--command-script` for play.py.

Walk straight ahead, ease to a stop, then stand. Time-based, because a command
script sees only `t`: the stop is placed by distance at the measured speed.

The landing spans x 1.66 to 2.46 m from the spawn (`scenes/dirty_stairs.py`).
`model_13098.pt` (the stairs fine-tune) ran 0.22 to 0.32 m/s up the steps at a
0.25 m/s command, native CPU backend, so `WALK` aims the stop at about x = 2.0 m
and leaves the landing's 0.4 m either side for take-to-take variation (play.py
has no `--seed`).

    play.py --task jumper.tripod --scene dirty_stairs --headless --backend native
      --device cpu --steps 525 --command-script tools/stairs_stop.py --video ...
"""

from __future__ import annotations

SPEED = 0.25
RAMP = 0.4
WALK = 7.4
STOP = 0.6


def script(t: float) -> dict[str, list[float]]:
    if t < RAMP:
        vx = SPEED * t / RAMP
    elif t < WALK:
        vx = SPEED
    elif t < WALK + STOP:
        vx = SPEED * (1.0 - (t - WALK) / STOP)
    else:
        vx = 0.0
    return {"twist": [vx, 0.0, 0.0]}
