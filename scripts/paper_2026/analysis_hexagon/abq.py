"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""

import numpy as np

from scripts.paper_2026.analysis_hexagon.config import *
from scripts.paper_2026.analysis_hexagon.config_abq import abq_values, bvp_config
from src.blocks.hexagon_based.block import get_blocks, group_faces
from src.blocks.hexagon_based.assembly import get_assembly
from src.blocks.abq_inp import generate_abq_input
from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k


#### parameters #####################
n = 4
t = 40.
n_layers = 12
q = 0.01

pres_overclosure = [2e-2, 1e-2] # clearance, pressure
gap = {'on': True, 'size': 1e-2}

out_config['out_dir'] = './outputs/paper2026/abq/'
# BVPs = ['pipe', 'tunnel', 'pillar', 'beam', 'shaft']
# clim = [[0.0, 0.4], [0.0, 0.05], [0.0, 0.014], [0.0, 0.2], [0.0, 0.25],]
BVPs = ['pipe', ]

##### plot config ################
plot_config['assembly_all'] = 'assembly' # 'together', 'assembly', 
plot_config['result_name'] = 'contact_pressure'
plot_config['show'] = True
plot_config['save'] = False
plot_config['html'] = False
plot_config['views'] = ['pers'] # None, 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['line_width'] = 4.
plot_config['intensity'] = 0.15
plot_config['window_size'] = (6000, 4000)
plot_config['zoom'] = 1.2

#### don't touch ######################
block_config['gap'] = gap # create gap between blocks
block_config['n'] = n
block_config['t'] = t
assembly_config['n_layers'] = n_layers
block_config['n_t'] = 11
block_config['n_l'] = int(80//block_config['n'])
    
bc_config['q'] = q

abq_values['abq_config']['load_p'] = q
abq_values['contact_config']['pressure-overclosure'] = pres_overclosure

########################################################################

def run():

    for i, bvp_type in enumerate(BVPs):

        out_config['name'] = f"{bvp_type}/hexagon_n{n}_t{t}"
        out_dir = f"{out_config['out_dir']}{out_config['name']}/"
        inp_path = f"{out_dir}{bvp_type}.inp"
        plot_config['out_dir'] = out_dir
        makeDirIfNotExists(out_dir)

        abq_values['bc_n_config']['bl_surf'] = bvp_config[bvp_type]['bl_surf']
        abq_values['bc_n_config']['el_surf'] = bvp_config[bvp_type]['el_surf']
        abq_values['bc_n_config']['bl_ids'] = bvp_config[bvp_type]['bl_ids']
        abq_values['bc_n_config']['bl_ids_fixed'] = bvp_config[bvp_type]['bl_ids_fixed']

        template_path = './src/blocks/hexagon_based/template_abq_inp.j2'
            
        generate_abq_input(
            block_config,
            get_blocks,
            group_faces,
            blocks_bvp_config,
            bvp_type,
            assembly_config,
            get_assembly,
            plot_config,
            values=abq_values,
            template_path=template_path,
            inp_path=inp_path,
        )

    return


if __name__ == '__main__':

    run()
