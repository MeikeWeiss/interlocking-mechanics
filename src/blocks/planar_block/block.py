"""
Block creation and manipulation module.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pyvista as pv
from src.blocks.planar_block.geometry import get_block_geometry, BlockConstants

logger = logging.getLogger(__name__)


class Block:
    """
    Represents a single block in the assembly.
    
    Attributes:
        vertices: Array of vertex coordinates
        faces: Array of face indices
        surface: PyVista PolyData surface
        centroid: Center of mass
        face_centers: Centers of each face
        face_normals: Normals of each face
        unit_forces: Unit force vectors for each face
        unit_momentum: Unit momentum vectors for each face
        A_b: Block matrix A (forces and moments)
        p_b: Block vector p (external forces and moments)
    """
    
    def __init__(self, block_type: str, refinement: int, h: Optional[float] = None):
        """
        Initialize a block.
        
        Args:
            block_type: Type of block to create
            refinement: Number of refinement levels
            h: Optional parameter for parameterized blocks
        """
        self.block_type = block_type
        self.refinement = refinement
        self.h = h
        
        # Generate geometry
        self.vertices, self.faces = get_block_geometry(block_type, refinement, h)
        
        # Compute derived properties
        self._compute_properties()
    
    def _compute_properties(self) -> None:
        """Compute all derived properties of the block."""
        # Create PyVista mesh
        cells = np.hstack([[3, *face] for face in self.faces]).astype(np.int64)
        self.mesh = pv.PolyData(self.vertices, cells)
        self.surface = self.mesh.extract_surface().compute_cell_sizes(
            length=False, volume=False, area=True
        )
        
        # Compute centroid
        self.centroid = self.mesh.center_of_mass()
        
        # Compute face properties
        normals_mesh = self.mesh.compute_normals(cell_normals=True, point_normals=False)
        self.face_normals = normals_mesh.cell_data["Normals"]
        self.face_areas = self.surface["Area"]
        self.face_centers = self.mesh.cell_centers().points
        self.unit_forces = -self.face_normals
        
        # Compute lever vectors
        self.lever_vectors = np.array([
            r - np.dot(r, n) * n
            for r, n in zip(self.face_centers - self.centroid, self.face_normals)
        ])
        
        # Compute unit momentum
        self.unit_momentum = np.cross(self.lever_vectors, -self.unit_forces)
        
        # Compute block matrix A (6x6)
        # Using faces 6 and above (typically side faces)
        A_b = np.hstack([
            self.unit_forces[6:, :],
            self.unit_momentum[6:, :]
        ]).T
        
        # Compute force and moment on top faces (indices 2-5)
        f = 1.0
        F_b = f * np.sum(self.unit_forces[2:6, :], axis=0)
        M_b = f * np.sum(self.unit_momentum[2:6, :], axis=0)
        self.p_b = -np.hstack([F_b, M_b])
        
        # Store only the non-singular part of A (usually 6x6)
        self.A_b = A_b
    
    def get_surface_groups(self) -> Dict[str, List[int]]:
        """
        Group faces by surface type.
        
        Returns:
            Dictionary with 'top_surf' and 'bottom_surf' face indices
        """
        surfaces = {
            'top_surf': [],
            'bottom_surf': [],
        }
        
        for i, face in enumerate(self.faces):
            z_vals = self.vertices[face, 2]
            
            if np.allclose(z_vals, BlockConstants.Z_BOTTOM):
                surfaces['bottom_surf'].append(i)
            elif np.allclose(z_vals, BlockConstants.Z_TOP):
                surfaces['top_surf'].append(i)
        
        return surfaces
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for serialization."""
        return {
            'all_points': self.vertices,
            'cells': {'3D': self.faces},
            'surface': self.surface,
            'face_areas': self.face_areas,
            'centroid': self.centroid,
            'face_centers': self.face_centers,
            'face_normals': self.face_normals,
            'unit_forces': self.unit_forces,
            'lever_vectors': self.lever_vectors,
            'unit_momentum': self.unit_momentum,
            'A_b': self.A_b,
            'p_b': self.p_b,
        }


def create_block(block_type: str, refinement: int, h: Optional[float] = None) -> Dict[str, Any]:
    """
    Factory function to create a block.
    """
    block = Block(block_type, refinement, h)
    block_dict = block.to_dict()
    
    # Füge cells_arr hinzu (wird von assembly.py benötigt)
    cells = np.hstack([[3, *face] for face in block.faces]).astype(np.int64)
    block_dict['cells_arr'] = {'3D': cells}
    
    return block_dict


# ============================================================================
# WICHTIG: Diese Funktion MUSS existieren für den Import in mbd_planar.py
# ============================================================================

def get_blocks(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get blocks from configuration.
    
    This function is required by the simulation framework.
    
    Args:
        config: Dictionary with block configuration (refinement, type, h, edgeLength)
    
    Returns:
        Dictionary with 'block' key containing the block properties
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

def group_faces(block: Dict[str, Any]) -> Dict[str, Any]:
    """
    Group faces of a block by surface type (ceiling boundary conditions).
    
    Args:
        block: Block dictionary from create_block
    
    Returns:
        Block dictionary with added 'surf_filter' key
    """
    faces = block.cells_2D
    verts = block.nodes
    
    surfaces = {
        'top_surf': [],
        'bottom_surf': [],
    }
    
    for i, f in enumerate(faces):
        z_vals = verts[f, 2]
        
        if np.allclose(z_vals, BlockConstants.Z_BOTTOM):
            surfaces['bottom_surf'].append(i)
        elif np.allclose(z_vals, BlockConstants.Z_TOP):
            surfaces['top_surf'].append(i)
    
    block.surf_filter = surfaces
      
    return block

def group_faces_wall(block, x_max, y_max):
    """
    Group faces of a Block object for wall boundary conditions.
    
    Args:
        block: Block object
        y_max_global: Maximum y-coordinate in the entire assembly
    
    Returns:
        Block object with added 'surf_filter' attribute
    """
    faces = block.cells_2D
    verts = block.nodes
    
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

        if np.allclose(z_vals, -1) :
            surfaces['bottom_surf'].append(i)
        elif np.allclose(z_vals, 0):
            surfaces['top_surf'].append(i)
        elif np.allclose(y_vals, y_max):
            surfaces['ext_surf'].append(i)
            block.unit_forces[i] = np.array([0, 1, 0])
        elif np.any(y_vals > y_max-0.5) and block.face_normals[i, 2] != 0:
            surfaces['ext_surf'].append(i)
        elif np.any(y_vals > y_max-0.5) and np.any(x_vals < 2): # TODO anpassen an kurze Reihen
            surfaces['top_left'].append(i)
            block.unit_forces[i] = np.array([-1, 0, 0])
        elif np.any(y_vals > y_max-0.5) and np.any(x_vals >= x_max):
            surfaces['top_right'].append(i)
            block.unit_forces[i] = np.array([1, 0, 0])

    block.surf_filter = surfaces

    return block