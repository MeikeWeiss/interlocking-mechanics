"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-08-30
Last Modified: ?

License: MIT

Reference:
"""

import numpy as np

from src.engine.plots import plot_assembly_quantity
from src.engine.util import makeDirIfNotExists, load_from_json
from src.blocks.block_class import Block
from src.blocks.run_mbd import setup_blocks


def analyse_results(snaps_file, show=False):
    
    # load snaps
    snaps = np.loadtxt(snaps_file)

    A_eff = compute_eff_area(snaps, show=False)
    measures = measure_pc(snaps, A_eff['mask'], show=False)

    if show:
        print(f"Effective area per block:\n {A_eff['per_block']}")
        print(f"Average effective area:\n {A_eff['average']}")
        
        print(f"Average pressure masked per block:\n {measures['avg_pc_masked_per_block']}")
        print(f"Average pressure masked: {measures['avg_pc_masked']}")
        print(f"Average pressure: {measures['avg_pc']}")
        print(f"Max pressure per block:\n {measures['max_pc_per_block']}")
        print(f"Max pressure:\n {measures['max_pc']}")
        print(f"Average of max pressure:\n {measures['avg_max_pc_per_block']}")

    return {'A_eff': A_eff, 'measures': measures}


def measure_pc(snaps, M, show=False):
    
    # average of masked elements per column
    avg_pc_masked_per_block = (snaps * M).sum(axis=0) / M.sum(axis=0)
    avg_pc_masked = (snaps * M).sum() / M.sum()
    avg_pc = np.mean(snaps)
    
    max_pc_per_block = np.max(snaps, axis=0)
    max_pc = np.max(snaps)
    avg_max_pc_per_block = np.mean(max_pc_per_block)

    measures = {
        'p_avg': avg_pc,
        'p_eff_bl': avg_pc_masked_per_block,
        'p_eff_bl_avg': avg_pc_masked,
        'p_max': max_pc,
        'p_max_bl': max_pc_per_block,
        'p_max_bl_avg': avg_max_pc_per_block,
    }
    
    if show:
        print(f"Average pressure masked per block:\n {avg_pc_masked_per_block}")
        print(f"Average pressure masked: {avg_pc_masked}")
        print(f"Average pressure: {avg_pc}")
        print(f"Max pressure per block:\n {max_pc_per_block}")
        print(f"Max pressure:\n {max_pc}")
        print(f"Average of max pressure:\n {avg_max_pc_per_block}")

    return measures


def compute_eff_area(snaps, show=False):

    '''
    Measures how many contact surfaces effectively contribute
    (sensitive to distribution concentration) in the contact.
    '''
    
    # Participation ratio / effective area
    f = np.abs(snaps) 
    N_eff = (f.sum(axis=0)**2) / ( (f**2).sum(axis=0) + 1e-30 )
    eff_fraction_per_block = N_eff / snaps.shape[0]
    
    # Mask from participation ratio
    M = np.zeros_like(snaps, dtype=bool)  # (n, m)
    for j in range(snaps.shape[1]):
        col = np.abs(snaps[:, j])
        N_eff_j = int((col.sum()**2) / ( (col**2).sum() + 1e-30 ))
        idx_sorted = np.argsort(col)[::-1]
        M[idx_sorted[:N_eff_j], j] = True

    A_eff = {
        'per_block': eff_fraction_per_block,
        'average': np.mean(eff_fraction_per_block),
        'mask': M,
    }
    
    if show:
        print(f"Effective area per block:\n {eff_fraction_per_block}")
        print(f"Average effective area:\n {np.mean(eff_fraction_per_block)}")
        
    return A_eff


def compute_active_fraction(snaps):    

    '''
    Computes fraction of contact surfaces flagged as influenced.
    '''
    # p = 5 # Relative / percentile threshold
    # T = np.percentile(np.abs(snaps), p, axis=0)
    T = 0.1
    M = (np.abs(snaps) >= T)
    # Fraction of grid points flagged as influenced:
    active_fraction = M.sum(axis=0) / M.shape[0]
    #print(active_fraction)
    print(M.sum(axis=0))

    return M


###########################################################################
# visualize snaps
###########################################################################

def plot_snaps(snaps_file,
               n_snaps,
               block_config,
               get_blocks,
               group_faces,
               blocks_bvp_config,
               bvp_type,
               plot_config ):
    
    
    # load snaps
    snaps = np.loadtxt(snaps_file)
    
    # create blocks and set them up for mbd simulation
    blocks = get_blocks(block_config)
    setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])

    # initialize block
    bl = Block(
        0,
        blocks['block'],
        np.array([0., 0., 0.]),
        0.,
        block_config['rot_axis']
    )
    
    for s in range(n_snaps):

        bl.solutions['Contact pressure'] = snaps[:,s]
        
        # Plot the quantity distribution on contact surfaces
        plot_assembly_quantity(
            [bl,], # assembly_together
            quantity_name='Contact pressure', # 'Contact pressure', 'lam',
            plt_conf=plot_config,
        )

    return
