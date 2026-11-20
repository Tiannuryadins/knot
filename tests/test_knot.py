"""Tests for Knot. Every test runs against a throwaway Relate store in a
temp dir — no network, no shared state.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from knot import ask as ask_mod
from knot import remember as rem
from knot.db import KnotDB
from knot.schema import seed


class KnotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = KnotDB(os.path.join(self.tmp.name, "test.rl"))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_seed_counts(self):
        nodes, rels = seed(self.db)
        self.assertEqual(nodes, 4 + 4 + 3 + 4 + 3)  # people+projects+decisions+tasks+topics
        self.assertEqual(rels, 19)
        stats = ask_mod.stats(self.db)
        self.assertEqual(stats["nodes"], 18)
        self.assertEqual(stats["relationships"], 19)

    def test_seed_is_idempotent(self):
        seed(self.db)
        nodes, rels = seed(self.db)
        self.assertEqual((nodes, rels), (0, 0))

    def test_remember_person_and_link(self):
        seed(self.db)
        rem.remember_node(self.db, "Person", {"name": "Rani", "role": "designer"})
        rem.remember_rel(self.db, "Person", "Rani", "WORKS_ON", "Project", "Knot")
        result = ask_mod.ask(self.db, "who works on Knot?")
        self.assertIn("Rani", result["answer"])
        self.assertIn("Januar", result["answer"])
        self.assertTrue(result["paths"])

    def test_ask_blocked_by(self):
        seed(self.db)
        result = ask_mod.ask(self.db, "what is Record Knot demo video blocked by?")
        self.assertIn("Publish Knot repo to GitHub", result["answer"])
        self.assertIn("BLOCKED_BY", result["cypher"])

    def test_ask_decisions_about_topic(self):
        seed(self.db)
        result = ask_mod.ask(self.db, "what did we decide about bounty hunting?")
        self.assertIn("Free-only rule", result["answer"])

    def test_ask_who_knows(self):
        seed(self.db)
        result = ask_mod.ask(self.db, "who knows Mira?")
        self.assertIn("Januar", result["answer"])
        self.assertIn("Ada", result["answer"])

    def test_ask_neighborhood_fallback(self):
        seed(self.db)
        result = ask_mod.ask(self.db, "tell me about TICKR")
        self.assertIn("TICKR", result["answer"])
        self.assertTrue(result["paths"])

    def test_ask_unknown_entity(self):
        seed(self.db)
        result = ask_mod.ask(self.db, "who works on Zebra?")
        self.assertIn("don't have anything", result["answer"])
        self.assertEqual(result["paths"], [])

    def test_remember_note_with_link(self):
        seed(self.db)
        rem.remember_note(self.db, "Relate round-trip verified on Linux",
                          "Project", "Knot")
        rows = self.db.run(
            "MATCH (n:Note)-[r:MENTIONS]->(p:Project {name: $k}) "
            "RETURN n.text AS t", {"k": "Knot"})
        self.assertEqual(len(rows), 1)

    def test_link_missing_node_raises(self):
        seed(self.db)
        with self.assertRaises(ValueError):
            rem.remember_rel(self.db, "Person", "Nobody", "WORKS_ON",
                             "Project", "Knot")

    def test_persistence_across_reopen(self):
        seed(self.db)
        self.db.close()
        db2 = KnotDB(os.path.join(self.tmp.name, "test.rl"))
        try:
            stats = ask_mod.stats(db2)
            self.assertEqual(stats["nodes"], 18)
        finally:
            db2.close()
            self.db = KnotDB(os.path.join(self.tmp.name, "test.rl"))

    def test_export_graph_shape(self):
        seed(self.db)
        g = ask_mod.export_graph(self.db)
        self.assertEqual(len(g["nodes"]), 18)
        self.assertEqual(len(g["edges"]), 19)
        labels = {n["label"] for n in g["nodes"]}
        self.assertEqual(labels, {"Person", "Project", "Decision", "Task", "Topic"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
