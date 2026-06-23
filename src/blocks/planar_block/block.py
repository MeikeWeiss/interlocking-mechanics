import numpy as np
from scipy.spatial import Delaunay
import pyvista as pv
import matplotlib.pyplot as plt

from src.engine.plots import *
from src.blocks.planar_block.meshing_mbd import *

########################################################################
# Vertices and cells
########################################################################

# Square centerd around (0,0) with edge length Sqrt(2) and rotated by 45 degrees
# bottom plane at z=0, top plane at z=1

def versatile(refinement):

    vertices_rot = np.array([
    [0.0,        1.0, 0.0],     # 1
    [1.0,        0.0, 0.0],     # 2
    [0.0,       -1.0, 0.0],     # 3
    [-1.0,       0.0, 0.0],     # 4

    [0.0,        1.0, 1.0],     # 5
    [-1.0,       1.0, 1.0],     # 6
    [-1.0,      -1.0, 1.0],     # 7
    [0.0,       -1.0, 1.0],     # 8
    [0.0,        0.0, 1.0],     # 9
    [-1.0,       0.0, 1.0],     # 10
    ])

    # Triangulierung
    faces = np.array([
        [0, 1, 3],  # [1,2,4]
        [1, 2, 3],  # [2,3,4]
        [6, 7, 8],  # [7,8,9]
        [5, 6, 8],  # [6,7,9]
        [4, 5, 8],  # [5,6,9]
        [0, 1, 8],  # [1,2,9]
        [1, 2, 8],  # [2,3,9]
        [0, 3, 5],  # [1,4,6]
        [2, 3, 6],  # [3,4,7]
        [2, 7, 8],  # [3,8,9]
        [0, 4, 8],  # [1,5,9]
        [0, 4, 5],  # [1,5,6]
        [3, 5, 9],  # [4,6,7]
        [3, 6, 9],
        [2, 6, 7],  # [3,7,8]
    ])

    
    V_ref, F_ref = refine_triangulation(vertices_rot, faces, levels=refinement)
    # plot_mesh_interactive(V_ref, F_ref)

    return V_ref, F_ref

def versatile_param(h,refinement):
    s2 = np.sqrt(2)

    vertices = [
        [-1.0,  0.0, 0.0],      # 0
        [ 0.0,  1.0, 0.0],      # 1
        [ 0.0, -1.0, 0.0],      # 2
        [ 1.0,  0.0, 0.0],      # 3

        [ 1.0,  0.0, 1.0],      # 4   
        [ 0.0,  0.0, 1.0],      # 5   
        [ 0.0,  1.0, 1.0],      # 6   
        [ 0.0, -1.0, 1.0],      # 7   
        [-1.0,  0.0, 1.0],      # 8   

        [0.5 - h/s2,  0.5 - h/s2, 1.0],   # 9   
        [0.5 - h/s2, -0.5 + h/s2, 1.0],   # 10
        [-0.5 - h/s2,  0.5 + h/s2, 1.0],  # 11  
        [-0.5 - h/s2, -0.5 - h/s2, 1.0],  # 12
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

    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=refinement)

    return V_ref, F_ref


def bisquare(refinement):

    vertices_rot = np.array([
    [-1.0,  0.0, 0.0],   # 1
    [ 0.0,  1.0, 0.0],   # 2
    [ 1.0,  0.0, 0.0],   # 3
    [ 0.0, -1.0, 0.0],   # 4

    [-1.0,  0.0, 1.0],   # 5
    [-1.0,  1.0, 1.0],   # 6
    [ 0.0,  1.0, 1.0],   # 7
    [ 1.0,  0.0, 1.0],   # 8
    [ 1.0, -1.0, 1.0],   # 9
    [ 0.0, -1.0, 1.0],   # 10
    [ 0.0,  0.0, 1.0],   # 11
    ])

    faces = np.array([
        [0, 1, 3],
        [1, 2, 3],
        [4, 5, 6],
        [4, 6,10],
        [7, 8, 9],
        [7, 9,10],
        [3, 8, 9],
        [2, 7, 8],
        [2, 3, 8],
        [0, 3,10],
        [0, 4,10],
        [3, 9,10],
        [1, 5, 6],
        [0, 4, 5],
        [1, 2,10],
        [1, 6,10],
        [2, 7,10],
        [0, 1, 5],
    ])

    V_ref, F_ref = refine_triangulation(vertices_rot, faces, levels=refinement)
    #plot_mesh_interactive(V_ref, F_ref)

    return V_ref, F_ref

def bisquare_param(h,refinement):
    s2 = np.sqrt(2)
    dh = h / s2

    vertices = [
        [-1.0,  0.0, 0.0],   # 0  v1
        [ 0.0,  1.0, 0.0],   # 1  v2
        [ 1.0,  0.0, 0.0],   # 2  v3
        [ 0.0, -1.0, 0.0],   # 3  v4

        [-0.5,  0.5, 0.0],   # 4  w1
        [-0.5, -0.5, 0.0],   # 5  w2
        [ 0.5,  0.5, 0.0],   # 6  w3
        [ 0.5, -0.5, 0.0],   # 7  w4

        [-1.0,  0.0, 1.0],   # 8  v5
        [-0.5 + dh, -0.5 + dh, 1.0],   # 9  vi1
        [ 0.0, -1.0, 1.0],   # 10 v6
        [ 0.5 + dh, -0.5 - dh, 1.0],   # 11 vo1
        [ 1.0,  0.0, 1.0],   # 12 v7
        [ 0.5 - dh,  0.5 - dh, 1.0],   # 13 vi2
        [ 0.0,  1.0, 1.0],   # 14 v8
        [-0.5 - dh,  0.5 + dh, 1.0],   # 15 vo2
    ]

    triangles = [
        # Unterseite
        [0, 1, 3],
        [1, 2, 3],

        # Oberseite
        [8, 15, 14],
        [8, 14, 13],
        [8, 13, 9],

        [12, 11, 10],
        [12, 10, 9],
        [12, 9, 13],

        # Seitenflächen
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

    V_ref, F_ref = refine_triangulation(vertices, triangles, levels=refinement)
    return V_ref, F_ref


########################################################################
# Block
########################################################################

def create_block(block_type, refinement, h=None):

    if block_type == 'versatile':
        # vertices of a versatile block
        points, triangles = versatile(refinement)
    elif block_type == 'bisquare':
        # vertices of a bisquare block
        points, triangles = bisquare(refinement)
    elif block_type == 'versatile_param':
        points, triangles = versatile_param(h, refinement)
    elif block_type == 'bisquare_param':
        points, triangles = bisquare_param(h, refinement)
    else:
        raise ValueError("Unsupported block type")

    all_points_arr = np.array(points)
    cells = np.hstack([[3, *triangle] for triangle in triangles]).astype(np.int64) 
    

    # Compute center of volume
    mesh = pv.PolyData(points, cells)
    centroid = mesh.center_of_mass()

    # Compute per-face (cell) normals
    normals_mesh = mesh.compute_normals(cell_normals=True, point_normals=False)
    face_normals = normals_mesh.cell_data["Normals"]
    unit_forces = -face_normals

    # Compute face centers
    face_centers = mesh.cell_centers().points

    # lever vectors projected perpendicular to normal
    lever_vectors = []
    for p, n in zip(face_centers, face_normals):
        r = p - centroid
        r_perp = r - np.dot(r, n) * n   # remove component along normal
        lever_vectors.append(r_perp)

    lever_vectors = np.array(lever_vectors)

    # cross product r x n: (n,3) x (n,3)
    unit_momentum = np.cross(lever_vectors, -unit_forces)

    # block array
    A_b = np.hstack([unit_forces[6:,:], unit_momentum[6:,:]]).T

    # right side: sum the normals of the top plane and multiply with a scalar f
    f = 1.
    F_b = f * np.sum(unit_forces[2:6,:], axis=0)
    M_b = f * np.sum(unit_momentum[2:6,:], axis=0)
    p_b = - np.hstack([F_b, M_b])

    surface = mesh.extract_surface().compute_cell_sizes(length=False, volume=False, area=True)

    output = {
        'all_points': all_points_arr,        
        'cells': {'3D': triangles}, 'cells_arr': {'3D': cells},
        'surface': surface,
        'face_areas': surface["Area"],
        'centroid': centroid,
        'face_centers': face_centers,
        'face_normals': face_normals, 'face_centers': face_centers,
        'unit_forces': unit_forces, 'lever_vectors': lever_vectors,
        'unit_momentum': unit_momentum,
        'A_b': A_b, 'p_b': p_b,
    }

    return output


########################################################################
# Faces (surface)
########################################################################

def group_faces(block):

    faces = block['cells']['3D']      # Dreiecke (Indices)
    verts = block['all_points']         # Koordinaten (n,3)

    surf_filter = {
        'top_surf': [], # faces on inner radius
        'bottom_surf': [], # faces on outer radius
    }

    for i, f in enumerate(faces):
        z_vals = verts[f, 2]          # z-Koordinaten der 3 Vertices

        if np.allclose(z_vals, 0.0):
            surf_filter['bottom_surf'].append(i)

        elif np.allclose(z_vals, 1.0):
            surf_filter['top_surf'].append(i)

    block['surf_filter'] = surf_filter
    return block


############################################################################

def get_blocks(config):

    block = create_block(config['type'],config['refinement'], config['h'])

    blocks = {
        'block': block
    }
    
    return blocks

def get_blocks_abq(config):
    
    block = create_block(config['type'],config['refinement'], config['h'])

    blocks = {
        'block': block,
        'frame_block_bottom': block,
        'frame_block_top': block,
    }
    
    return blocks