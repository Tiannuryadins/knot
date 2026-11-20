"""Thin wrapper around the relate-db Python client.

All Cypher goes through here so the rest of the app never touches the
driver directly. Values are always passed as parameters, never pasted
into the statement text.
"""

import os

import relate

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knot.rl")
DEFAULT_DB_PATH = os.path.normpath(DEFAULT_DB_PATH)


class KnotDB:
    def __init__(self, path=DEFAULT_DB_PATH):
        self.path = os.path.abspath(path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._conn = relate.connect(self.path)

    def run(self, cypher, params=None):
        """Execute a Cypher statement; return a list of dict rows."""
        cur = self._conn.cursor()
        cur.execute(cypher, params or {})
        try:
            rows = cur.fetchall()
        except Exception:
            rows = []
        return rows

    def write(self, cypher, params=None):
        rows = self.run(cypher, params)
        self._conn.commit()
        return rows

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
