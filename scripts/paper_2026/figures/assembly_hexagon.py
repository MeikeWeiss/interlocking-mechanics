"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-10-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""


from scripts.paper_2026.paper_figures.config_hexagon import *
from src.blocks.hexagon_based.block import get_blocks, group_faces
from src.blocks.hexagon_based.assembly import get_assembly # get_assembly_alternating
from src.blocks.run_mbd import setup_blocks
from src.engine.plots import plot_assembly_and_frame
from src.engine.util import makeDirIfNotExists

#### parameters #####################
n = 4 # 7
t = 40. # 20.
r0 = 120. # 150
n_l = 40  # 40
n_t = 20 # 10
n_layers = 12 # 4 

out_config['out_dir'] = './outputs/paper2026/figures/'
out_config['name'] = "assembly_hexagon"
bvp_type = 'tunnel'

##### plot config ################
plot_config['result_name'] = 'bvp' # 'assembly_frame'
plot_config['show'] = False
plot_config['save'] = True
plot_config['html'] = False
plot_config['views'] = ['xy',] # None, 'pers', 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['line_width'] = 4.
plot_config['intensity'] = 0.15
plot_config['window_size'] = (6000, 2000)
plot_config['zoom'] = 2.9

# Custom RGB color as float 0–1
rgb = np.array([240, 219, 168])
color = rgb/255
plot_config['color'] = color


########################################################################

def run():

    #### don't touch ######################
    block_config['n'] = n
    block_config['t'] = t
    block_config['r0'] = r0
    block_config['n_l'] = n_l
    block_config['n_t'] = n_t
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


if __name__ == '__main__':

    run()
