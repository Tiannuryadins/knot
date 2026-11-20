# Knot — your context, connected

**Relate by Neo4j Hackathon (NODES 2026) entry.**
Theme: *Context, Connected*.

Knot is a personal context agent whose **memory is a graph**. People,
projects, decisions, tasks and notes live as nodes in
[Relate](https://relatedb.ai) — Neo4j's open-source embedded graph database
for AI agents — and every answer the agent gives is grounded in real Cypher
queries, with the relationship paths it used shown as evidence.

No LLM, no API keys, no network calls, no cloud. Everything runs locally
on your machine; the graph persists in a single `knot.rl` file.

## What it does

- **Remember** — store people, projects, decisions, tasks, topics and
  notes, and link them (`WORKS_ON`, `KNOWS`, `DECIDED`, `ABOUT`,
  `BLOCKED_BY`, `DEPENDS_ON`, `TAGGED`, `MENTIONS`).
- **Ask** — ask in plain English, e.g. *"who works on Knot?"*,
  *"what is Record Knot demo video blocked by?"*,
  *"what did we decide about bounty hunting?"*.
  Knot matches entities in your question, plans a parameterized Cypher
  query, runs it against Relate, and answers with the exact paths as
  evidence — including the Cypher it ran, so the grounding is auditable.
- **See** — a web UI with a live force-directed graph of your whole
  context, plus an ask box and a remember form.

## How Relate is used

- **Embedded store**: one `data/knot.rl` file, opened with the official
  `relate-db` Python client (`relate.connect(...)`, DB-API 2.0 style).
- **Real Cypher 25**: all reads and writes are parameterized Cypher
  statements — `CREATE`, `MATCH`, `RETURN`, relationship traversal —
  executed through `knot/db.py`. Nothing is mocked; delete `data/knot.rl`
  and the graph is gone, re-seed and it is back.
- **Verified on Linux**: the build was developed and tested against
  Relate v1.1.0 (CLI + Python client) on Linux x86_64.

## Quickstart

```bash
# 1. Python 3.10+ and the Relate client
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Load the demo world (18 nodes, 19 relationships)
python cli.py seed

# 3. Ask the graph
python cli.py ask "who works on Knot?"
python cli.py ask "what did we decide about bounty hunting?"
python cli.py ask "what is Record Knot demo video blocked by?"

# 4. Remember something new
python cli.py remember person --name Rani --role designer
python cli.py link Person Rani WORKS_ON Project Knot

# 5. Web UI (seeds automatically on first run)
python cli.py serve --port 8765
# open http://127.0.0.1:8765
```

## CLI reference

| Command | What it does |
|---|---|
| `seed` | Load the demo world (skips if the graph already has data) |
| `ask "<question>"` | Answer from the graph, print answer + Cypher + paths |
| `remember <kind> ...` | Store a `person`, `project`, `decision`, `task`, `topic` or `note` |
| `link <FromLabel> <from-key> <REL> <ToLabel> <to-key>` | Create a relationship |
| `graph` | Dump the whole graph as JSON |
| `stats` | Node / relationship counts |
| `serve [--port 8765]` | Web UI + JSON API on localhost |

## Web API

- `GET /api/graph` — `{nodes, edges}` for the visualizer
- `GET /api/stats` — counts by label
- `GET /api/ask?q=...` — `{answer, cypher, paths, entity}`
- `POST /api/remember` — JSON `{kind, props}` / note with `about`

## Tests

```bash
python -m unittest discover -s tests -v
```

12 tests, all against throwaway Relate stores in temp dirs.

## Project layout

```
knot/            agent package (db.py, schema.py, remember.py, ask.py, server.py)
cli.py           terminal interface
web/index.html   single-file UI (vanilla JS, no CDN, hand-rolled force layout)
tests/           unittest suite
data/            the .rl store (created on first run, git-ignored)
```

## Hackathon

- **Event**: Relate by Neo4j Hackathon (NODES 2026), Devpost
- **Submissions close**: 11 Dec 2026 18:00 Pacific (12 Dec 09:00 WIB)
- **License**: MIT
