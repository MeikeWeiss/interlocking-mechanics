"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""

from scripts.paper_2026.analysis_hexagon.config import *
from src.blocks.hexagon_based.block import get_blocks, group_faces
from src.blocks.hexagon_based.assembly import get_assembly
from src.blocks.run_mbd import analyse_contact_pressure, test_interlocking
from src.engine.util import makeDirIfNotExists

#### parameters #####################
n = 4
t = 40.
n_layers = 12
q = 0.01
#out_config['out_dir'] = './outputs/paper/bvps/'
out_config['out_dir'] = './outputs/paper2026/bvps/'
bvp_type = 'tunnel'

##### plot config ################
plot_config['assembly_all'] = 'assembly'
plot_config['show'] = True
plot_config['save'] = False
plot_config['html'] = False
plot_config['views'] = ['pers'] # None, 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['clim'] = None # [0., 1.5], None
plot_config['line_width'] = 4.
plot_config['intensity'] = 0.15
plot_config['window_size'] = (2000, 6000)
plot_config['zoom'] = 2.9
plot_config['clim'] = None #[0, 0.05]
#### don't touch ######################
block_config['n'] = n
block_config['t'] = t
assembly_config['n_layers'] = n_layers
assembly_config['lp_method'] = 'mechanism_test' # 'dof', 'norm2', 'wang2018'

bc_config['q'] = q

out_config['name'] = f"{bvp_type}/hexagon_n{n}_t{t}"
out_dir = f"{out_config['out_dir']}{out_config['name']}/"
plot_config['out_dir'] = out_dir
makeDirIfNotExists(out_dir)
########################################################################

def run(mode='force_equilibrium'):

    if mode == 'force_equilibrium':
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

    elif mode == 'interlocking_test':
        test_interlocking(
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


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':

    run('interlocking_test')
    run('force_equilibrium')
    
