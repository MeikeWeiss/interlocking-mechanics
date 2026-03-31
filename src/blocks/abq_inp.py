"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-08-30
Last Modified: ?

License: MIT

Reference:
"""


from src.blocks.run_mbd import setup_blocks
from src.engine.plots import plot_assembly_and_frame
from src.abq import jinja2_templater as jt


def generate_abq_input(block_config,
                       get_blocks,
                       group_faces,
                       blocks_bvp_config,
                       bvp_type,
                       assembly_config,
                       get_assembly,
                       plot_config,
                       values,
                       template_path,
                       inp_path,
                       ):

    # create block according to the configurations
    blocks = get_blocks(block_config)
    setup_blocks(blocks, group_faces, blocks_bvp_config[bvp_type])

    # create assembly from the block
    assembly_all = get_assembly( blocks, assembly_config, block_config )
    
    plot_assembly_and_frame(
        assembly_all['assembly'],
        assembly_all['frame_bottom'] + assembly_all['frame_top'],
        plot_config,
    )
    
    values['assembly'] = assembly_all['assembly']
    values['assembly_frame'] = assembly_all['frame_bottom'] + assembly_all['frame_top']
    
    # generate input file using the tamplate and values
    jt.Templater(inp_path, template_path, values)

    # release memory
    del blocks
    del assembly_all

    return

