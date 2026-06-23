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

from scripts.paper_2026.analysis_sinus.config import *
from src.blocks.sinus_block.post_mbd import analyse_results

#################################################################################
# Change parameters only in this function
#################################################################################
def run():

    sh = [0.,] # sinus or cosinus
    show = True
    save = False
    out_config['out_dir'] = './outputs/paper2026/'
    plot_path = f"{out_config['out_dir']}test.png" # mbd_analysis_sinus.png
    plot_measure(
        'p_max_bl_avg',
        sh,
        show,
        save,
        plot_path
    )

    return

##################################################################################
# Plot function
##################################################################################
def plot_measure(measure_type, sh, show, save, plot_path):
    
    amplitude = [10.,15.,20.,25.]
    amplitude = [10.]
    shift = sh
    frequency = [1.0,]
    #frequency = [1.0,1.5]
    N = [2,3,4,5,6] # number of blocks per layer
    #N = [2,] # number of blocks per layer
    T = [30.,40.,50.,60.] # thickness
    #T = [30.,60.] # thickness

    plot_params = {
        'savefig.dpi': 600,
        'font.size': 11,
        #'font.sans-serif': 'Arial',
        'text.usetex': True,
        'pgf.rcfonts': False,
        "pgf.texsystem": "pdflatex",
    }

    # defintion of a centimeter
    cm = 1./2.54
    plt.rcParams.update(plot_params)
    ymin, ymax = 0., 2 #3.5

    # figsize=(17*cm,25*cm)
    fig, axes = plt.subplots(nrows=len(T), ncols=len(frequency), figsize=(17*cm,25*cm))

    for sh in shift:
        block_config['shift'] = sh
        #-----------------------------------
        for i,t in enumerate(T):
            block_config['t'] = t
            
            for j,fr in enumerate(frequency):
                block_config['frequency'] = fr
                #-----------------------------------
                for n in N:
                    block_config['n'] = n

                    pc = []
                    
                    for amp in amplitude:
                        block_config['amplitude'] = amp

                        snaps_file = get_snaps_file_path(n,t,sh,fr,amp, out_config)
                        
                        # 'avg_pc_masked', 'avg_max_pc_per_block'
                        results = analyse_results(snaps_file, show=False)
                        pc.append(results['measures']['p_max_bl_avg'])

                    amp_interp = np.linspace(
                        np.array(amplitude).min(),
                        np.array(amplitude).max(),
                        50
                    )

                    spl = make_interp_spline(
                        np.array(amplitude),
                        np.array(pc),
                        k=2
                    )

                    pc_interp = spl(amp_interp)
                        
                    ax = axes[i,j]
                    ax.scatter(amplitude, pc, label=f"$n = {n}$", marker='o', s=15)
                    ax.plot(amp_interp, pc_interp, '--')
                    ax.set_ylim(ymin, ymax)
                    ax.minorticks_on()
                    ax.grid(True, linestyle='-', linewidth=0.5)  # Turn on gridlines
                    #ax.set_xlabel('amplitude [mm]')
                    #ax.set_ylabel('$p_c$ [MPa]')
                    # ax.legend( fontsize=8) # ncol=3,

    fig.text(0.5, 0.02, r'amplitude $a$ [mm]', ha="center", fontsize=12)     # shared X
    fig.text(0.07, 0.5, r'maximum mean contact pressure $\bar{p}_{\mathrm{max}}$ [MPa]', va="center", rotation="vertical", fontsize=12)  # shared Y

    # collect handles and labels from one axes
    handles, labels = axes[0,0].get_legend_handles_labels()

    # create a single legend for the whole figure
    fig.legend(handles, labels,
               loc="upper left",    # top left of figure
               fontsize=9)
    
    # ---- Column titles (table headers) ----
    col_titles = [f"$f = {fr}$" for fr in frequency]
    for ax, col in zip(axes[0], col_titles):  # first row only
        ax.set_title(col, fontsize=12, pad=20)
        
    # ---- Row titles (row labels) ----
    row_titles = [f"$t = {t}$ mm" for t in T]
    for i, title in enumerate(row_titles):
        # y-position: center of each row (from top to bottom)
        y = -0.9*( i / len(T)) + 0.85
        fig.text(0.04, y, title,
                 va="center", ha="right",
                 rotation="vertical", fontsize=12)
        
    plt.tight_layout(rect=[0.11, 0.03, 1.0, 1.0])  # adjust spacing
    
    # Save the figure
    if save:
        plt.savefig(plot_path)

    # show the plot
    if show:
        plt.show()
    
    return


def get_snaps_file_path(n, t, sh, fr, amp, out_config):

    out_config['name'] = f'n{n}_t{t}_sh{sh}_fr{fr}_a{amp}'
    out_dir = f"{out_config['out_dir']}{out_config['name']}/"
    snaps_file = f"{out_dir}snaps.txt"

    return snaps_file


def analyse_results_test( ):

    amp = 20.
    sh = 0.
    fr = 1.5 
    n = 4 # number of blocks per layer
    t = 40. # thickness

    block_config['t'] = t
    block_config['n'] = n
    block_config['shift'] = sh
    block_config['frequency'] = fr
    block_config['amplitude'] = amp

    snaps_file = get_snaps_file_path(n,t,sh,fr,amp, out_config)
    pc = analyse_results(snaps_file, 'avg_pc_masked')
    print(pc)
    
    return 


#####################################################################################
# Main
#####################################################################################
if __name__ == '__main__':
    
    run()
    #analyse_results_test()

