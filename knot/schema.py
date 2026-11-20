"""Schema + demo seed data for Knot.

Node labels: Person, Project, Decision, Task, Topic, Note.
Relationships: WORKS_ON, KNOWS, DECIDED, ABOUT, BLOCKED_BY, DEPENDS_ON,
TAGGED, MENTIONS.

The seed is a small demo world (a solo builder's bounty/hackathon work)
so the first run already has something interesting to ask about.
"""

SEED_CYPHER = [
    # People
    "CREATE (p:Person {name: $name, role: $role})",
    # Projects
    "CREATE (p:Project {name: $name, status: $status, prize: $prize})",
    # Decisions
    "CREATE (d:Decision {text: $text, date: $date})",
    # Tasks
    "CREATE (t:Task {title: $title, status: $status})",
    # Topics
    "CREATE (t:Topic {name: $name})",
]

SEED_PEOPLE = [
    {"name": "Januar", "role": "builder"},
    {"name": "Tian", "role": "builder"},
    {"name": "Ada", "role": "reviewer"},
    {"name": "Mira", "role": "teammate"},
]

SEED_PROJECTS = [
    {"name": "Knot", "status": "building", "prize": "Mac Studio"},
    {"name": "TICKR", "status": "submitted", "prize": "$104K"},
    {"name": "TapeScope", "status": "submitted", "prize": "100K USDT"},
    {"name": "FrankenLab", "status": "submitted", "prize": "$5K"},
]

SEED_DECISIONS = [
    {"text": "Free-only rule: never pay for a tool, entry, or deposit",
     "date": "2026-11-16"},
    {"text": "Auto-submit mandate: verified free findings get submitted without asking",
     "date": "2026-11-16"},
    {"text": "Knot stores all context in a Relate graph, not in chat history",
     "date": "2026-11-20"},
]

SEED_TASKS = [
    {"title": "Record Knot demo video", "status": "todo"},
    {"title": "Publish Knot repo to GitHub", "status": "todo"},
    {"title": "Submit Knot on Devpost", "status": "todo"},
    {"title": "Verify Relate round-trip on Linux", "status": "done"},
]

SEED_TOPICS = [
    {"name": "graph database"},
    {"name": "bounty hunting"},
    {"name": "AI agents"},
]

# (from_label, from_key, rel, to_label, to_key)
SEED_RELS = [
    ("Person", "Januar", "WORKS_ON", "Project", "Knot"),
    ("Person", "Januar", "WORKS_ON", "Project", "TICKR"),
    ("Person", "Januar", "WORKS_ON", "Project", "TapeScope"),
    ("Person", "Tian", "WORKS_ON", "Project", "FrankenLab"),
    ("Person", "Mira", "WORKS_ON", "Project", "Knot"),
    ("Person", "Januar", "KNOWS", "Person", "Ada"),
    ("Person", "Januar", "KNOWS", "Person", "Mira"),
    ("Person", "Ada", "KNOWS", "Person", "Mira"),
    ("Person", "Januar", "DECIDED", "Decision",
     "Free-only rule: never pay for a tool, entry, or deposit"),
    ("Person", "Januar", "DECIDED", "Decision",
     "Auto-submit mandate: verified free findings get submitted without asking"),
    ("Person", "Januar", "DECIDED", "Decision",
     "Knot stores all context in a Relate graph, not in chat history"),
    ("Decision", "Free-only rule: never pay for a tool, entry, or deposit",
     "ABOUT", "Topic", "bounty hunting"),
    ("Decision", "Knot stores all context in a Relate graph, not in chat history",
     "ABOUT", "Topic", "graph database"),
    ("Task", "Record Knot demo video", "BLOCKED_BY", "Task", "Publish Knot repo to GitHub"),
    ("Task", "Submit Knot on Devpost", "DEPENDS_ON", "Task", "Record Knot demo video"),
    ("Task", "Publish Knot repo to GitHub", "DEPENDS_ON", "Task", "Verify Relate round-trip on Linux"),
    ("Project", "Knot", "TAGGED", "Topic", "graph database"),
    ("Project", "Knot", "TAGGED", "Topic", "AI agents"),
    ("Project", "TICKR", "TAGGED", "Topic", "bounty hunting"),
]

# Key property used to match a node of a label when creating relationships.
KEY_PROP = {
    "Person": "name",
    "Project": "name",
    "Decision": "text",
    "Task": "title",
    "Topic": "name",
    "Note": "text",
}


def seed(db):
    """Load the demo world. Returns (nodes_created, rels_created)."""
    existing = db.run("MATCH (n) RETURN count(n) AS n")[0]["n"]
    if existing:
        return 0, 0
    nodes = 0
    for person in SEED_PEOPLE:
        db.write("CREATE (p:Person {name: $name, role: $role})", person)
        nodes += 1
    for project in SEED_PROJECTS:
        db.write("CREATE (p:Project {name: $name, status: $status, prize: $prize})",
                 project)
        nodes += 1
    for decision in SEED_DECISIONS:
        db.write("CREATE (d:Decision {text: $text, date: $date})", decision)
        nodes += 1
    for task in SEED_TASKS:
        db.write("CREATE (t:Task {title: $title, status: $status})", task)
        nodes += 1
    for topic in SEED_TOPICS:
        db.write("CREATE (t:Topic {name: $name})", topic)
        nodes += 1
    rels = 0
    for fl, fk, rel, tl, tk in SEED_RELS:
        fk_prop, tk_prop = KEY_PROP[fl], KEY_PROP[tl]
        q = (
            f"MATCH (a:{fl} {{{fk_prop}: $fk}}), (b:{tl} {{{tk_prop}: $tk}}) "
            f"CREATE (a)-[:{rel}]->(b) RETURN 1 AS ok"
        )
        db.write(q, {"fk": fk, "tk": tk})
        rels += 1
    return nodes, rels
