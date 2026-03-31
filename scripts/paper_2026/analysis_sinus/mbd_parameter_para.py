"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""


from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm


from scripts.paper_2026.analysis_sinus.config import *
from src.blocks.sinus_block.block import get_blocks, group_faces
from src.blocks.sinus_block.assembly import get_assembly
from src.blocks.run_mbd import analyse_contact_pressure
from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k


def run():

    #out_config['out_dir'] = './outputs/paper/analysis/'
    out_config['out_dir'] = './outputs/paper2026/analysis/'
    
    # fixed parameters
    block_config['ri'] = 120.
    block_config['h'] = 200.

    plot_config['assembly_all'] = 'assembly'
    
    # parameter space
    amplitude = [10.,15.,20.,25.]
    shift = [0., 0.5]
    frequency = [1., 1.5, 2.0] 
    N = [2,3,4,5,6] # number of blocks per layer
    T = [30.,40.,50.,60.] # thickness of the block

    # amplitude = [10.,]
    # shift = [0., ]
    # frequency = [1., ] 
    # N = [2,] # number of blocks per layer
    # T = [30.,] # thickness

    # all parameter combinations
    param_combinations = list(product(T, shift, frequency, amplitude, N))


    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(tqdm(executor.map(run_mbd_simulation, param_combinations),
                            total=len(param_combinations)))

    
    return

def run_mbd_simulation(params):
    
    """Run one analysis for a single parameter combination."""

    # if other BVPs are desired you have to adjust set_bvp function
    bvp_type = 'pipe'
    
    t, sh, fr, amp, n = params
    block_config_base = block_config.copy()
    out_config_base = out_config.copy()
    plot_config_base = plot_config.copy()
    
    block_config_base['t'] = t
    block_config_base['n_t'] = int(2*(t//3))
    block_config_base['shift'] = sh
    block_config_base['frequency'] = fr
    block_config_base['amplitude'] = amp
    block_config_base['n'] = n
    
    # the discretization of l has to be devisable by k otherwise the mesh is non-conform
    block_config_base['n_l'] = nearest_divisible_by_k(180//n, k=int(fr*4))
    
    out_config_base['name'] = f'n{n}_t{t}_sh{sh}_fr{fr}_a{amp}'
    out_dir = f"{out_config_base['out_dir']}{out_config_base['name']}/"
    plot_config_base['out_dir'] = out_dir
    makeDirIfNotExists(out_dir)
        
    analyse_contact_pressure(
        block_config_base,
        get_blocks,
        group_faces,
        blocks_bvp_config,
        bvp_type,
        assembly_config,
        get_assembly,
        set_bvp,
        plot_config_base,
        out_config_base,
        info
    )

    return


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':
    
    run()
