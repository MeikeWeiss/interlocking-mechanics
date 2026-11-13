# Web Interface

A local web page to set the parameters of an MBD run, compute it and look at
the result (3D contact pressure plot, measures, interlocking test), to run
parameter studies and to browse existing results.

## Start

From the repository root, with the Python that has the packages of the
project (`requirements.txt`, incl. streamlit):

```bash
python -m streamlit run webapp/app.py        # Windows: py -3.10 -m streamlit run webapp/app.py
```

The browser opens at <http://localhost:8501>.

## Tasks (sidebar)

- **Single run**: set the parameters, compute, view the result.
- **Parameter study**: all settings stay fixed, one parameter is varied
  (values as a comma separated list, e.g. `0.2, 0.4` or `3*sqrt(2)/16`; only
  numbers, `+ - * / **`, `sqrt` and `pi` are accepted). Result: diagram of
  A_eff, p_eff/q, p_max/q over the parameter, table, Excel download; for the
  interlocking test a table of the results.
- **Existing results**: all result folders in `outputs/` (planar runs, paper
  runs in `paper2026/`, web runs), with filter; or the h-series of the planar
  runs (runs that differ only in h) as diagram and table.

## Assemblies

- **Planar** (ceiling): versatile (also parametrised with h), bisquare, tortuga (parametrised bisquare),
  cut octahedron (h = kept fraction of the height), starfish. The model options are fixed: exact contact
  detection (`intersection`), objective min ∫p² dA (`pressure`), supports
  depending on the block type (`frame` for octahedra, `implicit` otherwise),
  see `CHANGES.md` section 11. Bricks/walls are left out until walls are
  considered. Runs `scripts/planar/run_cli.py`.
- **Tubular (paper)**: sinus or hexagon block, BVPs pipe, tunnel, pillar, beam,
  shaft; n, t, layers, for the sinus block amplitude, frequency, shift; load q;
  interlocking test complete (`cone_mechanism`) or as in the paper
  (`mechanism_test`). Mesh as in the BVP study of the paper. The contact
  pressure of the hexagon block can only be computed for the tunnel (the
  hexagon block has a mechanism, there is no equilibrium for the other BVPs).
  Runs `scripts/tubular/run_cli.py`, which reproduces the paper results
  (e.g. sinus pipe n = 4: A_eff 28.3 %, p_eff 0.189; hexagon tunnel: 79.2 %,
  0.039).

Every new run is started as a separate process (its output is shown live) and
written to a new folder `outputs/webapp/<date>_<time>/` (studies:
`<date>_<time>_study/`); existing results are never overwritten.

Measures: planar runs use the area based definitions
(`src/blocks/planar_block/post_mbd.py`), tubular runs the definitions of the
paper code (`src/blocks/sinus_block/post_mbd.py`).

## Sharing

The page runs on the computer where it was started; `localhost` works only
there. Others in the same network can use the "Network URL" shown at start
(firewall permitting); every run is then computed on your computer. For access
from outside, the app has to be hosted (e.g. on an institute server).

## Notes

- Runs with `ref 4` and large assemblies take minutes and produce large HTML
  plots; switch off "Create plots" for studies.
- In WSL without a display, VTK may need an off-screen build (see
  `CHANGES.md`, section 7). On Windows it works directly.
