"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
Last Modified: 2026-03-25

License: MIT

Reference:
"""


import numpy as np
from src.engine.plots import plot_points_with_directions

info = {
    
    # This dictionary is a container of information about the computation
    # It will be filled during the computation
    
    't_cpu': {
        'real_0': {},
        'real_1': {},
        'cpu_0': {},
        'cpu_1': {},
        'dt_cpu': {},
        'dt_real': {},
    }
}

block_config = {

    # This is a dictionary of the block parameters and other configurations 
    
    'n': 4, # number of blocks
    't': 35., # thickness
    'r0': 120., # inner radius
    
    'n_l': 30, #180//4, # number of segments in l direction 
    'n_t': 15, #25, # number of segments in t direction: 25
    
    'cylindrical': True,
    'cell_types': {'2D': 'quad4', '3D': 'hex8'},

    'rot_axis': 0,
}

assembly_config = {

    # This is a dictionary of the assembly parameters and other configurations 
    
    'n_layers': 2, #12
}

bc_config = {
    
    # This is a dictionary of BC parameters
    
    'q': 0.01, #q = 1.e-2 # external force
}

out_config = {

    # This is a dictionary paths and names for outputs
    
    'out_dir': './outputs/paper2026/',
    'name': 'hexagon-based',
    'snap_name': ''
}

# Custom RGB color as float 0–1
rgb = np.array([240, 219, 168])
color = rgb/255
rgb_frame = np.array([99, 141, 247])
color_frame = rgb_frame/255

plot_config  = {

    # This is a dictionary of the plot configurations
    
    'window_size': (6000, 4000),
    'show_edges': True,
    'line_width': 5.,
    'show_nodes': False,
    'point_size': 12,
    'node_ids': False,
    'color': color,
    'color_frame': color_frame,
    'opacity': 1.,
    'ambient': 0.1,
    'grid_and_origin': False,
    'result_name': 'contact_pressure',
    'out_dir': './outputs/paper/bvps/',
    'show': True,
    'save': False, # False
    'html': False, # set 'show' on False
    'views': ['pers'], # None, 'xy', 'yx',['xy', ]
    'parallel': False, # parallel projection (perspective): True
    'clim': [0., 1.5], # color map limits: None, [vmin, vmax]
    'assembly_all': 'together', # which part of assembly to plot
}



#####################################################################
# BVP cases
#####################################################################



blocks_bvp_config = {

    ####################################################################
    # block has 2 groups of faces: 'outer_surf', 'inner_surf'
    # frame_block has 3 groups of faces: 'outer_surf', 'inner_surf', 'bottom_surf'
    #
    # These groups have to be assigned to eiter f_ext_surf of free_surf category
    # or if all faces are in contact then no group belogns to a category
    ####################################################################
    
    'pipe': {
        'block': {
            'q': 1e-2, # MPa
            'f_ext_surf': ['inner_surf',],
            'free_surf': ['outer_surf',],
        },
        'frame_block_bottom': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
        'frame_block_top': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
    },

    'tunnel': {
        'block': {
            'q': 1e-2, # MPa
            'f_ext_surf': ['outer_surf',],
            'free_surf': ['inner_surf',], 
        },
        'frame_block_bottom': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
        'frame_block_top': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
    },

    'pillar': {
        'block': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': ['inner_surf', 'outer_surf'],
        },
        'frame_block_bottom': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
        'frame_block_top': {
            'q': 1e-2, # MPa
            'f_ext_surf': ['bottom_surf',],
            'free_surf': [],
        },
    },
    
    'beam': {
        'block': {
            'q': 1e-2, #MPa 
            'f_ext_surf': [ 'outer_surf'],
            'free_surf': ['inner_surf',],
        },
        'frame_block_bottom': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
        'frame_block_top': {
            'q': 0., 
            'f_ext_surf': [],
            'free_surf': [],
        },
    },

    'shaft': {
        'block': {
            'q': 0.,
            'f_ext_surf': ['outer_surf'],
            'free_surf': ['inner_surf'],
        },
        'frame_block_bottom': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
        'frame_block_top': {
            'q': 0., # MPa
            'f_ext_surf': [],
            'free_surf': [],
        },
    },


}


def set_bvp( bvp_type, assembly_all, block_config, assembly_config):
    
    if bvp_type == 'beam':

        get_bending_case(
            assembly_all['together'],
            block_config['n']*(assembly_config['n_layers']//2 ), # block ID to load
        )

        # part of the assembly to compute on
        #ass_part = 'together'
        ass_part = 'assembly'

    elif bvp_type == 'shaft':

        '''fist assembly then frame (block IDs)!'''
        '''no frame for torsion, as the frame does not block the motion'''

        id0 = block_config['n']*(assembly_config['n_layers']//2)
        
        get_torsion_case(
            assembly_all['together'],
            np.arange(id0, id0+block_config['n']).tolist(),
            bc_config['q'],
        )
        
        # part of the assembly to compute on
        ass_part = 'assembly'
        #ass_part = 'together'

    elif bvp_type == 'pillar':

        ass_part = 'assembly_frame_top'
        #ass_part = 'together'

    else:
        # part of the assembly to compute on
        #ass_part = 'together'
        ass_part = 'assembly'
    
    
    return ass_part


def get_bending_case(assembly, k):

    '''k is the block ID number - this is the block to be loaded'''

    for i, bl in enumerate(assembly):
        # only block k stays loaded
        if i == k:
            pass
        else:
            bl.p_b = np.zeros((6))
    
    return


def get_torsion_case(assembly, k, q):

    '''k is a list of block where tangential forces are applied'''

    Rz = np.array([
        [np.cos(np.pi/2), -np.sin(np.pi/2), 0],
        [np.sin(np.pi/2),  np.cos(np.pi/2), 0],
        [0,              0,             1]
    ])
    Rx = np.array([
        [1,              0,               0],
        [0,  np.cos(np.pi/2), -np.sin(np.pi/2)],
        [0,  np.sin(np.pi/2),  np.cos(np.pi/2)]
    ])
    
    for i, bl in enumerate(assembly):
        # only block k stays loaded
        if i in k:
            idx_outer = bl.data['face_groups']['f_ext_faces']
            
            # normal vectors and lever vectors of outer faces
            n_outer = bl.face_normals[idx_outer, :]
            r_outer = bl.lever_vectors[idx_outer, :]

            # tangent vectors of outer faces and unit momentums
            #t_outer = np.column_stack([-n_outer[:,1], n_outer[:,0], n_outer[:,2]])
            #t_outer = n_outer
            t_outer = n_outer @ Rx.T

            # plot_points_with_directions(bl.face_centers[idx_outer], t_outer, scale=5)
            
            m_outer = np.cross(r_outer, t_outer)
            
            A = bl.data['face_areas'][idx_outer]
            f = q * A # compute force from load pressure q
            F_b = np.sum(f[:, np.newaxis] * t_outer, axis=0)
            M_b = np.sum(f[:, np.newaxis] * m_outer, axis=0)
            
            p_b = - np.hstack([F_b, M_b])

            bl.p_b = p_b
        else:
            bl.p_b = np.zeros((6))
    
    return


def get_pillar_case(assembly, k):

    '''
    this function adjusts the matrices of the top frame blocks to consider the right bcs
    of the pillar problem
    '''
    
    for bl in assembly[-k:]:
        
        # only blocks in top frame get adjusted: no moments

        bl.p_b[3:] = 0.
        bl.A_b[3:,:] = 0.
            
        
    return


