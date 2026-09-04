# Athena - detailed 3D model

A full-figure statue of Athena, sculpted procedurally from signed-distance
fields and exported as a real mesh. The face is modelled at 1.2 mm
resolution so the features read clearly: almond eyes with lids, pupils and
an upper-lid crease, brow ridges, a straight classical nose with nostrils
and alae, full lips with a cupid's bow and philtrum, a defined chin and
jaw, cheekbones and ears.

The rest of the figure:

- Corinthian helmet pushed back on the crown (bowl, T-shaped face opening,
  nasal guard, raised cheek pieces, rivets, crest keel) with a red
  horsehair plume sweeping down the back.
- Centre-parted wavy hair with a chignon and tresses over the shoulders.
- Scaled aegis over the shoulders and chest with a snake fringe and the
  gorgoneion (Medusa head with tongue out and snake hair) at its centre.
- Doric peplos with belted waist, apoptygma overfold and deep skirt folds.
- Right arm raised gripping a spear (fingers wrap the shaft), left hand
  resting on the rim of a hoplite shield with boss and concentric bands.
- Sandalled feet on a round plinth.

## Files

| File | What it is |
| --- | --- |
| `output/athena.glb` | Binary glTF, 14 parts, ~1.07 M triangles, PBR materials. Opens in any 3D viewer, phone included. |
| `output/athena_viewer.html` | Self-contained viewer (three.js inlined, mesh embedded, ~430 k triangle web LOD with the head at full detail). Open the file in a browser, no server needed. Buttons jump to Face / 3/4 / Profile / Bust / Full figure / Shield. |
| `previews/*.png` | Rendered preview images of the preset views. |
| `generate_athena.py` | The sculpt. Every feature is a named primitive with coordinates in metres, so tweaking the nose or the helmet tilt is a one-line change. |
| `sdf_toolkit.py` | Primitives, boolean/smooth combinators, marching cubes surfacing, decimation, normals. |
| `viewer_template.html`, `build_viewer.py` | Viewer page and the script that inlines three.js plus the mesh into it. |
| `render_previews.py` | Headless Chromium renders of the preset views. |

The OBJ/MTL export (~77 MB) is not committed. Regenerate it with the
script below; it lands in `output/athena.obj`.

## Regenerating

```bash
cd athena
pip install -r requirements.txt
python generate_athena.py            # ~6 min on 4 cores, ~2 GB RAM
python build_viewer.py               # output/athena_viewer.html
python render_previews.py output/athena_viewer.html previews
```

`python generate_athena.py --parts head` rebuilds only the head (about a
minute) for iterating on the face. `--fast` uses coarser voxels for quick
previews.

## How it works

Each part (head, hair, helmet, plume, arms, peplos, belt, aegis, gorgon,
sandals, shield, spear, spearhead, plinth) is a Python function that
combines SDF primitives (ellipsoids, capsules, tori, boxes) with smooth
unions and subtractions, plus displacement terms for hair waves, cloth
folds, aegis scales and plume strands. Each part is voxelised on its own
grid at a resolution matched to its scale, surfaced with marching cubes,
quadric-decimated, and exported with vertex normals. Parts overlap
slightly where they meet (hair under the helmet, hands around the spear)
so nothing floats or shows gaps.

three.js is vendored as `vendor_three.min.js` (MIT, see
`vendor_three.LICENSE`).
