"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-10-30
Last Modified: ?

License: MIT

Reference:
"""



import numpy as np


info = {
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
    
    'n': 4, # number of blocks
    't': 40., # thickness
    'h': 200., # height of the block: 200
    'ri': 120., # inner radius
    
    'n_l': 180//4, # number of segments in l direction 
    'n_t': 25, # number of segments in t direction: 25 
    'n_h': 20, # number of segments in h direction: 25

    'amplitude': 15.,
    'frequency': 1.,
    'shift': 0., # cosinus block s = 1/2; sinus block s = 0

    'cylindrical': True,
    'frame': False,
    'inout': 'out', # sin curve inside or outside of the tube: 'in', 'out' 
    'cell_types': {'2D': 'quad4', '3D': 'hex8'},

    'rot_axis': 2,
}

assembly_config = {
    'n_layers': 12, #12
}

out_config = {
    'out_dir': './outputs/paper2026/figures/',
    'name': 'test-mapping',
}

# Custom RGB color as float 0–1
rgb = np.array([119, 252, 192])
color = rgb/255
rgb_frame = np.array([250, 106, 171])
color_frame = rgb_frame/255

plot_config  = {
    'window_size': (6000, 4000),
    'zoom': 1.2,
    'show_edges': True,
    'line_width': 4.,
    'show_nodes': True,
    'point_size': 12,
    'node_ids': False,
    'color': color,
    'color_frame': color_frame,
    'opacity': 1.,
    'ambient': 0.1,
    'intensity': 0.1,
    'grid_and_origin': False,
    'result_name': None,
    'out_dir': './outputs/paper/figures/',
    'show': True,
    'save': False, # False
    'html': False, # set 'show' on False
    'views': ['yz'], # None, 'pers', 'xy', 'yx',['xy', ]
    'parallel': False, # parallel projection (perspective): True
    'clim': [0., 1.5], # color map limits: None, [vmin, vmax]
    'assembly_all': 'together', # which part of assembly to plot
}


#####################################################################
# BVP cases
#####################################################################

blocks_bvp_config = {
    
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
            'f_ext_surf': ['outer_surf',], # 'outer_surf', 'inner_surf', 'bottom_surf'
            'free_surf': ['inner_surf',], # 'outer_surf', 'inner_surf', 'bottom_surf'
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
            'f_ext_surf': [], # 'outer_surf', 'inner_surf', 'bottom_surf'
            'free_surf': ['inner_surf', 'outer_surf'], # 'outer_surf', 'inner_surf', 'bottom_surf'
        },
        'frame_block_bottom': {
            'q': 0.,
            'f_ext_surf': [],
            'free_surf': [],
        },
        'frame_block_top': {
            'q': 0.5, # MPa
            'f_ext_surf': ['bottom_surf',],
            'free_surf': [],
        },
    },
    
    'beam': {
        'block': {
            'q': 0.1, #MPa 
            'f_ext_surf': [ 'outer_surf'], # 'outer_surf', 'inner_surf', 'bottom_surf'
            'free_surf': ['inner_surf',], # 'outer_surf', 'inner_surf', 'bottom_surf'
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
            'f_ext_surf': ['outer_surf'], # 'outer_surf', 'inner_surf', 'bottom_surf'
            'free_surf': ['inner_surf'], # 'outer_surf', 'inner_surf', 'bottom_surf'
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
            t_outer = n_outer @ Rz.T
            
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

