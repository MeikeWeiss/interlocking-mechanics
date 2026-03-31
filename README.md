# Interlocking Mechanics

This repository contains code developed to investigate the mechanical performance of interlocking assemblies.

---

## Requirements

All required Python packages are listed in the repository-level file:

```
/requirements.txt
```

It is recommended to install the dependencies inside a virtual environment, for example:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Investigation Scripts

### Sine Block Study (`scripts/paper_2026/`)

The `scripts/paper_2026` directory contains scripts used to reproduce the results presented in the publication:

Macek, D., Weiß, M., Akpanya, R., Brepols, T., Holthusen, H. & Niemeyer, A.C. (2026). *Influence of the Geometry on the Mechanical Performance of Tubular Interlockings: A Study of the Sine Block*. Manuscript submitted for publication.

These scripts perform numerical analyses and post-processing for tubular interlocking structures.

Typical tasks performed by the scripts include:

* Running multibody contact analyses for tubular assemblies
* Performing parameter studies across geometric configurations
* Evaluating different boundary value problems (e.g., pipe, tunnel, pillar, beam, shaft)
* Computing performance measures such as effective contact area and maximum contact pressure
* Generating plots and figures used in the publication

The scripts rely on the implementation contained in the `src/` directory and write results to the `outputs/` directory.

---

## Reproducibility

The scripts are designed to allow full reproduction of the numerical investigations and figures reported in the associated publications.

---

## Citation

If you use this code in your research, please cite the corresponding publication:

> Macek, D., Weiß, M., Akpanya, R., Brepols, T., Holthusen, H. & Niemeyer, A.C. (2026). *Influence of the Geometry on the Mechanical Performance of Tubular Interlockings: A Study of the Sine Block*. Manuscript submitted for publication.
