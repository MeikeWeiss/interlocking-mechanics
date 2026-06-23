
# Planar Assemblies: Analysis Scripts

This directory contains scripts used to produce the **analysis** for planar assemblies.  
The scripts perform numerical simulations, parameter studies, and post-processing of results.

They rely on the main implementation in the repository (`src/engine`, `src/blocks`, etc.) and should be run from the repository root.

---

# Overview

The scripts in this directory perform the following tasks:

- Run **single MBD simulations** of planar assemblies
- **Post-process and visualize** MBD simulation results
- **Generate Abaqus input files** for quasi-static FEM simulations

The outputs include contact pressure fields, equilibrium checks, and aggregated performance measures used in the publication.

---

# Directory Contents

| File | Description |
|-----|-------------|
| `config.py` | Central configuration file defining geometry, assembly parameters, boundary conditions, plotting settings, and BVP definitions. |
| `mbd_planar.py` | Runs a single simulation and optionally performs an interlocking test. Useful for quick experimentation and debugging. |
| `post_results.py` | Post-processing and plotting of simulation results from the parameter study. |

---

# Usage

## Run a Single MBD Simulation

```bash
python -m scripts.planar.mbd_planar
```

This script:

- Builds the block assembly
- Performs an **interlocking test**
- Runs the equilibrium/contact analysis

Parameters such as:

- wallpaper group
- type ob block
- size of assembly

can be modified at the top of `mbd_planar.py`.

---

## Post-Processing Results

```bash
python -m scripts.planar.post_results
```

This script:

- reads simulation snapshots
- computes aggregated measures

---


## Notes

- All scripts assume they are executed **from the repository root**.
- Most parameters can be modified either in `config.py` or at the beginning of each script.

