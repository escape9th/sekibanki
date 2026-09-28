from __future__ import annotations

import argparse

from .server import serve


def main() -> None:
    parser = argparse.ArgumentParser(prog="sekibanki", description="Inspect local AI agent traces.")
    subparsers = parser.add_subparsers(dest="command")
    serve_parser = subparsers.add_parser("serve", help="start the local trace viewer")
    serve_parser.add_argument("--directory", default=".sekibanki")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.command == "serve":
        serve(args.directory, args.host, args.port)
    else:
        parser.print_help()
