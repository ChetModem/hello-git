"""Bobby Panda v3: an original heavy-set panda adventurer mini (25 mm base, ~31 mm tall).

Sculpted as signed distance fields (smooth-blended ellipsoids / round cones, carved grooves, fur noise)
and meshed with marching cubes, so the forms are organic instead of primitive-on-primitive.
Colour regions are a priority partition of one solid, so the parts share their boundaries exactly.

    python3 bobby_panda.py [voxel_mm]     -> writes bobby_fields_<voxel>.npz (part fields on a grid)
"""
import sys, numpy as np

F = np.float32
def nrm(v): v = np.asarray(v, float); return v / np.linalg.norm(v)

# ---------------------------------------------------------------- primitives (X, Y, Z are arrays)
def sph(X, Y, Z, c, r): return np.sqrt((X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2) - r
def local(X, Y, Z, c, R):
    x, y, z = X - c[0], Y - c[1], Z - c[2]
    if R is None: return x, y, z
    return (R[0, 0] * x + R[0, 1] * y + R[0, 2] * z, R[1, 0] * x + R[1, 1] * y + R[1, 2] * z, R[2, 0] * x + R[2, 1] * y + R[2, 2] * z)
def ell(X, Y, Z, c, r, R=None):
    x, y, z = local(X, Y, Z, c, R)
    k0 = np.sqrt((x / r[0]) ** 2 + (y / r[1]) ** 2 + (z / r[2]) ** 2)
    k1 = np.sqrt((x / r[0] ** 2) ** 2 + (y / r[1] ** 2) ** 2 + (z / r[2] ** 2) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)
def rbox(X, Y, Z, c, h, rr, R=None):
    x, y, z = local(X, Y, Z, c, R)
    qx, qy, qz = np.abs(x) - h[0] + rr, np.abs(y) - h[1] + rr, np.abs(z) - h[2] + rr
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2 + np.maximum(qz, 0) ** 2)
    return out + np.minimum(np.maximum(qx, np.maximum(qy, qz)), 0) - rr
def rcone(X, Y, Z, a, b, r1, r2):
    """Round cone (capsule with different end radii) from a to b."""
    a, b = np.asarray(a, float), np.asarray(b, float); ba = b - a
    l2 = ba @ ba; rr = r1 - r2; a2 = l2 - rr * rr; il2 = 1.0 / l2
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    y = px * ba[0] + py * ba[1] + pz * ba[2]; z = y - l2
    qx, qy, qz = px * l2 - ba[0] * y, py * l2 - ba[1] * y, pz * l2 - ba[2] * y
    x2 = qx * qx + qy * qy + qz * qz; y2 = y * y * l2; z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
    d1 = np.sqrt(x2 + z2) * il2 - r2
    d2 = np.sqrt(x2 + y2) * il2 - r1
    return np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))
def cap(X, Y, Z, a, b, r): return rcone(X, Y, Z, a, b, r, r)
def poly(X, Y, Z, pts, r):
    d = None
    for p, q in zip(pts[:-1], pts[1:]):
        e = cap(X, Y, Z, p, q, r); d = e if d is None else np.minimum(d, e)
    return d
def rcyl_x(X, Y, Z, c, r, h, rr):
    x, y, z = X - c[0], Y - c[1], Z - c[2]
    dx, dr = np.abs(x) - h + rr, np.sqrt(y * y + z * z) - r + rr
    return np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dr, 0) ** 2) + np.minimum(np.maximum(dx, dr), 0) - rr
def leaf(X, Y, Z, base, direc, normal, L, W, T, curl=0.0):
    """Pointed leaf (vesica outline) from base along direc, flat across normal, thickness T, curling by curl."""
    u = nrm(direc); n = nrm(normal); n = nrm(n - (n @ u) * u); v = np.cross(n, u)
    c = np.asarray(base, float) + u * L / 2
    px, py, pz = X - c[0], Y - c[1], Z - c[2]
    lu = px * u[0] + py * u[1] + pz * u[2]; lv = px * v[0] + py * v[1] + pz * v[2]; lw = px * n[0] + py * n[1] + pz * n[2]
    lw = lw - curl * (lu / (L / 2)) ** 2 + curl * 0.35            # gentle curve along the leaf
    b = L / 2; hw = W / 2; d = (b * b - hw * hw) / (2 * hw); r = d + hw
    ax, ay = np.abs(lv), np.abs(lu)
    d2 = np.where((ay - b) * d > ax * b, np.sqrt(ax ** 2 + (ay - b) ** 2), np.sqrt((ax + d) ** 2 + ay ** 2) - r)
    t = T / 2 * np.clip(1.0 - (ay / b) ** 2 * 0.45, 0.3, 1)            # thinner toward the tip, still >= ~0.9 mm
    return np.maximum(d2, np.abs(lw) - t)
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b + (a - b) * h - k * h * (1 - h)
def smax(a, b, k): return -smin(-a, -b, k)
def rotm(axis, deg):
    a = nrm(axis); t = np.radians(deg); c, s = np.cos(t), np.sin(t); x, y, z = a
    return np.array([[c + x * x * (1 - c), x * y * (1 - c) - z * s, x * z * (1 - c) + y * s],
                     [y * x * (1 - c) + z * s, c + y * y * (1 - c), y * z * (1 - c) - x * s],
                     [z * x * (1 - c) - y * s, z * y * (1 - c) + x * s, c + z * z * (1 - c)]])
def inv(R): return R.T                                               # world->local for ell/rbox

_rng = np.random.default_rng(7)
_W1 = [(nrm(_rng.normal(size=3) * [1, 1, 0.25]) * 2 * np.pi / _rng.uniform(0.45, 0.7), _rng.uniform(0, 6.3)) for _ in range(14)]
_W2 = [(nrm(_rng.normal(size=3)) * 2 * np.pi / _rng.uniform(2.6, 4.0), _rng.uniform(0, 6.3)) for _ in range(10)]
def fur(X, Y, Z):          # streaky (mostly vertical) fur noise, about -1..1
    s = 0
    for k, ph in _W1: s = s + np.sin(k[0] * X + k[1] * Y + k[2] * Z + ph)
    return s / np.sqrt(len(_W1) / 2)
def blotch(X, Y, Z):       # softer noise for tufty colour edges
    s = 0
    for k, ph in _W2: s = s + np.sin(k[0] * X + k[1] * Y + k[2] * Z + ph)
    return s / np.sqrt(len(_W2) / 2)
SEEDS = np.array([[r * np.cos(a), r * np.sin(a)] for r, a in zip(np.sqrt(_rng.uniform(0, 1, 16)) * 12, _rng.uniform(0, 6.3, 16))])
SEED_H = _rng.uniform(0.0, 0.3, len(SEEDS))

# ---------------------------------------------------------------- layout (mm). Panda faces -y, +z up.
BASE_TOP = 3.0
LEG = {s: dict(hip=(s * 4.0, 0.8, 9.8), ank=(s * 3.9, -0.5, 4.7), foot=(s * 4.1, -1.9, 4.0)) for s in (-1, 1)}
HEAD_C, HEAD_R = (0, -0.6, 24.6), (5.7, 5.3, 5.3)
# raised right paw (-x) holds the bamboo shoot to the corner of the mouth; left paw (+x) rests on the belly
RA = dict(S=(-6.0, 0.6, 19.6), E=(-7.75, -1.4, 15.0), W=(-6.9, -5.5, 20.7), F=(-6.25, -6.45, 22.2))   # elbow rests on the flank
LA = dict(S=(6.0, 0.6, 19.6), E=(8.2, 0.2, 14.4), W=(6.6, -4.0, 11.9), F=(6.0, -4.9, 11.5))
BAM_B = np.array([-1.45, -5.95, 22.7])
BAM_A = BAM_B + (np.array([-11.0, -7.25, 21.35]) - BAM_B) * 0.85      # short stick, held like a cigar
BAM_A[2] = 23.3                                                         # outer end tipped up: grows out of the fist
STAFF_TOP, STAFF_BOT = np.array([-8.3, 11.7, 31.0]), np.array([6.6, 10.0, 4.0])   # quarterstaff on the back, 29 deg from vertical

def torso(X, Y, Z):
    d = ell(X, Y, Z, (0, 0.3, 11.7), (8.0, 6.8, 7.4))
    d = smin(d, ell(X, Y, Z, (0, -2.2, 11.3), (6.6, 5.2, 6.0)), 2.0)                       # pot belly
    d = smin(d, ell(X, Y, Z, (0, 0.4, 17.4), (6.9, 5.7, 5.6)), 2.0)                        # chest
    for s in (-1, 1): d = smin(d, sph(X, Y, Z, (s * 5.7, 0.7, 19.4), 2.9), 1.6)           # shoulders
    return d
def head(X, Y, Z):
    d = ell(X, Y, Z, HEAD_C, HEAD_R)
    for s in (-1, 1): d = smin(d, ell(X, Y, Z, (s * 2.9, -3.1, 22.0), (3.0, 2.5, 2.4)), 1.2)   # jowls
    d = smin(d, ell(X, Y, Z, (0, -3.3, 20.9), (3.2, 2.4, 1.7)), 1.0)                       # double chin
    d = smin(d, ell(X, Y, Z, (0, -4.9, 23.3), (2.3, 1.7, 1.55)), 1.0)                      # muzzle
    return d
def core(X, Y, Z):          # body without limbs: used to place surface details
    return smin(torso(X, Y, Z), head(X, Y, Z), 2.0)

def surf_y(fn, x, z, y0=-16.0, sign=1):
    """March along +y (sign=1, from the front) or -y (from the back) to the surface of fn at (x, z)."""
    x = np.atleast_1d(np.asarray(x, float)); z = np.atleast_1d(np.asarray(z, float)); y = np.full_like(x, y0)
    lo = y.copy()
    for _ in range(400):                                   # step until inside, then bisect to the surface
        d = fn(x, y, z); out = d > 0
        lo = np.where(out, y, lo); y = np.where(out, y + sign * np.maximum(d * 0.5, 0.01), y)
    hi = y
    for _ in range(40):
        m = (lo + hi) / 2; d = fn(x, m, z); lo = np.where(d > 0, m, lo); hi = np.where(d > 0, hi, m)
    return (lo + hi) / 2
def on_face(pts, out=0.0):
    """(x, z) points -> 3D points on the head/body front surface, pushed out along -y by `out`."""
    pts = np.asarray(pts, float); y = surf_y(core, pts[:, 0], pts[:, 1])
    return [np.array([x, yy - out, z]) for (x, z), yy in zip(pts, y)]

# precomputed surface anchors for face details
EYE = {s: on_face([(s * 2.35, 25.65)])[0] for s in (-1, 1)}
NOSE = on_face([(0, 24.05)], 0.25)[0]
MOUTH_R = on_face([(0, 23.5), (0, 22.98), (0.65, 22.78), (1.35, 22.86), (1.9, 23.12), (2.15, 23.38)], -0.05)
MOUTH_L = on_face([(0, 22.98), (-0.6, 22.82), (-1.0, 22.82)], -0.05)
CHIN = on_face([(-2.7, 21.55), (-1.5, 21.0), (0, 20.85), (1.5, 21.0), (2.7, 21.55)], 0.03)        # soft double-chin fold
# chest tuft: a cluster of short hair flicks (irregular so it reads as fur, not a symbol)
TUFTS = [on_face(p, -0.02) for p in ([(-0.2, 15.9), (-0.35, 15.25)], [(0.45, 15.7), (0.35, 15.05)], [(-0.95, 15.3), (-0.95, 14.7)],
                                     [(1.05, 15.15), (1.15, 14.55)], [(0.05, 14.7), (-0.05, 14.05)], [(-0.6, 14.25), (-0.75, 13.7)],
                                     [(0.7, 14.15), (0.75, 13.6)], [(0.0, 13.45), (0.1, 12.95)])]
CHEST_Y = surf_y(torso, [0.0], [17.2])[0]
STRAP_P0 = {s: np.array([s * 3.55, 0, 21.2]) for s in (-1, 1)}
STRAP_N = {s: nrm([s * 8.0, 0, 2.6]) for s in (-1, 1)}                                   # straps run from neck to armpit

def fields(X, Y, Z):
    """Return (solid, {part: claim}) for a chunk. Claims are signed fields (<0 = this colour wants it)."""
    # ---------- panda body
    body = core(X, Y, Z)
    body = smin(body, ell(X, Y, Z, (0, 6.3, 9.4), (1.3, 0.75, 1.15)), 0.6)                      # stubby tail, pressed into the rump
    legs = None
    for s in (-1, 1):
        L = LEG[s]
        d = rcone(X, Y, Z, L['hip'], L['ank'], 3.5, 2.8)
        d = smin(d, ell(X, Y, Z, L['foot'], (2.6, 3.4, 1.7), inv(rotm([0, 0, 1], -s * 12))), 1.0)
        for dx in (-0.8, 0.0, 0.8):                                                          # toes
            cx = L['foot'][0] + dx
            g = np.maximum(np.maximum(np.abs(X - cx) - 0.13, Y - (L['foot'][1] - 1.9)), BASE_TOP + 0.15 - Z)
            d = np.maximum(d, -g)
        legs = d if legs is None else np.minimum(legs, d)
    body = smin(body, legs, 1.6)
    arch = np.maximum((5.9 - 1.25 * np.abs(X)) - Z, ell(X, Y, Z, (0, 0.2, 8.0), (5.5, 5.0, 5.0)))     # self-supporting crotch
    body = smin(body, arch, 0.5)
    # ears with a cupped inside
    ears = None
    for s in (-1, 1):
        e = ell(X, Y, Z, (s * 4.05, 0.3, 28.6), (1.95, 1.25, 1.85), inv(rotm([0, 1, 0], s * 25)))
        e = smax(e, -ell(X, Y, Z, (s * 4.15, -0.95, 28.75), (1.15, 0.55, 1.05), inv(rotm([0, 1, 0], s * 25))), 0.25)
        ears = e if ears is None else np.minimum(ears, e)
    body = smin(body, ears, 0.7)
    # arms
    def arm(A, raised):
        d = rcone(X, Y, Z, A['S'], A['E'], 2.75, 2.3)
        d = smin(d, rcone(X, Y, Z, A['E'], A['W'], 2.3, 1.95), 0.6)
        paw = ell(X, Y, Z, A['F'], (1.95, 1.8, 2.15)) if raised else ell(X, Y, Z, A['F'], (1.95, 1.65, 2.0))
        d = smin(d, paw, 0.8)
        for dx in (-0.62, 0.0, 0.62):                                                         # finger grooves
            cx = A['F'][0] + dx
            g = np.maximum(np.abs(X - cx) - 0.12, Y - (A['F'][1] - 0.9))
            if not raised: g = np.maximum(g, Z - (A['F'][2] + 0.2))
            d = np.maximum(d, -np.maximum(g, -(paw - 0.0) - 0.45))
        return d
    arm_r, arm_l = arm(RA, True), arm(LA, False)
    arms = np.minimum(arm_r, arm_l)
    body = smin(body, arms, 0.9)
    # painting guides: black fur areas stand 0.15 mm proud with a tufted edge
    tuft = 0.1 * blotch(X, Y, Z)
    yoke = np.maximum(np.abs(Z - (19.4 + 0.22 * Y)) - 2.6, -(Y + 1.2))                        # shoulder band over the back
    hips = np.maximum(np.minimum(legs - 0.6, ell(X, Y, Z, (0, 0.3, 7.2), (6.9, 6.2, 3.0))), Z - 9.0 - 0.8 * np.abs(X) / 6)
    black_fur = np.minimum(np.minimum(np.minimum(legs - 0.6, arms - 0.6), ears - 0.6 - tuft), np.minimum(np.minimum(yoke, hips), legs)) + tuft
    body = body - 0.15 * np.clip(-black_fur / 0.25, 0, 1)
    # face relief: raised eye patches, lids, nose; carved mouth, chin crease, brow and chest fur strokes
    patch = None; sclera = None; lid = None; pupil = None
    for s in (-1, 1):
        e = EYE[s]
        R = inv(rotm([0, 1, 0], s * 17) @ rotm([0, 0, 1], -s * 18))
        p = ell(X, Y, Z, e + [0, 0.25, 0], (1.75, 1.4, 1.1), R)
        sc = ell(X, Y, Z, e + [0, -0.05, -0.1], (0.95, 0.5, 0.5), R)
        ld = cap(X, Y, Z, e + [-s * 0.95, 0.02, 0.22] , e + [s * 0.9, 0.0, 0.16], 0.32)
        pu = sph(X, Y, Z, e + [-s * 0.08, -0.12, -0.12], 0.4)
        patch = p if patch is None else np.minimum(patch, p); sclera = sc if sclera is None else np.minimum(sclera, sc)
        lid = ld if lid is None else np.minimum(lid, ld); pupil = pu if pupil is None else np.minimum(pupil, pu)
    body = body - 0.16 * np.clip(-patch / 0.35, 0, 1)                                     # patches stand proud
    body = body - 0.1 * np.clip(-sclera / 0.25, 0, 1)
    body = body - 0.12 * np.clip(-pupil / 0.2, 0, 1)                                      # domed pupils
    body = smin(body, lid, 0.12)
    nose = ell(X, Y, Z, NOSE, (0.98, 0.62, 0.62), inv(rotm([1, 0, 0], -12)))
    body = smin(body, nose, 0.3)
    grooves = np.minimum(poly(X, Y, Z, MOUTH_R, 0.2), poly(X, Y, Z, MOUTH_L, 0.2))
    grooves = np.minimum(grooves, sph(X, Y, Z, MOUTH_R[-1] + [0, 0.05, 0], 0.27))            # smirk dimple
    grooves = np.minimum(grooves, poly(X, Y, Z, CHIN[1:-1], 0.16))
    for t in TUFTS: grooves = np.minimum(grooves, rcone(X, Y, Z, t[0], t[1], 0.2, 0.1))   # tapered flicks
    body = smax(body, -grooves, 0.08)
        # ---------- backpack (tan), bedroll (olive), straps (tan)
    tilt = inv(rotm([1, 0, 0], -7))
    pack = rbox(X, Y, Z, (0, 7.85, 15.5), (4.2, 2.1, 4.3), 1.1, tilt)
    flap = rbox(X, Y, Z, (0, 7.95, 18.1), (4.38, 2.25, 1.95), 1.1, tilt)
    pocket = rbox(X, Y, Z, (0, 10.0, 13.5), (2.7, 0.55, 1.75), 0.45)
    pack = np.minimum(np.minimum(pack, flap), pocket)
    for s in (-1, 1):
        pack = np.minimum(pack, rbox(X, Y, Z, (s * 1.6, 10.15, 17.3), (0.45, 0.22, 2.2), 0.15, tilt))      # flap straps
        buckle = rbox(X, Y, Z, (s * 1.6, 10.05, 15.4), (0.62, 0.3, 0.45), 0.12)
        buckle = smax(buckle, -rbox(X, Y, Z, (s * 1.6, 10.4, 15.4), (0.32, 0.4, 0.17), 0.05), 0.02)
        pack = np.minimum(pack, buckle)
        pack = np.minimum(pack, rbox(X, Y, Z, (s * 4.55, 7.9, 13.6), (0.9, 1.35, 1.9), 0.7))       # side pouches
    pack = smax(pack, -rbox(X, Y, Z, (0, 10.6, 14.35), (2.8, 0.3, 0.07), 0.02), 0.02)             # pocket flap seam
    yb = 0.0 + 6.8 * np.sqrt(np.clip(1 - (X / 8.0) ** 2, 0.05, 1))                           # just inside the back at hip height
    pack = smax(pack, (11.0 + (Y - yb)) - Z, 0.2)                                             # 45-degree underside from the back
    roll = rcyl_x(X, Y, Z, (0, 8.1, 21.05), 1.8, 4.9, 0.85)
    for r_ in (0.55, 1.15):                                                                  # rolled-up spiral rings on the ends
        ring = np.maximum(np.abs(np.sqrt((Y - 8.1) ** 2 + (Z - 21.05) ** 2) - r_) - 0.1, -(np.abs(X) - 4.7))
        roll = np.maximum(roll, -ring)
    ties = None
    for s in (-1, 1):
        t = np.maximum(np.abs(X - s * 2.7) - 0.38, np.sqrt((Y - 8.1) ** 2 + (Z - 21.05) ** 2) - 2.05)
        ties = t if ties is None else np.minimum(ties, t)
    tors = torso(X, Y, Z)
    shell = np.abs(tors - 0.22) - 0.3
    straps = None
    for s in (-1, 1):
        st = np.maximum(np.maximum(shell, np.abs((X - STRAP_P0[s][0]) * STRAP_N[s][0] + (Z - STRAP_P0[s][2]) * STRAP_N[s][2]) - 0.68), 12.1 - Z)
        wrap = np.maximum(np.maximum(shell, np.abs(Z - (12.55 + 0.12 * Y)) - 0.62), np.maximum(3.6 - s * X, -3.9 - Y))   # under the arm, round the side
        st = np.minimum(st, wrap)
        straps = st if straps is None else np.minimum(straps, st)
    chest_strap = np.maximum(np.maximum(shell, np.abs(Z - 17.25) - 0.5), np.maximum(np.abs(X) - 4.6, Y))
    straps = np.minimum(straps, chest_strap)
    straps = np.minimum(straps, rbox(X, Y, Z, (0, CHEST_Y - 0.35, 17.25), (0.75, 0.32, 0.7), 0.15))   # chest buckle
    sa, sb = STAFF_TOP, STAFF_BOT
    sax = sb - sa; sL = np.linalg.norm(sax); su = sax / sL
    staff = cap(X, Y, Z, sa, sb, 1.0)
    for t in np.arange(0.1, 0.95, 0.14):                                                      # bamboo nodes every ~4 mm
        c = sa + sax * t
        staff = smin(staff, cap(X, Y, Z, c - su * 0.08, c + su * 0.08, 1.1), 0.03)
    for c, d_ in ((sa, su), (sb, -su)):                                                       # cord binding near each end
        staff = smin(staff, cap(X, Y, Z, c + d_ * 0.5, c + d_ * 1.3, 1.13), 0.05)
    loops = None
    for t in (0.47, 0.64):                                                                    # two straps tie it to the pack
        c = sa + sax * t
        rel = (X - c[0]) * su[0] + (Y - c[1]) * su[1] + (Z - c[2]) * su[2]
        rx, ry, rz = X - c[0] - rel * su[0], Y - c[1] - rel * su[1], Z - c[2] - rel * su[2]
        lp = np.maximum(np.abs(rel) - 0.4, np.abs(np.sqrt(rx * rx + ry * ry + rz * rz) - 1.15) - 0.25)
        loops = lp if loops is None else np.minimum(loops, lp)
    ties = np.minimum(ties, loops)
    tan = np.minimum(np.minimum(pack, straps), ties)
    # ---------- bamboo stick (green), held like a cigar: node rings, slanted cut end on the base
    ax = BAM_B - BAM_A; Lb = np.linalg.norm(ax); u = ax / Lb
    bam = rcone(X, Y, Z, BAM_A, BAM_B, 0.9, 0.78)
    for t in (0.12, 0.8):                                                                # nodes: a crisp ring with a groove above it
        c = BAM_A + ax * t
        bam = smin(bam, cap(X, Y, Z, c - u * 0.08, c + u * 0.08, 0.9 - 0.12 * t + 0.1), 0.03)   # node ring 0.1 mm proud
    cut_n = nrm(-u + np.array([0, 0, 1.1]))                                                  # slanted cut at the outer end
    bam = np.maximum(bam, ((X - BAM_A[0] - u[0] * 0.5) * cut_n[0] + (Y - BAM_A[1] - u[1] * 0.5) * cut_n[1] + (Z - BAM_A[2] - u[2] * 0.5) * cut_n[2]))
    bam = smax(bam, -sph(X, Y, Z, BAM_A + u * 0.05 + [0, 0, 0.55], 0.5), 0.1)                 # shallow pith dimple on the cut (no thin lip)
    green = bam
    # ---------- flagstone base (grey) with a pebble
    r = np.sqrt(X * X + Y * Y)
    dd = np.stack([(X - sx) ** 2 + (Y - sy) ** 2 for sx, sy in SEEDS])
    o = np.argsort(dd, axis=0)
    d1, d2 = np.take_along_axis(dd, o[:1], 0)[0], np.take_along_axis(dd, o[1:2], 0)[0]
    edge = (np.sqrt(d2) - np.sqrt(d1)) / 2
    top = BASE_TOP - 0.15 + SEED_H[o[0]]
    qr, qz = r - 12.5 + 0.7, Z - BASE_TOP + 0.7
    base = np.sqrt(np.maximum(qr, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qr, qz), 0) - 0.7    # rounded top edge
    base = np.maximum(np.maximum(base, Z - top), (r - 12.5 + 0.4 - Z) * 0.7071)                                 # 0.4 mm chamfer at the bed
    base = smax(base, -np.maximum(edge - 0.16, top - 0.35 - Z), 0.08)                          # cracks between the stones
    base = np.minimum(base, ell(X, Y, Z, (8.3, -5.6, BASE_TOP), (1.3, 1.2, 0.75)))
    base = np.minimum(base, ell(X, Y, Z, (9.3, -3.9, BASE_TOP - 0.1), (0.8, 0.7, 0.55)))
    base = np.maximum(base, -Z)                                                              # flat bottom
    # ---------- whole solid
    solid = smin(body, tan, 0.25)
    solid = np.minimum(solid, smin(roll, ties, 0.05))
    solid = np.minimum(solid, smin(staff, loops, 0.05))
    solid = np.minimum(solid, green)
    solid = np.minimum(solid, base)
    solid = np.maximum(solid, -Z)
    # ---------- colour claims (paint guide; priority order is applied in partition())
    black_face = np.minimum(np.minimum(patch, lid), np.minimum(nose - 0.05, pupil))
    claims = dict(
        green=green,
        arms=arms - 0.6,               # arms go over the straps
        tan=tan,
        olive=np.minimum(roll, staff),
        sclera=np.maximum(sclera, -pupil),
        black=np.minimum(black_fur, black_face),
        base=base,
    )
    return solid, claims

ORDER = ['green', 'arms', 'tan', 'olive', 'sclera', 'black', 'base']     # then white = the rest
SLOT = {'green': 7, 'arms': 1, 'tan': 5, 'olive': 4, 'sclera': 2, 'black': 1, 'base': 6, 'white': 2}

def partition(solid, claims):
    out = {}; taken = None
    for k in ORDER:
        c = claims[k]; R = c if taken is None else np.maximum(c, -taken)
        out[k] = np.maximum(solid, R)
        taken = c if taken is None else np.minimum(taken, c)
    out['white'] = np.maximum(solid, -taken)
    return out

BOUNDS = np.array([[-13.2, 13.2], [-13.2, 13.6], [-0.4, 32.6]])
def grid(vox):
    xs, ys, zs = [np.arange(lo, hi + vox / 2, vox, dtype=F) for lo, hi in BOUNDS]
    return xs, ys, zs
def build(vox, chunk=24):
    xs, ys, zs = grid(vox)
    names = ORDER + ['white']
    parts = {k: np.empty((len(xs), len(ys), len(zs)), F) for k in names}
    X, Y = np.meshgrid(xs, ys, indexing='ij')
    for i0 in range(0, len(zs), chunk):
        zc = zs[i0:i0 + chunk]
        XX = np.repeat(X[..., None], len(zc), 2); YY = np.repeat(Y[..., None], len(zc), 2); ZZ = np.broadcast_to(zc, XX.shape).astype(F)
        solid, claims = fields(XX, YY, ZZ)
        for k, v in partition(solid, claims).items(): parts[k][:, :, i0:i0 + chunk] = v
        print(f'\r z {zc[-1]:.1f}', end='', flush=True)
    print()
    return xs, ys, zs, parts

if __name__ == '__main__':
    vox = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
    xs, ys, zs, parts = build(vox)
    np.savez(f'bobby_fields_{vox:g}.npz', xs=xs, ys=ys, zs=zs, **parts)
    print('saved', {k: int((v < 0).sum()) for k, v in parts.items()})
