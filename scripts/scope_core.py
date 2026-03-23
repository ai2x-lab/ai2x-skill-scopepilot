from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
import math
from typing import Any

try:
    import pyvisa
except ImportError:
    pyvisa = None

from logger import ActionLogger


def build_backend_hint() -> str:
    return (
        "No VISA backend found.\n"
        "Install one of the following:\n"
        "  1. Pure Python backend: pip install pyvisa-py\n"
        "  2. Vendor backend: NI-VISA or Keysight IO Libraries Suite\n"
    )


def open_resource_manager(visa_backend: str | None = None):
    if pyvisa is None:
        raise RuntimeError("pyvisa is not installed. Run: pip install -r requirements.txt")

    try:
        if visa_backend:
            return pyvisa.ResourceManager(visa_backend)
        return pyvisa.ResourceManager()
    except ValueError as exc:
        raise RuntimeError(f"{exc}\n\n{build_backend_hint()}") from exc


def render(template: str, **values: Any) -> str:
    return template.format(**values)


def expand_scale_values(rule: dict[str, Any]) -> list[float]:
    sequence = rule["sequence"]
    min_value = float(rule["min"])
    max_value = float(rule["max"])
    values: list[float] = []
    decade = math.floor(math.log10(min_value)) - 1
    upper_decade = math.ceil(math.log10(max_value)) + 1

    for power in range(decade, upper_decade + 1):
        multiplier = 10 ** power
        for base in sequence:
            candidate = float(base) * multiplier
            if min_value <= candidate <= max_value:
                values.append(candidate)

    return sorted(set(values))


def normalize_scale_value(
    requested: float,
    rule: dict[str, Any],
    mode: str = "nearest",
) -> float:
    if requested <= 0:
        raise ValueError("Scale must be > 0.")

    values = expand_scale_values(rule)
    if not values:
        raise ValueError("Scale rule did not produce any valid values.")

    if requested <= values[0]:
        return values[0]
    if requested >= values[-1]:
        return values[-1]

    if mode == "nearest":
        return min(values, key=lambda item: abs(item - requested))

    if mode == "floor":
        floor_values = [item for item in values if item <= requested]
        return floor_values[-1]

    if mode == "ceil":
        ceil_values = [item for item in values if item >= requested]
        return ceil_values[0]

    raise ValueError(f"Unsupported normalize mode '{mode}'")


@dataclass
class ScopeSession:
    resource_name: str
    profile_name: str
    profile: dict[str, Any]
    visa_backend: str | None = None
    timeout_ms: int = 5000
    logger: ActionLogger | None = None

    def __post_init__(self) -> None:
        self.rm = open_resource_manager(self.visa_backend)
        self.inst = self.rm.open_resource(self.resource_name)
        self.inst.timeout = self.timeout_ms
        self.inst.read_termination = "\n"
        self.inst.write_termination = "\n"

    def close(self) -> None:
        try:
            self.inst.close()
        finally:
            self.rm.close()

    def log(self, event: str, **payload: Any) -> None:
        if self.logger is not None:
            self.logger.log(
                event,
                resource=self.resource_name,
                profile=self.profile_name,
                **payload,
            )

    def write(self, command: str) -> None:
        self.log("scpi_write", command=command)
        self.inst.write(command)

    def query(self, command: str) -> str:
        self.log("scpi_query", command=command)
        response = str(self.inst.query(command)).strip()
        self.log("scpi_response", command=command, response=response)
        return response

    def reset(self) -> None:
        self.write("*RST")
        self.write("*CLS")
        time.sleep(2.0)

    def identify(self) -> str:
        command = self.profile["commands"]["identify"]
        return self.query(command)

    def channel_name(self, channel: int) -> str:
        pattern = self.profile["channel_format"]
        return render(pattern, index=channel)

    def _display_value(self, enabled: bool) -> str:
        mapping = self.profile["value_map"]
        return mapping["on"] if enabled else mapping["off"]

    def set_channel_display(self, channel: int, enabled: bool) -> None:
        name = self.channel_name(channel)
        command = render(
            self.profile["commands"]["set_channel_display"],
            channel=name,
            value=self._display_value(enabled),
        )
        self.write(command)
        self.log("channel_display", channel=name, enabled=enabled)

    def set_vertical_scale(self, channel: int, scale: float) -> None:
        rule = self.profile["scale_rules"]["vertical"]
        normalized = normalize_scale_value(scale, rule)
        name = self.channel_name(channel)
        command = render(
            self.profile["commands"]["set_vertical_scale"],
            channel=name,
            value=normalized,
        )
        self.write(command)
        self.log(
            "channel_scale",
            channel=name,
            requested_scale=scale,
            applied_scale=normalized,
            unit=rule.get("unit", "V/div"),
        )
        return normalized

    def set_time_scale(self, scale: float) -> None:
        rule = self.profile["scale_rules"]["time"]
        normalized = normalize_scale_value(scale, rule)
        command = render(
            self.profile["commands"]["set_time_scale"],
            value=normalized,
        )
        self.write(command)
        self.log(
            "time_scale",
            requested_scale=scale,
            applied_scale=normalized,
            unit=rule.get("unit", "s/div"),
        )
        return normalized

    def measure(self, channel: int, item: str) -> float:
        name = self.channel_name(channel)
        source_command = render(
            self.profile["commands"]["measure_source"],
            channel=name,
        )
        self.write(source_command)

        measure_map = self.profile["commands"]["measure"]
        if item not in measure_map:
            raise ValueError(f"Unsupported measurement '{item}'")

        result = float(self.query(measure_map[item]))
        self.log("measurement", channel=name, item=item, value=result)
        return result

    def list_capabilities(self) -> dict[str, bool]:
        return dict(self.profile.get("capabilities", {}))

    def run_acquisition(self) -> None:
        command = self.profile["commands"]["run_acquisition"]
        self.write(command)
        self.log("run_acquisition")

    def stop_acquisition(self) -> None:
        command = self.profile["commands"]["stop_acquisition"]
        self.write(command)
        self.log("stop_acquisition")

    def capture_screenshot(self, output_path: str) -> str:
        capture = self.profile["commands"]["capture"]
        for command in capture.get("setup", []):
            self.write(command)

        query = capture["query_binary"]
        self.log("capture_query", command=query, output_path=output_path)
        data = self.inst.query_binary_values(
            query,
            datatype="B",
            container=bytes,
        )

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self.log("capture_saved", output_path=str(path), size=len(data))
        return str(path)
