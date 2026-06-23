import numpy as np

from scripts.planar.config import *
from src.blocks.planar_block.block import get_blocks, group_faces
from src.blocks.planar_block.assembly import get_assembly
from src.blocks.run_mbd import analyse_contact_pressure, test_interlocking
from src.engine.util import makeDirIfNotExists

#### parameters #####################

h_list=[np.sqrt(2)/2,7*np.sqrt(2)/16,6*np.sqrt(2)/16,5*np.sqrt(2)/16,np.sqrt(2)/4,3*np.sqrt(2)/16,np.sqrt(2)/8,np.sqrt(2)/16]
h=h_list[1]

refinement = 4
n = 10
m = 10

type='bisquare_param' # 'versatile', 'bisquare'
group = 'p4' # 'p1', 'pg', 'p4'

bvp_type= 'ceiling'


block_config['refinement'] = refinement
block_config['type'] = type # 'versatile', 'bisquare'
block_config['h'] = h

assembly_config['n'] = n
assembly_config['m'] = m
assembly_config['lp_method'] = 'mechanism_test' # 'dof', 'norm2', 'wang2018', 'mechanism_test'
assembly_config['group'] = group # 'p1', 'pg', 'p4'

plot_config['show'] = False
plot_config['save'] = True
plot_config['html'] = True
plot_config['clim'] = None

out_config['out_dir'] = './outputs/planar/'
if type == 'versatile_param' or type == 'bisquare_param':
    out_config['name'] = f"{type}_{group}_{refinement}_{n}x{m}_h{h:.3f}"
else:
    out_config['name'] = f"{type}_{group}_{refinement}_{n}x{m}"

out_dir = f"{out_config['out_dir']}{out_config['name']}/"
plot_config['out_dir'] = out_dir

makeDirIfNotExists(out_dir)

########################################################################

def run():

    analyse_contact_pressure(
        block_config,
        get_blocks,
        group_faces,
        blocks_bvp_config,
        bvp_type,
        assembly_config,
        get_assembly,
        set_bvp,
        plot_config,
        out_config,
        info
    )
        

    return


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':

    run()