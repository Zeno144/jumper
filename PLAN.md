# Jumper Crab Robot Challenge 2026 — Cleaning Concept Plan

**Target post date:** October 25, 2026 (Round 1 deadline October 30)
**Concept:** Jumper cleans a floor with a brush mounted on its head — a simulation concept, not a finished feature.

---

## What this repo can and cannot do today

**Can do:**
- Train locomotion policies (tripod, flat, ripple, tetrapod, posture, jump, dance, gestures, and more)
- Replay a trained policy headlessly and record a 1080p MP4 at 30 or 60 fps with one command
- Load a `.map` scene from the companion jumper-design repo for replay (but not for training)
- Add visual-only geometry to `assets/jumper/jumper.xml` — cylinders, boxes, spheres attached to any body
- Show the robot in MuJoCo simulation with lighting, shadows, and studio/daylight/beach scenes
- Change body colors directly in the XML (`rgba=` on any geom)

**Cannot do (relevant to this project):**
- Load `.skin` files into the training environment (skins are display-only in the separate design repo)
- Train on custom maps — only the built-in scenes work for training
- Simulate real dirt accumulation, wet trails, or surface texture changes natively (MuJoCo does not model surface contamination)
- Add a new *actuated* joint to the head without rebuilding from URDF — the head/display module is rigidly attached (but we can add a passive visual-only child body)
- Enable the GPU (warp:cuda) backend without first installing MSVC Build Tools on this Windows machine (see GPU note below)

**GPU note:** ✅ MSVC Build Tools installed Oct 15. `torch.cuda.is_available()` = True. GPU training active at ~2.7 s/iter.

---

## Day-by-day schedule (Oct 15 – Oct 25)

### Day 1 — Oct 15 ✅ COMPLETE
- [x] Install Python venv (3.12.10), PyTorch cu128, all repo dependencies
- [x] Run all four gates: Warp `cuda:0`, MuJoCo 3.11.0, vendored copies confirmed, 18 tasks registered
- [x] Smoke test: 5-iteration GPU training confirmed the pipeline
- [x] 300-iteration CPU training completed → `logs/jumper/jumper.tripod/2026-10-15_22-09-57/model_299.pt`
- [x] 10-second test clip recorded → `test_clip.mp4` (1920×1080, 30fps, 301 frames, 909 KB)
- [x] MSVC Build Tools installed → GPU backend enabled
- [x] Fixed PyTorch: `pip install -e .` had silently overwritten cu128 with the CPU build from
  PyPI; reinstalled cu128, then pinned tensordict to 0.11.0 (0.15.0 requires torch≥2.13.0
  but cu128 index tops out at 2.11.0)
- [x] Full GPU overnight training started: `warp:cuda`, 4096 envs, ~2.7 s/iter, ETA ~8 h
  → log dir `logs/jumper/jumper.tripod/2026-10-15_23-19-10/`
- [x] That run died at iter ~117 (console window closed: `forrtl: error (200) ... window-CLOSE
  event`). Resumed from `model_100.pt` as a hidden detached process (`Start-Process
  -WindowStyle Hidden`), target now 10 100 iterations; old logs kept as `train_gpu_*_run1.txt`.
  Launch long runs detached so closing a terminal cannot kill them.

### Day 2 — Oct 16: Brush mesh + check training
- [ ] Check overnight training progress:
  ```powershell
  Get-Content .\train_gpu_stdout.txt | Select-String "Iteration time|ETA" | Select-Object -Last 4
  ```
- [ ] Add a brush/mop geom to `assets/jumper/jumper.xml` attached to the `display_module_link`
  body (front face of the robot at approximately x=0.08, z=0.05 relative to base). A
  simple cylinder pointing down works. No new joint needed — it is purely visual.
- [ ] Pick a skin color scheme for the "cleaning bot" look (see Skin section below)

### Day 3 — Oct 17: Dirt particles + scene
- [ ] Add a set of flat colored discs ("dirt patches") as free-floating passive bodies in
  a new custom scene XML — small cylinders resting on the floor that the robot walks through
  and scatters. These use MuJoCo's free joint so they react to contact without affecting
  the policy at all.
- [ ] Choose a scene. Recommendation: **studio** (neutral grey, makes the robot and dirt
  patches pop on camera) or a custom flat floor with a light tile texture.
- [ ] Test that the dirt patches scatter when the robot crosses them.

### Day 4 — Oct 18: Sweep pattern scripting
- [ ] Write a `--command-script` file (a small Python function of time `t`) that drives the
  robot in a back-and-forth sweeping pattern: move forward, turn 180°, move back, repeat.
  This does not require retraining — `play.py --command-script sweep.py` injects the command
  directly into the replay.
- [ ] Test the sweep looks natural and covers the dirt patches.

### Day 5 — Oct 19: Full gait checkpoint check + retrain if needed
- [ ] Evaluate the overnight checkpoint. If the gait is solid, proceed to filming.
  If not, let it keep running while you film earlier sections.
- [ ] Quick evaluation check:
  ```powershell
  .venv\Scripts\python.exe scripts/play.py --task jumper.tripod --headless `
    --steps 1000 --video gait_check.mp4 `
    --video-width 1920 --video-height 1080 --video-fps 30
  ```

### Day 6 — Oct 20: Filming day 1 — individual shots
- [ ] Shot 1 (hook): robot walks into frame and the brush sweeps a dirty floor — 3 s
- [ ] Shot 2: wide overhead angle showing the full sweep pattern — 8 s
- [ ] Shot 3: close-up of the brush and the dirt patches scattering — 5 s
- [ ] Shot 4: side-view of the tripod gait in action — 5 s

### Day 7 — Oct 21: "Building it with Claude Code" screen capture
- [ ] Record a 15–20 second screen capture of the Claude Code session: show a funny failed
  attempt (the OOM crash with 2048 envs on CPU, or the GPU backend refusing without MSVC),
  then the fix, then the training progress.
- [ ] This is the "sharing ideas, debugging and funny setbacks" element the judges reward.

### Day 8 — Oct 22: Video assembly
- [ ] Assemble the shots in order using a free editor (DaVinci Resolve is free on Windows).
  Total target: 65–75 seconds.
- [ ] Add original sound: robot servo sounds (can be synthesized from a short click/buzz loop),
  or record yourself explaining what you built in one sentence as a voiceover.
  No third-party music needed.
- [ ] Add captions for key moments (what the robot is doing, what task it's doing).

### Day 9 — Oct 23: GitHub setup
- [x] Fork exists at `https://github.com/Zeno144/jumper`; remotes configured Oct 16 (see
  "Git layout" below). Push to the `work` branch, not `main`.
- [ ] Write a short README section "Cleaning concept" — what the brush attachment is, how to
  run it, the one training command, the one record command.
- [ ] Push the XML change (brush attachment) and the sweep.py script as a single commit.

### Day 10 — Oct 24: YouTube upload + post
- [ ] Upload the video to YouTube as Public.
- [ ] Title, description and tags (see below).
- [ ] Post the link on the challenge platform. Done by Oct 25.

### Buffer — Oct 25: Contingency
- [ ] If anything slipped, finish and post today.

---

## How to attach the cleaning brush to jumper.xml

The robot's front face is the `display_module_link` body at position ~(0.08, 0, 0.05)
relative to `base_link`. Add a visual-only child body there with a cylinder geom pointing
downward. No new joint, no physics interaction, no retraining required.

**Add inside the `display_module_link` body block** in `assets/jumper/jumper.xml`:

```xml
<body name="brush_mount" pos="0 0 -0.02">
  <!-- The stem -->
  <geom name="brush_stem" class="visual" type="cylinder"
        fromto="0 0 0 0 0 -0.04" size="0.005"
        rgba="0.6 0.4 0.2 1"/>
  <!-- The brush head -->
  <geom name="brush_head" class="visual" type="cylinder"
        fromto="0 0 -0.04 0 0 -0.05" size="0.025"
        rgba="0.85 0.85 0.85 1"/>
</body>
```

The brush hangs below the display face. Adjust `pos` and `fromto` to get it close to the
floor in the standing pose — Jumper stands at about z=0.14 m (the `STAND_Z` constant in
`tasks/jumper/common/constants.py`), so the brush tip at approximately z = 0.14 - 0.05 = 0.09
from base will hover about 5 cm above the floor and sweep close when the body bobs downward.

**Head tilting:** The `display_module_link` is rigidly attached — there is no actuated joint
for it. To press the brush against the floor the robot's whole body would need to lower,
which the posture task (`jumper.posture`) controls via a height command. You can replay the
`jumper.posture` policy with a reduced height command to make the body crouch, bringing the
brush into contact with the floor. This is simpler than adding a new joint (which would
require rebuilding from URDF and potentially retraining if the new geometry interferes with
contact).

---

## Making cleaning visible on camera

The simulator doesn't model dirt. Three options, ranked easiest to hardest:

### Option A — Dirt patches (recommended)
Create a custom scene file `assets/scenes/sweep_floor.xml` that includes 15–20 small
flat cylinders placed on the floor as "dirt patches" (dark grey or brown). Give them
`mass="0.001"` and a `free` joint so they get pushed aside on contact. They are passive and
do not affect the training policy. The robot walking through them produces satisfying
scattering that reads clearly on camera.

```xml
<!-- example dirt patch, repeat with varied positions -->
<body name="dirt_0" pos="0.5 0.1 0.002">
  <joint type="free"/>
  <geom type="cylinder" size="0.015 0.002" rgba="0.3 0.2 0.1 1"
        mass="0.001" friction="0.1 0.005 0.005"/>
</body>
```

### Option B — Floor grid texture
Add a grid or chessboard floor material where alternate tiles are "dirty" (darker color).
The robot's path changes nothing, but it reads as sweeping a patterned floor. Works well for
a static shot where the camera is above.

### Option C — Trail geom (complex)
Programmatically add or remove floor geoms in Python by writing a custom `ReplayVideo`
subclass that drops new white cylinder "clean patches" behind the robot on each step. This
takes a full day to build and is the fallback if A and B do not look good enough.

**Recommendation for Oct 25 deadline:** Use Option A for the main shot, Option B as a
quick alternative if Option A's physics look unstable.

---

## Scene recommendation

**Primary: `studio`** — neutral grey floor, key + fill lights, dark sky. It makes colors
pop and is what the README screenshots use. The dirt patches contrast well against it.

**Alternative: `daylight`** — warm sun and shadows. More cinematic but the patches may
be less readable.

**Custom map:** The jumper-design repo has a `bedroom` map which would be thematically
perfect for a cleaning robot. To use it for replay:
```powershell
# Clone the design repo first (separate checkout, separate venv)
python scripts/play.py --task jumper.tripod `
  --scene ..\jumper-design\outputs\bedroom.map `
  --headless --steps 600 --video bedroom_clean.mp4 `
  --video-width 1920 --video-height 1080
```
Note: `train.py` refuses imported maps. Use the bedroom map only for recording, not training.
This adds a day of setup for the design repo checkout — treat it as a nice-to-have.

---

## Sweep motion

The `jumper.tripod` policy responds to velocity commands `(vx, vy, yaw)`. A back-and-forth
sweep pattern is a command script (no retraining). Create `scripts/sweep.py`:

```python
def script(t):
    """Back-and-forth sweeping command."""
    period = 4.0          # seconds per sweep pass
    phase = (t % period) / period
    if phase < 0.45:
        vx = 0.4          # forward
    elif phase < 0.55:
        vx = 0.0          # pause and turn
    elif phase < 1.0:
        vx = -0.4         # backward
    else:
        vx = 0.0
    yaw = 0.0
    if 0.45 <= phase <= 0.55:
        yaw = 1.5         # turn around
    return {"twist": [vx, 0.0, yaw]}
```

Run it with:
```powershell
.venv\Scripts\python.exe scripts/play.py --task jumper.tripod `
  --headless --steps 1200 --video sweep.mp4 `
  --command-script scripts/sweep.py `
  --video-width 1920 --video-height 1080 --video-fps 30
```

---

## Skin / appearance

A new skin requires the separate `jumper-design` repo and is display-only (cannot be
imported into training). For the contest video, changing the robot's color in the XML is
faster and permanent:

**Cleaning robot color scheme** (in `assets/jumper/jumper.xml`):
- Body shell (`upper_shell_link`): bright white `rgba="0.95 0.95 0.95 1"` — clean, clinical
- Shoulders + thighs: light teal `rgba="0.3 0.7 0.65 1"` — friendly, original
- Calves: white `rgba="0.95 0.95 0.95 1"`
- Display module: keep black, but add a small green geom "indicator light" for character

This is 100% original and does not reference any existing characters or brands. The white +
teal combination reads as a cleaning appliance (like a robot vacuum) without copying any
specific product's design.

**Fallback:** Leave the default colors (red/grey/black) and focus the judges on the concept
and the gait. Appearance is 1/3 of scoring and the other two (playfulness + usefulness) are
where this entry is strongest.

---

## Video shot list (65–75 seconds total)

| # | Duration | Shot | Camera |
|---|----------|------|--------|
| 1 | 0–3 s | **Hook:** robot walks into a dirty floor from the side, brush visible | Side view, low angle |
| 2 | 3–10 s | Wide overhead: robot sweeps across full floor, patches scatter | Top-down or 45° overhead |
| 3 | 10–18 s | Close-up: brush near floor, dirt patches being pushed aside | Front-low |
| 4 | 18–26 s | Full gait: clean tripod walk from behind | Behind-tracking |
| 5 | 26–38 s | "Building it" screen capture: Claude Code session, the OOM crash, the fix | Screen recording |
| 6 | 38–45 s | Text card: "Simulation concept — cleaning motions in development" (honest framing per rules) | Static |
| 7 | 45–55 s | Second sweep pass, completed. Floor is noticeably cleaner (patches cleared) | Side view |
| 8 | 55–65 s | Wide shot with robot in standing pose, brush highlighted | 3/4 angle, static |
| 9 | 65–70 s | End card: GitHub link, #Jumper #CrabRobot @KingKong Robotics | Static |

**First 3 seconds:** Brush hits the floor as the robot walks in — immediate "oh it's cleaning" moment. No title card at the start; the action speaks first.

---

## YouTube title, description and tags

**Title (under 70 characters):**
```
Jumper Crab Robot Cleans the Floor — Simulation Concept 🤖🧹
```

**Description:**
```
What if Jumper could sweep the floor? Here's our simulation concept for a cleaning-tool
attachment — trained with reinforcement learning, built with MuJoCo and Claude Code.

This is a simulation concept entry for the Jumper Crab Robot Challenge 2026.
Household capabilities remain in development — but the robot can already walk very well.

🔗 Code: https://github.com/Zeno144/jumper
📋 Challenge: https://beunlimited.me/zh/events/crab-robot-challenge-2026

Built using the open-source Jumper training framework. Apache-2.0 license.

@KingKong Robotics
```

**Tags (paste all):**
```
#Jumper #CrabRobot #OpenSourceRobot #RoboticsSimulation #ReinforcementLearning #MuJoCo #ClaudeCode #RobotDog #AIRobot #KingKongRobotics
```

---

## Git layout (set up Oct 16)

| Remote | URL | Use |
|---|---|---|
| `origin` | `https://github.com/Zeno144/jumper.git` | the fork; default push remote |
| `upstream` | `https://github.com/KingKongRobotics/jumper.git` | fetch only (push URL = `DISABLED`) |

| Local branch | Tracks | Contents |
|---|---|---|
| `work` (checked out) | `origin/work` | the training framework (`rl/`, `tasks/`, `scripts/`) — all challenge work goes here |
| `main` | `origin/main` | the fork's own `main`: a **different, unrelated history** ("Design Workflow": `ai/`, `library/`, `platforms/`, `src/`) with no training code |

- `work` started from upstream `main` at `78966f4`. Pull upstream changes with
  `git fetch upstream; git merge upstream/main` while on `work`.
- `push.default=upstream`, so a plain `git push` on `work` goes to `origin/work`.
- **Never `git checkout main` in this folder** — it deletes `rl/`, `tasks/` and `scripts/train.py`
  from the working tree and breaks any running training and the editable install. To look at
  `main`, use a separate worktree: `git worktree add ../jumper-main main`.

## GitHub setup

1. ~~Fork~~ done — see "Git layout" above; commit on `work` and push to `origin/work`.
2. Add a section to `README.md`:

```markdown
## Cleaning concept (Challenge 2026 entry)

A brush geom is attached to the robot's front face in `assets/jumper/jumper.xml`.
A sweep command script drives the robot in a back-and-forth pattern.

### Run the cleaning demo

```powershell
pip install -e .
python scripts/train.py --task jumper.tripod --backend native --device cpu --num_envs 256
python scripts/play.py --task jumper.tripod --headless --steps 1200 `
  --command-script scripts/sweep.py `
  --video sweep.mp4 --video-width 1920 --video-height 1080 --video-fps 30
```
```

3. Commit the two changed files: `assets/jumper/jumper.xml` and `scripts/sweep.py`.
4. Keep `LICENSE` and `NOTICE` unchanged (Apache-2.0 requirement).

---

## Risks and parts that may not be possible

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| GPU training unavailable (needs MSVC) | ✅ Resolved Oct 15 | MSVC installed, CUDA confirmed, GPU run active |
| CPU torch overwritten by pip install -e . | ✅ Resolved Oct 15 | Pin cu128 after every `pip install -e .`; tensordict pinned to 0.11.0 |
| 300-iter CPU checkpoint looks bad (robot jerks) | N/A | Superseded by GPU run |
| Dirt particles clip through the floor | Medium | Increase floor friction on the patch geoms; set `solref` tighter |
| Sweep command script makes the robot fall | Medium | Start with slow speeds (vx=0.2), increase after testing |
| Bedroom map scene setup takes too long | Medium | Fall back to built-in `studio` scene |
| Video is under 15 seconds | Low risk | Shot list targets 65–75 s |
| Music rights issue | N/A | Plan is no music; add a voiceover or use ambient servo sounds |

**Fallback video (if the full idea doesn't come together):**
Record the standard tripod gait in the `studio` scene with the brush attachment visible.
No dirt patches, no sweep pattern. Just: "Here is Jumper with a cleaning brush attached.
Sweeping behavior is in development." Caption the brush. 25 seconds. Post it.
This still hits playfulness (crab robot with a mop) and usefulness (concept demonstration).

---

## Quick command reference

```powershell
# Set UTF-8 (required every session on Windows)
$env:PYTHONIOENCODING = "utf-8"

# Train tripod (GPU — preferred now that MSVC is installed)
.venv\Scripts\python.exe scripts/train.py --task jumper.tripod `
  --backend warp --device cuda --num_envs 4096 --headless

# Train tripod (CPU fallback)
.venv\Scripts\python.exe scripts/train.py --task jumper.tripod `
  --backend native --device cpu --num_envs 256 --headless

# Check overnight training progress
Get-Content .\train_gpu_stdout.txt | Select-String "Iteration time|ETA" | Select-Object -Last 4

# Replay and record
.venv\Scripts\python.exe scripts/play.py --task jumper.tripod `
  --headless --steps 600 --video output.mp4 `
  --video-width 1920 --video-height 1080 --video-fps 30

# Record with sweep script
.venv\Scripts\python.exe scripts/play.py --task jumper.tripod `
  --headless --steps 1200 --video sweep.mp4 `
  --command-script scripts/sweep.py `
  --video-width 1920 --video-height 1080 --video-fps 30

# Run tests
.venv\Scripts\python.exe -m pytest tests/ -q `
  --ignore=tests/test_deploy_sources.py --ignore=tests/test_fsm_extension.py

# Check training logs in TensorBoard
.venv\Scripts\python.exe -m tensorboard --logdir logs/
```
