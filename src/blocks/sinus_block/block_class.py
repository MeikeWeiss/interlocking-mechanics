"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-08-30
Last Modified: ?

License: MIT

Reference:
"""

import numpy as np

from src.engine.util import get_R_and_R6


########################################################################
# Blocks class
########################################################################

class Block():

    def __init__(self, ID, data, trans, rot_angle, axis):

        self.ID = ID

        self.n_l = data['n_l']
        self.n_t = data['n_t']
        if 'n_h' in data:
            self.n_h = data['n_h']
            
        self.data = data

        # rotation matrix
        R, R6 = get_R_and_R6(rot_angle, axis)
        
        nodes = data['all_points'] @ R.T
        surface_nodes = data['surface'].points @ R.T
        face_centers = data['face_centers'] @ R.T

        if abs(rot_angle) > 0.:
            self.unit_forces = data['unit_forces'] @ R.T
            self.face_normals = data['face_normals'] @ R.T
            self.lever_vectors = data['lever_vectors'] @ R.T
            self.unit_momentum = data['unit_momentum'] @ R.T
            self.A_b = R6 @ data['A_b']
            self.p_b = R6 @ data['p_b']

        else:
            self.face_normals = data['face_normals']
            self.lever_vectors = data['lever_vectors']
            self.unit_forces = data['unit_forces']
            self.unit_momentum = data['unit_momentum']
            self.A_b = data['A_b']
            self.p_b = data['p_b']

        # translation
        nodes = nodes + R @ trans
        surface_nodes = surface_nodes + R @ trans
        face_centers = face_centers + R @ trans
                
        self.nodes = nodes
        self.surface_nodes = surface_nodes
        self.face_centers = face_centers
        
        # face groups and areas of the reference block (same for all copies);
        # accessed by the MBD engine as attributes, like for planar blocks
        self.face_groups = data.get('face_groups')
        self.face_areas = data.get('face_areas')

        self.cells_2D = data['cells']['2D']
        self.cells_2D_arr = data['surface'].faces
        
        self.cells = data['cells']['3D']
        self.cells_arr = data['cells_arr']['3D']

        self.cells_glob = None
        
        self.n_nodes = len(self.nodes)
        self.n_cells = len(self.cells)
        self.n_cells_2D = data['surface'].n_cells

        self.offset = {
            'nodes': 0,
            'cells': 0,
            'cells_2D': 0,
        }

        self.surfaces = {}

        self.contact_partners = {}

        self.solutions = {}
        
        return

    
    def get_surface_cell_ids(self):

        '''computes the IDs of the cells adjacent to the surfaces of the block'''
        
        all_ids = np.arange(self.n_cells) + self.offset['cells']

        surfaces = {
            0: [], # bottom surfaces 1 and 2
            4: [], # inner surface 1
            5: [], # inner surface 2
            7: [], # outer surface 1
            8: [] # outer surface 2
        }

        # bottom elements
        surfaces[0].extend(all_ids[0 : 2*self.n_l*self.n_t])
        
        # inner and outer elements
        for i_dh in range(self.n_h):
            i0 = i_dh*(2*self.n_l*self.n_t)
            i1 = (i_dh+1)*(2*self.n_l*self.n_t)-2*self.n_l
            surfaces[4].extend(all_ids[i0 : i0+self.n_l]) 
            surfaces[5].extend(all_ids[i0+self.n_l : i0+2*self.n_l])
            surfaces[7].extend(all_ids[i1 : i1+self.n_l]) 
            surfaces[8].extend(all_ids[i1+self.n_l : i1+2*self.n_l])
            
        self.surfaces = surfaces
        
        return

    
    def get_surface_cell_ids_hexagon(self):

        '''computes the IDs of the cells adjacent to the surfaces of the block'''
        
        all_ids = np.arange(self.n_cells) + self.offset['cells']

        surfaces = {
            4: [],
            5: [],
        }
        
        n_layers = self.n_t*2
        n_cells_layer = self.n_cells//n_layers
        
        surfaces[4].extend(all_ids[0 : n_cells_layer])

        i0 = (n_layers-1)*n_cells_layer
        surfaces[5].extend(all_ids[i0 : i0+n_cells_layer])
            
        self.surfaces = surfaces
        
        return    
