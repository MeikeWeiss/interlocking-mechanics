"""
Driver for the MBD analysis of planar assemblies.

In contrast to the tubular assemblies (src/blocks/run_mbd.py) the face groups
of a planar block depend on its position in the assembly (e.g. only the top
row of a wall is loaded). Therefore the blocks are prepared *after* they are
assembled, block by block.

Boundary conditions:
    'ceiling':    load q on the top faces (highest z), bottom faces free
    'wall_left':  load q from above on the top row and on the left end face
                  of the top row
    'wall_right': load q from above on the top row and on the right end face
                  of the top row

Contact faces without a contact partner act as rigid supports (frame).
"""

import numpy as np

from src.engine.mbd import compute_contact_pressure, check_kinematic_feasibility
from src.blocks.block_mbd import get_block_matrices
from src.blocks.run_mbd import categorize_face_groups, plot_and_save_pc
from src.blocks.planar_block.block import get_blocks, group_faces, group_faces_wall
from src.blocks.planar_block.assembly import get_assembly

WALL_BVPS = ('wall_left', 'wall_right')


def build_assembly(block_config, assembly_config, bvp_config, bvp_type):
    '''
    Creates the reference block, the assembly and prepares all blocks
    for the MBD computation.

    bvp_config: configuration of the boundary value problem, e.g.
                blocks_bvp_config['ceiling'] from scripts/planar/config.py
    '''
    blocks = get_blocks(block_config, assembly_config)
    assembly_all = get_assembly(blocks, assembly_config, block_config)
    setup_blocks_planar(assembly_all['together'], bvp_config, bvp_type)

    return assembly_all


def setup_blocks_planar(assembly, bvp_config, bvp_type):
    '''
    Groups the faces of the placed blocks and computes the block matrices.
    '''
    block_config = bvp_config['block']

    if bvp_type in WALL_BVPS:
        extent = assembly_extent(assembly)

    for block in assembly:

        if bvp_type in WALL_BVPS:
            group_faces_wall(block, extent)
        else:
            group_faces(block)

        block.face_groups = categorize_face_groups(
            block.surf_filter,
            n_faces=len(block.cells_2D),
            f_ext_surf=block_config['f_ext_surf'],
            free_surf=block_config['free_surf'],
        )

        get_block_matrices(block, block_config['q'])

    return assembly


def assembly_extent(assembly):
    '''bounding box of the assembly in the x-y plane'''
    nodes = np.vstack([bl.nodes for bl in assembly])
    return {
        'x_min': nodes[:, 0].min(),
        'x_max': nodes[:, 0].max(),
        'y_min': nodes[:, 1].min(),
        'y_max': nodes[:, 1].max(),
    }


############################################################################
# force equilibrium
############################################################################
def analyse_contact_pressure(block_config, assembly_config, bvp_config, bvp_type,
                             plot_config, out_config, info):

    assembly_all = build_assembly(block_config, assembly_config, bvp_config, bvp_type)

    compute_contact_pressure(assembly_all['assembly'], info)

    plot_and_save_pc(assembly_all, plot_config, out_config, info)

    return assembly_all


############################################################################
# kinematic feasibility
############################################################################
def test_interlocking(block_config, assembly_config, bvp_config, bvp_type, info):

    assembly_all = build_assembly(block_config, assembly_config, bvp_config, bvp_type)

    # planar assemblies contain no frame blocks: the frame is represented by
    # the contact faces without contact partner
    check_kinematic_feasibility(
        assembly_all['together'], info, assembly_config['lp_method'], n_fixed=0
    )

    return assembly_all
