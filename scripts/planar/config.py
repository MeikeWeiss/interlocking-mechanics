import numpy as np


def new_info():
    '''fresh dict for the computation info (timings, residuals) of one run'''
    return {
        't_cpu': {
            'real_0': {},
            'real_1': {},
            'cpu_0': {},
            'cpu_1': {},
            'dt_cpu': {},
            'dt_real': {},
        }
    }


info = new_info()

block_config = {
    'refinement': 2, # number of refinement levels for the triangulation of the block
    'type': 'versatile',
    'h': None,
    'edgeLength': None
}

assembly_config = {
    'n': 4, 
    'm': 4,
    'group': 'p1',
    'lp_method': 'mechanism_test', # 'dof', 'norm2', 'wang2018', 'mechanism_test'
}


out_config = {
    'out_dir': './outputs/planar/',
    'name': 'test-solution',
    'snap_name': '',
}

# Custom RGB color as float 0–1
rgb = np.array([119, 252, 192])
color = rgb/255
rgb_frame = np.array([250, 106, 171])
color_frame = rgb_frame/255

plot_config  = {
    'window_size': (4000, 6000),
    'show_edges': True,
    'line_width': 5.,
    'show_nodes': False,
    'point_size': 12,
    'node_ids': False,
    'color': color,
    'color_frame': color_frame,
    'opacity': 1.,
    'ambient': 0.1,
    'intensity': 0.15,
    'grid_and_origin': False,
    'result_name': 'contact_pressure',
    'out_dir': './outputs/planar/analysis/',
    'show': False,
    'save': True, # False
    'html': True, # set 'show' on False
    'views': ['pers'], # None, 'xy', 'yx',['xy', ]
    'parallel': False, # parallel projection (perspective): True
    'clim': None, # color map limits: None, [vmin, vmax]
    'assembly_all': 'assembly', # which part of the assembly to plot
    'zoom': 1.0,
}


#####################################################################
# BVP cases
#####################################################################

# Flächen, die nicht im Kontakt sind müssen kategorisiert werden.
# Kontaktflächen ohne Kontaktpartner wirken als starres Auflager (Rahmen).
blocks_bvp_config = {
    'ceiling': {
        'block': {
            'q': 1e-2, # MPa
            'f_ext_surf': ['top_surf',], # Flächen auf die Last aufgetragen werden
            'free_surf': ['bottom_surf',], # Flächen die nicht im Kontakt sind und keine Last aufnehmen
        }
    },
    'wall_left': {
        'block': {
            'q': 1e-2, # MPa
            'f_ext_surf': ['ext_surf', 'top_left'], # Flächen auf die Last aufgetragen werden
            'free_surf': ['top_surf','bottom_surf'],
        },
    },
    'wall_right': {
            'block': {
                'q': 1e-2, # MPa
                'f_ext_surf': ['ext_surf', 'top_right'], # Flächen auf die Last aufgetragen werden
                'free_surf': ['top_surf','bottom_surf'],
            },
        }
}
