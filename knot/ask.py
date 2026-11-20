"""Read side of Knot: turn a plain question into Cypher, run it against
the Relate graph, and answer with the relationship paths used as evidence.

No LLM is involved: the planner matches entity names present in the
question against node keys in the graph, picks an intent template, and
runs a parameterized Cypher query. The answer always names the query
that produced it, so the graph grounding is auditable.
"""

import re

from .schema import KEY_PROP

# (intent, regex, handler) — handlers take (db, entity_label, entity_key)
INTENTS = [
    ("who works on", re.compile(r"who (works on|is working on|builds?|built)\b"),
     "works_on"),
    ("blocked by", re.compile(r"(block(ed|s|ing)?|stuck on|waiting on)\b"),
     "blocked_by"),
    ("decisions", re.compile(r"(decid\w*|rule|mandate)\b"),
     "decisions"),
    ("who knows", re.compile(r"who knows\b"), "knows"),
    ("depends on", re.compile(r"depend(s|ed|ency|encies)?\b"), "depends_on"),
    ("tasks", re.compile(r"\btasks?\b"), "tasks"),
    ("projects", re.compile(r"\bprojects?\b"), "projects"),
]

LABELS = ["Person", "Project", "Decision", "Task", "Topic", "Note"]


def _all_entities(db):
    """All (label, key) pairs in the graph, for entity matching."""
    entities = []
    for label in LABELS:
        key = KEY_PROP[label]
        rows = db.run(f"MATCH (n:{label}) RETURN n.{key} AS k")
        for row in rows:
            if row["k"]:
                entities.append((label, str(row["k"])))
    return entities


def _find_entity(question, db):
    """Longest node key mentioned in the question (case-insensitive)."""
    q = question.lower()
    best = None
    for label, key in _all_entities(db):
        if key.lower() in q:
            if best is None or len(key) > len(best[1]):
                best = (label, key)
    return best


def _path_rows(rows):
    """Normalize query rows into evidence paths."""
    paths = []
    for r in rows:
        paths.append({
            "from": {"label": r.get("from_label"), "key": r.get("from_key")},
            "rel": r.get("rel"),
            "to": {"label": r.get("to_label"), "key": r.get("to_key")},
        })
    return paths


def _neighborhood(db, label, key, limit=10):
    q = (
        f"MATCH (n:{label})-[r]-(m) "
        f"WHERE n.{KEY_PROP[label]} = $key "
        "RETURN labels(n)[0] AS from_label, "
        f"n.{KEY_PROP[label]} AS from_key, type(r) AS rel, "
        "labels(m)[0] AS to_label, "
        "coalesce(m.name, m.title, m.text) AS to_key "
        "LIMIT $limit"
    )
    return _path_rows(db.run(q, {"key": key, "limit": limit}))


def _works_on(db, label, key):
    q = (
        "MATCH (p:Person)-[r:WORKS_ON]->(pr:Project) "
        "WHERE pr.name = $key "
        "RETURN 'Person' AS from_label, p.name AS from_key, "
        "type(r) AS rel, 'Project' AS to_label, pr.name AS to_key"
    )
    rows = db.run(q, {"key": key})
    if not rows:
        return None
    people = ", ".join(r["from_key"] for r in rows)
    return {
        "answer": f"{people} works on {key}.",
        "cypher": q.strip(),
        "paths": _path_rows(rows),
    }


def _blocked_by(db, label, key):
    q = (
        "MATCH (t:Task)-[r:BLOCKED_BY]->(b:Task) "
        "WHERE t.title = $key "
        "RETURN 'Task' AS from_label, t.title AS from_key, "
        "type(r) AS rel, 'Task' AS to_label, b.title AS to_key"
    )
    rows = db.run(q, {"key": key})
    if not rows:
        return None
    blockers = ", ".join(r["to_key"] for r in rows)
    return {
        "answer": f"{key} is blocked by: {blockers}.",
        "cypher": q.strip(),
        "paths": _path_rows(rows),
    }


def _decisions(db, label, key):
    if label == "Topic":
        q = (
            "MATCH (d:Decision)-[r:ABOUT]->(t:Topic) WHERE t.name = $key "
            "RETURN 'Decision' AS from_label, d.text AS from_key, "
            "type(r) AS rel, 'Topic' AS to_label, t.name AS to_key"
        )
    else:
        q = (
            "MATCH (d:Decision) WHERE d.text CONTAINS $key "
            "RETURN 'Decision' AS from_label, d.text AS from_key, "
            "'' AS rel, '' AS to_label, '' AS to_key"
        )
    rows = db.run(q, {"key": key})
    if not rows:
        return None
    items = "; ".join(r["from_key"] for r in rows)
    return {
        "answer": f"Decisions about {key}: {items}.",
        "cypher": q.strip(),
        "paths": _path_rows(rows),
    }


def _knows(db, label, key):
    q = (
        "MATCH (a:Person)-[r:KNOWS]->(b:Person) WHERE b.name = $key "
        "RETURN 'Person' AS from_label, a.name AS from_key, "
        "type(r) AS rel, 'Person' AS to_label, b.name AS to_key"
    )
    rows = db.run(q, {"key": key})
    if not rows:
        return None
    people = ", ".join(r["from_key"] for r in rows)
    return {
        "answer": f"{people} knows {key}.",
        "cypher": q.strip(),
        "paths": _path_rows(rows),
    }


def _depends_on(db, label, key):
    q = (
        "MATCH (t:Task)-[r:DEPENDS_ON]->(d:Task) WHERE t.title = $key "
        "RETURN 'Task' AS from_label, t.title AS from_key, "
        "type(r) AS rel, 'Task' AS to_label, d.title AS to_key"
    )
    rows = db.run(q, {"key": key})
    if not rows:
        return None
    deps = ", ".join(r["to_key"] for r in rows)
    return {
        "answer": f"{key} depends on: {deps}.",
        "cypher": q.strip(),
        "paths": _path_rows(rows),
    }


def _tasks(db, label, key):
    q = ("MATCH (t:Task) RETURN 'Task' AS from_label, t.title AS from_key, "
         "t.status AS rel, '' AS to_label, '' AS to_key LIMIT 20")
    rows = db.run(q)
    items = "; ".join(f"{r['from_key']} ({r['rel']})" for r in rows)
    return {
        "answer": f"Tasks: {items}." if items else "No tasks stored yet.",
        "cypher": q.strip(),
        "paths": _path_rows(rows),
    }


def _projects(db, label, key):
    q = ("MATCH (p:Project) RETURN 'Project' AS from_label, p.name AS from_key, "
         "p.status AS rel, p.prize AS to_label, '' AS to_key LIMIT 20")
    rows = db.run(q)
    items = "; ".join(f"{r['from_key']} [{r['rel']}, prize {r['to_label']}]"
                      for r in rows)
    return {
        "answer": f"Projects: {items}." if items else "No projects stored yet.",
        "cypher": q.strip(),
        "paths": _path_rows(rows),
    }


_HANDLERS = {
    "works_on": _works_on,
    "blocked_by": _blocked_by,
    "decisions": _decisions,
    "knows": _knows,
    "depends_on": _depends_on,
    "tasks": _tasks,
    "projects": _projects,
}


def ask(db, question):
    """Answer a question from the graph. Returns dict with answer, cypher,
    paths (evidence), and the matched entity (if any)."""
    question = question.strip()
    if not question:
        return {"answer": "Ask me something about your people, projects, "
                          "decisions or tasks.", "cypher": "", "paths": [],
                "entity": None}
    entity = _find_entity(question, db)
    q_lower = question.lower()
    for _name, pattern, handler_name in INTENTS:
        if pattern.search(q_lower):
            handler = _HANDLERS[handler_name]
            if handler_name in ("tasks", "projects"):
                result = handler(db, None, None)
            elif entity is None:
                continue
            else:
                result = handler(db, entity[0], entity[1])
            if result is not None:
                result["entity"] = entity
                return result
    if entity is not None:
        label, key = entity
        paths = _neighborhood(db, label, key)
        if paths:
            desc = "; ".join(
                f"{p['from']['key']} -[{p['rel']}]-> {p['to']['key']}"
                for p in paths
            )
            return {
                "answer": f"Here's what the graph knows about {key}: {desc}.",
                "cypher": f"MATCH (n:{label})-[r]-(m) WHERE n.{KEY_PROP[label]} "
                          f"= $key RETURN n, r, m",
                "paths": paths,
                "entity": entity,
            }
    return {
        "answer": "I don't have anything in the graph about that yet. "
                  "Try `remember` to add it first.",
        "cypher": "",
        "paths": [],
        "entity": entity,
    }


def export_graph(db):
    """Whole graph as JSON-able nodes + edges, for the web UI."""
    nodes = []
    seen = {}
    for label in LABELS:
        key = KEY_PROP[label]
        rows = db.run(
            f"MATCH (n:{label}) RETURN n.{key} AS k, properties(n) AS props"
        )
        for row in rows:
            nid = f"{label}:{row['k']}"
            if nid in seen:
                continue
            seen[nid] = len(nodes)
            nodes.append({"id": nid, "label": label,
                          "key": row["k"], "props": row["props"]})
    edges = []
    rows = db.run(
        "MATCH (a)-[r]->(b) RETURN labels(a)[0] AS fl, "
        "coalesce(a.name, a.title, a.text) AS fk, type(r) AS rel, "
        "labels(b)[0] AS tl, coalesce(b.name, b.title, b.text) AS tk"
    )
    for row in rows:
        src = f"{row['fl']}:{row['fk']}"
        dst = f"{row['tl']}:{row['tk']}"
        if src in seen and dst in seen:
            edges.append({"source": seen[src], "target": seen[dst],
                          "rel": row["rel"]})
    return {"nodes": nodes, "edges": edges}


def stats(db):
    nodes = db.run("MATCH (n) RETURN count(n) AS n")[0]["n"]
    rels = db.run("MATCH ()-[r]->() RETURN count(r) AS n")[0]["n"]
    by_label = db.run(
        "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS n")
    return {"nodes": nodes, "relationships": rels,
            "by_label": {r["label"]: r["n"] for r in by_label}}
