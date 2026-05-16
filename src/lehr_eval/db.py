from pathlib import Path
import sqlite3
from typing import Union


PathLike = Union[str, Path]


def connect(db_path: PathLike) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path, timeout=5.0)
    connection.row_factory = sqlite3.Row
    connection.execute("pragma foreign_keys = on")
    return connection
