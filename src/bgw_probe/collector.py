"""Fetch and normalize the gateway's read-only status pages."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import socket
import ssl
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .parser import parse_fiber_sensors, parse_label_value_rows

PAGE_PATHS = {
    "system": "/cgi-bin/sysinfo.ha",
    "broadband": "/cgi-bin/broadbandstatistics.ha",
    "firewall": "/cgi-bin/firewall.ha",
    "fiber": "/cgi-bin/fiberstat.ha",
}


def _text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())[:128]
    return cleaned or None


def _status(value: str | None) -> str | None:
    cleaned = _text(value)
    return cleaned.lower() if cleaned else None


def _number(value: str | None) -> int | float | None:
    if value is None:
        return None
    candidate = value.replace(",", "").strip().split()[0]
    try:
        parsed = float(candidate)
    except (ValueError, IndexError):
        return None
    return int(parsed) if parsed.is_integer() else parsed


def _scaled_number(value: str | None, divisor: int = 1) -> int | float | None:
    number = _number(value)
    if number is None:
        return None
    scaled = number / divisor
    return int(scaled) if scaled.is_integer() else scaled


def _duration_seconds(value: str | None) -> int | None:
    if not value:
        return None
    parts = value.strip().split(":")
    if len(parts) not in {3, 4}:
        return None
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return None
    if len(numbers) == 3:
        days = 0
        hours, minutes, seconds = numbers
    else:
        days, hours, minutes, seconds = numbers
    if min(numbers) < 0 or minutes > 59 or seconds > 59:
        return None
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _without_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


class GatewayClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ssl_context: ssl.SSLContext | None = None
        if settings.gateway_url.startswith("https://"):
            if settings.tls_verify:
                self._ssl_context = ssl.create_default_context()
            else:
                self._ssl_context = ssl._create_unverified_context()  # noqa: SLF001

    def fetch(self, page: str) -> str:
        path = PAGE_PATHS[page]
        request = Request(
            f"{self.settings.gateway_url}{path}",
            headers={"User-Agent": "bgw-probe/0.1"},
        )
        with urlopen(
            request,
            context=self._ssl_context,
            timeout=self.settings.timeout_seconds,
        ) as response:
            return response.read(1_000_000).decode("utf-8", "replace")


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, URLError):
        return "network_error"
    if isinstance(exc, ValueError):
        return "parse_error"
    return "unexpected_error"


class Collector:
    def __init__(self, fetch: Callable[[str], str]) -> None:
        self.fetch = fetch

    def collect(self) -> dict[str, Any]:
        started = time.monotonic()
        parsed: dict[str, dict[str, str]] = {}
        raw_pages: dict[str, str] = {}
        failures: dict[str, str] = {}

        for page in PAGE_PATHS:
            try:
                html = self.fetch(page)
                raw_pages[page] = html
                values = parse_label_value_rows(html)
                if not values:
                    raise ValueError("no table rows")
                parsed[page] = values
            except Exception as exc:  # Each page is an independent probe.
                failures[page] = _safe_error(exc)

        system = parsed.get("system", {})
        broadband = parsed.get("broadband", {})
        firewall = parsed.get("firewall", {})
        fiber = parsed.get("fiber", {})
        fiber_sensors = parse_fiber_sensors(raw_pages.get("fiber", ""))
        gateway_data = _without_none(
            {
                "manufacturer": _text(system.get("Manufacturer")),
                "model": _text(system.get("Model Number")),
                "firmware": _text(system.get("Software Version")),
                "uptime_seconds": _duration_seconds(
                    system.get("Time Since Last Reboot")
                ),
            }
        )
        broadband_data = _without_none(
            {
                "connection": _status(broadband.get("Broadband Connection")),
                "network_type": _text(broadband.get("Broadband Network Type")),
                "line_state": _status(broadband.get("Line State")),
                "speed_mbps": _number(broadband.get("Current Speed (Mbps)")),
                "duplex": _status(broadband.get("Current Duplex")),
                "rx_packets": _number(broadband.get("Receive Packets")),
                "tx_packets": _number(broadband.get("Transmit Packets")),
                "rx_bytes": _number(broadband.get("Receive Bytes")),
                "tx_bytes": _number(broadband.get("Transmit Bytes")),
                "rx_drops": _number(broadband.get("Receive Drops")),
                "tx_drops": _number(broadband.get("Transmit Drops")),
                "rx_errors": _number(broadband.get("Receive Errors")),
                "tx_errors": _number(broadband.get("Transmit Errors")),
                "collisions": _number(broadband.get("Collisions")),
                "tx_discards": _number(broadband.get("Transmit Discards")),
            }
        )
        firewall_data = _without_none(
            {
                "packet_filter": _status(firewall.get("Packet Filter")),
                "ip_passthrough": _status(firewall.get("IP Passthrough")),
                "nat_default_server": _status(firewall.get("NAT Default Server")),
                "advanced": _status(firewall.get("Firewall Advanced")),
            }
        )
        fiber_data = _without_none(
            {
                "optical_wan_operational_status": _status(
                    fiber.get("Optical WAN Operational Status")
                ),
                "link_state": _status(fiber.get("Link State")),
                "fiber_module": _status(fiber.get("Fiber Module")),
                "opt_powerlvl": _number(fiber.get("OPT Powerlvl")),
                "opt_los": _number(fiber.get("OPT LOS")),
                "opt_tx_fault": _number(fiber.get("OPT Tx Fault")),
                "opt_tx_disable": _number(fiber.get("OPT Tx Disable")),
                "rx_los_state": _number(fiber.get("Rx LOS State")),
                "tx_fault_state": _number(fiber.get("Tx Fault State")),
                "tx_disable_state": _number(fiber.get("Tx Disable State")),
                "rate_select_state": _number(fiber.get("Rate Select State")),
                "data_ready_bar_state": _number(fiber.get("Data Ready Bar State")),
                "wave_length": _number(fiber.get("Wave Length")),
                "length_smf_km": _number(fiber.get("Length SMF-km")),
            }
        )
        sensor_values: dict[str, dict[str, Any]] = {}
        for name, source_name, divisor in (
            ("temperature_c", "temperature", 1),
            ("vcc", "vcc", 1),
            ("tx_bias", "tx_bias", 1),
            ("tx_power_dbm", "tx_power", 10),
            ("rx_power_dbm", "rx_power", 10),
        ):
            sensor_data = _without_none(
                {
                    field: _scaled_number(value, divisor)
                    for field, value in fiber_sensors.get(source_name, {}).items()
                }
            )
            if sensor_data:
                sensor_values[name] = sensor_data
        fiber_data["sensors"] = sensor_values

        required_data_ok = bool(gateway_data.get("model")) and bool(
            broadband_data.get("connection")
        )
        if not parsed or not required_data_ok:
            overall = "error"
        elif failures:
            overall = "degraded"
        else:
            overall = "ok"

        return {
            "schema_version": 1,
            "status": overall,
            "collected_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "gateway": gateway_data,
            "broadband": broadband_data,
            "firewall": firewall_data,
            "fiber": fiber_data,
            "collector": {
                "duration_ms": round((time.monotonic() - started) * 1000),
                "successful_pages": sorted(parsed),
                "failed_pages": failures,
            },
        }
