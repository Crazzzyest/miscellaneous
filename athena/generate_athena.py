"""
Procedural, sculpted 3D model of Athena.

The figure is built entirely from signed-distance primitives: skull, jaw,
eyes with lids, nose, lips, ears, wavy hair, a Corinthian helmet pushed back
on the head with a horsehair crest, the scaled aegis with a gorgoneion,
a draped peplos, spear and shield. Each part is voxelised at a resolution
that fits its scale (the face at 1.2 mm so the features read clearly, the
dress at 4 mm), surfaced with marching cubes, decimated and exported.

Outputs (written next to this script under ./output):
  athena.obj + athena.mtl   standard mesh with one material per part
  athena.glb                binary glTF, opens in any 3D viewer / phone
  athena_mesh.json          compact quantised buffers for viewer.html

Run:  python generate_athena.py [--parts head,hair,...] [--fast]
"""
import argparse
import base64
import json
import os
import struct
import sys
import time

import numpy as np

from sdf_toolkit import (
    F32, Grid, box, capsule, cylinder_x, cylinder_y, decimate, ellipsoid,
    half_space, intersect, rotate_x, rotate_y, rotate_z, rounded_box, shell,
    smooth_intersect, smooth_subtract, smooth_union, sphere, subtract, surface,
    tapered_capsule, torus_x, torus_y, torus_z, union, vertex_normals,
)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# Figure layout (metres, Y up, she faces +Z, her right hand is at -X).
HEAD_C = (0.0, 1.70, 0.0)
EYE_Y = 1.710
EYE_X = 0.031
SPEAR_X, SPEAR_Z = -0.34, 0.07
SHIELD_C = (0.56, 0.46, 0.02)
SHIELD_R = 0.44

MATERIALS = {
    # name: (diffuse rgb, metallic, roughness)
    "skin":    ((0.93, 0.80, 0.70), 0.0, 0.55),
    "hair":    ((0.30, 0.19, 0.10), 0.0, 0.65),
    "helmet":  ((0.80, 0.62, 0.30), 1.0, 0.35),
    "plume":   ((0.72, 0.12, 0.10), 0.0, 0.75),
    "peplos":  ((0.92, 0.89, 0.80), 0.0, 0.85),
    "belt":    ((0.85, 0.70, 0.30), 1.0, 0.40),
    "aegis":   ((0.55, 0.50, 0.28), 0.6, 0.55),
    "gorgon":  ((0.78, 0.66, 0.36), 1.0, 0.40),
    "shield":  ((0.76, 0.58, 0.28), 1.0, 0.35),
    "spear":   ((0.45, 0.30, 0.16), 0.0, 0.70),
    "spearhead": ((0.82, 0.82, 0.78), 1.0, 0.30),
    "sandal":  ((0.42, 0.26, 0.14), 0.0, 0.80),
    "plinth":  ((0.85, 0.85, 0.83), 0.0, 0.60),
}


# =====================================================================  HEAD

def sculpt_head(g):
    """Skin of the head and neck. Facial features are laid out on a classical
    Greek profile: straight nose continuing the brow line, full lips, strong
    chin, almond eyes under a low brow."""
    cx, cy, cz = HEAD_C
    d = ellipsoid(g, (cx, cy + 0.028, cz - 0.012), (0.074, 0.090, 0.092))
    # Forehead is flatter and higher than a plain ellipsoid gives.
    d = smooth_union(d, ellipsoid(g, (cx, cy + 0.045, cz + 0.030), (0.066, 0.048, 0.050)), 0.03)
    # Jaw and chin.
    d = smooth_union(d, ellipsoid(g, (cx, cy - 0.045, cz + 0.010), (0.066, 0.062, 0.068)), 0.03)
    d = smooth_union(d, ellipsoid(g, (cx, cy - 0.085, cz + 0.060), (0.026, 0.020, 0.022)), 0.02)
    # Under-chin cut gives the jaw a real angle in profile instead of a
    # smooth slope from lips to throat.
    d = smooth_subtract(d, ellipsoid(g, (cx, cy - 0.140, cz + 0.085), (0.10, 0.030, 0.050)), 0.02)
    for s in (-1, 1):
        # Full cheeks below high, defined cheekbones.
        d = smooth_union(d, ellipsoid(g, (cx + s * 0.046, cy - 0.030, cz + 0.048), (0.030, 0.032, 0.036)), 0.03)
        d = smooth_union(d, ellipsoid(g, (cx + s * 0.055, cy + 0.000, cz + 0.045), (0.020, 0.016, 0.026)), 0.03)
    # Neck.
    d = smooth_union(d, tapered_capsule(g, (cx, cy - 0.235, cz - 0.02), (cx, cy - 0.10, cz - 0.015), 0.058, 0.048), 0.03)
    # Sternocleidomastoid hint so the neck is not a plain tube.
    for s in (-1, 1):
        d = smooth_union(d, capsule(g, (cx + s * 0.045, cy - 0.235, cz - 0.02), (cx + s * 0.02, cy - 0.12, cz + 0.02), 0.014), 0.025)
    # Anything that decorates the surface is clipped against this dilated
    # base so it can never float free of the head (the first draft had brows
    # sticking out into the air past the temples).
    base = d.copy()

    # ---- brow ridge and eyebrows
    for s in (-1, 1):
        bc = (cx + s * 0.033, cy + 0.024, cz + 0.076)
        brow_frame = g.transformed(rotate_y(s * 0.45, bc))
        brow = ellipsoid(brow_frame, bc, (0.032, 0.0070, 0.014))
        brow = intersect(brow, base - 0.0045)
        d = smooth_union(d, brow, 0.012)

    # ---- eyes: eyeball wrapped in a skin layer, almond opening cut into it
    r_eye = 0.016
    for s in (-1, 1):
        ex = cx + s * EYE_X
        ez = cz + 0.061
        # Soft orbital hollow between brow and lid.
        d = smooth_subtract(d, ellipsoid(g, (ex, EYE_Y + 0.012, cz + 0.098), (0.024, 0.011, 0.016)), 0.010)
        d = smooth_union(d, sphere(g, (ex, EYE_Y, ez), r_eye + 0.0035), 0.010)
        tilt = g.transformed(rotate_z(-s * 0.10, (ex, EYE_Y, ez)))
        opening = ellipsoid(tilt, (ex, EYE_Y - 0.0005, ez + 0.012), (0.018, 0.0085, 0.014))
        d = subtract(d, opening)
        d = union(d, sphere(g, (ex, EYE_Y, ez), r_eye))
        # Cornea bump so the eye catches light at the iris.
        d = smooth_union(d, sphere(g, (ex + s * 0.001, EYE_Y - 0.0005, ez + r_eye - 0.0025), 0.0055), 0.003)
        # Upper lid crease and the inner-corner pocket.
        d = smooth_subtract(d, ellipsoid(tilt, (ex, EYE_Y + 0.0135, ez + 0.016), (0.016, 0.0015, 0.004)), 0.004)
        # Pupil dimple: a dark point that makes the gaze readable at a distance.
        d = smooth_subtract(d, sphere(g, (ex + s * 0.001, EYE_Y - 0.0005, ez + r_eye + 0.0035), 0.0028), 0.001)
        d = smooth_subtract(d, sphere(g, (cx + s * 0.013, EYE_Y - 0.003, cz + 0.083), 0.0035), 0.004)

    # ---- nose: straight bridge running up into the brow, defined tip and alae
    bridge = tapered_capsule(g, (cx, cy + 0.040, cz + 0.078), (cx, cy - 0.018, cz + 0.100), 0.0070, 0.0095)
    d = smooth_union(d, bridge, 0.012)
    d = smooth_union(d, sphere(g, (cx, cy - 0.024, cz + 0.104), 0.0115), 0.008)
    for s in (-1, 1):
        d = smooth_union(d, ellipsoid(g, (cx + s * 0.0115, cy - 0.029, cz + 0.094), (0.0065, 0.0060, 0.0085)), 0.008)
        d = smooth_subtract(d, ellipsoid(g, (cx + s * 0.006, cy - 0.034, cz + 0.099), (0.0030, 0.0025, 0.005)), 0.002)
    # Columella underside, so there is a real nose base rather than a blob.
    d = smooth_union(d, box(g, (cx, cy - 0.033, cz + 0.097), (0.0035, 0.0025, 0.009)), 0.004)

    # ---- mouth: full classical lips with cupid's bow and philtrum
    mouth_y = cy - 0.056
    upper_lip = ellipsoid(g, (cx, mouth_y + 0.0055, cz + 0.086), (0.024, 0.0062, 0.011))
    lower_lip = ellipsoid(g, (cx, mouth_y - 0.0070, cz + 0.083), (0.020, 0.0072, 0.012))
    d = smooth_union(d, upper_lip, 0.006)
    d = smooth_union(d, lower_lip, 0.006)
    for s in (-1, 1):
        # Twin peaks of the cupid's bow.
        d = smooth_union(d, sphere(g, (cx + s * 0.0055, mouth_y + 0.009, cz + 0.094), 0.0033), 0.004)
    d = smooth_subtract(d, sphere(g, (cx, mouth_y + 0.012, cz + 0.098), 0.0032), 0.003)
    # Mouth line, curved slightly up at the corners. Kept wider than one
    # voxel so marching cubes resolves it as a clean groove instead of noise.
    corner_lift = 0.0025 * (np.abs(g.X - cx) / 0.024) ** 2
    line = box(g.transformed(lambda X, Y, Z: (X, (Y - corner_lift).astype(F32), Z)),
               (cx, mouth_y - 0.0005, cz + 0.092), (0.0225, 0.0014, 0.012))
    d = smooth_subtract(d, line, 0.0025)
    # Philtrum groove between nose and lip.
    d = smooth_subtract(d, box(g, (cx, cy - 0.043, cz + 0.100), (0.0025, 0.008, 0.004)), 0.003)
    # Corners of the mouth sink into the cheek slightly.
    for s in (-1, 1):
        d = smooth_subtract(d, sphere(g, (cx + s * 0.026, mouth_y - 0.001, cz + 0.088), 0.0035), 0.004)
    # Mentolabial fold above the chin.
    d = smooth_subtract(d, ellipsoid(g, (cx, cy - 0.074, cz + 0.095), (0.015, 0.003, 0.006)), 0.008)

    # ---- ears
    for s in (-1, 1):
        ear_c = (cx + s * 0.080, cy + 0.002, cz - 0.012)
        er = g.transformed(rotate_y(-s * 0.25, ear_c))
        ear = ellipsoid(er, ear_c, (0.009, 0.031, 0.020))
        ear = smooth_subtract(ear, ellipsoid(er, (ear_c[0] + s * 0.007, ear_c[1] - 0.004, ear_c[2] + 0.003), (0.006, 0.019, 0.012)), 0.003)
        # Helix rim and tragus.
        ear = smooth_union(ear, torus_x(er, (ear_c[0] + s * 0.003, ear_c[1] + 0.004, ear_c[2] + 0.001), 0.016, 0.0035), 0.003)
        ear = smooth_union(ear, sphere(er, (ear_c[0] + s * 0.002, ear_c[1] - 0.004, ear_c[2] + 0.012), 0.005), 0.003)
        d = smooth_union(d, ear, 0.006)
    return d


def sculpt_hair(g):
    """Centre-parted wavy hair under the helmet, gathered into a chignon at
    the nape with loose tresses over the shoulders."""
    cx, cy, cz = HEAD_C
    skull = ellipsoid(g, (cx, cy + 0.028, cz - 0.012), (0.074, 0.090, 0.092))
    cap = ellipsoid(g, HAIR_CAP_C, HAIR_CAP_R)
    cap = subtract(cap, skull - 0.004)
    # Hairline: high on the forehead, dipping at the temples, low at the nape.
    angle = np.arctan2(g.X - cx, g.Z - cz)
    hairline = cy + 0.068 - 0.022 * np.abs(np.sin(angle)) ** 2 - 0.085 * np.clip(-(g.Z - cz) / 0.09, 0, 1) ** 1.5
    # Widow's peak in the centre part.
    hairline = hairline - 0.006 * np.exp(-(g.X - cx) ** 2 / 0.0004)
    cap = intersect(cap, half_space(g.Y, hairline))
    # Wave relief: strands radiating from the parting and rippling downward.
    waves = 0.0014 * np.sin(angle * 14.0 + (g.Y - cy) * 40.0) + 0.0008 * np.sin(angle * 33.0)
    cap = cap + waves.astype(F32)
    # Centre parting groove.
    cap = smooth_subtract(cap, box(g, (cx, cy + 0.11, cz + 0.02), (0.0015, 0.03, 0.09)), 0.003)
    d = cap
    # Chignon at the nape.
    bun = ellipsoid(g, (cx, cy - 0.040, cz - 0.100), (0.056, 0.044, 0.038))
    bun = bun + (0.002 * np.sin((g.Y - cy) * 120.0 + angle * 6.0)).astype(F32)
    d = smooth_union(d, bun, 0.015)
    # Tresses falling from the temples along the neck to the shoulders: many
    # thin strands with a short, low-amplitude wave read as hair; a few fat
    # ones read as rope.
    for s in (-1, 1):
        for i, (xo, zo, rr, ylen, ph) in enumerate([
                (0.066, -0.040, 0.0095, 0.30, 0.0), (0.078, -0.012, 0.0085, 0.25, 1.1),
                (0.058, -0.075, 0.0090, 0.34, 2.3), (0.072, -0.058, 0.0080, 0.28, 3.1),
                (0.048, -0.092, 0.0085, 0.32, 4.0), (0.084, -0.030, 0.0075, 0.22, 5.2)]):
            wave_x = 0.004 * np.sin((g.Y - cy) * 75.0 + ph)
            wave_z = 0.003 * np.sin((g.Y - cy) * 60.0 + ph * 1.7)
            shifted = g.transformed(lambda X, Y, Z, s=s, wx=wave_x, wz=wave_z: ((X - s * wx).astype(F32), Y, (Z - wz).astype(F32)))
            tress = tapered_capsule(shifted, (cx + s * xo, cy + 0.01, cz + zo), (cx + s * (xo + 0.025), cy - ylen, cz + zo - 0.015), rr, rr * 0.7)
            d = smooth_union(d, tress, 0.008)
    # Never let hair poke through the face: carve the head out of it.
    from_head = ellipsoid(g, (cx, cy + 0.028, cz - 0.012), (0.073, 0.089, 0.091))
    d = subtract(d, from_head)
    return d


# Positive angle tips the helmet's front upward. The first two drafts got the
# sign and the amount wrong (35 degrees looked like a visor, negative pulled
# it down over the eyes); ~54 degrees with the bowl centred above and behind
# the skull gives the pushed-back Athena Parthenos look.
HELMET_TILT = 0.95
HELMET_PIVOT = (0.0, 1.772, -0.035)
HAIR_CAP_C = (0.0, 1.725, -0.016)
HAIR_CAP_R = (0.083, 0.100, 0.101)


def helmet_frame(g):
    return g.transformed(rotate_x(HELMET_TILT, HELMET_PIVOT))


def sculpt_helmet(g):
    """Corinthian helmet worn pushed up on the crown: bowl, cheek pieces,
    nasal guard, eye openings, ridge and crest holder. Everything is defined
    in the helmet's own frame around HELMET_PIVOT and then tilted."""
    h = helmet_frame(g)
    cx, cy, cz = HELMET_PIVOT
    outer = ellipsoid(h, (cx, cy, cz), (0.092, 0.112, 0.108))
    inner = ellipsoid(h, (cx, cy, cz), (0.085, 0.105, 0.101))
    bowl = subtract(outer, inner)
    # Keep the upper bowl everywhere, plus cheek pieces and a short neck guard.
    keep = half_space(h.Y, cy - 0.015)
    cheek_l = intersect(half_space(h.Y, cy - 0.095), half_space(np.abs(h.X - cx), 0.030))
    cheek_l = intersect(cheek_l, half_space(h.Z, cz + 0.090, keep_above=False))
    cheek_l = intersect(cheek_l, half_space(h.Z, cz - 0.02))
    neck_guard = intersect(half_space(h.Y, cy - 0.055), half_space(h.Z, cz - 0.02, keep_above=False))
    keep = union(keep, union(cheek_l, neck_guard))
    bowl = intersect(bowl, keep)
    # Face opening: a T-shaped cut leaving the nasal guard in place.
    opening = box(h, (cx, cy - 0.020, cz + 0.100), (0.062, 0.035, 0.040))
    opening = subtract(opening, box(h, (cx, cy - 0.050, cz + 0.100), (0.011, 0.090, 0.060)))
    bowl = subtract(bowl, opening)
    nasal = box(h, (cx, cy - 0.050, cz + 0.102), (0.010, 0.045, 0.006))
    bowl = smooth_union(bowl, nasal, 0.006)
    # Every raised decoration is clipped to a thin band around the shell so
    # nothing floats in the air where the shell has been cut away.
    on_shell = intersect(outer - 0.006, -(inner - 0.002))
    bead = intersect(shell(ellipsoid(h, (cx, cy, cz), (0.095, 0.115, 0.111)), 0.004),
                     half_space(np.abs(h.Y - (cy - 0.020)), 0.006, keep_above=False))
    bowl = smooth_union(bowl, intersect(bead, on_shell), 0.003)
    for s in (-1, 1):
        ridge = torus_z(h, (cx + s * 0.034, cy + 0.020, cz + 0.104), 0.028, 0.0035)
        ridge = intersect(ridge, half_space(h.Y, cy + 0.020))
        bowl = smooth_union(bowl, intersect(ridge, on_shell), 0.004)
    # Crest holder: a raised keel running front to back along the crown.
    keel = intersect(shell(ellipsoid(h, (cx, cy, cz), (0.100, 0.120, 0.116)), 0.014),
                     half_space(np.abs(h.X - cx), 0.006, keep_above=False))
    keel = intersect(keel, half_space(h.Y, cy + 0.030))
    bowl = smooth_union(bowl, keel, 0.006)
    for s in (-1, 1):
        for i in range(3):
            rivet = sphere(h, (cx + s * 0.088, cy - 0.040 - 0.020 * i, cz + 0.040), 0.004)
            bowl = smooth_union(bowl, intersect(rivet, outer - 0.005), 0.003)
    # The helmet rests on the hair: carve the (slightly dilated) hair cap
    # out of it so the bronze never passes through the head.
    # Smooth rather than hard subtraction: a hard cut through a 7 mm shell at
    # a grazing angle left a serrated rim.
    bowl = smooth_subtract(bowl, ellipsoid(g, HAIR_CAP_C, tuple(r + 0.004 for r in HAIR_CAP_R)), 0.010)
    return bowl


def sculpt_plume(g):
    """Horsehair crest: a fin over the crown sweeping down the back, grooved
    along the direction the hair flows so it reads as strands."""
    h = helmet_frame(g)
    cx, cy, cz = HELMET_PIVOT
    d = None
    ctrl = np.array([[cx, cy + 0.105, cz + 0.060], [cx, cy + 0.178, cz + 0.000], [cx, cy + 0.140, cz - 0.150], [cx, cy + 0.020, cz - 0.190]])
    for t in np.linspace(0, 1, 28):
        p = ((1 - t) ** 3) * ctrl[0] + 3 * ((1 - t) ** 2) * t * ctrl[1] + 3 * (1 - t) * t * t * ctrl[2] + (t ** 3) * ctrl[3]
        r = 0.020 + 0.026 * np.sin(np.pi * min(1.0, 0.15 + t * 0.9))
        seg = ellipsoid(h, tuple(p), (0.009 + 0.004 * t, r, r * 0.9))
        d = seg if d is None else smooth_union(d, seg, 0.03)
    radial = np.sqrt((h.Y - cy) ** 2 + (h.Z - cz) ** 2)
    strands = 0.0007 * np.sin(radial * 520.0) + 0.0005 * np.sin(h.X * 1600.0 + radial * 90.0)
    d = d + strands.astype(F32)
    d = subtract(d, ellipsoid(h, (cx, cy, cz), (0.094, 0.114, 0.110)))
    return d


# =====================================================================  BODY

def torso_core(g):
    """Shared body volume under the clothing so the bodice, overfold, belt
    and aegis all hug the same shape and layer cleanly."""
    d = ellipsoid(g, (0, 1.30, -0.01), (0.165, 0.21, 0.105))
    d = smooth_union(d, capsule(g, (-0.13, 1.455, 0), (0.13, 1.455, 0), 0.052), 0.05)
    d = smooth_union(d, ellipsoid(g, (0, 1.05, 0), (0.19, 0.16, 0.13)), 0.08)
    for s in (-1, 1):
        d = smooth_union(d, ellipsoid(g, (s * 0.07, 1.35, 0.07), (0.065, 0.058, 0.045)), 0.04)
    return d


def peplos_folds(g, count, amplitude, phase=0.0):
    angle = np.arctan2(g.X, g.Z)
    return (amplitude * np.sin(angle * count + phase)).astype(F32)


def sculpt_peplos(g):
    """Doric peplos: fitted bodice, belted waist, long skirt with vertical
    folds and an overfold (apoptygma) hanging over the hips."""
    core = torso_core(g)
    y = g.Y
    bodice = intersect(core - 0.024, half_space(y, 1.05))
    # Skirt: elliptical cone widening to the hem with deepening folds. The
    # left knee pressed forward pushes the cloth out in front.
    t = np.clip((1.18 - y) / 1.18, 0, 1)
    base_r = 0.175 + 0.14 * t
    knee = 0.05 * np.exp(-((g.X - 0.09) ** 2 + (y - 0.55) ** 2) / 0.02)
    radial = np.sqrt(g.X ** 2 + ((g.Z - knee) / 0.80) ** 2)
    folds = peplos_folds(g, 18, 0.004 + 0.022 * t) + peplos_folds(g, 7, 0.010 * t, 1.3)
    skirt = (radial - (base_r + folds)).astype(F32)
    skirt = intersect(skirt, half_space(y, 0.0))
    skirt = intersect(skirt, half_space(y, 1.20, keep_above=False))
    d = smooth_union(bodice, skirt, 0.05)
    # Waist cinch pulls the fabric in above the belt.
    d = smooth_subtract(d, torus_y(g, (0, 1.17, -0.005), 0.30, 0.09), 0.05)
    # Apoptygma: overfold hanging from under the aegis to the hips, a layer
    # outside the bodice with its own folds and a wavy hem.
    t2 = np.clip((1.30 - y) / 0.35, 0, 1)
    hem = 0.95 + 0.035 * np.sin(np.arctan2(g.X, g.Z) * 5.0 + 0.7)
    over_folds = peplos_folds(g, 13, 0.004 + 0.012 * t2, 0.4)
    # The belt cinches the overfold in, so the band can sit on the cloth.
    cinch = 0.010 * np.exp(-((y - 1.17) / 0.03) ** 2)
    over = (core - (0.034 + over_folds - cinch)).astype(F32)
    over = subtract(over, core - 0.016)
    over = intersect(over, half_space(y, hem))
    over = intersect(over, half_space(y, 1.30, keep_above=False))
    d = smooth_union(d, over, 0.012)
    # Clean neckline (hidden by the aegis, but keeps the silhouette tidy).
    d = smooth_subtract(d, capsule(g, (0, 1.40, -0.02), (0, 1.75, -0.02), 0.075), 0.01)
    return d


def sculpt_belt(g):
    core = torso_core(g)
    band = intersect(shell(core - 0.036, 0.012), half_space(np.abs(g.Y - 1.17), 0.013, keep_above=False))
    # Knot at the front.
    band = smooth_union(band, torus_z(g, (0, 1.17, 0.138), 0.018, 0.008), 0.005)
    return band


def sculpt_aegis(g):
    """The goatskin aegis over the shoulders and chest: a scaled cape lying
    on the bodice, with a fringe of snakes and the gorgoneion at its centre."""
    core = torso_core(g)
    cape = subtract(core - 0.058, core - 0.046)
    angle = np.arctan2(g.X, g.Z)
    lower_edge = 1.28 + 0.035 * np.sin(angle * 6.0) + 0.05 * np.clip(-np.cos(angle), 0, 1)
    cape = intersect(cape, half_space(g.Y, lower_edge))
    cape = subtract(cape, capsule(g, (0, 1.35, -0.02), (0, 1.80, -0.02), 0.088))
    # Scale pattern: staggered rows of overlapping bumps.
    row = np.floor(g.Y * 120.0)
    scale = 0.0025 * np.abs(np.sin(angle * 40.0 + row * np.pi * 0.5)) * np.abs(np.sin(g.Y * 120.0 * np.pi))
    cape = cape - scale.astype(F32)
    d = cape
    # Snake fringe hanging from the lower edge.
    for i in range(14):
        a = -2.6 + i * (5.2 / 13)
        x0 = 0.222 * np.sin(a)
        z0 = 0.165 * np.cos(a) - 0.01
        y0 = 1.28 + 0.035 * np.sin(a * 6.0) + 0.05 * max(0.0, -np.cos(a))
        wobble = g.transformed(lambda X, Y, Z, a=a: ((X + 0.012 * np.sin((Y - 1.0) * 70.0 + a)).astype(F32), Y, Z))
        snake = tapered_capsule(wobble, (x0, y0 + 0.02, z0), (x0 * 1.08, y0 - 0.09, z0 * 1.08), 0.010, 0.006)
        head = ellipsoid(g, (x0 * 1.08, y0 - 0.105, z0 * 1.08), (0.011, 0.012, 0.014))
        d = smooth_union(d, smooth_union(snake, head, 0.006), 0.008)
    return d


def sculpt_gorgon(g):
    """Gorgoneion (Medusa head) mounted on the aegis: round face, tongue out,
    with a ring of snakes for hair."""
    c = (0.0, 1.375, 0.166)
    face = ellipsoid(g, c, (0.050, 0.052, 0.024))
    for s in (-1, 1):
        face = smooth_subtract(face, sphere(g, (c[0] + s * 0.018, c[1] + 0.012, c[2] + 0.024), 0.010), 0.004)
        face = smooth_union(face, sphere(g, (c[0] + s * 0.018, c[1] + 0.012, c[2] + 0.018), 0.007), 0.003)
        face = smooth_union(face, ellipsoid(g, (c[0] + s * 0.020, c[1] + 0.026, c[2] + 0.022), (0.014, 0.004, 0.006)), 0.004)
    face = smooth_union(face, ellipsoid(g, (c[0], c[1] - 0.002, c[2] + 0.026), (0.008, 0.014, 0.008)), 0.005)
    mouth = ellipsoid(g, (c[0], c[1] - 0.024, c[2] + 0.026), (0.020, 0.008, 0.010))
    face = smooth_subtract(face, mouth, 0.004)
    tongue = ellipsoid(g, (c[0], c[1] - 0.034, c[2] + 0.028), (0.009, 0.013, 0.006))
    face = smooth_union(face, tongue, 0.003)
    d = face
    for i in range(12):
        a = i * (2 * np.pi / 12)
        sx, sy = c[0] + 0.058 * np.cos(a), c[1] + 0.058 * np.sin(a)
        ex, ey = c[0] + 0.085 * np.cos(a + 0.5), c[1] + 0.085 * np.sin(a + 0.5)
        snake = tapered_capsule(g, (sx, sy, c[2] + 0.005), (ex, ey, c[2] + 0.012), 0.008, 0.005)
        d = smooth_union(d, snake, 0.006)
    return d


def sculpt_arms(g):
    """Bare arms and hands. Right arm raised holding the spear, left arm down
    resting on the shield rim. Feet included since they share the skin."""
    d = None

    def add(part, k=0.03):
        nonlocal d
        d = part if d is None else smooth_union(d, part, k)

    # Right arm (her right = -X): upper arm forward and out, forearm up to grip the spear.
    sh = (-0.20, 1.45, 0.0)
    el = (-0.31, 1.24, 0.09)
    wr = (SPEAR_X + 0.035, 1.49, SPEAR_Z - 0.01)
    add(sphere(g, sh, 0.056))
    add(tapered_capsule(g, sh, el, 0.048, 0.038))
    add(sphere(g, el, 0.040))
    add(tapered_capsule(g, el, wr, 0.038, 0.027))
    # Right hand: palm behind the shaft, four fingers curling around the
    # front of it, thumb locked over the top. Fingers are torus segments
    # around the spear axis so they visibly wrap the wood.
    palm = rounded_box(g, (SPEAR_X + 0.012, 1.535, SPEAR_Z - 0.028), (0.020, 0.042, 0.016), 0.010)
    hand = palm
    for i in range(4):
        fy = 1.505 + i * 0.021
        finger = torus_y(g, (SPEAR_X, fy, SPEAR_Z), 0.021, 0.0085)
        finger = intersect(finger, half_space(g.Z, SPEAR_Z - 0.012))
        hand = smooth_union(hand, finger, 0.004)
    thumb = capsule(g, (SPEAR_X + 0.02, 1.575, SPEAR_Z - 0.02), (SPEAR_X - 0.018, 1.585, SPEAR_Z + 0.012), 0.0095)
    hand = smooth_union(hand, thumb, 0.005)
    add(hand, 0.012)
    # Left arm: down and out, hand resting over the top rim of the shield.
    sh2 = (0.20, 1.45, 0.0)
    el2 = (0.33, 1.21, 0.03)
    rim_top = (SHIELD_C[0] + 0.025 - 0.003, SHIELD_C[1] + SHIELD_R - 0.008, SHIELD_C[2])
    wr2 = (rim_top[0] - 0.05, rim_top[1] + 0.055, rim_top[2] + 0.01)
    add(sphere(g, sh2, 0.056))
    add(tapered_capsule(g, sh2, el2, 0.048, 0.038))
    add(sphere(g, el2, 0.040))
    add(tapered_capsule(g, el2, wr2, 0.038, 0.027))
    palm2 = rounded_box(g, (rim_top[0] - 0.024, rim_top[1] + 0.028, rim_top[2] + 0.01), (0.014, 0.030, 0.036), 0.010)
    hand2 = palm2
    for i in range(4):
        fz = rim_top[2] - 0.030 + i * 0.020
        finger = torus_z(g, (rim_top[0], rim_top[1], fz), 0.023, 0.0085)
        finger = intersect(finger, union(half_space(g.Y, rim_top[1] - 0.005), half_space(g.X, rim_top[0])))
        finger = intersect(finger, half_space(g.X, rim_top[0] - 0.026))
        hand2 = smooth_union(hand2, finger, 0.004)
    thumb2 = capsule(g, (rim_top[0] - 0.03, rim_top[1] + 0.02, rim_top[2] + 0.045), (rim_top[0] - 0.03, rim_top[1] - 0.03, rim_top[2] + 0.06), 0.0095)
    hand2 = smooth_union(hand2, thumb2, 0.005)
    add(hand2, 0.012)
    # Feet showing under the hem.
    for s, zf in ((-1, 0.22), (1, 0.27)):
        foot = ellipsoid(g, (s * 0.09, 0.045, zf), (0.050, 0.038, 0.125))
        foot = smooth_union(foot, sphere(g, (s * 0.09, 0.07, zf - 0.10), 0.045), 0.02)
        for i in range(5):
            tx = s * 0.09 + (i - 2) * 0.019
            foot = smooth_union(foot, capsule(g, (tx, 0.030, zf + 0.09), (tx, 0.030, zf + 0.125 - abs(i - 1) * 0.008), 0.011), 0.005)
        add(foot, 0.02)
    return d


def sculpt_sandals(g):
    d = None
    for s, zf in ((-1, 0.22), (1, 0.27)):
        sole = ellipsoid(g, (s * 0.09, 0.012, zf + 0.01), (0.056, 0.012, 0.135))
        strap = intersect(shell(ellipsoid(g, (s * 0.09, 0.045, zf), (0.054, 0.042, 0.129)), 0.006),
                          half_space(np.abs(g.Z - (zf + 0.02)), 0.008, keep_above=False))
        strap2 = intersect(shell(ellipsoid(g, (s * 0.09, 0.045, zf), (0.054, 0.042, 0.129)), 0.006),
                           half_space(np.abs(g.Z - (zf - 0.06)), 0.008, keep_above=False))
        part = union(sole, union(strap, strap2))
        d = part if d is None else union(d, part)
    return d


def sculpt_shield(g):
    """Round hoplite shield resting on the ground at her left, convex face
    outward, with a rim, concentric bands and a central boss."""
    c = SHIELD_C
    local = g.transformed(rotate_z(-0.15, c))
    disc = cylinder_x(local, c, SHIELD_R, 0.010)
    dome = sphere(local, (c[0] - 1.10, c[1], c[2]), 1.20)
    disc = intersect(disc + 0.0, dome - 0.0)
    disc = union(disc, intersect(cylinder_x(local, c, SHIELD_R, 0.045), subtract(dome, sphere(local, (c[0] - 1.10, c[1], c[2]), 1.185))))
    d = disc
    d = smooth_union(d, torus_x(local, (c[0] + 0.025, c[1], c[2]), SHIELD_R - 0.008, 0.014), 0.01)
    d = smooth_union(d, torus_x(local, (c[0] + 0.045, c[1], c[2]), SHIELD_R * 0.62, 0.008), 0.006)
    d = smooth_union(d, torus_x(local, (c[0] + 0.052, c[1], c[2]), SHIELD_R * 0.30, 0.008), 0.006)
    d = smooth_union(d, sphere(local, (c[0] + 0.02, c[1], c[2]), 0.075), 0.02)
    # Owl relief: Athena's bird, simplified as a body with two large eyes.
    owl = ellipsoid(local, (c[0] + 0.055, c[1] - 0.20, c[2]), (0.012, 0.065, 0.045))
    for s in (-1, 1):
        owl = smooth_union(owl, torus_x(local, (c[0] + 0.062, c[1] - 0.17, c[2] + s * 0.024), 0.014, 0.005), 0.004)
    d = smooth_union(d, owl, 0.008)
    return d


def sculpt_spear(g):
    shaft = capsule(g, (SPEAR_X, 0.0, SPEAR_Z), (SPEAR_X, 2.28, SPEAR_Z), 0.012)
    butt = tapered_capsule(g, (SPEAR_X, 0.0, SPEAR_Z), (SPEAR_X, -0.05, SPEAR_Z), 0.014, 0.004)
    return union(shaft, butt)


def sculpt_spearhead(g):
    socket = tapered_capsule(g, (SPEAR_X, 2.26, SPEAR_Z), (SPEAR_X, 2.36, SPEAR_Z), 0.016, 0.010)
    blade = ellipsoid(g, (SPEAR_X, 2.48, SPEAR_Z), (0.030, 0.16, 0.007))
    midrib = ellipsoid(g, (SPEAR_X, 2.46, SPEAR_Z), (0.008, 0.15, 0.012))
    return smooth_union(socket, smooth_union(blade, midrib, 0.006), 0.01)


def sculpt_plinth(g):
    d = cylinder_y(g, (0.10, -0.04, 0.02), 0.72, 0.035)
    d = smooth_union(d, cylinder_y(g, (0.10, -0.07, 0.02), 0.78, 0.02), 0.01)
    return d


# ---------------------------------------------------------------- part table

def part_table(fast):
    f = 1.7 if fast else 1.0
    return [
        # name, material, sculpt fn, bounds, voxel (m), decimation target (tris)
        ("head", "skin", sculpt_head, ((-0.115, 0.115), (1.455, 1.87), (-0.13, 0.145)), 0.0012 * f, 160_000),
        ("hair", "hair", sculpt_hair, ((-0.135, 0.135), (1.32, 1.86), (-0.17, 0.12)), 0.0016 * f, 90_000),
        ("helmet", "helmet", sculpt_helmet, ((-0.17, 0.17), (1.56, 2.00), (-0.25, 0.22)), 0.0018 * f, 110_000),
        ("plume", "plume", sculpt_plume, ((-0.08, 0.08), (1.50, 2.05), (-0.36, 0.20)), 0.0018 * f, 60_000),
        ("arms", "skin", sculpt_arms, ((-0.45, 0.65), (-0.01, 1.66), (-0.12, 0.42)), 0.0030 * f, 120_000),
        ("peplos", "peplos", sculpt_peplos, ((-0.37, 0.37), (-0.005, 1.55), (-0.36, 0.40)), 0.0040 * f, 160_000),
        ("belt", "belt", sculpt_belt, ((-0.24, 0.24), (1.14, 1.21), (-0.20, 0.17)), 0.0025 * f, 20_000),
        ("aegis", "aegis", sculpt_aegis, ((-0.30, 0.30), (1.05, 1.60), (-0.20, 0.22)), 0.0022 * f, 140_000),
        ("gorgon", "gorgon", sculpt_gorgon, ((-0.10, 0.10), (1.27, 1.48), (0.13, 0.22)), 0.0012 * f, 50_000),
        ("sandals", "sandal", sculpt_sandals, ((-0.18, 0.18), (-0.005, 0.10), (0.05, 0.45)), 0.0025 * f, 20_000),
        ("shield", "shield", sculpt_shield, ((0.40, 0.72), (-0.01, 0.95), (-0.48, 0.52)), 0.0030 * f, 90_000),
        ("spear", "spear", sculpt_spear, ((SPEAR_X - 0.03, SPEAR_X + 0.03), (-0.07, 2.32), (SPEAR_Z - 0.03, SPEAR_Z + 0.03)), 0.0025 * f, 20_000),
        ("spearhead", "spearhead", sculpt_spearhead, ((SPEAR_X - 0.05, SPEAR_X + 0.05), (2.22, 2.66), (SPEAR_Z - 0.03, SPEAR_Z + 0.03)), 0.0015 * f, 20_000),
        ("plinth", "plinth", sculpt_plinth, ((-0.72, 0.92), (-0.10, 0.01), (-0.80, 0.84)), 0.0080 * f, 10_000),
    ]


# ---------------------------------------------------------------- exporters

def write_obj(path, meshes):
    mtl_path = os.path.splitext(path)[0] + ".mtl"
    with open(mtl_path, "w") as m:
        for name, (rgb, metal, rough) in MATERIALS.items():
            m.write(f"newmtl {name}\nKd {rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f}\nKs {metal:.2f} {metal:.2f} {metal:.2f}\nNs {int((1 - rough) * 200)}\n\n")
    offset = 1
    with open(path, "w") as f:
        f.write(f"mtllib {os.path.basename(mtl_path)}\n")
        for name, material, verts, faces, normals in meshes:
            f.write(f"o {name}\nusemtl {material}\n")
            np.savetxt(f, verts, fmt="v %.5f %.5f %.5f")
            np.savetxt(f, normals, fmt="vn %.4f %.4f %.4f")
            idx = faces + offset
            np.savetxt(f, np.column_stack([idx[:, 0], idx[:, 0], idx[:, 1], idx[:, 1], idx[:, 2], idx[:, 2]]), fmt="f %d//%d %d//%d %d//%d")
            offset += len(verts)


def write_glb(path, meshes):
    """Minimal binary glTF 2.0 writer: one mesh primitive per part with a
    PBR material, float32 positions/normals and uint32 indices."""
    buffers = []
    buffer_views = []
    accessors = []
    materials = []
    material_index = {}
    primitives = []
    offset = 0

    def add_view(data, target):
        nonlocal offset
        data = np.ascontiguousarray(data)
        raw = data.tobytes()
        pad = (-len(raw)) % 4
        buffers.append(raw + b"\0" * pad)
        buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(raw), "target": target})
        offset += len(raw) + pad
        return len(buffer_views) - 1

    for name, material, verts, faces, normals in meshes:
        if material not in material_index:
            rgb, metal, rough = MATERIALS[material]
            material_index[material] = len(materials)
            materials.append({"name": material, "pbrMetallicRoughness": {"baseColorFactor": [*rgb, 1.0], "metallicFactor": metal, "roughnessFactor": rough}})
        v32 = verts.astype(np.float32)
        n32 = normals.astype(np.float32)
        i32 = faces.astype(np.uint32).ravel()
        pv = add_view(v32, 34962)
        accessors.append({"bufferView": pv, "componentType": 5126, "count": len(v32), "type": "VEC3", "min": v32.min(0).tolist(), "max": v32.max(0).tolist()})
        nv = add_view(n32, 34962)
        accessors.append({"bufferView": nv, "componentType": 5126, "count": len(n32), "type": "VEC3"})
        iv = add_view(i32, 34963)
        accessors.append({"bufferView": iv, "componentType": 5125, "count": len(i32), "type": "SCALAR"})
        primitives.append({"name": name, "attributes": {"POSITION": len(accessors) - 3, "NORMAL": len(accessors) - 2}, "indices": len(accessors) - 1, "material": material_index[material]})

    bin_blob = b"".join(buffers)
    gltf = {
        "asset": {"version": "2.0", "generator": "generate_athena.py"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Athena"}],
        "meshes": [{"name": "Athena", "primitives": [{k: v for k, v in p.items() if k != "name"} for p in primitives]}],
        "materials": materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(bin_blob)}],
    }
    json_blob = json.dumps(gltf, separators=(",", ":")).encode()
    json_blob += b" " * ((-len(json_blob)) % 4)
    total = 12 + 8 + len(json_blob) + 8 + len(bin_blob)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(json_blob), 0x4E4F534A))
        f.write(json_blob)
        f.write(struct.pack("<II", len(bin_blob), 0x004E4942))
        f.write(bin_blob)


def write_viewer_json(path, meshes):
    """Quantised buffers for the self-contained HTML viewer: positions as
    uint16 inside the part's bounding box, normals as int8, indices uint32.
    This keeps the embedded page well under the artifact size limit."""
    parts = []
    for name, material, verts, faces, normals in meshes:
        lo = verts.min(0)
        hi = verts.max(0)
        span = np.maximum(hi - lo, 1e-6)
        q = np.round((verts - lo) / span * 65535).astype(np.uint16)
        n8 = np.clip(np.round(normals * 127), -127, 127).astype(np.int8)
        parts.append({
            "name": name,
            "material": material,
            "min": lo.tolist(),
            "max": hi.tolist(),
            "vertexCount": int(len(verts)),
            "positions": base64.b64encode(np.ascontiguousarray(q).tobytes()).decode(),
            "normals": base64.b64encode(np.ascontiguousarray(n8).tobytes()).decode(),
            "indices": base64.b64encode(np.ascontiguousarray(faces.astype(np.uint32)).tobytes()).decode(),
        })
    with open(path, "w") as f:
        json.dump({"materials": {k: {"color": v[0], "metalness": v[1], "roughness": v[2]} for k, v in MATERIALS.items()}, "parts": parts}, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="", help="comma-separated subset of part names")
    ap.add_argument("--fast", action="store_true", help="coarser voxels for quick previews")
    ap.add_argument("--no-decimate", action="store_true")
    ap.add_argument("--web-ratio", type=float, default=0.35, help="triangle budget of the viewer LOD relative to the full one")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    wanted = set(p for p in args.parts.split(",") if p)
    meshes = []
    web_meshes = []
    t_all = time.time()
    for name, material, fn, bounds, voxel, target in part_table(args.fast):
        if wanted and name not in wanted:
            continue
        t0 = time.time()
        g = Grid(bounds, voxel)
        print(f"{name}: grid {g.X.shape} @ {voxel * 1000:.2f} mm")
        field = fn(g)
        result = surface(g, field, name)
        del g, field
        if result is None:
            continue
        verts, faces = result
        if not args.no_decimate:
            verts, faces = decimate(verts, faces, target)
            print(f"  [{name}] decimated to {len(faces):,} tris")
        meshes.append((name, material, verts, faces, vertex_normals(verts, faces)))
        # A lighter copy for the self-contained web viewer: base64 buffers for
        # a million triangles would push the page past what phones and the
        # artifact host accept.
        # The face is the point of the model, so it keeps its full budget.
        wv, wf = decimate(verts, faces, target if name == "head" else int(target * args.web_ratio))
        web_meshes.append((name, material, wv, wf, vertex_normals(wv, wf)))
        print(f"  [{name}] {time.time() - t0:.1f}s")
    suffix = "" if not wanted else "_" + "_".join(sorted(wanted))
    write_obj(os.path.join(OUT_DIR, f"athena{suffix}.obj"), meshes)
    write_glb(os.path.join(OUT_DIR, f"athena{suffix}.glb"), meshes)
    write_viewer_json(os.path.join(OUT_DIR, f"athena_mesh{suffix}.json"), web_meshes)
    print(f"web LOD: {sum(len(m[3]) for m in web_meshes):,} triangles")
    total = sum(len(m[3]) for m in meshes)
    print(f"done: {len(meshes)} parts, {total:,} triangles, {time.time() - t_all:.1f}s")


if __name__ == "__main__":
    main()
