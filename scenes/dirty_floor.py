"""A dirty floor for the cleaning concept: crumbs the robot walks through.

**This scene is physical** -- it adds props, so `apply` warns -- and it is meant
for replay, not training. The crumbs are free bodies with mass and they collide,
so a policy trained among them would not be comparable to one trained without.

## What pushes the crumbs

Two things: the feet and legs, through the ordinary collision channel (bit 0),
and the brush on the robot's head, through a private one (`DIRT_BIT`).

The brush in `assets/jumper/jumper.xml` is visual only, `contype=0`, and it stays
that way in the asset: training strips non-colliding geoms and must keep doing so.
`decorate` gives the bristles `DIRT_BIT` on this scene alone, after the robot has
been attached, so the brush collides with crumbs and with nothing else -- not the
floor, not the robot's own legs. With no crumbs in the world it touches nothing,
which is why selecting this scene changes the robot's own contacts not at all.

Same mask arithmetic as `football.BALL_BIT`: MuJoCo collides two geoms when
`(contype1 & conaffinity2) || (contype2 & conaffinity1)`, so

    bristles  contype = DIRT_BIT         conaffinity = DIRT_BIT
    crumb     contype = 1 | DIRT_BIT     conaffinity = 1 | DIRT_BIT

puts bristles against crumbs on `DIRT_BIT` and crumbs against floor and feet on
bit 0, while bristles against anything else shares no bit.

## Where the robot starts, and where the crumbs are

**This scene pins the spawn**: at its environment origin, facing +x. mjlab's
`reset_base` draws the robot's position from +/-0.5 m and its yaw from the whole
circle, so without the pin "ahead of the robot" is a different patch of floor
every episode. The first layout here was a ring all round the spawn point for
that reason, and it did not work: measured over 5 s at 0.25 m/s, 3 of 80 crumbs
moved more than 1 cm, because a ring puts most of the dirt where the robot is
not going. A scene cannot narrow the task's `reset_base` (`apply_scene` refuses
to replace a task's event), so `face_forward` is a second reset term that runs
after it and puts the robot back at the origin -- what `jumper.five_foot` gets
by narrowing the range, done by adding instead.

The crumbs are a field ahead of that spawn, `FIELD_X` by `FIELD_Y`, which is
where a forward walk and a back-and-forth sweep both go. Positions come from a
fixed seed, so every run starts from the same mess and clips can be compared.
Like any prop, every crumb returns to its spot at each episode reset
(`registry._place_props`).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from . import studio
from .registry import GROUND, Scene

#: The collision channel the brush and the crumbs share. Distinct from
#: `football.BALL_BIT`, though the two scenes are never selected together.
DIRT_BIT = 1 << 11

#: The bristles' geom name in the robot asset. Matched as a suffix, because the
#: attached robot's geoms carry its entity prefix.
BRISTLES = "brush_bristles"

N_CRUMBS = 120
SEED = 2026

#: The field, in the spawn's frame: ahead of the robot, centred on its line. Its
#: near edge clears the front legs at spawn.
FIELD_X = (0.25, 1.60)
FIELD_Y = (-0.35, 0.35)

#: Crumb half-sizes. The bristles' lower face hangs 4 to 7 mm above the floor
#: while walking (two replays of `jumper.tripod` at 0.25 m/s, RTX 5060 Ti: mean
#: 4.1 and 6.6 mm, dipping to -0.7 and 2.9 mm), so a crumb has to be taller than
#: that for the brush to reach it at all: half-heights from 4 mm give 8 mm and up. Footprints of 1.6 to 3.2 cm are what still read on camera
#: at a whole-robot framing; half that, the first try, was specks.
HALF_X = (0.008, 0.016)
HALF_Y = (0.006, 0.012)
HALF_Z = (0.004, 0.007)

#: A gram or two: enough to sit still on the floor, light enough that a foot or
#: the brush moves it without the robot noticing.
CRUMB_MASS = 0.004

#: Dark against the floor below: soil, dust and the odd dry leaf.
COLOURS = (
    (0.16, 0.13, 0.10),
    (0.24, 0.18, 0.12),
    (0.30, 0.29, 0.28),
    (0.55, 0.34, 0.14),
)


def _crumb_spec(name: str, pos: tuple[float, float, float], quat: tuple[float, ...],
                half: tuple[float, float, float],
                rgba: tuple[float, float, float, float]) -> Any:
    import mujoco

    spec = mujoco.MjSpec()
    # The body carries the crumb's spot as well as `init_state`, because a free
    # joint's `qpos0` is the body's spec pose and the model is first put on the
    # device in that pose, before any reset event has run. Left at the origin,
    # all the crumbs start inside one another and inside the robot -- measured:
    # `nconmax must be >= 4922` at construction.
    body = spec.worldbody.add_body(name=name, pos=list(pos), quat=list(quat))
    body.add_freejoint()
    body.add_geom(
        name=name,
        type=mujoco.mjtGeom.mjGEOM_BOX,
        size=list(half),
        mass=CRUMB_MASS,
        rgba=list(rgba),
        friction=[0.6, 0.005, 0.0001],
        contype=1 | DIRT_BIT,
        conaffinity=1 | DIRT_BIT,
        group=2,
    )
    return spec


def _crumbs() -> dict[str, Any]:
    from mjlab.entity import EntityCfg

    rng = np.random.default_rng(SEED)
    props: dict[str, Any] = {}
    for i in range(N_CRUMBS):
        name = f"dirt_{i:02d}"
        x, y = rng.uniform(*FIELD_X), rng.uniform(*FIELD_Y)
        half = (rng.uniform(*HALF_X), rng.uniform(*HALF_Y), rng.uniform(*HALF_Z))
        rgba = (*COLOURS[rng.integers(len(COLOURS))], 1.0)
        yaw = rng.uniform(-math.pi, math.pi)
        pos = (x, y, half[2])
        quat = (math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2))
        props[name] = EntityCfg(
            # Default arguments bind this iteration's values; a bare closure would
            # give every crumb the last one's.
            spec_fn=lambda name=name, pos=pos, quat=quat, half=half, rgba=rgba:
                _crumb_spec(name, pos, quat, half, rgba),
            init_state=EntityCfg.InitialStateCfg(pos=pos, rot=quat),
        )
    return props


def _face_forward() -> Any:
    """A reset term that undoes `reset_base`'s position and yaw -- see the module
    docstring. An empty `pose_range` puts the robot at its `init_state` plus the
    environment origin, which is the origin, upright, facing +x. It runs after
    `reset_base` because scene events are merged after the task's."""
    from mjlab.envs.mdp import events as mdp_events
    from mjlab.managers.event_manager import EventTermCfg
    from mjlab.managers.scene_entity_config import SceneEntityCfg

    return EventTermCfg(
        func=mdp_events.reset_root_state_uniform,
        mode="reset",
        params={"pose_range": {}, "velocity_range": {},
                "asset_cfg": SceneEntityCfg("robot")},
    )


def _brush_collides_with_dirt(spec: Any) -> None:
    hits = 0
    for geom in spec.geoms:
        if (geom.name or "").endswith(BRISTLES):
            geom.contype = DIRT_BIT
            geom.conaffinity = DIRT_BIT
            hits += 1
    if not hits:
        raise RuntimeError(
            f"scene 'dirty_floor' found no geom ending in {BRISTLES!r}; this robot "
            f"has no brush, and the crumbs would only ever be moved by the feet."
        )


def scene() -> Scene:
    from mjlab.utils import spec_config as sc

    # The studio's lights and ambient, on a warm light floor instead of its grey
    # one: dark crumbs and a white-and-blue robot both read against it.
    base = studio.scene()
    return Scene(
        headlight=base.headlight,
        textures=(
            sc.TextureCfg(
                name="dirty_floor", type="2d", builtin="checker", mark="edge",
                rgb1=(0.74, 0.66, 0.55), rgb2=(0.70, 0.62, 0.51),
                markrgb=(0.60, 0.53, 0.44), width=512, height=512,
            ),
            *(t for t in base.textures if t.type == "skybox"),
        ),
        materials=(
            sc.MaterialCfg(
                name="dirty_floor", texture="dirty_floor", texuniform=True,
                texrepeat=(6.0, 6.0), reflectance=0.0, geom_names_expr=GROUND,
            ),
        ),
        lights=base.lights,
        # A crumb lying on the floor is up to four contacts, and swept crumbs
        # pile against each other, so allow eight each. The robot's own budget
        # is 128 contacts and 512 constraint rows (`velocity_env.py`).
        nconmax=128 + 8 * N_CRUMBS,
        njmax=512 + 32 * N_CRUMBS,
        events={"face_forward": _face_forward()},
        decorate=_brush_collides_with_dirt,
        props=_crumbs(),
    )
