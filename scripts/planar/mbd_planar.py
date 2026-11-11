"""
Main script for planar interlocking simulations.
"""
import numpy as np

from scripts.planar.config import *
from src.blocks.planar_block.block import get_blocks, group_faces, group_faces_wall
from src.blocks.planar_block.assembly import get_assembly
from src.blocks.run_mbd import analyse_contact_pressure, test_interlocking
from src.engine.util import makeDirIfNotExists


# Plot settings (überschreiben die config.py)
SHOW = False      # Plot anzeigen
SAVE = True       # Plot speichern
HTML = True       # HTML speichern


# ============================================================================
# Parameter lists
# ============================================================================

# Für Versatile/Bisquare:
# h_list = [np.sqrt(2)/2, 7*np.sqrt(2)/16, 6*np.sqrt(2)/16, 5*np.sqrt(2)/16, 
#           np.sqrt(2)/4, 3*np.sqrt(2)/16, np.sqrt(2)/8, np.sqrt(2)/16]

# Für Octahedron:
h_list = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


# ============================================================================
# Simulation functions
# ============================================================================

def run(h_value=None, block_type=None, group_name=None, n_blocks=None, m_blocks=None, 
        ref=None, bvp=None, out_dir_override=None):
    """
    Run simulation with optional overrides.
    """
    # Use config defaults
    if block_type is None:
        block_type = block_config['type']
    if group_name is None:
        group_name = assembly_config['group']
    if n_blocks is None:
        n_blocks = assembly_config['n']
    if m_blocks is None:
        m_blocks = assembly_config['m']
    if ref is None:
        ref = block_config['refinement']
    if bvp is None:
        bvp = 'ceiling'
    
    # h_value nur für parametrisierte Blöcke
    if h_value is None:
        h_value = block_config['h']
    
    # Update configs
    block_config['type'] = block_type
    block_config['refinement'] = ref
    block_config['edgeLength'] = np.sqrt(3) / np.sqrt(2)
    
    # h nur setzen wenn nicht None
    if h_value is not None:
        block_config['h'] = h_value
    else:
        # Für nicht-parametrisierte Blöcke h entfernen
        block_config['h'] = None
    
    assembly_config['n'] = n_blocks
    assembly_config['m'] = m_blocks
    assembly_config['group'] = group_name
    
    # Generate name
    if h_value is not None and 'param' in block_type or block_type == 'irr_octahedron':
        name = f"{block_type}_{group_name}_{bvp}_{ref}_{n_blocks}x{m_blocks}_h{h_value:.3f}"
    else:
        name = f"{block_type}_{group_name}_{bvp}_{ref}_{n_blocks}x{m_blocks}"
    
    out_dir = out_dir_override if out_dir_override else out_config['out_dir']
    out_dir = f"{out_dir}{name}/"
    
    out_config['name'] = name
    plot_config['out_dir'] = out_dir
    #plot_config['clim'] = [0.0,0.25]
    plot_config['assembly_all'] = 'together' # 'together', 'assembly'
    
    makeDirIfNotExists(out_dir)
    
    # Run
    group_func = group_faces_wall if bvp == 'wall_left' or bvp == 'wall_right' else group_faces
    
    analyse_contact_pressure(
        block_config, get_blocks, group_func,
        blocks_bvp_config, bvp,
        assembly_config, get_assembly, set_bvp,
        plot_config, out_config, info
    )

    #test_interlocking(
    #        block_config, get_blocks, group_func,
    #        blocks_bvp_config, bvp,
    #        assembly_config, get_assembly, set_bvp,
    #        plot_config, out_config, info
    #    )
    


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

    #run(block_type='octahedron', group_name='octa', n_blocks=4, m_blocks=4, ref=4)
    
    # 2. Parametrisierter Block (mit h)
    #run(block_type='irr_octahedron', h_value=0.7, group_name='octa', n_blocks=6, m_blocks=6,ref=4)

    #run(block_type='versatile_param', h_value=np.sqrt(2)/2, group_name='p4', n_blocks=6, m_blocks=6,ref=4)
    
    # 3. H-Sweep für parametrisierte Blöcke
    #h_sweep(block_type='irr_octahedron', group_name='irr_octa', n_blocks=6, m_blocks=6, h_values=h_list, ref=4)
    
    # 4. H-Sweep für Versatile
    #h_sweep(
    #    h_values=[np.sqrt(2)/2, 6*np.sqrt(2)/16, np.sqrt(2)/4],
    #    block_type='versatile_param',
    #    group_name='p4',
    #    n_blocks=4,
    #    m_blocks=4,
    #    ref=4
    #)
    
    # 5. Wall BVP
    run(block_type='brick_inter', bvp='wall_left', n_blocks=5, m_blocks=15, ref=4,group_name='p1_brick')

    #run(block_type='brick', bvp='wall_left', n_blocks=5, m_blocks=15, ref=4,group_name='p1_brick')