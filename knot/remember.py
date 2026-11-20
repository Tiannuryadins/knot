"""Write side of Knot: remember people, projects, decisions, tasks, notes
and the relationships between them. Every write is a parameterized
Cypher statement executed against the Relate store.
"""

from .schema import KEY_PROP

LABEL_PROPS = {
    "Person": ("name", "role"),
    "Project": ("name", "status", "prize"),
    "Decision": ("text", "date"),
    "Task": ("title", "status"),
    "Topic": ("name",),
    "Note": ("text",),
}


def remember_node(db, label, props):
    """Create a node. `props` must include the label's key property."""
    key = KEY_PROP[label]
    if key not in props or not props[key]:
        raise ValueError(f"{label} needs a {key!r}")
    assignments = ", ".join(f"{k}: ${k}" for k in props)
    rows = db.write(f"CREATE (n:{label} {{{assignments}}}) RETURN n", props)
    return rows


def remember_rel(db, from_label, from_key, rel, to_label, to_key):
    """Create a relationship between two existing nodes, matched by key."""
    fk_prop, tk_prop = KEY_PROP[from_label], KEY_PROP[to_label]
    q = (
        f"MATCH (a:{from_label} {{{fk_prop}: $fk}}), "
        f"(b:{to_label} {{{tk_prop}: $tk}}) "
        f"CREATE (a)-[:{rel}]->(b) RETURN a, b"
    )
    rows = db.write(q, {"fk": from_key, "tk": to_key})
    if not rows:
        raise ValueError(
            f"could not link {from_label}({from_key!r}) -[:{rel}]-> "
            f"{to_label}({to_key!r}): one side does not exist yet"
        )
    return rows


def remember_note(db, text, about_label=None, about_key=None):
    """Store a free-text note, optionally linked to an existing node."""
    db.write("CREATE (n:Note {text: $text})", {"text": text})
    if about_label and about_key:
        prop = KEY_PROP[about_label]
        db.write(
            f"MATCH (n:Note {{text: $text}}), (t:{about_label} {{{prop}: $key}}) "
            "CREATE (n)-[:MENTIONS]->(t) RETURN 1 AS ok",
            {"text": text, "key": about_key},
        )
    return {"text": text}
