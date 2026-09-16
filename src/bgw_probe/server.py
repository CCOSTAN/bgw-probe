"""Minimal HTTP server and polling loop."""

from __future__ import annotations

from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import threading
import time
from typing import Any

from .collector import Collector

LOGGER = logging.getLogger(__name__)


class StateStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict[str, Any] | None = None
        self._updated_monotonic: float | None = None

    def put(self, snapshot: dict[str, Any]) -> None:
        with self._lock:
            self._snapshot = deepcopy(snapshot)
            self._updated_monotonic = time.monotonic()

    def get(self) -> dict[str, Any] | None:
        with self._lock:
            if self._snapshot is None or self._updated_monotonic is None:
                return None
            snapshot = deepcopy(self._snapshot)
            snapshot["age_seconds"] = round(
                max(0.0, time.monotonic() - self._updated_monotonic), 1
            )
            return snapshot


class Poller(threading.Thread):
    def __init__(
        self,
        collector: Collector,
        store: StateStore,
        interval_seconds: int,
    ) -> None:
        super().__init__(name="bgw-poller", daemon=True)
        self.collector = collector
        self.store = store
        self.interval_seconds = interval_seconds
        self.stop_event = threading.Event()

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.store.put(self.collector.collect())
            except Exception as exc:  # Keep serving health while a probe fails.
                LOGGER.error("probe cycle failed: %s", type(exc).__name__)
            self.stop_event.wait(self.interval_seconds)

    def stop(self) -> None:
        self.stop_event.set()


class ProbeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        store: StateStore,
        max_ready_age_seconds: int,
    ) -> None:
        super().__init__(address, ProbeHandler)
        self.store = store
        self.max_ready_age_seconds = max_ready_age_seconds


class ProbeHandler(BaseHTTPRequestHandler):
    server: ProbeServer

    def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._json(HTTPStatus.OK, {"status": "ok"})
            return

        snapshot = self.server.store.get()
        if self.path == "/readyz":
            ready = bool(
                snapshot
                and snapshot.get("status") != "error"
                and float(snapshot.get("age_seconds", 0))
                <= self.server.max_ready_age_seconds
            )
            self._json(
                HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE,
                {"status": "ready" if ready else "not_ready"},
            )
            return

        if self.path == "/api/v1/status":
            if snapshot is None:
                self._json(
                    HTTPStatus.SERVICE_UNAVAILABLE,
                    {"status": "starting", "schema_version": 1},
                )
            else:
                self._json(HTTPStatus.OK, snapshot)
            return

        self._json(HTTPStatus.NOT_FOUND, {"status": "not_found"})

    def log_message(self, format: str, *args: object) -> None:
        LOGGER.info("http %s", args[1] if len(args) > 1 else "request")
