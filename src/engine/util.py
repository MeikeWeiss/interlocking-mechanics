"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-07-30
Last Modified: ?

License: MIT

Reference:
"""

import time
import os
import shutil
from filecmp import dircmp
import pickle
from json_tricks import dump, load
import numpy as np

def save_to_json(a, outpath):

    # Save to file
    with open(outpath, "w") as f:
        dump(a, f, indent=4)

    return


def load_from_json(path):

    # Save to file
    with open(path, "r") as f:
        a = load(f)

    return a


def makeDirIfNotExists(filePath):
    '''if no directory for files create it'''
    if not os.path.exists(os.path.dirname(filePath)):
        try:
            os.makedirs(os.path.dirname(filePath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

            
def start_time( t, name ):

    t['real_0'][name] = time.perf_counter()
    t['cpu_0'][name] = time.process_time()        
    
    return 


def end_time( t, name ):
    
    t['cpu_1'][name] = time.process_time()
    t['real_1'][name] = time.perf_counter()
    t['dt_cpu'][name] = t['cpu_1'][name] - t['cpu_0'][name]
    t['dt_real'][name] = t['real_1'][name] - t['real_0'][name]
    
    return


def nearest_divisible_by_k(n: int, k: int) -> int:
    """
    Return the integer nearest to n that is divisible by k.
    If two numbers are equally near, the smaller one is returned.
    """
    # Round to nearest multiple of 4
    remainder = n % k
    lower = n - remainder
    upper = lower + k
    
    if n - lower <= upper - n:
        return lower
    else:
        return upper

    
def get_R_and_R6(rot_angle, axis=2):

    '''
    rot_angle: angle of rotation in rad
    axis: 0,1 or 2 - x-axis, y-axis, z-axis
    '''

    c = np.cos(rot_angle)
    s = np.sin(rot_angle)

    if axis == 0:

        # rotation matrix: around x-axis
        R = np.array([
            [1, 0, 0],
            [0, c, -s],
            [0, s, c]
        ])

        # 6x6 block diagonal
        R6 = np.block([
            [R, np.zeros((3,3))],
            [np.zeros((3,3)), R]
        ])

    elif axis == 1:
        pass

    elif axis == 2:
        R = np.array([
            [c, -s, 0],
            [s,  c, 0],
            [0, 0,  1]
        ])
        # 6x6 block diagonal
        R6 = np.block([
            [R, np.zeros((3,3))],
            [np.zeros((3,3)), R]
        ])

    
    return R, R6


def get_M_and_M6(plane):

    '''
    Creates refelction matrix that
    mirrors across the xy-plane or yz-plane or xz-plane
    '''


    if plane == 'xy':

        M = np.array([
            [1,   0,  0],
            [0.,  1,  0],
            [0,   0, -1]
        ])

    elif plane == 'yz':
        M = np.array([
            [-1,   0,  0],
            [0.,  1,  0],
            [0,   0,  1]
        ])

    elif plane == 'xz':
        M = np.array([
            [1,   0,  0],
            [0., -1,  0],
            [0,   0,  1]
        ])

    # 6x6 block diagonal
    M6 = np.block([
        [M, np.zeros((3,3))],
        [np.zeros((3,3)), M]
    ])

    
    return M, M6
