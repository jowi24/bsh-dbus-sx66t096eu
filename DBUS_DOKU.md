# Siemens BSH DBUS Doku (bestaetigte Formate)

Diese Doku beschreibt die aktuell bestaetigten seriellen DBUS-Formate.

Es gibt zwei Bestaetigungsstufen:
- Log-basiert bestaetigt: per `parse_log.py` aus `spuelmaschine_log.txt` korreliert.
- Laufend funktional: in `esphome.yaml` implementiert und laut aktuellem Betriebsstand funktionierend.

## Datenbasis und Methode

- Quelle: `spuelmaschine_log.txt`
- Auswertung: `parse_log.py` mit direkter Frame->Sensor-Korrelation
- Kriterium fuer "bestaetigt":
  - Sensor-Log folgt direkt auf den Frame
  - Zeitdifferenz liegt im Parser-Fenster (`--max-lag-ms`, Standard 300 ms)

Log-Auswertung (aktueller Stand):
- `441` Frames insgesamt
- `126` Frames mit direkt korreliertem Sensor-Event
- Bestaetigte `dest/cmd` mit Sensor-Korrelation:
  - `0x24 / 0x2006` (6x)
  - `0x27 / 0x2007` (3x)
  - `0x25 / 0x2008` (114x)
  - `0x25 / 0x2010` (2x)

## Gegenpruefung mit `esphome.yaml` (funktioniert bereits)

Folgende Decoder sind in `esphome.yaml` aktiv und gelten als funktionierend:

- `0x24 / 0x2006`
  - `Klarspueler` (Bit 1)
  - `Salz` (Bit 0)
  - `Tuer` (Bit 3 invertiert)
- `0x27 / 0x2007`
  - `Status` (running)
- `0x25 / 0x2008`
  - `Restzeit` (Minuten)
- `0x17 / 0x1012`
  - `Zeitvorwahl` (Stunden)
- `0x17 / 0x1000`
  - Option-Bits vom Bedienpanel (`VarioSpeed`, `IntensivZone`, `Hygiene`, `Glanztrocknen`)
- `0x17 / 0x1011`
  - Programmnamen vom Bedienpanel
- `0x25 / 0x2010`
  - Init/Programmtext und Option-Bits (inkl. Spiegelung auf Template-Sensoren)

## Allgemeines Frame-Format

ESPHome Logformat:

```text
Received frame dest 0xDD cmd 0xCCCC: 0xPPPP...
```

- `dest`: Zielknoten (1 Byte, hex)
- `cmd`: Kommando (2 Byte, hex)
- `payload`: Nutzdaten variabler Laenge (hex)

Hinweis: Bei langen Payloads kann im Log eine Fortsetzungszeile ohne Timestamp folgen. Der Parser fuegt diese korrekt zusammen.

## Bestaetigte Formate

### 1) Tuerstatus

- `dest`: `0x24`
- `cmd`: `0x2006`
- `payload`: 1 Byte

Beobachtung:
- `payload 0x00` -> `Tuer ON` (offen)
- `payload 0x08` -> `Tuer OFF` (geschlossen)

Evidenzbeispiele:
- `spuelmaschine_log.txt:140` + `spuelmaschine_log.txt:141`
- `spuelmaschine_log.txt:142` + `spuelmaschine_log.txt:143`
- `spuelmaschine_log.txt:446` + `spuelmaschine_log.txt:447`

Interpretation in `esphome.yaml`:
- `door = !((x[0] >> 3) & 0x01)`

### 2) Laufstatus (Running)

- `dest`: `0x27`
- `cmd`: `0x2007`
- `payload`: 1 Byte

Beobachtung:
- `payload 0x01` -> `Status ON`
- `payload 0x02` -> `Status OFF`

Evidenzbeispiele:
- `spuelmaschine_log.txt:448` + `spuelmaschine_log.txt:449`
- `spuelmaschine_log.txt:346` + `spuelmaschine_log.txt:347`

Interpretation in `esphome.yaml`:
- `running = (x[0] == 0x01)`

### 3) Restzeit

- `dest`: `0x25`
- `cmd`: `0x2008`
- `payload`: 3 Byte (`0xMM0000` beobachtet)

Beobachtung:
- Erstes Payload-Byte (`MM`) entspricht Restzeit in Minuten.
- Beispiele:
  - `0xa00000` -> `160 min`
  - `0x9f0000` -> `159 min`
  - `0x980000` -> `152 min`

Evidenzbeispiele:
- `spuelmaschine_log.txt:302` + `spuelmaschine_log.txt:303`
- `spuelmaschine_log.txt:471` + `spuelmaschine_log.txt:472`
- `spuelmaschine_log.txt:518` + `spuelmaschine_log.txt:519`

Interpretation in `esphome.yaml`:
- `Restzeit = x[0]`

### 4) Init/Programm/Optionen

- `dest`: `0x25`
- `cmd`: `0x2010`
- `payload`: langes Mehrbyte-Format

Bestaetigt beobachtet:
- Beispielpayload: `0x0d000001050062000037010000`
- Direkt danach wurden aktualisiert:
  - `Option VarioSpeed = OFF`
  - `Option IntensivZone = OFF`
  - `Option Hygiene = OFF`
  - `Option Glanztrocknen = OFF`
  - `bsh_helper_init = 'Auto 45-65°'`
  - `Ausgewaehltes Programm = 'Auto 45-65°'`

Evidenzbeispiele:
- `spuelmaschine_log.txt:334`
- `spuelmaschine_log.txt:335`
- `spuelmaschine_log.txt:343`
- `spuelmaschine_log.txt:344`

Interpretation in `esphome.yaml` (aktueller Stand):
- Programmcode aus `x[0]` (z. B. `0x0D -> Auto 45-65°`)
- Optionsbits aus `x[8]` (`0x80`, `0x40`, `0x08`, `0x02`)

## Noch nicht final bestaetigt

Folgende Telegramme wurden oft gesehen, aber ohne direkte Sensor-Korrelation in diesem Log oder noch ohne klare Semantik:
- `0x25 / 0x2000`
- `0x25 / 0x2004`
- `0x25 / 0x2005`
- `0x55 / 0x5003`, `0x55 / 0x5006`, `0x55 / 0x5008`
- `0x22 / 0x40f2`, `0x22 / 0x7ff1`
- `0x17 / 0x1001`, `0x17 / 0x1007`, `0x17 / 0x1013`

Diese sind als naechster Analyseblock vorgesehen.

## Bezug zur ESPHome-Config

Ziel bleibt eine vollstaendige `esphome.yaml`, die den beobachteten DBUS-Verkehr robust dekodiert.

Der aktuelle Stand in `esphome.yaml` deckt die Kernpunkte bereits ab (Tuer, Running, Restzeit, Zeitvorwahl, Programm/Optionen) und ist die Arbeitsbasis fuer den weiteren Ausbau.
