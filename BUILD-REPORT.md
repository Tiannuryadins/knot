# BUILD REPORT — Knot (Relate by Neo4j Hackathon entry)

Built: 20 Nov 2026, ~15:00–16:00 WIB. Location: `~/workspace/relate-hackathon/`.

## What was built

**Knot — your context, connected.** A personal context agent whose memory
is a Relate graph (embedded, Cypher 25). It stores people, projects,
decisions, tasks, topics and notes as graph nodes, answers plain-English
questions by planning and running real parameterized Cypher queries, and
shows the relationship paths used as evidence (including the Cypher it
ran). A single-file web UI visualizes the live graph with a hand-rolled
force layout. No LLM, no API keys, no network calls, no cloud — fully
local and free.

- `knot/db.py` — Relate client wrapper (parameterized Cypher only)
- `knot/schema.py` — schema + demo seed (18 nodes, 19 relationships)
- `knot/remember.py` — write side (nodes, relationships, notes)
- `knot/ask.py` — question → Cypher planner + evidence paths + graph export
- `knot/server.py` — stdlib-only HTTP server + JSON API
- `cli.py` — terminal interface (`seed`, `ask`, `remember`, `link`, `graph`, `stats`, `serve`)
- `web/index.html` — single-file UI, vanilla JS, zero CDN dependencies
- `tests/test_knot.py` — 12 unittest tests (throwaway `.rl` stores)
- `README.md`, `LICENSE` (MIT), `.gitignore`, `requirements.txt` (`relate-db==1.1.0`)

## How to run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python cli.py seed
python cli.py ask "who works on Knot?"
python cli.py serve --port 8765   # open http://127.0.0.1:8765
python -m unittest discover -s tests -v
```

## Verification (all real, on this Linux VM)

- **Relate install**: official `install.sh` → Relate CLI **v1.1.0**, signature/SHA-256 checks passed.
- **Round-trip smoke test**: `CREATE` + `MATCH` against a persisted `smoke.rl` — write and read-back both returned the expected rows.
- **Python client**: `relate-db==1.1.0`, `relate.connect()` + parameterized `CREATE`/`MATCH`, persistence verified across reopen.
- **Tests**: **12/12 pass** (`python -m unittest discover -s tests -v`, 0.28s).
- **CLI end-to-end**: `seed` → 18 nodes / 19 rels; `ask "who works on Knot?"` → "Januar, Mira works on Knot." with `WORKS_ON` paths; `ask "what did we decide about bounty hunting?"` → Free-only rule; `ask "what is Record Knot demo video blocked by?"` → "Publish Knot repo to GitHub."; `remember` + `link` verified live (Rani added, then data reset to canonical seed).
- **Web server end-to-end**: `GET /` → 200 (9,520 bytes); `/api/stats`, `/api/graph`, `/api/ask` all returned correct JSON; `POST /api/remember` → `{"ok": true}` and the graph grew 19→20 nodes.
- **Bug found & fixed during testing**: the decisions intent regex `(decid|...)\b` never matched "decide" (no word boundary after "decid"); fixed to `decid\w*`, re-tested, 12/12 still pass and the decisions answer is now correct.

Final shipped state: `data/knot.rl` re-seeded to the canonical demo world
(18 nodes, 19 relationships). No secrets, keys, or mnemonics anywhere in
the repo.

## What remains (user-only steps)

1. **GitHub publish** — create repo `Tiannuryadins/knot` (or similar) and
   push this directory. Needs the user's GitHub sudo code; NOT done here.
2. **Devpost registration** — register for "Relate by Neo4j Hackathon" on
   Devpost (free, online) and link the repo.
3. **Demo video** — record a ≤3 min walkthrough (CLI ask + web UI graph)
   and upload it; attach to the Devpost submission.
4. **Submit on Devpost** — deadline **11 Dec 2026 18:00 Pacific
   (12 Dec 09:00 WIB)**; winners announced 17 Dec.
5. Optional polish before submitting: richer seed data, more intent
   templates in `ask.py`, a screenshot/GIF in the README.

## Notes / caveats

- Prizes are hardware (Mac Studio / Mac mini for three winners + a
  Community Favorite), not cash.
- The relate CLI binary lives at `~/.local/bin/relate` (outside the repo);
  the repo itself only needs `pip install -r requirements.txt`.
- The `.venv/` and `data/` directories are git-ignored; the repo is
  publish-ready as-is.
