"""Stoop behavior tests (majors 01-02): the store contract, the entry gate, the
server guards, and the forgetting engine.

Run from the repo root:
    python3 -m unittest discover -t . -s tests
"""

import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

# Make `import src...` work whether run via unittest discover or directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import config, murmur, themes  # noqa: E402
from src.archive import JsonlArchive  # noqa: E402
from src.box import Box  # noqa: E402
from src.decay import DecayWeights, keep_score, pick_eviction  # noqa: E402
from src.ratelimit import RateLimiter  # noqa: E402
from src.server import Handler, validate_text  # noqa: E402
from src.settings import Settings  # noqa: E402
from src.store import Entry, JsonFileStore  # noqa: E402


# --- helpers ---

def _weights(horizon=100.0, squeeze=0.0, w_recency=1.0, w_seconds=1.0):
    return DecayWeights(
        age_horizon_seconds=horizon,
        pressure_squeeze=squeeze,
        w_recency=w_recency,
        w_seconds=w_seconds,
    )


class FakeClock:
    """A clock we advance by hand, so aging is deterministic without sleeping."""

    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t


def _temp_store():
    return JsonFileStore(os.path.join(tempfile.mkdtemp(), "entries.json"))


# --- store ---

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

    def test_remove_and_update(self):
        store = JsonFileStore(self.path)
        e = store.add("x")
        store.update(Entry(id=e.id, text=e.text, ts=e.ts, seconds=2))
        self.assertEqual(store.get(e.id).seconds, 2)
        self.assertEqual(store.remove(e.id).id, e.id)
        self.assertIsNone(store.get(e.id))
        self.assertEqual(store.count(), 0)


# --- the entry gate ---

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


# --- the forgetting policy (pure) ---

class DecayTests(unittest.TestCase):
    def _e(self, eid, ts, seconds=0):
        return Entry(id=eid, text=eid, ts=ts, seconds=seconds)

    def test_newer_scores_higher(self):
        w = _weights()
        older, newer = self._e("a", ts=0), self._e("b", ts=50)
        self.assertGreater(keep_score(newer, 50, 0.0, w), keep_score(older, 50, 0.0, w))

    def test_seconds_raise_score(self):
        w = _weights()
        plain, loved = self._e("a", ts=0), self._e("b", ts=0, seconds=3)
        self.assertGreater(keep_score(loved, 0, 0.0, w), keep_score(plain, 0, 0.0, w))

    def test_pressure_erodes_age_faster(self):
        w = _weights(squeeze=0.6)
        e = self._e("a", ts=0)
        empty_box = keep_score(e, 40, 0.0, w)
        full_box = keep_score(e, 40, 1.0, w)
        self.assertGreater(empty_box, full_box)

    def test_pick_eviction_is_lowest_then_oldest(self):
        w = _weights()
        entries = [self._e("old", ts=0), self._e("mid", ts=50), self._e("new", ts=90)]
        self.assertEqual(pick_eviction(entries, 90, 0.0, w).id, "old")


# --- the box: forgetting in motion ---

class BoxTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock(0.0)
        self.archive_path = os.path.join(tempfile.mkdtemp(), "evicted.jsonl")
        self.archive = JsonlArchive(self.archive_path)

    def _box(self, capacity, w=None):
        return Box(
            _temp_store(),
            capacity=capacity,
            weights=w or _weights(),
            archive=self.archive,
            clock=self.clock,
        )

    def test_capacity_is_never_exceeded(self):
        box = self._box(capacity=3)
        for i in range(10):
            self.clock.t = i
            box.leave(f"entry {i}")
        self.assertEqual(len(box.read()), 3)

    def test_oldest_unloved_is_composted(self):
        box = self._box(capacity=3)
        for i, name in enumerate(["a", "b", "c"]):
            self.clock.t = i * 10
            box.leave(name)
        self.clock.t = 30
        box.leave("d")
        texts = [e.text for e in box.read()]
        self.assertEqual(len(texts), 3)
        self.assertNotIn("a", texts)  # oldest, unloved -> composted

    def test_seconding_saves_the_oldest(self):
        box = self._box(capacity=3)
        first = None
        for i, name in enumerate(["a", "b", "c"]):
            self.clock.t = i * 10
            e = box.leave(name)
            if name == "a":
                first = e
        box.second(first.id)
        box.second(first.id)  # two "keeps" buy it past the fresher, unloved ones
        self.clock.t = 30
        box.leave("d")
        texts = [e.text for e in box.read()]
        self.assertIn("a", texts)     # saved
        self.assertNotIn("b", texts)  # next-least-kept composted instead

    def test_evicted_entry_is_archived_not_destroyed(self):
        box = self._box(capacity=1)
        self.clock.t = 0
        box.leave("ghost")
        self.clock.t = 1
        box.leave("living")
        with open(self.archive_path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        self.assertEqual([r["text"] for r in rows], ["ghost"])
        self.assertEqual(rows[0]["reason"], "composted")


# --- the murmur (pure) ---

class MurmurTests(unittest.TestCase):
    def _e(self, eid, text, ts, seconds=0):
        return Entry(id=eid, text=text, ts=ts, seconds=seconds)

    def test_empty_is_quiet(self):
        d = murmur.derive([], now=100)
        self.assertEqual(d["count"], 0)
        self.assertEqual(d["threads"], [])
        self.assertIsNone(d["holding"])
        self.assertIsNone(d["oldest_age"])

    def test_threads_are_recurring_words_only(self):
        entries = [
            self._e("a", "the river is high today", ts=0),
            self._e("b", "river rocks by the water", ts=10),
            self._e("c", "a quiet morning", ts=20),
        ]
        d = murmur.derive(entries, now=20)
        words = [t[0] for t in d["threads"]]
        self.assertIn("river", words)       # said across two entries
        self.assertNotIn("the", words)      # stopword
        self.assertNotIn("morning", words)  # only one entry — not recurring
        self.assertEqual(dict(d["threads"])["river"], 2)  # document frequency

    def test_holding_is_the_most_kept(self):
        entries = [
            self._e("a", "plain", ts=0, seconds=0),
            self._e("b", "beloved", ts=10, seconds=3),
        ]
        d = murmur.derive(entries, now=10)
        self.assertEqual(d["holding"]["text"], "beloved")
        self.assertEqual(d["holding"]["seconds"], 3)

    def test_no_holding_when_nothing_is_kept(self):
        d = murmur.derive([self._e("a", "x", ts=0)], now=0)
        self.assertIsNone(d["holding"])

    def test_ages_span_oldest_to_newest(self):
        entries = [self._e("a", "old", ts=0), self._e("b", "new", ts=30)]
        d = murmur.derive(entries, now=50)
        self.assertEqual(d["oldest_age"], 50)
        self.assertEqual(d["newest_age"], 20)


# --- the rate limiter (pure) ---

class RateLimitTests(unittest.TestCase):
    def test_allows_then_blocks_within_window(self):
        rl = RateLimiter(2, 10, clock=FakeClock(0.0))
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))

    def test_window_resets(self):
        clock = FakeClock(0.0)
        rl = RateLimiter(1, 10, clock=clock)
        self.assertTrue(rl.allow("a"))
        self.assertFalse(rl.allow("a"))
        clock.t = 11
        self.assertTrue(rl.allow("a"))

    def test_keys_are_independent(self):
        rl = RateLimiter(1, 10, clock=FakeClock(0.0))
        self.assertTrue(rl.allow("a"))
        self.assertTrue(rl.allow("b"))
        self.assertFalse(rl.allow("a"))

    def test_disabled_when_max_nonpositive(self):
        rl = RateLimiter(0, 10, clock=FakeClock(0.0))
        self.assertTrue(all(rl.allow("a") for _ in range(50)))


# --- theming + keeper settings ---

class ThemeTests(unittest.TestCase):
    def test_resolve_returns_bundle_with_skin(self):
        b = themes.resolve("stoop", "phosphor")
        self.assertEqual(b["skin"], "phosphor")
        self.assertIn("prompt", b)
        self.assertIn("noun_plural", b)

    def test_prompt_override(self):
        self.assertEqual(themes.resolve("stoop", "paper", "Custom?")["prompt"], "Custom?")

    def test_unknown_theme_falls_back(self):
        self.assertEqual(
            themes.resolve("nope", "paper")["title"],
            themes.THEMES[themes.DEFAULT_THEME]["title"],
        )

    def test_unknown_skin_falls_back(self):
        self.assertEqual(themes.resolve("stoop", "nope")["skin"], themes.DEFAULT_SKIN)


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "settings.json")

    def test_defaults(self):
        d = Settings(self.path).get()
        self.assertEqual(d["theme"], config.DEFAULT_THEME)
        self.assertEqual(d["skin"], config.DEFAULT_SKIN)
        self.assertIsNone(d["prompt"])

    def test_update_persists_across_instances(self):
        Settings(self.path).update({"theme": "rocks", "skin": "phosphor", "prompt": "Rocks?"})
        reopened = Settings(self.path).get()
        self.assertEqual(reopened["theme"], "rocks")
        self.assertEqual(reopened["skin"], "phosphor")
        self.assertEqual(reopened["prompt"], "Rocks?")

    def test_unknown_theme_or_skin_raises(self):
        s = Settings(self.path)
        with self.assertRaises(ValueError):
            s.update({"theme": "nope"})
        with self.assertRaises(ValueError):
            s.update({"skin": "nope"})

    def test_prompt_clear_and_length(self):
        s = Settings(self.path)
        s.update({"prompt": "hi"})
        self.assertEqual(s.get()["prompt"], "hi")
        s.update({"prompt": "   "})  # blank clears
        self.assertIsNone(s.get()["prompt"])
        with self.assertRaises(ValueError):
            s.update({"prompt": "x" * (config.ENTRY_MAX_LEN + 1)})

    def test_resolved_applies_theme(self):
        s = Settings(self.path)
        s.update({"theme": "tips"})
        self.assertEqual(s.resolved()["noun_plural"], "tips")


# --- handler robustness ---

class HandlerLogTests(unittest.TestCase):
    def test_log_message_survives_a_connection_with_no_request(self):
        # A socket that times out before sending a request line has no command/
        # path set; log_message (called via log_error) must not crash.
        handler = Handler.__new__(Handler)  # allocate without parsing a request
        handler.log_message("Request timed out: %r", "boom")  # should be a no-op


# --- the server, end to end ---

class ServerTests(unittest.TestCase):
    """The box runs on the street: oversized POSTs are refused before allocation,
    seconding behaves, and the keeper gate fails closed."""

    def setUp(self):
        Handler.box = Box(_temp_store(), capacity=50, weights=_weights())
        Handler.settings = Settings(os.path.join(tempfile.mkdtemp(), "settings.json"))
        Handler.limiter = RateLimiter(1000, 60)  # effectively off for most tests
        os.environ["STOOP_KEEPER_KEY"] = "test-key"
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        os.environ.pop("STOOP_KEEPER_KEY", None)

    def _post(self, path, body):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", path, body=body, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        status, payload = resp.status, resp.read()
        conn.close()
        return status, payload

    def _get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        status, payload = resp.status, resp.read()
        conn.close()
        return status, payload

    def _post_keyed(self, path, body, key):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST", path, body=body,
            headers={"Content-Type": "application/json", "X-Keeper-Key": key},
        )
        resp = conn.getresponse()
        status, payload = resp.status, resp.read()
        conn.close()
        return status, payload

    def test_normal_post_accepted(self):
        status, _ = self._post("/entries", json.dumps({"text": "hello block"}))
        self.assertEqual(status, 201)

    def test_oversized_body_rejected_with_413(self):
        huge = json.dumps({"text": "x" * (config.MAX_BODY_BYTES + 1000)})
        status, _ = self._post("/entries", huge)
        self.assertEqual(status, 413)

    def test_second_unknown_id_404(self):
        status, _ = self._post("/second", json.dumps({"id": "nope"}))
        self.assertEqual(status, 404)

    def test_second_existing_entry_increments(self):
        status, payload = self._post("/entries", json.dumps({"text": "keepable"}))
        self.assertEqual(status, 201)
        eid = json.loads(payload)["id"]
        status, payload = self._post("/second", json.dumps({"id": eid}))
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload)["seconds"], 1)

    def test_murmur_route(self):
        self._post("/entries", json.dumps({"text": "river rocks and rain"}))
        status, payload = self._get("/murmur")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload)["count"], 1)

    def test_config_route_default_theme(self):
        status, payload = self._get("/config")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload)["title"], "the stoop")

    def test_admin_requires_key(self):
        _, payload = self._post("/entries", json.dumps({"text": "spam"}))
        eid = json.loads(payload)["id"]
        status, _ = self._post("/admin/remove", json.dumps({"id": eid}))  # no key
        self.assertEqual(status, 403)

    def test_admin_wrong_key_is_rejected(self):
        _, payload = self._post("/entries", json.dumps({"text": "spam"}))
        eid = json.loads(payload)["id"]
        status, _ = self._post_keyed("/admin/remove", json.dumps({"id": eid}), "wrong")
        self.assertEqual(status, 403)

    def test_admin_remove_with_key(self):
        _, payload = self._post("/entries", json.dumps({"text": "spam"}))
        eid = json.loads(payload)["id"]
        status, _ = self._post_keyed("/admin/remove", json.dumps({"id": eid}), "test-key")
        self.assertEqual(status, 200)
        _, listing = self._get("/entries")
        self.assertEqual(json.loads(listing)["entries"], [])

    def test_admin_settings_changes_the_box(self):
        status, _ = self._post_keyed("/admin/settings", json.dumps({"theme": "rocks"}), "test-key")
        self.assertEqual(status, 200)
        _, cfg = self._get("/config")
        self.assertEqual(json.loads(cfg)["title"], "show us your rock")

    def test_rapid_posts_are_throttled(self):
        Handler.limiter = RateLimiter(2, 60)  # tiny, just for this test
        body = json.dumps({"text": "hi"})
        self.assertEqual(self._post("/entries", body)[0], 201)
        self.assertEqual(self._post("/entries", body)[0], 201)
        self.assertEqual(self._post("/entries", body)[0], 429)  # the flood is turned away

    def test_keeper_actions_bypass_throttle(self):
        Handler.limiter = RateLimiter(1, 60)  # one public post allowed
        _, payload = self._post("/entries", json.dumps({"text": "keep me"}))
        eid = json.loads(payload)["id"]
        # public quota is now spent, but the keeper is exempt:
        status, _ = self._post_keyed("/admin/remove", json.dumps({"id": eid}), "test-key")
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
