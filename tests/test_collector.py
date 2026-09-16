import unittest

from bgw_probe.collector import Collector

PAGES = {
    "system": """
      <table>
        <tr><td>Manufacturer</td><td>ARRIS</td></tr>
        <tr><td>Model Number</td><td>BGW210-700</td></tr>
        <tr><td>Serial Number</td><td>SECRET-SERIAL</td></tr>
        <tr><td>Software Version</td><td>4.28.8</td></tr>
        <tr><td>MAC Address</td><td>00:11:22:33:44:55</td></tr>
        <tr><td>Time Since Last Reboot</td><td>01:02:03:04</td></tr>
      </table>
    """,
    "broadband": """
      <table>
        <tr><td>Broadband Connection</td><td>Up</td></tr>
        <tr><td>Broadband Network Type</td><td>Ethernet</td></tr>
        <tr><td>Broadband IPv4 Address</td><td>203.0.113.25</td></tr>
        <tr><td>Line State</td><td>Up</td></tr>
        <tr><td>Current Speed (Mbps)</td><td>1000</td></tr>
        <tr><td>Receive Bytes</td><td>1,234</td></tr>
        <tr><td>Transmit Errors</td><td>2</td></tr>
      </table>
    """,
    "firewall": """
      <table>
        <tr><td>Packet Filter</td><td>On</td></tr>
        <tr><td>IP Passthrough</td><td>Off</td></tr>
      </table>
    """,
}


class CollectorTests(unittest.TestCase):
    def test_collector_allowlists_safe_fields(self) -> None:
        result = Collector(PAGES.__getitem__).collect()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["gateway"]["uptime_seconds"], 93784)
        self.assertEqual(result["broadband"]["rx_bytes"], 1234)
        self.assertEqual(result["broadband"]["tx_errors"], 2)
        rendered = str(result)
        self.assertNotIn("SECRET-SERIAL", rendered)
        self.assertNotIn("00:11:22:33:44:55", rendered)
        self.assertNotIn("203.0.113.25", rendered)

    def test_collector_reports_partial_failure_without_exception_text(self) -> None:
        def fetch(page: str) -> str:
            if page == "firewall":
                raise TimeoutError("contains-private-host")
            return PAGES[page]

        result = Collector(fetch).collect()
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(
            result["collector"]["failed_pages"], {"firewall": "timeout"}
        )
        self.assertNotIn("contains-private-host", str(result))


if __name__ == "__main__":
    unittest.main()
