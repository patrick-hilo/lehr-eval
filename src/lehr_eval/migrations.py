from pathlib import Path
from importlib import resources

from lehr_eval.db import connect


def initialize_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    schema = resources.files("lehr_eval").joinpath("schema.sql").read_text(
        encoding="utf-8"
    )

    with connect(path) as db:
        db.execute("pragma journal_mode = wal")
        db.executescript(schema)
        apply_migrations(db)


def apply_migrations(db) -> None:
    columns = {row["name"] for row in db.execute("pragma table_info(admin_log)")}
    if "target_evaluation_id" not in columns:
        db.execute("alter table admin_log add column target_evaluation_id integer")

    teacher_pin_columns = {
        row["name"] for row in db.execute("pragma table_info(teacher_pins)")
    }
    if "pin_code" not in teacher_pin_columns:
        db.execute("alter table teacher_pins add column pin_code text")

    evaluation_columns = {
        row["name"] for row in db.execute("pragma table_info(evaluations)")
    }
    if "base_url" not in evaluation_columns:
        db.execute("alter table evaluations add column base_url text not null default ''")
    if "current_item_index" not in evaluation_columns:
        db.execute("alter table evaluations add column current_item_index integer")
    if "previous_status" not in evaluation_columns:
        db.execute("alter table evaluations add column previous_status text")
