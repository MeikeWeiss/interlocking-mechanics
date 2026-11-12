"""
Influence of the parameter h on the contact measures of an h-sweep
(effective area, effective pressure, maximum pressure), one panel per measure.

Run from the repository root:
    python -m scripts.planar.plot_h_sweep
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.planar.mbd_planar import get_run_name
from src.blocks.planar_block.post_mbd import analyse_results

COLOR = '#2a78d6'
INK = '#52514e'
GRID = '#e4e3df'


def collect(h_list, block_type, group, ref, n, m, bvp='ceiling', support='implicit',
            objective='pressure', out_dir='./outputs/planar/'):
    rows = []
    for h in h_list:
        name = get_run_name(block_type, group, bvp, ref, n, m, h, support, objective)
        f = f"{out_dir}{name}/snaps.txt"
        if not os.path.exists(f):
            print(f"missing: {f}")
            continue
        r = analyse_results(f)
        rows.append((h, r['A_eff'], r['p_eff'], r['p_max']))
    return np.array(rows)


def plot_h_sweep(data, q, title, out_file, h_label='h'):
    h, A, pe, pm = data.T
    panels = [
        (A * 100, 'Effektive Kontaktfläche A_eff / A_Kontakt [%]', '{:.0f} %'),
        (pe / q, 'Effektiver Druck p_eff / q [–]', '{:.1f}'),
        (pm / q, 'Maximaler Druck p_max / q [–]', '{:.1f}'),
    ]

    plt.rcParams.update({'font.size': 10, 'axes.edgecolor': INK, 'axes.labelcolor': INK,
                         'xtick.color': INK, 'ytick.color': INK})
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), constrained_layout=True)
    for ax, (y, label, fmt) in zip(axes, panels):
        ax.plot(h, y, color=COLOR, lw=2, marker='o', ms=6,
                markeredgecolor='white', markeredgewidth=1.5, zorder=3)
        ax.set_title(label, fontsize=10, loc='left', color='#0b0b0b')
        ax.set_xlabel(h_label)
        ax.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        # direct labels only at the ends
        for i in (0, -1):
            ax.annotate(fmt.format(y[i]), (h[i], y[i]), textcoords='offset points',
                        xytext=(0, 8), ha='center', fontsize=9, color=INK)
        lo, hi = y.min(), y.max()
        pad = 0.15 * (hi - lo if hi > lo else abs(hi))
        ax.set_ylim(lo - pad, hi + 2 * pad)
    fig.suptitle(title, x=0.01, ha='left', fontsize=11)

    if out_file:
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        fig.savefig(out_file, dpi=200)
        fig.savefig(out_file.replace('.png', '.pdf'))
        print(f"saved: {out_file}")
    return fig


if __name__ == '__main__':
    from scripts.planar.config import blocks_bvp_config

    q = blocks_bvp_config['ceiling']['block']['q']
    r2 = np.sqrt(2)
    series = [
        ('irr_octahedron', 'irr_octa', 6, [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], 'frame',
         'Irreguläres Oktaeder, Decke 6×6 (Rahmen fixiert, innere 4×4 Blöcke), ref 4'),
        ('versatile_param', 'p4', 10, [k * r2 / 16 for k in range(1, 9)], 'implicit',
         'Versatile (p4), Decke 10×10, ref 4'),
        ('bisquare_param', 'p4', 10, [k * r2 / 16 for k in range(1, 8)], 'implicit',
         'Bisquare (p4), Decke 10×10, ref 4'),
    ]
    for block_type, group, n, h_list, support, title in series:
        data = collect(h_list, block_type, group, ref=4, n=n, m=n,
                       support=support, objective='pressure')
        if len(data):
            plot_h_sweep(data, q, title, f'./outputs/planar/analysis/{block_type}_h_sweep.png')
