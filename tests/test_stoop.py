"""Major 01 behavior: the store contract and the entry gate.

Run from the repo root:
    python3 -m unittest discover -t . -s tests
"""

import os
import sys
import tempfile
import unittest

# Make `import src...` work whether run via unittest discover or directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import config  # noqa: E402
from src.server import validate_text  # noqa: E402
from src.store import JsonFileStore  # noqa: E402


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "entries.json")

    def test_add_and_list_newest_first(self):
        store = JsonFileStore(self.path)
        a = store.add("first")
        b = store.add("second")
        items = store.list()
        self.assertEqual([e.text for e in items], ["second", "first"])
        self.assertTrue(a.id and b.id and a.id != b.id)
        self.assertGreater(a.ts, 0)

    def test_persists_across_instances(self):
        JsonFileStore(self.path).add("remembered")
        reopened = JsonFileStore(self.path)
        self.assertEqual([e.text for e in reopened.list()], ["remembered"])

    def test_missing_file_is_empty(self):
        self.assertEqual(JsonFileStore(self.path).list(), [])


class ValidateTests(unittest.TestCase):
    def test_rejects_empty_or_blank(self):
        for bad in [None, 123, "", "   ", "\n\t  "]:
            with self.assertRaises(ValueError):
                validate_text(bad)

    def test_rejects_too_long(self):
        with self.assertRaises(ValueError):
            validate_text("x" * (config.ENTRY_MAX_LEN + 1))

    def test_trims_and_accepts(self):
        self.assertEqual(validate_text("  hello block  "), "hello block")
        self.assertEqual(validate_text("x" * config.ENTRY_MAX_LEN), "x" * config.ENTRY_MAX_LEN)


if __name__ == "__main__":
    unittest.main()
