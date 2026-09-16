import unittest

from bgw_probe.server import StateStore


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


if __name__ == "__main__":
    unittest.main()
