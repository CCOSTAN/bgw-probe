"""Small HTML table parser for gateway status pages."""

from __future__ import annotations

from html import unescape
from html.parser import HTMLParser


def clean_text(value: str) -> str:
    return " ".join(unescape(value).replace("\xa0", " ").split())


class _TableRows(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
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
                self.rows.append(self._row)
            self._row = None
            self._cell = None


def parse_label_value_rows(html: str) -> dict[str, str]:
    parser = _TableRows()
    parser.feed(html)
    values: dict[str, str] = {}
    for row in parser.rows:
        label = row[0].strip().rstrip(":")
        value = row[1].strip()
        if label and label not in values:
            values[label] = value
    return values
