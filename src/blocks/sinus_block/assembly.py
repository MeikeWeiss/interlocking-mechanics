"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: ?

Contributors:
- Reymond Akpanya, The School of Mathematics and Statistics, The University of Sydney
- Meike Weiß, RWTH Aachen University, Chair of Algebra and Representation Theory

License: MIT

Reference:
"""


import numpy as np

from src.blocks.sinus_block.block_class import Block
from src.engine.util import get_R_and_R6


def get_assembly(blocks, assembly_config, block_config):
    
    # assemble a tube
    assembly, offset = create_tube(blocks['block'], assembly_config['n_layers'])

    # assemble frame: bottom and top
    frame_bottom, offset = create_frame_bottom(
        blocks['frame_block_bottom'],
        assembly_config['n_layers'],
        h_block=block_config['h'],
        offset=offset
    )
    
    frame_top, offset = create_frame_top(
        blocks['frame_block_top'],
        assembly_config['n_layers'],
        h_block=block_config['h'],
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
                f = block['frequency']
                k = j + 0.5 + 0.5*(1- 1/f)
                bl = init_block(block, i, j, k, offset)
                assembly.append(bl)

                offset['nodes'] += bl.n_nodes
                offset['cells'] += bl.n_cells
                offset['cells_2D'] += bl.n_cells_2D

        offset['ID'] += block['n']
  
    return assembly, offset


def create_tube_alternating(block, n_block_layer ):

    assembly = []
    offset = {
        'ID': 0,
        'nodes': 0,
        'cells': 0,
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
            # every second row has missing blocks

            l = i//2 
            if l % 2 == 0:
                x = 0
            else:
                x = 2
            
            for j in range(np.ceil(block['n'] * 0.75).astype(int)):

                #k = j + i*0.5
                k = 0.5 + j + x
                bl = init_block(block, i, j, k, offset)
                assembly.append(bl)

                offset['nodes'] += bl.n_nodes
                offset['cells'] += bl.n_cells
                offset['cells_2D'] += bl.n_cells_2D

        offset['ID'] += block['n']
        
    return assembly, offset


def create_frame(frame_block, n_block_layer, h_block, offset=None):

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
    
    shift_frame = frame_block['shift']
    
    # bottom ring ######################################
    for j in range(frame_block['n']):

        ID = offset['ID'] + j
        uz = - frame_block['h']
        k = j + shift_frame

        bl = init_frame_block(
            frame_block,
            ID,
            uz,
            k,
            offset,
        )
        assembly_frame.append(bl)
        
        offset['nodes'] += bl.n_nodes
        offset['cells'] += bl.n_cells
        offset['cells_2D'] += bl.n_cells_2D
        
    offset['ID'] += frame_block['n']
    
    # top ring #########################################
    # mirror the block
    frame_block['all_points'][:,0] = - frame_block['all_points'][:,0]
    frame_block['all_points'][:,2] = - frame_block['all_points'][:,2]

    shift_frame = frame_block['shift']/2.
    
    if n_block_layer % 2 == 0:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            uz = h_block * n_block_layer + frame_block['h']
            k = j+shift_frame
            
            bl = init_frame_block(frame_block, ID, uz, k, offset)
            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D
            
    else:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            uz = h_block * n_block_layer  + frame_block['h']
            k = j + shift_frame
            
            bl = init_frame_block(frame_block, ID, uz, k, offset)
            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D

    offset['ID'] += frame_block['n']
    
    return assembly_frame, offset


def create_frame_bottom(frame_block, n_block_layer, h_block, offset=None):

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

    shift_frame = frame_block['shift'] / frame_block['frequency']
    
    # bottom ring ######################################
    for j in range(frame_block['n']):

        ID = offset['ID'] + j
        uz = - frame_block['h']
        k = j + shift_frame

        bl = init_frame_block(
            frame_block,
            ID,
            uz,
            k,
            offset,
        )
        assembly_frame.append(bl)
        
        offset['nodes'] += bl.n_nodes
        offset['cells'] += bl.n_cells
        offset['cells_2D'] += bl.n_cells_2D
        
    offset['ID'] += frame_block['n']

    return assembly_frame, offset


def create_frame_top(frame_block, n_block_layer, h_block, offset=None):

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

    shift_frame = frame_block['shift']/(frame_block['frequency'] * 2)

    # rotation matrix
    Rx, R6_x = get_R_and_R6(rot_angle=np.pi, axis=0)

    if n_block_layer % 2 == 0:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            #k = j+shift_frame
            f = frame_block['frequency']
            s = frame_block['shift']
            k = j + frame_block['n']/2  + (1/(2*f)) * s
                                    
            bl = init_frame_block(frame_block, ID, 0., k, offset)

            bl.nodes = bl.nodes @ Rx.T
            bl.surface_nodes = bl.surface_nodes @ Rx.T
            bl.face_centers = bl.face_centers @ Rx.T
            bl.unit_forces = bl.unit_forces @ Rx.T
            bl.face_normals = bl.face_normals @ Rx.T
            bl.lever_vectors = bl.lever_vectors @ Rx.T
            bl.unit_momentum = bl.unit_momentum @ Rx.T
            bl.A_b = R6_x @ bl.A_b
            bl.p_b = R6_x @ bl.p_b

            uz = h_block * n_block_layer + frame_block['h']
            trans = np.array([0., 0., uz])
            bl.nodes = bl.nodes + trans
            bl.surface_nodes = bl.surface_nodes + trans
            bl.face_centers = bl.face_centers + trans

            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D
            
    else:
        
        for j in range(frame_block['n']):

            ID = offset['ID'] + j
            #k = j + shift_frame
            f = frame_block['frequency']
            s = frame_block['shift']
            k = j + frame_block['n']/2  + (1/(2*f)) * s
            
            bl = init_frame_block(frame_block, ID, 0., k, offset)

            bl.nodes = bl.nodes @ Rx.T
            bl.surface_nodes = bl.surface_nodes @ Rx.T
            bl.face_centers = bl.face_centers @ Rx.T
            bl.unit_forces = bl.unit_forces @ Rx.T
            bl.face_normals = bl.face_normals @ Rx.T
            bl.lever_vectors = bl.lever_vectors @ Rx.T
            bl.unit_momentum = bl.unit_momentum @ Rx.T
            bl.A_b = R6_x @ bl.A_b
            bl.p_b = R6_x @ bl.p_b
            
            uz = h_block * n_block_layer + frame_block['h']
            trans = np.array([0., 0., uz])
            bl.nodes = bl.nodes + trans
            bl.surface_nodes = bl.surface_nodes + trans
            bl.face_centers = bl.face_centers + trans

            assembly_frame.append(bl)
        
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells
            offset['cells_2D'] += bl.n_cells_2D
            
    offset['ID'] += frame_block['n']
            
    return assembly_frame, offset

##############################################################################
def init_block(block, i, j, k, offset):
    '''Initializes the block object and sets the global node ids'''
    
    bl = Block(
        ID=i*block['n']+j,
        data=block,
        trans=np.array([0., block['ri'], i*block['h']]),
        rot_angle=k*block['alpha'],
        axis=2
    )
    
    # Set offset of the block ids
    bl.offset['nodes'] += offset['nodes']
    bl.offset['cells'] += offset['cells']
    bl.offset['cells_2D'] += offset['cells_2D']

    # set global ids of the nodes
    bl.cells_glob = [[(node_id+1) + offset['nodes'] for node_id in nodes[1 : ]] \
                     for nodes in bl.cells]

    bl.get_surface_cell_ids()
    
    return bl


def init_frame_block(frame_block, ID, uz, k, offset):
    '''Initializes the block object and sets the global node ids'''
    
    bl = Block(
        ID=ID,
        data=frame_block,
        trans=np.array([0., frame_block['ri'], uz]),
        rot_angle=k*frame_block['alpha'],
        axis=2
    )
    
    # Set offset of the block ids
    bl.offset['nodes'] += offset['nodes']
    bl.offset['cells'] += offset['cells']
    bl.offset['cells_2D'] += offset['cells_2D']

    # set global ids of the nodes
    bl.cells_glob = [[(node_id+1) + offset['nodes'] for node_id in nodes[1 : ]] \
                     for nodes in bl.cells]

    bl.get_surface_cell_ids()
    
    return bl
