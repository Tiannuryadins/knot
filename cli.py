#!/usr/bin/env python3
"""Knot CLI — talk to your Relate-backed context graph from the terminal.

Usage:
  python cli.py seed                                  load the demo world
  python cli.py ask "who works on Knot?"              ask a question
  python cli.py remember person --name Ada --role reviewer
  python cli.py remember project --name Knot --status building --prize "Mac Studio"
  python cli.py remember decision --text "..." --date 2026-11-20
  python cli.py remember task --title "..." --status todo
  python cli.py remember topic --name "graph database"
  python cli.py remember note --text "..." [--about-label Project --about Knot]
  python cli.py link Person Januar WORKS_ON Project Knot
  python cli.py graph                                 print graph as JSON
  python cli.py stats                                 node/relationship counts
  python cli.py serve [--port 8765]                   web UI + JSON API
"""

import argparse
import json
import sys

from knot.db import KnotDB
from knot import ask as ask_mod
from knot import remember as rem
from knot import schema


def _db(args):
    return KnotDB(args.db)


def cmd_seed(args):
    with _db(args) as db:
        nodes, rels = schema.seed(db)
        if nodes == 0:
            print("Graph already has data — seed skipped (nothing overwritten).")
        else:
            print(f"Seeded {nodes} nodes and {rels} relationships.")


def cmd_ask(args):
    with _db(args) as db:
        result = ask_mod.ask(db, args.question)
        print(result["answer"])
        if result["cypher"]:
            print(f"\nCypher: {result['cypher']}")
        for p in result["paths"]:
            print(f"  {p['from']['key']} -[{p['rel']}]-> {p['to']['key']}")


def cmd_remember(args):
    props = {k: v for k, v in vars(args).items()
             if k in ("name", "role", "status", "prize", "text", "date", "title")
             and v is not None}
    with _db(args) as db:
        if args.kind == "note":
            out = rem.remember_note(db, props["text"],
                                    args.about_label, args.about)
            print(f"Noted: {out['text']}")
            return
        rem.remember_node(db, args.kind.capitalize(), props)
        print(f"Remembered {args.kind}: {props}")


def cmd_link(args):
    with _db(args) as db:
        rem.remember_rel(db, args.from_label, args.from_key, args.rel,
                         args.to_label, args.to_key)
        print(f"Linked {args.from_label}({args.from_key}) "
              f"-[:{args.rel}]-> {args.to_label}({args.to_key})")


def cmd_graph(args):
    with _db(args) as db:
        print(json.dumps(ask_mod.export_graph(db), indent=2))


def cmd_stats(args):
    with _db(args) as db:
        print(json.dumps(ask_mod.stats(db), indent=2))


def cmd_serve(args):
    from knot.server import serve
    serve(args.db, args.port)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="knot",
                                     description="Personal context agent on Relate")
    parser.add_argument("--db", default=None,
                        help="path to the .rl store (default data/knot.rl)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("seed", help="load the demo world")
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser("ask", help="ask the graph a question")
    p.add_argument("question")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("remember", help="store a node")
    p.add_argument("kind", choices=["person", "project", "decision",
                                    "task", "topic", "note"])
    p.add_argument("--name")
    p.add_argument("--role")
    p.add_argument("--status")
    p.add_argument("--prize")
    p.add_argument("--text")
    p.add_argument("--date")
    p.add_argument("--title")
    p.add_argument("--about-label")
    p.add_argument("--about")
    p.set_defaults(func=cmd_remember)

    p = sub.add_parser("link", help="create a relationship")
    p.add_argument("from_label")
    p.add_argument("from_key")
    p.add_argument("rel")
    p.add_argument("to_label")
    p.add_argument("to_key")
    p.set_defaults(func=cmd_link)

    p = sub.add_parser("graph", help="dump the whole graph as JSON")
    p.set_defaults(func=cmd_graph)

    p = sub.add_parser("stats", help="node/relationship counts")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("serve", help="start the web UI")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(func=cmd_serve)

    args = parser.parse_args(argv)
    if args.db is None:
        from knot.db import DEFAULT_DB_PATH
        args.db = DEFAULT_DB_PATH
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
