# Planar Assemblies: Analysis Scripts

This directory contains scripts for the multibody (MBD) analysis of planar
interlocking assemblies. They rely on the implementation in `src/engine` and
`src/blocks/planar_block` and must be run from the repository root.

The planar driver (`src/blocks/planar_block/run_mbd_planar.py`) is separate
from the driver of the tubular assemblies of the paper (`src/blocks/run_mbd.py`),
so that changes for planar assemblies do not affect the published results.

---

# Directory Contents

| File | Description |
|-----|-------------|
| `config.py` | Default block/assembly parameters, plot settings and boundary value problems (`blocks_bvp_config`). |
| `mbd_planar.py` | Runs single simulations (`run`) or h-sweeps (`h_sweep`): force equilibrium or interlocking test. |
| `post_results.py` | Aggregated measures (effective area, pressures) of an h-sweep, exported to Excel. |

---

# Usage

## Run a Simulation

```bash
python -m scripts.planar.mbd_planar
```

Edit the examples at the bottom of `mbd_planar.py`, e.g.

```python
run(block_type='versatile', group_name='p4', n_blocks=4, m_blocks=4, ref=2)
run(block_type='versatile_param', h_value=0.5, group_name='p4', n_blocks=6, m_blocks=6, ref=4)
run(block_type='brick_inter', bvp='wall_left', n_blocks=5, m_blocks=15, ref=4, group_name='p1_brick')
run(block_type='versatile', group_name='p4', n_blocks=4, m_blocks=4, mode='interlocking_test')
```

Arguments that are not given are taken from `config.py`; `config.py` itself is
not modified by `run`.

| Argument | Values |
|---|---|
| `block_type` | `versatile`, `bisquare`, `octahedron`, `brick`, `brick_inter`, `versatile_param`*, `bisquare_param`*, `irr_octahedron`* (* requires `h_value`) |
| `group_name` | `p1`, `pg`, `p4` (square blocks), `octa`, `irr_octa` (octahedra), `p1_brick` (bricks) |
| `bvp` | `ceiling` (default), `wall_left`, `wall_right` |
| `mode` | `force_equilibrium` (default), `interlocking_test` |

## Boundary Value Problems

- `ceiling`: load `q` on the top faces (highest z), the bottom faces are free.
  Blocks in z ∈ [0, 1].
- `wall_left` / `wall_right` (bricks): the wall lies in the x-y plane (y = height,
  z = thickness). Load `q` from above on the top row and on the left/right end
  face of the top row. Front and back are free.

Contact faces without a contact partner act as rigid supports (frame). For
assemblies in which interior blocks have exposed side faces (e.g. octahedra,
whose side faces are only partially in contact) these faces are currently also
treated as supports — see `REVIEW_FINDINGS.md`.

## Output

All results of a run are written to
`./outputs/planar/<block>_<group>_<bvp>_<ref>_<n>x<m>[_h<h>]/`:

- `snaps.txt` — contact pressure, one column per block (NaN padded if blocks
  have different numbers of contact faces)
- `info.json` — solver status, residual, timings and the parameters of the run
- `contact_pressure.html` / `.png` — plots (if enabled in `config.py`)

## Post-Processing

```bash
python -m scripts.planar.post_results
```

Reads the `snaps.txt` files of an h-sweep and writes an Excel file with the
aggregated measures (requires `pandas` and `xlsxwriter`).
