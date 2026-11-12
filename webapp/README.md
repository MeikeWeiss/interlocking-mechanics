# Web Interface

A local web page to set the parameters of an MBD run, start it and look at
the result (3D contact pressure plot, measures, interlocking test).

## Start

From the repository root, with the Python that has the packages of the
project (`requirements.txt`, incl. streamlit):

```bash
python -m streamlit run webapp/app.py        # Windows: py -3.10 -m streamlit run webapp/app.py
```

The browser opens at <http://localhost:8501>.

## Content

- **Planar**: block type, arrangement, h, n × m, refinement, BVP (ceiling,
  wall), contact pressure or interlocking test, model options (supports,
  objective, contact detection), plots on/off. Runs `scripts/planar/run_cli.py`.
- **Tubular (Paper)**: sinus or hexagon block, BVP (pipe, tunnel, pillar,
  beam, shaft), n, t, number of layers, for the sinus block amplitude,
  frequency, shift and the mesh over the thickness; load q; interlocking test
  complete (`cone_mechanism`) or as in the paper (`mechanism_test`). Runs
  `scripts/tubular/run_cli.py`, which sets the parameters exactly like the
  paper scripts (the paper results are reproduced, e.g. sinus pipe n = 4:
  A_eff 28.3 %, p_eff 0.189).

Every run is started as a separate process (its output is shown live) and
written to a new folder `outputs/webapp/<date>_<time>/`. The page shows only
the runs of the current session (list in the sidebar); existing results in
`outputs/` are not read or overwritten.

Measures: planar runs use the area based definitions
(`src/blocks/planar_block/post_mbd.py`), tubular runs the definitions of the
paper code (`src/blocks/sinus_block/post_mbd.py`).

## Sharing

The page runs on the computer where it was started. `localhost` works only
there. Others in the same network can use the "Network URL" shown at start
(firewall permitting); every run is then computed on your computer. For
access from outside, the app has to be hosted (e.g. on an institute server).

## Notes

- Runs with `ref 4` and large assemblies take minutes and produce large HTML
  plots; switch off "Plots erzeugen" for quick studies.
- In WSL without a display, VTK may need an off-screen build (see
  `CHANGES.md`, section 7). On Windows it works directly.
