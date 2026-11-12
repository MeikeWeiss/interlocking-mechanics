"""
Web interface for the MBD analysis of interlocking assemblies.

Start from the repository root:
    python -m streamlit run webapp/app.py

Planar assemblies (scripts/planar) and tubular assemblies of the paper
(sinus and hexagon block, scripts/paper_2026). Every run is started as a
separate process and written to a new folder outputs/webapp/<time>/; only the
runs of the current session are shown (existing results are not read).
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='Interlocking MBD', layout='wide')

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.planar.mbd_planar import PARAMETRIZED_BLOCKS  # noqa: E402
    from src.blocks.planar_block.post_mbd import analyse_results as measures_planar  # noqa: E402
    from src.blocks.sinus_block.post_mbd import analyse_results as measures_tubular  # noqa: E402
except ModuleNotFoundError as exc:
    st.error(
        f"Das Python, mit dem die Web-Seite läuft ({sys.executable}), hat nicht alle Pakete "
        f"des Projekts: **{exc.name}** fehlt.\n\n"
        "Pakete für genau dieses Python installieren und die Seite darüber starten:\n\n"
        f"```\n{sys.executable} -m pip install -r requirements.txt\n"
        f"{sys.executable} -m streamlit run webapp/app.py\n```")
    st.stop()

WEB_OUT = ROOT / 'outputs' / 'webapp'

# planar block types and the groups (arrangements) available for them
PLANAR_BLOCKS = {
    'versatile':       ['p1', 'pg', 'p4'],
    'versatile_param': ['p1', 'pg', 'p4'],
    'bisquare':        ['p1', 'pg', 'p4'],
    'bisquare_param':  ['p1', 'pg', 'p4'],
    'octahedron':      ['octa'],
    'irr_octahedron':  ['irr_octa'],
    'brick':           ['p1_brick'],
    'brick_inter':     ['p1_brick'],
}
WALL_BLOCKS = ('brick', 'brick_inter')
# blocks whose side faces are only partially in contact -> frame supports
FRAME_DEFAULT = ('octahedron', 'irr_octahedron')
H_HELP = {
    'versatile_param': 'Übliche Werte: k·√2/16, k = 1…8 (0.088 … 0.707)',
    'bisquare_param':  'Übliche Werte: k·√2/16, k = 1…7 (0.088 … 0.619)',
    'irr_octahedron':  'Übliche Werte: 0.2 … 1.0',
}

TUBULAR_BVPS = {
    'pipe':   'pipe – Innendruck',
    'tunnel': 'tunnel – Außendruck',
    'pillar': 'pillar – Druck von oben',
    'beam':   'beam – Biegung (Einzellast in der Mitte)',
    'shaft':  'shaft – Torsion',
}

MODES = {'Kontaktdruck (Gleichgewicht)': 'force_equilibrium',
         'Interlocking-Test': 'interlocking_test'}

LP_METHODS = {'cone_mechanism': 'vollständiger Test (cone_mechanism)',
              'mechanism_test': 'wie im Paper (mechanism_test)'}


###########################################################################
# helpers
###########################################################################
def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def classify_mechanism(gamma, tol=1e-6):
    '''same classification as src/engine/mbd.py:mechanism_test'''
    if not gamma or gamma[0] is None:
        return 'Klassifikation nicht verfügbar'
    g_min, g_max = gamma
    if g_max > tol and g_min < -tol:
        return 'frei (in beide Richtungen, die Last schränkt die Bewegung nicht ein)'
    if g_max > tol:
        return 'aktiviert (die Last treibt die Bewegung an)'
    if g_min < -tol:
        return 'unterdrückt (die Last wirkt allen Bewegungen entgegen)'
    return 'neutral (die Last leistet keine Arbeit)'


def run_process(module, params, label):
    '''starts a run as a separate process, streams its output, stores the result folder'''
    out_dir = WEB_OUT / time.strftime('%Y%m%d_%H%M%S')
    params = dict(params)
    if module == 'scripts.planar.run_cli':
        params['out_dir_override'] = str(out_dir) + '/'
    else:
        params['out_dir'] = str(out_dir) + '/'

    cmd = [sys.executable, '-u', '-m', module, json.dumps(params)]
    log_box = st.empty()
    lines, result_dir = [], None
    t0 = time.time()
    with st.status('Rechnung läuft …', expanded=True) as status:
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
        dt = time.time() - t0
        ok = proc.returncode == 0 and result_dir
        if ok:
            status.update(label=f'Rechnung fertig ({dt:.0f} s)', state='complete', expanded=False)
            run = {'label': label, 'dir': str((ROOT / result_dir).resolve()),
                   'kind': 'planar' if 'planar' in module else 'tubular',
                   'mode': params.get('mode', 'force_equilibrium'),
                   'time': time.strftime('%H:%M:%S'), 'log': lines}
            st.session_state.setdefault('runs', []).insert(0, run)
            st.session_state['selected'] = 0
        else:
            status.update(label=f'Rechnung fehlgeschlagen (Exit-Code {proc.returncode})',
                          state='error', expanded=True)
    log_box.empty()
    if not ok:
        st.code('\n'.join(lines[-60:]), language=None)


def show_result(run):
    folder = Path(run['dir'])
    info = load_json(folder / 'info.json')
    inter = load_json(folder / 'interlocking.json')
    st.subheader(run['label'])
    try:
        shown = folder.relative_to(ROOT)
    except ValueError:
        shown = folder
    st.caption(f"Gerechnet um {run['time']} · Ordner `{shown}`")

    if run['mode'] == 'force_equilibrium' and info:
        cols = st.columns(5)
        res_rel = info.get('res_rel', float('nan'))
        eq = info.get('equilibrium', bool(res_rel < 1e-6 and info.get('status') == 'optimal'))
        cols[0].metric('Gleichgewicht', 'ja' if eq else 'nein',
                       help=f"relatives Residuum {res_rel:.1e}, Solver: {info.get('status', '–')}")
        snaps = folder / 'snaps.txt'
        if snaps.exists():
            try:
                if run['kind'] == 'planar':
                    m = measures_planar(str(snaps))
                    vals = (m['A_eff'], m['p_eff'], m['p_max'], m['p_max_bl_avg'])
                    hint = 'flächengewichtet, Mittel über die Blöcke'
                else:
                    r = measures_tubular(str(snaps))
                    vals = (r['A_eff']['average'], r['measures']['p_eff_bl_avg'],
                            r['measures']['p_max'], r['measures']['p_max_bl_avg'])
                    hint = 'Definition wie im Paper-Code'
                cols[1].metric('A_eff', f"{vals[0]*100:.1f} %", help=f'Effektive Kontaktfläche ({hint})')
                cols[2].metric('p_eff', f"{vals[1]:.4g}", help=f'Effektiver Kontaktdruck ({hint})')
                cols[3].metric('p_max', f"{vals[2]:.4g}", help='Maximaler Kontaktdruck')
                cols[4].metric('p_max (Mittel der Blöcke)', f"{vals[3]:.4g}")
            except Exception as exc:  # noqa: BLE001
                st.warning(f"Kennzahlen nicht berechenbar: {exc}")
        if not eq:
            st.warning('Kein Gleichgewicht gefunden: Die Last kann mit Druckkräften allein nicht '
                       'abgetragen werden (oder der Solver ist gescheitert). Die Drücke sind dann '
                       'nicht aussagekräftig.')

    if run['mode'] == 'interlocking_test' and inter and 'interlocking' in inter:
        r = inter['interlocking']
        if r.get('motion'):
            st.error(f"**Mechanismus vorhanden** · {classify_mechanism(r.get('gamma'))}")
        elif r.get('motion') is None:
            st.warning('Test nicht auswertbar (Solver gescheitert).')
        else:
            st.success('**Verzahnt** – keine zulässige Bewegung')
        with st.expander('Details Interlocking-Test'):
            st.json(r)

    html = folder / 'contact_pressure.html'
    pngs = sorted(folder.glob('*.png'))
    if html.exists():
        st.markdown('**Kontaktdruck** (3D, mit der Maus drehbar)')
        size_mb = html.stat().st_size / 1e6
        if size_mb > 50:
            st.warning(f"Die HTML-Datei ist {size_mb:.0f} MB groß, das Laden kann dauern.")
        # the plot was written by this code (trusted), it needs JavaScript
        if hasattr(st, 'iframe'):
            st.iframe(html, height=650)
        else:  # older streamlit versions
            components.html(html.read_text(encoding='utf-8', errors='ignore'), height=650)
    elif pngs:
        st.image(str(pngs[0]))

    with st.expander('Protokoll, Dateien'):
        st.code('\n'.join(run['log'][-200:]), language=None)
        c = st.columns(4)
        for i, fname in enumerate(('snaps.txt', 'areas.txt', 'info.json', 'interlocking.json')):
            p = folder / fname
            if p.exists():
                c[i].download_button(fname, p.read_bytes(), file_name=f"{folder.name}_{fname}",
                                     key=f"dl_{run['dir']}_{fname}")


###########################################################################
# forms
###########################################################################
def form_planar():
    c1, c2, c3 = st.columns(3)
    with c1:
        block_type = st.selectbox('Blocktyp', list(PLANAR_BLOCKS))
        group = st.selectbox('Anordnung (Gruppe)', PLANAR_BLOCKS[block_type])
        h = None
        if block_type in PARAMETRIZED_BLOCKS:
            h = st.number_input('h', value=0.5 if block_type == 'irr_octahedron' else float(np.sqrt(2) / 4),
                                min_value=0.01, max_value=2.0, step=0.05, format='%.4f',
                                help=H_HELP.get(block_type))
    with c2:
        n = st.number_input('n (Blöcke in x)', 1, 30, 6 if block_type in FRAME_DEFAULT else 4)
        m = st.number_input('m (Blöcke in y)', 1, 30, 6 if block_type in FRAME_DEFAULT else 4)
        ref = st.number_input('Verfeinerung (ref)', 0, 6, 2,
                              help='Verfeinerungsstufen der Triangulierung. ref 4 ist fein und kann '
                                   'bei großen Assemblies einige Minuten dauern.')
    with c3:
        bvps = ['ceiling', 'wall_left', 'wall_right'] if block_type in WALL_BLOCKS else ['ceiling']
        bvp = st.selectbox('Randwertproblem', bvps)
        mode = MODES[st.radio('Rechnung', list(MODES))]

    with st.expander('Modelloptionen', expanded=block_type in FRAME_DEFAULT):
        o1, o2, o3, o4 = st.columns(4)
        support = o1.selectbox('Auflager', ['implicit', 'frame'],
                               index=1 if block_type in FRAME_DEFAULT else 0,
                               help='implicit: Flächen ohne Kontakt wirken als Auflager. '
                                    'frame: Randblöcke fixiert, sonst freie Flächen (nötig für Oktaeder).')
        contact_method = o3.selectbox('Kontakterkennung', ['intersection', 'matching'],
                                      help='intersection: exakter Dreiecksschnitt. matching: Originalverfahren.')
        objective = o2.selectbox('Zielfunktion', ['pressure', 'force'],
                                 disabled=contact_method == 'matching',
                                 help='pressure: min ∫p² dA (netzunabhängig). force: min Σλ² (wie im Paper).')
        plots = o4.checkbox('Plots erzeugen', True, help='Ohne Plots ist die Rechnung deutlich schneller.')
        if contact_method == 'matching':
            objective, support = 'force', 'implicit'

    if st.button('Rechnen', type='primary'):
        params = dict(block_type=block_type, group_name=group, n_blocks=int(n), m_blocks=int(m),
                      ref=int(ref), bvp=bvp, mode=mode, support=support, objective=objective,
                      contact_method=contact_method, plots=plots)
        label = f"{block_type} {group} {n}×{m} ref {ref} · {bvp}"
        if block_type in PARAMETRIZED_BLOCKS:
            params['h_value'] = float(h)
            label += f" · h = {h:.3f}"
        label += ' · ' + ('Interlocking-Test' if mode == 'interlocking_test' else 'Kontaktdruck')
        run_process('scripts.planar.run_cli', params, label)


def form_tubular():
    c1, c2, c3 = st.columns(3)
    with c1:
        block_type = st.selectbox('Blocktyp', ['sinus', 'hexagon'],
                                  format_func={'sinus': 'Sinus-Block', 'hexagon': 'Hexagon-Block'}.get)
        bvp = st.selectbox('Randwertproblem', list(TUBULAR_BVPS), format_func=TUBULAR_BVPS.get)
        mode = MODES[st.radio('Rechnung', list(MODES))]
    with c2:
        n = st.number_input('n (Blöcke pro Ring)', 2, 12, 4)
        t = st.number_input('t (Wanddicke)', 10., 100., 40., step=5.)
        n_layers = st.number_input('Lagen', 2, 30, 12, step=2,
                                   help='Anzahl der Blocklagen (im Paper 12). Für beam und shaft '
                                        'wird die mittlere Lage belastet.')
    with c3:
        if block_type == 'sinus':
            amp = st.number_input('Amplitude a', 0., 50., 20., step=5.)
            fr = st.selectbox('Frequenz f', [1.0, 1.5, 2.0], index=1)
            sh = st.selectbox('Verschiebung s', [0.0, 0.5],
                              format_func={0.0: '0 (Sinus)', 0.5: '0.5 (Kosinus)'}.get)
        else:
            st.caption('Der Hexagon-Block hat keine weiteren Geometrieparameter.')

    with st.expander('Optionen'):
        o1, o2, o3 = st.columns(3)
        q = o1.number_input('Last q [MPa]', 0.0001, 10., 0.01, format='%.4f')
        lp = o2.selectbox('Interlocking-Test', list(LP_METHODS), format_func=LP_METHODS.get,
                          disabled=mode != 'interlocking_test',
                          help='Für alle Paper-Fälle liefern beide Tests dasselbe Ergebnis.')
        plots = o3.checkbox('Plots erzeugen', True)
        n_t = None
        if block_type == 'sinus':
            n_t = o1.number_input('Netz: Segmente über die Dicke (n_t)', 4, 60, int(2 * (t // 3)),
                                  help='Standard wie in der BVP-Studie des Papers: 2·(t // 3)')
    st.caption('Rechenzeit mit den Paper-Einstellungen (n = 4, 12 Lagen): etwa 1 Minute, mit Plots länger.')

    if st.button('Rechnen', type='primary'):
        params = dict(block_type=block_type, bvp=bvp, mode=mode, n=int(n), t=float(t),
                      n_layers=int(n_layers), q=float(q), lp_method=lp, plots=plots)
        label = f"{'Sinus' if block_type == 'sinus' else 'Hexagon'} · {bvp} · n = {n}, t = {t:g}"
        if block_type == 'sinus':
            params.update(amplitude=float(amp), frequency=float(fr), shift=float(sh), n_t=int(n_t))
            label += f", a = {amp:g}, f = {fr:g}, s = {sh:g}"
        label += ' · ' + ('Interlocking-Test' if mode == 'interlocking_test' else 'Kontaktdruck')
        run_process('scripts.tubular.run_cli', params, label)


###########################################################################
# page
###########################################################################
with st.sidebar:
    st.title('Interlocking MBD')
    kind = st.radio('Assembly', ['Planar', 'Tubular (Paper)'])

st.header('Planare Assembly' if kind == 'Planar' else 'Tubulare Assembly (Sinus- / Hexagon-Block)')
if kind == 'Planar':
    form_planar()
else:
    form_tubular()

runs = st.session_state.get('runs', [])
if runs:
    with st.sidebar:
        st.divider()
        st.markdown('**Rechnungen dieser Sitzung**')
        sel = st.radio('Ergebnis', list(range(len(runs))),
                       index=min(st.session_state.get('selected', 0), len(runs) - 1),
                       format_func=lambda i: f"{runs[i]['time']} · {runs[i]['label']}",
                       label_visibility='collapsed')
        st.session_state['selected'] = sel
    st.divider()
    show_result(runs[sel])
