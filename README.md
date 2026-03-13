# BSH DBus Analyse (Siemens Spuelmaschine)

Dieses Verzeichnis dient zur Analyse eines ESPHome-Debug-Logs einer Siemens Spuelmaschine (BSH DBus), um serielle Pakete auf der Leitung zu verstehen und in ESPHome sauber abzubilden.

## Ziel

Ziel ist eine robuste `esphome.yaml`, die relevante DBus-Telegramme der Maschine korrekt interpretiert und als Home-Assistant-Sensoren bereitstellt.

Konkret:
- serielle Frames erkennen (`dest`, `cmd`, `payload`)
- Frames mit direkt folgenden Sensor-Events korrelieren
- daraus stabile Mapping-Regeln fuer Binary-, Numeric- und Text-Sensoren ableiten

## Aktuelle Dateien

- `spuelmaschine_log.txt`: Roh-Log aus ESPHome (`Received frame ...` + Sensor-Logs)
- `parse_log.py`: Parser fuer Frame-Extraktion und Frame->Sensor-Korrelation
- `esphome.yaml`: aktuelle Arbeits-Config fuer den ESP32-C6 inkl. `bshdbus`

## Parser-Logik (`parse_log.py`)

Der Parser extrahiert aus Zeilen wie:

```text
Received frame dest 0x24 cmd 0x2006: 0x00
```

folgende Felder:
- `dest`
- `cmd`
- `payload`

Danach ordnet er direkt folgende Sensorzeilen dem zuletzt empfangenen Frame zu, z. B.:

```text
[18:11:33.591][D][main:432]: Received frame dest 0x24 cmd 0x2006: 0x00
[18:11:33.659][D][binary_sensor:047]: 'Tuer' >> ON
```

=> Mapping: `0x24 / 0x2006 / 0x00 -> Tuer ON`

Wichtig:
- Payload-Fortsetzungszeilen ohne Timestamp werden erkannt und angehaengt.
- Die Zuordnung nutzt ein Zeitfenster (Default `--max-lag-ms 300`), damit spaete System-Logs (z. B. `Uptime`, `WiFi Signal`) nicht falsch zugeordnet werden.

## Bisherige Erkenntnisse aus dem Log

Stand auf Basis von `spuelmaschine_log.txt`:
- Gesamtzahl erkannter Frames: `441`
- Viele zyklische Frames ohne direkte Sensorfolge (normal bei Polling/Status-Traffic)

Bisher gut bestaetigte Korrelationen:
- `dest 0x24, cmd 0x2006, payload 0x00` -> `Tuer ON`
- `dest 0x24, cmd 0x2006, payload 0x08` -> `Tuer OFF`
- `dest 0x27, cmd 0x2007, payload 0x01/0x02` -> `Status ON/OFF`
- `dest 0x25, cmd 0x2008, payload 0x..0000` -> `Restzeit` (Minutenwert aus Byte 0)
- `dest 0x25, cmd 0x2010` -> Programm-/Optionsdaten (u. a. Programmnamen und Option-Bits)

Diese Beobachtungen sind bereits in der aktuellen `esphome.yaml` als erste Dekodierung umgesetzt.

## Aktueller Config-Status (`esphome.yaml`)

Die aktuelle Config enthaelt bereits:
- UART + `bshdbus`-Empfang
- Roh-Frame-Logging via `on_frame`
- Dekodierung fuer
  - Tuersensor (`0x24/0x2006`)
  - Laufstatus (`0x27/0x2007`)
  - Restzeit (`0x25/0x2008`)
  - Zeitvorwahl (`0x17/0x1012`)
  - Programmnamen und Optionsbits ueber Helper-Sensoren (`0x17/0x1011`, `0x17/0x1000`, `0x25/0x2010`)

## Nutzung

Parser starten:

```bash
python parse_log.py spuelmaschine_log.txt
python parse_log.py spuelmaschine_log.txt --events
python parse_log.py spuelmaschine_log.txt --json-out result.json
```

Optionales Tuning fuer strengere/lockerere Zuordnung:

```bash
python parse_log.py spuelmaschine_log.txt --max-lag-ms 500
```

## Naechste Schritte

- Weitere `dest/cmd`-Kombinationen systematisch labeln (insb. `0x25/0x2000`, `0x25/0x2004`, `0x25/0x2005`)
- Bit- und Byte-Semantik pro Kommando dokumentieren
- Mapping in `esphome.yaml` schrittweise von "experimentell" auf "stabil" bringen
- Am Ende: vollstaendige, nachvollziehbar dokumentierte ESPHome-Config fuer dieses Geraet
