# BSH DBus Analysis (Siemens Dishwasher)

This workspace is used to analyze an ESPHome debug log from a Siemens dishwasher (BSH DBus) to understand the serial packets on the bus and map them correctly in ESPHome.

## Goal

The goal is a robust `esphome.yaml` that correctly interprets relevant DBus telegrams from the appliance and exposes them as Home Assistant sensors.

Specifically:
- detect serial frames (`dest`, `cmd`, `payload`)
- correlate frames with directly following sensor events
- derive stable mapping rules for binary, numeric, and text sensors

## Current Files

- `spuelmaschine_log.txt`: raw ESPHome log (`Received frame ...` plus sensor log lines)
- `parse_log.py`: parser for frame extraction and frame-to-sensor correlation
- `esphome.yaml`: current working config for ESP32-C6 including `bshdbus`

## Parser Logic (`parse_log.py`)

The parser extracts fields from lines such as:

```text
Received frame dest 0x24 cmd 0x2006: 0x00
```

Extracted fields:
- `dest`
- `cmd`
- `payload`

It then maps directly following sensor lines to the last received frame, for example:

```text
[18:11:33.591][D][main:432]: Received frame dest 0x24 cmd 0x2006: 0x00
[18:11:33.659][D][binary_sensor:047]: 'Door' >> ON
```

Mapping result: `0x24 / 0x2006 / 0x00 -> Door ON`

Important details:
- Payload continuation lines without timestamp are detected and appended.
- Mapping uses a time window (default `--max-lag-ms 300`) so delayed system logs (for example `Uptime`, `WiFi Signal`) are not incorrectly linked.

## Findings So Far

Based on `spuelmaschine_log.txt`:
- total detected frames: `441`
- many cyclic frames have no direct sensor line below them (normal polling/status traffic)

Well-confirmed correlations:
- `dest 0x24, cmd 0x2006, payload 0x00` -> `Door (Tuer) ON`
- `dest 0x24, cmd 0x2006, payload 0x08` -> `Door (Tuer) OFF`
- `dest 0x27, cmd 0x2007, payload 0x01/0x02` -> `Status ON/OFF`
- `dest 0x25, cmd 0x2008, payload 0x..0000` -> `Remaining time (Restzeit)` (minutes from byte 0)
- `dest 0x25, cmd 0x2010` -> program/option data (including program name and option bits)

These observations are already implemented as first-level decoding in `esphome.yaml`.

## Current Config Status (`esphome.yaml`)

The current config already includes:
- UART + `bshdbus` receive path
- raw frame logging via `on_frame`
- decoding for:
  - door sensor (`Tuer`, `0x24/0x2006`)
  - running status (`0x27/0x2007`)
  - remaining time (`Restzeit`, `0x25/0x2008`)
  - delay start (`Zeitvorwahl`, `0x17/0x1012`)
  - program names and option bits via helper sensors (`0x17/0x1011`, `0x17/0x1000`, `0x25/0x2010`)

## Usage

Run parser:

```bash
python parse_log.py spuelmaschine_log.txt
python parse_log.py spuelmaschine_log.txt --events
python parse_log.py spuelmaschine_log.txt --json-out result.json
```

Optional tuning for stricter/looser correlation:

```bash
python parse_log.py spuelmaschine_log.txt --max-lag-ms 500
```

## Log Naming Convention

To keep multiple runs organized, store logs per program and use the log capture timestamp in filenames.

Pattern:

```text
<program>_logs/spuelmaschine_log_YYYY-MM-DD_HHMMSS.txt
<program>_logs/spuelmaschine_log_YYYY-MM-DD_HHMMSS_parsed.txt
```

Important:
- use the timestamp from when the log was recorded
- do not use the rename/import date if those differ

Example:

```text
auto_45_65_logs/spuelmaschine_log_2026-03-12_151857.txt
auto_45_65_logs/spuelmaschine_log_2026-03-12_151857_parsed.txt
```

## Next Steps

- label additional `dest/cmd` combinations systematically (especially `0x25/0x2000`, `0x25/0x2004`, `0x25/0x2005`)
- document bit and byte semantics per command
- move mappings in `esphome.yaml` step-by-step from "experimental" to "stable"
- final outcome: complete and clearly documented ESPHome config for this device
