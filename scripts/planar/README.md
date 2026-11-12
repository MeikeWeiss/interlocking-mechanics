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
run(block_type='octahedron', group_name='octa', n_blocks=6, m_blocks=6, ref=3, support='frame')
```

Arguments that are not given are taken from `config.py`; `config.py` itself is
not modified by `run`.

| Argument | Values |
|---|---|
| `block_type` | `versatile`, `bisquare`, `octahedron`, `brick`, `brick_inter`, `versatile_param`*, `bisquare_param`*, `irr_octahedron`* (* requires `h_value`) |
| `group_name` | `p1`, `pg`, `p4` (square blocks), `octa`, `irr_octa` (octahedra), `p1_brick` (bricks) |
| `bvp` | `ceiling` (default), `wall_left`, `wall_right` |
| `mode` | `force_equilibrium` (default), `interlocking_test` |
| `support` | `implicit` (default), `frame` — see below |
| `objective` | `pressure` (default), `force` (as in the paper) — see below |
| `contact_method` | `intersection` (default), `matching` (original method) |

## Boundary Value Problems

- `ceiling`: load `q` on the top faces (highest z), the bottom faces are free.
  Blocks in z ∈ [0, 1].
- `wall_left` / `wall_right` (bricks): the wall lies in the x-y plane (y = height,
  z = thickness). Load `q` from above on the top row and on the left/right end
  face of the top row. Front and back are free.

## Contacts and Supports

**Contact detection** (`contact_method`, implemented in
`src/blocks/planar_block/contacts.py`): two surface triangles of different
blocks are in contact if they lie in the same plane with opposite normals. With
`intersection` the contact region is the exact intersection polygon of the two
triangles, so the contact area is correct even if the triangulations of the
neighbouring blocks do not match; the triangulation only determines how finely
the pressure field is resolved. For matching triangulations the results are
identical to the original method (`matching`: faces with coinciding centres).

Every run prints a contact report (also stored in `info.json`): number of
contact elements, how many of them are pairs of identical triangles, faces
that are only partially in contact (the boundary of a contact region crosses
the triangle; the pressure is then averaged over the face → refine), etc.

**Supports** (`support`):

- `implicit`: every candidate contact face without any contact acts as a
  rigid support (frame). Suitable if all exposed side faces lie on the outer
  boundary of the assembly (versatile, bisquare, walls).
- `frame`: the frame blocks (`frame_blocks='boundary'`: all blocks with fewer
  neighbours than the interior blocks, or a list of indices) are fixed. Faces
  of the analysed blocks are supported only where they touch a frame block;
  all other faces without contact are free. Required for **octahedra**: their
  side faces are only half in contact with the neighbour (inherent to the
  octahedra arrangement), with `implicit` the free halves would act as
  supports. Results (`snaps.txt`) contain only the analysed blocks.

**Objective** (`objective`): the static problem is statically indeterminate;
`pressure` (default) minimises ∫p² dA = Σ λ²/A, `force` selects the contact
forces with minimal ‖λ‖² (as in the paper). Both coincide if all contact
elements have the same area; for elements of different size (non-matching
triangulations, different face sizes) only `pressure` is independent of the
mesh. Runs with `objective='pressure'` get the suffix `_pressure` in the folder
name. `contact_method='matching'` always uses `force`.

## Interlocking Test

`mode='interlocking_test'` with `lp_method='cone_mechanism'` (default for
planar assemblies) checks whether the cone of first-order admissible motions
{δq : Gᵀδq ≥ 0, frame fixed} is {0}:

1. nullspace of Gᵀ on the free DOFs → motions without normal velocity
   (e.g. bidirectional sliding),
2. LP max 1ᵀ(Gᵀδq) with 0 ≤ Gᵀδq ≤ 1 → motions that open a contact.

The constraints are imposed at the vertices of the contact polygons; since the
normal velocity of a rigid motion is linear on a planar contact region, the
test is exact and independent of the refinement. If a motion exists, the
mechanism test classifies it (activated / suppressed / free / neutral). The
result is written to `interlocking.json`.

The older `mechanism_test` (margin LP of Wang et al. 2018) misses motions
without separation, e.g. plain bricks sliding out of the plane are reported
as interlocked.

## Output

All results of a run are written to
`./outputs/planar/<block>_<group>_<bvp>_<ref>_<n>x<m>[_h<h>]/`:

- `snaps.txt` — contact pressure, one column per block (NaN padded if blocks
  have different numbers of contact faces)
- `areas.txt` — areas of the contact faces, same layout as `snaps.txt`
  (needed for the area based measures)
- `info.json` — solver status, residual, timings and the parameters of the run
- `contact_pressure.html` / `.png` — plots (if enabled in `config.py`)

## Post-Processing

```bash
python -m scripts.planar.post_results
```

Reads the `snaps.txt` files of an h-sweep and writes an Excel file with the
aggregated measures (requires `pandas` and `xlsxwriter`). The measures are
area based (`src/blocks/planar_block/post_mbd.py`, `compute_measures`):

- `A_eff`: per block A_eff,b / A_b with A_eff,b = (∫p dA)² / ∫p² dA
  (participation ratio of the pressure field), averaged over the blocks.
- `p_eff`: per block the area weighted mean pressure on the effective region
  (faces with the highest pressure until their area reaches A_eff,b), then
  the arithmetic mean over the blocks (definition of the paper).
- `p_max`, average of the block maxima.

For equal face areas `A_eff` equals the original count based value. The
original values (count based A_eff, global p_eff) are written as additional
columns `(count)`. Runs without `areas.txt` (older runs) are evaluated with
equal areas.
