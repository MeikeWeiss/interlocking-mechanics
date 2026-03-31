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
from src.blocks.run_mbd import analyse_contact_pressure
from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k
from src.blocks.post_mbd import analyse_results


#### parameters #####################
n = 4
t = 40.
amp = 20.
fr = 1.5
sh = 0. # 0.5
n_layers = 12
q = 0.01
#out_config['out_dir'] = './outputs/paper/bvps_v0.3/'
out_config['out_dir'] = './outputs/paper2026/bvps/'
BVPs = ['pipe', 'tunnel', 'pillar', 'beam', 'shaft']
clim = [[0.0, 0.4], [0.0, 0.05], [0.0, 0.014], [0.0, 0.2], [0.0, 0.25],]
# BVPs = ['pipe',]
# clim = [ [0.0, 0.4],]

##### plot config ################
plot_config['assembly_all'] = 'assembly' # 'together', 'assembly',
plot_config['result_name'] = 'contact_pressure'
plot_config['show'] = False
plot_config['save'] = True
plot_config['html'] = False
plot_config['views'] = ['pers'] # None, 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['line_width'] = 4.
plot_config['intensity'] = 0.15
plot_config['window_size'] = (2000, 6000)
plot_config['zoom'] = 2.9

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

        analyse_contact_pressure(
            block_config,
            get_blocks,
            group_faces,
            blocks_bvp_config,
            bvp_type,
            assembly_config,
            get_assembly,
            set_bvp,
            plot_config,
            out_config,
            info
        )


    return


def compute_measure():

    print(f"BVP   Equilibrium    Effective area     p_eff_avg     p_max_avg\n")
    for i, bvp_type in enumerate(BVPs):

        out_config['name'] = f"{bvp_type}/n{n}_t{t}_sh{sh}_fr{fr}_a{amp}"
        out_dir = f"{out_config['out_dir']}{out_config['name']}/"
        snaps_file = f"{out_dir}snaps.txt"
        
        # 'avg_pc_masked', 'avg_max_pc_per_block'
        results = analyse_results(snaps_file, show=False)
        
        print(f"{bvp_type} & yes & ${results['A_eff']['average']*100:.1f}$ & ${results['measures']['p_eff_bl_avg']:.3f}$ & ${results['measures']['p_max_bl_avg']:.3f}$")
        
    return


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':

    run()
    compute_measure()
