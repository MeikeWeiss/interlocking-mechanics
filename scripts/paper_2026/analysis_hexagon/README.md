
# Hexagon-based Block ( et al.): Analysis Scripts

This directory contains scripts used to reproduce the **analysis** for the Sinus Block assemblies.  
The scripts perform numerical simulations, parameter studies, and post-processing of results.

They rely on the main implementation in the repository (`src/engine`, `src/blocks`, etc.) and should be run from the repository root.

---

# Overview

The scripts in this directory perform the following tasks:

- Run **single MBD simulations** of hexagon-based block assemblies
- **Generate Abaqus input files** for quasi-static FEM simulations

The outputs include contact pressure fields, equilibrium checks, and aggregated performance measures used in the publication.

---

# Directory Contents

| File | Description |
|-----|-------------|
| `config.py` | Central configuration file defining geometry, assembly parameters, boundary conditions, plotting settings, and BVP definitions. |
| `mbd.py` | Runs a single simulation and optionally performs an interlocking test. Useful for quick experimentation and debugging. |
| `mbd_bvp.py` | Runs simulations for several predefined boundary value problems (pipe, tunnel, pillar, beam, shaft) and computes measures from the results. |
| `config_abq.py` | Configuration file defining Abaqus simulation parameters. |
| `abq.py` | Creating Abaqus input files to run quasi-static FEM simultions for several predefined boundary value problems (pipe, tunnel, pillar, beam, shaft). |

---

# Usage

## Run a Single MBD Simulation

```bash
python -m scripts.paper_2026.analysis_hexagon.mbd
```

This script:

- Builds the block assembly
- Performs an **interlocking test**
- Runs the equilibrium/contact analysis


Parameters such as:

- number of blocks
- block thickness
- number of layers

can be modified at the top of `mbd.py`.

---

## Run Multiple Boundary Value Problems

```bash
python -m scripts.paper_2026.analysis_hexagon.mbd_bvp
```

This script evaluates different **BVP scenarios**:

- `pipe`
- `tunnel`
- `pillar`
- `beam`
- `shaft`

It computes contact pressure distributions and prints summary measures such as:

- effective contact area
- average effective pressure
- maximum average contact pressure.

---

## Generate Abaqus Input Files

```bash
python -m scripts.paper_2026.analysis_hexagon.abq
```

This script generates **Abaqus `.inp` files** for quasi-static FEM simulations of the block assemblies.  
The configurations and Abaqus-specific parameters are defined in:

```
config_abq.py
```

The generated models correspond to the same **boundary value problems** used in the MBD simulations:

- `pipe`

These input files can then be executed directly in Abaqus for validation and comparison with the in-house simulation framework.

---

## Notes

- All scripts assume they are executed **from the repository root**.
- Most parameters can be modified either in `config.py` or at the beginning of each script.
