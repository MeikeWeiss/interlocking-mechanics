"""
Web interface for the MBD analysis of interlocking assemblies.

Start from the repository root:
    python -m streamlit run webapp/app.py

Tasks:
    Single run        set the parameters, compute, view the result
    Parameter study   vary one parameter, compute all runs, diagram + table
    Existing results  browse the results in outputs/ (planar and paper runs),
                      incl. diagrams of existing h-series

Planar assemblies (scripts/planar) and tubular assemblies of the paper
(sinus and hexagon block, scripts/paper_2026). Every new run is started as a
separate process and written to a new folder outputs/webapp/<time>/.
"""

import io
import os
import ast
import sys
import json
import re
import time
import operator
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='Interlocking MBD', layout='wide')

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.planar.mbd_planar import PARAMETRIZED_BLOCKS  # noqa: E402
    from scripts.planar.config import blocks_bvp_config as PLANAR_BVPS  # noqa: E402
    from scripts.planar.plot_h_sweep import plot_h_sweep  # noqa: E402
    from src.blocks.planar_block.post_mbd import analyse_results as measures_planar  # noqa: E402
    from src.blocks.sinus_block.post_mbd import analyse_results as measures_tubular  # noqa: E402
except ModuleNotFoundError as exc:
    st.error(
        f"The Python running this page ({sys.executable}) does not have all packages of the "
        f"project: **{exc.name}** is missing.\n\n"
        "Install the packages for exactly this Python and start the page with it:\n\n"
        f"```\n{sys.executable} -m pip install -r requirements.txt\n"
        f"{sys.executable} -m streamlit run webapp/app.py\n```")
    st.stop()

OUT = ROOT / 'outputs'
WEB_OUT = OUT / 'webapp'

# planar block types and the groups (arrangements) available for them
PLANAR_BLOCKS = {
    'versatile':       ['p1', 'pg', 'p4'],
    'versatile_param': ['p1', 'pg', 'p4'],
    # bisquare, tortuga: only p4 (with p1/pg the blocks overlap, see CHANGES.md section 14)
    'bisquare':        ['p4'],
    'tortuga':         ['p4'],
    # cut octahedron: middle part of a regular octahedron, h = kept fraction of the height
    'octahedron':      ['octa'],
    # starfish (Schnelle et al. 2026): hexagon of side n in a rigid frame (n = 2: assembly of the paper)
    'starfish':        ['p6'],
    # brick, brick_inter (walls) are left out until walls are considered
}
# blocks whose side faces are only partially in contact -> frame supports
FRAME_BLOCKS = ('octahedron',)
H_HELP = {
    'versatile_param': 'Typical values: k·√2/16, k = 1…8 (0.088 … 0.707)',
    'tortuga':         'Typical values: k·√2/16, k = 1…7 (0.088 … 0.619)',
    'octahedron':      'Kept fraction of the height of the octahedron (1 = full octahedron), 0.2 … 1.0; '
                       'scaled in z to the volume of the versatile block',
    'starfish':        'h = d / 20 mm (d of the paper), 0 < h < 0.9306; paper: d = 1 … 11, 15, 18.5 mm '
                       '(h = 0.05 … 0.55, 0.75, 0.925). h = 0 is not interlocking.',
}
H_DEFAULT = {'octahedron': 1.0, 'starfish': 0.4}

TUBULAR_BVPS = {
    'pipe':   'pipe – internal pressure',
    'tunnel': 'tunnel – external pressure',
    'pillar': 'pillar – compression from above',
    'beam':   'beam – bending (point load at mid-span)',
    'shaft':  'shaft – torsion',
}

MODES = {'Contact pressure (equilibrium)': 'force_equilibrium',
         'Interlocking test': 'interlocking_test'}

LP_METHODS = {'cone_mechanism': 'complete test (cone_mechanism)',
              'mechanism_test': 'as in the paper (mechanism_test)'}


###########################################################################
# helpers
###########################################################################
def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def rel(path):
    try:
        return Path(path).resolve().relative_to(ROOT)
    except ValueError:
        return Path(path)


def mode_label(mode):
    return 'interlocking test' if mode == 'interlocking_test' else 'contact pressure'


def classify_mechanism(gamma, tol=1e-6):
    '''same classification as src/engine/mbd.py:mechanism_test'''
    if not gamma or gamma[0] is None:
        return 'classification not available'
    g_min, g_max = gamma
    if g_max > tol and g_min < -tol:
        return 'free (both directions, the load does not constrain the motion)'
    if g_max > tol:
        return 'activated (the load drives the motion)'
    if g_min < -tol:
        return 'suppressed (the load opposes all motions)'
    return 'neutral (the load does no work)'


def run_process(module, params, label, out_dir=None):
    '''
    Starts a run as a separate process and streams its output. Returns the run
    (dict) and adds it to the runs of the session, or None if it failed.
    '''
    out_dir = out_dir or WEB_OUT / time.strftime('%Y%m%d_%H%M%S')
    params = dict(params)
    if module == 'scripts.planar.run_cli':
        params['out_dir_override'] = str(out_dir) + '/'
    else:
        params['out_dir'] = str(out_dir) + '/'

    cmd = [sys.executable, '-u', '-m', module, json.dumps(params)]
    log_box = st.empty()
    lines, result_dir, run = [], None, None
    t0 = time.time()
    with st.status('Computing …', expanded=True) as status:
        # UTF-8 on both sides (Windows otherwise uses the console code page)
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace', bufsize=1, env=env)
        for line in proc.stdout:
            if line.startswith('RESULT_DIR='):
                result_dir = line.split('=', 1)[1].strip()
                continue
            lines.append(line.rstrip())
            log_box.code('\n'.join(lines[-25:]), language=None)
        proc.wait()
        ok = proc.returncode == 0 and result_dir
        if ok:
            status.update(label=f'Finished ({time.time() - t0:.0f} s)', state='complete', expanded=False)
            run = {'label': label, 'dir': str((ROOT / result_dir).resolve()),
                   'kind': 'planar' if 'planar' in module else 'tubular',
                   'mode': params.get('mode', 'force_equilibrium'),
                   'time': time.strftime('%H:%M:%S'), 'log': lines}
            st.session_state.setdefault('runs', []).insert(0, run)
            st.session_state['selected'] = 0
        else:
            status.update(label=f'Run failed (exit code {proc.returncode})', state='error', expanded=True)
    log_box.empty()
    if not ok:
        st.code('\n'.join(lines[-60:]), language=None)
    return run


def run_measures(run):
    '''equilibrium and measures (contact pressure) or result of the interlocking test'''
    folder = Path(run['dir'])
    out = {}
    if run['mode'] == 'interlocking_test':
        r = (load_json(folder / 'interlocking.json') or {}).get('interlocking', {})
        out['motion'] = r.get('motion')
        out['result'] = ('mechanism: ' + classify_mechanism(r.get('gamma')).split(' (')[0]
                         if r.get('motion') else 'interlocked' if r.get('motion') is False
                         else 'not evaluable')
        return out
    info = load_json(folder / 'info.json') or {}
    res_rel = info.get('res_rel', float('nan'))
    out['equilibrium'] = bool(info.get('equilibrium', res_rel < 1e-6 and info.get('status') == 'optimal'))
    out['res_rel'] = res_rel
    snaps = folder / 'snaps.txt'
    if snaps.exists():
        if run['kind'] == 'planar':
            m = measures_planar(str(snaps))
            out.update(A_eff=m['A_eff'], p_eff=m['p_eff'], p_max=m['p_max'], p_max_bl=m['p_max_bl_avg'])
        else:
            r = measures_tubular(str(snaps))
            out.update(A_eff=r['A_eff']['average'], p_eff=r['measures']['p_eff_bl_avg'],
                       p_max=r['measures']['p_max'], p_max_bl=r['measures']['p_max_bl_avg'])
    return out


def show_result(run):
    folder = Path(run['dir'])
    info = load_json(folder / 'info.json')
    inter = load_json(folder / 'interlocking.json')
    st.subheader(run['label'])
    st.caption((f"Computed at {run['time']} · " if run.get('time') else '') + f"folder `{rel(folder)}`")

    if info and (folder / 'snaps.txt').exists():
        try:
            m = run_measures(dict(run, mode='force_equilibrium'))
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Measures could not be computed: {exc}")
            m = {}
        hint = ('area weighted, mean over the blocks' if run['kind'] == 'planar'
                else 'definition of the paper code')
        cols = st.columns(5)
        eq = m.get('equilibrium')
        cols[0].metric('Equilibrium', 'yes' if eq else 'no',
                       help=f"relative residual {info.get('res_rel', float('nan')):.1e}, "
                            f"solver: {info.get('status', '–')}")
        if 'A_eff' in m:
            cols[1].metric('A_eff', f"{m['A_eff']*100:.1f} %", help=f'Effective contact area ({hint})')
            cols[2].metric('p_eff', f"{m['p_eff']:.4g}", help=f'Effective contact pressure ({hint})')
            cols[3].metric('p_max', f"{m['p_max']:.4g}", help='Maximum contact pressure')
            cols[4].metric('p_max (mean of the blocks)', f"{m['p_max_bl']:.4g}")
        if not eq:
            st.warning('No equilibrium found: the load cannot be carried by compressive contact forces '
                       'alone (or the solver failed). The pressures are not meaningful then.')

    if inter and 'interlocking' in inter:
        r = inter['interlocking']
        if r.get('motion'):
            st.error(f"**Mechanism exists** · {classify_mechanism(r.get('gamma'))}")
        elif r.get('motion') is None:
            st.warning('Interlocking test not evaluable (solver failed).')
        else:
            st.success('**Interlocked** – no admissible motion')
        with st.expander('Details of the interlocking test'):
            st.json(r)

    html = folder / 'contact_pressure.html'
    pngs = sorted(folder.glob('*.png'))
    if html.exists():
        st.markdown('**Contact pressure** (3D, rotate with the mouse)')
        size_mb = html.stat().st_size / 1e6
        if size_mb > 50:
            st.warning(f"The HTML file has {size_mb:.0f} MB, loading may take a while.")
        # the plot was written by this code (trusted), it needs JavaScript
        if hasattr(st, 'iframe'):
            st.iframe(html, height=650)
        else:  # older streamlit versions
            components.html(html.read_text(encoding='utf-8', errors='ignore'), height=650)
    elif pngs:
        st.image(str(pngs[0]))

    with st.expander('Log, files'):
        if run.get('log'):
            st.code('\n'.join(run['log'][-200:]), language=None)
        elif info:
            st.json({k: info[k] for k in ('contacts', 'options', 'parameters', 'res_rel', 'status')
                     if k in info})
        c = st.columns(4)
        for i, fname in enumerate(('snaps.txt', 'areas.txt', 'info.json', 'interlocking.json')):
            p = folder / fname
            if p.exists():
                c[i].download_button(fname, p.read_bytes(), file_name=f"{folder.name}_{fname}",
                                     key=f"dl_{folder}_{fname}")


###########################################################################
# forms: return the parameters of a run and the parameters that can be varied
###########################################################################
def form_planar():
    c1, c2, c3 = st.columns(3)
    with c1:
        block_type = st.selectbox('Block type', list(PLANAR_BLOCKS))
        group = st.selectbox('Arrangement (group)', PLANAR_BLOCKS[block_type])
        h = None
        if block_type in PARAMETRIZED_BLOCKS:
            h = st.number_input('h', value=H_DEFAULT.get(block_type, float(np.sqrt(2) / 4)),
                                min_value=0.0 if block_type == 'starfish' else 0.01,
                                max_value={'starfish': 0.93, 'octahedron': 1.0}.get(block_type, 2.0), step=0.05, format='%.4f',
                                help=H_HELP.get(block_type))
    with c2:
        if block_type == 'starfish':
            n = st.number_input('n (side of the hexagon in blocks)', 1, 10, 2,
                                help='6 n² blocks in a rigid frame; n = 2: the 24 inner blocks of the paper '
                                     '(the 30 fixed frame blocks of the paper act like the rigid frame)')
            m = n
        else:
            n = st.number_input('n (blocks in x)', 1, 30, 6 if block_type in FRAME_BLOCKS else 4)
            m = st.number_input('m (blocks in y)', 1, 30, 6 if block_type in FRAME_BLOCKS else 4)
        ref = st.number_input('Refinement (ref)', 0, 6, 2,
                              help='Refinement levels of the triangulation. ref 4 is fine and can take '
                                   'several minutes for large assemblies.')
    with c3:
        bvp = 'ceiling'
        st.markdown('**Boundary value problem:** ceiling (load q from above)')
        mode = MODES[st.radio('Computation', list(MODES))]

    # model options fixed (see CHANGES.md, section 11): exact contact detection,
    # objective min integral p^2, supports depending on the block type
    contact_method, objective = 'intersection', 'pressure'
    support = 'frame' if block_type in FRAME_BLOCKS else 'implicit'
    plots = st.checkbox('Create plots', True, help='Without plots the computation is much faster.')
    if support == 'frame':
        st.caption('Model: the outer blocks form the fixed frame; the inner blocks are computed and '
                   'evaluated (the side faces of octahedra touch the neighbour only on half of their '
                   'area, the free parts must not act as supports). Exact contacts, objective min ∫p² dA.')
    else:
        st.caption('Model: all blocks are computed, the assembly lies in a rigid frame (contact faces on '
                   'the outer boundary are supports). Exact contacts, objective min ∫p² dA.')

    params = dict(block_type=block_type, group_name=group, n_blocks=int(n), m_blocks=int(m),
                  ref=int(ref), bvp=bvp, mode=mode, support=support, objective=objective,
                  contact_method=contact_method, plots=plots)
    label = f"{block_type} {group} {n}×{m} ref {ref} · {bvp}"
    if block_type in PARAMETRIZED_BLOCKS:
        params['h_value'] = float(h)
        label += f" · h = {h:.3f}"

    # parameters that can be varied: key -> (label, default values, setter)
    study = {}
    if block_type in PARAMETRIZED_BLOCKS:
        if block_type == 'octahedron':
            default = '1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2'
        elif block_type == 'starfish':
            default = ', '.join(f'{d}/20' for d in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 18.5))
        else:
            default = ', '.join(f'{k}*sqrt(2)/16' for k in range(1, 9 if block_type == 'versatile_param' else 8))
        study['h'] = ('h', default, lambda p, v: p.update(h_value=v))
    study['n = m'] = ('n = m (blocks)', '1, 2, 3' if block_type == 'starfish' else '4, 6, 8', lambda p, v: p.update(n_blocks=int(v), m_blocks=int(v)))
    study['ref'] = ('refinement ref', '1, 2, 3', lambda p, v: p.update(ref=int(v)))
    q = PLANAR_BVPS.get(bvp, {}).get('block', {}).get('q', 1.)
    return 'scripts.planar.run_cli', params, label, study, q


def form_tubular():
    c1, c2, c3 = st.columns(3)
    with c1:
        block_type = st.selectbox('Block type', ['sinus', 'hexagon'],
                                  format_func={'sinus': 'sinus block', 'hexagon': 'hexagon block'}.get)
        mode = MODES[st.radio('Computation', list(MODES))]
        bvps = list(TUBULAR_BVPS)
        if block_type == 'hexagon' and mode == 'force_equilibrium':
            # the hexagon block has a mechanism: no equilibrium except for the tunnel
            bvps = ['tunnel']
        bvp = st.selectbox('Boundary value problem', bvps, format_func=TUBULAR_BVPS.get)
        if block_type == 'hexagon' and mode == 'force_equilibrium':
            st.caption('The hexagon block has a mechanism: an equilibrium exists only for the tunnel '
                       '(as in the paper). Check the other cases with the interlocking test.')
    with c2:
        n = st.number_input('n (blocks per ring)', 2, 12, 4)
        t = st.number_input('t (wall thickness)', 10., 100., 40., step=5.)
        n_layers = st.number_input('Layers', 2, 30, 12, step=2,
                                   help='Number of block layers (12 in the paper). For beam and shaft '
                                        'the middle layer is loaded.')
    with c3:
        if block_type == 'sinus':
            amp = st.number_input('Amplitude a', 0., 50., 20., step=5.)
            fr = st.selectbox('Frequency f', [1.0, 1.5, 2.0], index=1)
            sh = st.selectbox('Shift s', [0.0, 0.5], format_func={0.0: '0 (sine)', 0.5: '0.5 (cosine)'}.get)
        else:
            st.caption('The hexagon block has no further geometry parameters.')

    with st.expander('Options'):
        o1, o2, o3 = st.columns(3)
        q = o1.number_input('Load q [MPa]', 0.0001, 10., 0.01, format='%.4f')
        lp = o2.selectbox('Interlocking test', list(LP_METHODS), format_func=LP_METHODS.get,
                          disabled=mode != 'interlocking_test',
                          help='For all cases of the paper both tests give the same result.')
        plots = o3.checkbox('Create plots', True)
        auto_nt = True
        n_t = None
        if block_type == 'sinus':
            auto_nt = o1.checkbox('Mesh over the thickness as in the paper (n_t = 2·(t // 3))', True)
            if not auto_nt:
                n_t = o1.number_input('n_t (segments over the thickness)', 4, 60, int(2 * (t // 3)))
    st.caption('Computing time with the settings of the paper (n = 4, 12 layers): about 1 minute, '
               'longer with plots.')

    params = dict(block_type=block_type, bvp=bvp, mode=mode, n=int(n), t=float(t),
                  n_layers=int(n_layers), q=float(q), lp_method=lp, plots=plots)
    label = f"{block_type} · {bvp} · n = {n}, t = {t:g}"
    if block_type == 'sinus':
        params.update(amplitude=float(amp), frequency=float(fr), shift=float(sh))
        if not auto_nt:
            params['n_t'] = int(n_t)
        label += f", a = {amp:g}, f = {fr:g}, s = {sh:g}"

    study = {
        'n': ('n (blocks per ring)', '2, 3, 4, 5, 6', lambda p, v: p.update(n=int(v))),
        't': ('t (wall thickness)', '30, 40, 50, 60', lambda p, v: p.update(t=float(v))),
        'layers': ('layers', '4, 8, 12', lambda p, v: p.update(n_layers=int(v))),
    }
    if block_type == 'sinus':
        study['a'] = ('amplitude a', '10, 15, 20, 25', lambda p, v: p.update(amplitude=float(v)))
        study['f'] = ('frequency f', '1, 1.5, 2', lambda p, v: p.update(frequency=float(v)))
        study['s'] = ('shift s', '0, 0.5', lambda p, v: p.update(shift=float(v)))
    return 'scripts.tubular.run_cli', params, label, study, float(q)


###########################################################################
# parameter study
###########################################################################
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow}


def _safe_number(expr):
    '''evaluates numbers with + - * / ** , sqrt(...) and pi only (no eval)'''
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError('exponent too large')
            return _OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            v = ev(node.operand)
            return -v if isinstance(node.op, ast.USub) else v
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'sqrt'
                and len(node.args) == 1 and not node.keywords):
            return float(np.sqrt(ev(node.args[0])))
        if isinstance(node, ast.Name) and node.id == 'pi':
            return float(np.pi)
        raise ValueError(f'not allowed: {expr}')
    if len(expr) > 100:
        raise ValueError('expression too long')
    return ev(ast.parse(expr, mode='eval'))


def parse_values(text):
    '''"0.2, 0.4" or "1*sqrt(2)/16, 2*sqrt(2)/16" -> list of floats'''
    vals = [_safe_number(tok.strip()) for tok in text.replace(';', ',').split(',') if tok.strip()]
    if len(vals) > 50:
        raise ValueError('at most 50 values')
    return vals


def run_study(module, params, label, setter, name, values, q):
    # the fixed value of the varied parameter (e.g. "h = 0.500" of the form) is
    # not part of the label, every run gets its own value
    label = re.sub(rf' · {re.escape(name)} = [^·]+', '', label).strip()
    out_dir = WEB_OUT / (time.strftime('%Y%m%d_%H%M%S') + '_study')
    progress = st.progress(0., text=f'Parameter study: 0 of {len(values)} runs')
    rows = []
    for i, v in enumerate(values):
        p = dict(params)
        setter(p, v)
        run = run_process(module, p, f"{label} · {name} = {v:g} · {mode_label(p['mode'])}", out_dir)
        row = {name: v}
        if run:
            try:
                row.update(run_measures(run))
            except Exception as exc:  # noqa: BLE001
                row['error'] = str(exc)
        else:
            row['error'] = 'run failed'
        rows.append(row)
        progress.progress((i + 1) / len(values), text=f'Parameter study: {i + 1} of {len(values)} runs')
    study = {'label': label, 'name': name, 'mode': params['mode'], 'q': q, 'rows': rows,
             'dir': str(out_dir), 'time': time.strftime('%H:%M:%S')}
    st.session_state.setdefault('studies', []).insert(0, study)
    st.session_state['study_sel'] = 0  # show the new study (widget is created later in this run)
    st.session_state['view'] = 'study'


def study_table_and_plot(df, name, q, title, mode, key):
    '''diagram (contact pressure) and table of a series of runs'''
    if mode == 'force_equilibrium' and 'A_eff' in df:
        ok = df.dropna(subset=['A_eff']).sort_values(name)
        if len(ok) >= 2:
            data = ok[[name, 'A_eff', 'p_eff', 'p_max']].to_numpy(dtype=float)
            st.pyplot(plot_h_sweep(data, q, title, None, h_label=name, lang='en'))
        if 'equilibrium' in df and not df['equilibrium'].fillna(False).astype(bool).all():
            st.warning('Not all runs are in equilibrium (column equilibrium).')
        table = pd.DataFrame({
            name: df[name],
            'equilibrium': df.get('equilibrium'),
            'A_eff [%]': df['A_eff'] * 100,
            'p_eff': df['p_eff'], 'p_max': df['p_max'],
            'p_max (mean of the blocks)': df.get('p_max_bl'),
            'p_eff / q': df['p_eff'] / q,
            'p_max / q': df['p_max'] / q,
        })
    else:
        table = df[[c for c in (name, 'result', 'error') if c in df]]
    st.dataframe(table, hide_index=True)
    buf = io.BytesIO()
    table.to_excel(buf, index=False)
    st.download_button('Table as Excel', buf.getvalue(), file_name=f"study_{key}.xlsx", key=f"dl_tab_{key}")


def show_study(study):
    st.subheader(f"Parameter study: {study['name']}")
    st.caption(f"{study['label']} · {mode_label(study['mode'])} · computed at {study['time']} · "
               f"folder `{rel(study['dir'])}`")
    study_table_and_plot(pd.DataFrame(study['rows']), study['name'], study['q'], study['label'],
                         study['mode'], study['time'].replace(':', ''))
    st.caption('The single runs (with 3D plot) are listed in the sidebar under "Runs of this session".')


###########################################################################
# existing results
###########################################################################
def existing_runs():
    '''all result folders in outputs/ (planar, paper, web runs)'''
    found = []
    for marker in ('info.json', 'interlocking.json'):
        for f in OUT.rglob(marker):
            d = f.parent
            if d not in [x[0] for x in found]:
                kind = 'planar' if 'planar' in d.relative_to(OUT).parts[0] or \
                    (d / 'areas.txt').exists() else 'tubular'
                found.append((d, kind))
    return sorted(found, key=lambda x: str(x[0]))


def h_series():
    '''runs of parametrised planar blocks that differ only in h'''
    series = {}
    for d, kind in existing_runs():
        info = load_json(d / 'info.json')
        if kind != 'planar' or not info or 'parameters' not in info or not (d / 'snaps.txt').exists():
            continue
        p = info['parameters']
        b, a = p['block'], p['assembly']
        if b.get('h') is None:
            continue
        key = (b['type'], a['group'], p['bvp'], b['refinement'], a['n'], a['m'],
               a.get('support', 'implicit'), a.get('objective', 'force'))
        series.setdefault(key, []).append((b['h'], d))
    return {k: sorted(v) for k, v in series.items() if len(v) >= 2}


def page_existing():
    st.header('Existing results')
    view = st.radio('Show', ['Single result', 'h-series (planar)'], horizontal=True)
    if view == 'Single result':
        runs = existing_runs()
        if not runs:
            st.info('No results in outputs/.')
            return
        flt = st.text_input('Filter (part of the path, e.g. "octa", "frame", "bvps/pipe")')
        sel = [(d, k) for d, k in runs if flt.lower() in str(rel(d)).lower()]
        if not sel:
            st.warning('No folder matches the filter.')
            return
        i = st.selectbox(f'Result folder ({len(sel)})', range(len(sel)), format_func=lambda j: str(rel(sel[j][0])))
        d, kind = sel[i]
        mode = 'interlocking_test' if (d / 'interlocking.json').exists() and not (d / 'snaps.txt').exists() \
            else 'force_equilibrium'
        show_result({'label': d.name, 'dir': str(d), 'kind': kind, 'mode': mode})
    else:
        series = h_series()
        if not series:
            st.info('No series with at least two h values.')
            return

        def label(k):
            t, g, bvp, ref, n, m, sup, obj = k
            return f"{t} · {g} · {bvp} · ref {ref} · {n}×{m} · {sup} · {obj}  ({len(series[k])} runs)"

        key = st.selectbox('Series', list(series), format_func=label)
        rows = []
        for h, d in series[key]:
            row = {'h': h}
            row.update(run_measures({'dir': str(d), 'kind': 'planar', 'mode': 'force_equilibrium'}))
            rows.append(row)
        q = PLANAR_BVPS.get(key[2], {}).get('block', {}).get('q', 1.)
        study_table_and_plot(pd.DataFrame(rows), 'h', q, label(key).split('  (')[0],
                             'force_equilibrium', '_'.join(map(str, key)))


###########################################################################
# page
###########################################################################
with st.sidebar:
    st.title('Interlocking MBD')
    task = st.radio('Task', ['Single run', 'Parameter study', 'Existing results'])
    if task != 'Existing results':
        kind = st.radio('Assembly', ['Planar', 'Tubular (paper)'])

if task == 'Existing results':
    page_existing()
else:
    st.header('Planar assembly' if kind == 'Planar' else 'Tubular assembly (sinus / hexagon block)')
    module, params, label, study_params, q = form_planar() if kind == 'Planar' else form_tubular()

    if task == 'Single run':
        if st.button('Compute', type='primary'):
            if run_process(module, params, f"{label} · {mode_label(params['mode'])}"):
                st.session_state['view'] = 'run'
    else:
        st.markdown('**Parameter study**: all settings above stay fixed, one parameter is varied.')
        s1, s2 = st.columns([1, 2])
        key = s1.selectbox('Parameter', list(study_params), format_func=lambda k: study_params[k][0])
        name, default, setter = study_params[key]
        text = s2.text_input('Values (comma separated, e.g. 0.2, 0.4 or 3*sqrt(2)/16)', default,
                             key=f'values_{kind}_{key}')
        try:
            values = parse_values(text)
            s2.caption(f"{len(values)} runs: " + ', '.join(f'{v:.4g}' for v in values))
        except Exception:  # noqa: BLE001
            values = []
            s2.error('The values could not be read.')
        if params.get('plots'):
            st.caption('Tip: switch off "Create plots" for studies, that saves a lot of time.')
        if st.button('Start study', type='primary', disabled=not values):
            run_study(module, params, label, setter, key, values, q)

    studies = st.session_state.get('studies', [])
    runs = st.session_state.get('runs', [])
    sel = 0
    with st.sidebar:
        if studies:
            st.divider()
            st.markdown('**Studies of this session**')
            st.radio('Study', list(range(len(studies))),
                     format_func=lambda i: f"{studies[i]['time']} · {studies[i]['name']} · {studies[i]['label']}",
                     label_visibility='collapsed', key='study_sel',
                     on_change=lambda: st.session_state.update(view='study'))
        if runs:
            st.divider()
            st.markdown('**Runs of this session**')
            sel = st.radio('Result', list(range(len(runs))),
                           index=min(st.session_state.get('selected', 0), len(runs) - 1),
                           format_func=lambda i: f"{runs[i]['time']} · {runs[i]['label']}",
                           label_visibility='collapsed',
                           on_change=lambda: st.session_state.update(view='run'))
            st.session_state['selected'] = sel

    view = st.session_state.get('view', 'run')
    if view == 'study' and studies:
        st.divider()
        show_study(studies[st.session_state.get('study_sel', 0) or 0])
    elif runs:
        st.divider()
        show_result(runs[sel])
