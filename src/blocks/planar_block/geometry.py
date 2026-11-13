"""
Geometry module for different block shapes.
Contains functions to generate vertices and faces for various block types.
"""

from typing import Tuple, Optional
import numpy as np
import pyvista as pv
from src.blocks.planar_block.meshing_mbd import refine_triangulation


class BlockConstants:
    """Constants used in block geometry."""
    Z_BOTTOM = 0.0
    Z_TOP = 1.0
    CENTER_XY = 0.0
    SQRT2 = np.sqrt(2)
    SQRT3 = np.sqrt(3)


def versatile(refinement: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate versatile block geometry.
    
    Args:
        refinement: Number of refinement levels for triangulation
    
    Returns:
        Tuple of (vertices, faces) as numpy arrays
    """
    vertices_rot = np.array([
        [0.0, 1.0, 0.0],      # 0
        [1.0, 0.0, 0.0],      # 1
        [0.0, -1.0, 0.0],     # 2
        [-1.0, 0.0, 0.0],     # 3
        [0.0, 1.0, 1.0],      # 4
        [-1.0, 1.0, 1.0],     # 5
        [-1.0, -1.0, 1.0],    # 6
        [0.0, -1.0, 1.0],     # 7
        [0.0, 0.0, 1.0],      # 8
        [-1.0, 0.0, 1.0],     # 9
    ])

    faces = np.array([
        [0, 1, 3],   # [1,2,4]
        [1, 2, 3],   # [2,3,4]
        [6, 7, 8],   # [7,8,9]
        [5, 6, 8],   # [6,7,9]
        [4, 5, 8],   # [5,6,9]
        [0, 1, 8],   # [1,2,9]
        [1, 2, 8],   # [2,3,9]
        [0, 3, 5],   # [1,4,6]
        [2, 3, 6],   # [3,4,7]
        [2, 7, 8],   # [3,8,9]
        [0, 4, 8],   # [1,5,9]
        [0, 4, 5],   # [1,5,6]
        [3, 5, 9],   # [4,6,10]
        [3, 6, 9],   # [4,7,10]
        [2, 6, 7],   # [3,7,8]
    ])
    
    V_ref, F_ref = refine_triangulation(vertices_rot, faces, levels=int(refinement))
    return V_ref, F_ref


def versatile_param(refinement: int, h: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate parameterized versatile block geometry.
    
    Args:
        h: Height parameter controlling the block shape
        refinement: Number of refinement levels for triangulation
    
    Returns:
        Tuple of (vertices, faces) as numpy arrays
    """
    s2 = BlockConstants.SQRT2
    
    vertices = [
        [-1.0, 0.0, 0.0],                      # 0
        [0.0, 1.0, 0.0],                      # 1
        [0.0, -1.0, 0.0],                    # 2
        [1.0, 0.0, 0.0],                      # 3
        [1.0, 0.0, 1.0],                      # 4
        [0.0, 0.0, 1.0],                      # 5
        [0.0, 1.0, 1.0],                      # 6
        [0.0, -1.0, 1.0],                    # 7
        [-1.0, 0.0, 1.0],                    # 8
        [0.5 - h/s2, 0.5 - h/s2, 1.0],      # 9
        [0.5 - h/s2, -0.5 + h/s2, 1.0],     # 10
        [-0.5 - h/s2, 0.5 + h/s2, 1.0],     # 11
        [-0.5 - h/s2, -0.5 - h/s2, 1.0],    # 12
    ]

    triangles = [
        [0, 1, 2],
        [3, 1, 2],
        [4, 9, 10],
        [5, 9, 10],
        [5, 9, 6],
        [5, 10, 7],
        [12, 7, 5],
        [11, 5, 6],
        [12, 8, 5],
        [11, 8, 5],
        [10, 3, 2],
        [9, 3, 1],
        [11, 0, 1],
        [12, 0, 2],
        [10, 3, 4],
        [10, 2, 7],
        [9, 3, 4],
        [9, 1, 6],
        [12, 2, 7],
        [12, 0, 8],
        [11, 1, 6],
        [11, 0, 8],
    ]

    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=int(refinement))
    return V_ref, F_ref


def bisquare(refinement: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate bisquare block geometry."""
    vertices_rot = np.array([
        [-1.0, 0.0, 0.0],   # 0
        [0.0, 1.0, 0.0],    # 1
        [1.0, 0.0, 0.0],    # 2
        [0.0, -1.0, 0.0],   # 3
        [-1.0, 0.0, 1.0],   # 4
        [-1.0, 1.0, 1.0],   # 5
        [0.0, 1.0, 1.0],    # 6
        [1.0, 0.0, 1.0],    # 7
        [1.0, -1.0, 1.0],   # 8
        [0.0, -1.0, 1.0],   # 9
        [0.0, 0.0, 1.0],    # 10
    ])

    faces = np.array([
        [0, 1, 3],
        [1, 2, 3],
        [4, 5, 6],
        [4, 6, 10],
        [7, 8, 9],
        [7, 9, 10],
        [3, 8, 9],
        [2, 7, 8],
        [2, 3, 8],
        [0, 3, 10],
        [0, 4, 10],
        [3, 9, 10],
        [1, 5, 6],
        [0, 4, 5],
        [1, 2, 10],
        [1, 6, 10],
        [2, 7, 10],
        [0, 1, 5],
    ])

    V_ref, F_ref = refine_triangulation(vertices_rot, faces, levels=int(refinement))
    return V_ref, F_ref


def tortuga(refinement: int, h: float) -> Tuple[np.ndarray, np.ndarray]:
    """Generate the tortuga block (parameterized bisquare block)."""
    s2 = BlockConstants.SQRT2
    dh = h / s2

    vertices = [
        [-1.0, 0.0, 0.0],                     # 0
        [0.0, 1.0, 0.0],                     # 1
        [1.0, 0.0, 0.0],                     # 2
        [0.0, -1.0, 0.0],                   # 3
        [-0.5, 0.5, 0.0],                   # 4
        [-0.5, -0.5, 0.0],                 # 5
        [0.5, 0.5, 0.0],                   # 6
        [0.5, -0.5, 0.0],                 # 7
        [-1.0, 0.0, 1.0],                 # 8
        [-0.5 + dh, -0.5 + dh, 1.0],     # 9
        [0.0, -1.0, 1.0],                # 10
        [0.5 + dh, -0.5 - dh, 1.0],     # 11
        [1.0, 0.0, 1.0],                # 12
        [0.5 - dh, 0.5 - dh, 1.0],     # 13
        [0.0, 1.0, 1.0],               # 14
        [-0.5 - dh, 0.5 + dh, 1.0],   # 15
    ]

    triangles = [
        # Bottom
        [0, 1, 3],
        [1, 2, 3],
        # Top
        [8, 15, 14],
        [8, 14, 13],
        [8, 13, 9],
        [12, 11, 10],
        [12, 10, 9],
        [12, 9, 13],
        # Side faces
        [0, 8, 15],
        [0, 1, 15],
        [1, 15, 14],
        [1, 2, 13],
        [1, 14, 13],
        [2, 12, 13],
        [2, 3, 11],
        [2, 12, 11],
        [3, 11, 10],
        [0, 3, 9],
        [0, 8, 9],
        [3, 10, 9],
    ]

    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=int(refinement))
    return V_ref, F_ref

def brick(refinement: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate brick block geometry."""
    vertices = [
        [0.0, 0.0, 0.0],
        [0.0, 0.5, 0.0],
        [1.0, 0.5, 0.0],
        [2.0, 0.5, 0.0],
        [2.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0],
        [0.0, 0.5, -1.0],
        [1.0, 0.5, -1.0],
        [2.0, 0.5, -1.0],
        [2.0, 0.0, -1.0],
        [1.0, 0.0, -1.0],
    ]

    triangles = [
        [0, 1, 5],
        [1, 2, 5],
        [2, 3, 5],
        [3, 4, 5],
        [6, 7, 11],
        [7, 8, 11],
        [8, 9, 11],
        [9, 10, 11],
        [0, 1, 6],
        [1, 6, 7],
        [1, 2, 7],
        [2, 7, 8],
        [2, 3, 8],
        [3, 8, 9],
        [3, 4, 10],
        [3, 9, 10],
        [4, 10, 11],
        [4, 5, 11],
        [5, 11, 6],
        [5, 0, 6]
    ]
    
    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=int(refinement))
    return V_ref, F_ref


def brick_inter(refinement: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate brick block geometry."""
    vertices = [
        [0.0, 0.0, 0.0],
        [0.0, 0.5, 0.0],
        [1.0, 0.5, 0.0],
        [2.0, 0.5, 0.0],
        [2.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0],
        [1.0, 0.5, -1.0],
        [2.0, 0.5, -1.0],
        [2.0, 0.0, -1.0],
        [1.0, -0.5, -1.0],
        [1.0, 0.0, -1.0],
    ]

    triangles = [
        [0, 1, 2],
        [0, 2, 5],
        [2, 4, 5],
        [2, 3, 4],
        [9, 10, 11],
        [6, 7, 11],
        [7, 8, 11],
        [8, 9, 11],
        [5, 10, 9],
        [5, 10, 11],
        [5, 4, 9],
        [3, 4, 9],
        [3, 8, 9],
        [3, 8, 7],
        [2, 3, 7],
        [1, 2, 7],
        [1, 6, 7],
        [0, 1, 6],
        [0, 5, 6],
        [5, 6, 11]
    ]
    
    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=int(refinement))
    return V_ref, F_ref


########################################################################
# Cut octahedron (middle part of a regular octahedron)
########################################################################

# volume of all octahedra (= volume of the versatile block in the normalised
# units, height 1, area 2; corresponds to target_volume=0.016 in the original script)
OCTAHEDRON_VOLUME = 2.0
# order of the side edges (bottom vertex, top vertex), cyclic, as the side faces
_OCTA_EDGES = [(0, 4), (1, 4), (1, 5), (2, 5), (2, 3), (0, 3)]


def octahedron_vertices(H: float) -> np.ndarray:
    """Regular octahedron with height H (distance of the bottom and top face), bottom face at z = 0."""
    e = H * BlockConstants.SQRT3 / BlockConstants.SQRT2
    ht = BlockConstants.SQRT3 / 2 * e
    return np.array([
        [0.0, 2 * ht / 3, 0.0],
        [-e / 2, -ht / 3, 0.0],
        [e / 2, -ht / 3, 0.0],
        [e / 2, ht / 3, H],
        [-e / 2, ht / 3, H],
        [0.0, -2 * ht / 3, H],
    ])


def octahedron_height(volume: float = OCTAHEDRON_VOLUME) -> float:
    """height H of the full regular octahedron with the given volume (V = sqrt(3)/2 H^3)"""
    return float((2. * volume / BlockConstants.SQRT3) ** (1. / 3.))


def octahedron_edge_length(volume: float = OCTAHEDRON_VOLUME) -> float:
    """edge length of the full octahedron, determines the lattice of the assembly"""
    return octahedron_height(volume) * BlockConstants.SQRT3 / BlockConstants.SQRT2


def _closed_volume(V: np.ndarray, F: np.ndarray) -> float:
    """volume of a closed triangulated surface with outward oriented faces"""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    return float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6.)


def octahedron(refinement: int, h: float = 1.0, volume: float = OCTAHEDRON_VOLUME) -> Tuple[np.ndarray, np.ndarray]:
    """
    Cut octahedron: middle part of a regular octahedron (same construction as
    cut_octahedra_volume of the original script).

    1. Regular octahedron (bottom and top face parallel) with the volume
       `volume` (height H).
    2. Middle part between z1 = (1 - h)/2 H and z2 = H - z1: hexagonal bottom
       and top face, 6 planar trapezoids as side faces (parts of the side
       faces of the octahedron). h = 1: full octahedron (bottom and top are
       triangles, the hexagon degenerates).
    3. Moved to z = 0 and scaled in z only, so that the volume is again
       `volume` (compensates the cut volume). The x-y geometry, and therefore
       the lattice of the assembly, does not depend on h.

    Faces as in the original script: bottom and top as fans around their
    centroid, every side quad as 4 triangles around its centroid.

    Args:
        h: kept fraction of the height of the octahedron, 0 < h <= 1
           (fracs of the CIRP paper: 1.0, 0.9, ..., 0.2)
    """
    if not 0. < h <= 1.:
        raise ValueError("octahedron: h (kept fraction of the height) must lie in (0, 1]")
    H = octahedron_height(volume)
    verts = octahedron_vertices(H)

    z1 = (1. - h) / 2. * H
    z2 = H - z1

    def point_on_edge(ib, it, z):
        return verts[ib] + z / H * (verts[it] - verts[ib])

    L = np.array([point_on_edge(a, b, z1) for a, b in _OCTA_EDGES])   # lower hexagon
    U = np.array([point_on_edge(a, b, z2) for a, b in _OCTA_EDGES])   # upper hexagon
    side_centroids = np.array([(L[i] + L[(i + 1) % 6] + U[(i + 1) % 6] + U[i]) / 4. for i in range(6)])
    V = np.vstack([L, U, L.mean(axis=0), U.mean(axis=0), side_centroids])
    # indices: L 0..5, U 6..11, centre bottom 12, centre top 13, side centroids 14..19

    F = []
    for i in range(6):
        j = (i + 1) % 6
        F.append([12, i, j])
        F.append([13, 6 + j, 6 + i])
        sc = 14 + i
        F += [[sc, i, j], [sc, j, 6 + j], [sc, 6 + j, 6 + i], [sc, 6 + i, i]]
    F = np.array(F)

    # h = 1: the lower hexagon degenerates to the bottom triangle (and the upper
    # one to the top triangle) -> merge coinciding points (as trimesh with
    # process=True) and drop zero-area triangles
    key = np.round(V / (1e-9 * H)).astype(np.int64)
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    V, F = V[first], inverse.reshape(-1)[F]
    area =np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)
    F = F[area > 1e-12 * H ** 2]

    # outward orientation (convex body)
    G = V.mean(axis=0)
    for k, (a, b, c) in enumerate(F):
        n = np.cross(V[b] - V[a], V[c] - V[a])
        if np.dot((V[a] + V[b] + V[c]) / 3. - G, n) < 0.:
            F[k] = [a, c, b]

    # bottom to z = 0, scale in z to the target volume
    V[:, 2] -= z1
    V[:, 2] *= volume / _closed_volume(V, F)

    V_ref, F_ref = refine_triangulation(V, F, levels=int(refinement))
    return V_ref, F_ref


########################################################################
# Starfish block (Schnelle et al. 2026, Procedia CIRP 142, 446-450)
########################################################################

# edge length of the triangle: area 2 at height 1, i.e. 800 mm^2 at a height of
# 20 mm as in the paper (same height and volume as the versatile block)
STARFISH_EDGE = float(np.sqrt(8. / np.sqrt(3.)))   # = 42.9829 mm / 20 mm
# largest d without self-intersection: sqrt(3) a / 4 (= 18.6 mm / 20 mm)
STARFISH_D_MAX = float(np.sqrt(3.) * STARFISH_EDGE / 4.)


def starfish_outline(d: float, a: float = STARFISH_EDGE) -> Tuple[np.ndarray, np.ndarray]:
    '''
    Bottom and top outline (9 points each, counterclockwise) of the starfish block.

    Bottom: equilateral triangle 1-2-3 (fundamental domain of p6, vertex 1 at
    the origin = 6-fold rotation centre, vertices 2 and 3 = 3-fold centres) with
    the points at 1/4 and 3/4 of every edge. Top: the same points, the point at
    1/4 of every edge (counterclockwise) moved by d to the inside, the point at
    3/4 by d to the outside (Fig. 1 of the paper). Every deformed edge is point
    symmetric about its midpoint, so the deformed triangle is again a
    fundamental domain of p6.
    '''
    corners = np.array([[0., 0.], [a, 0.], [a / 2., a * np.sqrt(3.) / 2.]])
    bottom, top = [], []
    for i in range(3):
        p, q = corners[i], corners[(i + 1) % 3]
        t = (q - p) / a
        n_in = np.array([-t[1], t[0]])   # interior lies to the left
        for s, sign in ((0., 0.), (0.25, 1.), (0.75, -1.)):
            x = p + s * (q - p)
            bottom.append(x)
            top.append(x + sign * d * n_in)
    return np.array(bottom), np.array(top)


def _ear_clip(poly: np.ndarray) -> list:
    '''triangulation of a simple counterclockwise polygon (ear clipping)'''
    idx = list(range(len(poly)))
    tris = []
    scale = np.ptp(poly, axis=0).max() ** 2

    def cross(o, u, v):
        return (u[0] - o[0]) * (v[1] - o[1]) - (u[1] - o[1]) * (v[0] - o[0])

    while len(idx) > 3:
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if cross(a, b, c) <= 1e-12 * scale:      # reflex or degenerate corner
                continue
            if any(cross(a, b, poly[j]) >= 0 and cross(b, c, poly[j]) >= 0 and cross(c, a, poly[j]) >= 0
                   for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append([i0, i1, i2])
            idx.pop(k)
            break
        else:
            raise ValueError("Polygon could not be triangulated (self-intersecting?)")
    tris.append(idx)
    return tris


def starfish(refinement: int, h: float) -> Tuple[np.ndarray, np.ndarray]:
    '''
    Starfish block (wallpaper group p6), height 1, z in [0, 1].

    The bottom (z = 0) is the equilateral triangle, the top (z = 1) the
    deformed triangle, i.e. the load of the 'ceiling' BVP acts on the deformed
    side as in the paper. The side surfaces interpolate linearly between
    corresponding points of bottom and top; the (non-planar) quadrilaterals
    are split into 4 triangles at their centre, so that the triangulation is
    invariant under the symmetries of p6 and neighbouring blocks have
    identical contact surfaces.

    Args:
        h: design parameter d in units of the block height
           (d [mm] = 20 h for the blocks of the paper, 0 <= h < 0.9306)
    '''
    if not 0. <= h < STARFISH_D_MAX:
        raise ValueError(f"starfish: h must lie in [0, {STARFISH_D_MAX:.4f}) "
                         "(larger values give self-intersecting blocks)")
    bottom, top = starfish_outline(h)
    n = len(bottom)

    vertices = [[*p, 0.] for p in bottom] + [[*p, 1.] for p in top]
    faces = []

    # bottom: fan from the centroid of the triangle (convex), normal -z
    g = len(vertices)
    vertices.append([*bottom.mean(axis=0), 0.])
    for i in range(n):
        faces.append([g, (i + 1) % n, i])

    # top: ear clipping (the deformed triangle is not convex), normal +z
    for tri in _ear_clip(top):
        faces.append([n + j for j in tri])

    # sides: quadrilateral B_i, B_i+1, T_i+1, T_i (outward orientation)
    for i in range(n):
        j = (i + 1) % n
        quad = [i, j, n + j, n + i]
        P = np.array([vertices[k] for k in quad])
        normal = np.cross(P[1] - P[0], P[3] - P[0])
        if abs(np.dot(P[2] - P[0], normal)) < 1e-12 * np.linalg.norm(normal):
            faces += [[quad[0], quad[1], quad[2]], [quad[0], quad[2], quad[3]]]
        else:
            c = len(vertices)
            vertices.append(P.mean(axis=0).tolist())
            for k in range(4):
                faces.append([c, quad[k], quad[(k + 1) % 4]])

    V_ref, F_ref = refine_triangulation(np.array(vertices), np.array(faces), levels=int(refinement))
    return V_ref, F_ref


# Map of block types to their generator functions
BLOCK_GENERATORS = {
    'versatile': versatile,
    'bisquare': bisquare,
    'brick': brick,
    'brick_inter': brick_inter,
    'octahedron': octahedron,
    'versatile_param': versatile_param,
    'tortuga': tortuga,
    'starfish': starfish,
}


# block types that require the parameter h
PARAMETRIZED_BLOCKS = ('versatile_param', 'tortuga', 'octahedron', 'starfish')


def get_block_geometry(block_type: str, refinement: int, h: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Factory function to get block geometry by type.
    
    Args:
        block_type: Type of block to generate
        refinement: Number of refinement levels
        h: Optional parameter for parameterized blocks
    
    Returns:
        Tuple of (vertices, faces) as numpy arrays
    
    Raises:
        ValueError: If block_type is unknown
    """
    if block_type not in BLOCK_GENERATORS:
        raise ValueError(f"Unknown block type: {block_type}. Available: {list(BLOCK_GENERATORS.keys())}")
    
    generator = BLOCK_GENERATORS[block_type]
    
    if block_type == 'octahedron' and h is None:
        h = 1.0   # default: full octahedron (not cut)
    if block_type in PARAMETRIZED_BLOCKS:
        if h is None:
            raise ValueError(f"Parameter h required for block type: {block_type}")
        return generator(refinement, h)
    else:
        return generator(refinement)