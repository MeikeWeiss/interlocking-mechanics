"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: ?

License: MIT

Reference:
"""

import numpy as np
from scipy.spatial import Delaunay

########################################################################
# Cells
########################################################################

def create_tri3_cells(points):

    # Delaunay triangulation
    tri = Delaunay(points[:,:2])
    triangles = tri.simplices  # shape (N_tri, 3)
    
    # Create cell array: [3, p0, p1, p2, 3, p0, p1, p2, ...]
    cells = np.hstack([[3, *triangle] for triangle in triangles]).astype(np.int64)
    
    return triangles, cells


def create_quad4_cells(points, tol=1e-8):

    """
    Create quad4 cells from grid-aligned 2D or 3D points on a Cartesian grid.
    Assumes consistent spacing and full rectangular grid coverage.
    """
    # Extract x, y coordinates (ignore z)
    xy = points[:, :2]

    # Find unique x and y values to determine grid layout
    x_vals = np.unique(np.round(xy[:, 0], decimals=8))
    y_vals = np.unique(np.round(xy[:, 1], decimals=8))
    nx, ny = len(x_vals), len(y_vals)

    # Create a 2D array of point indices matching the grid structure
    index_grid = -np.ones((ny, nx), dtype=int)
    for idx, (x, y) in enumerate(xy):
        i = np.argmin(np.abs(x_vals - x))
        j = np.argmin(np.abs(y_vals - y))
        index_grid[j, i] = idx  # row-major: j is y, i is x

    # Generate quad4 elements from the index grid
    quads = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            n0 = index_grid[j, i]
            n1 = index_grid[j, i+1]
            n2 = index_grid[j+1, i+1]
            n3 = index_grid[j+1, i]
            if -1 not in [n0, n1, n2, n3]:  # ensure all points are valid
                quads.append([n0, n1, n2, n3])

    cells = np.hstack([[4, *quad] for quad in quads]).astype(np.int64)
                
    return np.array(quads), cells


def create_prism6_cells(n_points, triangles, n_h):

    # Prism cells
    prisms = []


    for i in range(n_h):
        
        for tri in triangles:
            
            a, b, c = tri
                    
            a0, b0, c0 = i*n_points + a, i*n_points + b, i*n_points + c
            a1, b1, c1 = a0 + n_points, b0 + n_points, c0 + n_points
        
            # Order: base triangle, then top triangle
            #prisms.append([6, c0, b0, a0, c1, b1, a1])  # WEDGE_6
            prisms.append([6, a0, b0, c0, a1, b1, c1])  # WEDGE_6

    cells = np.hstack(prisms).astype(np.int64)
    
    return prisms, cells


def create_hex8_cells(n_points, quads, n_h):

    # Prism cells
    hexahedrons = []

    for i in range(n_h):
        for quad in quads:

            a, b, c, d = quad
                    
            a0, b0, c0, d0 = i*n_points + a, i*n_points + b, i*n_points + c, i*n_points + d
            a1, b1, c1, d1 = a0 + n_points, b0 + n_points, c0 + n_points, d0 + n_points
        
            # Order: base triangle, then top triangle
            hexahedrons.append([8, a0, b0, c0, d0, a1, b1, c1, d1])  # HEXAHEDRON
            
    cells = np.hstack(hexahedrons).astype(np.int64)
    
    return hexahedrons, cells
