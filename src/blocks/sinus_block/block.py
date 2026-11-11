"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: ?

Contributors:
- Reymond Akpanya, The School of Mathematics and Statistics, The University of Sydney
- Meike Weiß, RWTH Aachen University, Chair of Algebra and Representation Theory

License: MIT

Reference:
"""


import numpy as np
from src.blocks.sinus_block.transformations import *
from src.engine.cells import *
from src.engine.plots import *

########################################################################
# Point clouds / grids
########################################################################

def create_point_grid(l, t, n_l, n_t):

    dl = l/n_l
    dt = t/n_t

    n_all_points = (2*n_l+1)*(n_t+1)
    points = []
    
    for i in range(-n_l, n_l+1):
        #for j in range(-n_t, n_t+1):
        for j in range(n_t+1):
            
            points.append(np.array([dl*i, dt*j, 0.]))


    return points


def create_layers(points, h, n_h):

    dh = h / n_h

    np_2D = points.shape[0]
    np_3D = np_2D * (n_h+1)
    
    points_vol = np.empty((np_3D,3))
    
    for i in range(n_h+1):
        points_vol[np_2D*i : np_2D*i + np_2D] = points + np.array([0.,0.,dh*i]) 

    return points_vol


def create_grid_cylindrical_segment( n_l, n_t ):

    l = 1.
    t = 1.
    dl = l/n_l
    dt = t/n_t

    n_all_points = (2*n_l+1)*(n_t+1)
    points = []
    
    for i in range(-n_l, n_l+1):
        
        for j in range(n_t+1):
            
            points.append(np.array([dl*i, dt*j, 0.]))

    return points


########################################################################
# Block
########################################################################

def create_block(
        n, # number of blocks
        ri, # inner radius
        t, # thickness
        h, # height of the block
    
        n_l, # number of segments in l direction
        n_t, # number of segments in t direction
        n_h, # number of segments in h direction

        amplitude, # A*sin(x)
        frequency, # sin(f*x)
        shift, # sin(x+s*pi), if s=0.5 -> cos() 

        cylindrical, # True, False: form of the block (round or not)
        frame, # True, False: frame block

        cell_types, # {'2D': 'quad4', '3D': 'hex8'}

        inout='out', # where to create the sinus curve - inner or outer radius
        
        gap={'on': False, 'size': 0.0} # create gap between blocks (needed for Abaqus simulations)
):
    
    alpha = 2*np.pi/n
    
    l = ri*np.sqrt(2*(1-np.cos(alpha/2)))

    ######################################################
    # 2D grid of points
    ######################################################
    if cylindrical:
        points = create_grid_cylindrical_segment(n_l, n_t)
    else:
        points = create_point_grid(l, t, n_l, n_t)
        
    # plot_point_cloud(points)    

    ######################################################
    # Create 2D cells
    ######################################################
    if cell_types['2D'] == 'tri3':
        triangles, tri3_cells = create_tri3_cells(np.array(points))
        
    elif cell_types['2D'] == 'quad4':
        quads, quad4_cells = create_quad4_cells(np.array(points))
    
    # # Plot the 2D mesh
    # plot_faces(
    #     np.array(points), len(triangles), np.array(tri3_cells),
    #     nodes=True, ids=False,
    #     save=False, path="test.png"
    # )

    ######################################################
    # extrude
    ######################################################
    points_arr = np.array(points)

    # gap between sinus curves
    if gap['on']:
        all_points_arr0 = create_layers(points_arr, h - gap['size'], n_h)
    else:
        all_points_arr0 = create_layers(points_arr, h, n_h)

    all_points = all_points_arr0.tolist()

    ######################################################
    # transformations of the grid
    ######################################################
    if cylindrical:

        if frame:
            if inout == 'in':
                transform_sin_z_in(all_points, 1., 1., h, amplitude, frequency, shift*np.pi)
            elif inout == 'in_top_out_bottom':
                transform_sin_in_top_out_bottom_z(all_points, 1., 1., h, amplitude, frequency, shift * np.pi)
            elif inout == 'in_bottom_out_top':
                transform_sin_in_bottom_out_top_z(all_points, 1., 1., h, amplitude, frequency, shift * np.pi)
            else:
                transform_sin_z(all_points, 1., 1., h, amplitude, frequency, shift*np.pi)
        else:
            if inout == 'in':
                transform_sin_in(all_points, 1., 1., amplitude, frequency, shift*np.pi)
            elif inout == 'in_top_out_bottom':
                transform_sin_in_top_out_bottom(all_points, 1., 1., h, amplitude, frequency, shift * np.pi)
            elif inout == 'in_bottom_out_top':
                transform_sin_in_bottom_out_top(all_points, 1., 1., h, amplitude, frequency, shift * np.pi)
            else:
                transform_sin(all_points, 1., 1., amplitude, frequency, shift*np.pi)

        # gap between side surfaces
        if gap['on']:
            transform_cylinder_gap(all_points, ri, alpha, t, gap['size'])
        else:
            transform_cylinder(all_points, ri, alpha, t)

    else:

        if frame:
            transform_sin_z(all_points, l, t, h, amplitude, frequency, shift*np.pi)
        else:
            transform_sin(all_points, l, t, amplitude, frequency, shift*np.pi)

        transform_distortion(all_points, ri, alpha, l, t)
        
    
    all_points_arr = np.array(all_points)

    ######################################################
    # create 3D cells and return dict
    ######################################################
    if cell_types['3D'] == 'prism6':
        prism6, prism6_arr = create_prism6_cells(len(points), triangles, n_h)
        return {'n': n, 'ri': ri, 't': t, 'h': h,
                'alpha': alpha, 'shift': shift, 'frequency': frequency,
                'n_l': n_l, 'n_t': n_t, 'n_h': n_h,
                'all_points': all_points_arr,
                # 'cells': prisms6, 'cells_arr': prism6_arr
                'cells': {'2D': None, '3D': prism6},
                'cells_arr': {'2D': None, '3D': prism6_arr},
                'frame': frame,
                }

    elif cell_types['3D'] == 'hex8':
        hex8, hex8_arr = create_hex8_cells(len(points), quads, n_h)
        return {'n': n, 'ri': ri, 't': t, 'h': h,
                'alpha': alpha, 'shift': shift, 'frequency': frequency,
                'n_l': n_l, 'n_t': n_t, 'n_h': n_h,
                'all_points': all_points_arr,
                # 'cells': hex8, 'cells_arr': hex8_arr,
                'cells': {'2D': None, '3D': hex8},
                'cells_arr': {'2D': None, '3D': hex8_arr},
                'frame': frame,
                }


########################################################################
# Faces (surface)
########################################################################

def group_faces( block ):

    ri = block['ri']
    t = block['t']
    tol = 1e-3  # tolerance for floating point comparison
    
    #############################################
    # Collect cells that satisfy the condition
    #############################################
    surf_filter = {
        'inner_surf': [], # faces on inner radius
        'outer_surf': [], # faces on outer radius
    }
    idx_bottom = [] # faces on the flat bottom plane
    idx_left = [] # faces on the left plane
    idx_right = [] # faces on the right plane
    
    # get surface mesh
    mesh = block['surface']
    
    for cid in range(block['surface'].n_cells):
        
        # get cell points and their coordinates
        pt_ids = mesh.get_cell(cid).point_ids
        coords = mesh.points[pt_ids]

        # compute the radius and z-coord of each point and filter the faces
        r = np.linalg.norm(np.stack([coords[:,0], coords[:,1]+ri], axis=1), axis=1)
        outer = np.allclose(r, ri+t, atol=tol)
        inner = np.allclose(r, ri, atol=tol)

        if outer:
            surf_filter['outer_surf'].append(cid)
        elif inner:
            surf_filter['inner_surf'].append(cid)
            
        # if frame block filter out also the bottom faces
        if block['frame']:
            
            z = coords[:,2]
            phi = np.arctan2(coords[:,1]+ri, coords[:,0])
            
            bottom = np.allclose(z, 0.0, atol=tol)
            left = np.allclose(phi, block['alpha']/2, atol=tol)
            right = np.allclose(-phi, -block['alpha']/2, atol=tol)
            
            if bottom:
                idx_bottom.append(cid)

            if left:
                idx_left.append(cid)

            if right:
                idx_right.append(cid)

    if block['frame']:
        surf_filter['bottom_surf'] = idx_bottom
        surf_filter['left_surf'] = idx_left
        surf_filter['right_surf'] = idx_right
        
    block['surf_filter'] = surf_filter
    
    return block

############################################################################

def get_blocks(config, assembly_config):
    
    # create the sinus block
    block = create_block(
        config['n'], config['ri'], config['t'], config['h'],
        config['n_l'], config['n_t'], config['n_h'],
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], False, config['cell_types'],
        config['inout']
    )
    
    # create the bottom frame block
    frame_block_bottom = create_block(
        config['n'], config['ri'], config['t'], config['h']/2,
        config['n_l'], config['n_t'], config['n_h']//2,
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], True, config['cell_types'],
        config['inout']
    )
        
    # create the top frame block
    frame_block_top = create_block(
        config['n'], config['ri'], config['t'], config['h']/2,
        config['n_l'], config['n_t'], config['n_h']//2,
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], True, config['cell_types'],
        config['inout']
    )

    blocks = {
        'block': block,
        'frame_block_bottom': frame_block_bottom,
        'frame_block_top': frame_block_top,
    }
    
    return blocks

def get_blocks_inout(config, assembly_config):
    
    # create the sinus block
    block1 = create_block(
        config['n'], config['ri'], config['t'], config['h'],
        config['n_l'], config['n_t'], config['n_h'],
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], False, config['cell_types'],
        'in_bottom_out_top'
    )

    block2 = create_block(
        config['n'], config['ri'], config['t'], config['h'],
        config['n_l'], config['n_t'], config['n_h'],
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], False, config['cell_types'],
        'in_top_out_bottom'
    )

    # create the bottom frame block
    if assembly_config['order']:
        frame_block_bottom = create_block(
            config['n'], config['ri'], config['t'], config['h']/2,
            config['n_l'], config['n_t'], config['n_h']//2,
            config['amplitude'], config['frequency'], config['shift'],
            config['cylindrical'], True, config['cell_types'],
            'in_top_out_bottom'
        )
    else:
        frame_block_bottom = create_block(
            config['n'], config['ri'], config['t'], config['h']/2,
            config['n_l'], config['n_t'], config['n_h']//2,
            config['amplitude'], config['frequency'], config['shift'],
            config['cylindrical'], True, config['cell_types'],
            'in_bottom_out_top'
        )
        
    # create the top frame block
    if (assembly_config['order'] and assembly_config['n_layers'] % 2 == 0) or (not assembly_config['order'] and assembly_config['n_layers'] % 2 == 1):
        frame_block_top = create_block(
            config['n'], config['ri'], config['t'], config['h']/2,
            config['n_l'], config['n_t'], config['n_h']//2,
            config['amplitude'], config['frequency'], config['shift'],
            config['cylindrical'], True, config['cell_types'],
            'in_top_out_bottom'
        )
    else:
        frame_block_top = create_block(
            config['n'], config['ri'], config['t'], config['h']/2,
            config['n_l'], config['n_t'], config['n_h']//2,
            config['amplitude'], config['frequency'], config['shift'],
            config['cylindrical'], True, config['cell_types'],
            'in_bottom_out_top'
        )

    blocks = {
        'block': [block1, block2],
        'frame_block_bottom': frame_block_bottom,
        'frame_block_top': frame_block_top,
    }
    
    return blocks


def get_blocks_abq(config):
    
    # create the sinus block
    block = create_block(
        config['n'], config['ri'], config['t'], config['h'],
        config['n_l'], config['n_t'], config['n_h'],
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], False, config['cell_types'],
        config['inout'],
        gap=config['gap']
    )
    
    # create the bottom frame block
    frame_block_bottom = create_block(
        config['n'], config['ri'], config['t'], config['h']/2,
        config['n_l'], config['n_t'], config['n_h']//2,
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], True, config['cell_types'],
        config['inout'],
        gap=config['gap']
    )
        
    # create the top frame block
    frame_block_top = create_block(
        config['n'], config['ri'], config['t'], config['h']/2,
        config['n_l'], config['n_t'], config['n_h']//2,
        config['amplitude'], config['frequency'], config['shift'],
        config['cylindrical'], True, config['cell_types'],
        config['inout'],
        gap=config['gap']
    )

    blocks = {
        'block': block,
        'frame_block_bottom': frame_block_bottom,
        'frame_block_top': frame_block_top,
    }
    
    return blocks

