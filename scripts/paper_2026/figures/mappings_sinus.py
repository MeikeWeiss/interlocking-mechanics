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
from src.blocks.sinus_block.transformations import transform_sin, transform_cylinder_ri
from src.blocks.sinus_block.block import create_point_grid, create_layers
from src.engine.cells import create_tri3_cells, create_quad4_cells, create_hex8_cells
from src.engine.plots import plot_faces, plot_cells
from src.engine.util import makeDirIfNotExists

#### parameters #####################
n = 5
t = 20.
h = 30.
ri = 50.
n_l = 20
n_t = 10
n_h = 10
amp = 10.
fr = 1.
sh = 0.
n_layers = 3 #12

out_config['out_dir'] = './outputs/paper2026/figures/'
out_config['name'] = "mapping_sinus"
bvp_type = 'pillar'

##### plot config ################
plot_config['show'] = False
plot_config['save'] = True
plot_config['html'] = False
plot_config['views'] = ['pers',] # None, 'pers', 'xy', 'yx',['xy', ]
plot_config['parallel'] = False
plot_config['line_width'] = 3.
plot_config['window_size'] = (4000, 3000)

# Custom RGB color as float 0–1
rgb = np.array([99, 185, 255])
color = rgb/255
plot_config['color'] = color


########################################################################

def run():

    #### don't touch ######################
    block_config['n'] = n
    block_config['t'] = t
    block_config['h'] = h
    block_config['ri'] = ri
    block_config['n_l'] = n_l
    block_config['n_t'] = n_t
    block_config['n_h'] = n_h
    block_config['amplitude'] = amp
    block_config['frequency'] = fr
    block_config['shift'] = sh
    assembly_config['n_layers'] = n_layers

    out_dir = f"{out_config['out_dir']}{out_config['name']}/"
    plot_config['out_dir'] = out_dir
    makeDirIfNotExists(out_dir)

    plot_mappings(block_config, plot_config)

    return


def plot_mappings(bl_conf, plt_conf):

    # set depnedent parameters
    alpha = 2*np.pi/bl_conf['n']
    l = bl_conf['ri']*np.sqrt(2*(1-np.cos(alpha/2)))

    ########################################################################
    # create 2D grid of points
    points = create_point_grid(
        l,
        bl_conf['t'],
        bl_conf['n_l'],
        bl_conf['n_t']
    )
        
    # plot_point_cloud(points)
    
    ########################################################################    
    # Create plane (2D) cells
    if bl_conf['cell_types']['2D'] == 'tri3':
        triangles, tri3_cells = create_tri3_cells(np.array(points))
        
    elif bl_conf['cell_types']['2D'] == 'quad4':
        quads, quad4_cells = create_quad4_cells(np.array(points))
    
    # Plot the 2D mesh
    plt_conf['result_name'] = 'grid'
    plot_faces(
        np.array(points), len(quads), np.array(quad4_cells),
        plt_conf,
    )
    
    ########################################################################
    # sin mapping
    transform_sin(
        points,
        l,
        bl_conf['t'],
        bl_conf['amplitude'],
        bl_conf['frequency'],
        bl_conf['shift']*np.pi
    )

    # Plot the sin mapping
    plt_conf['result_name'] = 'sin-mapping'
    plot_faces(
        np.array(points),
        len(quads),
        np.array(quad4_cells),
        plt_conf,
    )

    # ########################################################################
    # # cylindrical mapping of the grid
    # transform_cylinder_ri(points, bl_conf['ri'], alpha, l, bl_conf['t'])

    # # Plot the cylindrical mapping
    # plt_conf['result_name'] = 'cylindrical-mapping'
    # plot_faces(
    #     np.array(points),
    #     len(quads),
    #     np.array(quad4_cells),
    #     plt_conf,
    # )

    ########################################################################
    # extrude
    points_arr = np.array(points)
    all_points_arr = create_layers(points_arr, bl_conf['h'], bl_conf['n_h'])
    all_points = all_points_arr.tolist()
    
    hex8, hex8_arr = create_hex8_cells(len(points), quads, bl_conf['n_h'])

    plt_conf['result_name'] = 'extrude-mapping'
    plot_cells(
        all_points_arr,
        len(hex8),
        hex8_arr,
        plt_conf,
    )

    ########################################################################
    # cylindrical mapping of the planar block
    transform_cylinder_ri(all_points, bl_conf['ri'], alpha, l, bl_conf['t'])

    # Plot the cylindrical mapping
    rgb = np.array([119, 252, 192])
    color = rgb/255
    plt_conf['color'] = color
    plt_conf['result_name'] = 'cylindrical-mapping'
    plot_cells(
        np.array(all_points),
        len(hex8),
        hex8_arr,
        plt_conf,
    )


    return


if __name__ == '__main__':

    run()
