"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-10
Last Modified: ?

License: MIT

Reference:
"""

import numpy as np
import os

from src.engine.mbd import compute_contact_pressure, check_kinematic_feasibility
from src.blocks.block_mbd import get_mbd_data, get_block_matrices
from src.engine.util import makeDirIfNotExists, save_to_json
from src.engine.plots import plot_assembly_and_frame, plot_assembly_quantity, plot_assembly

############################################################################
# test force equilibrium and plot contact pressure
############################################################################
def analyse_contact_pressure(block_config,
                             get_blocks,
                             group_faces,
                             blocks_bvp_config,
                             bvp_type,
                             assembly_config,
                             get_assembly,
                             set_bvp,
                             plot_config,
                             out_config,
                             info):
    blocks = get_blocks(block_config)
    
    assembly_all = get_assembly( blocks, assembly_config, block_config )
    setup_blocks(assembly_all['together'], group_faces, blocks_bvp_config[bvp_type],bvp_type,assembly_config)
    
    
    # select the boundary value problem (script dependent)
    ass_part = set_bvp(bvp_type, assembly_all, block_config, assembly_config)

    #plot_assembly(
    #    assembly_all[plot_config['assembly_all']],
    #    plt_conf=plot_config,
    #)

    # Do the simulation
    compute_contact_pressure(assembly_all[ass_part], info)
    
    # Plot the pressure contact and save the solution as snaps
    plot_and_save_pc(assembly_all, plot_config, out_config, info)
    
    # release memory
    del blocks
    del assembly_all
    
    return

############################################################################
# test kinematic feasibility
############################################################################
def test_interlocking(block_config,
                      get_blocks,
                      group_faces,
                      blocks_bvp_config,
                      bvp_type,
                      assembly_config,
                      get_assembly,
                      set_bvp,
                      plot_config,
                      out_config,
                      info):
    
    blocks = get_blocks(block_config)

    assembly_all = get_assembly( blocks, assembly_config, block_config )
    setup_blocks(assembly_all['together'], group_faces, blocks_bvp_config[bvp_type],bvp_type,assembly_config)

    # select the boundary value problem (script dependent)
    ass_part = set_bvp(bvp_type, assembly_all, block_config, assembly_config)
    
    # test the kinematic feasibility
    lp_method = assembly_config['lp_method']
    check_kinematic_feasibility(assembly_all['together'], info, lp_method)
    
    # release memory
    del blocks
    del assembly_all

    return


############################################################################
# prepare blocks
############################################################################

def setup_blocks(blocks, group_faces, bvp_config, bvp_type, assembly_config=None):
    y_max_global = 0.5 * (assembly_config['m']+1)-0.25
    x_max_global = 2 * (assembly_config['n']+1)
    block_config = bvp_config['block']

    for block in blocks:
        if not hasattr(block, 'surf_filter'):
            if bvp_type == 'wall_left' and y_max_global is not None and x_max_global is not None:
                block = group_faces(block, x_max_global, y_max_global)
            else:
                block = group_faces(block)
      
        block = categorize_face_groups(
            block,
            f_ext_surf=block_config['f_ext_surf'],
            free_surf=block_config['free_surf'],
        )
        
        if not hasattr(block, 'face_areas'):
            block.face_areas = compute_face_areas(block)
        
        block = get_block_matrices(block, block_config['q'])
    
    return blocks

def compute_face_areas(block):
    """
    Compute area of each triangular face in the block.
    
    Args:
        block: Block object with 'cells_2D' (n,3) and 'nodes' (m,3)
    
    Returns:
        numpy array of shape (n,) with face areas
    """
    faces = block.cells_2D          # (n_faces, 3)
    verts = block.nodes             # (n_nodes, 3)
    
    # Vektorisierte Berechnung
    p0 = verts[faces[:, 0]]
    p1 = verts[faces[:, 1]]
    p2 = verts[faces[:, 2]]
    
    cross = np.cross(p1 - p0, p2 - p0)
    areas = 0.5 * np.linalg.norm(cross, axis=1)
    
    return areas

def categorize_face_groups(block, f_ext_surf, free_surf):
    """
    Categorize face groups based on config names.
    
    Args:
        block: Block object with 'surf_filter' attribute
        f_ext_surf: List of surface names for external load
        free_surf: List of surface names for free surfaces
    
    Returns:
        Block object with 'face_groups' attribute
    """
    surf_filter = block.surf_filter

    if f_ext_surf:
        arrays = [np.asarray(surf_filter[i], dtype=int) for i in f_ext_surf if len(surf_filter[i]) > 0]
        if arrays:
            f_ext_faces = np.concatenate(arrays).astype(int)
        else:
            f_ext_faces = np.array([], dtype=int)
    else:
        f_ext_faces = np.array([], dtype=int)

    if free_surf:
        arrays = [np.asarray(surf_filter[i], dtype=int) for i in free_surf if len(surf_filter[i]) > 0]
        if arrays:
            free_faces = np.concatenate(arrays).astype(int)
        else:
            free_faces = np.array([], dtype=int)
    else:
        free_faces = np.array([], dtype=int)
    
    f_ext_free_faces = np.concatenate((f_ext_faces, free_faces))

    ###################################################
    # all indices of all the faces
    ##################################################
    all_faces = np.arange(len(block.cells_2D))

    #################################################
    # only contact faces
    ################################################
    mask = ~np.isin(all_faces, f_ext_free_faces)
    contact_faces = all_faces[mask]

    face_groups = {
        'all_faces': all_faces,
        'contact_faces': contact_faces,
        'f_ext_faces': f_ext_faces,
        'free_faces': free_faces,
    }
    
    block.face_groups = face_groups    # ← Attribut-Zugriff
    
    return block

######################################################################

def plot_and_save_pc(assembly_all, plot_config, out_config, info):
    
    # Plot the quantity distribution on contact surfaces
    plot_assembly_quantity(
        assembly_all[plot_config['assembly_all']],
        quantity_name='Contact pressure', # 'Contact pressure', 'lam',
        plt_conf=plot_config,
    )

    # save contact pressure solution as snapshot matrix
    save_solution(assembly_all['assembly'], out_config)

    # save information of the computation
    save_to_json(info, f"{out_config['out_dir']}{out_config['name']}/info.json")

    return


def save_solution(assembly, out_config):
    """
    Save contact pressure solution to file.
    
    Args:
        assembly: List of Block objects
        out_config: Output configuration dict
    """
    pressures = [np.asarray(bl.solutions['Contact pressure']) for bl in assembly]
    
    if not pressures or all(len(p) == 0 for p in pressures):
        print("Warning: no contact pressure data to save")
        return
    
    # Auf gleiche Länge bringen (Padding mit NaN)
    max_len = max(len(p) for p in pressures)
    padded = np.full((len(pressures), max_len), np.nan)
    for i, p in enumerate(pressures):
        padded[i, :len(p)] = p
    
    snaps = padded.T  # (max_len, n_blocks)
    
    os.makedirs(f"{out_config['out_dir']}{out_config['name']}", exist_ok=True)
    
    output_path = f"{out_config['out_dir']}{out_config['name']}/snaps.txt"
    np.savetxt(output_path, snaps, fmt='%.10e')
    print(f"Saved snaps with shape {snaps.shape} to {output_path}")
