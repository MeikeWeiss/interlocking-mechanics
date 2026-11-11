"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
Last Modified: ?

License: MIT

Reference:
"""


from scripts.paper_2026.analysis_sinus.config import *
from src.blocks.sinus_block.block import get_blocks, group_faces
from src.blocks.sinus_block.post_mbd import plot_snaps
from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k

#### parameters #####################
n = 3
t = 40.
amp = 15.
fr = 1.5
sh = 0.0
n_layers = 3 #12
q = 0.01
out_config['out_dir'] = './outputs/paper2026/bvps/'
bvp_type = 'pillar'

##### plot config ################
plot_config['assembly_all'] = 'together'
plot_config['show'] = True
plot_config['save'] = False
plot_config['html'] = False
plot_config['views'] = ['pers'] # None, 'xy', 'yx',['xy', ]
plot_config['parallel'] = True
plot_config['clim'] = [0., 1.5] # None

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

out_config['name'] = f"{bvp_type}/n{n}_t{t}_sh{sh}_fr{fr}_a{amp}"
out_dir = f"{out_config['out_dir']}{out_config['name']}/"
plot_config['out_dir'] = out_dir
snaps_file = f"{out_dir}snaps.txt"
n_snaps = 2
########################################################################

def run():

    plot_snaps(
        snaps_file,
        n_snaps,
        block_config,
        get_blocks,
        group_faces,
        blocks_bvp_config,
        bvp_type,
        plot_config,
    )

    return

#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':

    run()
