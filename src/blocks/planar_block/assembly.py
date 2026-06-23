import numpy as np
from scipy.spatial import Delaunay
import pyvista as pv
import matplotlib.pyplot as plt

from src.engine.plots import *
from src.blocks.planar_block.meshing_mbd import *


# Square centerd around (0,0) with edge length Sqrt(2) and rotated by 45 degrees

def get_assembly(blocks, assembly_config, block_config):
    n = assembly_config['n']
    m = assembly_config['m']
    group = assembly_config['group']

    if group == 'p1':
        assembly, offset = create_p1(blocks['block'], n, m)
    elif group == 'pg':
        assembly, offset = create_pg(blocks['block'], n, m)
    elif group == 'p4':
        assembly, offset = create_p4(blocks['block'], n, m)

    together = assembly 

    # To Do Frame
    assembly_all = {
        'assembly': assembly,
        'frame': [],
        'frame_bottom': [],
        'frame_top': [],
        'together': together
    }
   
    return assembly_all


########################################################################
# Assemblies
########################################################################

def create_p1(block, nx, ny ):

    assembly = []
    offset = {
        'id': 0,
        'nodes': 0,
        'cells': 0,
    }

    ij = create_grid(nx, ny)
    
    for pos in ij:
        
        bl = init_block(block, offset, pos, alpha=0.)
        assembly.append(bl)

        offset['id'] += 1
        offset['nodes'] += bl.n_nodes
        offset['cells'] += bl.n_cells

    return assembly, offset


def create_pg(block, nx, ny ):

    assembly = []
    offset = {
        'id': 0,
        'nodes': 0,
        'cells': 0,
    }

    grid = np.zeros((nx, ny, 2))

    # Define rotation matrix for 45 degrees (π/4 radians)
    theta = np.pi / 4
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta),  np.cos(theta)]])

    # Example: fill with coordinates (x, y, z)
    for r in range(ny):
        for c in range(nx):
            point = np.array([np.sqrt(2)*c, np.sqrt(2)*r])
            rotated_point = R @ point
            grid[c, r] = rotated_point

    for r in range(ny):
        for c in range(nx):
            if c % 2:  # every second column (odd indices)
                alpha = 3*np.pi/2.
            else:
                alpha = np.pi
            
            bl = init_block(block, offset, grid[c,r], alpha)
            assembly.append(bl)

            offset['id'] += 1
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells

    return assembly, offset


def create_p4(block, nx, ny ):

    assembly = []
    offset = {
        'id': 0,
        'nodes': 0,
        'cells': 0,
    }

    grid = np.zeros((nx, ny, 2))

    # Define rotation matrix for 45 degrees (π/4 radians)
    theta = np.pi / 4
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta),  np.cos(theta)]])

    # Example: fill with coordinates (x, y, z)
    for r in range(ny):
        for c in range(nx):
            point = np.array([np.sqrt(2)*c, np.sqrt(2)*r])
            rotated_point = R @ point
            grid[c, r] = rotated_point

    for r in range(ny):
        for c in range(nx):
            if c % 2:  # every second column (odd indices)
                
                if r % 2:
                    alpha = np.pi/2.
                else:
                    alpha = np.pi
                
            else:

                if r % 2:
                    alpha = 0.
                else:
                    alpha = -np.pi/2.
                
            
            bl = init_block(block, offset, grid[c,r], alpha)
            assembly.append(bl)

            bl.face_centers = bl.face_centers

            offset['id'] += 1
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells

    return assembly, offset


def create_grid(nx, ny):

    # Create a grid of points
    x = np.linspace(0, np.sqrt(2)*(nx-1), nx)  # 11 points from -5 to 5
    y = np.linspace(0, np.sqrt(2)*(ny-1), ny)
    xx, yy = np.meshgrid(x, y)

    # Flatten into coordinate pairs
    points = np.vstack([xx.ravel(), yy.ravel()])

    # Define rotation matrix for 45 degrees (π/4 radians)
    theta = np.pi / 4
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta),  np.cos(theta)]])

    # Rotate all points
    rotated_points = R @ points # (2,nx*ny)
    

    return rotated_points.T


########################################################################
# Blocks class
########################################################################


class Block():

    def __init__(self, ID, data, trans, rot_angle):

        self.ID = ID
        self.data = data
        
        # rotation matrix
        Rz = np.array([
            [np.cos(rot_angle), -np.sin(rot_angle), 0],
            [np.sin(rot_angle),  np.cos(rot_angle), 0],
            [0,              0,             1]
        ])
        # 6x6 block diagonal
        R6 = np.block([
            [Rz, np.zeros((3,3))],
            [np.zeros((3,3)), Rz]
        ])
        
        nodes = data['all_points'] @ Rz.T
        face_centers = data['face_centers'] @ Rz.T

        if abs(rot_angle) > 0.:
            self.unit_forces = data['unit_forces'] @ Rz.T
            self.face_normals = data['face_normals'] @ Rz.T
            self.unit_momentum = data['unit_momentum'] @ Rz.T
            self.A_b = R6 @ data['A_b']
            self.p_b = R6 @ data['p_b']

        else:
            self.face_normals = data['face_normals']
            self.unit_forces = data['unit_forces']
            self.unit_momentum = data['unit_momentum']
            self.A_b = data['A_b']
            self.p_b = data['p_b']

        # translation
        nodes = nodes + trans
        face_centers = face_centers + trans
                
        self.nodes = nodes
        self.surface_nodes = nodes
        self.face_centers = face_centers
        
        self.cells_2D = data['cells']['3D']
        self.cells_2D_arr = data['cells_arr']['3D']

        self.cells_glob = None
        
        self.n_nodes = len(self.nodes)
        self.n_cells = len(self.cells_2D)

        self.offset = {
            'nodes': 0,
            'cells': 0,
        }

        self.surfaces = {}

        self.contact_partners = {}

        self.solutions = {}
        
        return

    
def init_block(data, offset, pos, alpha):
    '''Initializes the block object and sets the global node ids'''
    
    bl = Block(
        offset['id'],
        data,
        np.concatenate([pos, [0]]),
        alpha, # rot_angle
    )
    
    # Set offset of the block ids
    bl.offset['nodes'] += offset['nodes']
    bl.offset['cells'] += offset['cells']

    # set global ids of the nodes
    bl.cells_glob = [[(node_id+1) + offset['nodes'] for node_id in nodes[1 : ]] \
                     for nodes in bl.cells_2D]
    
    return bl