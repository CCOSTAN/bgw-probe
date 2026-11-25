"""Small HTML table parser for gateway status pages."""

from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re


def clean_text(value: str) -> str:
    return " ".join(unescape(value).replace("\xa0", " ").split())


class _TableRows(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.values: dict[str, str] = {}
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None:
            if self._row is not None:
                self._row.append(clean_text("".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if len(self._row) >= 2:
                self._consume_row(self._row)
            self._row = None
            self._cell = None

    def _consume_row(self, row: list[str]) -> None:
        label = row[0].strip().rstrip(":")
        if label:
            self.values.setdefault(label, row[1].strip())


def parse_label_value_rows(html: str) -> dict[str, str]:
    parser = _TableRows()
    parser.feed(html)
    return parser.values


class _FiberSensorTables(_TableRows):
    _sensor_names = {
        "temperature": "temperature",
        "vcc": "vcc",
        "tx bias": "tx_bias",
        "tx power": "tx_power",
        "rx power": "rx_power",
    }
    _threshold = re.compile(r"\bThreshold\s+([-+]?\d+(?:\.\d+)?)", re.IGNORECASE)
    _current = re.compile(
        r"^\s*(Temperature|Vcc|Tx Bias|Tx Power|Rx Power)\s+Currently\s+"
        r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*$",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        super().__init__()
        self.sensors: dict[str, dict[str, str]] = {}
        self._heading: list[str] | None = None
        self._sensor: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h1":
            self._heading = []
            self._sensor = None
        elif tag == "table" and self._sensor is not None:
            summary = dict(attrs).get("summary")
            if summary and self._sensor.replace("_", " ") not in summary.lower():
                self._sensor = None
        super().handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        super().handle_data(data)
        if self._heading is not None:
            self._heading.append(data)

    def handle_endtag(self, tag: str) -> None:
        super().handle_endtag(tag)
        if tag == "table":
            self._sensor = None
        elif tag == "h1" and self._heading is not None:
            match = self._current.match(clean_text("".join(self._heading)))
            if match:
                key = self._sensor_names[match.group(1).lower()]
                self.sensors[key] = {"current": match.group(2)}
                self._sensor = key
            self._heading = None

    def _consume_row(self, row: list[str]) -> None:
        super()._consume_row(row)
        if self._sensor is None or len(row) < 3:
            return
        kind = row[0].strip().lower()
        if kind not in {"alarm", "warning"}:
            return
        for bound, value in zip(("low", "high"), row[1:3]):
            match = self._threshold.search(value)
            if match:
                self.sensors[self._sensor][f"{kind}_{bound}"] = match.group(1)


def parse_fiber_page(html: str) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    parser = _FiberSensorTables()
    parser.feed(html)
    return parser.values, parser.sensors
