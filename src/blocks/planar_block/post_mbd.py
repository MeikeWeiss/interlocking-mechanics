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
import pandas as pd
from pathlib import Path

from src.engine.plots import plot_assembly_quantity
from src.engine.util import makeDirIfNotExists, load_from_json
from src.blocks.planar_block.assembly import Block
from src.blocks.planar_block.run_mbd_planar import setup_blocks_planar


def analyse_results(snaps_file, show=False):
    
    # load snaps
    snaps = np.loadtxt(snaps_file)

    A_eff = compute_eff_area(snaps, show=False)
    measures = measure_pc(snaps, A_eff['mask'], show=False)

    if show:
        #print(f"Effective area per block:\n {A_eff['per_block']}")
        print(f"Average effective area:\n {A_eff['average']}")
        
        #print(f"Average pressure masked per block:\n {measures['p_eff_bl']}")
        print(f"Average pressure masked: {measures['p_eff_bl_avg']}")
        #print(f"Average pressure:\n {measures['p_avg']}")
        #print(f"Max pressure per block:\n {measures['p_max_bl']}")
        print(f"Max pressure:\n {measures['p_max']}")
        print(f"Average of max pressure:\n {measures['p_max_bl_avg']}")

    return {'A_eff': A_eff, 'measures': measures}

def analyse_results_to_excel(snaps_file, output_file='results.xlsx', show=False):
    
    # load snaps
    snaps = np.loadtxt(snaps_file)
    
    A_eff = compute_eff_area(snaps, show=False)
    measures = measure_pc(snaps, A_eff['mask'], show=False)
    
    results = {
        'Average effective area': A_eff['average'],
        'Average pressure masked': {measures['p_eff_bl_avg']},
        'Max pressure': measures['p_max'],
        'Average of max pressure': measures['p_max_bl_avg']
    }
    
    df = pd.DataFrame([results])
    df.to_excel(output_file, index=False)
    
    if show:
        print(f"Ergebnisse wurden in '{output_file}' gespeichert:")
        print(df.to_string(index=False))
    
    return {'A_eff': A_eff, 'measures': measures, 'results': results}


def measure_pc(snaps, M, show=False):
    
    # snaps may contain NaN (padding, if the blocks have different numbers
    # of contact faces); NaN entries are ignored
    snaps_0 = np.nan_to_num(snaps, nan=0.)
    M = M & ~np.isnan(snaps)

    # average of masked elements per column
    avg_pc_masked_per_block = (snaps_0 * M).sum(axis=0) / M.sum(axis=0)
    avg_pc_masked = (snaps_0 * M).sum() / M.sum()
    avg_pc = np.nanmean(snaps)
    
    max_pc_per_block = np.nanmax(snaps, axis=0)
    max_pc = np.nanmax(snaps)
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
    
    # snaps may contain NaN (padding, if the blocks have different numbers
    # of contact faces); NaN entries are ignored
    valid = ~np.isnan(snaps)
    n_faces = valid.sum(axis=0)  # number of contact faces per block

    # Participation ratio / effective area
    f = np.abs(np.nan_to_num(snaps, nan=0.))
    N_eff = (f.sum(axis=0)**2) / ( (f**2).sum(axis=0) + 1e-30 )
    eff_fraction_per_block = N_eff / n_faces
    
    # Mask from participation ratio
    M = np.zeros_like(snaps, dtype=bool)  # (n, m)
    for j in range(snaps.shape[1]):
        col = f[:, j]
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
    
    # create the reference block and set it up for the plot
    # (group_faces is not used: the faces are grouped by the planar driver)
    blocks = get_blocks(block_config)

    # initialize block
    bl = Block(
        0,
        blocks['block'],
        np.array([0., 0., 0.]),
        0.
    )
    setup_blocks_planar([bl], blocks_bvp_config[bvp_type], bvp_type)
    
    for s in range(n_snaps):

        bl.solutions['Contact pressure'] = snaps[:,s]
        
        # Plot the quantity distribution on contact surfaces
        plot_assembly_quantity(
            [bl,], # assembly_together
            quantity_name='Contact pressure', # 'Contact pressure', 'lam',
            plt_conf=plot_config,
        )

    return
