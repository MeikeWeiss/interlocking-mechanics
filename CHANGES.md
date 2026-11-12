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

- `force` (Default, wie im Paper): min Σλ².
- `pressure`: min Σλ²/A = ∫p² dA.
- *Warum optional:* Bei unterschiedlich großen Kontaktelementen hängt `force` vom Netz ab
  (Beispiel: mittlerer Druck 0.0060 → 0.0066 bei gemischtem Netz), `pressure` nicht (0.0060 in
  allen Varianten). Default unverändert, weil es eine methodische Entscheidung ist.
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
