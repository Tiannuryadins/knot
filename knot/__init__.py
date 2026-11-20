"""Knot — a personal context agent whose memory is a Relate graph.

The agent stores people, projects, decisions, tasks and notes as nodes in
an embedded Relate database (Cypher 25) and answers questions by running
real Cypher queries, returning the relationship paths it used as evidence.
No LLM, no API keys, no network calls: everything runs locally.
"""

from .db import KnotDB, DEFAULT_DB_PATH

__all__ = ["KnotDB", "DEFAULT_DB_PATH"]
__version__ = "0.1.0"
