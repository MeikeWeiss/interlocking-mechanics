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
run(block_type='octahedron', h_value=0.5, group_name='octa', n_blocks=6, m_blocks=6, ref=3, support='frame')
run(block_type='starfish', h_value=8/20, group_name='p6', n_blocks=2, ref=3)
```

Arguments that are not given are taken from `config.py`; `config.py` itself is
not modified by `run`.

| Argument | Values |
|---|---|
| `block_type` | `versatile`, `bisquare`, `brick`, `brick_inter`, `versatile_param`*, `tortuga`* (parameterised bisquare), `octahedron`*, `starfish`* (* requires `h_value`) |
| `group_name` | `p1`, `pg`, `p4` (versatile; bisquare and tortuga only `p4`, with `p1`/`pg` the bisquare blocks overlap), `octa` (octahedra), `p1_brick` (bricks), `p6` (starfish). Orientation of p1/pg/p4 as in Goertzen et al. (2025) |
| `bvp` | `ceiling` (default), `wall_left`, `wall_right` (walls: model still open, see `REVIEW_FINDINGS.md`) |
| `mode` | `force_equilibrium` (default), `interlocking_test` |
| `support` | `implicit` (default), `frame` — see below |
| `objective` | `pressure` (default), `force` (as in the paper) — see below |
| `contact_method` | `intersection` (default), `matching` (original method) |

## Octahedron (cut)

`octahedron` (`src/blocks/planar_block/geometry.py`, construction as in the
script `cut_octahedra_volume`): middle part of a regular octahedron.

- Regular octahedron (bottom and top face parallel) with the volume of the
  versatile block (2 in the normalised units; 0.016 in the original script).
- **`h_value` = kept fraction of the height** (frac): the part between
  z1 = (1 − h)/2·H and H − z1 is kept (hexagonal bottom and top, 6 planar
  trapezoids). h = 1 is the full octahedron (default if `h_value` is not given). Values of the CIRP paper:
  1.0, 0.9, …, 0.2.
- Then scaled in z only, so that the volume is again 2. The x-y geometry and
  the lattice of the assembly do not depend on h.
- `group_name='octa'`: m rows (x) of n blocks (y), every second row shifted,
  translations only (as `octahedron_interlocking`). Use `support='frame'`:
  the frame (first/last row and column) is fixed, for 6×6 20 frame and 16
  inner blocks. The gap of 1e-5 of the original script is left out (exact
  contact detection).
- Replaces the former `octahedron` (height 1, no parameter) and
  `irr_octahedron`/`irr_octa`.

## Starfish Block

Block of Schnelle et al. (2026), *Influence of a generative parameter on the
mechanical performance of topological interlocking assemblies of a hexagonal
block*, Procedia CIRP 142, 446–450 (`starfish.pdf`), implemented in
`src/blocks/planar_block/geometry.py` (`starfish`) and
`src/blocks/planar_block/assembly.py` (`create_p6`).

- Wallpaper group p6, fundamental domain: equilateral triangle. On every edge
  the points at ¼ and ¾ are moved by d normal to the edge (¼ inwards, ¾
  outwards, counterclockwise), the deformed triangle is again a fundamental
  domain. Bottom (z = 0): triangle, top (z = 1): deformed triangle, i.e. the
  load of `ceiling` acts on the deformed side as in the paper.
- Scaled to height 1 with the proportions of the paper (height 20 mm, area
  800 mm², a = 42.9829 mm → a = 2.149): **`h_value` = d / 20 mm**, admissible
  0 ≤ h < √3a/4 = 0.9306 (d < 18.6 mm). Paper values d = 1 … 11, 15, 18.5 mm
  → h = 0.05 … 0.55, 0.75, 0.925. Volume 2 as the versatile block.
- Side surfaces: linear interpolation between corresponding points of bottom
  and top; the non-planar quadrilaterals are split into 4 triangles at their
  centre, so neighbouring blocks have identical contact surfaces (all contact
  elements are matching triangle pairs).
- `group_name='p6'`: hexagon of side `n_blocks` (6n² blocks, `m_blocks` is
  ignored and set to n).
- Support model as for the versatile block (`support='implicit'`, default):
  the blocks fit without gaps, so the outer faces act as the rigid frame.
  **n = 2 is the assembly of the paper** (24 inner blocks; the 30 fixed frame
  blocks of the paper are replaced by the rigid boundary). Checked: n = 2
  `implicit` and n = 3 `support='frame'` (30 frame blocks) give identical
  pressures (difference < 1e-14) and the same interlocking result.
- `support='frame'` still works; for p6 the default is then
  `frame_blocks='perimeter'` (all blocks touching the boundary, also only at
  a corner — `boundary` would give only the 18 blocks with an edge on the
  boundary).
- Interlocking test: h = 0 is not interlocked (sliding modes), every h > 0 is
  interlocked, as stated in the paper.
- Note: the rigid block model gives contact pressures that decrease
  monotonically with d; the reversal above d ≈ 10 mm in the FEM results of the
  paper is caused by stress concentrations in thin regions of the blocks,
  which a rigid model cannot capture.

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
mesh. Runs with `objective='force'` get the suffix `_force` in the folder name.
`contact_method='matching'` always uses `force`.

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
`./outputs/planar/<block>_<group>_<bvp>_<ref>_<n>x<m>[_h<h>][_frame][_force]/`
(suffixes only for non-default options: `_frame` for `support='frame'`,
`_force` for `objective='force'`):

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
