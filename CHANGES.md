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
