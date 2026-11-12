"""
Command line entry for a single planar run (used by the web interface, which
starts every run as a separate process).

    python -m scripts.planar.run_cli '{"block_type": "versatile", "group_name": "p4",
                                       "n_blocks": 4, "m_blocks": 4, "ref": 2}'

All keys are passed to scripts.planar.mbd_planar.run(). Additional keys:
    "plots": false   no plots (faster; snaps.txt, info.json are written anyway)
The name of the output folder is printed as the last line: RESULT_DIR=<path>
"""

import sys
import json

import scripts.planar.mbd_planar as mbd_planar


def main(argv):
    params = json.loads(argv[1]) if len(argv) > 1 else {}

    if not params.pop('plots', True):
        mbd_planar.plot_config['save'] = False
        mbd_planar.plot_config['html'] = False
        mbd_planar.plot_config['show'] = False

    info = mbd_planar.run(**params)
    print(f"RESULT_DIR={info['out_dir']}", flush=True)


if __name__ == '__main__':
    main(sys.argv)
