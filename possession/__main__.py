import argparse
import os

from possession.db import init_db


def main():
    parser = argparse.ArgumentParser(
        description="possession-terminal: home inventory manager"
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to SQLite database file",
    )
    args = parser.parse_args()

    # Resolve path: --db flag > POSSESSION_DB env var > default
    db_override = args.db or os.environ.get("POSSESSION_DB")

    resolved_path = init_db(db_override)
    print(f"Database ready: {resolved_path}")


if __name__ == "__main__":
    main()
