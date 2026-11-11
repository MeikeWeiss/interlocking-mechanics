"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-10-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""


from scripts.paper_2026.figures.config_sinus import *
from src.blocks.sinus_block.block import get_blocks, group_faces
from src.blocks.sinus_block.assembly import get_assembly # get_assembly_alternating
from src.blocks.run_mbd import setup_blocks
from src.engine.plots import plot_assembly_and_frame
from src.engine.util import makeDirIfNotExists

#### parameters #####################
n = 4 # 5
t = 40. # 30.
h =  200. # 50.
ri = 120. # 70.
n_l = 40 # 40
n_t = 30 # 10
n_h = 30 # 20
amp = 15. # 10.
fr = 1. # 1.
sh = 0. # 0.
n_layers = 12 # 5

out_config['out_dir'] = './outputs/paper2026/figures/'
out_config['name'] = "assembly_sinus"
bvp_type = 'pillar'

##### plot config ################
plot_config['result_name'] = 'bvp' # 'assembly_frame'
plot_config['show'] = False
plot_config['save'] = True
plot_config['html'] = False
plot_config['views'] = ['yz',] # None, 'pers', 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['line_width'] = 4.
plot_config['intensity'] = 0.15
plot_config['window_size'] = (2000, 6000)
plot_config['zoom'] = 2.9

########################################################################

def run():

    #### don't touch ######################
    block_config['n'] = n
    block_config['t'] = t
    block_config['h'] = h
    block_config['ri'] = ri
    block_config['n_l'] = n_l
    block_config['n_t'] = n_t
    block_config['n_h'] = n_h
    block_config['amplitude'] = amp
    block_config['frequency'] = fr
    block_config['shift'] = sh
    assembly_config['n_layers'] = n_layers

    out_dir = f"{out_config['out_dir']}{out_config['name']}/"
    plot_config['out_dir'] = out_dir
    makeDirIfNotExists(out_dir)
    
    # create the sinus block
    blocks = get_blocks(block_config)

    setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])
    
    # assemble a tube
    assembly_all = get_assembly(blocks, assembly_config, block_config)
    
    plot_assembly_and_frame(
        assembly_all['assembly'],
        assembly_all['frame_bottom'] + assembly_all['frame_top'],
        plot_config,
    )

    return


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':

    run()

