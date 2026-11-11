# Code-Review: Befunde (Stand 2026-11-11)

Review des Branches `meike/planar` inkl. uncommitteter Änderungen (Basis: Commit `8bf1d73`).
Getestet mit kleinen Modellen (ohne Plots) in einer separaten Python-3.10-Umgebung
(numpy 2.2, cvxpy 1.7, pyvista 0.49).

## Kurzfazit

- Planar `ceiling` mit `versatile`/`bisquare` (`p4`/`p1`/`pg`) funktioniert: Gleichgewicht wird
  erreicht (relatives Residuum ~1e-16).
- **Die Paper-Skripte (Sinusblock) laufen mit den uncommitteten Änderungen nicht mehr** (auf `HEAD` laufen sie).
- **Oktaeder-Ergebnisse sind physikalisch nicht korrekt** (Phantom-Auflager, siehe 2.).
- Weitere Crashes (`wall_right`) und kleinere Fehler.

---

## Fehler (nach Schwere)

### 1. Shared Code für Sinus/Paper kaputt
Dateien: `src/blocks/run_mbd.py`, `src/engine/mbd.py`, `src/engine/plots.py`

- `setup_blocks` wurde auf die planare `Block`-Klasse umgebaut (erwartet `block.surf_filter`,
  `block.face_groups`, `assembly_config['m']`, wird nach der Assemblierung auf Block-Objekten
  aufgerufen). Sinus-/Hexagon-Blöcke speichern die Daten in `bl.data[...]` und brauchen
  `A_b`/`p_b` bereits *vor* der Assemblierung (die `Block`-Klasse kopiert sie im Konstruktor).
- `mbd.py` (`split_solutions_by_blocks`, `compute_pc`, `get_edges`) und `plots.py`
  (`plot_assembly_quantity`) greifen jetzt auf `bl.face_groups` statt `bl.data['face_groups']` zu.
- Sinus `get_blocks(config, assembly_config)` wird in `run_mbd.py` mit nur einem Argument
  aufgerufen → `TypeError` (reproduziert).
- `scripts/paper_2026/analysis_sinus/mbd.py:15`: `from turtle import mode` (versehentlicher
  Auto-Import; lädt Tkinter, kann headless crashen).
- Weitere Aufrufer mit altem Interface (bereits auf `HEAD` teilweise inkonsistent):
  `abq_inp.py`, `figures/*.py`, `mbd_bvp_layer.py`, `post_snaps.py` (importiert nicht
  existierendes `src.blocks.post_mbd`), `planar_block/post_mbd.py::plot_snaps`.

→ Reproduzierbarkeit des Papers betroffen. Planare und Paper-Logik sollten getrennt bleiben.

### 2. Oktaeder: freie Flächen werden als Auflager behandelt
- Kontaktflächen ohne Partner (kein Face-Center innerhalb r=0.01) werden implizit zu festen
  Auflagern (Frame). Beim Oktaeder liegen Seitenflächen nur **zur Hälfte** am Nachbarn an;
  die freie Hälfte jeder Seitenfläche (auch bei inneren Blöcken) wird als Auflager behandelt.
- Gemessen (octahedron, octa, 5×5, ref 2): ca. **36 % aller Auflagerreaktionen** auf solchen
  Phantom-Auflagern innerer Blöcke (Blöcke mit voller Nachbarzahl 6).
- Betrifft `octahedron` und `irr_octahedron` (inkl. bereits gerechnetem h-Sweep).
  `versatile`/`bisquare` mit `p4`: keine ungepaarten Flächen bei inneren Blöcken → ok.
- Geprüft: keine Durchdringungen, keine fehlgepaarten Netze (Faces, die auf einem anderen Block
  liegen, aber nicht gepaart sind: 0).

### 3. `wall_right` crasht immer
`src/blocks/run_mbd.py:107-110`: Nur `wall_left` bekommt `x_max`/`y_max`; bei `wall_right`
wird `group_faces_wall(block)` ohne Argumente aufgerufen → `TypeError`.
Außerdem sind `x_max_global = 2*(n+1)` und `y_max_global = 0.5*(m+1)-0.25` nur für das
Ziegel-Layout (`p1_brick`) gültig, werden aber für alle BVPs berechnet (KeyError ohne `m`).

### 4. Interlocking-Test: hart codiert `n_fixed=8`
`src/engine/mbd.py:121-131`: Es werden immer die letzten 8 Blöcke fixiert.
- Sinus: nur korrekt für n=4 (Frame = 2·n Blöcke).
- Planar: es gibt keinen Frame aus Blöcken → die letzten 8 Blöcke der Assembly werden fixiert (falsch).
- Falle bei `n_fixed=0`: `Y[-0:] == 0` fixiert den gesamten Vektor → Test meldet immer „interlocked“.

### 5. Normalen bei `brick`/`brick_inter` zeigen nach innen
- Geprüft mit trimesh (`fix_normals`) vs. pyvista-Normalen: alle anderen Blöcke außen, `brick`
  und `brick_inter` innen. Da Last und Kontakt dieselben `unit_forces` nutzen, hebt sich das
  im Gleichgewicht auf.
- `group_faces_wall` überschreibt `block.unit_forces[i]` (`[0,1,0]`, `[±1,0,0]`); die Werte
  stimmen nur zufällig, *weil* die Normalen falsch herum sind (bei korrekter Orientierung wären
  die Lasten falsch). `unit_momentum` wird nicht mit angepasst.
- Aliasing: Unrotierte Blöcke teilen sich dasselbe numpy-Array
  (`src/blocks/planar_block/assembly.py:306`, `self.unit_forces = data['unit_forces']`) →
  eine Änderung an einem Block ändert alle.
- Ebenen hart codiert: `group_faces` nutzt z=0 (unten)/z=1 (oben), `group_faces_wall` z=-1/0.
  `brick*` liegt in z∈[-1,0], alle anderen in z∈[0,1] → Ziegel nur mit `wall`, Rest nur mit `ceiling`.
- `brick_inter`/wall: Bedingung `face_normals[i, 2] != 0` (exakter Float-Vergleich) zählt geneigte
  Oberseiten zu `ext_surf`; Druck normal auf geneigte Flächen erzeugt horizontale Lastanteile.
- `top_left` existiert nur, wenn die oberste Reihe gerade ist (`x < 2`, TODO im Code).

### 6. Kleinere Fehler
- `scripts/planar/post_results.py:10`: Ordnername ohne `_{bvp}_` → findet Ergebnisse von
  `mbd_planar.py` nicht.
- `save_solution` füllt bei ungleicher Flächenanzahl mit NaN auf (Wand); `measure_pc` /
  `compute_eff_area` nutzen `np.max`/`sum` → NaN.
- `mbd_planar.run(out_dir_override=...)`: `out_config['out_dir']` wird nicht angepasst → Plots
  und `snaps.txt`/`info.json` landen in verschiedenen Ordnern.
- `requirements.txt`: `trimesh`, `pandas`, `xlsxwriter` fehlen; `pyvista[jupyter]` nötig für HTML-Export.
- `src/engine/util.py:46`: `errno` nicht importiert.
- `geometry.py`: `import trimesh` ungenutzt; `'octahedron_param'` in Liste, aber kein Generator.
- `versatile` (nicht-param.): Kanten (5,9),(6,9) offen, da 5–9–6 kollinear (T-Knoten,
  Fläche 0) → harmlos, aber unsauber.
- `planar_block/block.py::Block._compute_properties`: `A_b`/`p_b` mit hart codierten Indizes
  (`[6:]`, `[2:6]`) — toter Code, wird später überschrieben.
- `get_mbd_data` (`block_mbd.py`): `block['centroid'] = centroid,` erzeugt Tupel (Komma).
- `info`-Dict ist global und wird über Läufe (h-Sweep) weiterverwendet.

---

## Methodische Punkte (zur Diskussion, kein Bug)

- **Minimum-Norm über λ (Kräfte)** bei ungleich großen Dreiecken (planar) bevorzugt kleine
  Flächen → netzabhängige Druckverteilung. `min Σ λ²/A` (= ∫p² dA) wäre netzobjektiv.
  (Sinus: gleich große Quads → unkritisch.)
- **Effektive Fläche**: Code rechnet `N_eff / k_b` (Anzahl). Paper: Summe der *Flächeninhalte*
  der Elemente mit M=1.
- **p_eff**: Code mittelt global gewichtet (`(snaps*M).sum()/M.sum()`), Paper definiert den
  arithmetischen Mittelwert der Blockwerte (Sinus und planar).
- Wand: Druck normal zu geneigten Oberseiten erzeugt horizontale Lastanteile.
- Wand-Lagerung: alle ungepaarten Flächen (Unterseite unterste Reihe, beide Wandenden jeder
  Reihe) sind Auflager → Wand ist seitlich eingespannt. Bewusst so gewollt?

---

## Optimierungsvorschläge

- Eine zentrale Funktion `run_planar(params) -> result` ohne globale, mutierte Config-Dicts.
- Explizite Randbedingungen statt „jede ungepaarte Fläche = Auflager“ (z.B. nur Flächen auf
  dem Umriss der Assembly) → behebt Oktaeder-Problem.
- Plausibilitäts-Report pro Lauf: Normalen-Orientierung, ungepaarte Flächen je Block,
  Residuum, Lastsumme.
- Solver-Output (`verbose=True`) abschaltbar; Screenshot-Fenster 4000×6000 sehr groß.
- Vektorisieren: `get_edges` (lil-Schleife), `to_keep` (`np.setdiff1d`), `expand_solution`.
  Bei 23k Faces unkritisch, bei ~380k Faces (10×10, ref 4) spürbar.

---

## Weboberfläche (Vorschlag)

Lokale **Streamlit-App**:
- Sidebar: Blocktyp (h nur bei parametrisierten), Gruppe (nur kompatible), n×m, Verfeinerung,
  BVP, Last q, Modus (Gleichgewicht / Interlocking-Test), optional h-Sweep.
- Jeder Lauf als Subprozess (VTK/Solver-Crash isoliert), Ergebnis-Cache pro Parametersatz.
- Ergebnis: eingebettete pyvista-HTML, Kennzahlen (Status, Residuum, A_eff, p_eff, p_max),
  Sweep-Tabelle/Diagramm, Downloads, Historie.
- Voraussetzung: `run_planar(params)`.

## Plan

1. Branch: Sinus-Pfad wieder lauffähig/reproduzierbar, `wall_right`, `n_fixed`, Normalen,
   Benennung, NaN fixen + Test-Durchlauf.
2. `run_planar(params)` + explizite Randbedingungen (Oktaeder).
3. Streamlit-App.
