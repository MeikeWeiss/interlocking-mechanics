"""
Main script for planar interlocking simulations.

Run from the repository root:

    python -m scripts.planar.mbd_planar
"""
import copy
import numpy as np

from scripts.planar.config import (
    block_config, assembly_config, blocks_bvp_config, out_config, plot_config,
    new_info,
)
from src.blocks.planar_block.run_mbd_planar import analyse_contact_pressure, test_interlocking
from src.engine.util import makeDirIfNotExists, save_to_json


# ============================================================================
# Parameter lists
# ============================================================================

# Für Versatile/Bisquare:
# h_list = [np.sqrt(2)/2, 7*np.sqrt(2)/16, 6*np.sqrt(2)/16, 5*np.sqrt(2)/16,
#           np.sqrt(2)/4, 3*np.sqrt(2)/16, np.sqrt(2)/8, np.sqrt(2)/16]

# Für Octahedron:
h_list = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

PARAMETRIZED_BLOCKS = ('versatile_param', 'bisquare_param', 'irr_octahedron')


# ============================================================================
# Simulation functions
# ============================================================================

def get_run_name(block_type, group_name, bvp, ref, n_blocks, m_blocks, h_value=None,
                 support='implicit', objective='force'):
    '''name of the output folder of a run'''
    name = f"{block_type}_{group_name}_{bvp}_{ref}_{n_blocks}x{m_blocks}"
    if h_value is not None and block_type in PARAMETRIZED_BLOCKS:
        name += f"_h{h_value:.3f}"
    if support != 'implicit':
        name += f"_{support}"
    if objective != 'force':
        name += f"_{objective}"
    return name


def run(h_value=None, block_type=None, group_name=None, n_blocks=None, m_blocks=None,
        ref=None, bvp='ceiling', out_dir_override=None, mode='force_equilibrium',
        support=None, objective=None, contact_method=None):
    """
    Run a single simulation. Arguments that are None are taken from config.py.

    mode:           'force_equilibrium' or 'interlocking_test'
    support:        'implicit' or 'frame' (see config.py)
    objective:      'force' or 'pressure'
    contact_method: 'intersection' or 'matching'
    """
    # local copies: the configuration in config.py is not modified
    b_conf = copy.deepcopy(block_config)
    a_conf = copy.deepcopy(assembly_config)
    o_conf = copy.deepcopy(out_config)
    p_conf = copy.deepcopy(plot_config)

    if block_type is not None:
        b_conf['type'] = block_type
    if ref is not None:
        b_conf['refinement'] = ref
    if h_value is not None:
        b_conf['h'] = h_value
    if b_conf['type'] not in PARAMETRIZED_BLOCKS:
        b_conf['h'] = None

    if group_name is not None:
        a_conf['group'] = group_name
    if n_blocks is not None:
        a_conf['n'] = n_blocks
    if m_blocks is not None:
        a_conf['m'] = m_blocks
    if support is not None:
        a_conf['support'] = support
    if objective is not None:
        a_conf['objective'] = objective
    if contact_method is not None:
        a_conf['contact_method'] = contact_method

    name = get_run_name(b_conf['type'], a_conf['group'], bvp, b_conf['refinement'],
                        a_conf['n'], a_conf['m'], b_conf['h'],
                        a_conf.get('support', 'implicit'), a_conf.get('objective', 'force'))

    if out_dir_override:
        o_conf['out_dir'] = out_dir_override
    o_conf['name'] = name

    # all results of the run (plots, snaps.txt, info.json) in one folder
    out_dir = f"{o_conf['out_dir']}{name}/"
    p_conf['out_dir'] = out_dir
    makeDirIfNotExists(out_dir)

    info = new_info()
    info['parameters'] = {
        'block': b_conf, 'assembly': a_conf, 'bvp': bvp,
    }

    if mode == 'force_equilibrium':
        analyse_contact_pressure(b_conf, a_conf, blocks_bvp_config[bvp], bvp,
                                 p_conf, o_conf, info)
    elif mode == 'interlocking_test':
        test_interlocking(b_conf, a_conf, blocks_bvp_config[bvp], bvp, info)
        save_to_json(info, f"{out_dir}interlocking.json")
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return info


def h_sweep(h_values=None, **kwargs):
    """Run simulations for multiple h values."""
    if h_values is None:
        h_values = h_list

    for h_val in h_values:
        print(f"\n{'='*60}")
        print(f"h = {h_val:.4f}")
        print(f"{'='*60}")
        run(h_value=h_val, **kwargs)


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':

    # ====== BEISPIELE ======

    # 1. Nicht-parametrisierter Block (kein h)
    #run(block_type='versatile', group_name='p4', n_blocks=4, m_blocks=4)

    # Oktaeder: Seitenflächen nur teilweise im Kontakt -> Rahmen als Auflager
    #run(block_type='octahedron', group_name='octa', n_blocks=6, m_blocks=6, ref=3, support='frame')

    # 2. Parametrisierter Block (mit h)
    #run(block_type='irr_octahedron', h_value=0.7, group_name='irr_octa', n_blocks=6, m_blocks=6, ref=4, support='frame')

    #run(block_type='versatile_param', h_value=np.sqrt(2)/2, group_name='p4', n_blocks=6, m_blocks=6,ref=4)

    # 3. H-Sweep für parametrisierte Blöcke
    #h_sweep(block_type='irr_octahedron', group_name='irr_octa', n_blocks=6, m_blocks=6, h_values=h_list, ref=4, support='frame')

    # 4. H-Sweep für Versatile
    #h_sweep(
    #    h_values=[np.sqrt(2)/2, 6*np.sqrt(2)/16, np.sqrt(2)/4],
    #    block_type='versatile_param',
    #    group_name='p4',
    #    n_blocks=4,
    #    m_blocks=4,
    #    ref=4
    #)

    # 5. Interlocking-Test
    #run(block_type='versatile', group_name='p4', n_blocks=4, m_blocks=4, mode='interlocking_test')

    # 6. Wall BVP
    run(block_type='brick_inter', bvp='wall_left', n_blocks=5, m_blocks=15, ref=4, group_name='p1_brick')

    #run(block_type='brick', bvp='wall_left', n_blocks=5, m_blocks=15, ref=4,group_name='p1_brick')
