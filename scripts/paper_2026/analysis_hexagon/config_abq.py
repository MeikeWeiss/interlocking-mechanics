"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2026-03-31
Last Modified: 2026-03-31

License: MIT

Reference:
"""

import numpy as np

######################################################################
# Abaqus parameters: units are in [mm] and [MPa]
######################################################################

mat_config = {
    'density': 2400.0e-12,
    'E': 33.e3,
    'nu': 0.2,
    'damping_alpha': 2.,
    'damping_beta': 1e-8,
}

bc_d_config = {
    #'name': 'BC-Set-1',
    'type': 'ENCASTRE',
}

bc_n_config = {
    'smooth_step': [0., 0., 1., 1.]
}

contact_config = {
    'friction': 0.01,
    'pressure-overclosure': [2.0e-2, 0.1],
}

abq_config = {
    'load_p': 1.e-2,
    't_end': 2.,
    'bulk_viscosity': [0.06, 1.2],
    'out_n_intervals': 300, # how many time steps to save
}

##################################################################
# BVPs
##################################################################
bvp_config = {
    'pipe': {
        'bl_surf': [4,5],
        'el_surf': 'S1',
        'bl_ids': list(range(4*12)),
        'bl_ids_fixed': list(range(2*4)),
    },
    # 'tunnel': {
    #     'bl_surf': [7,8],
    #     'el_surf': 'S1',
    #     'bl_ids': list(range(4*12)),
    #     'bl_ids_fixed': list(range(2*4)),
    # },
}

##################################################################
# dictionary of all configurations for the abq input file
##################################################################

abq_values = {
    'assembly': None, #assembly,
    'assembly_frame': None, #assembly_frame,
    'mat_config': mat_config,
    'bc_d_config': bc_d_config,
    'bc_n_config': bc_n_config,
    'contact_config': contact_config,
    'abq_config': abq_config,
    'el_surf': 'S1', # which surface of the element to load
}

