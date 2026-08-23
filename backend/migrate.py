"""Migration CLI wrapper.

Usage (from backend/):
    python migrate.py status          # show current revision / pending
    python migrate.py up              # upgrade to head
    python migrate.py down            # downgrade one revision
    python migrate.py down --all      # downgrade to base
    python migrate.py revision -m ""  # create a new empty revision

Thin wrapper over Alembic so the common commands are explicit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_ROOT = Path(__file__).resolve().parent


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser(prog="migrate")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("up", help="Upgrade database to the latest revision")
    sub.add_parser("status", help="Show current revision and pending updates")

    down = sub.add_parser("down", help="Downgrade one revision (or --all to base)")
    down.add_argument("--all", action="store_true", help="Downgrade all the way to base")

    rev = sub.add_parser("revision", help="Create a new migration revision")
    rev.add_argument("-m", "--message", default="", help="Revision message")
    rev.add_argument(
        "--autogenerate",
        action="store_true",
        help="Autogenerate from current ORM models",
    )

    args = parser.parse_args()
    cfg = _alembic_config()

    if args.cmd == "up":
        command.upgrade(cfg, "head")
    elif args.cmd == "down":
        command.downgrade(cfg, "base" if args.all else "-1")
    elif args.cmd == "status":
        command.current(cfg, verbose=True)
    elif args.cmd == "revision":
        command.revision(cfg, message=args.message, autogenerate=args.autogenerate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
