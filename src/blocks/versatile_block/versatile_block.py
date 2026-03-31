import numpy as np
from scipy.spatial import Delaunay
import pyvista as pv
import matplotlib.pyplot as plt

from src.engine.plots import *

########################################################################
# Vertices and cells
########################################################################

def create_vertices():

    points = [
        np.array([0., 0., 0.]),
        np.array([1., 1., 0.]),
        np.array([2., 0., 0.]),
        np.array([1, -1, 0]),
        np.array([0., 1., 1.]),
        np.array([1., 1., 1.]),
        np.array([1., 0., 1.]),
        np.array([1., -1., 1.]),
        np.array([0., -1., 1.]),
        np.array([0., 0., 1.]),
        
        np.array([0., -0.5, 0.5]),
        np.array([0., 0.5, 0.5]),
        np.array([1., -0.5, 0.5]),
        np.array([1., 0.5, 0.5]),
        np.array([0.5, -1., 0.5]),
        np.array([0.5, 1., 0.5]),
        np.array([0., 0., 0.5]),
        np.array([1.5, 0., 0.5]),
        
        np.array([1.5, 0.5, 0.]),
        np.array([1.5, -0.5, 0.]),
        np.array([0.5, -0.5, 0.]),
        np.array([0.5, 0.5, 0.]),
    ]
    
    return points

def create_tri3_cells():

    triangles = np.array([
        [0,1,2], # bottom
        [0,2,3], # bottom
        [4,6,5], # top
        #[4,8,6], # top
        [4,9,6], # top
        [9,8,6], # top
        [6,8,7], # top
        [3,12,7], # front       0
        [12,6,7], # front       0
        [1,5,13], # front       1
        [13,5,6], # front       1
        
        [1,13,18], # tip left    2
        [13,6,17], # tip left    2
        [13,17,18], # tip left    2
        [18,17,2], # tip left    2
        
        [2,17,19], # tip right   3
        [17,6,12], # tip right   3
        [12,19,17], # tip right   3
        [3,19,12], # tip right   3
        
        [1,15,5], # side left   4
        [15,4,5], # side left   4
        [3,7,14], # side right  5
        [14,7,8], # side right  5
        
        [0,9,11], # back left    6
        [11,9,4], # back left    6
        [0,10,9], # back right   7
        [10,8,9], # back right   7
        
        [0,11,21], # back bottom left   8
        [11,4,15], # back bottom left   8
        [15,21,11], # back bottom left   8
        [21,15,1], # back bottom left   8

        [0,20,10], # back bottom right  9
        [10,20,14], # back bottom right  9
        [20,3,14], # back bottom right  9
        [10,14,8], # back bottom right  9
    ])

    # Create cell array: [3, p0, p1, p2, 3, p0, p1, p2, ...]
    cells = np.hstack([[3, *triangle] for triangle in triangles]).astype(np.int64)
    
    return triangles, cells


# def create_tri3_cells():

#     triangles = np.array([
#         [0,1,2], # bottom
#         [0,2,3], # bottom
#         [4,6,5], # top
#         #[4,8,6], # top
#         [4,9,6], # top
#         [9,8,6], # top
#         [6,8,7], # top
#         [3,6,7], # front       0
#         [1,5,6], # front       1
#         [1,6,2], # tip left    2
#         [2,6,3], # tip right   3
#         [1,4,5], # side left   4
#         [3,7,8], # side right  5
#         #[0,8,4], # back        6
#         [0,9,4], # back left    6
#         [0,8,9], # back right   7
#         [0,1,4], # back bottom left   8
#         [0,3,8], # back bottom right  9
#     ])

#     # Create cell array: [3, p0, p1, p2, 3, p0, p1, p2, ...]
#     cells = np.hstack([[3, *triangle] for triangle in triangles]).astype(np.int64)
    
#     return triangles, cells


def create_tet4_cells():

    tets = np.array([
        [4,5,6,1], # top left
        [6,7,8,3], # top right
        #[4,6,8,0], # middle
        [4,6,9,0], # middle left
        [9,6,8,0], # middle right
        [1,0,2,6], # bottom left
        [0,3,2,6], # bottom right
        [0,1,4,6], # side left
        [3,0,8,6], # side right
    ])

    # Create cell array: [4, p0, p1, p2, p3, 4, p0, p1, p2, p3,...]
    cells = np.hstack([[4, *tet4] for tet4 in tets]).astype(np.int64)
    
    return tets, cells


########################################################################
# Block
########################################################################

def create_block(
        scale,
        frame, # True, False: frame block
        cell_types, # {'2D': 'quad4', '3D': 'hex8'}
):

    # vertices of a versatile block
    points = create_vertices()
    all_points_arr = np.array(points)
    
    #plot_point_cloud(points)    
    
    # Create 2D cells
    triangles, tri3_cells = create_tri3_cells()

    # create 3D cells
    tet4, tet4_arr = create_tet4_cells()

    # Compute center of volume
    mesh = pv.PolyData(points, tri3_cells)
    centroid = mesh.center_of_mass()

    # Compute per-face (cell) normals
    normals_mesh = mesh.compute_normals(cell_normals=True, point_normals=False)
    face_normals = normals_mesh.cell_data["Normals"]
    unit_forces = -face_normals

    # Compute face centers
    face_centers = mesh.cell_centers().points

    # lever vectors projected perpendicular to normal
    lever_vectors = []
    for p, n in zip(face_centers, face_normals):
        r = p - centroid
        r_perp = r - np.dot(r, n) * n   # remove component along normal
        lever_vectors.append(r_perp)

    lever_vectors = np.array(lever_vectors)

    # cross product r x n: (n,3) x (n,3)
    unit_momentum = np.cross(lever_vectors, -unit_forces)

    # block array
    A_b = np.hstack([unit_forces[6:,:], unit_momentum[6:,:]]).T

    # right side: sum the normals of the top plane and multiply with a scalar f
    f = 1.
    F_b = f * np.sum(unit_forces[2:6,:], axis=0)
    M_b = f * np.sum(unit_momentum[2:6,:], axis=0)
    p_b = - np.hstack([F_b, M_b])

    output = {
        'all_points': all_points_arr,        
        'cells': {'2D': triangles, '3D': tet4}, 'cells_arr': {'2D': tri3_cells, '3D': tet4_arr},
        'centroid': centroid,
        'face_normals': face_normals, 'face_centers': face_centers,
        'unit_forces': unit_forces, 'lever_vectors': lever_vectors,
        'unit_momentum': unit_momentum,
        'A_b': A_b, 'p_b': p_b,
    }

    return output




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
        #surface_nodes = data['surface'].points @ Rz.T
        face_centers = data['face_centers'] @ Rz.T

        # if abs(rot_angle) > 0.:
        #     data['face_normals'] = data['face_normals'] @ Rz.T
        #     data['unit_forces'] = data['unit_forces'] @ Rz.T
        #     data['unit_momentum'] = data['unit_momentum'] @ Rz.T
        #     data['A_b'] = R6 @ data['A_b']
        #     data['p_b'] = R6 @ data['p_b']

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
        # nodes = nodes + Rz @ trans
        # face_centers = face_centers + Rz @ trans
        nodes = nodes + trans
        face_centers = face_centers + trans
                
        self.nodes = nodes
        self.surface_nodes = nodes
        self.face_centers = face_centers
        
        self.cells_2D = data['cells']['2D']
        self.cells_2D_arr = data['cells_arr']['2D']
        
        self.cells = data['cells']['3D']
        self.cells_arr = data['cells_arr']['3D']

        self.cells_glob = None
        
        self.n_nodes = len(self.nodes)
        self.n_cells = len(self.cells)

        self.offset = {
            'nodes': 0,
            'cells': 0,
        }

        self.surfaces = {}

        self.contact_partners = {}
        
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
                     for nodes in bl.cells]
    
    return bl


########################################################################
# Faces (surface)
########################################################################

def group_faces(block):

    all_faces = np.arange(len(block['cells']['2D']))
    
    #################################################
    # only contact faces
    ################################################
    contact_faces = all_faces[6:]

    #################################################
    # f_ext faces
    ################################################
    top_faces = all_faces[2:6]
    bottom_faces = all_faces[:2]
    
    face_groups = {
        'all_faces': all_faces,
        'contact_faces': contact_faces,
        'top_faces': top_faces,
        'bottom_faces': bottom_faces,
    }
    
    block['face_groups'] = face_groups
    
    return block



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
                alpha = np.pi/2.
                trans_pg = np.array([1.,-1.])
            else:
                alpha = 0.
                trans_pg = np.array([0.,0.])
            
            bl = init_block(block, offset, grid[c,r]+trans_pg, alpha)
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
                    trans_pg = np.array([1.,-1.])
                else:
                    alpha = np.pi
                    trans_pg = np.array([2.,0.])
                
            else:

                if r % 2:
                    alpha = 0.
                    trans_pg = np.array([0.,0.])
                else:
                    alpha = -np.pi/2.
                    trans_pg = np.array([1.,1.])
                
            
            bl = init_block(block, offset, grid[c,r]+trans_pg, alpha)
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
    
    # # Plot to visualize
    # plt.scatter(points[0], points[1], color='blue', label="Original grid")
    # plt.scatter(rotated_points[0], rotated_points[1], color='red', label="Rotated grid")
    # plt.axis("equal")
    # plt.legend()
    # plt.show()

    return rotated_points.T
