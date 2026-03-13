# Siemens BSH DBUS Documentation (Confirmed Formats)

This document describes the currently confirmed serial DBUS formats.

There are two confirmation levels:
- Log-confirmed: correlated from `spuelmaschine_log.txt` via `parse_log.py`.
- Functionally confirmed: implemented in `esphome.yaml` and currently working in operation.

## Data Source and Method

- Source: `spuelmaschine_log.txt`
- Analysis: `parse_log.py` with direct frame-to-sensor correlation
- Confirmation criteria:
  - sensor log line appears directly after the frame
  - time difference is within parser window (`--max-lag-ms`, default 300 ms)

Log analysis (current snapshot):
- `441` total frames
- `126` frames with directly correlated sensor events
- confirmed `dest/cmd` with sensor correlation:
  - `0x24 / 0x2006` (6x)
  - `0x27 / 0x2007` (3x)
  - `0x25 / 0x2008` (114x)
  - `0x25 / 0x2010` (2x)

## Cross-check with `esphome.yaml` (Already Working)

The following decoders are active in `esphome.yaml` and considered working:

- `0x24 / 0x2006`
  - `Rinse aid (Klarspueler)` (bit 1)
  - `Salt (Salz)` (bit 0)
  - `Door (Tuer)` (bit 3 inverted)
- `0x27 / 0x2007`
  - `Status` (running)
- `0x25 / 0x2008`
  - `Remaining time (Restzeit)` (minutes)
- `0x17 / 0x1012`
  - `Delay start (Zeitvorwahl)` (hours)
- `0x17 / 0x1000`
  - option bits from control panel (`VarioSpeed`, `IntensivZone`, `Hygiene`, `Shine & Dry (Glanztrocknen)`)
- `0x17 / 0x1011`
  - program names from control panel
- `0x25 / 0x2010`
  - init/program text and option bits (including mirrored template sensors)

## Generic Frame Format

ESPHome log format:

```text
Received frame dest 0xDD cmd 0xCCCC: 0xPPPP...
```

- `dest`: destination node (1 byte, hex)
- `cmd`: command (2 bytes, hex)
- `payload`: variable-length payload (hex)

Note: for long payloads, a continuation line without timestamp may follow. The parser merges these lines correctly.

## Confirmed Formats

### 1) Door Status (Tuer)

- `dest`: `0x24`
- `cmd`: `0x2006`
- `payload`: 1 byte

Observed:
- `payload 0x00` -> `Door (Tuer) ON` (open)
- `payload 0x08` -> `Door (Tuer) OFF` (closed)

Evidence examples:
- `spuelmaschine_log.txt:140` + `spuelmaschine_log.txt:141`
- `spuelmaschine_log.txt:142` + `spuelmaschine_log.txt:143`
- `spuelmaschine_log.txt:446` + `spuelmaschine_log.txt:447`

Interpretation in `esphome.yaml`:
- `door = !((x[0] >> 3) & 0x01)`

### 2) Running Status

- `dest`: `0x27`
- `cmd`: `0x2007`
- `payload`: 1 byte

Observed:
- `payload 0x01` -> `Status ON`
- `payload 0x02` -> `Status OFF`

Evidence examples:
- `spuelmaschine_log.txt:448` + `spuelmaschine_log.txt:449`
- `spuelmaschine_log.txt:346` + `spuelmaschine_log.txt:347`

Interpretation in `esphome.yaml`:
- `running = (x[0] == 0x01)`

### 3) Remaining Time (Restzeit)

- `dest`: `0x25`
- `cmd`: `0x2008`
- `payload`: 3 bytes (`0xMM0000` observed)

Observed:
- first payload byte (`MM`) equals remaining minutes.
- examples:
  - `0xa00000` -> `160 min`
  - `0x9f0000` -> `159 min`
  - `0x980000` -> `152 min`

Evidence examples:
- `spuelmaschine_log.txt:302` + `spuelmaschine_log.txt:303`
- `spuelmaschine_log.txt:471` + `spuelmaschine_log.txt:472`
- `spuelmaschine_log.txt:518` + `spuelmaschine_log.txt:519`

Interpretation in `esphome.yaml`:
- `Remaining time = x[0]`

### 4) Init / Program / Options

- `dest`: `0x25`
- `cmd`: `0x2010`
- `payload`: long multi-byte format

Confirmed observations:
- example payload: `0x0d000001050062000037010000`
- immediate updates afterwards:
  - `Option VarioSpeed = OFF`
  - `Option IntensivZone = OFF`
  - `Option Hygiene = OFF`
  - `Option Shine & Dry (Glanztrocknen) = OFF`
  - `bsh_helper_init = 'Auto 45-65°'`
  - `Selected Program (Ausgewähltes Programm) = 'Auto 45-65°'`

Evidence examples:
- `spuelmaschine_log.txt:334`
- `spuelmaschine_log.txt:335`
- `spuelmaschine_log.txt:343`
- `spuelmaschine_log.txt:344`

Interpretation in `esphome.yaml` (current):
- program code from `x[0]` (for example `0x0D -> Auto 45-65°`)
- option bits from `x[8]` (`0x80`, `0x40`, `0x08`, `0x02`)

## Not Yet Fully Confirmed

The following telegrams were frequently observed, but do not yet have clear semantics from direct sensor correlation in this log:
- `0x25 / 0x2000`
- `0x25 / 0x2004`
- `0x25 / 0x2005`
- `0x55 / 0x5003`, `0x55 / 0x5006`, `0x55 / 0x5008`
- `0x22 / 0x40f2`, `0x22 / 0x7ff1`
- `0x17 / 0x1001`, `0x17 / 0x1007`, `0x17 / 0x1013`

These are planned as the next analysis block.

## Relation to ESPHome Config

The goal remains a complete `esphome.yaml` that robustly decodes observed DBUS traffic.

The current `esphome.yaml` already covers the main points (door/Tuer, running/Status, remaining time/Restzeit, delay start/Zeitvorwahl, program/options) and is the working base for further expansion.
