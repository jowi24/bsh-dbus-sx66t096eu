# CLAUDE.md — Projektkontext für Claude Code

## Projekt

Reverse-Engineering des BSH-DBus-Protokolls einer Siemens-Spülmaschine (SX66T096EU) via ESP32-C6 mit ESPHome. Ziel: ein robustes `esphome.yaml`, das DBus-Frames korrekt als Home Assistant Sensoren abbildet.

## Wichtige Dateien

| Datei / Ordner | Zweck |
|---|---|
| `COMMANDS.md` | Vollständige Referenz aller bekannten Frames, Payloads, Bitfelder und Konfidenzlevels — **immer aktuell halten** |
| `esphome.yaml` | Aktuelle ESPHome-Konfiguration; enthält bereits bestätigte Sensor-Mappings |
| `parse_log.py` | Parser für ESPHome-Logs → extrahiert Frames, korreliert Sensor-Ausgaben |
| `*_logs/` | Rohlogs und `_parsed.txt` je Programm |
| `README.md` | Nur Scope + Parser-Doku; keine Findings |

## Workflow: Neues Log verarbeiten

Wenn ein rohes Log im Root-Verzeichnis liegt (`spuelmaschine_YYYYMMDD_HHMMSS.txt`):

1. **Programm identifizieren** — Frames `0x17/0x1011` oder `0x25/0x2010` Byte 0 (Programm-ID-Tabelle in COMMANDS.md). Fallback: `0x55/0x5003` (nominale Restzeit) und `0x25/0x2004` Bit 17 (Niedertemperatur-Flag).

2. **Zielordner und Dateiname bestimmen:**
   ```
   <programm>_logs/spuelmaschine_log_YYYY-MM-DD_HHMMSS.txt
   ```
   Zeitstempel = erster `[HH:MM:SS...]`-Eintrag im Log (**UTC**, nicht MESZ).

3. **Datei verschieben und parsen:**
   ```bash
   cp spuelmaschine_YYYYMMDD_HHMMSS.txt <ziel>.txt
   python parse_log.py <ziel>.txt > <ziel>_parsed.txt
   git rm spuelmaschine_YYYYMMDD_HHMMSS.txt
   ```

4. **Phasenverlauf analysieren** — Frames `0x25/0x2005` (Phasenstatus) und `0x25/0x2008` (Restzeit) zeitlich auswerten. Auf `0x12`-Übergänge und unbekannte `0x2004`-Werte achten.

5. **COMMANDS.md aktualisieren** — neues Log in Legende eintragen, Tabellen und Erkenntnisse ergänzen. Konfidenzlevel beachten: ✅ Bestätigt / 🟡 Plausibel / ❓ Unklar.

6. **Commit, Push, PR** auf Branch `claude/review-new-log-yy9kT` → `main`.

## Technischer Kontext

### Log-Format
```
[HH:MM:SS.mmm][D][main:432]: Received frame dest 0x24 cmd 0x2006: 0x08
```
Zeitstempel sind **UTC**. Lokale Zeit (MESZ) = UTC + 2h.

### Programm-IDs (`0x17/0x1011` und `0x25/0x2010` Byte 0)
| ID | Programm |
|---|---|
| `0x10` | Auto 35-45° |
| `0x0d` | Auto 45-65° |
| `0x0b` | Auto 65-75° |
| `0x0e` | Eco 50° |
| `0x11` | Schnell 45° |
| `0x12` | Vorspülen |

### Log-Buchstaben (bisher)
`A`=Auto45-65° Mar-12, `B`=Auto65-75° Mar-25, `C`=Auto65-75° Mar-28, `D`=Auto35-45°+IZ Mar-29, `E`=Eco50° Apr-01, `F`=Auto45-65° Apr-03, `G`=Auto45-65° Apr-04, `H`=Auto45-65° Apr-05, `I`=Auto45-65° Apr-11, `J`=Auto45-65° Apr-14 (Zeitvorwahl 7h), `K`=Auto45-65° Apr-18 (Zeitvorwahl ~58min), `L`=Auto45-65° Apr-23 (mid-run, neue 0x2004-Trocknen-Flags), `M`=Auto65-75° Apr-26 (0× 0x12, kurz, bestätigt Bit13=Glanztrocknen). Nächstes Log = `N`.

### Schlüssel-Frames
| Frame | Bedeutung |
|---|---|
| `0x25/0x2005` | Programmphase: `0x21`=Init, `0x22`=läuft, `0x12`=Übergang, `0x24`=Klarspülen, `0x28`=Trocknen, `0x20`=Ende |
| `0x25/0x2008` | Restzeit in Minuten (Byte 0) |
| `0x25/0x2010` | Programm-Init-Frame (13 Byte); Byte 0 = Programm-ID, Byte 8 = Optionen |
| `0x27/0x2007` | `0x01`=läuft, `0x03`=Programmende, `0x02`=Standby/bereit |
| `0x24/0x2006` | Bit 3=Tür(inv), Bit 1=Klarspüler leer, Bit 0=Salz leer |
| `0x17/0x1000` | Panel-Optionen: Bit7=VarioSpeed, Bit6=IntensivZone, Bit3=Hygiene, Bit1=Glanz |
| `0x55/0x5003` | Nominale Restzeit bei Programmstart (20× Burst) |

### Dispenser-Öffnung
Das Tab-Fach öffnet beim Start des Hauptspülens:
- Ohne Vorspülen (1× `0x12`): beim ersten `0x2005=0x22` nach `0x21`
- Mit Vorspülen (2–4× `0x12`): vermutlich beim ersten `0x12`-Übergang (nicht physisch bestätigt)

### Adaptivität
Die Anzahl der `0x12`-Übergänge bei Auto 45-65° variiert je nach Verschmutzungsgrad: 1×, 2×, 3× oder 4× beobachtet. Die Restzeit wird bei jedem `0x12`-Übergang neu geschätzt (kann stark springen).

## Git-Workflow

- **Entwicklungsbranch:** `claude/review-new-log-yy9kT`
- Immer von `main` mergen bevor neue Änderungen committet werden
- PR nach `main`; Repo: `jowi24/bsh-dbus-sx66t096eu`
