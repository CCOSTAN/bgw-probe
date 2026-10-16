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
    "fiber": """
      <table>
        <tr><td>Optical WAN Operational Status</td><td>Up</td></tr>
        <tr><td>Link State</td><td>Up</td></tr>
        <tr><td>Fiber Module</td><td>Unavailable</td></tr>
        <tr><td>Alarm</td><td>0 (Threshold -50)</td></tr>
        <tr><td>Warning</td><td>0 (Threshold -45)</td></tr>
        <tr><td>OPT Powerlvl</td><td>2</td></tr>
        <tr><td>OPT LOS</td><td>0</td></tr>
        <tr><td>OPT Tx Fault</td><td>0</td></tr>
        <tr><td>OPT Tx Disable</td><td>0</td></tr>
        <tr><td>Rx LOS State</td><td>1</td></tr>
        <tr><td>Tx Fault State</td><td>0</td></tr>
        <tr><td>Tx Disable State</td><td>0</td></tr>
        <tr><td>Rate Select State</td><td>0</td></tr>
        <tr><td>Data Ready Bar State</td><td>0</td></tr>
        <tr><td>Wave Length</td><td>1270 nm</td></tr>
        <tr><td>Length SMF-km</td><td>40</td></tr>
        <tr><td>Vendor SN</td><td>SECRET-TRANSCEIVER-SERIAL</td></tr>
      </table>
      <h1>Temperature&nbsp;&nbsp;Currently 40</h1>
      <table summary="Temperature table">
        <tr><th></th><th>Low</th><th>High</th></tr>
        <tr><td>Alarm</td><td>0 (Threshold -50)</td><td>0 (Threshold 95)</td></tr>
        <tr><td>Warning</td><td>0 (Threshold -45)</td><td>0 (Threshold 90)</td></tr>
      </table>
      <h1>Vcc&nbsp;&nbsp;Currently 3</h1>
      <table summary="Test results for Vcc">
        <tr><th></th><th>Low</th><th>High</th></tr>
        <tr><td>Alarm</td><td>0 (Threshold 3)</td><td>0 (Threshold 3)</td></tr>
        <tr><td>Warning</td><td>0 (Threshold 3)</td><td>0 (Threshold 3)</td></tr>
      </table>
      <h1>Tx Bias&nbsp;&nbsp;Currently 6</h1>
      <table summary="Tx Bias table">
        <tr><th></th><th>Low</th><th>High</th></tr>
        <tr><td>Alarm</td><td>0 (Threshold 0)</td><td>0 (Threshold 500)</td></tr>
        <tr><td>Warning</td><td>0 (Threshold 0)</td><td>0 (Threshold 400)</td></tr>
      </table>
      <h1>Tx Power&nbsp;&nbsp;Currently 33</h1>
      <table summary="Tx Power table">
        <tr><th></th><th>Low</th><th>High</th></tr>
        <tr><td>Alarm</td><td>0 (Threshold -10)</td><td>0 (Threshold 59)</td></tr>
        <tr><td>Warning</td><td>0 (Threshold 0)</td><td>0 (Threshold 49)</td></tr>
      </table>
      <h1>Rx Power&nbsp;&nbsp;Currently -186</h1>
      <table summary="Rx Power table">
        <tr><th></th><th>Low</th><th>High</th></tr>
        <tr><td>Alarm</td><td>0 (Threshold -292)</td><td>0 (Threshold -90)</td></tr>
        <tr><td>Warning</td><td>0 (Threshold -279)</td><td>0 (Threshold -100)</td></tr>
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
        self.assertEqual(result["fiber"]["optical_wan_operational_status"], "up")
        self.assertEqual(result["fiber"]["link_state"], "up")
        self.assertEqual(result["fiber"]["fiber_module"], "unavailable")
        self.assertEqual(result["fiber"]["opt_powerlvl"], 2)
        self.assertEqual(result["fiber"]["opt_los"], 0)
        self.assertEqual(result["fiber"]["opt_tx_fault"], 0)
        self.assertEqual(result["fiber"]["opt_tx_disable"], 0)
        self.assertEqual(result["fiber"]["rx_los_state"], 1)
        self.assertEqual(result["fiber"]["tx_fault_state"], 0)
        self.assertEqual(result["fiber"]["tx_disable_state"], 0)
        self.assertEqual(result["fiber"]["rate_select_state"], 0)
        self.assertEqual(result["fiber"]["data_ready_bar_state"], 0)
        self.assertEqual(result["fiber"]["wave_length"], 1270)
        self.assertEqual(result["fiber"]["length_smf_km"], 40)
        self.assertEqual(
            result["fiber"]["sensors"],
            {
                "temperature_c": {
                    "current": 40,
                    "alarm_low": -50,
                    "alarm_high": 95,
                    "warning_low": -45,
                    "warning_high": 90,
                },
                "vcc": {
                    "current": 3,
                    "alarm_low": 3,
                    "alarm_high": 3,
                    "warning_low": 3,
                    "warning_high": 3,
                },
                "tx_bias": {
                    "current": 6,
                    "alarm_low": 0,
                    "alarm_high": 500,
                    "warning_low": 0,
                    "warning_high": 400,
                },
                "tx_power_dbm": {
                    "current": 3.3,
                    "alarm_low": -1,
                    "alarm_high": 5.9,
                    "warning_low": 0,
                    "warning_high": 4.9,
                },
                "rx_power_dbm": {
                    "current": -18.6,
                    "alarm_low": -29.2,
                    "alarm_high": -9,
                    "warning_low": -27.9,
                    "warning_high": -10,
                },
            },
        )
        rendered = str(result)
        self.assertNotIn("SECRET-SERIAL", rendered)
        self.assertNotIn("SECRET-TRANSCEIVER-SERIAL", rendered)
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
