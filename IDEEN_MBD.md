# Ideen: Verbesserung der MBD-Analyse (Stand 2026-11-13)

Auslöser: Starfish-Block (Schnelle et al. 2026, `starfish.pdf`). Im FEM des Papers werden
Mises-Spannung, Kontaktdruck und Verschiebung bis d ≈ 10 mm besser und danach wieder schlechter
(Fig. 3). In der MBD fallen die Kontaktdrücke dagegen monoton mit d (p_max 3.05 → 0.26,
p_eff 0.83 → 0.07 für d = 1 → 18.5 mm, n = 2, ref 3, `CHANGES.md` §15).

Die relative effektive Fläche A_eff ist nicht monoton: 0.578 (d = 1) → Minimum 0.483
(d ≈ 5–6) → Maximum 0.501 (d = 15) → 0.495 (d = 18.5). Das ist aber nicht das Optimum des
Papers: Das Extremum bei d ≈ 5 ist ein Minimum (ungünstigste Verteilung), und A_eff ist auf die
Kontaktfläche bezogen, die mit d um ca. 50 % wächst. Die absolute effektive Fläche steigt ab
d ≈ 4 stetig (3.24 → 4.90). Offen: Ist der kleine Abfall von d = 15 auf 18.5 (ca. 1 %) ein
Maximum der Gleichmäßigkeit zwischen 11 und 18.5 mm? Dafür müsste man mit Zwischenwerten
d = 12, 13, 14, 16, 17, 18 mm nachrechnen.

## Warum die MBD das Optimum nicht zeigt

1. **Starre Blöcke:** Die Materialdicke spielt keine Rolle. Ein dünner Sporn trägt genauso viel
   wie massives Material. Das Paper erklärt die Umkehr aber genau mit dünnen Bereichen und
   spitzen Winkeln, die bei großem d entstehen (Abschnitt 4.2, Fig. 4e).
2. **Keine Spannungen im Block:** Die wichtigste Kennzahl des Papers (max. Mises-Spannung)
   lässt sich mit der MBD nicht berechnen. Wir haben nur Kontaktdrücke.
3. **Idealisierte Druckverteilung:** Das statische Problem ist unbestimmt. Wir wählen die
   Lösung mit minimalem ∫p² dA, also die gleichmäßigste mögliche Verteilung. Im FEM legt die
   Steifigkeit fest, wo die Last durchgeht; an steifen Kanten und Ecken entstehen Spitzen.
4. **Daher zählt in der MBD nur die Geometrie der Kontaktflächen.** Mit wachsendem d werden die
   verzahnenden Flächen größer (Blockoberfläche 10.45 → 13.9), deshalb sinkt der Druck monoton.

Die MBD zeigt also den aufsteigenden Ast richtig (Verzahnung erst ab d > 0, starke Verbesserung
für kleine d). Das Optimum kann sie grundsätzlich nicht zeigen.

---

## Ideen (nach Aufwand sortiert)

### 1. Geometrische Kennzahlen neben den MBD-Drücken (Aufwand: gering)

Kennzahlen, die die dünnen Bereiche direkt messen, aufgetragen über d neben p_eff / p_max:

- kleinster Innenwinkel des verformten Umrisses (Oberseite),
- minimale Wandstärke: kleinster Abstand eines verschobenen Punkts zur gegenüberliegenden
  Kante (beim Starfish analytisch: geht gegen 0 für d → √3a/4 = 18.6 mm),
- minimale Querschnittsfläche eines „Sporns“ (Schnitt senkrecht zum Sporn),
- Kompaktheit des Umrisses, z.B. 4π·Fläche / Umfang².

Ergebnis: Ein Bild „Kontaktdruck fällt / Wandstärke fällt“. Wo sich die Kurven schneiden, ist ein
Kandidat für das Optimum. Das ist nur heuristisch, aber schnell und ohne Änderung der MBD.

### 2. Schnittgrößen in kritischen Querschnitten (Aufwand: mittel)

Mit den Kontaktkräften der MBD lassen sich ohne FEM Spannungen abschätzen:

- Einen Block an einem kritischen Querschnitt (Hals eines Sporns) gedanklich schneiden.
- Aus dem Gleichgewicht des abgeschnittenen Teils (Summe der Kontaktkräfte und der Last auf
  diesem Teil) die Schnittgrößen N, V, M berechnen. Das ist exakt, weil der Block starr ist und
  die Kräfte bekannt sind.
- Spannung wie beim Balken: σ ≈ N/A + M/W, τ ≈ V/A, daraus eine Vergleichsspannung.

Damit bekommt die MBD eine Spannungskennzahl, die mit dünner werdendem Querschnitt steigt,
also genau den Effekt, der im Paper die Umkehr verursacht. Offene Frage: wie die Querschnitte
automatisch gewählt werden (z.B. Schnitte an allen Punkten des Umrisses senkrecht zur
Mittellinie, den schlechtesten nehmen).

### 3. Andere Zielfunktion / Grenzbetrachtung (Aufwand: gering)

- `min max p` (LP) statt `min ∫p²`: kleinstmöglicher Spitzendruck, eine untere Schranke.
- Spanne der zulässigen Lösungen: für jede Fläche den minimal und maximal möglichen Druck
  unter Gleichgewicht berechnen. Zeigt, wie stark das Ergebnis von der Auswahl der Lösung
  abhängt (bei großer Spanne ist die MBD-Kennzahl wenig aussagekräftig).

Erfasst keine dünnen Bereiche, macht aber die Unsicherheit durch die statische
Unbestimmtheit sichtbar.

### 4. Nachgiebige Kontakte (Aufwand: mittel)

Kontaktkraft proportional zur Eindringung, λ = k·(Gᵀ δq)⁻ (Penalty bzw. Winkler-Bettung).
Die Blockverschiebungen δq folgen aus dem Minimum der Energie; die Druckverteilung ist dann
eindeutig und wird durch Steifigkeit bestimmt statt durch min ∫p².

- Mit konstantem k: ähnlich wie heute, aber Kanten und Ecken werden stärker belastet
  (Kippen der Blöcke wird abgebildet).
- Mit k abhängig von der lokalen Materialdicke hinter der Fläche (Strahl in Richtung −n bis
  zum Austritt aus dem Block): dünne Bereiche geben nach. Achtung: Das verlagert Last *weg* von
  dünnen Bereichen, erzeugt also für sich allein keine Spannungsspitzen; sinnvoll nur zusammen
  mit Idee 2.
- Liefert zusätzlich eine Durchbiegung (vergleichbar mit der Verschiebung U2 im Paper), wenn k
  aus E und einer Bezugslänge kalibriert wird.

### 5. Elastische Blöcke über Superelemente (Aufwand: hoch)

Jeden (identischen) Block einmal mit linear-elastischen Tetraedern vernetzen (z.B.
`pyvista`/`tetgen`), die Steifigkeitsmatrix auf die Knoten der Kontaktflächen kondensieren
(statische Kondensation, Guyan) und in der Assembly wiederverwenden. Kontakt weiter mit der
vorhandenen Kontakterkennung, Lösung als Kontaktproblem (LCP/QP).

- Erfasst Spannungskonzentrationen in dünnen Bereichen und Mises-Spannungen direkt.
- Da alle Blöcke gleich sind, ist die Kondensation nur einmal nötig. Damit bleibt der Ansatz
  deutlich schneller als FEM der ganzen Assembly (Paper: „FEM computations took quite a long
  time“; dort wird so ein zugeschnittenes Werkzeug ausdrücklich angeregt).
- Validierung gegen Table 1 des Papers (d = 3, 8, 15 mm).

### 6. Validierung gegen das Paper (Aufwand: gering, unabhängig von den anderen Ideen)

- Last wie im Paper (q = 0.15 MPa statt 0.01) und Maße in mm, dann max. Kontaktdruck direkt
  mit Fig. 3 / Table 1 vergleichen.
- Für kleine d (aufsteigender Ast) sollten die Trends übereinstimmen; Abweichungen zeigen, wie
  groß der Einfluss der Elastizität schon dort ist.
- Die Daten des Papers liegen bei Zenodo (doi.org/10.5281/zenodo.17045363).

---

## Empfehlung

Zuerst 1 und 6 (schnell, zeigen ob der Ansatz trägt), dann 2 als eigentliche Erweiterung der
MBD (Spannungskennzahl aus vorhandenen Kontaktkräften, ohne neues Lösungsverfahren). 4 und 5
nur, wenn die Kontaktdruckverteilung selbst realistischer werden muss.
