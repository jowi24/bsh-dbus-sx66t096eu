#!/usr/bin/env python3
"""Parse ESPHome BSH dishwasher logs and correlate sensor updates to received frames.

Examples:
  python3 parse_log.py spuelmaschine_log.txt
  python3 parse_log.py spuelmaschine_log.txt --events
  python3 parse_log.py spuelmaschine_log.txt --json-out result.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from typing import Any

FRAME_RE = re.compile(
    r"^\[(?P<ts>[^\]]+)\]\[[A-Z]\]\[main:\d+\]: Received frame dest "
    r"(?P<dest>0x[0-9a-fA-F]+) cmd (?P<cmd>0x[0-9a-fA-F]+): (?P<payload>0x[0-9a-fA-F]*)\s*$"
)

SENSOR_RE = re.compile(
    r"^\[(?P<ts>[^\]]+)\]\[[A-Z]\]\[(?P<sensor_type>binary_sensor|sensor|text_sensor):\d+\]: "
    r"'(?P<name>[^']+)' >> (?P<value>.+)$"
)

TIMESTAMPED_RE = re.compile(r"^\[\d{2}:\d{2}:\d{2}\.\d{3}\]")
HEX_CONTINUATION_RE = re.compile(r"^[0-9a-fA-F\s]+$")


@dataclass
class SensorEvent:
    line_no: int
    timestamp: str
    sensor_type: str
    name: str
    value: str


@dataclass
class FrameEvent:
    line_no: int
    timestamp: str
    dest: str
    cmd: str
    payload: str
    sensors: list[SensorEvent]


def parse_time_to_ms(ts: str) -> int:
    """Convert HH:MM:SS.mmm into milliseconds (same-day reference)."""
    hh, mm, rest = ts.split(":")
    ss, msec = rest.split(".")
    return ((int(hh) * 3600 + int(mm) * 60 + int(ss)) * 1000) + int(msec)


def parse_log(path: str, max_lag_ms: int) -> tuple[list[FrameEvent], list[SensorEvent]]:
    frames: list[FrameEvent] = []
    unlinked_sensors: list[SensorEvent] = []

    active_frame: FrameEvent | None = None

    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.rstrip("\n")

            frame_match = FRAME_RE.match(line)
            if frame_match:
                active_frame = FrameEvent(
                    line_no=line_no,
                    timestamp=frame_match.group("ts"),
                    dest=frame_match.group("dest").lower(),
                    cmd=frame_match.group("cmd").lower(),
                    payload=frame_match.group("payload").lower(),
                    sensors=[],
                )
                frames.append(active_frame)
                continue

            # Some payloads continue in the next raw line without timestamp.
            if active_frame and not TIMESTAMPED_RE.match(line):
                stripped = line.strip()
                if stripped and HEX_CONTINUATION_RE.fullmatch(stripped):
                    active_frame.payload += stripped.replace(" ", "").lower()
                    continue

            sensor_match = SENSOR_RE.match(line)
            if sensor_match:
                sensor = SensorEvent(
                    line_no=line_no,
                    timestamp=sensor_match.group("ts"),
                    sensor_type=sensor_match.group("sensor_type"),
                    name=sensor_match.group("name"),
                    value=sensor_match.group("value"),
                )
                if active_frame is not None:
                    frame_ms = parse_time_to_ms(active_frame.timestamp)
                    sensor_ms = parse_time_to_ms(sensor.timestamp)
                    lag = sensor_ms - frame_ms

                    # Only map sensors that arrive very shortly after the frame.
                    if 0 <= lag <= max_lag_ms:
                        active_frame.sensors.append(sensor)
                    else:
                        unlinked_sensors.append(sensor)
                        active_frame = None
                else:
                    unlinked_sensors.append(sensor)
                continue

            # Any other timestamped log line breaks the implicit frame->sensor block.
            if TIMESTAMPED_RE.match(line):
                active_frame = None

    return frames, unlinked_sensors


def print_summary(frames: list[FrameEvent]) -> None:
    print("Unique packets (dest, cmd, payload):")

    packet_counts: Counter[tuple[str, str, str]] = Counter(
        (f.dest, f.cmd, f.payload) for f in frames
    )

    packet_sensors: defaultdict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
    for frame in frames:
        key = (frame.dest, frame.cmd, frame.payload)
        for sensor in frame.sensors:
            packet_sensors[key][f"{sensor.name} -> {sensor.value}"] += 1

    for dest, cmd, payload in sorted(packet_counts.keys()):
        count = packet_counts[(dest, cmd, payload)]
        print(f"- {dest}, {cmd}, {payload} (count={count})")
        sensors = packet_sensors[(dest, cmd, payload)]
        if sensors:
            top = ", ".join(f"{name} x{cnt}" for name, cnt in sensors.most_common(5))
            print(f"  sensors: {top}")


def print_events(frames: list[FrameEvent]) -> None:
    print("Frame events:")
    for frame in frames:
        if not frame.sensors:
            print(
                f"- line {frame.line_no}: {frame.dest} {frame.cmd} {frame.payload} -> (no direct sensor below)"
            )
            continue

        for sensor in frame.sensors:
            print(
                f"- line {frame.line_no}: {frame.dest} {frame.cmd} {frame.payload} -> "
                f"{sensor.name} = {sensor.value} (line {sensor.line_no})"
            )


def write_json(path: str, frames: list[FrameEvent], unlinked_sensors: list[SensorEvent]) -> None:
    payload: dict[str, Any] = {
        "frames": [
            {
                **asdict(frame),
                "sensors": [asdict(sensor) for sensor in frame.sensors],
            }
            for frame in frames
        ],
        "unlinked_sensors": [asdict(sensor) for sensor in unlinked_sensors],
    }

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse ESPHome log frames and correlate directly-following sensor lines "
            "to the most recent received frame."
        )
    )
    parser.add_argument("logfile", help="Path to log file (e.g. spuelmaschine_log.txt)")
    parser.add_argument(
        "--events",
        action="store_true",
        help="Print each frame event and mapped sensors instead of only unique packet summary.",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path to write parsed events as JSON.",
    )
    parser.add_argument(
        "--max-lag-ms",
        type=int,
        default=300,
        help=(
            "Max allowed time difference between frame and directly-following sensor line "
            "for mapping (default: 300ms)."
        ),
    )

    args = parser.parse_args()

    frames, unlinked_sensors = parse_log(args.logfile, args.max_lag_ms)

    if args.events:
        print_events(frames)
    else:
        print_summary(frames)

    print(f"\nTotal frames: {len(frames)}")
    print(f"Unlinked sensor lines: {len(unlinked_sensors)}")

    if args.json_out:
        write_json(args.json_out, frames, unlinked_sensors)
        print(f"JSON written to: {args.json_out}")


if __name__ == "__main__":
    main()
