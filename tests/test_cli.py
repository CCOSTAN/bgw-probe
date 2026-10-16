import logging
import os
import unittest
from unittest.mock import patch

from bgw_probe.cli import _configure_logging


class LoggingConfigurationTests(unittest.TestCase):
    def test_log_level_environment_variable_and_fallback(self) -> None:
        cases = [
            ("DEBUG", logging.DEBUG),
            ("warning", logging.WARNING),
            ("not-a-level", logging.INFO),
        ]
        for value, expected_level in cases:
            with self.subTest(value=value), patch.dict(
                os.environ, {"BGW_LOG_LEVEL": value}
            ), patch("bgw_probe.cli.logging.basicConfig") as basic_config:
                _configure_logging()
                self.assertEqual(
                    basic_config.call_args.kwargs["level"], expected_level
                )

    def test_log_level_defaults_to_info(self) -> None:
        with patch.dict(os.environ):
            os.environ.pop("BGW_LOG_LEVEL", None)
            with patch("bgw_probe.cli.logging.basicConfig") as basic_config:
                _configure_logging()
        self.assertEqual(basic_config.call_args.kwargs["level"], logging.INFO)


if __name__ == "__main__":
    unittest.main()
