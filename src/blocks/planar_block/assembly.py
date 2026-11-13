import numpy as np
from scipy.spatial import Delaunay
import pyvista as pv
import matplotlib.pyplot as plt

from src.engine.plots import *
from src.blocks.planar_block.meshing_mbd import *


# Square centered around (0,0) with edge length Sqrt(2) and rotated by 45 degrees

# Rotation of the whole assembly about the z-axis, so that p1, pg and p4 have the
# same orientation as in Goertzen et al. (2025), IJSS 306, 113102 (Figs. 6-8, 12, 13):
# determined from the load transfer onto the frame (which frame edges and which
# frame blocks carry load). A rotation does not change the mechanics of the
# assembly, only its position in the coordinate system.
GROUP_ROTATION = {'p1': np.pi / 2, 'pg': np.pi, 'p4': 0.}
# start angle of the p4 arrangement (see create_p4); 0 or pi give valid assemblies
P4_START_ANGLE = np.pi   # loaded frame blocks as in the Interlocking Flows (Fig. 6)


def rotate_placement(pos, alpha, phi):
    '''position and rotation angle of a block after rotating the assembly by phi'''
    R = np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])
    return R @ np.asarray(pos, dtype=float), alpha + phi

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
        assembly, offset = create_octahedron_assembly(blocks['block'], n, m)
    elif group == 'p6':
        assembly, offset = create_p6(blocks['block'], n)
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
        
        pos, alpha = rotate_placement(pos, 0., GROUP_ROTATION['p1'])
        bl = init_block(block, offset, pos, alpha)
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
            
            pos, alpha = rotate_placement(grid[c, r], alpha, GROUP_ROTATION['pg'])
            bl = init_block(block, offset, pos, alpha)
            assembly.append(bl)

            offset['id'] += 1
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells

    return assembly, offset


def create_p4(block, nx, ny, a0=None):
    '''
    p4 arrangement: the four blocks around a 4-fold rotation centre are rotated
    by a0, a0 + 90°, a0 + 180°, a0 + 270° in counterclockwise order (as their
    positions). With an even number of blocks the centre of the assembly is a
    4-fold centre, as in Goertzen et al. (2025), Figs. 6 and 12 ("X" of long
    joints through the centre).

    Before (until 2026-11-12) the angles were assigned in clockwise order
    (-90° per step): the arrangement tiled the plane, but was only 2-fold
    symmetric about the centre of the assembly.
    '''
    if a0 is None:
        a0 = P4_START_ANGLE

    assembly = []
    offset = {
        'id': 0,
        'nodes': 0,
        'cells': 0,
    }

    # Define rotation matrix for 45 degrees (π/4 radians)
    theta = np.pi / 4
    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta),  np.cos(theta)]])

    # position in the 2x2 cell -> number of quarter turns (counterclockwise)
    quarter_turns = {(0, 0): 0, (1, 0): 1, (1, 1): 2, (0, 1): 3}

    for r in range(ny):
        for c in range(nx):
            pos = R @ np.array([np.sqrt(2)*c, np.sqrt(2)*r])
            alpha = a0 + quarter_turns[(c % 2, r % 2)] * np.pi / 2.
            pos, alpha = rotate_placement(pos, alpha, GROUP_ROTATION['p4'])
            bl = init_block(block, offset, pos, alpha)
            assembly.append(bl)

            offset['id'] += 1
            offset['nodes'] += bl.n_nodes
            offset['cells'] += bl.n_cells

    return assembly, offset


def create_p6(block, n, a=None):
    '''
    p6 arrangement of the starfish block: hexagon of side n (in triangle edge
    lengths) of 6 n^2 blocks, centred at a 6-fold rotation centre (origin).

    The reference block has its 6-fold vertex at the origin. Around every
    6-fold centre c of the lattice (spacing a sqrt(3)) six blocks are placed,
    rotated by k * 60 deg about c. With support='implicit' (as for the
    versatile block) n = 2 gives the assembly of Schnelle et al. (2026): the 24
    inner blocks, the outer faces act as the rigid frame. This is identical to
    n = 3 with support='frame' and frame_blocks='perimeter' (30 fixed frame
    blocks as in the paper).
    '''
    from src.blocks.planar_block.geometry import STARFISH_EDGE
    if a is None:
        a = STARFISH_EDGE

    u = np.array([1.5 * a, np.sqrt(3.) / 2. * a])
    v = np.array([0., np.sqrt(3.) * a])
    # centroid of the reference triangle relative to its 6-fold vertex
    g0 = np.array([a / 2., a * np.sqrt(3.) / 6.])
    # inside the hexagon with corners n a (cos k 60, sin k 60): apothem n a sqrt(3)/2
    normals = [np.array([np.cos(t), np.sin(t)]) for t in (np.pi / 6, np.pi / 2, 5 * np.pi / 6)]
    apothem = n * a * np.sqrt(3.) / 2.

    placements = []
    for i in range(-2 * n - 1, 2 * n + 2):
        for j in range(-2 * n - 1, 2 * n + 2):
            c = i * u + j * v
            for k in range(6):
                alpha = k * np.pi / 3.
                R = np.array([[np.cos(alpha), -np.sin(alpha)], [np.sin(alpha), np.cos(alpha)]])
                g = c + R @ g0
                if all(abs(g @ w) < apothem for w in normals):
                    placements.append((np.linalg.norm(g), np.arctan2(g[1], g[0]) % (2 * np.pi), c, alpha))

    # numbering from the centre outwards
    placements.sort(key=lambda t: (round(t[0], 9), round(t[1], 9)))

    assembly = []
    offset = {'id': 0, 'nodes': 0, 'cells': 0}
    for _, _, c, alpha in placements:
        bl = init_block(block, offset, c, alpha)
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

def create_octahedron_assembly(block, n, m, edge_length=None):
    '''
    Layer of (cut) octahedra, all with the same orientation (translations
    only), as octahedron_interlocking of the original script: m rows in x,
    n blocks per row in y, every second row shifted by half a block.

    The lattice is determined by the edge length of the full octahedron (the
    cut and the scaling in z do not change the x-y geometry). The gap of the
    original script (1e-5) is left out: the contacts are detected exactly.
    The frame of the original script (first/last row and column) is the
    frame of support='frame' with frame_blocks='boundary'.
    '''
    from src.blocks.planar_block.geometry import octahedron_edge_length
    if edge_length is None:
        edge_length = octahedron_edge_length()
    h = np.sqrt(3) / 2 * edge_length

    assembly = []
    offset = {'id': 0, 'nodes': 0, 'cells': 0}

    for i in range(m):        # rows
        for j in range(n):    # columns
            x_translation = i * 1.5 * edge_length / 2
            y_translation = j * h
            if i % 2 != 0:
                y_translation -= h / 2

            bl = init_block(block, offset, np.array([x_translation, y_translation]), 0.0)
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
        self.centroid = np.asarray(data['centroid']) @ Rz.T + trans
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