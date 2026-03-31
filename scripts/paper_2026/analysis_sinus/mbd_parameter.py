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


def run():

    # if other BVPs are desired you have to adjust set_bvp function
    bvp_type = 'pipe'

    out_config['out_dir'] = './outputs/paper2026/analysis/'
    
    # fixed parameters
    block_config['ri'] = 120.
    block_config['h'] = 200.

    # parameter space
    amplitude = [10.,15.,20.,25.]
    shift = [0., 0.5]
    frequency = [1., 1.5, 2.0] 
    N = [2,3,4,5,6] # number of blocks per layer
    T = [30.,40.,50.,60.] # thickness

    # run analysis for each parameter set
    for t in T:
        block_config['t'] = t
        block_config['n_t'] = int(2*(t//3))
        
        for sh in shift:
            block_config['shift'] = sh
                
            for fr in frequency:
                block_config['frequency'] = fr
                    
                for amp in amplitude:
                    block_config['amplitude'] = amp

                    for n in N:
                        block_config['n'] = n

                        # the discretization of l has to be devisable by k otherwise the mesh is non-conform
                        block_config['n_l'] = nearest_divisible_by_k(180//n, k=int(fr*4))
            
                        out_config['name'] = f'n{n}_t{t}_sh{sh}_fr{fr}_a{amp}'
                        out_dir = f"{out_config['out_dir']}{out_config['name']}/"
                        plot_config['out_dir'] = out_dir
                        makeDirIfNotExists(out_dir)
                        
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


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':
    
    run()
