"""
Block creation and face grouping for planar assemblies.
"""

import logging
from typing import Dict, Any, Optional, List
import numpy as np
import pyvista as pv
from src.blocks.planar_block.geometry import get_block_geometry

logger = logging.getLogger(__name__)

# tolerance for classifying faces by their coordinates
TOL = 1e-9


class Block:
    """
    Reference block (surface triangulation) of a planar assembly.

    Attributes:
        vertices: Array of vertex coordinates
        faces: Array of face indices (triangles)
        mesh: PyVista PolyData of the surface
        centroid: Reference point for the moments
        face_centers: Centers of each face
        face_normals: Outward unit normals of each face
        face_areas: Area of each face
        unit_forces: Unit contact force of each face (= -outward normal)
        unit_momentum: Unit moment of each face w.r.t. the centroid
    """

    def __init__(self, block_type: str, refinement: int, h: Optional[float] = None):
        self.block_type = block_type
        self.refinement = refinement
        self.h = h

        # Generate geometry
        self.vertices, self.faces = get_block_geometry(block_type, refinement, h)

        # Compute derived properties
        self._compute_properties()

    def _compute_properties(self) -> None:
        """Compute all derived properties of the block."""
        cells = np.hstack([[3, *face] for face in self.faces]).astype(np.int64)
        self.mesh = pv.PolyData(self.vertices, cells)

        # all quantities refer to the faces of self.mesh in the order of self.faces
        self.face_areas = np.asarray(
            self.mesh.compute_cell_sizes(length=False, area=True, volume=False)["Area"]
        )
        self.face_centers = np.asarray(self.mesh.cell_centers().points)

        # consistently oriented normals (the face order is kept) ...
        normals_mesh = self.mesh.compute_normals(
            cell_normals=True, point_normals=False, consistent_normals=True,
            auto_orient_normals=False, split_vertices=False,
        )
        face_normals = np.asarray(normals_mesh.cell_data["Normals"], dtype=float)

        # ... that point outwards: for a closed surface the flux
        # sum((c - x0) . n * A) equals 3 * volume > 0
        x0 = self.vertices.mean(axis=0)
        flux = np.sum(np.einsum('ij,ij->i', self.face_centers - x0, face_normals) * self.face_areas)
        if flux < 0.:
            face_normals = -face_normals
        self.face_normals = face_normals

        # Reference point for the moments
        self.centroid = self.mesh.center_of_mass()

        # contact force acts against the outward normal
        self.unit_forces = -self.face_normals

        # Lever vectors (component perpendicular to the normal)
        self.lever_vectors = np.array([
            r - np.dot(r, n) * n
            for r, n in zip(self.face_centers - self.centroid, self.face_normals)
        ])

        # Unit moment (sign convention of the original implementation:
        # moment rows of A_b and p_b use the same sign, so equilibrium is unaffected)
        self.unit_momentum = np.cross(self.lever_vectors, -self.unit_forces)

    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary used by the assembly."""
        cells = np.hstack([[3, *face] for face in self.faces]).astype(np.int64)
        return {
            'block_type': self.block_type,
            'all_points': self.vertices,
            'cells': {'3D': self.faces},
            'cells_arr': {'3D': cells},
            'surface': self.mesh,
            'face_areas': self.face_areas,
            'centroid': self.centroid,
            'face_centers': self.face_centers,
            'face_normals': self.face_normals,
            'unit_forces': self.unit_forces,
            'lever_vectors': self.lever_vectors,
            'unit_momentum': self.unit_momentum,
        }


def create_block(block_type: str, refinement: int, h: Optional[float] = None) -> Dict[str, Any]:
    """Factory function to create a reference block (dict)."""
    return Block(block_type, refinement, h).to_dict()


def get_blocks(config: Dict[str, Any], assembly_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the reference blocks from the configuration.

    Args:
        config: block configuration (refinement, type, h)
        assembly_config: unused, same signature as for the other block types

    Returns:
        Dictionary with key 'block'
    """
    block = create_block(
        block_type=config['type'],
        refinement=config['refinement'],
        h=config.get('h')
    )
    return {'block': block}


# ============================================================================
# Group faces functions
# ============================================================================

def _on_plane(vals, value):
    return np.allclose(vals, value, atol=TOL)


def group_faces(block):
    """
    Group the faces of a placed block for the 'ceiling' boundary conditions:
    bottom and top plane of the block (lowest and highest z).

    Args:
        block: Block object of the assembly

    Returns:
        Block object with 'surf_filter' attribute
    """
    faces = block.cells_2D
    verts = block.nodes
    z_bottom = verts[:, 2].min()
    z_top = verts[:, 2].max()

    surfaces = {
        'top_surf': [],
        'bottom_surf': [],
    }

    for i, f in enumerate(faces):
        z_vals = verts[f, 2]

        if _on_plane(z_vals, z_bottom):
            surfaces['bottom_surf'].append(i)
        elif _on_plane(z_vals, z_top):
            surfaces['top_surf'].append(i)

    block.surf_filter = surfaces

    return block


def group_faces_wall(block, extent):
    """
    Group the faces of a placed block for wall boundary conditions.

    The wall lies in the x-y plane (x: along the wall, y: height); the
    z-direction is the thickness of the wall.

    Surfaces:
        bottom_surf / top_surf: back and front of the wall (lowest/highest z)
        ext_surf:  faces of the top row that are loaded from above
        top_left:  left end face of the top row
        top_right: right end face of the top row

    Args:
        block: Block object of the assembly
        extent: dict with 'x_min', 'x_max', 'y_max' of the whole assembly

    Returns:
        Block object with 'surf_filter' attribute
    """
    faces = block.cells_2D
    verts = block.nodes
    z_bottom = verts[:, 2].min()
    z_top = verts[:, 2].max()

    x_min, x_max, y_max = extent['x_min'], extent['x_max'], extent['y_max']
    row_height = extent.get('row_height', 0.5)

    surfaces = {
        'top_surf': [],
        'bottom_surf': [],
        'side_surf': [],
        'ext_surf': [],
        'top_left': [],
        'top_right': []}

    for i, f in enumerate(faces):
        x_vals = verts[f, 0]
        y_vals = verts[f, 1]
        z_vals = verts[f, 2]

        in_top_row = np.any(y_vals > y_max - row_height + TOL)

        if _on_plane(z_vals, z_bottom):
            surfaces['bottom_surf'].append(i)
        elif _on_plane(z_vals, z_top):
            surfaces['top_surf'].append(i)
        elif _on_plane(y_vals, y_max):
            surfaces['ext_surf'].append(i)
        elif in_top_row and abs(block.face_normals[i, 2]) > TOL:
            # inclined top faces (e.g. brick_inter)
            surfaces['ext_surf'].append(i)
        elif in_top_row and np.any(x_vals < x_min + 1.):  # TODO adapt to short rows
            surfaces['top_left'].append(i)
        elif in_top_row and np.any(x_vals >= x_max - TOL):
            surfaces['top_right'].append(i)

    block.surf_filter = surfaces

    return block
