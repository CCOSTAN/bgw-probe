# BGW Probe

BGW Probe turns the read-only status pages on AT&T BGW gateways into a small,
stable JSON API. It can run as a CLI for one-shot diagnostics or as a hardened
Docker container for Home Assistant, Prometheus adapters, and other local
automation tools.

The initial release is tested with a BGW210-700. The parser targets page and
field names shared by BGW210 and BGW320 firmware, but additional gateway and
firmware reports are welcome.

## What it exposes

- Gateway model, firmware, manufacturer, and uptime
- Broadband connection and line state
- Negotiated speed and duplex
- Packet, byte, drop, error, collision, and discard counters
- High-level firewall feature states
- Collector freshness and per-page success or failure

The output deliberately excludes serial numbers, MAC addresses, IP addresses,
DNS addresses, Wi-Fi settings, logs, and credentials.

## Quick start

```bash
cp .env.example .env
# Edit BGW_URL if your gateway does not use the default address.
docker compose up -d --build
curl http://127.0.0.1:8080/api/v1/status
```

The gateway commonly uses a self-signed certificate, so certificate validation
is disabled by default. Keep the probe and its API on a trusted local network.

## CLI

BGW Probe has no runtime dependencies outside the Python standard library.

```bash
python -m pip install .
BGW_URL=https://192.168.1.254 bgw-probe once --pretty
BGW_URL=https://192.168.1.254 bgw-probe serve
```

## API

- `GET /healthz` checks the local process.
- `GET /readyz` succeeds after a recent, usable gateway collection.
- `GET /api/v1/status` returns the cached, allowlisted gateway snapshot.

The service polls independently, so each downstream consumer reads cached data
instead of creating another session against the gateway.

## Home Assistant

The package in [`examples/home-assistant/bgw_probe.yaml`](examples/home-assistant/bgw_probe.yaml)
uses one REST request to create connectivity, uptime, and traffic entities.
Copy it into your package directory, replace `PROBE_HOST`, and run a Home
Assistant configuration check before restarting.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `BGW_URL` | `https://192.168.1.254` | Gateway root URL |
| `BGW_TIMEOUT_SECONDS` | `8` | Per-page request timeout |
| `BGW_POLL_INTERVAL_SECONDS` | `60` | Collection interval |
| `BGW_TLS_VERIFY` | `false` | Verify the gateway certificate |
| `BGW_BIND` | `0.0.0.0` | API bind address inside the container |
| `BGW_PORT` | `8080` | API port inside the container |

No access code is needed for the pages collected by version 0.1. See
[`SECURITY.md`](SECURITY.md) for the credential policy that future authenticated
collectors must follow.

## Related work

The endpoint coverage review in
[`TheSethRose/BGW320-CLI`](https://github.com/TheSethRose/BGW320-CLI) helped
identify the shared BGW status-page surface. BGW Probe is an independent,
standard-library implementation with a deliberately narrow, read-only output.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
docker build -t bgw-probe:test .
```

BGW Probe is available under the MIT License.
