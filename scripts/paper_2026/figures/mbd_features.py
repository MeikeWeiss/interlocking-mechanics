"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-10-30
Last Modified: 2026-03-31

License: MIT

Reference:
"""


from scripts.paper_2026.paper_figures.config_sinus import *
from src.blocks.sinus_block.block import get_blocks, group_faces
from src.blocks.sinus_block.assembly import get_assembly # get_assembly_alternating
from src.blocks.run_mbd import setup_blocks
from src.engine.plots import plot_assembly_and_frame


def run():

    bvp_type = 'pipe'
    
    # create the sinus block
    blocks = get_blocks(block_config)

    setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])
    
    # assemble a tube
    assembly_all = get_assembly(blocks, assembly_config, block_config)
    
    # # Plot the mesh of the block
    # plot_faces(block['surface'].points,
    #            block['surface'].n_cells,
    #            block['surface'].faces,
    #            nodes=False, ids=False,
    #            save=False, path="images/sine-block.png")

    # idx_faces = block['face_groups']['contact_faces']
    # n_idx = len(idx_faces)
    # idx_ext = [j for i in idx_faces for j in range(i*5, i*5 + 5)]
    
    # # Plot a block with face normals
    # plot_block_surfaces(
    #     block['surface'].points,
    #     n_idx,
    #     block['surface'].faces[idx_ext],
    #     block['centroid'],
    #     block['face_centers'],
    #     block['unit_forces'],
    #     block['lever_vectors'],
    #     block['unit_momentum'],
    #     ids=False,
    #     save=False, path='./images/versatile_block_forces.png', # '.html'
    # ) 

    ################################################
    # Frame block
    ################################################
    # frame_block = create_block(
    #     n, ri, t, h/2,
    #     n_l, n_t, n_h//2,
    #     amplitude, frequency, shift,
    #     cylindrical, True, cell_types,
    # )

    # setup_frame_block_for_mbd_simulation(
    #     frame_block,
    #     f,
    #     f_ext_surf=['bottom_surf'], # 'outer_surf', 'inner_surf', 'bottom_surf'
    #     free_surf=[], # 'outer_surf', 'inner_surf', 'bottom_surf'
    # )
    
    # # Plot the mesh of the frame_block
    # plot_faces(frame_block['surface'].points,
    #            frame_block['surface'].n_cells,
    #            frame_block['surface'].faces,
    #            nodes=False, ids=False,
    #            save=False, path="images/sine-frame_block.png")

    # idx_faces = frame_block['face_groups']['contact_faces']
    # n_idx = len(idx_faces)
    # idx_ext = [j for i in idx_faces for j in range(i*5, i*5 + 5)]
    
    # # Plot a frame_block with face normals
    # plot_block_surfaces(
    #     frame_block['surface'].points,
    #     n_idx,
    #     frame_block['surface'].faces[idx_ext],
    #     frame_block['centroid'],
    #     frame_block['face_centers'],
    #     frame_block['unit_forces'],
    #     frame_block['lever_vectors'],
    #     frame_block['unit_momentum'],
    #     ids=False,
    #     save=False, path='./images/sinus_frame_block_forces.png', # '.html'
    # ) 

    
    # assemble a tube
    #assembly = [Block(0, block, np.array([0,0,0]), 0.)]

    # # Plot only the assembly
    # plot_assembly(assembly, save=False, path='images/round_block.png')    

    plot_assembly_and_frame(
        assembly_all['assembly'],
        assembly_all['frame_bottom'] + assembly_all['frame_top'],
        plot_config,
    )

    return





#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':

    run()

