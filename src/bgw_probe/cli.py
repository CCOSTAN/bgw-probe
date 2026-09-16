"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import logging

from .collector import Collector, GatewayClient
from .config import Settings
from .server import Poller, ProbeServer, StateStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bgw-probe",
        description="Read-only telemetry probe for AT&T BGW gateways",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    once = subparsers.add_parser("once", help="collect once and print JSON")
    once.add_argument("--pretty", action="store_true", help="indent JSON output")
    subparsers.add_parser("serve", help="poll and serve the cached JSON API")
    return parser


def main() -> int:
    args = _parser().parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = Settings.from_env()
    collector = Collector(GatewayClient(settings).fetch)

    if args.command == "once":
        snapshot = collector.collect()
        print(json.dumps(snapshot, indent=2 if args.pretty else None, sort_keys=True))
        return 1 if snapshot["status"] == "error" else 0

    store = StateStore()
    poller = Poller(collector, store, settings.poll_interval_seconds)
    server = ProbeServer(
        (settings.bind, settings.port),
        store,
        max_ready_age_seconds=max(60, settings.poll_interval_seconds * 3),
    )
    poller.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        poller.stop()
        server.shutdown()
        server.server_close()
    return 0
