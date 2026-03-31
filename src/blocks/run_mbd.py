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

from src.engine.mbd import compute_contact_pressure, check_kinematic_feasibility
from src.blocks.block_mbd import get_mbd_data, get_block_matrices
from src.engine.util import makeDirIfNotExists, save_to_json
from src.engine.plots import plot_assembly_and_frame, plot_assembly_quantity

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
    setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])
    
    assembly_all = get_assembly( blocks, assembly_config, block_config )
    
    # select the boundary value problem (script dependent)
    ass_part = set_bvp(bvp_type, assembly_all, block_config, assembly_config)
    
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
    setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])
    
    assembly_all = get_assembly( blocks, assembly_config, block_config )

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
def setup_blocks(blocks, group_faces, bvp_config):

    for block_type, config in bvp_config.items():

        # compute data needed for the computation: normal vectors, unit forces, etc.
        block = get_mbd_data(blocks[block_type])
        
        # create groups of surface faces

        if 'surf_filter' not in blocks[block_type]:
            
            block = group_faces( blocks[block_type] )
            
        block = categorize_face_groups(
            blocks[block_type],
            f_ext_surf=config['f_ext_surf'],
            free_surf=config['free_surf'],
        )
    
        # compute block matrices for MBD: f - force magnitude, f_ext - faces where load is applied
        block = get_block_matrices(blocks[block_type], config['q'])
    
    return


def categorize_face_groups(block, f_ext_surf, free_surf):

    surf_filter = block['surf_filter']
    
    if f_ext_surf:
        f_ext_faces = np.concatenate([surf_filter[i] for i in f_ext_surf])
    else:
        f_ext_faces = np.array([])  # or np.empty((0, ...)) with correct shape

    if free_surf:
        free_faces = np.concatenate([surf_filter[i] for i in free_surf])
    else:
        free_faces = np.array([])  # or np.empty((0, ...)) with correct shape
    
    f_ext_free_faces = np.concatenate((f_ext_faces, free_faces))

    ###################################################
    # all indices of all the faces
    ##################################################
    all_faces = np.arange(block['surface'].n_cells)

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
    
    block['face_groups'] = face_groups
    
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

    snaps = np.array([bl.solutions['Contact pressure'] for bl in assembly]).T
    np.savetxt(f"{out_config['out_dir']}{out_config['name']}/snaps.txt", snaps)

    return
