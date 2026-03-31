"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""

import math

from scripts.paper_2026.analysis_sinus.config import *
from scripts.paper_2026.analysis_sinus.config_abq import abq_values, bvp_config
from src.blocks.sinus_block.block import get_blocks_abq, group_faces
from src.blocks.sinus_block.assembly import get_assembly
from src.blocks.abq_inp import generate_abq_input
from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k

#### block parameters #####################
n = 4
t = 40.
amp = 20.
fr = 1.5
sh = 0.
n_layers = 12 #12
q = 1e-2
pres_overclosure = [2e-2, 1e-2] # clearance, pressure
gap = {'on': True, 'size': 1e-2}
#out_config['out_dir'] = './outputs/paper/abq/'
out_config['out_dir'] = './outputs/paper2026/abq/'
#BVPs = ['pipe', 'tunnel', 'beam', 'shaft', pillar]
BVPs = ['pipe',]

##### plot config ################
plot_config['assembly_all'] = 'assembly' # 'together', 'assembly', 
plot_config['show'] = False
plot_config['save'] = False
plot_config['html'] = False
plot_config['views'] = ['pers'] # None, 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['line_width'] = 4.
plot_config['intensity'] = 0.15
plot_config['window_size'] = (2000, 2000)
plot_config['zoom'] = 1.

#### don't touch ######################
block_config['gap'] = gap # create gap between blocks
block_config['n'] = n
block_config['t'] = t
block_config['amplitude'] = amp
block_config['frequency'] = fr
block_config['shift'] = sh
assembly_config['n_layers'] = n_layers
block_config['n_t'] = 11  #int(block_config['t']//3)
block_config['n_l'] = nearest_divisible_by_k(
    160//block_config['n'],
    k=int(block_config['frequency']*4)
)
block_config['n_h'] = int(block_config['h']//20)
bc_config['q'] = q
abq_values['abq_config']['load_p'] = q
abq_values['contact_config']['pressure-overclosure'] = pres_overclosure

########################################################################


def run():

    for i, bvp_type in enumerate(BVPs):

        out_config['name'] = f"{bvp_type}/n{n}_t{t}_sh{sh}_fr{fr}_a{amp}_nLay{n_layers}"
        out_dir = f"{out_config['out_dir']}{out_config['name']}/"
        inp_path = f"{out_dir}{bvp_type}.inp"
        plot_config['out_dir'] = out_dir
        makeDirIfNotExists(out_dir)

        abq_values['bc_n_config']['bl_surf'] = bvp_config[bvp_type]['bl_surf']
        abq_values['bc_n_config']['el_surf'] = bvp_config[bvp_type]['el_surf']
        abq_values['bc_n_config']['bl_ids'] = bvp_config[bvp_type]['bl_ids']
        abq_values['bc_n_config']['bl_ids_fixed'] = bvp_config[bvp_type]['bl_ids_fixed']

        if bvp_type == 'pillar':
            template_path = './src/blocks/sinus_block/template_abq_inp_pillar.j2'
        else:
            template_path = './src/blocks/sinus_block/template_abq_inp_tunnel.j2'
            
        generate_abq_input(
            block_config,
            get_blocks_abq,
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




def exponential_from_two_points(x0, y0, x1, y1, x):
    """
    Returns the y-value of a shifted exponential passing through (x0, y0) and (x1, y1)
    at a given x-coordinate.

    Function form: y = A * (exp(B * (x - x0)) - 1)
    """
    if y1 <= 0:
        raise ValueError("y1 must be positive for exponential growth.")
    
    # Solve for B first (using x0 as reference, y0 assumed 0)
    B = math.log(1 + y1 / y1) / (x1 - x0) if y0 == 0 else math.log((y1 / y0) + 1) / (x1 - x0)
    
    # Solve for A
    A = y1 / (math.exp(B * (x1 - x0)) - 1)
    
    # Compute y at x
    y = A * (math.exp(B * (x - x0)) - 1)
    return y


if __name__ == '__main__':

    run()

    # x0, y0 = -2e-2, 0.
    # x1, y1 = 0., 1e-2
    # x = 0.01
    # y = exponential_from_two_points(x0, y0, x1, y1, x)
    # print(f"y({x}) = {y}")
