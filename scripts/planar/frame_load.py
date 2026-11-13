"""
Load transfer onto the frame of a planar assembly (ceiling, support='frame').

For every frame block: vertical reaction force, split into contacts in the
lower half (z < 1/2, "bottom plane") and in the upper half of the assembly
("top plane"), normalised with the load of one inner block. The sum over all
frame blocks equals the number of inner blocks, as for the Interlocking Flows
of Goertzen et al. (2025), IJSS 306, 113102, so the values can be compared
directly with their Figs. 6-8 and 13.

Run from the repository root:
    python -m scripts.planar.frame_load
"""

import copy
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.planar.config import block_config, assembly_config, blocks_bvp_config
from scripts.planar.config import new_info
from src.blocks.planar_block.run_mbd_planar import (build_assembly, get_options, prepare_contacts,
                                                    solve_contacts)


def grid_index(bl):
    '''(i, j) of a block in the square lattice of the assembly (diagonal in x-y)'''
    c = (bl.nodes.min(0) + bl.nodes.max(0)) / 2
    return int(round((c[0] + c[1]) / 2)), int(round((c[1] - c[0]) / 2))


def frame_load(block_type='versatile', group='p4', n=10, ref=2, h=None):
    b = copy.deepcopy(block_config)
    a = copy.deepcopy(assembly_config)
    b.update(type=block_type, refinement=ref, h=h)
    a.update(n=n, m=n, group=group, support='frame', objective='pressure',
             contact_method='intersection')
    bvp = blocks_bvp_config['ceiling']

    blocks = build_assembly(b, a, bvp, 'ceiling')['together']
    opts = get_options(a)
    contacts = prepare_contacts(blocks, opts)
    info = new_info()
    solve_contacts(blocks, contacts, opts, info)

    frame = set(contacts['frame'])
    el = contacts['elements']
    # reaction on the frame blocks: vertical force, lower / upper half
    F = {f: np.zeros(2) for f in frame}   # vertical component
    N = {f: np.zeros(2) for f in frame}   # magnitude of the normal force (incl. horizontal thrust)
    for (kind, k), lam in zip(contacts['columns'], contacts['lam']):
        if kind != 'el':
            continue
        ia, ib = el['a'][k], el['b'][k]
        if (ia in frame) == (ib in frame):
            continue
        n_a = np.asarray(el['normal'][k])
        # force on block a is -lam * n_a (compression), on block b +lam * n_a
        fz = -lam * n_a[2] if ia in frame else lam * n_a[2]
        f = ia if ia in frame else ib
        z = np.asarray(el['centroid'][k])[2]
        F[f][0 if z < 0.5 else 1] += -fz           # downward load carried by the frame
        N[f][0 if z < 0.5 else 1] += lam

    total = sum(v.sum() for v in F.values())
    n_inner = len(contacts['active'])
    scale = n_inner / total                         # load of one inner block = 1

    idx = {i: grid_index(blocks[i]) for i in range(len(blocks))}
    i0 = min(v[0] for v in idx.values())
    j0 = min(v[1] for v in idx.values())
    grid = np.full((2, n, n), np.nan)
    grid_n = np.full((2, n, n), np.nan)
    for f, v in F.items():
        i, j = idx[f]
        grid[:, j - j0, i - i0] = v * scale
        grid_n[:, j - j0, i - i0] = N[f] * scale
    return {'grid': grid, 'grid_normal': grid_n, 'equilibrium': info['equilibrium'], 'res_rel': info['res_rel'],
            'n_inner': n_inner, 'n_frame': len(frame)}


def plot_frame_load(results, out_file, key='grid', label='vertical load on frame block / load of one inner block'):
    groups = list(results)
    fig, axes = plt.subplots(3, len(groups), figsize=(4.2 * len(groups), 12), constrained_layout=True)
    vmax = max(np.nanmax(r[key].sum(0)) for r in results.values())
    rows = [('bottom plane (z < 1/2)', lambda g: g[0]), ('top plane (z > 1/2)', lambda g: g[1]),
            ('total', lambda g: g.sum(0))]
    for c, grp in enumerate(groups):
        for r, (title, fun) in enumerate(rows):
            ax = axes[r, c]
            G = fun(results[grp][key])
            im = ax.imshow(np.where(np.isnan(G), np.nan, G), origin='lower', cmap='turbo',
                           vmin=0, vmax=vmax)
            for (j, i), v in np.ndenumerate(G):
                if not np.isnan(v) and v > 0.05:
                    ax.text(i, j, f'{v:.1f}', ha='center', va='center', fontsize=7,
                            color='white' if v < 0.6 * vmax else 'black')
            ax.set_title(f'{grp}: {title}', fontsize=10)
            ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=axes, shrink=0.5, label=label)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    fig.savefig(out_file, dpi=150)
    print(f'saved: {out_file}')


if __name__ == '__main__':
    res = {}
    for grp in ('p1', 'pg', 'p4'):
        r = frame_load('versatile', grp, n=10, ref=2)
        res[grp] = r
        g = r['grid']
        gn = r['grid_normal']
        print(f"{grp}: equilibrium {r['equilibrium']} (res {r['res_rel']:.1e}), {r['n_inner']} inner, "
              f"{r['n_frame']} frame blocks; vertical bottom {np.nansum(g[0]):.1f}, top {np.nansum(g[1]):.1f};"
              f" normal force bottom {np.nansum(gn[0]):.1f}, top {np.nansum(gn[1]):.1f}")
    plot_frame_load(res, './outputs/planar/analysis/versatile_frame_load_10x10.png')
    plot_frame_load(res, './outputs/planar/analysis/versatile_frame_normal_force_10x10.png', 'grid_normal',
                    'normal contact force on frame block / load of one inner block')
    np.savez('./outputs/planar/analysis/versatile_frame_load_10x10.npz',
             **{f'{k}_vertical': v['grid'] for k, v in res.items()},
             **{f'{k}_normal': v['grid_normal'] for k, v in res.items()})
