# Änderungsprotokoll (Branch `planar-mbd-improvements`)

Was geändert wurde, **warum** es so gemacht wurde und **wie** es geprüft wurde.
Die Befundliste mit Status steht in `REVIEW_FINDINGS.md`.

- Repository: Fork `MeikeWeiss/interlocking-mechanics` (Original `domenmacek/interlocking-mechanics`
  ist lokal als Remote `upstream` eingetragen, es wird nur auf den Fork gepusht).
- Basis: `meike/planar` (`8bf1d73`). Referenz für die Reproduzierbarkeit: `paper2026` (Release).
- Das frühere private Repo `MeikeWeiss/interlocking-mechanics` wurde nicht gelöscht, sondern in
  `interlocking-mechanics-old` umbenannt (Löschen ist nicht rückgängig zu machen).

---

## Commits

| Commit | Inhalt |
|---|---|
| `9e04ace` | Dein uncommitteter Arbeitsstand von `meike/planar`, unverändert gesichert (damit meine Änderungen getrennt nachvollziehbar sind) |
| `6244028` | `REVIEW_FINDINGS.md` |
| `40fa6d7` | Reproduzierbarkeit der Paper-Skripte + planarer Treiber |
| `5d0b2f7` | READMEs, `requirements.txt` |
| `109ba45` | Kontakte über Dreiecksschnitt, Rahmen-Auflager, vollständiger Interlocking-Test |
| (folgende) | siehe Abschnitte unten |

---

## 1. Paper-Skripte (Sinus/Hexagon) wieder reproduzierbar

**Problem:** Der gemeinsame Code (`run_mbd.py`, `engine/mbd.py`, `engine/plots.py`,
`block_mbd.py`) war für die planaren Blöcke umgebaut worden; die Sinus-Skripte brachen ab.

**Änderungen:**
- `src/blocks/run_mbd.py` wieder mit der Logik des Releases: Die Referenzblöcke werden *vor* der
  Assemblierung vorbereitet (`setup_blocks` auf den Dicts), `snaps.txt` im Release-Format.
- Planare Logik in einen eigenen Treiber `src/blocks/planar_block/run_mbd_planar.py`.
  *Warum getrennt:* Planare Flächengruppen hängen von der Position des Blocks in der Assembly ab
  (Wand), Sinus-Blöcke nicht. Ein gemeinsamer Treiber hatte die Paper-Ergebnisse gefährdet;
  getrennt können planare Änderungen die Paper-Ergebnisse nicht mehr beeinflussen.
- Die Engine greift einheitlich auf `bl.face_groups` / `bl.face_areas` zu; die Sinus/Hexagon-
  `Block`-Klasse (`sinus_block/block_class.py`) stellt diese Attribute aus `data` bereit.
- `block_mbd.get_block_matrices` funktioniert mit Dicts (Paper) und Block-Objekten (planar).
- `extract_surface(algorithm="dataset_surface")` explizit (Fallback für alte pyvista-Versionen).
  *Warum:* Die Reihenfolge der Oberflächen-Faces bestimmt die Spalten in `snaps.txt`; neuere
  pyvista-Versionen ändern den Default.
- `plots.plot_assembly_quantity`: Schrittweite (Dreieck/Viereck) aus den Oberflächen-Faces statt
  aus dem Zelltyp (Prismen-Netze führten zu einem Fehler).
- `scripts/paper_2026/analysis_sinus/mbd.py` = Release-Stand (inkl. Entfernen von
  `from turtle import mode`). Deine In/Out-Variante liegt jetzt in
  `scripts/sinus_inout/mbd_inout.py` mit eigenem Ausgabeordner `outputs/sinus_inout/`
  (*warum:* sonst überschreibt sie die Paper-Ergebnisse im selben Ordner).
- Kaputte Importpfade (schon im Release): `figures/*.py` (`paper_figures` → `figures`),
  `post_snaps.py`, `mbd_bvp_layer.py` (`src.blocks.post_mbd` → `src.blocks.sinus_block.post_mbd`).
- `get_blocks(config, assembly_config=None)` für alle Blocktypen (In/Out braucht `assembly_config`).

**Interlocking-Test, Anzahl fixierter Blöcke:** vorher fest `8`. Der Rahmen hat 2·n Blöcke, d.h.
nur für n = 4 korrekt (n < 4: Rohrblöcke fälschlich fixiert, n > 4: Rahmenblöcke frei). Jetzt
wird die tatsächliche Anzahl verwendet (für n = 4 identisch). `n_fixed = 0` fixierte vorher wegen
`Y[-0:]` den ganzen Vektor; abgefangen. Die Parameterstudie (n = 2…6) rechnet nur das
Kraftgleichgewicht und ist davon nicht betroffen.

**Nachweis:** Release (`paper2026`) und Branch mit identischen Parametern gerechnet (Plots aus):
`snaps.txt` aller Sinus-BVPs (pipe, tunnel, pillar, beam, shaft), des Sinus-Einzellaufs und des
Hexagon-Tunnels **byte-identisch**; Kennzahlen und Interlocking-Tests gleich. Nach jedem
weiteren Schritt wiederholt (zuletzt nach der Kontakt-/Interlocking-Erweiterung).

---

## 2. Planare Blöcke: Fehlerbehebungen

- **`wall_right`** stürzte immer ab (Argumente fehlten) → behoben. Ausdehnung der Wand
  (`x_min`, `x_max`, `y_max`) aus der Geometrie statt aus Formeln für das Ziegel-Layout.
- **Normalen** von `brick`/`brick_inter` zeigten nach innen → werden jetzt immer nach außen
  orientiert (Fluss-Test ∑(c−x₀)·n·A > 0). Die Überschreibungen von `unit_forces` in
  `group_faces_wall` waren nur wegen der falschen Orientierung richtig und wurden entfernt.
  *Ergebnis unverändert* (Abweichung 0), weil sich Last und Kontakt vorher gemeinsam umkehrten.
- **Aliasing:** Unrotierte Blöcke teilten sich dieselben numpy-Arrays (eine Änderung an einem
  Block änderte alle) → jeder Block hat eigene Kopien.
- Flächen oben/unten aus der z-Ausdehnung des Blocks statt fest z = 0/1 bzw. −1/0.
- `face_areas` direkt aus dem Netz (vorher aus `extract_surface`, dessen Reihenfolge nicht
  garantiert ist). Toter Code (`A_b`/`p_b` mit festen Indizes) entfernt.
- `mbd_planar.run()` verändert `config.py` nicht mehr (Kopien), eigenes `info` pro Lauf, alle
  Ergebnisse eines Laufs in einem Ordner (vorher bei `out_dir_override` getrennt).
- `post_results.py` findet die Ordner (Name enthält jetzt `bvp`, ggf. `_frame`/`_pressure`).
- NaN-sichere Kennzahlen (Wände: Blöcke mit unterschiedlich vielen Kontaktflächen).
- Kleinkram: `errno`-Import, ungenutzter `trimesh`-Import, `centroid`-Tupel, `requirements.txt`
  (`pandas`, `xlsxwriter`).

**Nachweis:** Kontaktdrücke vor/nach für versatile, bisquare_param, octahedron, brick und
brick_inter (Wand) identisch (≤ 6e-16).

---

## 3. Kontaktmodell über Dreiecksschnitt (`src/blocks/planar_block/contacts.py`)

**Problem:** Kontakt wurde nur erkannt, wenn zwei Dreiecke exakt aufeinander liegen
(Mittelpunkte gleich). Passt die Triangulierung nicht zur Kontaktfläche, geht Kontakt verloren —
und Flächen ohne Partner wurden automatisch zu festen Auflagern.

**Lösung:** Zwei Dreiecke verschiedener Blöcke, die in einer Ebene mit entgegengesetzten
Normalen liegen, werden geschnitten (Sutherland-Hodgman). Jeder nicht-leere Schnitt ist ein
Kontaktelement mit einer Kraft λ ≥ 0 im Schwerpunkt.
- Die Kontaktfläche ist exakt, auch bei nicht passenden Netzen; das Netz bestimmt nur die
  Auflösung des Druckfelds.
- Bei passenden Netzen ist jedes Element ein Paar identischer Dreiecke → identisch zum alten
  Verfahren. Das alte Verfahren bleibt als `contact_method='matching'` verfügbar.
- *Warum Schnitt statt Umvernetzen (Imprinting):* kein Eingriff in die Blockgeometrie nötig,
  funktioniert für beliebige Netze, Engine-Struktur (Jacobi-Matrix) bleibt gleich.
- Performance: Vorauswahl vektorisiert; Flächen mit identischem Partner werden nicht geschnitten
  (sie sind vollständig belegt). Schneller als das alte Matching (10×10, ref 3: 1.0 s statt 2.1 s).
- Kontakt-Bericht in `info.json['contacts']` (Anzahl Elemente, davon identische Paare, teilweise
  belegte Flächen usw.).

**Nachweis:**
- Passende Netze: Drücke identisch zum alten Verfahren (relative Abweichung ≤ 1.3e-14).
- Absichtlich nicht passende Netze (Schachbrett aus ref 2 und baryzentrisch unterteiltem ref 1,
  ref 3 / ref 2+bary): Kontaktfläche in allen Varianten exakt gleich (18.1865), Gleichgewicht
  immer erreicht.

---

## 4. Auflager: `support='implicit' | 'frame'`

**Problem (Oktaeder):** Die Seitenflächen liegen nur zur Hälfte am Nachbarn an. Die freie Hälfte
wurde als festes Auflager behandelt (ca. 36 % der Auflagerkräfte auf solchen Schein-Auflagern).

**Prüfung der Assembly:** keine Durchdringungen; Mittelebene zu 100 % gefüllt, zu Ober-/Unterseite
~72 % → die halbe Kontaktfläche gehört zur Oktaeder-Anordnung, die Assembly ist korrekt.

**Lösung:**
- `implicit` (Default, bisheriges Verhalten): Flächen ohne jeden Kontakt sind Auflager.
- `frame`: Die Rahmenblöcke (`frame_blocks='boundary'` = Blöcke mit weniger Nachbarn als die
  inneren, oder Liste) sind fest; Flächen werden nur dort gestützt, wo sie einen Rahmenblock
  berühren; alle anderen Flächen ohne Kontakt sind frei. `snaps.txt` enthält nur die inneren Blöcke.
- *Warum Rahmenblöcke:* entspricht der TIA-Definition und dem Vorgehen beim Sinus-Rohr
  (Rahmenringe fest).
- *Warum Default weiterhin `implicit`:* bisherige Ergebnisse (versatile, bisquare, Wand) bleiben
  unverändert; bei Wänden ist `frame` nicht sinnvoll (die belastete oberste Reihe wäre Rahmen).

**Nachweis:** Oktaeder 5×5, `frame`: mittlerer Druck konvergiert mit der Verfeinerung
(0.0279 → 0.0274 → 0.0273).

---

## 5. Zielfunktion: `objective='force' | 'pressure'`

- `force` (wie im Paper): min Σλ².
- `pressure`: min Σλ²/A = ∫p² dA.
- *Warum:* Bei unterschiedlich großen Kontaktelementen hängt `force` vom Netz ab
  (Beispiel: mittlerer Druck 0.0060 → 0.0066 bei gemischtem Netz), `pressure` nicht (0.0060 in
  allen Varianten).
- Default für planare Assemblies ist inzwischen `pressure` (siehe Abschnitt 9). Die Paper-Skripte
  (Sinus/Hexagon, `src/blocks/run_mbd.py`) sind davon nicht betroffen.
- Kein zulässiges Gleichgewicht (z.B. ref 0: nur eine Punktkraft pro Fuge, keine
  Momentenübertragung) → `equilibrium=False` statt Absturz.

---

## 6. Interlocking-Test: `lp_method='cone' | 'cone_mechanism'`

**Problem:** Der bisherige Test (`mechanism_test` = Wang 2018: max s mit Gᵀδq ≥ s) übersieht
Bewegungen ohne Separation. Bei bidirektionalen Gleitbewegungen ist die optimale Menge
symmetrisch, der Innere-Punkte-Löser liefert δq = 0 → „interlocked“. Beispiel: einfache Ziegel
als Decke wurden als verzahnt gemeldet.
Gl. (11) im Paper ist in der abgedruckten Form degeneriert (s = 1 zulässig für δq = 0, z* immer
maximal).

**Lösung** (`engine/mbd.py: cone_interlocking_test`), Kegel K = {δq : Gᵀδq ≥ 0, Rahmen fest}:
1. Nullraum von Gᵀ auf den freien DOFs → Gleitmoden,
2. LP max 1ᵀ(Gᵀδq) mit 0 ≤ Gᵀδq ≤ 1 → öffnende Bewegungen.
K = {0} genau dann, wenn beides null ist. Danach Klassifikation mit dem bestehenden
`mechanism_test` (activated/suppressed/free/neutral).

Für planare Assemblies werden die Bedingungen an den **Eckpunkten der Kontaktpolygone**
gestellt. *Warum:* Die Normalgeschwindigkeit einer Starrkörperbewegung ist auf einer ebenen
Kontaktfläche linear → Bedingung an den Ecken ⇔ auf der ganzen Fläche. Der Test ist damit exakt
und unabhängig von der Verfeinerung (vorher Schein-Mechanismen bei groben Netzen).

*Warum der Paper-Pfad unverändert bleibt:* Reproduzierbarkeit; der neue Test ist für die
Paper-Skripte nur als Option verfügbar (siehe Abschnitt 8).

**Nachweis:** ref 0, 1, 2 mit `implicit` und `frame`: versatile (p1, p4), bisquare, brick_inter,
octahedron, irr_octahedron verzahnt; einfache Ziegel freier Mechanismus; Wand: Abheben der
obersten Reihe gefunden („suppressed“ durch die Last).

---

## 7. Plots in WSL

VTK stürzt in WSL mit dem X-Backend (WSLg) ab, auch bei minimalen Plots. Für die Läufe in WSL
wurde eine Offscreen-VTK-Variante (`vtk-osmesa`) plus `trame`, `trame-vtk`, `trame-vuetify`,
`trame-pyvista`, `nest_asyncio2` (für `export_html`) in einer separaten Umgebung genutzt. Am Code
ist dafür nichts geändert. Unter Windows ist das nicht nötig.

---

## 8. Neuberechnungen

### 8.1 Oktaeder mit Rahmen-Auflagern (`support='frame'`)

Gleiche Parameter wie die alten Läufe, Ergebnisse in neuen Ordnern mit Zusatz `_frame`
(die alten Ordner/Dateien sind unverändert):

- `outputs/planar/octahedron_octa_ceiling_{2,4}_4x4_frame/` (4×4: 12 Rahmenblöcke, 4 innere)
- `outputs/planar/irr_octahedron_irr_octa_ceiling_4_6x6_h{0.200…1.000}_frame/` (6×6: 20 Rahmen, 16 innere)
- `outputs/planar/results_irr_octahedron_frame.xlsx` (Kennzahlen des h-Sweeps)
- jeweils `info.json` (inkl. Kontakt-Bericht), `snaps.txt`, Plot (PNG/HTML); `interlocking.json`
  für octahedron ref 2/4 und irr_octahedron h = 0.5

Alle Läufe im Gleichgewicht (relatives Residuum ≤ 1e-14), Interlocking-Test: verzahnt.

| h | A_eff alt | A_eff neu | p_eff alt | p_eff neu | p_max alt | p_max neu |
|---|---|---|---|---|---|---|
| 0.2 | 0.316 | 0.403 | 0.0159 | 0.262 | 0.0258 | 0.845 |
| 0.3 | 0.317 | 0.399 | 0.0159 | 0.236 | 0.0261 | 0.807 |
| 0.4 | 0.319 | 0.394 | 0.0158 | 0.206 | 0.0264 | 0.739 |
| 0.5 | 0.324 | 0.390 | 0.0156 | 0.177 | 0.0266 | 0.654 |
| 0.6 | 0.330 | 0.388 | 0.0154 | 0.151 | 0.0265 | 0.569 |
| 0.7 | 0.339 | 0.390 | 0.0152 | 0.129 | 0.0260 | 0.483 |
| 0.8 | 0.348 | 0.397 | 0.0150 | 0.111 | 0.0255 | 0.435 |
| 0.9 | 0.357 | 0.409 | 0.0147 | 0.096 | 0.0248 | 0.389 |
| 1.0 | 0.365 | 0.432 | 0.0145 | 0.085 | 0.0249 | 0.324 |

*Interpretation:* Vorher haben die Schein-Auflager (freie Flächenhälften auch innerer Blöcke) einen
Großteil der Last direkt abgefangen (im alten Plot sind diese Hälften eingefärbt). Jetzt wird die
Last über die Verzahnung zum Rahmen abgetragen → 10–30-fach höhere Drücke und deutlich stärkere
Abhängigkeit von h (flachere Blöcke, kleiner h, ergeben höhere Drücke).
A_eff ist nur eingeschränkt vergleichbar: gezählt werden jetzt nur tatsächlich berührende Flächen
und nur die inneren Blöcke.

### 8.2 Plots

- `plot_assembly_quantity` brach bei Blöcken ohne Kontaktfläche ab (Rahmen-Eckblöcke, die keinen
  inneren Block berühren) → solche Blöcke werden übersprungen. Für die Paper-Skripte ohne Wirkung
  (dort hat jeder Block Kontaktflächen).
- **Blöcke waren im Plot nicht mehr erkennbar** (Hinweis von dir): Gezeichnet wurden nur die
  Flächen mit Kontakt. Beim alten Modell waren das fast alle Seitenflächen (inkl. Schein-Auflager),
  beim korrekten Modell nur noch die halben Kontaktbereiche → Oktaeder und Lücken unsichtbar.
  Neue Option `show_free_faces` (in `scripts/planar/config.py` an, Default sonst aus, damit die
  Paper-Plots unverändert bleiben): Flächen ohne Kontakt halbtransparent grau (`color_free`,
  `opacity_free = 0.25`), Rahmenblöcke in `color_frame`, Kanten aller Blöcke schwarz.
  *Warum halbtransparent:* Die Kontaktflächen liegen zwischen den Blöcken; undurchsichtige Blöcke
  verdecken sie.
- Die `_frame`-Ergebnisse wurden mit den neuen Plots neu erzeugt; Kennzahlen unverändert
  (Abweichung < 1e-12).

### 8.3 Verzahnung Sinus-/Hexagon-Block (Prüfung der Paper-Aussagen)

Geprüft mit dem neuen vollständigen Test (`cone_mechanism`) und zum Vergleich mit dem alten Test
(`mechanism_test`), jeweils mit korrekt 2·n fixierten Rahmenblöcken bzw. wie im Release fest 8.

**Sinus, gesamter Parameterraum aus Tabelle 3** (480 Kombinationen: a ∈ {10, 15, 20, 25},
s ∈ {0, 0.5}, f ∈ {1, 1.5, 2}, n ∈ {2…6}, t ∈ {30, 40, 50, 60}; Netz wie in
`mbd_parameter_para.py`, 12 Lagen, BVP pipe):
- alle 480 **verzahnt** (kein Mechanismus) — mit allen drei Varianten, keine Abweichung.
- Bestätigt Tabelle 4 des Papers („locked“ für s = 0 und s = 0.5).
- Die fest codierten 8 fixierten Blöcke hatten hier keinen Einfluss auf das Ergebnis.
- Hinweis: Für die Paper-Blöcke wird die Kinematik an den Flächenmittelpunkten geprüft (nicht an
  den Polygonecken). Das ist eine schwächere Bedingung; „verzahnt“ gilt damit erst recht.

**Fünf BVPs (n = 4, t = 40, 12 Lagen)** — alter und neuer Test identisch:

| BVP | Sinus | Hexagon |
|---|---|---|
| pipe | verzahnt | activated (Last treibt Mechanismus) |
| tunnel | verzahnt | suppressed (Last wirkt dagegen) |
| pillar | verzahnt | neutral (Last leistet keine Arbeit) |
| beam | verzahnt | free (beidseitig) |
| shaft | verzahnt | free (beidseitig) |

Bestätigt die Paper-Aussage: Der Hexagon-Block hat einen Mechanismus („explodiert“) und hält nur
beim Tunnel (Außendruck); der Sinus-Block ist für alle BVPs verzahnt.

Skripte der Prüfung (nicht im Repo, nur für die Auswertung genutzt): Sweep über den
Parameterraum mit `kinematic_feasibility(G, f, method, n_fixed)` aus `src/engine/mbd.py`.

---

## 9. Flächenbasierte Kennzahlen und Zielfunktion `pressure` (planar)

### 9.1 Was geändert wurde und warum

Die Kennzahlen der planaren Auswertung (`src/blocks/planar_block/post_mbd.py`) hingen bisher von der
**Anzahl** der Kontaktflächen ab, nicht von ihrer **Fläche**. Bei den planaren Blöcken sind die
Dreiecke unterschiedlich groß (bei Versatile/Bisquare bis Faktor 2), bei nicht passenden Netzen
noch stärker. Ein kleines Dreieck zählte dann genauso viel wie ein großes, das Ergebnis hing also
von der Triangulierung ab. Drei Änderungen:

| | vorher | jetzt | Warum |
|---|---|---|---|
| **Zielfunktion** | `force`: min Σλ² | `pressure`: min ∫p² dA = Σλ²/A (Default für planar) | Σλ² bevorzugt kleine Elemente (gleiche Kraft auf halber Fläche = doppelter Druck), die Druckverteilung hängt vom Netz ab. ∫p² dA ist netzunabhängig. |
| **A_eff** | N_eff / Anzahl Flächen, N_eff = (Σp)²/Σp² | A_eff,b / A_b = (∫p dA)² / (A_b ∫p² dA), Mittel über die Blöcke | Paper-Definition über *Flächeninhalte*. Für gleich große Flächen identisch mit der alten Formel. |
| **Maske** | die int(N_eff) Flächen mit dem höchsten Druck | Flächen mit dem höchsten Druck, bis ihre Fläche A_eff,b erreicht | wie oben, für gleiche Flächen identisch |
| **p_eff** | globales Mittel über alle maskierten Flächen aller Blöcke | pro Block flächengewichtetes Mittel auf der Maske, dann arithmetisches Mittel über die Blöcke | Paper-Definition (Mittel der Blockwerte). Das globale Mittel gewichtet Blöcke mit vielen Flächen stärker. Flächengewichtet = Kraft im wirksamen Bereich / A_eff. |

Neu dafür: Jeder planare Lauf schreibt `areas.txt` (Flächen der Kontaktflächen, gleiche Form wie
`snaps.txt`). Alte Läufe ohne `areas.txt` werden mit gleichen Flächen ausgewertet.
Die alten Werte stehen weiter in den Excel-Dateien (Spalten `(count)`) und in
`compute_measures(...)['A_eff_count' | 'p_eff_count']`.

**Nicht betroffen:** Paper-Skripte (Sinus/Hexagon) nutzen `src/blocks/sinus_block/post_mbd.py` und
`src/blocks/run_mbd.py` mit unveränderten Definitionen und Zielfunktion.

**Prüfung der Netzunabhängigkeit** (künstliches Druckfeld, 50 Flächen × 3 Blöcke): dasselbe Feld
auf ein ungleichmäßig verfeinertes Netz verteilt → A_eff neu 0.763 → 0.763 (exakt), A_eff alt
0.763 → 0.754. p_eff ändert sich minimal (0.672 → 0.671), weil die Maske nur ganze Flächen enthält.

### 9.2 Vergleichstabellen

„alt“ = Anzahl/globales Mittel, „neu“ = Fläche/Blockmittel. p_max ist bei beiden Definitionen
gleich (hängt nur von der Zielfunktion ab). Drücke in MPa bei q = 0.01 MPa.

**Oktaeder** (Decke, Rahmen fixiert, `support='frame'`): Alle Kontaktdreiecke sind exakt gleich
groß → `force` und `pressure` liefern identische Drücke (max. Abweichung 1.5e-15), A_eff alt = neu.
Nur p_eff ändert sich (+1–2 %) durch das Mitteln pro Block.

| | A_eff alt | A_eff neu | p_eff alt | p_eff neu | p_max |
|---|---|---|---|---|---|
| octahedron 4×4, ref 2 | 0.546 | 0.546 | 0.0318 | 0.0316 | 0.0586 |
| octahedron 4×4, ref 4 | 0.551 | 0.551 | 0.0314 | 0.0313 | 0.0638 |
| irr h = 0.2 | 0.403 | 0.403 | 0.2624 | 0.2654 | 0.8451 |
| irr h = 0.3 | 0.399 | 0.399 | 0.2361 | 0.2392 | 0.8070 |
| irr h = 0.4 | 0.394 | 0.394 | 0.2062 | 0.2093 | 0.7389 |
| irr h = 0.5 | 0.390 | 0.390 | 0.1770 | 0.1800 | 0.6535 |
| irr h = 0.6 | 0.388 | 0.388 | 0.1509 | 0.1536 | 0.5685 |
| irr h = 0.7 | 0.390 | 0.390 | 0.1288 | 0.1311 | 0.4826 |
| irr h = 0.8 | 0.397 | 0.397 | 0.1107 | 0.1129 | 0.4350 |
| irr h = 0.9 | 0.408 | 0.408 | 0.0964 | 0.0984 | 0.3891 |
| irr h = 1.0 | 0.431 | 0.431 | 0.0851 | 0.0866 | 0.3243 |

**Versatile** (p4, Decke 10×10, ref 4, `support='implicit'`): Dreiecksflächen variieren um Faktor
1.7–2.0. „bisher“ = Zielfunktion `force` + alte Kennzahlen, „jetzt“ = `pressure` + neue Kennzahlen;
dazwischen die Einzeleffekte.

| h | A_eff bisher | A_eff (force, neu) | A_eff jetzt | p_eff bisher | p_eff (force, neu) | p_eff jetzt | p_max force | p_max pressure |
|---|---|---|---|---|---|---|---|---|
| 1√2/16 | 0.483 | 0.484 | 0.500 | 0.9891 | 0.9442 | 0.9283 | 2.3800 | 2.6853 |
| 2√2/16 | 0.445 | 0.433 | 0.442 | 0.4634 | 0.4536 | 0.4419 | 1.9307 | 2.1317 |
| 3√2/16 | 0.419 | 0.396 | 0.384 | 0.3701 | 0.3639 | 0.3568 | 1.9684 | 2.2054 |
| 4√2/16 | 0.409 | 0.376 | 0.366 | 0.3515 | 0.3461 | 0.3381 | 2.5919 | 2.1707 |
| 5√2/16 | 0.402 | 0.364 | 0.359 | 0.3485 | 0.3427 | 0.3350 | 2.7663 | 2.3490 |
| 6√2/16 | 0.395 | 0.357 | 0.352 | 0.3463 | 0.3403 | 0.3339 | 2.7230 | 2.3630 |
| 7√2/16 | 0.390 | 0.352 | 0.347 | 0.3425 | 0.3366 | 0.3312 | 2.6144 | 2.2944 |
| 8√2/16 | 0.356 | 0.325 | 0.324 | 0.3351 | 0.3304 | 0.3232 | 2.2325 | 1.9578 |

**Bisquare** (p4, Decke 10×10, ref 4, `support='implicit'`):

| h | A_eff bisher | A_eff (force, neu) | A_eff jetzt | p_eff bisher | p_eff (force, neu) | p_eff jetzt | p_max force | p_max pressure |
|---|---|---|---|---|---|---|---|---|
| 1√2/16 | 0.542 | 0.543 | 0.560 | 1.1950 | 1.1893 | 1.1724 | 5.9473 | 5.2060 |
| 2√2/16 | 0.511 | 0.502 | 0.506 | 0.6415 | 0.6288 | 0.6319 | 3.5160 | 2.9131 |
| 3√2/16 | 0.469 | 0.461 | 0.463 | 0.4726 | 0.4596 | 0.4613 | 2.9840 | 2.2922 |
| 4√2/16 | 0.451 | 0.445 | 0.448 | 0.3900 | 0.3810 | 0.3783 | 2.4480 | 1.7952 |
| 5√2/16 | 0.444 | 0.435 | 0.443 | 0.3455 | 0.3385 | 0.3303 | 2.0674 | 1.4914 |
| 6√2/16 | 0.439 | 0.427 | 0.440 | 0.3176 | 0.3114 | 0.2989 | 1.8037 | 1.4282 |
| 7√2/16 | 0.436 | 0.422 | 0.433 | 0.2950 | 0.2906 | 0.2769 | 1.6017 | 1.4034 |

Erzeugt aus `outputs/planar/*_p4_ceiling_4_10x10_h*` (`force`) und `…_pressure` (`pressure`).

**Einordnung:**
- Bei gleich großen Dreiecken (Oktaeder) ändert sich nur p_eff um 1–2 % (Mittel pro Block).
- Bei Versatile/Bisquare ändern sich A_eff um bis zu 4 Prozentpunkte und p_eff um bis zu 6 %. Die
  **Trends über h bleiben gleich**: A_eff und p_eff fallen mit h, bei Bisquare stetig.
- p_max reagiert am stärksten auf die Zielfunktion, in beide Richtungen: Versatile h = 1√2/16
  2.38 → 2.69 (+13 %), sonst meist kleiner mit `pressure` (Bisquare bis −27 %, Versatile bis −16 %).
  Die Spitzen liegen auf einzelnen Elementen, deren Größe bei `force` mitbestimmt, wie viel Kraft
  sie bekommen. Für p_max ist die Wahl der Zielfunktion also besonders wichtig.
- Die alten gespeicherten Ergebnisse von Versatile (Ordner ohne `ceiling`, vor diesem Branch
  gerechnet) weichen ab h = 5√2/16 auch bei gleicher Zielfunktion leicht ab (z.B. A_eff 0.376 statt
  0.356 bei h = 8√2/16). Ursache sind die Korrekturen aus Abschnitt 2 (Normalen, Flächen), nicht das
  Kontaktmodell: Mit dem aktuellen Code liefern `matching` und `intersection` identische Drücke
  (geprüft für h = 4√2/16 und 5√2/16, 4×4, ref 2: max. Abweichung 3e-16).

### 9.3 Diagramme und Dateien

- `scripts/planar/plot_h_sweep.py`: Einfluss von h auf A_eff, p_eff/q, p_max/q, ein Feld pro Größe
  (keine zwei y-Achsen). Ergebnisse in `outputs/planar/analysis/<block>_h_sweep.png|.pdf` für
  irreguläres Oktaeder, Versatile und Bisquare.
  - Achtung beim Oktaeder: `irr_octahedron` normiert die Blockhöhe auf 1, die Grundfläche wächst mit
    1/h. Ein Teil des Druckanstiegs bei kleinem h ist reine Maßstabswirkung (mehr Last pro Block).
    Versatile/Bisquare haben dagegen für alle h dieselben Abmessungen (2 × 2 × 1).
- Excel: `results_irr_octahedron_frame_pressure.xlsx`, `results_versatile_pressure.xlsx`,
  `results_bisquare_pressure.xlsx` (mit alten Kennzahlen als Zusatzspalten).
- Neu gerechnete Ordner (`outputs/`, nicht im Repo): alle Oktaeder-Läufe mit `force` und `pressure`,
  Versatile/Bisquare 10×10 ref 4 mit `force` (Ordner `…_ceiling_…`) und `pressure`
  (`…_pressure`). Alle 52 Läufe im Gleichgewicht.

### 9.4 Weitere Änderungen in diesem Schritt

- `scripts/planar/mbd_planar.run` gibt den Ergebnisordner in `info['out_dir']` zurück;
  `contact_method='matching'` setzt die Zielfunktion automatisch auf `force` (nur diese wird dort
  unterstützt).
- `scripts/planar/post_results.py`: nutzt die neuen Kennzahlen; Beispiele auf `pressure` bzw.
  `support='frame'` umgestellt.
- `src/blocks/run_mbd.py`:
  - `plot_and_save_pc` plottet nur, wenn `show`, `save` oder `html` gesetzt ist (vorher wurde
    immer ein VTK-Fenster angelegt, das ohne Bildschirm abstürzt; für die Paper-Skripte ohne
    Wirkung, dort ist immer eine Ausgabe aktiv).
  - `test_interlocking` gibt das Ergebnis zurück (vorher `None`).

---

## 10. Web-Oberfläche (`webapp/`)

Wunsch: Parameter einstellen, rechnen und die Ergebnisse (HTML-Plot) direkt ansehen.

- `webapp/app.py` (Streamlit), Start: `python -m streamlit run webapp/app.py` (Windows:
  `py -3.10 -m streamlit run webapp/app.py`). Anleitung in `webapp/README.md`.
- **Planar**: alle Blocktypen, Anordnungen, h, n × m, ref, BVP, Kontaktdruck oder
  Interlocking-Test, Modelloptionen.
- **Tubular (Paper)**: Sinus- oder Hexagon-Block, BVPs pipe/tunnel/pillar/beam/shaft, n, t, Lagen,
  Amplitude/Frequenz/Verschiebung, Netz, Last, Interlocking-Test vollständig oder wie im Paper.
  Neuer Einstiegspunkt `scripts/tubular/run_cli.py` setzt die Parameter genau wie die
  Paper-Skripte. Geprüft: Sinus pipe n = 4 → A_eff 28.3 %, p_eff 0.189, p_max (Blockmittel) 0.467
  wie Tabelle 5 im Paper; Sinus pillar identisch zum gespeicherten Paper-Ergebnis (3e-16);
  Hexagon tunnel → unterdrückter Mechanismus.
- **Warum jede Rechnung ein eigener Prozess** (`scripts/planar/run_cli.py`,
  `scripts/tubular/run_cli.py`): Die Configs sind Modul-Dicts, die die Skripte verändern; VTK hält
  Zustand; ein Absturz (z.B. VTK ohne Bildschirm) reißt so nicht die Seite mit. Die Ausgabe wird
  live angezeigt.
- **Nur neue Rechnungen** (auf Wunsch): Jede Rechnung wird in einen neuen Ordner
  `outputs/webapp/<Datum>_<Uhrzeit>/` geschrieben, vorhandene Ergebnisse werden weder gelesen noch
  überschrieben. Die Seite zeigt die Rechnungen der aktuellen Sitzung (Liste in der Seitenleiste).
- Fehlen dem Python der Seite Pakete, zeigt die Seite, welches Python läuft und wie man die Pakete
  installiert (Anlass: Start mit dem WSL-Python ohne cvxpy).
- `.streamlit/config.toml`: Nutzungsstatistik von Streamlit aus, größere Nachrichten erlaubt
  (große 3D-Plots).
- `requirements.txt`: `streamlit`.
- Geprüft: alle Formulare und Rechnungen (planar, Sinus, Hexagon, mit/ohne Plots) über die
  Streamlit-Testumgebung und den echten Server in WSL; von dir unter Windows gestartet.

---

## 11. Web-Oberfläche: Parameterstudie, feste Modelloptionen, vorhandene Ergebnisse, Englisch; Aufräumen von `outputs/`

### 11.1 Web-Oberfläche (`webapp/app.py`)

- **Sprache Englisch** (Wunsch).
- **Parameterstudie** (Wunsch: Studie „wie vorher“): Alle Einstellungen bleiben fest, ein Parameter
  wird variiert (planar: h, n = m, ref; tubular: n, t, Lagen, a, f, s). Es werden alle Läufe neu
  gerechnet (Ordner `outputs/webapp/<Zeit>_study/`), danach Diagramm A_eff, p_eff/q, p_max/q über dem
  Parameter (`plot_h_sweep`, jetzt auch mit englischen Achsen), Tabelle und Excel-Download; beim
  Interlocking-Test eine Ergebnistabelle.
  - Die Werteliste wird mit einem eigenen kleinen Parser gelesen (nur Zahlen, `+ - * / **`,
    `sqrt`, `pi`), **nicht mit `eval`**: Wird die Seite im Netz geteilt, könnte sonst jeder mit dem
    Link Code auf dem Rechner ausführen.
- **Vorhandene Ergebnisse** wieder anzeigbar (nach dem Aufräumen, Wunsch): alle Ergebnisordner in
  `outputs/` (planar, Paper, Web) mit Filter, sowie die h-Serien der planaren Läufe als Diagramm.
- **Modelloptionen fest** (Wunsch nach Rückfrage, weil die Optionen meist dasselbe Ergebnis lieferten):
  - Kontakterkennung `intersection`: Bei allen vorhandenen Blöcken passen die Netze benachbarter
    Blöcke exakt aufeinander, `matching` liefert dann identische Drücke (~1e-16); bei nicht
    passenden Netzen ist nur `intersection` richtig.
  - Zielfunktion `pressure`: bei gleich großen Kontaktdreiecken (Oktaeder) identisch mit `force`,
    sonst netzunabhängig (§5, §9).
  - Auflager nach Blocktyp: `frame` für Oktaeder (sonst Schein-Auflager an den freien Hälften der
    Seitenflächen, §8.1), `implicit` für Versatile/Bisquare (alle Flächen ohne Partner liegen am
    Außenrand). Das gewählte Modell wird unter dem Formular angezeigt.
  - Im Code (`run_mbd_planar.py`, `mbd_planar.run`) bleiben alle Optionen erhalten.
- **brick / brick_inter entfernt** (Wunsch; erst wieder, wenn Wände betrachtet werden).
- **Hexagon-Block:** Kontaktdruck nur für tunnel wählbar. Der Hexagon-Block hat einen Mechanismus;
  für die anderen BVPs gibt es kein Gleichgewicht und der Solver suchte minutenlang (pipe nach
  > 5 min abgebrochen). Im Paper wurde der Kontaktdruck ebenfalls nur für tunnel berechnet.
- **Netz der tubularen Läufe wie in der BVP-Studie des Papers:** Sinus n_t = 2·(t // 3), Hexagon
  zusätzlich n_l = 160 // n (`scripts/tubular/run_cli.py`). Vorher nutzte der Hexagon-Block das
  gröbere Netz aus der Config (A_eff 79.3 % statt 79.2 %). Jetzt: Hexagon tunnel identisch zum
  gespeicherten Paper-Ergebnis (2e-15), A_eff 79.2 %, p_eff 0.039, p_max 0.103 wie Tabelle 5.

### 11.2 Namenskonvention der planaren Ergebnisordner

`<block>_<group>_<bvp>_<ref>_<n>x<m>[_h<h>][_frame][_force]` — Suffixe nur noch für die
Nicht-Standard-Optionen. Da `pressure` jetzt Standard ist, entfällt `_pressure`; Läufe mit `force`
bekommen `_force` (`scripts/planar/mbd_planar.get_run_name`; `post_results.py` entsprechend).

### 11.3 Aufräumen von `outputs/` (Wunsch)

Nichts gelöscht, sondern verschoben nach
`../interlocking-mechanics-outputs-archiv-2026-11-12/` (neben dem Repo, 816 MB; kann gelöscht
werden, wenn nichts mehr gebraucht wird).

- **Behalten und umbenannt** (`_pressure` entfernt): alle aktuellen Läufe (Kontakte exakt,
  `pressure`): Versatile 10×10 ref 4 (8 h-Werte), Bisquare 10×10 ref 4 (7 h-Werte), irreguläres
  Oktaeder 6×6 ref 4 `_frame` (9 h-Werte), Oktaeder 4×4 ref 2/4 `_frame`, zwei kleine Versatile-Läufe.
  Die Ergebnisse des Interlocking-Tests (`interlocking.json`, unabhängig von der Zielfunktion) wurden
  aus den alten `force`-Ordnern übernommen.
- Excel: `results_irr_octahedron.xlsx`, `results_versatile.xlsx`, `results_bisquare.xlsx` (aktuell);
  Diagramme `analysis/*_h_sweep.png|pdf`.
- **Archiviert:** Ordner mit alten Namen (vor diesem Branch, ohne BVP im Namen), alle `force`-Läufe,
  Bricks/Wände, alte Excel-/PDF-Dateien, alte Plots in `analysis/`, Testläufe der Web-Seite.
- **Nicht angefasst:** `outputs/paper2026/` (Referenz des Papers) und `outputs/GAMM/` (anderes
  Projekt).

---

## 12. Vergleich mit den FEM-Ergebnissen für den Versatile Block (Goertzen et al. 2025)

Quelle: T. Goertzen, D. Macek, L. Schnelle, M. Weiß, S. Reese, H. Holthusen, A. C. Niemeyer:
*Influence of block arrangement on mechanical performance in topological interlocking assemblies:
A study of the versatile block*, IJSS 306 (2025) 113102 (PDF `versatile.pdf`, nicht im Repo).

### 12.1 Was vergleichbar ist

FEM im Paper: 8×8 innere Blöcke + fester Rahmen (10×10), p1/pg/p4, elastisch (Stahl), reibungsfrei,
weicher Kontakt, Flächendruck 1.5 bar von oben, Abaqus/Explicit quasi-statisch. Ergebnisse nur als
Abbildungen (Kontaktdruck Fig. 12–14, logarithmische Farbskala 10³–10⁸ Pa), Zahlen nur für
Durchbiegung und Spannungen (vom Starrkörpermodell nicht berechenbar).

Vergleichbar ist der **Lastabtrag auf den Rahmen**: welche Rahmenblöcke Last aufnehmen, in der
unteren oder oberen Ebene, mit welcher Symmetrie (Fig. 12, 13), und die Werte der Interlocking
Flows (Fig. 6–8, Summe = Anzahl innerer Blöcke = 64).

MBD-Modell dafür: Versatile 10×10, `support='frame'` (36 Randblöcke fest), Decke, `pressure`,
ref 2. Neues Skript `scripts/planar/frame_load.py`: pro Rahmenblock die Vertikalkraft und der
Betrag der Normalkraft, getrennt nach Kontakten in der unteren (z < 1/2) und oberen Hälfte,
normiert auf die Last eines inneren Blocks. Dafür gibt `solve_contacts` jetzt die Kraft jedes
Kontaktelements zurück (`contacts['lam']`, `contacts['columns']`). Bilder:
`outputs/planar/analysis/versatile_frame_load_10x10.png` (vertikal),
`versatile_frame_normal_force_10x10.png` (Normalkraft).

### 12.2 Ergebnis

Alle drei im Gleichgewicht. Normalkraft auf den Rahmen (Summe, Einheit: Last eines inneren Blocks):

| | untere Hälfte | obere Hälfte | FEM obere Ebene am Rahmen |
|---|---|---|---|
| p1 | 456 | 226 | hoch (rechter und oberer Rand) |
| pg | 296 | 95 | hoch (rechter Rand) |
| p4 | 248 | 7 | niedrig |

- **Die gesamte Vertikallast** geht in allen drei Fällen über Kontakte der unteren Hälfte in den
  Rahmen. In der oberen Hälfte wirken nur horizontale Druckkräfte (Gewölbewirkung) – genau die
  Drücke, die die FEM in der oberen Ebene am Rahmen zeigt.
- **p1:** MBD: untere Ebene zwei benachbarte Ränder stark, obere Ebene die beiden
  gegenüberliegenden; Spiegelsymmetrie zur Diagonalen; die Last steigt entlang der Ränder vom
  gemeinsamen Eck weg an (bis 8.6 Blocklasten vertikal). FEM: „bottom plane: left and lower edges,
  top plane: right and top edges“, Diagonalsymmetrie, roter Bereich am unteren Rand rechts (vom Eck
  weg). Übereinstimmung. Die Interlocking Flows sagen dagegen das Maximum *am* Eck voraus (7 → 1);
  das Paper schreibt selbst, dass die Größe bei p1 nicht zur FEM passt.
- **pg:** MBD: untere Ebene ein Rand durchgehend, die beiden angrenzenden Ränder nur jeder zweite
  Block (vertikal), obere Ebene der gegenüberliegende Rand. FEM: „bottom: left, lower and upper
  edges, only every second block at lower and upper edges; top: right edge“. Übereinstimmung.
  Auch hier nimmt die Last an den abwechselnden Rändern vom durchgehenden Rand weg zu, wie im
  FEM-Bild (roter Bereich am oberen Rand rechts), entgegen den Interlocking Flows.
- **p4:** MBD: alle vier Ränder, jeder zweite Block (1.6 / 5.6 / 7.1 / 4.0 je Rand),
  vierzählige Drehsymmetrie, obere Ebene fast lastfrei. FEM: identische Beschreibung.
  Interlocking Flows: gleiches Muster, ähnliche Werte.
- **Orientierung:** Zunächst stimmten die Muster nur bis auf eine Drehung überein (p1 und p4 um
  90°, pg um 180°). Die Anordnungen sind inzwischen gedreht und stimmen ohne Transformation mit dem
  Paper überein (§14).

### 12.3 Warum kein direkter Vergleich der Kontaktdrücke

- Die FEM-Drücke liegen nur als Bilder mit logarithmischer Skala vor (eine Farbe = eine
  Zehnerpotenz); ablesbar ist höchstens die Größenordnung.
- Die Druck*verteilung innerhalb* einer Kontaktfläche ist in beiden Modellen etwas anderes: In der
  FEM entsteht sie aus der Verformung, mit Spitzen an Kanten und Ecken (bis 2.5·10⁸ Pa bei 1.5·10⁵ Pa
  Last, also ~1600 q), die von Netz und Kontaktsteifigkeit abhängen. Im Starrkörpermodell ist sie
  nicht bestimmt, die Zielfunktion wählt eine aus (min ∫p² dA verteilt möglichst gleichmäßig).
  Lokale Drücke und p_max sind daher nicht vergleichbar.
- Vergleichbar sind integrale Größen: Kräfte pro Kontaktfläche, pro Block oder pro Rahmenblock, und
  wo Last übertragen wird. Für einen quantitativen Vergleich bräuchte man die FEM-Ergebnisdaten
  (Abaqus-ODB); auf Zenodo (10.5281/zenodo.10246034) liegen nur die Eingabedateien.

---

## 13. Plots: Farbskala und Scheinkanten

- **Farbskala** (Wunsch: Farbunterschiede besser sichtbar): Bisher reichte die Skala linear vom
  kleinsten bis zum größten Druck; wenige Spitzen drückten fast alle Flächen in die untersten
  Farbstufen. Neu für planare Plots (`scripts/planar/config.py`: `'clim_percentile'`): obere
  Grenze = Perzentil der Drücke, Werte darüber in der Farbe des Maximums. Erst 98. Perzentil mit
  eigener dunkelroter Farbe; auf Wunsch (zu viel Dunkelrot) jetzt 99. Perzentil ohne eigene Farbe und ohne
  „above“-Eintrag in der Legende (Werte darüber werden auf die Farbe des Maximums begrenzt). Mit
  `'clim_percentile': None` oder einem festen `'clim'` wie bisher. Paper-Skripte unverändert (dort
  ist der Schlüssel nicht gesetzt).
- **Scheinkanten** (Wunsch: Kanten der ursprünglichen Dreiecke bei den parametrisierten Blöcken
  entfernen): Die Dreiecke der Blockgeometrien haben keine einheitliche Umlaufrichtung (rund die
  Hälfte ist andersherum nummeriert; für die Rechnung werden die Außennormalen separat bestimmt,
  deshalb hatte das keinen Einfluss auf die Ergebnisse). Die Kantenerkennung der Plots berechnet die
  Normalen aber aus der Umlaufrichtung und sah an den Nähten gegensätzlich nummerierter, koplanarer
  Dreiecke einen 180°-Knick. Neu: `sharp_edges` in `src/engine/plots.py` ordnet die Dreiecke vor der
  Kantenerkennung einheitlich (nur für den Plot). Beispiel Versatile h = √2/16, ref 2:
  104 → 64 Kantensegmente; in der Draufsicht verschwinden alle Nähte auf Ober- und Unterseite, die
  echten Blockkanten bleiben.
- Gilt automatisch auch für die Web-Oberfläche. Bereits vorhandene Plots in `outputs/` sind noch mit
  der alten Darstellung erzeugt; neu erzeugen heißt neu rechnen.

---

## 14. Orientierung von p1, pg, p4 wie im Versatile-Paper

Wunsch: Die Anordnungen sollen mit Goertzen et al. (2025) übereinstimmen.

- Die Anordnungen entstanden im Code aus Drehungen der Blöcke (keine Spiegelungen), lagen aber
  gegenüber den Abbildungen im Paper verdreht.
- **p4 war keine echte p4-Anordnung um das Zentrum** (Hinweis von dir: im Paper ist das „X“ durch
  die Mitte zu sehen, bei uns nicht). Die Drehwinkel der vier Blöcke um einen Gitterpunkt liefen im
  Code im Uhrzeigersinn (−90° pro Schritt), die Positionen gegen den Uhrzeigersinn. Die Blöcke
  passten zwar lückenlos zusammen, die Assembly war aber um ihr Zentrum nur zweizählig symmetrisch
  (Test: 90°-Drehung um das Zentrum bildet 0 von 100 Blöcken auf Blöcke ab). Neu
  (`create_p4`): Winkel a0, a0+90°, a0+180°, a0+270° gegen den Uhrzeigersinn → vierzählig
  symmetrisch (100/100), durchgehende Fugen auf beiden Diagonalen durch das Zentrum (38 statt 12–16
  Längeneinheiten, das „X“). Gültig (ohne Überlappung) sind a0 = 0 und 180°; a0 = 180°
  (`P4_START_ANGLE`) gibt die belasteten Rahmenblöcke wie die Interlocking Flows in Fig. 6
  (unten gerade, oben ungerade, links ungerade, rechts gerade Positionen). Interlocking-Test:
  Versatile, Versatile-param, Bisquare-param 6×6 verzahnt. Die frühere p4-Anordnung ist damit
  eine andere Assembly; die früheren p4-Ergebnisse (h-Serien) gelten für diese andere Anordnung und
  wurden neu gerechnet.
- **Überlappungsprüfung** (Volumen, 6×6): Versatile p1/pg/p4 überlappungsfrei (bei h = √2/2 ca. 1 %
  bei allen drei Gruppen gleich, vermutlich Artefakt der dort zusammenfallenden Eckpunkte, nicht
  weiter geprüft). **Bisquare mit p1 und pg überlappt deutlich (7–13 % des Volumens), mit p4 nicht**
  – schon vor diesen Änderungen. In der Web-Oberfläche ist Bisquare daher nur noch mit p4 wählbar.
- p1 und pg: bestimmt über den Lastabtrag auf den Rahmen (§12), weil der die Orientierung eindeutig festlegt:
  welcher Rand durchgehend trägt und welche Rahmenblöcke (gerade/ungerade Position) Last
  bekommen. Ergebnis: jeweils eine reine Drehung der ganzen Assembly um die z-Achse, p1 90°, pg 180°
  (gegen den Uhrzeigersinn, in der Darstellung mit achsparallelen Unterseiten wie im Paper).
- Umsetzung: `GROUP_ROTATION` und `rotate_placement` in `src/blocks/planar_block/assembly.py`
  (Position und Drehwinkel jedes Blocks). Gilt für alle Blöcke mit diesen Gruppen (Versatile,
  Bisquare).
- Prüfung (`python -m scripts.planar.frame_load`, Versatile 10×10, Rahmen fest), jetzt ohne
  Transformation:
  - p1: untere Ebene linker und unterer Rand, obere Ebene rechter und oberer Rand,
    Spiegelsymmetrie zur Diagonalen links unten – rechts oben (FEM Fig. 12 ✓).
  - pg: linker Rand durchgehend, unten Rahmenblöcke an geraden, oben an ungeraden Positionen;
    obere Ebene rechter Rand (FEM ✓, Interlocking Flows Fig. 8 ✓).
  - p4 (neue Anordnung): unten gerade, oben ungerade, links ungerade, rechts gerade Positionen
    (Interlocking Flows Fig. 6 ✓), vierzählige Drehsymmetrie um das Zentrum, obere Ebene nahezu
    lastfrei (FEM ✓).
- Für p1 und pg ändert die Drehung mechanisch nichts: Gleichgewicht, Kennzahlen und Kraftsummen
  sind unverändert (z.B. Normalkraft auf den Rahmen p1 456 / 226, wie vorher), nur
  Blockreihenfolge und Lage im Koordinatensystem ändern sich. p4 ist eine neue Anordnung (s.o.).
- Die h-Serien von Versatile und Bisquare (p4) wurden danach neu gerechnet (neue Plots mit
  Farbskala und ohne Scheinkanten, §13), ebenso das irreguläre Oktaeder (nur wegen der Plots).
- **Neu gerechnet** (alle 24 Läufe im Gleichgewicht; Plots mit neuer Farbskala und ohne
  Scheinkanten, im 3D-Plot der Versatile-p4-Decke ist das „X“ hoher Drücke durch die Mitte sichtbar):
  - Versatile p4 10×10 ref 4, neue Anordnung (`results_versatile.xlsx`): A_eff 0.500 / 0.434 /
    0.380 / 0.367 / 0.360 / 0.354 / 0.349 / 0.326 und p_eff 0.926 … 0.323 für h = 1…8·√2/16 —
    gegenüber der alten Anordnung A_eff höchstens ~1 Prozentpunkt, p_eff < 1 % anders, p_max bis
    ca. 6 % (z.B. h = 8√2/16: 1.96 → 1.84). Die Trends über h bleiben gleich.
  - Bisquare p4: Ergebnisse identisch zur alten Anordnung. Der Bisquare-Block ist offenbar
    symmetrisch unter 180°-Drehung, dann ergeben die alte und die neue Winkelregel dieselbe
    Assembly.
  - Irreguläres Oktaeder: nur neue Plots, Werte unverändert.
  - `frame_load` mit neuer p4-Anordnung: Normalkraft auf den Rahmen unten 254, oben 14 (vorher
    248 / 7); p1 und pg unverändert.

---

## 15. Starfish-Block (p6, Schnelle et al. 2026)

**Neu:** Block aus *Influence of a generative parameter on the mechanical performance of
topological interlocking assemblies of a hexagonal block* (Procedia CIRP 142, 2026, `starfish.pdf`).

- Geometrie `starfish` (`src/blocks/planar_block/geometry.py`): Gleichseitiges Dreieck
  (Fundamentalbereich von p6, Ecke 1 = 6-zähliges Drehzentrum im Ursprung). Auf jeder Kante werden
  die Punkte bei ¼ (nach innen) und ¾ (nach außen) um d verschoben (Fig. 1); jede Kante ist danach
  punktsymmetrisch zu ihrem Mittelpunkt, das verformte Dreieck ist wieder ein Fundamentalbereich.
  Unterseite: Dreieck, Oberseite: verformtes Dreieck (Last auf der verformten Seite wie im Paper).
- Skalierung auf Höhe 1 mit den Proportionen des Papers (20 mm, 800 mm², a = 42.9829 mm):
  **h = d / 20 mm**, 0 ≤ h < √3a/4 = 0.9306 (d < 18.6 mm, sonst Selbstdurchdringung → Fehler).
  Volumen 2 wie der Versatile Block.
- Seitenflächen: lineare Interpolation zwischen entsprechenden Punkten; die nicht ebenen Vierecke
  werden am Schwerpunkt in 4 Dreiecke geteilt. Damit ist die Triangulierung invariant unter den
  p6-Symmetrien und benachbarte Blöcke haben identische Kontaktflächen (mit nur 2 Dreiecken pro
  Viereck hätten die Nachbarn die andere Diagonale → Lücken/Durchdringungen). Oberseite (nicht
  konvex) per Ear Clipping, Unterseite als Fächer.
- Anordnung `p6` (`create_p6` in `assembly.py`): Sechseck mit Seitenlänge n Blöcke (6n² Blöcke),
  `m` wird ignoriert (= n gesetzt).
- **Auflagermodell wie beim Versatile Block** (`support='implicit'`, Standard): Beide Blöcke
  schließen lückenlos aneinander, die freien Außenflächen wirken als starrer Rahmen. **n = 2 ist die
  Assembly des Papers** (24 innere Blöcke; die 30 festen Rahmenblöcke des Papers entsprechen dem
  starren Rand). Geprüft: n = 2 `implicit` und n = 3 `support='frame'` mit den 30 Rahmenblöcken
  liefern identische Drücke (Abweichung < 1e-14, d = 1, 8, 18.5 mm) und dasselbe
  Interlocking-Ergebnis. (Zuerst hatte ich `support='frame'` mit n = 3 gewählt; umgestellt, damit
  Versatile und Starfish einheitlich behandelt werden.)
- Neue Option `frame_blocks='perimeter'` (`run_mbd_planar.py`), nur für `support='frame'`: alle
  Blöcke, die den äußeren Rand berühren, auch nur mit einer Ecke (für p6 dann Standard);
  `boundary` würde nur die 18 Blöcke mit einer Kante am Rand liefern, nicht den 30er-Rahmen des Papers.
- `cone_interlocking_test` (`src/engine/mbd.py`): wenn CLARABEL am LP scheitert (passierte bei
  h = 0), wird mit SCIPY (HiGHS) erneut gelöst. Vorher brach der Lauf mit `SolverError` ab.
- `PARAMETRIZED_BLOCKS` steht jetzt in `geometry.py` (eine Liste statt zwei).
- Web-Oberfläche: `starfish` mit `p6`, Eingabe n = Seitenlänge des Sechsecks (Standard 2),
  Auflagermodell wie Versatile, Parameterstudie mit den d-Werten des Papers.

**Prüfung:**
- Volumen 2.000 für h = 0 … 0.925, Oberfläche geschlossen, Normalen der Oberseite +z.
- n = 3, ref 1: 30 Rahmen-, 24 innere Blöcke; alle 3456 Kontaktelemente sind identische
  Dreieckspaare, keine teilweise berührten Flächen (für h > 0).
- Interlocking-Test (cone_mechanism): h = 0 nicht verzahnt (30 Gleitmoden, freier Mechanismus),
  h = 0.05, 0.4, 0.925 verzahnt — wie im Paper (d = 0 kein Interlocking).
- Gleichgewicht n = 3, ref 2 für d = 1, 3, 5, 8, 10, 15, 18.5 mm: alle im Gleichgewicht
  (Residuum < 1e-13), p_max 2.91 / 1.07 / 0.73 / 0.51 / 0.42 / 0.29 / 0.26 (q = 0.01).
  Der Druck fällt monoton mit d; das Minimum bei d ≈ 10 mm im FEM des Papers kommt von
  Spannungskonzentrationen in dünnen Bereichen, die das Starrkörpermodell nicht abbildet.
- Plot d = 8 mm entspricht Fig. 2(d) des Papers.
- Vollständiger d-Sweep des Papers (d = 1 … 11, 15, 18.5 mm), n = 2, ref 3, `implicit`
  (`outputs/planar/starfish_p6_ceiling_3_2x2_h*/`): alle im Gleichgewicht,
  p_max = 3.05 / 1.48 / 1.10 / 0.89 / 0.76 / 0.66 / 0.59 / 0.53 / 0.48 / 0.45 / 0.41 / 0.31 / 0.26
  (q = 0.01), monoton fallend.
- Sweep mit ref 4 (wie die anderen Blöcke), n = 2, `implicit`: alle 13 Läufe im Gleichgewicht
  (Residuum < 2e-13). Kennzahlen in `outputs/planar/results_starfish.xlsx`, Plot
  `outputs/planar/analysis/starfish_h_sweep.png` (x-Achse d [mm]); in `post_results.py` und
  `plot_h_sweep.py` eingetragen. Gegenüber ref 3 ändern sich A_eff und p_eff um < 0.1 %, p_max um
  2–4 %. A_eff: 57.8 % (d = 1) → Minimum 48.3 % (d = 5) → 50.0 % (d = 15) → 49.4 % (d = 18.5);
  p_eff und p_max fallen monoton. Einordnung siehe `IDEEN_MBD.md`.

---

## 16. Oktaeder: abgeschnittenes Oktaeder ersetzt `octahedron` und `irr_octahedron`

**Neu:** `octahedron` wird wie im Skript `cut_octahedra_volume` (CIRP-Paper) erzeugt und ist jetzt
parametrisiert. Die bisherigen Blöcke `octahedron` (Höhe 1, ohne Parameter) und `irr_octahedron`
sowie die Gruppe `irr_octa` wurden entfernt.

- Geometrie (`geometry.py`, `octahedron`): reguläres Oktaeder mit dem Volumen des Versatile Blocks
  (2 in den normierten Einheiten, entspricht `target_volume=0.016` des Skripts; volle Höhe
  H = 1.3218). **h = behaltener Anteil der Höhe** (frac): Mittelteil zwischen z1 = (1 − h)/2·H und
  H − z1 (Sechseck unten/oben, 6 ebene Trapeze), nach z = 0 verschoben und nur in z auf das
  Volumen 2 skaliert. Triangulierung wie im Skript (Fächer um die Mittelpunkte der Sechsecke und
  der Seitenvierecke). h = 1: volles Oktaeder; die zusammenfallenden Punkte werden zusammengeführt
  (wie trimesh mit `process=True`). trimesh wird nicht benötigt.
- Anordnung (`assembly.py`, `create_octahedron_assembly`): wie `octahedron_interlocking`, nur
  Translationen, Gitter aus der Kantenlänge des vollen Oktaeders (unabhängig von h). Der Spalt
  1e-5 des Skripts entfällt (exakte Kontakterkennung). Der Rahmen des Skripts (erste/letzte Reihe
  und Spalte) ist genau der Rahmen von `support='frame'`, `frame_blocks='boundary'`.
- Skripte (`mbd_planar.py`, `post_results.py` → `results_octahedron.xlsx`, `plot_h_sweep.py` →
  `analysis/octahedron_h_sweep.png`), Web-Oberfläche und READMEs angepasst.
- Alte Ergebnisse (`outputs/planar/irr_octahedron_*`, `octahedron_octa_*` ohne `_h`,
  `results_irr_octahedron.xlsx`) bleiben liegen, gehören aber zu den alten Geometrien.

**Prüfung:**
- Volumen 2.000000 für h = 1.0, 0.9, 0.5, 0.2 (ref 0 und 2), Oberfläche geschlossen; Höhe 1.3218
  (h = 1) bis 1.1802 (h = 0.2). Mit Volumen 0.016 Höhe 0.2417 bei h = 0.5 = Skript × 0.2
  (Maßstab (0.016/2)^(1/3)).
- 6×6, ref 1/2: 20 Rahmen- (Blöcke 0–6, 11, 12, 17, 18, 23, 24, 29–35) und 16 innere Blöcke,
  h = 1.0, 0.6, 0.2 verzahnt (cone_mechanism) und im Gleichgewicht.

---

## 17. `bisquare_param` heißt jetzt `tortuga`

- Der parametrisierte Bisquare-Block heißt im Code `tortuga` (Funktion `tortuga` in
  `geometry.py`, `PARAMETRIZED_BLOCKS`, Web-Oberfläche, `post_results.py`, `plot_h_sweep.py`,
  READMEs). Der nicht parametrisierte Block heißt weiterhin `bisquare`. Geometrie unverändert.
- Vorhandene Ergebnisse umbenannt, damit sie weiter gefunden werden:
  `outputs/planar/bisquare_param_*` → `tortuga_*` (7 Ordner),
  `outputs/webapp/*/bisquare_param_*` → `tortuga_*` (2 Ordner), Blocktyp und Pfade in den
  `info.json` angepasst, `results_bisquare.xlsx` → `results_tortuga.xlsx`,
  `analysis/bisquare_param_h_sweep.*` → `tortuga_h_sweep.*` (Plot mit neuem Titel neu erzeugt).
- Ältere Abschnitte dieses Protokolls verwenden noch den alten Namen `bisquare_param`.

---

## 18. Plots: Kontaktbereiche statt Dreiecke einfärben

**Problem:** Beim abgeschnittenen Oktaeder verlaufen die Ränder der Kontaktbereiche quer durch die
Dreiecke der Seitenflächen (Fächer um die Trapez-Schwerpunkte). Im Plot bekam jedes Dreieck den
über die ganze Fläche gemittelten Druck; teilweise berührte Dreiecke erschienen dadurch mit zu
niedrigem Druck (fleckige Ränder), obwohl der Kontaktbereich gleichmäßig belastet ist. Beim alten
Oktaeder lagen die Kontaktränder auf Netzkanten.

**Lösung:** `store_contact_regions` (`run_mbd_planar.py`) speichert für jeden Block die Polygone der
Kontaktelemente und Auflager mit ihrem eigenen Druck (Kraft / Fläche des Elements);
`plot_contact_regions` (`src/engine/plots.py`) färbt diese Polygone statt der Dreiecke. Teilweise
berührte Dreiecke werden nicht grau unterlegt (keine Überlagerung), die Blockkanten bleiben.
Option `plot_config['contact_regions']` (Standard `True`).

- Nur Darstellung: `snaps.txt`, `areas.txt` und die Kennzahlen sind unverändert (weiter pro Dreieck).
- Bei passenden Netzen (Versatile, Tortuga, Starfish) ist jedes Polygon genau ein Dreieck:
  Werte identisch (geprüft Versatile p4 4×4, Abweichung 0).
- Oktaeder-Sweep (ref 4) mit den neuen Plots neu gestartet.

---

## 19. Oktaeder: Standard h = 1; Web-Oberfläche: kein doppeltes h in Parameterstudien

- `octahedron` ohne `h_value` ist das volle Oktaeder (h = 1) in `mbd_planar.run` und
  `get_block_geometry`; in der Web-Oberfläche ist 1.0 vorbelegt (vorher 0.5).
- Parameterstudie in der Web-Oberfläche: Die Beschriftung enthielt den Wert aus dem Formular und
  den variierten Wert („… · h = 0.500 · h = 0.3 · …“). Der feste Wert des variierten Parameters
  wird jetzt aus der Beschriftung entfernt (`run_study`). Bereits gerechnete Studien dieser Sitzung
  behalten ihre alte Beschriftung.
- h-Sweep abgeschnittenes Oktaeder (h = 1.0 … 0.2, 6×6, ref 4, Rahmen fest, Plots mit
  Kontaktbereichen §18): alle im Gleichgewicht (Residuum < 1e-13). `results_octahedron.xlsx`,
  `analysis/octahedron_h_sweep.png`. Von h = 1 zu h = 0.2: A_eff 48 % → 67 %, p_eff 0.066 → 0.20,
  p_max 0.23 → 0.43 (q = 0.01). Je stärker abgeschnitten, desto gleichmäßiger, aber höher der Druck
  (kleinere geneigte Kontaktflächen bei gleichem Volumen).
