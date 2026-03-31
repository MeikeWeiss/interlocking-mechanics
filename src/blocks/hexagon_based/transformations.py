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
from scipy.spatial import Delaunay

########################################################################
# Transformations
########################################################################

def transform_rectangle_to_hexagon(points, ro, ri):

    for i in points:

        a = i[1]/(ro/2.)
        if i[0] >= 0:
            b = -(ro/2.)/ri
        elif i[0] < 0:
            b = (ro/2.)/ri
        uy = a*(b*i[0] + ro/2.)

        i[1] += uy
    
    return


def find_points_inside(points, region):
    
    region_hull = Delaunay(region)
    
    node_ids = np.arange(len(points))
    
    # Find nodes inside the region using Delaunay
    inside_mask = region_hull.find_simplex(points) >= 0
    inside_node_ids = node_ids[inside_mask]

    return inside_node_ids


# def transform_edge(points, ro, ri, direction):

#     tol = 5e-3
#     region = np.array([[+ro*1/2, +tol, +3*tol],
#                        [-ro*1/2, +tol, +3*tol],
#                        [ro*np.sin(np.pi/6.)-tol, ro*np.cos(np.pi/6.)+tol, +3*tol],
#                        [-ro*np.sin(np.pi/6.)+tol, ro*np.cos(np.pi/6.)+tol, +3*tol],
#                        [+ro*1/2, +tol, -3*tol],
#                        [-ro*1/2, +tol, -3*tol],
#                        [ro*np.sin(np.pi/6.)-tol, ro*np.cos(np.pi/6.)+tol, -3*tol],
#                        [-ro*np.sin(np.pi/6.)+tol, ro*np.cos(np.pi/6.)+tol, -3*tol],])

#     inside_node_ids = find_points_inside(points, region)

#     for i_id in inside_node_ids:

#         i = points[i_id]
#         a = i[1]/ri # linear change in the direction of ri (inner radius of the hexagon)
#         dh = np.sqrt(ro**2 - i[0]**2) - ri
        
#         uy = a*dh
        
#         i[1] += uy * direction
        
#     return


# def transform_hexagon_edges(points, ro, ri):

#     # rotate for 90 deg (for easier transformation of edges)
#     R = rot_mat_z(np.pi/2)
#     rot_points(points, R)

#     # transform
#     for n in range(6):
        
#         if n % 2 == 0:
#             transform_edge(points, ro, ri, -1.)
        
#         else:
#             transform_edge(points, ro, ri, +1.)

#         R = rot_mat_z(np.pi/3)
#         rot_points(points, R)

#     return


def transform_edge(points, ro, ri, h2, direction):

    tol = 5e-3
    region = np.array([[+ro*1/2, +tol, h2+3*tol],
                       [-ro*1/2, +tol, h2+3*tol],
                       [ro*np.sin(np.pi/6.)-tol, ro*np.cos(np.pi/6.)+tol, h2+3*tol],
                       [-ro*np.sin(np.pi/6.)+tol, ro*np.cos(np.pi/6.)+tol, h2+3*tol],
                       [+ro*1/2, +tol, -h2-3*tol],
                       [-ro*1/2, +tol, -h2-3*tol],
                       [ro*np.sin(np.pi/6.)-tol, ro*np.cos(np.pi/6.)+tol, -h2-3*tol],
                       [-ro*np.sin(np.pi/6.)+tol, ro*np.cos(np.pi/6.)+tol, -h2-3*tol],])

    inside_node_ids = find_points_inside(points, region)

    for i_id in inside_node_ids:

        i = points[i_id]
        a = i[1]/ri # linear change in the direction of ri (inner radius of the hexagon)
        dh = np.sqrt(ro**2 - i[0]**2) - ri

        b = i[2]/h2 # linear change in the direction of h (height of the block)
        
        uy = a*b*dh
        
        i[1] += uy * direction
        
    return


def transform_hexagon_edges(points, ro, ri, h2):

    # rotate for 90 deg (for easier transformation of edges)
    R = rot_mat_z(np.pi/2)
    rot_points(points, R)

    # transform
    for n in range(6):
        
        if n % 2 == 0:
            transform_edge(points, ro, ri, h2, -1.)
        
        else:
            transform_edge(points, ro, ri, h2, +1.)

        R = rot_mat_z(np.pi/3)
        rot_points(points, R)

    return


def rot_mat(alpha):

    R = np.array([[np.cos(alpha), -np.sin(alpha)],
                  [np.sin(alpha), np.cos(alpha)],
                  ])
    return R

def rot_mat_z(alpha):

    R = np.array([[np.cos(alpha), -np.sin(alpha), 0.],
                  [np.sin(alpha), np.cos(alpha), 0.],
                  [0., 0., 1.],
                  ])
    return R

def rot_points(points, R):

    for i, p in enumerate(points):

        points[i] = R @ np.array(p).T

    return


def transform_cylinder(points, r0, alpha, ri, t):

    '''ri: inner radius of a tube '''
    
    points_1 = []
    
    for i in points:

        r = (r0 + t/2) + i[2] 
        beta = i[1]/ri*alpha/2
        
        y = r * np.sin(beta)
        z = r * np.cos(beta) - (r0 + t/2)

        i[1] = y
        i[2] = z

        points_1.append(i)
        
    return points_1

