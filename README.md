# BSH DBus Analysis (Siemens Dishwasher)

Dieses Repo analysiert den ESPHome-Debug-Log einer Siemens-Spülmaschine (BSH DBus), um die seriellen Pakete auf dem Bus zu verstehen und korrekt in ESPHome abzubilden.

## Ziel

Ein robustes `esphome.yaml`, das relevante DBus-Telegramme des Geräts interpretiert und als Home Assistant Sensoren bereitstellt (Tür, Restzeit, Programm, Optionen, Verbrauchsmittelstatus).

## Dateien

| Datei / Ordner | Inhalt |
|---|---|
| `esphome.yaml` | Aktuelle ESPHome-Konfiguration für ESP32-C6 |
| `parse_log.py` | Parser zur Frame-Extraktion und Sensor-Korrelation |
| `COMMANDS.md` | Vollständige Referenz aller bekannten Commands und Payloads |
| `auto_45_65_logs/` | Rohlogs und Parse-Ausgaben für Programm Auto 45-65° |
| `auto_65_75_logs/` | Rohlogs und Parse-Ausgaben für Programm Auto 65-75° |

## Parser (`parse_log.py`)

Der Parser verarbeitet ESPHome-Logs im Format:

```text
[18:11:33.591][D][main:432]: Received frame dest 0x24 cmd 0x2006: 0x00
[18:11:33.659][D][binary_sensor:047]: 'Tür' >> ON
```

Er extrahiert `dest`, `cmd` und `payload` und korreliert direkt folgende Sensor-Zeilen mit dem jeweils letzten Frame innerhalb eines konfigurierbaren Zeitfensters.

**Verwendung:**

```bash
python parse_log.py <logfile>
python parse_log.py <logfile> --events       # Zeitliche Abfolge aller Frame-Events
python parse_log.py <logfile> --json-out result.json
python parse_log.py <logfile> --max-lag-ms 500  # Korrelationsfenster anpassen
```

## Log-Namenskonvention

```text
<programm>_logs/spuelmaschine_log_YYYY-MM-DD_HHMMSS.txt
<programm>_logs/spuelmaschine_log_YYYY-MM-DD_HHMMSS_parsed.txt
```

Zeitstempel = Aufnahmezeitpunkt des Logs (nicht Importdatum).

## Erkenntnisse

Alle analysierten Commands, Payloads, Bit-Strukturen und Konfidenzlevels sind in **[COMMANDS.md](COMMANDS.md)** dokumentiert.
