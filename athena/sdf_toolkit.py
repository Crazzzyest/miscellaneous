"""
Signed-distance-field sculpting toolkit used by generate_athena.py.

Every primitive returns a float32 array of signed distances evaluated on a
voxel grid: negative inside, positive outside. Parts are sculpted by
combining primitives (smooth unions for organic blending, subtractions for
hollows) and then surfaced with marching cubes at level 0.
"""
import numpy as np
from skimage import measure

F32 = np.float32


class Grid:
    """Holds the voxel coordinate arrays for one part. Kept separate per part
    so that the face can be sampled at ~1 mm while the dress uses ~4 mm."""

    def __init__(self, bounds, voxel):
        (x0, x1), (y0, y1), (z0, z1) = bounds
        self.voxel = voxel
        self.origin = np.array([x0, y0, z0], dtype=F32)
        xs = np.arange(x0, x1 + voxel, voxel, dtype=F32)
        ys = np.arange(y0, y1 + voxel, voxel, dtype=F32)
        zs = np.arange(z0, z1 + voxel, voxel, dtype=F32)
        self.X, self.Y, self.Z = np.meshgrid(xs, ys, zs, indexing="ij")

    def transformed(self, fn):
        """Return a lightweight grid whose coordinates were remapped by fn.
        Used to evaluate a primitive in a rotated/tilted local frame."""
        g = Grid.__new__(Grid)
        g.voxel = self.voxel
        g.origin = self.origin
        g.X, g.Y, g.Z = fn(self.X, self.Y, self.Z)
        return g


# ---------------------------------------------------------------- transforms

def rotate_x(angle_rad, pivot):
    """Rotate coordinates about the X axis around a pivot point. Positive angle
    tips the +Z (front) direction upward, which is what a helmet pushed back
    on the head needs."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    px, py, pz = pivot

    def fn(X, Y, Z):
        y = Y - py
        z = Z - pz
        return X, (c * y - s * z + py).astype(F32), (s * y + c * z + pz).astype(F32)
    return fn


def rotate_y(angle_rad, pivot):
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    px, py, pz = pivot

    def fn(X, Y, Z):
        x = X - px
        z = Z - pz
        return (c * x + s * z + px).astype(F32), Y, (-s * x + c * z + pz).astype(F32)
    return fn


def rotate_z(angle_rad, pivot):
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    px, py, pz = pivot

    def fn(X, Y, Z):
        x = X - px
        y = Y - py
        return (c * x - s * y + px).astype(F32), (s * x + c * y + py).astype(F32), Z
    return fn


# ---------------------------------------------------------------- primitives

def sphere(g, center, r):
    cx, cy, cz = center
    return np.sqrt((g.X - cx) ** 2 + (g.Y - cy) ** 2 + (g.Z - cz) ** 2) - F32(r)


def ellipsoid(g, center, radii):
    """Inigo Quilez's bound-preserving ellipsoid approximation; exact enough
    for surfacing at level 0."""
    cx, cy, cz = center
    rx, ry, rz = radii
    px = (g.X - cx) / rx
    py = (g.Y - cy) / ry
    pz = (g.Z - cz) / rz
    k0 = np.sqrt(px * px + py * py + pz * pz)
    k1 = np.sqrt((px / rx) ** 2 + (py / ry) ** 2 + (pz / rz) ** 2)
    return (k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)).astype(F32)


def capsule(g, a, b, r):
    ax, ay, az = a
    bx, by, bz = b
    bax, bay, baz = bx - ax, by - ay, bz - az
    denom = bax * bax + bay * bay + baz * baz
    pax = g.X - ax
    pay = g.Y - ay
    paz = g.Z - az
    h = np.clip((pax * bax + pay * bay + paz * baz) / denom, 0.0, 1.0)
    dx = pax - bax * h
    dy = pay - bay * h
    dz = paz - baz * h
    return (np.sqrt(dx * dx + dy * dy + dz * dz) - r).astype(F32)


def tapered_capsule(g, a, b, ra, rb):
    """Capsule whose radius interpolates from ra at a to rb at b (limbs)."""
    ax, ay, az = a
    bx, by, bz = b
    bax, bay, baz = bx - ax, by - ay, bz - az
    denom = bax * bax + bay * bay + baz * baz
    pax = g.X - ax
    pay = g.Y - ay
    paz = g.Z - az
    h = np.clip((pax * bax + pay * bay + paz * baz) / denom, 0.0, 1.0)
    dx = pax - bax * h
    dy = pay - bay * h
    dz = paz - baz * h
    return (np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * h)).astype(F32)


def box(g, center, half):
    cx, cy, cz = center
    hx, hy, hz = half
    qx = np.abs(g.X - cx) - hx
    qy = np.abs(g.Y - cy) - hy
    qz = np.abs(g.Z - cz) - hz
    outside = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    inside = np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0)
    return (outside + inside).astype(F32)


def rounded_box(g, center, half, r):
    return box(g, center, half) - F32(r)


def cylinder_y(g, center, r, half_h):
    cx, cy, cz = center
    d_rad = np.sqrt((g.X - cx) ** 2 + (g.Z - cz) ** 2) - r
    d_y = np.abs(g.Y - cy) - half_h
    outside = np.sqrt(np.maximum(d_rad, 0) ** 2 + np.maximum(d_y, 0) ** 2)
    inside = np.minimum(np.maximum(d_rad, d_y), 0)
    return (outside + inside).astype(F32)


def cylinder_x(g, center, r, half_w):
    cx, cy, cz = center
    d_rad = np.sqrt((g.Y - cy) ** 2 + (g.Z - cz) ** 2) - r
    d_x = np.abs(g.X - cx) - half_w
    outside = np.sqrt(np.maximum(d_rad, 0) ** 2 + np.maximum(d_x, 0) ** 2)
    inside = np.minimum(np.maximum(d_rad, d_x), 0)
    return (outside + inside).astype(F32)


def torus_y(g, center, major, minor):
    cx, cy, cz = center
    q = np.sqrt((g.X - cx) ** 2 + (g.Z - cz) ** 2) - major
    return (np.sqrt(q * q + (g.Y - cy) ** 2) - minor).astype(F32)


def torus_x(g, center, major, minor):
    cx, cy, cz = center
    q = np.sqrt((g.Y - cy) ** 2 + (g.Z - cz) ** 2) - major
    return (np.sqrt(q * q + (g.X - cx) ** 2) - minor).astype(F32)


def torus_z(g, center, major, minor):
    cx, cy, cz = center
    q = np.sqrt((g.X - cx) ** 2 + (g.Y - cy) ** 2) - major
    return (np.sqrt(q * q + (g.Z - cz) ** 2) - minor).astype(F32)


def half_space(value, threshold, keep_above=True):
    """Distance to a plane: negative on the side that is kept."""
    return (threshold - value).astype(F32) if keep_above else (value - threshold).astype(F32)


# ---------------------------------------------------------------- combinators

def union(a, b):
    return np.minimum(a, b)


def intersect(a, b):
    return np.maximum(a, b)


def subtract(a, b):
    return np.maximum(a, -b)


def smooth_union(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return (b + (a - b) * h - k * h * (1.0 - h)).astype(F32)


def smooth_subtract(a, b, k):
    h = np.clip(0.5 - 0.5 * (a + b) / k, 0.0, 1.0)
    return (a + (-b - a) * h + k * h * (1.0 - h)).astype(F32)


def smooth_intersect(a, b, k):
    h = np.clip(0.5 - 0.5 * (b - a) / k, 0.0, 1.0)
    return (b + (a - b) * h + k * h * (1.0 - h)).astype(F32)


def shell(d, thickness):
    return (np.abs(d) - thickness * 0.5).astype(F32)


# ---------------------------------------------------------------- surfacing

def surface(g, field, name):
    """Marching cubes -> (vertices, faces) in world coordinates with outward
    winding. Returns None when the field never crosses zero."""
    if field.min() >= 0 or field.max() <= 0:
        print(f"  [{name}] empty field, skipped")
        return None
    # Pad with positive values so surfaces that touch the grid edge get closed
    # instead of leaving open holes.
    padded = np.pad(field, 1, mode="constant", constant_values=1.0)
    verts, faces, _, _ = measure.marching_cubes(
        padded, level=0.0, spacing=(g.voxel,) * 3, gradient_direction="ascent")
    verts = verts.astype(np.float64) - g.voxel + g.origin.astype(np.float64)
    verts, faces = ensure_outward(verts, faces)
    print(f"  [{name}] {len(verts):,} verts / {len(faces):,} tris")
    return verts, faces.astype(np.int64)


def ensure_outward(verts, faces):
    """Signed volume decides whether marching cubes handed us inward-facing
    triangles; flipping here means every downstream consumer can assume CCW."""
    v0 = verts[faces[:, 0]]
    v1 = verts[faces[:, 1]]
    v2 = verts[faces[:, 2]]
    vol = np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6.0
    if vol < 0:
        faces = faces[:, ::-1].copy()
    return verts, faces


def decimate(verts, faces, target_tris):
    """Quadric decimation keeps the sculpted detail where curvature lives and
    collapses the flat regions, which is what keeps the export under control."""
    if len(faces) <= target_tris:
        return verts, faces
    import fast_simplification
    reduction = 1.0 - target_tris / len(faces)
    out_v, out_f = fast_simplification.simplify(
        verts.astype(np.float32), faces.astype(np.int32), target_reduction=reduction, agg=5)
    out_v = out_v.astype(np.float64)
    out_f = out_f.astype(np.int64)
    out_v, out_f = ensure_outward(out_v, out_f)
    return out_v, out_f


def vertex_normals(verts, faces):
    fn = np.cross(verts[faces[:, 1]] - verts[faces[:, 0]], verts[faces[:, 2]] - verts[faces[:, 0]])
    normals = np.zeros_like(verts)
    for i in range(3):
        np.add.at(normals, faces[:, i], fn)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    return normals / np.maximum(lengths, 1e-12)
