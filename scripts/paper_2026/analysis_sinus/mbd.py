"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
Last Modified: ?

License: MIT

Reference:
"""


from turtle import mode

from scripts.paper_2026.analysis_sinus.config import *
from src.blocks.sinus_block.block import get_blocks, get_blocks_inout, group_faces
from src.blocks.sinus_block.assembly import get_assembly, get_assembly_inout
from src.blocks.run_mbd import analyse_contact_pressure, test_interlocking
from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k

#### parameters #####################
n = 4
t = 40.
amp = 20. #20.
fr = 1.5
sh = 0.
n_layers = 12
q = 0.01
out_config['out_dir'] = './outputs/paper2026/'
bvp_type = 'pillar'
inout='out' # 'in', 'out'

##### plot config ################
plot_config['assembly_all'] = 'assembly' # 'together', 'assembly', 'assembly_frame_top'
plot_config['show'] = True
plot_config['save'] = False
plot_config['html'] = False
plot_config['views'] = ['pers'] # None, 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['clim'] = None #[0., 1.] # None
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
block_config['inout'] = inout
assembly_config['n_layers'] = n_layers
assembly_config['lp_method'] = 'mechanism_test' # 'dof', 'norm2', 'wang2018', 'mechanism_test'

block_config['n_t'] = 22 # int(2*(block_config['t']//3))
block_config['n_l'] = nearest_divisible_by_k(
    180//block_config['n'], #180//block_config['n'],
    k=int(block_config['frequency']*4)
)
bc_config['q'] = q

out_config['name'] = f"{bvp_type}/n{n}_t{t}_sh{sh}_fr{fr}_a{amp}"
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


def run_inout(mode='force_equilibrium'):

    order = False # order=True: 1. Reihe in_bottom_out_top und 2.Reihe in_top_out_bottom (for False other way around)
    assembly_config['order'] = order

    if mode == 'force_equilibrium':
        analyse_contact_pressure(
            block_config,
            get_blocks_inout,
            group_faces,
            blocks_bvp_config,
            bvp_type,
            assembly_config,
            get_assembly_inout,
            set_bvp,
            plot_config,
            out_config,
            info
        )
        
    elif mode == 'interlocking_test':
        test_interlocking(
            block_config,
            get_blocks_inout,
            group_faces,
            blocks_bvp_config,
            bvp_type,
            assembly_config,
            get_assembly_inout,
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

    #run('interlocking_test')
    #run('force_equilibrium')
    #run_inout('interlocking_test')
    run_inout('force_equilibrium')
