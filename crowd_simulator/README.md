# 3D Crowd Panic Simulator

A crowd of animated 3D stick people wanders around an arena. Click the ground
to spawn a danger — everyone nearby panics and flees, and fear spreads through
the crowd by contagion. When the danger expires, people calm down and go back
to wandering.

## Run it

Open `index.html` in any browser. No dependencies, no build step, no network —
the 3D rendering is a small hand-written perspective projector drawing onto a
2D canvas.

## Controls

| Action | Effect |
|--------|--------|
| Click / tap the ground | Spawn a danger (lasts ~7 s) |
| Drag | Orbit the camera |
| Scroll / pinch | Zoom |
| Crowd size slider | 20–300 people |
| Random danger | Spawn a danger somewhere in the arena |
| Clear / Reset | Remove dangers / respawn the crowd |

## How the simulation works

Each person steers with a few simple forces:

- **Flee** — dangers within 13 m push agents directly away, weighted by proximity.
- **Panic contagion** — an agent near (< 3 m) a more frightened agent catches
  its fear and copies its flee direction, so panic ripples outward past the
  danger's own radius.
- **Separation** — agents closer than 1.2 m push apart, so the crowd doesn't
  collapse into a point while stampeding.
- **Wander** — calm agents follow a smoothly drifting heading.
- **Bounds** — agents steer back toward the centre near the arena edge.

Fear drives everything visual: walking becomes sprinting (stride, lean, arm
pumping and pace all scale with fear), colour shifts from bluish-white to
orange, and panicked agents get a "!" marker. Fear decays over a few seconds
once no danger is in range.
