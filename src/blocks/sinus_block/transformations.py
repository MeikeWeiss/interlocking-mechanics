"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: ?

License: MIT

Reference:
"""


import numpy as np


########################################################################
# Transformations
########################################################################

def transform_sin(points, l, t, amplitude, frequency, shift):

    points_1 = []
    for i in points:
        
        Ay = amplitude * i[1]/t
        z = Ay * np.sin(2*np.pi * i[0]/l * frequency + shift)
        i[2] += z
        points_1.append(i)
        
    return points_1


def transform_sin_in(points, l, t, amplitude, frequency, shift):

    points_1 = []
    for i in points:
        
        Ay = -amplitude * (i[1]/t-t)
        z = Ay * np.sin(2*np.pi * i[0]/l * frequency + shift)
        i[2] += z
        points_1.append(i)
        
    return points_1


def transform_cos(points, l, t, amplitude, frequency):

    points_1 = []
    for i in points:
        
        Ay = amplitude * i[1]/t
        z = Ay * np.cos(2*np.pi * i[0]/l * frequency)
        i[2] = z
        points_1.append(i)
        
    return points_1


def transform_sin_z(points, l, t, h, amplitude, frequency, shift):

    points_1 = []
    for i in points:
        
        Ayz = amplitude * i[1]/t * i[2]/h
        z = Ayz * np.sin(2*np.pi * i[0]/l * frequency + shift)
        i[2] += z
        points_1.append(i)
        
    return points_1


def transform_sin_z_in(points, l, t, h, amplitude, frequency, shift):

    points_1 = []
    for i in points:
        
        Ayz = -amplitude * (i[1]/t-t) * i[2]/h
        z = Ayz * np.sin(2*np.pi * i[0]/l * frequency + shift)
        i[2] += z
        points_1.append(i)
        
    return points_1


def transform_cos_z(points, l, t, h, amplitude, frequency):

    points_1 = []
    for i in points:
        
        Ayz = amplitude * i[1]/t * i[2]/h
        z = Ayz * np.cos(2*np.pi * i[0]/l * frequency)
        i[2] += z
        points_1.append(i)
        
    return points_1


def rot_mat(alpha):

    R = np.array([[np.cos(alpha), -np.sin(alpha)],
                  [np.sin(alpha), np.cos(alpha)],
                  ])
    return R

def transform_distortion(points, ri, alpha, l, t ):

    points_1 = []
    for i in points:
        
        ly = (ri + i[1])*np.sqrt(2*(1-np.cos(alpha/2)))
        s = ly/l
        
        # create elbow
        beta = (np.pi-alpha/2)/2
        gamma = np.pi/2 - beta # = alpha/4
        if i[0] >= 0.:
            R = rot_mat(-gamma)
        elif i[0] < 0.:
            R = rot_mat(gamma)
            
        x = s*i[0]
        
        Rx = R @ np.array([x, 0.])
        i[0] = Rx[0]
        i[1] = i[1]+ Rx[1]
        # print(i[1])
        points_1.append(i)

    return points_1


def transform_cylinder(points, ri, alpha, t):

    points_1 = []
    
    for i in points:

        r = ri + i[1]*t
        beta = alpha/2 * i[0]
        
        x = r * np.sin(beta)
        y = r * np.cos(beta) - ri
        
        i[0] = x
        i[1] = y

        points_1.append(i)
        
    return points_1


def transform_cylinder_ri(points, ri, alpha, l, t):

    points_1 = []
    
    for i in points:

        r = ri + i[1]
        beta = alpha/2 * i[0]/l
        
        x = r * np.sin(beta)
        y = r * np.cos(beta) - ri
        
        i[0] = x
        i[1] = y

        points_1.append(i)
        
    return points_1

###################################################################
# gap
###################################################################
def transform_cylinder_gap(points, ri, alpha, t, gap_size):

    '''
    Creates a small gap at one end of the cylindrical block.
    It works only it the segment (before deformed) has dimensions: l = 1 and t = 1
    '''
    
    points_1 = []
    
    for i in points:

        r = ri + i[1]*t

        if i[0] == 1.: 
            beta = alpha/2 * i[0] - gap_size/r
            i[2] = i[2] + gap_size
        else:
            beta = alpha/2 * i[0]
        
        x = r * np.sin(beta)
        y = r * np.cos(beta) - ri
        
        i[0] = x
        i[1] = y

        points_1.append(i)
        
    return points_1

    return
