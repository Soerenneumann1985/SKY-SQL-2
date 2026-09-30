"""Entry point: ``sky-sql web`` starts the web app, ``sky-sql cli`` the interactive menu."""

from __future__ import annotations

import argparse
import logging

from sky_sql import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sky-sql", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    web = sub.add_parser("web", help="start the web app (default)")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=5000)
    web.add_argument("--debug", action="store_true", help="enable Flask debug mode")

    sub.add_parser("cli", help="start the interactive command-line menu")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.command == "cli":
        from sky_sql.cli import main as cli_main

        return cli_main()

    from sky_sql.web import run

    run(
        host=getattr(args, "host", "127.0.0.1"),
        port=getattr(args, "port", 5000),
        debug=getattr(args, "debug", False),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
