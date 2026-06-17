"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-15
Last Modified: ?

License: MIT

Reference:
"""

import numpy as np
import pyvista as pv

def get_block_matrices(block, q):

    '''
    f_ext: type str, name of the face group to load
    '''

    contact_faces = block['face_groups']['contact_faces']
    f_ext_faces = block['face_groups']['f_ext_faces']
    
    # block array
    A_b = np.hstack([
        block['unit_forces'][contact_faces,:],
        block['unit_momentum'][contact_faces,:]
    ]).T

    # right side: sum the normals of the top plane and multiply with a scalar f
    if f_ext_faces.size == 0:
        p_b = np.zeros((6))
    else:
        A = block['face_areas'][f_ext_faces]
        f = q * A # compute force from load pressure q
        F_b = np.sum(f[:, np.newaxis] * block['unit_forces'][f_ext_faces,:], axis=0)
        M_b = np.sum(f[:, np.newaxis] * block['unit_momentum'][f_ext_faces,:], axis=0)
        p_b = np.hstack([F_b, M_b])

    block['A_b'] = A_b
    block['p_b'] = p_b
    
    return block


def get_mbd_data(block):

    surface = extract_block_surface(
        block['all_points'],
        len(block['cells']['3D']),
        block['cells_arr']['3D']
    )

    # This adds face areas as an array
    surface = surface.compute_cell_sizes(length=False, volume=False, area=True)
    
    centroid = surface.center_of_mass()

    # Compute per-face (cell) normals
    normals_surface = surface.compute_normals(cell_normals=True, point_normals=False)
    face_normals = normals_surface.cell_data["Normals"]
    unit_forces = -face_normals

    # Compute face centers
    face_centers = surface.cell_centers().points

    # lever vectors projected perpendicular to normal
    lever_vectors = []
    for p, n in zip(face_centers, face_normals):
        r = p - centroid
        r_perp = r - np.dot(r, n) * n   # remove component along normal
        lever_vectors.append(r_perp)

    lever_vectors = np.array(lever_vectors)

    # cross product r x n: (n,3) x (n,3)
    unit_momentum = np.cross(lever_vectors, unit_forces)

    block['surface'] = surface
    block['centroid'] = centroid,
    block['face_normals'] = face_normals
    block['face_centers'] = face_centers
    block['unit_forces'] = unit_forces
    block['lever_vectors'] = lever_vectors
    block['unit_momentum'] = unit_momentum
    block['face_areas'] = surface["Area"] # Access face areas
    
    return block


def extract_block_surface( all_points, n_cells, cells_arr ):

    if cells_arr[0] == 4:
        cell_types = np.full(n_cells, pv.CellType.TETRA)

    elif cells_arr[0] == 6:
        cell_types = np.full(n_cells, pv.CellType.WEDGE)
        
    elif cells_arr[0] == 8:
        cell_types = np.full(n_cells, pv.CellType.HEXAHEDRON)

    # Build mesh
    mesh = pv.UnstructuredGrid(cells_arr, cell_types, all_points)

    # Extract the outer surface
    surface = mesh.extract_surface()
    
    return surface
