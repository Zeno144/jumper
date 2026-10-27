"""A short flight of dirty steps for the cleaning concept: climb, sweep, arrive.

**This scene is physical** -- it adds props, so `apply` warns -- and it is meant
for replay, not training. It is `dirty_floor` with a staircase in the field: the
same crumbs, the same brush channel and the same pinned spawn, all taken from
that module rather than copied, so the two scenes cannot drift apart.

## Steps at this robot's size, not a house's

A household riser is about 0.17 m and this robot stands 0.106 m tall, so a real
staircase is a wall to it. The steps here are sized from `scenes/rough.py`'s
`pyramid_stairs` column, which is what the stairs fine-tune trains on: a tread of
`0.30 * H_SCALE` (0.264 m, so the 0.331 m stance straddles 1.25 treads) and a
riser a policy can actually reach. `RISER` is the one number to move per take:
`jumper.tripod`'s 0.025 m foot-lift target clears terrain level 4, whose steps
are 0.021 m, and that is the ceiling this scene starts under.

The staircase is one fixed-base prop of stacked blocks, each running from its
own step edge to the far end of the landing, so there is no gap under any tread
for a foot to find. Its geoms keep MuJoCo's default collision bit, which is the
ground channel the feet collide on (`constants.py`, "Collision masks").

## The crumbs

Spread over the approach floor, every tread and the landing, each sitting on the
surface below it. Positions come from a fixed seed, as in `dirty_floor`.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from . import dirty_floor, studio
from .registry import Scene

#: Height of each step. See the module docstring for why it starts here.
RISER = 0.02

N_STEPS = 4

#: `rough.py`'s tread: `0.30 * H_SCALE`.
TREAD = 0.264

#: Where the first riser stands, ahead of the pinned spawn. Far enough for the
#: robot to reach walking speed and for the brush to work the floor first.
STAIR_X0 = 0.60

LANDING = 0.80
WIDTH = 0.90

#: Two stone tones, alternated per step so every edge reads on camera.
STEP_RGBA = ((0.82, 0.78, 0.72, 1.0), (0.76, 0.72, 0.66, 1.0))

N_FLOOR_CRUMBS = 30
N_TREAD_CRUMBS = 14
N_LANDING_CRUMBS = 30
SEED = 2026

#: Crumbs keep this far from a riser, so none is spawned straddling an edge.
EDGE_CLEAR = 0.02


def _x_end() -> float:
    return STAIR_X0 + N_STEPS * TREAD + LANDING


def _stairs_spec() -> Any:
    import mujoco

    spec = mujoco.MjSpec()
    body = spec.worldbody.add_body(name="stairs", pos=[0.0, 0.0, 0.0])
    x_end = _x_end()
    for i in range(N_STEPS):
        x0 = STAIR_X0 + i * TREAD
        body.add_geom(
            name=f"step_{i}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=[(x0 + x_end) / 2, 0.0, (i + 0.5) * RISER],
            size=[(x_end - x0) / 2, WIDTH / 2, RISER / 2],
            rgba=list(STEP_RGBA[i % 2]),
            group=2,
        )
    return spec


def _stairs() -> Any:
    from mjlab.entity import EntityCfg

    return EntityCfg(
        spec_fn=_stairs_spec,
        init_state=EntityCfg.InitialStateCfg(pos=(0.0, 0.0, 0.0)),
    )


def _patches() -> list[tuple[int, tuple[float, float], float, float]]:
    """(count, x range, surface height, y half-width) per surface that gets crumbs."""
    y = WIDTH / 2 - EDGE_CLEAR
    patches = [(N_FLOOR_CRUMBS, (dirty_floor.FIELD_X[0], STAIR_X0 - EDGE_CLEAR), 0.0, y)]
    for i in range(N_STEPS):
        x0 = STAIR_X0 + i * TREAD
        patches.append((N_TREAD_CRUMBS, (x0 + EDGE_CLEAR, x0 + TREAD - EDGE_CLEAR),
                        (i + 1) * RISER, y))
    x0 = STAIR_X0 + N_STEPS * TREAD
    patches.append((N_LANDING_CRUMBS, (x0 + EDGE_CLEAR, _x_end() - EDGE_CLEAR),
                    N_STEPS * RISER, y))
    return patches


def _crumbs() -> dict[str, Any]:
    from mjlab.entity import EntityCfg

    rng = np.random.default_rng(SEED)
    props: dict[str, Any] = {}
    i = 0
    for count, x_range, z0, y_half in _patches():
        # The floor patch keeps `dirty_floor`'s narrower lane; the steps span
        # their whole width, which is what a sweep up the middle leaves behind.
        y_range = dirty_floor.FIELD_Y if z0 == 0.0 else (-y_half, y_half)
        for _ in range(count):
            name = f"dirt_{i:03d}"
            i += 1
            x, y = rng.uniform(*x_range), rng.uniform(*y_range)
            half = (rng.uniform(*dirty_floor.HALF_X), rng.uniform(*dirty_floor.HALF_Y),
                    rng.uniform(*dirty_floor.HALF_Z))
            rgba = (*dirty_floor.COLOURS[rng.integers(len(dirty_floor.COLOURS))], 1.0)
            yaw = rng.uniform(-math.pi, math.pi)
            pos = (x, y, z0 + half[2])
            quat = (math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2))
            props[name] = EntityCfg(
                spec_fn=lambda name=name, pos=pos, quat=quat, half=half, rgba=rgba:
                    dirty_floor._crumb_spec(name, pos, quat, half, rgba),
                init_state=EntityCfg.InitialStateCfg(pos=pos, rot=quat),
            )
    return props


def n_crumbs() -> int:
    return sum(p[0] for p in _patches())


def scene() -> Scene:
    base = dirty_floor.scene()
    n = n_crumbs()
    return Scene(
        headlight=studio.scene().headlight,
        textures=base.textures,
        materials=base.materials,
        lights=base.lights,
        # `dirty_floor`'s per-crumb budget, plus the robot's footholds on the
        # steps, which are boxes rather than the plane.
        nconmax=128 + 8 * n,
        njmax=512 + 32 * n,
        events={"face_forward": dirty_floor._face_forward()},
        decorate=dirty_floor._brush_collides_with_dirt,
        props={"stairs": _stairs(), **_crumbs()},
    )

