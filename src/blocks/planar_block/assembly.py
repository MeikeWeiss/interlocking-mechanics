import numpy as np
from scipy.spatial import Delaunay
import pyvista as pv
import matplotlib.pyplot as plt

from src.engine.plots import *
from src.blocks.planar_block.meshing_mbd import *


# Square centered around (0,0) with edge length Sqrt(2) and rotated by 45 degrees

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
    elif group == 'p1_brick':
        assembly, offset = create_p1_brick(blocks['block'], n, m)
    elif group == 'octa':
        assembly, offset = create_octahedron_assembly(blocks['block'], n, m, block_config['h'])
    elif group == 'irr_octa':
        assembly, offset = create_irr_octahedron_assembly(blocks['block'], n, m, block_config['h'])
    else:
        raise ValueError(f"Unknown group: {group}")

    together = assembly 

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

            offset['id'] += 1
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells

    return assembly, offset

def create_p1_brick(block, nx, ny ):

    assembly = []
    offset = {
        'id': 0,
        'nodes': 0,
        'cells': 0,
    }

    center = [1,0.25]
    
    for i in range(nx):
        for j in range(ny):
            if j%2==0:
                trans_j = [2*i,0.5*j]
            else:
                trans_j = [2*i+1,0.5*j]
        
            bl = init_block(block, offset,[center[0] +trans_j[0],center[1] + trans_j[1]], alpha=0.)
            assembly.append(bl)

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

def create_irr_octahedron_assembly(block, n, m, h):
  
    edge_length = np.sqrt(4. / np.sqrt(3.)) *1/h # np.sqrt(4. / np.sqrt(3.)) *1/h, np.sqrt(3) / np.sqrt(2)  # regulär, für Höhe 1
    h = np.sqrt(3) / 2 * edge_length

    assembly = []
    offset = {'id': 0, 'nodes': 0, 'cells': 0}

    for i in range(m):        # Zeilen
        for j in range(n):    # Spalten

            x_translation = i * 1.5 * edge_length / 2
            y_translation = j * h
            if i % 2 != 0:
                y_translation -= h / 2

            position = np.array([x_translation, y_translation])  # nur 2D, wie in create_p4
            alpha = 0.0  # keine Rotation -- siehe Hinweis unten

            bl = init_block(block, offset, position, alpha)
            assembly.append(bl)

            offset['id'] += 1
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells

    return assembly, offset


def create_octahedron_assembly(block, n, m,h):
  
    edge_length = np.sqrt(3) / np.sqrt(2) # np.sqrt(4. / np.sqrt(3.)) *1/h, np.sqrt(3) / np.sqrt(2)  # regulär, für Höhe 1
    h = np.sqrt(3) / 2 * edge_length

    assembly = []
    offset = {'id': 0, 'nodes': 0, 'cells': 0}

    for i in range(m):        # Zeilen
        for j in range(n):    # Spalten

            x_translation = i * 1.5 * edge_length / 2
            y_translation = j * h
            if i % 2 != 0:
                y_translation -= h / 2

            position = np.array([x_translation, y_translation])  # nur 2D, wie in create_p4
            alpha = 0.0  # keine Rotation -- siehe Hinweis unten

            bl = init_block(block, offset, position, alpha)
            assembly.append(bl)

            offset['id'] += 1
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells

    return assembly, offset


########################################################################
# Blocks class
########################################################################


class Block():
    '''
    Placed copy of a reference block: rotated by rot_angle about the z-axis
    and translated by trans. All arrays are copies, so modifying one block
    does not affect the others. A_b and p_b are computed in the setup
    (src/blocks/planar_block/run_mbd_planar.py).
    '''

    def __init__(self, ID, data, trans, rot_angle):

        self.ID = ID
        self.data = data

        # rotation matrix about the z-axis
        Rz = np.array([
            [np.cos(rot_angle), -np.sin(rot_angle), 0],
            [np.sin(rot_angle),  np.cos(rot_angle), 0],
            [0,              0,             1]
        ])

        # rotation (vectors) and translation (points)
        self.nodes = data['all_points'] @ Rz.T + trans
        self.surface_nodes = self.nodes
        self.face_centers = data['face_centers'] @ Rz.T + trans
        self.face_normals = data['face_normals'] @ Rz.T
        self.unit_forces = data['unit_forces'] @ Rz.T
        self.unit_momentum = data['unit_momentum'] @ Rz.T
        self.face_areas = np.array(data['face_areas'], copy=True)

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
        alpha#, rot_angle
    )
    
    # Set offset of the block ids
    bl.offset['nodes'] += offset['nodes']
    bl.offset['cells'] += offset['cells']

    # set global ids of the nodes
    bl.cells_glob = [[(node_id+1) + offset['nodes'] for node_id in nodes[1 : ]] \
                     for nodes in bl.cells_2D]
    
    return bl