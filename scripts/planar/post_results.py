"""
Author: Domen Macek
Affiliation: RWTH Aachen University / Institute of Applied Mechanics (IFAM)
Email: domen.macek@ifam.rwth-aachen.de

Created: 2025-09-30
Last Modified: ?

License: MIT

Reference:
"""


import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

from scripts.planar.config import *
from src.blocks.planar_block.post_mbd import analyse_results

def get_snaps_file_path(type, group, refinement,n,m, h,out_config):

    if h!=None:
        out_config['name'] = f'{type}_{group}_{refinement}_{n}x{m}_h{h:.3f}'
    else:
        out_config['name'] = f'{type}_{group}_{refinement}_{n}x{m}'
    out_dir = f"{out_config['out_dir']}{out_config['name']}/"
    snaps_file = f"{out_dir}snaps.txt"

    return snaps_file


def analyse_results_test( ):

    h_list=[np.sqrt(2)/2,7*np.sqrt(2)/16,6*np.sqrt(2)/16,5*np.sqrt(2)/16,np.sqrt(2)/4,3*np.sqrt(2)/16,np.sqrt(2)/8,np.sqrt(2)/16]
    h=None

    refinement = 4
    n = 10
    m = 10

    type='versatile' # 'versatile', 'bisquare'
    group = 'p4' # 'p1', 'pg', 'p4'


    block_config['refinement'] = refinement
    block_config['type'] = type # 'versatile', 'bisquare'
    block_config['h'] = h


    out_config['out_dir'] = './outputs/planar/'


    snaps_file = get_snaps_file_path(type, group, refinement,n,m, h,out_config)
    analyse_results(snaps_file, 'avg_pc_masked')
    
    return 


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':
    
    analyse_results_test()

