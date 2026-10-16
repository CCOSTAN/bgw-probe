from http.client import HTTPConnection
import logging
import threading
import unittest

from bgw_probe.server import ProbeHandler, ProbeServer, StateStore


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
            with self.assertLogs("bgw_probe.server", level="DEBUG") as successful_logs:
                connection.request("GET", "/healthz")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                response.read()
            self.assertEqual(successful_logs.records[0].levelno, logging.DEBUG)
            self.assertEqual(successful_logs.records[0].getMessage(), "http 200")

            with self.assertLogs("bgw_probe.server", level="DEBUG") as error_logs:
                connection.request("GET", "/missing")
                response = connection.getresponse()
                self.assertEqual(response.status, 404)
                response.read()
            self.assertEqual(error_logs.records[0].levelno, logging.WARNING)
            self.assertEqual(error_logs.records[0].getMessage(), "http 404")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_error_messages_are_logged_as_warnings(self) -> None:
        with self.assertLogs("bgw_probe.server", level="WARNING") as logs:
            handler = object.__new__(ProbeHandler)
            handler.log_message("bad %s", "request")
            handler.log_message("bad %d", "request")
        self.assertEqual(logs.records[0].levelno, logging.WARNING)
        self.assertEqual(logs.records[0].getMessage(), "http error: bad request")
        self.assertEqual(logs.records[1].getMessage(), "http error: bad %d request")


if __name__ == "__main__":
    unittest.main()
