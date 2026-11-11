"""
Geometry module for different block shapes.
Contains functions to generate vertices and faces for various block types.
"""

from typing import Tuple, Optional
import numpy as np
import trimesh
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


def bisquare_param(refinement: int, h: float) -> Tuple[np.ndarray, np.ndarray]:
    """Generate parameterized bisquare block geometry."""
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


def octahedron(refinement: int, height_octahedron: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """Generate octahedron block geometry."""
    edge_length = height_octahedron * BlockConstants.SQRT3 / BlockConstants.SQRT2
    height_triangle = BlockConstants.SQRT3 / 2 * edge_length

    vertices = [
        [0.0, 2*height_triangle/3, 0.0],
        [-edge_length/2, -height_triangle/3, 0.0],
        [edge_length/2, -height_triangle/3, 0.0],
        [edge_length/2, height_triangle/3, height_octahedron],
        [-edge_length/2, height_triangle/3, height_octahedron],
        [0.0, -2*height_triangle/3, height_octahedron],
    ]

    triangles = [
        [0, 2, 1],  # Bottom
        [3, 4, 5],  # Top
        [0, 4, 1],  # Side
        [4, 1, 5],
        [1, 5, 2],
        [5, 2, 3],
        [2, 3, 0],
        [3, 0, 4],
    ]

    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=int(refinement))
    return V_ref, F_ref


def irr_octahedron(refinement: int, height_octahedron: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """Generate irregular octahedron block geometry."""
    edge_length = np.sqrt(4.0 / BlockConstants.SQRT3)
    height_triangle = BlockConstants.SQRT3 / 2 * edge_length

    vertices = [
        [0.0, 2*height_triangle/3, 0.0],
        [-edge_length/2, -height_triangle/3, 0.0],
        [edge_length/2, -height_triangle/3, 0.0],
        [edge_length/2, height_triangle/3, height_octahedron],
        [-edge_length/2, height_triangle/3, height_octahedron],
        [0.0, -2*height_triangle/3, height_octahedron],
    ]
    
    # Normalize by height
    vertices = [[x/height_octahedron for x in v] for v in vertices]
    
    triangles = [
        [0, 2, 1],  # Bottom
        [3, 4, 5],  # Top
        [0, 4, 1],  # Side
        [4, 1, 5],
        [1, 5, 2],
        [5, 2, 3],
        [2, 3, 0],
        [3, 0, 4],
    ]

    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=int(refinement))
    return V_ref, F_ref


# Map of block types to their generator functions
BLOCK_GENERATORS = {
    'versatile': versatile,
    'bisquare': bisquare,
    'brick': brick,
    'brick_inter': brick_inter,
    'octahedron': octahedron,
    'versatile_param': versatile_param,
    'bisquare_param': bisquare_param,
    'irr_octahedron': irr_octahedron,
}


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
    
    if block_type in ['versatile_param', 'bisquare_param', 'octahedron_param', 'irr_octahedron']:
        if h is None:
            raise ValueError(f"Parameter h required for block type: {block_type}")
        return generator(refinement, h)
    else:
        return generator(refinement)