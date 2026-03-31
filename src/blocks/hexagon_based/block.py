"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: 2026-03-31

License: MIT

Reference:
Wenzheng Xu, Xiaoshan Lin, and Yi Min Xie. A novel non-planar interlocking element for tubular structures. Tunnelling and Underground Space Technology, 103:103503, 2020. doi: https://doi.org/10.1016/j.tust.2020.103503.
"""

import numpy as np
from src.blocks.hexagon_based.transformations import *
from src.engine.cells import *
from src.engine.plots import *

########################################################################
# Point clouds / grids
########################################################################

def create_point_grid(l, b, n_l, n_b):

    dl = l/n_l
    db = b/n_b

    n_all_points = (2*n_l+1)*(n_b+1)
    points = []
    
    for i in range(-n_l, n_l+1):
        
        for j in range(-n_b, n_b+1):
            
            points.append(np.array([dl*i, db*j, 0.]))
            
    return points


def create_point_grid_frame(l, b, n_l, n_b):

    dl = l/n_l
    db = b/n_b

    n_all_points = (2*n_l+1)*(n_b+1)
    points = []
    
    for i in range(-n_l, n_l+1):
        
        for j in range(n_b+1):
            
            points.append(np.array([dl*i, db*j, 0.]))
            
    return points


def create_layers(points, t2, n_t):

    dt = t2 / n_t

    np_2D = points.shape[0]
    np_3D = np_2D * (2*n_t+1)
    
    points_vol = np.empty((np_3D,3))
    
    for i_id, i in enumerate(range(-n_t, n_t+1)):
        points_vol[np_2D*i_id : np_2D*i_id + np_2D] = points + np.array([0.,0.,dt*i]) 

    return points_vol



########################################################################
# Hexagon-based block
########################################################################

def create_block(
        n, # number of blocks in the layer (ring)
        r0, # inner radius of the tube
        t, # thickness
    
        n_l, # number of segments in l direction
        n_t, # number of segments in t direction

        cylindrical, # True, False: form of the block (round or not)
        frame, # True, False: frame block

        cell_types, # {'2D': 'quad4', '3D': 'hex8'}
        
):
    
    alpha = 2*np.pi/n
    
    l = r0*alpha

    # 2D grid of points
    ri = l/2.
    ro = 2./np.sqrt(3) * ri

    bl_data = {
        'n': n, 'r0': r0, 't': t, 'alpha': alpha, 'ri': ri, 'ro': ro,
        'n_l': n_l, 'n_t': n_t,
        'frame': frame,
    }
    
    # point cloud
    if frame:
        points = create_point_grid_frame(ri, ro/2., n_l, n_l//2)
    else:    
        points = create_point_grid(ri, ro/2., n_l, n_l//2)

    # Create 2D cells
    if cell_types['2D'] == 'tri3':
        triangles, tri3_cells = create_tri3_cells(np.array(points))
        
    elif cell_types['2D'] == 'quad4':
        quads, quad4_cells = create_quad4_cells(np.array(points))
        
    # Plot the 2D mesh
    #plot_quad4_cells(np.array(points), quads, quad4_cells, ids=False)

    # extrude
    points_arr = np.array(points)
    all_points_arr0 = create_layers(points_arr, t/2, n_t)
    all_points = all_points_arr0.tolist()
    
    ######################################################
    # create 3D cells
    ######################################################

    if cell_types['3D'] == 'prism6':
        #prism6, prism6_arr
        cells, cells_arr = create_prism6_cells(len(points), triangles, 2*n_t)
    elif cell_types['3D'] == 'hex8':
        # hex8, hex8_arr
        cells, cells_arr = create_hex8_cells(len(points), quads, 2*n_t)

    ######################################################
    # group faces
    ######################################################
    undeformed_surface = extract_block_surface(all_points_arr0, len(cells), cells_arr)
    bl_data['surf_filter'] = group_faces( ri, t/2, ro, undeformed_surface, frame, tol=1e-9 )

    ######################################################
    # transformations of the grid
    ######################################################

    # create hexagon
    transform_rectangle_to_hexagon(all_points, ro, ri)

    # transform all 6 edges to a circle segment
    transform_hexagon_edges(all_points, ro, ri, t/2)

    #plot_point_cloud(all_points)
    
    # transformations of the grid
    if cylindrical:

        transform_cylinder(all_points, r0, alpha, ri, t)

        
    all_points_arr = np.array(all_points)
    
    ##########################################################
    # update data dictionary
    ##########################################################
    bl_data['all_points'] = all_points_arr
    bl_data['cells'] = {'2D': None, '3D': cells}
    bl_data['cells_arr'] = {'2D': None, '3D': cells_arr}

    return bl_data

########################################################################
# Faces (surface)
########################################################################

def group_faces( l, b, h, surface, frame, tol=1e-6 ):
    '''
    l: length of the block
    b: thickness of the block
    h: height of the block
    surface: the extracted boundary of the volume
    tol = 1e-6  # tolerance for floating point comparison
    '''
    
    ### Collect cells that satisfy the condition ###
    surf_filter = {}

    surf_filter['inner_surf'] = extract_cell_IDs_by_centroid(
        surface, (-l-tol, l+tol, -h-tol, h+tol, -b-tol, -b+tol)
    )
    surf_filter['outer_surf'] = extract_cell_IDs_by_centroid(
        surface, (-l-tol, l+tol, -h-tol, h+tol, +b-tol, +b+tol)
    )
    surf_filter['top_surf'] = extract_cell_IDs_by_centroid(
        surface, (-l-tol, l+tol, h/2-tol, h+tol, -b+tol, +b-tol)
    )
    if frame:
        surf_filter['bottom_surf'] = extract_cell_IDs_by_centroid(
            surface, (-l-tol, l+tol, 0.-tol, 0.+tol, -b+tol, +b-tol)
        )
    else:
        surf_filter['bottom_surf'] = extract_cell_IDs_by_centroid(
            surface, (-l-tol, l+tol, -h-tol, -h/2+tol, -b+tol, +b-tol)
        )
    

    ### function to test the groups (defined below) ###
    #plot_grouped_faces(surface, surf_filter['top_surf'])
    
    return surf_filter


def extract_cell_IDs_by_centroid(mesh, bounds):

    centers = mesh.cell_centers().points
    xmin, xmax, ymin, ymax, zmin, zmax = bounds

    mask = (
        (centers[:,0] >= xmin) & (centers[:,0] <= xmax) &
        (centers[:,1] >= ymin) & (centers[:,1] <= ymax) &
        (centers[:,2] >= zmin) & (centers[:,2] <= zmax)
    )

    cell_ids = np.where(mask)[0]
    #return mesh.extract_cells(np.where(mask)[0])
    
    return cell_ids


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
    surface = mesh.extract_surface(algorithm="dataset_surface")
    
    return surface


def plot_grouped_faces(surface, cell_ids):

    import pyvista as pv
    
    inside_surface = surface.extract_cells(cell_ids)

    plotter = pv.Plotter()
    plotter.add_mesh(surface, color="lightgray", opacity=0.2)
    plotter.add_mesh(inside_surface, color="red", show_edges=True)
    plotter.add_axes()
    plotter.show()

    return

#############################################################################
# construct all block types
#############################################################################

def get_blocks(config):
    
    # create the sinus block
    block = create_block(
        config['n'], config['r0'], config['t'],
        config['n_l'], config['n_t'],
        config['cylindrical'], False, config['cell_types']
    )
    
    # create the bottom frame block
    frame_block_bottom = create_block(
        config['n'], config['r0'], config['t'],
        config['n_l'], config['n_t'],
        config['cylindrical'], True, config['cell_types']
    )
        
    # create the top frame block
    frame_block_top = create_block(
        config['n'], config['r0'], config['t'],
        config['n_l'], config['n_t'],
        config['cylindrical'], True, config['cell_types'],
    )

    blocks = {
        'block': block,
        'frame_block_bottom': frame_block_bottom,
        'frame_block_top': frame_block_top,
    }
    
    return blocks

