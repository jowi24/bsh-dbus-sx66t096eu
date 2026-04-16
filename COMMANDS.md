# BSH DBus — Command & Payload Referenz

Alle in den bisherigen Logs beobachteten Frames, ihre Bedeutung und der aktuelle Erkenntnisstand.

**Logs:**
- `A` = Auto 45-65° (2026-03-12)
- `B` = Auto 65-75° (2026-03-25)
- `C` = Auto 65-75° (2026-03-28, vollständiger Lauf)
- `D` = Auto 35-45° + IntensivZone (2026-03-29, vollständiger Lauf)
- `E` = Eco 50° (2026-04-01, erster vollständiger Eco-Lauf)
- `F` = Auto 45-65° (2026-04-03, zweiter vollständiger Lauf)
- `G` = Auto 45-65° (2026-04-04, dritter Lauf — adaptiv verkürzt)
- `H` = Auto 45-65° (2026-04-05, vierter Lauf — 4× `0x12`, kein 0x2010/5003 im Log)
- `I` = Auto 45-65° (2026-04-11, fünfter Lauf — 3× `0x12`, langer Log mit Tür-Öffnungs-Burst)
- `J` = Auto 45-65° (2026-04-14, sechster Lauf — 3× `0x12`, erster Zeitvorwahl-Lauf mit 7h Delay)

**Hinweis zu Zeitstempeln:** Alle Log-Zeitstempel sind in UTC (GMT). Lokale Zeit (MESZ) = UTC + 2h.

**Konfidenz:**
- ✅ Bestätigt — direkte Sensor-Korrelation, durch manuelles Testen am Gerät verifiziert, oder in `esphome.yaml` implementiert
- 🟡 Plausibel — konsistent über Logs, gute Indizien, aber keine direkte Bestätigung
- ❓ Unklar — beobachtet, Bedeutung noch unbekannt

---

## Geräte-Adressen (dest)

| dest | Vermutliche Funktion | Konfidenz |
|---|---|---|
| `0x17` | Bedienpanel | ✅ |
| `0x22` | Unbekanntes Gerät | ❓ |
| `0x24` | Türsensor / Verbrauchsmittelstatus | ✅ |
| `0x25` | Hauptsteuergerät (Controller) | ✅ |
| `0x26` | Unbekanntes Gerät | ❓ |
| `0x27` | Betriebsstatus-Knoten | ✅ |
| `0x55` | Anzeige / Display-Knoten | 🟡 |

---

## dest `0x17` — Bedienpanel

### `0x17 / 0x1000` — Panel-Optionen (Byte 1, Bitfeld)

Vom Panel gesendete Optionswahl. Byte 0 unbekannt, Byte 1 enthält die Optionen:

| Bit in Byte 1 | Maske | Option | Konfidenz |
|---|---|---|---|
| Bit 7 | `0x80` | VarioSpeed | ✅ |
| Bit 6 | `0x40` | IntensivZone | ✅ |
| Bit 3 | `0x08` | Hygiene | ✅ |
| Bit 1 | `0x02` | Glanztrocknen | ✅ |

Beobachtete Payloads: `0x0000` (alle Optionen OFF), `0x0040` (nur IntensivZone ON, Log D).

### `0x17 / 0x1001`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x02` | Unbekannt | A | ❓ |

### `0x17 / 0x1007`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00` | Unbekannt; erscheint kurz vor Programmstart | A B C H | ❓ |
| `0x01` | Erscheint einmalig direkt neben `0x00` beim Start (Log H); Bedeutung unklar | H | ❓ |

### `0x17 / 0x1010`

Payload = 1 Byte; erscheint jeweils unmittelbar vor dem entsprechenden `0x1011`-Frame mit identischem Wert. Möglicherweise eine Art "Cursor"-Meldung beim Durchblättern der Programme.

| Payload | Programm | Logs | Konfidenz |
|---|---|---|---|
| `0x0b` (11) | Auto 65-75° | B | ❓ |
| `0x0d` (13) | Auto 45-65° | D E | ❓ |
| `0x0e` (14) | Eco 50° | E | ❓ |

### `0x17 / 0x1011` — Panel-seitige Programm-ID

Vom Panel gesendete Programm-Auswahl. Payload = 1 Byte.

| Payload | Programm | Logs | Konfidenz |
|---|---|---|---|
| `0x10` (16) | Auto 35-45° | D | ✅ |
| `0x0d` (13) | Auto 45-65° | — | ✅ |
| `0x0b` (11) | Auto 65-75° | B | ✅ |
| `0x0e` (14) | Eco 50° | E | ✅ |
| `0x11` (17) | Schnell 45° | — | ✅ |
| `0x12` (18) | Vorspülen | — | ✅ |

In Logs A und C nicht beobachtet — der Panel sendet diesen Frame nur beim aktiven Drücken der Programmauswahl. Mapping durch manuelles Testen am Gerät bestätigt (implementiert in `esphome.yaml`).

### `0x17 / 0x1012` — Zeitvorwahl (Delay Start)

Payload: 3 Byte `[AA][BB][CC]`.

| Byte | Bedeutung | Konfidenz |
|---|---|---|
| Byte 0 (AA) | Rollierender Sequenzzähler; ändert sich in unregelmäßigen Abständen | ❓ |
| Byte 1 (BB) | Verbleibende Stunden bis Programmstart (0–9) | ✅ |
| Byte 2 (CC) | Verbleibende Minuten innerhalb der aktuellen Stunde (0x00–0x3b = 0–59, zählt abwärts) | ✅ |

Der Frame wird einmal pro Minute gesendet und zählt BB:CC rückwärts. Wenn CC 0x00 erreicht und BB > 0, dekrementiert BB um 1 und CC springt auf 0x3b (59). Bei BB=CC=0 startet das Programm.

Erstmals live beobachtet in Log J (2026-04-14): Log startete mit 7h48min verbleibender Wartezeit — erster Frame `0x100730` (AA=0x10, BB=0x07, CC=0x30=48). Jede Minute dekrementierte CC um 1. AA blieb im beobachteten Zeitraum konstant bei 0x10 (BB=7), nahm zuvor andere Werte 0x00–0x0f an. ESPHome-Sensor `Zeitvorwahl` zeigt BB (Stunden) ✅; Minuten-Auflösung via CC wäre ergänzbar.

### `0x17 / 0x1013`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x01` | Programmstart-Signal (erscheint direkt vor `Status → ON`) | A B C F J | 🟡 |

---

## dest `0x22` — Unbekanntes Gerät

### `0x22 / 0x40f2`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| *(leer)* | Unbekannt; erscheint einmalig beim Start | A B C | ❓ |

### `0x22 / 0x7ff1`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x10` | Unbekannt; erscheint einmalig beim Start (Broadcast / Handshake?) | A B C | ❓ |

---

## dest `0x24` — Türsensor / Verbrauchsmittelstatus

### `0x24 / 0x2006` — Tür, Klarspüler, Salz (Byte 0, Bitfeld)

| Bit | Maske | Sensor | Logik | Konfidenz |
|---|---|---|---|---|
| Bit 3 | `0x08` | Tür | `0` = offen (ON), `1` = geschlossen (OFF) | ✅ |
| Bit 1 | `0x02` | Klarspüler leer | `1` = Problem | ✅ |
| Bit 0 | `0x01` | Salz leer | `1` = Problem | ✅ |

Typische Payloads:

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00` | Tür offen, kein Verbrauchsmittelproblem | A B C H | ✅ |
| `0x02` | Tür offen, Klarspüler leer | H | ✅ |
| `0x08` | Tür geschlossen, kein Verbrauchsmittelproblem | A B C H | ✅ |

**Log H Klarspüler-Sequenz** (physisch bestätigt ✅): Klarspüler war leer; Benutzer füllte manuell auf, bevor das Programm startete:
- 21:29:54 UTC: `0x2006=0x02` → Klarspüler leer gemeldet
- 21:30:04 UTC: `0x2006=0x00` → nach ~10 Sek. wieder OK (Auffüllen)
- 21:30:27 UTC: `0x2006=0x08` → Tür geschlossen, Programm startet

Damit ist `0x02` (Bit 1) als Klarspüler-leer-Signal durch direkte Korrelation bestätigt. ✅

---

## dest `0x25` — Hauptsteuergerät

### `0x25 / 0x2000` — Laufender Zähler

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00`–`0x63` | Zyklischer Zähler (0–99), läuft während des Programms durch | A B C | 🟡 |

Der Zähler inkrementiert alle ~30 Sekunden. Lücken im Zähler deuten auf Bus-Stille (Phasenwechsel, Heizphasen) hin. Bedeutung des Inhalts unklar.

### `0x25 / 0x2004` — Betriebsmodus / Flagfeld (3 Byte)

Bitfeld; die wichtigsten beobachteten Werte:

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x000000` | Inaktiv / Standby (vor Programmstart und nach Ende) | A B C D | 🟡 |
| `0x020000` | Einmalig bei Niedertemperatur-Programmstart (Bit 17) | A D E F | 🟡 |
| `0x200000` | Normalbetrieb (Bit 21 gesetzt) | A B C E F | 🟡 |
| `0x201000` | Normalbetrieb mit aktivem Teilprogramm (Bit 21 + Bit 12) | A B C E F | 🟡 |
| `0x220000` | Niedertemperatur-Programme: Bit 21 + Bit 17 | A E F | 🟡 |
| `0x220200` | Auto 35-45° + IntensivZone: Bit 21 + Bit 17 + Bit 9 | D | 🟡 |
| `0x221000` | Niedertemperatur-Programme: Bit 21 + 17 + 12 | A E F | 🟡 |
| `0x221200` | Auto 35-45° + IntensivZone: Bit 21 + 17 + 12 + 9 | D | 🟡 |
| `0x800000` | Einmalig bei Programmstart (Bit 23) — nur Auto 65-75° | B C | 🟡 |
| `0x820000` | Einmalig bei Programmstart (Bit 23 + Bit 17) — Niedertemperatur-Programme | A D E F | 🟡 |

**Bit-Interpretation (vorläufig):**
- Bit 23 (`0x800000`): Programm-Initialisierungs-Flag (einmalig, direkt nach Programmstart)
- Bit 21 (`0x200000`): Programm läuft
- Bit 17 (`0x020000`): Niedertemperatur-Flag — in Auto 35-45° und Auto 45-65° gesetzt, bei Auto 65-75° nicht
- Bit 12 (`0x001000`): aktiver Teilschritt innerhalb einer Phase
- Bit 9 (`0x000200`): IntensivZone aktiv in aktueller Phase — nur wenn Option IntensivZone ausgewählt ✅ (Log D)

**Log E (Eco 50°):** `0x220000`, `0x221000` und `0x820000` beobachtet → Bit 17 ist auch bei Eco 50° gesetzt. Eco 50° ist damit ein Niedertemperatur-Programm (wie Auto 35-45° und Auto 45-65°). ✅

**Log F (Auto 45-65°):** Selbe Werte wie Log A: `0x020000`, `0x820000`, `0x220000` bei Start, dann `0x221000` im Betrieb. ✅

**Log G (Auto 45-65°):** Identisch zu Log A/F. Niedertemperatur-Flag (Bit 17) konsistent. ✅

### `0x25 / 0x2005` — Programmphase

Zentrales Statusfeld; Werte erscheinen in fester Reihenfolge:

| Payload | Phase | Bedeutung | Logs | Konfidenz |
|---|---|---|---|---|
| `0x21` | Init | Programmstart; erscheint unmittelbar nach `Status → ON`. In Log F **zweimal** beobachtet: einmal bei Status→ON, einmal ~2 min später direkt nach dem `0x2010`-Frame — möglicherweise sendet der Controller nach der Programmdaten-Übermittlung einen Re-Init. | A B C F | ✅ |
| `0x22` | Laufende Phase | Vorspülen, Hauptspülen, Zwischenspülen (generischer „Betrieb"-Zustand) | A B C | ✅ |
| `0x12` | Phasenwechsel | Kurzer Übergangs-Frame; Restzeit wird anschließend neu berechnet | A B C | ✅ |
| `0x14` | Phasenwechsel | Kurzer Übergang innerhalb der Klarspül-Endphase | A B C | ✅ |
| `0x24` | Klarspülen | Stabile Phase, ~38–41 min Restzeit | A B C | ✅ |
| `0x28` | Trocknen-Vorphase | ~16–20 min Restzeit | A B C | ✅ |
| `0x20` | Trocknen / Auslauf | Erscheint zweimal bei ~1 min Restzeit | A B C | ✅ |

Das `0x10`-Bit markiert generell Übergangszustände (`0x12`, `0x14`); das `0x20`-Bit ist in allen stabilen Betriebszuständen gesetzt.

**Phasenverlauf je Programm:**

| Phase | Auto 35-45° | Auto 45-65° (Log A) | Auto 45-65° (Log F) | Auto 45-65° (Log G) | Auto 65-75° | Eco 50° |
|---|---|---|---|---|---|---|
| Init | `0x21` @ 0 min | `0x21` @ 0 min | `0x21` @ 0 min (+ 2. `0x21` @ +2 min) | `0x21` @ 0 min | `0x21` @ 0 min | `0x21` @ 0 min |
| **Vorspülen / erste Phase** | `0x22` @ +14 min ⚡ | `0x22` @ +21 min | `0x22` @ +22 min | `0x22` @ +11 min | `0x22` @ +21 min | `0x22` @ +14 min |
| Übergang | `0x12` @ +52 min | `0x12` @ +44 min | `0x12` @ +76 min | `0x12` @ +43 min | `0x12` @ +61–81 min | `0x12` @ +110 min |
| Hauptspülen | `0x22` @ +52 min | `0x22` @ +86 min | `0x22` @ +76 min (instant) | `0x22` @ +43 min | `0x22` @ +98 min | `0x22` @ +110 min |
| Übergang (Zwischenspülen) | — | `0x12` @ +95 min | `0x12` @ +92 min | — | — | — |
| Zwischenspülen | — | `0x22` @ +110 min | `0x22` @ +92 min (4 Sek.) | — | — | — |
| Übergang (Klarspülen) | — | `0x12` @ +119 min | — | — | — | — |
| Klarspülen | `0x24` @ +62 min | `0x24` @ +119 min | `0x24` @ +92 min | `0x24` @ +52 min | `0x24` @ +108 min | `0x24` @ +120 min |
| Übergang | `0x14` @ +74 min | `0x14` @ +133 min | `0x14` @ +104 min | `0x14` @ +64 min | `0x14` @ +120 min | `0x14` @ +130 min |
| — | `0x24` @ +74 min | `0x24` @ +135 min | `0x24` @ +104 min | `0x24` @ +64 min | `0x24` @ +123 min | `0x24` @ +130 min |
| Trocknen | `0x28` @ +80 min | `0x28` @ +140 min | `0x28` @ +110 min | `0x28` @ +70 min | `0x28` @ +128 min | `0x28` @ +136 min |
| Auslauf | `0x20` @ +95 min | `0x20` @ +159 min | `0x20` @ +128 min | `0x20` @ +85 min | `0x20` @ +144 min | `0x20` @ ~+172 min |

Initiale Restzeiten: Auto 35-45° (mit IntensivZone) 105 min; Auto 45-65° Logs A/F 160 min; **Auto 45-65° Log G 100 min** (adaptiv, s.u.); Eco 50° 165 min; Auto 65-75° 145 min.

**Anzahl `0x12`-Übergänge ist adaptiv** — bei Auto 45-65° bisher 1×, 2×, 3× und **4×** beobachtet (je nach Verschmutzungsgrad / Sensorentscheidung des Geräts):

| Log | `0x12`-Zahl | Laufdauer | Restzeit-Start | Besonderheit |
|---|---|---|---|---|
| G | **1×** | 85 min | 100 min | kein Vorspülen |
| F | **2×** | 128 min | 160 min | Zwischenspülen nur 4 Sek. |
| A | **3×** | 159 min | 160 min | Volllauf, Zwischenspülen lang |
| I | **3×** | ~101 min | 138 min* | 3 Phasen komprimiert (innerhalb 20 min) |
| H | **4×** | ~109 min | 138 min* | 4 Waschphasen + 2 sehr kurz (1.7/0 min) |
| J | **3×** | 106 min | 139 min* | erster Zeitvorwahl-Lauf (7h Delay); Restzeit-Start nominal 160 min |

*Restzeit beim ersten `0x22` (0x21-Frame hatte keine 0x2008 im Log).

Log H (2026-04-05) Phasensequenz im Detail:
- `0x21` @ +0 min; `0x22` @ +22 min (Vorspülen, 27 min)
- `0x12` #1 @ +49 min → Restzeit 111→74; `0x22` @ +50 min (9 min)
- `0x12` #2 @ +60 min → Restzeit 64→52; `0x22` @ +61 min (1.7 min — sehr kurz)
- `0x12` #3 @ +63 min → Restzeit 50→50; `0x22` @ +63 min (9 min)
- `0x12` #4 @ +72 min → Restzeit 41→41; `0x24` @ +72 min (Klarspülen direkt)
- `0x28` @ +91 min; `0x20` @ +109 min

Hypothese: Die kurzen Phasen (1.7 min, 0 sec) könnten Spülwasserwechsel / Zwischenentleerungen darstellen. Bei stark verschmutztem Geschirr führt das Gerät mehr Spülphasen durch.

Die anderen Programme zeigen bisher jeweils 1× `0x12` (Auto 35-45°, Auto 65-75°, Eco 50°) — ob das ebenfalls adaptiv ist, ist noch unklar.

Ab `0x24` (Klarspülen) ist die Sequenz in allen beobachteten Läufen identisch.

**Initiale Restzeit kann von 0x5003 abweichen (Log G):** `0x5003` zeigte 160 min (Nominalwert), aber `0x2008` bei `0x2005=0x21` zeigte bereits 100 min. Das Gerät schätzt die tatsächliche Laufzeit scheinbar schon zu Beginn anhand von Beladung/Sensorik und unterschreitet dabei den Nominalwert. 🟡

**Restzeit-Korrekturen bei `0x12`-Übergängen:**
- Log F, 1. `0x12` @ +76 min: Restzeit 85 → 50 min (−35 min)
- Log F, 2. `0x12` @ +92 min: Restzeit 35 → 41 min (+6 min)
- Log G, 1. `0x12` @ +43 min: Restzeit 42 → 42 min (keine Korrektur)
- Log I, 1. `0x12` @ +44 min: Restzeit 116 → 74 min (−42 min, starke Abwärtskorrektur)
- Log I, 2. `0x12` @ +55 min: Restzeit 64 → 50 min (−14 min)
- Log I, 3. `0x12` @ +64 min: Restzeit 41 → 41 min (keine Korrektur)
- Log H, 1. `0x12` @ +49 min: Restzeit 111 → 74 min (−37 min, starke Abwärtskorrektur)
- Log H, 2. `0x12` @ +60 min: Restzeit 64 → 52 min (−12 min)
- Log H, 3.+4. `0x12`: keine Restzeit-Korrekturen (50→50, 41→41)
- Log J, 1. `0x12` @ +44 min: Restzeit 116 → 78 min (−38 min)
- Log J, 2. `0x12` @ +54 min: Restzeit 70 → 55 min (−15 min)
- Log J, 3. `0x12` @ +68 min: Restzeit 41 → 41 min (keine Korrektur)
- Eco 50° (Log E), `0x12` @ +110 min: Restzeit ~55 → 65 min (+10 min)

**⚡ Dispenser-Öffnung = Start des Hauptspülens** (bestätigt in Log D und Log G):

| Log | Programm | Vorspülen? | Dispenser-Signal | Beobachtet (MESZ) | Log-Frame (UTC) |
|---|---|---|---|---|---|
| D | Auto 35-45° + IntensivZone | Nein | erster `0x22` nach `0x21` | 15:49 | 13:50:06 |
| G | Auto 45-65° (adaptiv 1× `0x12`) | Nein | erster `0x22` nach `0x21` | 00:03 | 22:04:03 |

**Regel:** Das Gerät öffnet das Tab-Fach zu Beginn der Hauptspülphase. Ob diese direkt als erster `0x22` erscheint oder erst nach einem `0x12`-Übergang, hängt davon ab, ob ein Vorspülen stattfindet:
- **Kein Vorspülen** (1× `0x12`, z.B. Auto 35-45°, kurzer Auto 45-65°-Lauf): Dispenser bei erstem `0x22` ✅
- **Mit Vorspülen** (2–3× `0x12`, langer Auto 45-65°-Lauf): Dispenser vermutlich beim ersten `0x12`-Übergang — noch nicht physisch bestätigt.

### `0x25 / 0x2008` — Restzeit

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0xNN0000` | Byte 0 = Restzeit in Minuten; Byte 0 = Minuten, Bytes 1–2 immer `0x00` | A B C E F | ✅ |

Restzeit wird bei jedem `0x12`-Phasenübergang neu berechnet (Schätzkorrektur, kann deutlich springen).

### `0x25 / 0x2009` — Uptime-Poll

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00` | Polling-Frame; ESPHome antwortet mit aktuellem Uptime-Sensorwert | A B C | ✅ |

Erscheint alle ~10–30 Sekunden während des laufenden Programms.

### `0x25 / 0x2010` — Programm-Init

Payload: 13 Byte. Erscheint typischerweise kurz nach Verbindungsaufbau. In Log F erschien er ~2 min **nach** Programmstart — der Controller sendet ihn aktiv (nicht nur beim ESP-Handshake), vermutlich einmalig pro Programmlauf.

**Byte 0 — Programm-ID** (gleiche Codierung wie `0x17/0x1011`):

| Wert | Programm | Logs | Konfidenz |
|---|---|---|---|
| `0x10` (16) | Auto 35-45° | B* D | ✅ |
| `0x0d` (13) | Auto 45-65° | A F G | ✅ |
| `0x0b` (11) | Auto 65-75° | C | ✅ |
| `0x0e` (14) | Eco 50° | E | ✅ |
| `0x11` (17) | Schnell 45° | — | ✅ |
| `0x12` (18) | Vorspülen | — | ✅ |

*Log B zeigt `0x10` (Auto 35-45°) — dies stammt von einem vorherigen Lauf, bei dem der ESP mid-run verbunden hat. Der nachfolgende Auto 65-75°-Lauf überlagerte den Programmwert via `0x17/0x1011`.

**Byte 8 — Optionen (Bitfeld)** (gleiche Codierung wie `0x17/0x1000` Byte 1):

| Bit | Maske | Option | Konfidenz |
|---|---|---|---|
| Bit 7 | `0x80` | VarioSpeed | ✅ |
| Bit 6 | `0x40` | IntensivZone | ✅ |
| Bit 3 | `0x08` | Hygiene | ✅ |
| Bit 1 | `0x02` | Glanztrocknen | ✅ |

Bytes 1–7 und 9–12: konstant `000001050062000037010000` über alle bisher geloggten Läufe; Bedeutung unklar.

### `0x25 / 0x2011` — Programmliste (Hypothese)

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0xa5100d0b0e1112a1a080818486a2` | Identisch in allen Logs | A B C | ❓ |

**Hinweis:** Die Bytes 1–6 der Payload (`10 0d 0b 0e 11 12`) entsprechen exakt den 6 bekannten Programm-IDs in der Reihenfolge Auto 35-45°, Auto 45-65°, Auto 65-75°, Eco 50°, Schnell 45°, Vorspülen. Byte 0 (`0xa5`) könnte ein Header oder die Programmanzahl sein. Die zweite Hälfte (`a1 a0 80 81 84 86 a2`) ist noch ungeklärt — möglicherweise Temperaturwerte oder Klarspülparameter je Programm.

### `0x25 / 0x2012`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00` | Erscheint einmalig vor Programmstart | A B C | ❓ |
| `0x01` | Erscheint einmalig nach Programmstart | A B C | ❓ |

### `0x25 / 0x2013`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0xffff` | Erscheint 1–3× beim Start; Anzahl hängt offenbar davon ab, wie frühzeitig der ESP verbunden ist — Log F (ESP verbunden kurz vor Start) nur 1×, andere Logs 2–3× | A B C F | ❓ |

---

## dest `0x26` — Unbekanntes Gerät

### `0x26 / 0x2002`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00000000` | Erscheint 2× pro Programmdurchlauf (Start und Ende); Bedeutung unklar | A B C | ❓ |

---

## dest `0x27` — Betriebsstatus

### `0x27 / 0x2007` — Programmstatus (Betrieb EIN/AUS)

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x01` | Status = ON (Programm läuft) | A B C | ✅ |
| `0x02` | Status = Standby/bereit — erscheint sowohl beim Programmende als auch beim Öffnen der Tür im Standby (Log I: 6h nach Programmende bei Türöffnung) | A B C I | 🟡 |
| `0x03` | Programmende-Signal — erscheint einmalig beim tatsächlichen Programmabschluss | A B C I | ✅ |

**Log I (2026-04-11):** Nach Programmende (09:55 UTC, `0x03`) öffnete der Benutzer die Tür ~6h später (16:03 UTC). Dies löste einen kompletten Status-Burst aus: `0x2006=0x00`, `0x2004=0x200000`, `0x2008=0xa0`, `0x2011`, `0x2012`, `0x2013`, `0x2010=0x0d...`, `0x2007=0x02`. Das bedeutet: **`0x02` ist kein reines Programmende-Signal**, sondern eher ein allgemeiner "Gerät bereit/Standby"-Frame. `0x03` hingegen markiert eindeutig das Programmende.

---

## dest `0x55` — Display / Anzeige-Knoten

### `0x55 / 0x5003` — Initiale Restzeit

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0xNN0000` | Byte 0 = Restzeit bei Programmstart in Minuten | A C | 🟡 |

Bestätigt: `0xa0`=160 (Auto 45-65°, Log A), `0x91`=145 (Auto 65-75°, Log C), `0x69`=105 (Auto 35-45° + IntensivZone, Log D).
Log B zeigt `0x64`=100, weil der ESP mid-run verbunden hat.
Log E zeigt `0x64`=100 — allerdings erschienen diese 20 Frames bereits während der Programm-Auswahl (16:25:09, vor Status→ON um 16:25:31). Die tatsächliche Startrestzeit von Eco 50° war 165 min. Hypothese: der 20×-Burst feuert bei jeder Programmauswahl auf dem Panel (nicht nur beim Start), was erklärt, warum Log E den Wert des zuletzt gesichteten Programms (Auto 45-65° = 100 min?) zeigt.
Log F: **nicht beobachtet** — ESP verband sich kurz vor Programmstart, der 20×-Burst erfolgte offenbar vor dem Log-Beginn. Dies zeigt, dass der Burst ein Startup-Signal des Controllers ist, das unabhängig von einer ESP-Verbindung gesendet wird.
Log G: `0xa0`=160 (Nominalwert Auto 45-65°) — aber `0x2008` zeigte bei `0x2005=0x21` bereits 100 min. `0x5003` zeigt den Nominalwert des Programms, nicht die adaptive Schätzung.
Erscheint 20× zu Beginn jedes Programms.

### `0x55 / 0x5006`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00000000` | Erscheint 19–20× zu Beginn; immer Null; Bedeutung unklar | A B C | ❓ |

### `0x55 / 0x5008`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x000000` | Erscheint 20× zu Beginn; immer Null; Bedeutung unklar | A B C | ❓ |

---

## Offene Fragen

1. **`0x2004` Bit 17 (`0x020000`)**: ✅ Durch Log E bestätigt: Eco 50° hat Bit 17 gesetzt (`0x220000`, `0x221000`, `0x820000`). Damit ist die Hypothese "Niedertemperatur-Flag" für alle bisherigen Eco/Auto-35-45°/Auto-45-65°-Läufe konsistent. Offen: gilt das auch für Schnell 45°?
2. **`0x22 / 0x40f2` und `0x22 / 0x7ff1`**: Destination `0x22` ist unbekannt. Beide Frames erscheinen einmalig beim Start.
3. **`0x2011` zweite Hälfte**: Bytes 7–13 (`a1 a0 80 81 84 86 a2`) noch unklar. Hypothese: Temperatur- oder Klarspülparameter je Programm.
4. **Dispenser-Signal mit Vorspülen**: Bei Auto 45-65° ohne Vorspülen (Log G, 1× `0x12`) physisch bestätigt: erster `0x2005=0x22` ✅. Bei Läufen mit Vorspülen (2–3× `0x12`) bleibt der erste `0x12`-Übergang als stärkster Kandidat — noch nicht physisch bestätigt.
5. **`0x17 / 0x1010`**: In Log B und D beobachtet. Möglicherweise "Set Program"-Request vom Panel vor `0x1011`.
6. **`0x2012` und `0x2013`**: Immer gleiche Werte, Bedeutung unklar.

---

## Nächste Schritte

- [x] Log für **Auto 35-45°** aufzeichnen → Phasenzahl und `0x2010` Byte 0 (`0x10`) im Log bestätigt (Log D)
- [x] Dispenser-Öffnung physisch synchronisiert für **Auto 35-45°** → erster `0x2005=0x22`-Frame ✅
- [x] Dispenser-Öffnung physisch synchronisiert für **Auto 45-65° (adaptiv, kein Vorspülen)** → erster `0x2005=0x22`-Frame ✅ (Log G, 00:03 MESZ)
- [ ] Dispenser-Signal für **Auto 45-65° mit Vorspülen** (2–3× `0x12`) physisch bestätigen — vermutlich erster `0x12`-Übergang
- [x] **Zeitvorwahl-Lauf** aufzeichnen → `0x17/0x1012` vollständige Payload-Struktur in Log J bestätigt (`[AA][BB][CC]`, BB=Stunden, CC=Minuten)
- [x] `0x2004` Bit 17 bei **Eco 50°** bestätigt (Log E) → Bit 17 gesetzt ✅
- [x] Zweiter vollständiger **Auto 45-65°**-Lauf aufgezeichnet (Log F) → Phasenverlauf und 0x2004-Flags bestätigt
- [ ] `0x2004` Bit 17 bei **Schnell 45°** prüfen
- [ ] `0x2011` Bytes 7–13 analysieren (Temperaturtabelle?)
- [ ] **`0x55/0x5003`-Burst** Hypothese prüfen: feuert er bei jeder Panel-Programmauswahl (nicht nur beim Start)?
- [ ] Dispenser-Signal für **Eco 50°** physisch bestätigen (erster `0x22`-Frame bei +14 min?)
- [ ] Zweites `0x21` in Log F: prüfen ob dieses Muster in weiteren vollständigen Logs reproduzierbar ist
- [ ] Auto 45-65°: klären ob 2× oder 3× `0x12`-Übergänge (Log A vs. Log F) von Beladung/Temperatur abhängen
