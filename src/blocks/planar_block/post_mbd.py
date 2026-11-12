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


def load_areas(snaps_file, snaps):
    '''
    Loads the areas of the contact faces (areas.txt next to snaps.txt, same
    layout). Returns None if the file does not exist (older runs).
    '''
    areas_file = Path(snaps_file).with_name('areas.txt')
    if not areas_file.exists():
        return None
    areas = np.loadtxt(areas_file)
    if areas.shape != snaps.shape:
        raise ValueError(f"areas.txt {areas.shape} does not match snaps.txt {snaps.shape}")
    return areas


def compute_measures(snaps, areas=None):
    '''
    Measures of the contact pressure of an assembly (one column per block).

    Area based definitions (default for planar assemblies, see CHANGES.md):
      A_eff    = mean over the blocks of A_eff,b / A_b with
                 A_eff,b = (int p dA)^2 / int p^2 dA
      p_eff    = mean over the blocks of the area weighted mean pressure on
                 the effective region (faces with the highest pressure until
                 their area reaches A_eff,b)
      p_max    = maximum pressure, p_max_bl_avg = mean of the block maxima
    Without areas (older runs) all faces get the same area; A_eff is then the
    original count based value.

    The original count based values ('A_eff_count', 'p_eff_count': global
    mean over the masked faces of all blocks) are returned for comparison.
    '''
    if areas is None:
        areas = np.where(np.isnan(snaps), np.nan, 1.)

    A_new = compute_eff_area_weighted(snaps, areas)
    p_new = measure_pc_weighted(snaps, areas, A_new['mask'])

    A_old = compute_eff_area(snaps)
    p_old = measure_pc(snaps, A_old['mask'])

    return {
        'A_eff': A_new['average'],
        'p_eff': p_new['p_eff_avg'],
        'p_max': p_new['p_max'],
        'p_max_bl_avg': p_new['p_max_bl_avg'],
        'A_eff_count': A_old['average'],
        'p_eff_count': p_old['p_eff_bl_avg'],
        'A_eff_bl': A_new['per_block'],
        'p_eff_bl': p_new['p_eff_bl'],
        'mask': A_new['mask'],
    }


def analyse_results(snaps_file, show=False):

    snaps = np.loadtxt(snaps_file)
    if snaps.ndim == 1:
        snaps = snaps[:, None]
    areas = load_areas(snaps_file, snaps)
    measures = compute_measures(snaps, areas)

    if show:
        if areas is None:
            print("areas.txt not found: all faces weighted equally")
        print(f"Average effective area: {measures['A_eff']}")
        print(f"Average effective pressure: {measures['p_eff']}")
        print(f"Max pressure: {measures['p_max']}")
        print(f"Average of max pressure: {measures['p_max_bl_avg']}")

    return measures


def analyse_results_to_excel(snaps_file, output_file='results.xlsx', show=False):

    measures = analyse_results(snaps_file)
    results = {
        'Average effective area': measures['A_eff'],
        'Average pressure masked': measures['p_eff'],
        'Max pressure': measures['p_max'],
        'Average of max pressure': measures['p_max_bl_avg'],
    }

    df = pd.DataFrame([results])
    df.to_excel(output_file, index=False)

    if show:
        print(f"Ergebnisse wurden in '{output_file}' gespeichert:")
        print(df.to_string(index=False))

    return {'measures': measures, 'results': results}


def compute_eff_area_weighted(snaps, areas):
    '''
    Area weighted effective contact area per block:
        A_eff,b / A_b = (sum p_i A_i)^2 / (A_b * sum p_i^2 A_i)
    (participation ratio of the pressure field; 1 for uniform pressure).
    The mask contains the faces with the highest pressure until their
    cumulated area reaches A_eff,b (for equal areas: the int(N_eff) faces of
    the count based definition).
    '''
    valid = ~np.isnan(snaps) & ~np.isnan(areas)
    p = np.where(valid, np.abs(np.nan_to_num(snaps, nan=0.)), 0.)
    a = np.where(valid, np.nan_to_num(areas, nan=0.), 0.)

    A_b = a.sum(axis=0)
    A_eff_b = (p * a).sum(axis=0)**2 / ((p**2 * a).sum(axis=0) + 1e-30)
    frac = A_eff_b / A_b

    M = np.zeros_like(snaps, dtype=bool)
    for j in range(snaps.shape[1]):
        idx = np.argsort(p[:, j], kind='stable')[::-1]
        idx = idx[valid[idx, j]]
        cum = np.cumsum(a[idx, j])
        take = cum <= A_eff_b[j] * (1 + 1e-9)
        take[0] = True  # at least the face with the highest pressure
        M[idx[take], j] = True

    return {'per_block': frac, 'average': np.mean(frac), 'mask': M, 'A_eff_b': A_eff_b}


def measure_pc_weighted(snaps, areas, M):
    '''
    Area weighted mean pressure on the effective region of every block,
    then the arithmetic mean over the blocks (definition of the paper).
    '''
    valid = ~np.isnan(snaps) & ~np.isnan(areas)
    p = np.nan_to_num(snaps, nan=0.)
    a = np.where(valid & M, np.nan_to_num(areas, nan=0.), 0.)

    p_eff_bl = (p * a).sum(axis=0) / a.sum(axis=0)
    p_max_bl = np.nanmax(snaps, axis=0)

    return {
        'p_eff_bl': p_eff_bl,
        'p_eff_avg': np.mean(p_eff_bl),
        'p_max': np.nanmax(snaps),
        'p_max_bl': p_max_bl,
        'p_max_bl_avg': np.mean(p_max_bl),
    }


def measure_pc(snaps, M, show=False):
    # original definition (global mean over the masked faces), kept for comparison
    
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
    Original count based definition (kept for comparison).
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
