"""Online SQLite backup. Never copy only the .db file while WAL is active."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def backup(source, destination):
    source_path, destination_path = Path(source).resolve(), Path(destination).resolve()
    if not source_path.is_file() or destination_path.exists():
        raise ValueError("Source must exist and destination must be a new file")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)) as origin:
        with closing(sqlite3.connect(destination_path)) as target:
            origin.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a consistent, verified SQLite backup")
    parser.add_argument("--source", default="data/travel.db")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    backup(args.source, args.output)
    print("Backup created and integrity checked.")
