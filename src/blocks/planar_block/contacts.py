"""
Contact detection for planar assemblies by intersecting the surface triangles.

Two triangles of different blocks are in contact if they lie in the same plane
with opposite outward normals. Their contact region is the intersection polygon
of the two triangles (computed exactly by polygon clipping). Every non-empty
intersection is one *contact element* with one unknown normal force
lambda_e >= 0 acting at its centroid.

Consequences:
- The contact area is exact, independent of whether the triangulations of the
  two blocks match. The triangulation only defines the resolution of the
  pressure field.
- For matching triangulations (each triangle coincides with a triangle of the
  neighbour) every contact element is one pair of faces, i.e. the formulation
  is identical to the face matching of src/engine/mbd.py.

Supports ('support' option):
- 'implicit': faces that are not in contact with any block at all act as rigid
  supports (behaviour of the face matching). Faces that are partially in
  contact are only in contact with the neighbour.
- 'frame':    the frame blocks are fixed. Faces of the analysed blocks are
  supported only where they touch a frame block; all other faces without
  contact are free surfaces.

Sign convention (as in the original implementation): for a force acting
against the outward normal n at the point c of block b the column of the
contact Jacobian is [-n, (c - x_b) x n] (moment rows with the opposite sign of
r x F, consistently for loads and contacts).
"""

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree


# ---------------------------------------------------------------------------
# 2D polygon helpers (small polygons -> plain python is faster than numpy)
# ---------------------------------------------------------------------------

def _signed_area(poly):
    a = 0.
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def _area_centroid(poly):
    a = cx = cy = 0.
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        cr = x0 * y1 - x1 * y0
        a += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    a *= 0.5
    if abs(a) < 1e-300:
        return 0., (0., 0.)
    return a, (cx / (6. * a), cy / (6. * a))


def _clip(subject, clip):
    '''Sutherland-Hodgman: intersection of convex polygons (both counter-clockwise)'''
    output = subject
    n = len(clip)
    for i in range(n):
        if not output:
            break
        ax, ay = clip[i]
        bx, by = clip[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        inp = output
        output = []
        m = len(inp)
        for k in range(m):
            px, py = inp[k - 1]
            qx, qy = inp[k]
            sp_ = ex * (py - ay) - ey * (px - ax)
            sq = ex * (qy - ay) - ey * (qx - ax)
            if sq >= 0.:
                if sp_ < 0.:
                    t = sp_ / (sp_ - sq)
                    output.append((px + t * (qx - px), py + t * (qy - py)))
                output.append((qx, qy))
            elif sp_ >= 0.:
                t = sp_ / (sp_ - sq)
                output.append((px + t * (qx - px), py + t * (qy - py)))
    return output


def _same_vertices(bl_a, fa, bl_b, fb, tol):
    pa = bl_a.nodes[bl_a.cells_2D[fa]]
    pb = bl_b.nodes[bl_b.cells_2D[fb]]
    d = np.linalg.norm(pa[:, None, :] - pb[None, :, :], axis=2)
    return d.min(axis=1).max() < tol


def _ccw(poly):
    return poly if _signed_area(poly) >= 0. else poly[::-1]


# ---------------------------------------------------------------------------
# contact elements
# ---------------------------------------------------------------------------

def find_contact_elements(blocks, rel_tol=1e-6):
    '''
    Finds all contact elements between the candidate contact faces of the blocks.

    blocks: list of Block objects with nodes, cells_2D, face_normals,
            face_centers, face_areas and face_groups['contact_faces']

    Returns a dict of arrays (one entry per contact element):
        'a', 'fa', 'b', 'fb': block index and face index of both sides
        'area', 'centroid', 'normal' (outward normal of side a)
    '''
    # all candidate faces
    owner, face, centers, normals, areas, radius = [], [], [], [], [], []
    for ib, bl in enumerate(blocks):
        cf = np.asarray(bl.face_groups['contact_faces'], dtype=int)
        tri = bl.nodes[bl.cells_2D[cf]]                       # (k, 3, 3)
        c = bl.face_centers[cf]
        owner.append(np.full(len(cf), ib))
        face.append(cf)
        centers.append(c)
        normals.append(bl.face_normals[cf])
        areas.append(bl.face_areas[cf])
        radius.append(np.linalg.norm(tri - c[:, None, :], axis=2).max(axis=1))

    owner = np.concatenate(owner)
    face = np.concatenate(face)
    centers = np.vstack(centers)
    normals = np.vstack(normals)
    areas = np.concatenate(areas)
    radius = np.concatenate(radius)

    scale = max(np.ptp(centers, axis=0).max(), 1.)
    tol = rel_tol * scale

    tree = cKDTree(centers)
    pairs = tree.query_pairs(r=2. * radius.max() + tol, output_type='ndarray')
    if len(pairs) == 0:
        pairs = np.zeros((0, 2), dtype=int)
    i, j = pairs[:, 0], pairs[:, 1]

    # vectorized pre-selection: different blocks, opposite normals, same plane,
    # overlapping bounding circles
    d = centers[j] - centers[i]
    dist = np.linalg.norm(d, axis=1)
    keep = (owner[i] != owner[j]) \
        & (np.einsum('ij,ij->i', normals[i], normals[j]) < -1. + 1e-6) \
        & (np.abs(np.einsum('ij,ij->i', normals[i], d)) <= tol) \
        & (dist <= radius[i] + radius[j] + tol)
    i, j = i[keep], j[keep]
    # side a = block with the lower index
    swap = owner[i] > owner[j]
    i, j = np.where(swap, j, i), np.where(swap, i, j)

    # identical triangles (matching triangulation): whole face is the contact element
    same_center = (np.linalg.norm(centers[j] - centers[i], axis=1) < tol) & (np.abs(areas[i] - areas[j]) < tol * tol)
    matched = np.zeros(len(i), dtype=bool)
    for k in np.where(same_center)[0]:
        matched[k] = _same_vertices(blocks[owner[i[k]]], face[i[k]], blocks[owner[j[k]]], face[j[k]], tol)

    el = {'a': [], 'fa': [], 'b': [], 'fb': [], 'area': [], 'centroid': [], 'normal': [], 'matched': [],
          'vertices': []}

    def add(ia, fa, ib, fb, area, centroid, n, is_matched, verts):
        el['a'].append(ia); el['fa'].append(fa)
        el['b'].append(ib); el['fb'].append(fb)
        el['area'].append(area); el['centroid'].append(centroid)
        el['normal'].append(n); el['matched'].append(is_matched)
        el['vertices'].append(verts)

    for k in np.where(matched)[0]:
        a, b = i[k], j[k]
        bl = blocks[owner[a]]
        add(owner[a], face[a], owner[b], face[b], areas[a], centers[a], normals[a], True,
            bl.nodes[bl.cells_2D[face[a]]])

    # a face with an identical partner is fully in contact; since the blocks do
    # not overlap, no other face can overlap it with a positive area
    is_matched = np.zeros(len(owner), dtype=bool)
    is_matched[i[matched]] = True
    is_matched[j[matched]] = True
    to_clip = ~matched & ~is_matched[i] & ~is_matched[j]

    # general case: clip the triangles in the plane of face a
    for k in np.where(to_clip)[0]:
        a, b = i[k], j[k]
        n = normals[a]
        bl = blocks[owner[a]]
        pa = bl.nodes[bl.cells_2D[face[a]]]
        o = pa[0]
        e1 = pa[1] - pa[0]
        e1 = e1 / np.linalg.norm(e1)
        e2 = np.cross(n, e1)
        tri_a = _ccw([tuple(((p - o) @ e1, (p - o) @ e2)) for p in pa])
        blb = blocks[owner[b]]
        pb = blb.nodes[blb.cells_2D[face[b]]]
        tri_b = _ccw([tuple(((p - o) @ e1, (p - o) @ e2)) for p in pb])

        poly = _clip(tri_a, tri_b)
        if len(poly) < 3:
            continue
        area, (cx, cy) = _area_centroid(poly)
        if area <= tol * tol:
            continue
        add(owner[a], face[a], owner[b], face[b], area, o + cx * e1 + cy * e2, n, False,
            np.array([o + x * e1 + y * e2 for x, y in poly]))

    vertices = el.pop('vertices')
    out = {k: np.array(v) for k, v in el.items()}
    out['vertices'] = vertices  # list of (k, 3) arrays (polygon of each element)
    for k in ['a', 'fa', 'b', 'fb']:
        out[k] = out[k].astype(int)
    out['matched'] = out['matched'].astype(bool)
    if len(out['area']) == 0:
        out['centroid'] = np.zeros((0, 3))
        out['normal'] = np.zeros((0, 3))
    return out


def contact_coverage(blocks, elements):
    '''
    Fraction of the area of every candidate contact face that is in contact.
    Returns a list (per block) of arrays aligned with face_groups['contact_faces'].
    '''
    cov = []
    for ib, bl in enumerate(blocks):
        cf = np.asarray(bl.face_groups['contact_faces'], dtype=int)
        pos = {f: k for k, f in enumerate(cf)}
        c = np.zeros(len(cf))
        for side, fside in (('a', 'fa'), ('b', 'fb')):
            sel = elements[side] == ib
            for f, a in zip(elements[fside][sel], elements['area'][sel]):
                c[pos[f]] += a
        cov.append(c / bl.face_areas[cf])
    return cov


def coverage_report(blocks, elements, coverage, frame=()):
    '''
    Summary of how well the triangulation fits the contact regions:
    - n_matched_elements: contact elements that are a pair of identical triangles
    - n_faces_partial:    faces that are only partially in contact, i.e. the
                          boundary of the contact region crosses the triangle
                          (the pressure is then averaged over the whole face)
    '''
    frame = set(frame)
    cov_all = np.concatenate([c for ib, c in enumerate(coverage) if ib not in frame]) \
        if len(coverage) > len(frame) else np.zeros(0)
    tot_contact = elements['area'].sum()
    partial = (cov_all > 1e-9) & (cov_all < 1. - 1e-6)
    sliver = elements['area'] < 0.05 * np.median(elements['area']) if len(elements['area']) else np.zeros(0, bool)
    return {
        'n_elements': int(len(elements['area'])),
        'contact_area': float(tot_contact),
        'n_faces_full': int((cov_all >= 1. - 1e-6).sum()),
        'n_faces_partial': int(partial.sum()),
        'n_faces_none': int((cov_all <= 1e-9).sum()),
        'n_matched_elements': int(elements['matched'].sum()) if len(elements['area']) else 0,
        'n_sliver_elements': int(sliver.sum()),
        'contact_boundary_resolved': bool(partial.sum() == 0),
    }


# ---------------------------------------------------------------------------
# Jacobian
# ---------------------------------------------------------------------------

def _columns(block, centroid, normal_out):
    '''generalized force of a unit contact force acting against normal_out'''
    lever = centroid - block.centroid
    lever = lever - (lever @ normal_out) * normal_out
    return np.hstack([-normal_out, np.cross(lever, normal_out)])


def assemble_contact_jacobian(blocks, active, elements, supports, points='centroid'):
    '''
    Contact Jacobian J (6*N_active x N_columns) and load vector f_ext.

    points: 'centroid' one force per contact element at its centroid (statics,
            pressure field), or 'vertices' one column per vertex of the contact
            polygon. For a rigid motion the normal velocity is linear on a
            planar contact region, so with 'vertices' the condition
            J^T dq >= 0 holds on the whole contact region (exact kinematic
            test, independent of the refinement).

    active:   indices of the blocks whose equilibrium is solved (in this order)
    elements: contact elements (find_contact_elements)
    supports: list of (block, face, area, centroid, normal) of support elements
              (only the side of the analysed block enters the equations)

    Returns J, f_ext and the list of columns: ('el', k) or ('sup', k)
    '''
    row = {ib: 6 * k for k, ib in enumerate(active)}
    rows, cols, vals = [], [], []
    columns = []

    def add(ib, c, col):
        if ib in row:
            r0 = row[ib]
            for k in range(6):
                if c[k] != 0.:
                    rows.append(r0 + k); cols.append(col); vals.append(c[k])

    if points not in ('centroid', 'vertices'):
        raise ValueError(f"Unknown points: {points}")

    col = 0
    for k in range(len(elements['area'])):
        ia, ib = elements['a'][k], elements['b'][k]
        if ia not in row and ib not in row:
            continue
        n = elements['normal'][k]
        pts = [elements['centroid'][k]] if points == 'centroid' else elements['vertices'][k]
        for c in pts:
            add(ia, _columns(blocks[ia], c, n), col)
            add(ib, _columns(blocks[ib], c, -n), col)
            columns.append(('el', k))
            col += 1

    for k, (ib, f, area, c, n) in enumerate(supports):
        pts = [c] if points == 'centroid' else blocks[ib].nodes[blocks[ib].cells_2D[f]]
        for p in pts:
            add(ib, _columns(blocks[ib], p, n), col)
            columns.append(('sup', k))
            col += 1

    J = sp.csc_matrix((vals, (rows, cols)), shape=(6 * len(active), col))
    f_ext = np.concatenate([blocks[ib].p_b for ib in active])

    return J, f_ext, columns
