# BSH DBus — Command & Payload Referenz

Alle in den bisherigen Logs beobachteten Frames, ihre Bedeutung und der aktuelle Erkenntnisstand.

**Logs:**
- `A` = Auto 45-65° (2026-03-12)
- `B` = Auto 65-75° (2026-03-25)
- `C` = Auto 65-75° (2026-03-28, vollständiger Lauf)

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

Bisher beobachtete Payloads: `0x0000` (alle Optionen OFF).

### `0x17 / 0x1001`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x02` | Unbekannt | A | ❓ |

### `0x17 / 0x1007`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00` | Unbekannt; erscheint kurz vor Programmstart | A B C | ❓ |

### `0x17 / 0x1010`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x0b` | Unbekannt; vermutl. "Set Program Request" vom Panel (nur in Log B beobachtet) | B | ❓ |

### `0x17 / 0x1011` — Panel-seitige Programm-ID

Vom Panel gesendete Programm-Auswahl. Payload = 1 Byte.

| Payload | Programm | Logs | Konfidenz |
|---|---|---|---|
| `0x10` (16) | Auto 35-45° | — | ✅ |
| `0x0d` (13) | Auto 45-65° | — | ✅ |
| `0x0b` (11) | Auto 65-75° | B | ✅ |
| `0x0e` (14) | Eco 50° | — | ✅ |
| `0x11` (17) | Schnell 45° | — | ✅ |
| `0x12` (18) | Vorspülen | — | ✅ |

In Logs A und C nicht beobachtet — der Panel sendet diesen Frame nur beim aktiven Drücken der Programmauswahl. Mapping durch manuelles Testen am Gerät bestätigt (implementiert in `esphome.yaml`).

### `0x17 / 0x1012` — Zeitvorwahl (Delay Start)

| Byte | Bedeutung | Konfidenz |
|---|---|---|
| Byte 1 | Verzögerung in Stunden | ✅ |

In bisherigen Logs nicht beobachtet (kein Delayed-Start-Lauf aufgezeichnet). Mapping durch manuelles Testen bestätigt (implementiert in `esphome.yaml`).

### `0x17 / 0x1013`

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x01` | Programmstart-Signal (erscheint direkt vor `Status → ON`) | A B C | 🟡 |

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
| `0x00` | Tür offen, kein Verbrauchsmittelproblem | A B C | ✅ |
| `0x08` | Tür geschlossen, kein Verbrauchsmittelproblem | A B C | ✅ |

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
| `0x000000` | Inaktiv / Standby (vor Programmstart und nach Ende) | A B C | 🟡 |
| `0x020000` | Einmalig bei Auto 45-65° Programmstart (Bit 17) | A | ❓ |
| `0x200000` | Normalbetrieb (Bit 21 gesetzt) | A B C | 🟡 |
| `0x201000` | Normalbetrieb mit aktivem Teilprogramm (Bit 21 + Bit 12) | A B C | 🟡 |
| `0x220000` | Nur Auto 45-65°: Bit 21 + Bit 17 — möglicherweise Hochtemperatur-Flag | A | ❓ |
| `0x221000` | Nur Auto 45-65°: Bit 21 + 17 + 12 | A | ❓ |
| `0x800000` | Einmalig bei Programmstart (Bit 23) — nur Auto 65-75° | B C | 🟡 |
| `0x820000` | Einmalig bei Programmstart (Bit 23 + 17) — nur Auto 45-65° | A | 🟡 |

**Bit-Interpretation (vorläufig):**
- Bit 23 (`0x800000`): Programm-Initialisierungs-Flag (einmalig, direkt nach Programmstart)
- Bit 21 (`0x200000`): Programm läuft
- Bit 17 (`0x020000`): programmspezifisch — nur bei Auto 45-65° (Temperaturklasse?)
- Bit 12 (`0x001000`): aktiver Teilschritt innerhalb einer Phase

### `0x25 / 0x2005` — Programmphase

Zentrales Statusfeld; Werte erscheinen in fester Reihenfolge:

| Payload | Phase | Bedeutung | Logs | Konfidenz |
|---|---|---|---|---|
| `0x21` | Init | Programmstart, erster Frame nach `Status → ON` | A B C | ✅ |
| `0x22` | Laufende Phase | Vorspülen, Hauptspülen, Zwischenspülen (generischer „Betrieb"-Zustand) | A B C | ✅ |
| `0x12` | Phasenwechsel | Kurzer Übergangs-Frame; Restzeit wird anschließend neu berechnet | A B C | ✅ |
| `0x14` | Phasenwechsel | Kurzer Übergang innerhalb der Klarspül-Endphase | A B C | ✅ |
| `0x24` | Klarspülen | Stabile Phase, ~38–41 min Restzeit | A B C | ✅ |
| `0x28` | Trocknen-Vorphase | ~16–20 min Restzeit | A B C | ✅ |
| `0x20` | Trocknen / Auslauf | Erscheint zweimal bei ~1 min Restzeit | A B C | ✅ |

Das `0x10`-Bit markiert generell Übergangszustände (`0x12`, `0x14`); das `0x20`-Bit ist in allen stabilen Betriebszuständen gesetzt.

**Phasenverlauf je Programm:**

| Phase | Auto 45-65° | Auto 65-75° |
|---|---|---|
| Init | `0x21` @ 0 min | `0x21` @ 0 min |
| Vorspülen | `0x22` @ +21 min | `0x22` @ +21 min |
| Übergang (Hauptspülen) | `0x12` @ +44 min | `0x12` @ +61–81 min |
| Hauptspülen | `0x22` @ +86 min | `0x22` @ +98 min |
| Übergang (Zwischenspülen) | `0x12` @ +95 min | — |
| Zwischenspülen | `0x22` @ +110 min | — |
| Übergang (Klarspülen) | `0x12` @ +119 min | — |
| Klarspülen | `0x24` @ +119 min | `0x24` @ +108 min |
| Übergang | `0x14` @ +133 min | `0x14` @ +120 min |
| — | `0x24` @ +135 min | `0x24` @ +123 min |
| Trocknen | `0x28` @ +140 min | `0x28` @ +128 min |
| Auslauf | `0x20` @ +159 min | `0x20` @ +144 min |

Auto 45-65° hat 3× `0x12`-Übergänge (inkl. Zwischenspülen), Auto 65-75° nur 1×.
Ab `0x24` (Klarspülen) ist die Sequenz in beiden Programmen identisch.

**Hypothese Dispensersignal:** Der erste `0x12`-Übergang nach `Status → ON` markiert den Wechsel von Vorspülen zu Hauptspülen. Dies ist der plausibelste Zeitpunkt für das Öffnen des Reinigertab-Fachs. Nicht physisch bestätigt.

### `0x25 / 0x2008` — Restzeit

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0xNN0000` | Restzeit in Minuten; Byte 0 = Minuten, Bytes 1–2 immer `0x00` | A B C | ✅ |

Restzeit wird bei jedem `0x12`-Phasenübergang neu berechnet (Schätzkorrektur, kann deutlich springen).

### `0x25 / 0x2009` — Uptime-Poll

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0x00` | Polling-Frame; ESPHome antwortet mit aktuellem Uptime-Sensorwert | A B C | ✅ |

Erscheint alle ~10–30 Sekunden während des laufenden Programms.

### `0x25 / 0x2010` — Programm-Init

Payload: 13 Byte. Erscheint einmalig kurz nach Verbindungsaufbau / vor Programmstart.

**Byte 0 — Programm-ID** (gleiche Codierung wie `0x17/0x1011`):

| Wert | Programm | Logs | Konfidenz |
|---|---|---|---|
| `0x10` (16) | Auto 35-45° | B* | ✅ |
| `0x0d` (13) | Auto 45-65° | A | ✅ |
| `0x0b` (11) | Auto 65-75° | C | ✅ |
| `0x0e` (14) | Eco 50° | — | ✅ |
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
| `0xffff` | Erscheint 2–3× beim Start; Bedeutung unklar | A B C | ❓ |

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
| `0x01` | Status = ON (Programm läuft); `x[0] == 0x01` | A B C | ✅ |
| `0x02` | Status = OFF (Programm beendet, erste Meldung) | A B C | ✅ |
| `0x03` | Status = OFF (Programm beendet, zweite Meldung) | A B C | ✅ |

---

## dest `0x55` — Display / Anzeige-Knoten

### `0x55 / 0x5003` — Initiale Restzeit

| Payload | Bedeutung | Logs | Konfidenz |
|---|---|---|---|
| `0xNN0000` | Byte 0 = Restzeit bei Programmstart in Minuten | A C | 🟡 |

Bestätigt: `0xa0`=160 (Auto 45-65°, Log A), `0x91`=145 (Auto 65-75°, Log C).
Log B zeigt `0x64`=100, weil der ESP mid-run verbunden hat.
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

1. **`0x2004` Bit 17 (`0x020000`)**: Nur bei Auto 45-65°. Könnte Temperaturklasse oder Zwischenspül-Konfiguration codieren.
2. **`0x22 / 0x40f2` und `0x22 / 0x7ff1`**: Destination `0x22` ist unbekannt. Beide Frames erscheinen einmalig beim Start.
3. **`0x2011` zweite Hälfte**: Bytes 7–13 (`a1 a0 80 81 84 86 a2`) noch unklar. Hypothese: Temperatur- oder Klarspülparameter je Programm.
4. **Dispenser-Signal**: Kein dedizierter Bus-Frame für das Öffnen des Tab-Fachs identifiziert. Stärkster Kandidat: erster `0x25/0x2005/0x12`-Frame nach Programmstart.
5. **`0x17 / 0x1010`**: Nur in Log B. Möglicherweise "Set Program"-Request vom Panel vor `0x1011`.
6. **`0x2012` und `0x2013`**: Immer gleiche Werte, Bedeutung unklar.

---

## Nächste Schritte

- [ ] Log für **Auto 35-45°** aufzeichnen → Phasenzahl und `0x2010` Byte 0 (`0x10`) im Log bestätigen
- [ ] **Zeitvorwahl-Lauf** aufzeichnen → `0x17/0x1012` Byte 1 im echten Log sehen
- [ ] Dispenser-Öffnung physisch mit Log-Zeitstempel synchronisieren (erster `0x12`-Übergang bestätigen)
- [ ] Bedeutung von `0x2004` Bit 17 klären (Experiment mit Option IntensivZone oder Auto 35-45° Log)
- [ ] `0x2011` Bytes 7–13 analysieren (Temperaturtabelle?)
