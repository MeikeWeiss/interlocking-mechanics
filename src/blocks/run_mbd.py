"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-10
Last Modified: ?

License: MIT

Reference:

Driver for the tubular assemblies (sine block, hexagon based block) used in
the paper. The reference blocks are prepared (``setup_blocks``) *before* they
are assembled; the ``Block`` objects of the assembly copy the prepared data.

Planar assemblies use their own driver in
``src/blocks/planar_block/run_mbd_planar.py`` because their face groups depend
on the position of each block in the assembly.
"""

import numpy as np
import os

from src.engine.mbd import compute_contact_pressure, check_kinematic_feasibility
from src.blocks.block_mbd import get_mbd_data, get_block_matrices
from src.engine.util import makeDirIfNotExists, save_to_json
from src.engine.plots import plot_assembly_quantity

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

    blocks = get_blocks(block_config, assembly_config)
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

    blocks = get_blocks(block_config, assembly_config)
    setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])

    assembly_all = get_assembly( blocks, assembly_config, block_config )

    # select the boundary value problem (script dependent)
    ass_part = set_bvp(bvp_type, assembly_all, block_config, assembly_config)

    # the frame blocks are appended after the assembly blocks in 'together'
    # and are the ones that are fixed in space
    n_fixed = count_frame_blocks(assembly_all)

    # test the kinematic feasibility
    lp_method = assembly_config['lp_method']
    result = check_kinematic_feasibility(assembly_all['together'], info, lp_method, n_fixed=n_fixed)

    # release memory
    del blocks
    del assembly_all

    return result


def count_frame_blocks(assembly_all):
    '''number of fixed frame blocks at the end of assembly_all['together']'''

    together = assembly_all['together']
    n_fixed = len(together) - len(assembly_all['assembly'])

    # the frame has to be the tail of 'together'
    assert together[:len(assembly_all['assembly'])] == assembly_all['assembly'], \
        "expected 'together' = 'assembly' + frame blocks"

    return n_fixed


############################################################################
# prepare blocks
############################################################################
def setup_blocks(blocks, group_faces, bvp_config, bvp_type=None):
    '''
    Prepares the reference blocks (dicts) for the MBD computation.

    blocks: dict of reference blocks, e.g. {'block': ..., 'frame_block_bottom': ...}.
            An entry may also be a list of reference blocks (e.g. in/out variants).
    bvp_type: unused, kept for backwards compatibility of the call signature.
    '''

    for block_type, config in bvp_config.items():

        variants = blocks[block_type]
        if not isinstance(variants, (list, tuple)):
            variants = [variants]

        for block in variants:

            # compute data needed for the computation: normal vectors, unit forces, etc.
            get_mbd_data(block)

            # create groups of surface faces
            if 'surf_filter' not in block:
                group_faces(block)

            block['face_groups'] = categorize_face_groups(
                block['surf_filter'],
                n_faces=block['surface'].n_cells,
                f_ext_surf=config['f_ext_surf'],
                free_surf=config['free_surf'],
            )

            # compute block matrices for MBD: q - load pressure, f_ext - faces where load is applied
            get_block_matrices(block, config['q'])

    return


def categorize_face_groups(surf_filter, n_faces, f_ext_surf, free_surf):
    '''
    Splits the faces of a block into loaded, free and contact faces.

    surf_filter: dict, name of the surface -> list of face ids
    n_faces:     total number of surface faces of the block
    f_ext_surf:  names of the surfaces that carry the external load
    free_surf:   names of the surfaces that are neither loaded nor in contact

    Returns the dict of face groups.
    '''

    def collect(names):
        arrays = [np.asarray(surf_filter[name], dtype=int) for name in (names or [])]
        if arrays:
            return np.concatenate(arrays)
        return np.array([], dtype=int)

    f_ext_faces = collect(f_ext_surf)
    free_faces = collect(free_surf)

    # all indices of all the faces
    all_faces = np.arange(n_faces)

    # only contact faces
    mask = ~np.isin(all_faces, np.concatenate((f_ext_faces, free_faces)))
    contact_faces = all_faces[mask]

    face_groups = {
        'all_faces': all_faces,
        'contact_faces': contact_faces,
        'f_ext_faces': f_ext_faces,
        'free_faces': free_faces,
    }

    return face_groups

######################################################################

def plot_and_save_pc(assembly_all, plot_config, out_config, info):

    # Plot the quantity distribution on contact surfaces (skipped if no
    # output is requested: no window, no file)
    if plot_config.get('show') or plot_config.get('save') or plot_config.get('html'):
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
    '''
    Saves the contact pressure as snapshot matrix (one column per block).

    If the blocks have different numbers of contact faces (e.g. planar walls),
    the shorter columns are padded with NaN.
    '''

    out_dir = f"{out_config['out_dir']}{out_config['name']}"
    os.makedirs(out_dir, exist_ok=True)

    pressures = [np.asarray(bl.solutions['Contact pressure']) for bl in assembly]
    lengths = {len(p) for p in pressures}

    if len(lengths) == 1:
        # identical to the published version (same format of snaps.txt)
        snaps = np.array(pressures).T
    else:
        snaps = np.full((max(lengths), len(pressures)), np.nan)
        for j, p in enumerate(pressures):
            snaps[:len(p), j] = p

    np.savetxt(f"{out_dir}/snaps.txt", snaps)

    return
