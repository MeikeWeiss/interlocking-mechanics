"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""

from scripts.paper_2026.analysis_sinus.config import *
from src.blocks.sinus_block.block import get_blocks, group_faces
from src.blocks.sinus_block.assembly import get_assembly
from src.blocks.run_mbd import setup_blocks
from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k
from src.blocks.sinus_block.post_mbd import analyse_results
from src.engine.plots import plot_assembly_quantity

#### parameters #####################
n = 4
t = 40.
amp = 20.
fr = 1.5
sh = 0. # 0.5
n_layers = 12
q = 0.01
out_config['out_dir'] = './outputs/paper2026/bvps/'
# BVPs = ['pipe', 'tunnel', 'pillar', 'beam', 'shaft']
# clim = [[0., 0.4], [0., 0.05], [0., 0.014], [0., 0.2], [0., 0.25],]
# BVPs = ['pipe', 'tunnel', 'shaft']
# clim = [[0.0, 0.4], [0.0, 0.03], [0.0, 0.25]]
BVPs = ['tunnel',]
clim = [ [0.0, 0.05],]
n_lay = 7 # number of the layer to plot
layer = [(n_lay-1) * n + i for i in range(n)]
#layer = [(n_lay-1) * n, ]

##### plot config ################
plot_config['result_name'] = f'pc_layer{n_lay}'
#plot_config['result_name'] = f'pc_layer{n_lay}_block1'
plot_config['show'] = False
plot_config['save'] = True
plot_config['html'] = False
plot_config['views'] = ['xy', 'yx'] #['zx', 'xz'] # None, 'xy', 'yx',['xy', ]
plot_config['parallel'] = True
plot_config['line_width'] = 8.
plot_config['intensity'] = 0.15
plot_config['window_size'] = (3000, 3000)
plot_config['zoom'] = 1.0

#### don't touch ######################
block_config['n'] = n
block_config['t'] = t
block_config['amplitude'] = amp
block_config['frequency'] = fr
block_config['shift'] = sh
assembly_config['n_layers'] = n_layers
block_config['n_t'] = int(2*(block_config['t']//3))
block_config['n_l'] = nearest_divisible_by_k(
    180//block_config['n'],
    k=int(block_config['frequency']*4)
)
bc_config['q'] = q

########################################################################

def run():

    for i, bvp_type in enumerate(BVPs):

        out_config['name'] = f"{bvp_type}/n{n}_t{t}_sh{sh}_fr{fr}_a{amp}"
        out_dir = f"{out_config['out_dir']}{out_config['name']}/"
        plot_config['out_dir'] = out_dir
        makeDirIfNotExists(out_dir)

        plot_config['clim'] = clim[i]
        
        # load snaps
        snaps = np.loadtxt(f"{out_dir}snaps.txt")

        # create blocks
        blocks = get_blocks(block_config)
        setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])

        # create assembly
        assembly_all = get_assembly( blocks, assembly_config, block_config )

        # select the boundary value problem (script dependent)
        ass_part = set_bvp(bvp_type, assembly_all, block_config, assembly_config)

        # prescribe solutions (from snaps) to the blocks
        for bl in assembly_all['assembly']:
            bl.solutions['Contact pressure'] = snaps[:,bl.ID]
        
        # Plot the quantity distribution on contact surfaces
        plot_assembly_quantity(
            [assembly_all['assembly'][i] for i in layer],
            quantity_name='Contact pressure', # 'Contact pressure', 'lam',
            plt_conf=plot_config,
        )

    return


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':

    run()
