"""
Command line entry for a single run of a tubular assembly (sinus or hexagon
block, as in the paper; used by the web interface, which starts every run as
a separate process).

    python -m scripts.tubular.run_cli '{"block_type": "sinus", "bvp": "pipe", "n": 4, "t": 40}'

The configuration is taken from scripts/paper_2026/analysis_<block>/config.py
and the given parameters are set exactly like in the paper scripts
(scripts/paper_2026/analysis_*/mbd.py). Parameters:

    block_type   'sinus' or 'hexagon'
    bvp          'pipe', 'tunnel', 'pillar', 'beam', 'shaft'
    mode         'force_equilibrium' or 'interlocking_test'
    n, t, n_layers, q
    amplitude, frequency, shift, inout     (sinus block only)
    n_t, n_h                               (sinus mesh; default n_t = 2*(t//3) as in the
                                            BVP study; n_l follows from n and f as in the paper)
    n_t, n_l                               (hexagon mesh; default as in the BVP study:
                                            n_t = 2*(t//3), n_l = 160//n)
    lp_method    interlocking test: 'cone_mechanism' (complete test) or
                 'mechanism_test' (as in the paper)
    plots        True/False
    out_dir      output directory (the run is written to <out_dir>/<name>/)

The output folder is printed as the last line: RESULT_DIR=<path>
"""

import sys
import json

from src.engine.util import makeDirIfNotExists, nearest_divisible_by_k, save_to_json


def configure(params):
    block_type = params.get('block_type', 'sinus')

    if block_type == 'sinus':
        import scripts.paper_2026.analysis_sinus.config as cfg
        from src.blocks.sinus_block.block import get_blocks, group_faces
        from src.blocks.sinus_block.assembly import get_assembly
    elif block_type == 'hexagon':
        import scripts.paper_2026.analysis_hexagon.config as cfg
        from src.blocks.hexagon_based.block import get_blocks, group_faces
        from src.blocks.hexagon_based.assembly import get_assembly
    else:
        raise ValueError(f"Unknown block_type: {block_type}")

    b, a = cfg.block_config, cfg.assembly_config
    b['n'] = int(params.get('n', 4))
    b['t'] = float(params.get('t', 40.))
    a['n_layers'] = int(params.get('n_layers', 12))
    a['lp_method'] = params.get('lp_method', 'cone_mechanism')
    q = float(params.get('q', 0.01))
    cfg.bc_config['q'] = q
    # the load of the BVPs (config) is given for q = 0.01
    for part in cfg.blocks_bvp_config.values():
        for conf in part.values():
            if conf.get('q'):
                conf['q'] = q

    if block_type == 'sinus':
        b['amplitude'] = float(params.get('amplitude', 20.))
        b['frequency'] = float(params.get('frequency', 1.5))
        b['shift'] = float(params.get('shift', 0.))
        b['inout'] = params.get('inout', 'out')
        # default as in the BVP study of the paper (mbd_bvp.py)
        b['n_t'] = int(params.get('n_t', 2 * (b['t'] // 3)))
        b['n_h'] = int(params.get('n_h', b['n_h']))
        # as in the paper: n_l divisible by 4*f
        b['n_l'] = nearest_divisible_by_k(180 // b['n'], k=int(b['frequency'] * 4))
        name = (f"sinus_{params['bvp']}_n{b['n']}_t{b['t']}_sh{b['shift']}_fr{b['frequency']}"
                f"_a{b['amplitude']}_L{a['n_layers']}")
    else:
        # mesh as in the BVP study of the paper (analysis_hexagon/mbd_bvp.py)
        b['n_t'] = int(params.get('n_t', 2 * (b['t'] // 3)))
        b['n_l'] = int(params.get('n_l', 160 // b['n']))
        name = f"hexagon_{params['bvp']}_n{b['n']}_t{b['t']}_L{a['n_layers']}"

    p = cfg.plot_config
    p.update({'assembly_all': 'assembly', 'show': False, 'views': ['pers'], 'parallel': False,
              'clim': None, 'line_width': 4., 'intensity': 0.15, 'window_size': (2000, 6000),
              'zoom': 2.9})
    plots = params.get('plots', True)
    p['save'] = bool(plots)
    p['html'] = bool(plots)

    o = cfg.out_config
    o['out_dir'] = params.get('out_dir', './outputs/webapp/')
    o['name'] = name
    out_dir = f"{o['out_dir']}{name}/"
    p['out_dir'] = out_dir
    makeDirIfNotExists(out_dir)

    return cfg, (get_blocks, group_faces, get_assembly), out_dir


def main(argv):
    params = json.loads(argv[1]) if len(argv) > 1 else {}
    params.setdefault('bvp', 'pipe')
    mode = params.get('mode', 'force_equilibrium')

    cfg, (get_blocks, group_faces, get_assembly), out_dir = configure(params)
    from src.blocks.run_mbd import analyse_contact_pressure, test_interlocking

    args = (cfg.block_config, get_blocks, group_faces, cfg.blocks_bvp_config, params['bvp'],
            cfg.assembly_config, get_assembly, cfg.set_bvp, cfg.plot_config, cfg.out_config,
            cfg.info)

    cfg.info['parameters'] = params
    if mode == 'force_equilibrium':
        analyse_contact_pressure(*args)
    elif mode == 'interlocking_test':
        result = test_interlocking(*args)
        cfg.info['interlocking'] = {k: v for k, v in result.items() if k != 'dq'}
        save_to_json(cfg.info, f"{out_dir}interlocking.json")
    else:
        raise ValueError(f"Unknown mode: {mode}")

    print(f"RESULT_DIR={out_dir}", flush=True)


if __name__ == '__main__':
    main(sys.argv)
