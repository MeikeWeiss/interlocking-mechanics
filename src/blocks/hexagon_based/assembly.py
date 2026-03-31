"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: ?

License: MIT

Reference:
Wenzheng Xu, Xiaoshan Lin, and Yi Min Xie. A novel non-planar interlocking element for tubular structures. Tunnelling and Underground Space Technology, 103:103503, 2020. doi: https://doi.org/10.1016/j.tust.2020.103503.
"""


import numpy as np

from src.blocks.block_class import Block
from src.engine.util import get_M_and_M6

def get_assembly(blocks, assembly_config, block_config):
    
    # assemble a tube
    assembly, offset = create_tube(blocks['block'], assembly_config['n_layers'])

    # assemble frame: bottom and top
    frame_bottom, offset = create_frame_bottom(
        blocks['frame_block_bottom'],
        assembly_config['n_layers'],
        offset=offset
    )
    
    frame_top, offset = create_frame_top(
        blocks['frame_block_top'],
        assembly_config['n_layers'],
        offset=offset
    )
    
    together = assembly + frame_bottom + frame_top 

    assembly_all = {
        'assembly': assembly,
        'frame_bottom': frame_bottom,
        'frame_top': frame_top,
        'assembly_frame_top': assembly + frame_top,
        'together': together
    }
    
    return assembly_all


########################################################################
# Assemblies
########################################################################

def create_tube(block, n_block_layer ):

    assembly = []
    offset = {
        'ID': 0,
        'nodes': 0,
        'cells': 0,
        'cells_2D': 0,
    }
    for i in range(n_block_layer):

        if i % 2 == 0:
        
            for j in range(block['n']):

                k = j
                bl = init_block(block, i, j, k, offset)
                assembly.append(bl)

                offset['nodes'] += bl.n_nodes
                offset['cells'] += bl.n_cells
                offset['cells_2D'] += bl.n_cells_2D
                
        else:

            for j in range(block['n']):

                k = j+0.5
                bl = init_block(block, i, j, k, offset)
                assembly.append(bl)

                offset['nodes'] += bl.n_nodes
                offset['cells'] += bl.n_cells
                offset['cells_2D'] += bl.n_cells_2D

        offset['ID'] += block['n']
        
    return assembly, offset


def create_frame_top(frame_block, n_block_layer, offset=None):

    '''the frame is created after the assembly - important for the offset (numbering of nodes)'''

    assembly_frame = []
    
    if offset is None:
        offset = {
            'nodes': 0,
            'cells': 0,
            'cells_2D': 0,
            'ID': 0,
        }
        
    else:
        # # how many blocs are in the assembly
        # offset['ID'] = n_block_layer * frame_block['n']
        pass
    
    # top ring #########################################
    
    if n_block_layer % 2 == 0:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            ux = 1.5*frame_block['ro'] * n_block_layer #+ frame_block['ro']
            k = j
            
            bl = init_frame_block(frame_block, ID, ux, k, offset)
            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D
            
    else:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            ux = 1.5*frame_block['ro'] * n_block_layer #+ frame_block['ro']
            k = j + 0.5
            
            bl = init_frame_block(frame_block, ID, ux, k, offset)
            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D
            
    offset['ID'] += frame_block['n']

    return assembly_frame, offset


def create_frame_bottom(frame_block, n_block_layer, offset=None):

    assembly_frame = []
    
    if offset is None:
        offset = {
            'nodes': 0,
            'cells': 0,
            'cells_2D': 0,
            'ID': 0,
        }
        
    else:
        # # how many blocs are in the assembly
        # offset['ID'] = n_block_layer * frame_block['n']
        pass
    
    # mirror the block
    frame_block['all_points'][:,0] = - frame_block['all_points'][:,0]

    # invert the numeration in the cells
    cells_new = []
    for cell in frame_block['cells']['3D']:
        cell_new = [cell[0]] + cell[5:9] + cell[1:5]
        cells_new.append(cell_new)
    frame_block['cells']['3D'] = cells_new

    # Reflection matrix
    Mx, M6_x = get_M_and_M6(plane='yz')

    for j in range(frame_block['n']):

        ID = offset['ID'] + j
        ux = - 1.5*frame_block['ro']
        k = j + 0.5

        bl = init_frame_block(frame_block, ID, 0., k, offset)

        #bl.nodes = bl.nodes @ Rz.T
        bl.surface_nodes = bl.surface_nodes @ Mx.T
        bl.face_centers = bl.face_centers @ Mx.T
        bl.unit_forces = bl.unit_forces @ Mx.T
        bl.face_normals = bl.face_normals @ Mx.T
        bl.lever_vectors = bl.lever_vectors @ Mx.T
        bl.unit_momentum = bl.unit_momentum @ Mx.T
        bl.A_b = M6_x @ bl.A_b
        bl.p_b = M6_x @ bl.p_b

        trans = np.array([ux, 0., 0.])
        bl.nodes = bl.nodes + trans
        bl.surface_nodes = bl.surface_nodes + trans
        bl.face_centers = bl.face_centers + trans

        assembly_frame.append(bl)
        
        offset['nodes'] += bl.n_nodes
        offset['cells'] += bl.n_cells
        offset['cells_2D'] += bl.n_cells_2D

        
    offset['ID'] += frame_block['n']
    
                
    return assembly_frame, offset



def create_frame(frame_block, n_block_layer, offset=None):

    '''the frame is created after the assembly - important for the offset (numbering of nodes)'''

    assembly_frame = []
    
    if offset is None:
        offset = {
            'nodes': 0,
            'cells': 0,
            'cells_2D': 0,
            'ID': 0,
        }
        
    else:
        # # how many blocs are in the assembly
        # offset['ID'] = n_block_layer * frame_block['n']
        pass
    
    # top ring #########################################
    
    if n_block_layer % 2 == 0:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            ux = 1.5*frame_block['ro'] * n_block_layer #+ frame_block['ro']
            k = j
            
            bl = init_frame_block(frame_block, ID, ux, k, offset)
            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D
            
    else:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            ux = 1.5*frame_block['ro'] * n_block_layer #+ frame_block['ro']
            k = j + 0.5
            
            bl = init_frame_block(frame_block, ID, ux, k, offset)
            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D
            
    offset['ID'] += frame_block['n']

    # mirror the block
    frame_block['all_points'][:,0] = - frame_block['all_points'][:,0]

    # invert the numeration in the cells
    cells_new = []
    for cell in frame_block['cells']:
        cell_new = [cell[0]] + cell[5:9] + cell[1:5]
        cells_new.append(cell_new)
    frame_block['cells'] = cells_new
    
    # bottom ring ######################################
    for j in range(frame_block['n']):

        ID = offset['ID'] + j
        ux = - 1.5*frame_block['ro']
        k = j + 0.5

        bl = init_frame_block(frame_block, ID, ux, k, offset)
        assembly_frame.append(bl)
        
        offset['nodes'] += bl.n_nodes
        offset['cells'] += bl.n_cells
        offset['cells_2D'] += bl.n_cells_2D
        
    offset['ID'] += frame_block['n']
    
                
    return assembly_frame, offset

#############################################################################
def init_block(block, i, j, k, offset):

    '''Initializes the block object and sets the global node ids'''
    
    bl = Block(
        ID=i*block['n']+j,
        data=block,
        trans=np.array([i*3./2.*block['ro'], 0., block['r0']+block['t']/2.]),
        rot_angle=k*block['alpha'],
        axis=0
    )
    
    # Set offset of the block ids
    bl.offset['nodes'] += offset['nodes']
    bl.offset['cells'] += offset['cells']
    bl.offset['cells_2D'] += offset['cells_2D']
    
    # set global ids of the nodes
    bl.cells_glob = [[(node_id+1) + offset['nodes'] for node_id in nodes[1 : ]] \
                     for nodes in bl.cells]

    bl.get_surface_cell_ids_hexagon()
    
    return bl


def init_frame_block(frame_block, ID, ux, k, offset):

    '''Initializes the block object and sets the global node ids'''
    
    bl = Block(
        ID=ID,
        data=frame_block,
        trans=np.array([ux, 0., frame_block['r0'] + frame_block['t']/2.]),
        rot_angle=k*frame_block['alpha'],
        axis=0
    )
    
    # Set offset of the block ids
    bl.offset['nodes'] += offset['nodes']
    bl.offset['cells'] += offset['cells']
    bl.offset['cells_2D'] += offset['cells_2D']
    
    # set global ids of the nodes
    bl.cells_glob = [[(node_id+1) + offset['nodes'] for node_id in nodes[1 : ]] \
                     for nodes in bl.cells]

    bl.get_surface_cell_ids_hexagon()
    
    return bl

