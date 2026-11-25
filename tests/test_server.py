from http.client import HTTPConnection
import logging
import threading
import unittest

from bgw_probe.server import ProbeServer, StateStore


class StateStoreTests(unittest.TestCase):
    def test_state_store_adds_age_without_mutating_snapshot(self) -> None:
        store = StateStore()
        source = {"status": "ok", "schema_version": 1}
        store.put(source)
        returned = store.get()
        self.assertIsNotNone(returned)
        assert returned is not None
        self.assertEqual(returned["status"], "ok")
        self.assertGreaterEqual(returned["age_seconds"], 0)
        self.assertNotIn("age_seconds", source)


class RequestLoggingTests(unittest.TestCase):
    def test_access_log_levels_follow_response_status(self) -> None:
        server = ProbeServer(("127.0.0.1", 0), StateStore(), 60)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            connection = HTTPConnection(*server.server_address)
            for method, path, status, level in (
                ("GET", "/healthz", 200, logging.DEBUG),
                ("GET", "/missing", 404, logging.WARNING),
                ("POST", "/private-path", 501, logging.WARNING),
            ):
                with self.subTest(method=method, status=status):
                    with self.assertLogs("bgw_probe.server", level="DEBUG") as logs:
                        connection.request(method, path)
                        response = connection.getresponse()
                        self.assertEqual(response.status, status)
                        response.read()
                    self.assertEqual(
                        [(entry.levelno, entry.getMessage()) for entry in logs.records],
                        [(level, f"http {status}")],
                    )
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
