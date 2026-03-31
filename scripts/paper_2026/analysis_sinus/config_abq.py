"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
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

# Dirichlet BCs
bc_d_config = {
    'type': 'ENCASTRE',
}

# Neumann BCs
bc_n_config = {
    'bl_surf': [7,8], # [4,5], [7,8] 
    'el_surf': 'S5', # which surface of the element to load: pipe -'S3', tunnel - 'S5', torsion - 'S4', 'S6'
    'bl_ids': list(range(3*4)), # [6*4,], list(range(12*4)),  list(range(len(assembly)))
    'smooth_step': [0., 0., 0.15, 1.] # t0,a0,t1,a1
}

contact_config = {
    'friction': 0.01,
    'pressure-overclosure': [1e-3, 1e-4], # clearance, pressure [2.0e-2, 0.1]
}

abq_config = {
    'load_p': 1.e-2,
    't_end': 0.2,
    'bulk_viscosity': [0.06, 1.2],
    'out_n_intervals': 200, # how many time steps to save
}

##################################################################
# BVPs
##################################################################
bvp_config = {
    'pipe': {
        'bl_surf': [4,5],
        'el_surf': 'S3',
        'bl_ids': list(range(4*12)),
        'bl_ids_fixed': list(range(2*4)),
    },
    'tunnel': {
        'bl_surf': [7,8],
        'el_surf': 'S5',
        'bl_ids': list(range(4*12)),
        'bl_ids_fixed': list(range(2*4)),
    },
    'pillar': {
        'bl_surf': [0,],
        'el_surf': 'S1',
        'bl_ids': [4,5,6,7],
        'bl_ids_fixed': [0,1,2,3],
    },
    'beam': {
        'bl_surf': [7,8],
        'el_surf': 'S5',
        'bl_ids': [6*4,],
        'bl_ids_fixed': list(range(2*4)),
    },
    'shaft': {
        'bl_surf': [7,8],
        'el_surf': 'S4',
        'bl_ids': [6*4, 6*4+1, 6*4+2, 6*4+3], # neumann
        'bl_ids_fixed': list(range(2*4)), # dirichlet
    },
}

##################################################################
# dictionary of all configurations for the abq input file
##################################################################
abq_values = {
    'assembly': None,
    'assembly_frame': None,
    'mat_config': mat_config,
    'bc_d_config': bc_d_config,
    'bc_n_config': bc_n_config,
    'contact_config': contact_config,
    'abq_config': abq_config,
    #'el_surf': 'S3', # which surface of the element to load
}
