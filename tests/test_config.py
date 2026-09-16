import unittest

from bgw_probe.config import normalize_gateway_url


class ConfigTests(unittest.TestCase):
    def test_normalize_gateway_url(self) -> None:
        self.assertEqual(
            normalize_gateway_url("https://192.168.1.254/"),
            "https://192.168.1.254",
        )

    def test_rejects_unsafe_or_non_root_urls(self) -> None:
        values = [
            "ftp://192.168.1.254",
            "https://user:password@192.168.1.254",
            "https://192.168.1.254/cgi-bin/sysinfo.ha",
            "https://192.168.1.254?mode=diagnostic",
        ]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_gateway_url(value)


if __name__ == "__main__":
    unittest.main()
