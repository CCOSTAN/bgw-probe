# Security

BGW Probe is designed for trusted local networks. It does not provide
authentication or TLS for its own JSON endpoint, so bind it to a trusted LAN
address or localhost and do not publish it to the internet.

The collector uses an explicit allowlist. It intentionally excludes serial
numbers, MAC addresses, public and private IP addresses, DNS server addresses,
Wi-Fi settings, logs, and credentials from its output.

Version 0.1 does not require the gateway access code. Plaintext access-code
environment variables are intentionally unsupported. If authenticated pages
are added later, credentials must be supplied through a file such as
`/run/secrets/bgw_access_code` and must never be logged or returned by the API.

Please report security issues privately through GitHub's security advisory
feature rather than opening a public issue.
