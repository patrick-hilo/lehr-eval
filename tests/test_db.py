from pathlib import Path
import sqlite3

import pytest

from lehr_eval.db import connect
from lehr_eval.migrations import initialize_database


def test_initialize_database_creates_core_tables(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        tables = {
            row["name"]
            for row in db.execute(
                "select name from sqlite_master where type = 'table'"
            )
        }

    assert {
        "teachers",
        "teacher_pins",
        "evaluations",
        "participants",
        "live_answers",
        "item_aggregates",
        "admin_log",
    }.issubset(tables)


def test_database_uses_wal_mode(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        mode = db.execute("pragma journal_mode").fetchone()[0]

    assert mode.lower() == "wal"


def test_live_answers_use_domain_answer_value_scale(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        insert_teacher(db)
        insert_evaluation(db)
        insert_participant(db)

        db.execute(
            """
            insert into live_answers (
                evaluation_id,
                participant_id,
                item_key,
                answer_value
            ) values (1, 1, 'item-1', 0)
            """
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                insert into live_answers (
                    evaluation_id,
                    participant_id,
                    item_key,
                    answer_value
                ) values (1, 1, 'item-2', 4)
                """
            )


def test_live_answer_participant_must_match_evaluation(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        insert_teacher(db)
        insert_evaluation(db, evaluation_id=1, student_token="STUDENT1")
        insert_evaluation(
            db,
            evaluation_id=2,
            class_group="8b",
            student_token="STUDENT2",
            teacher_token="TEACHER2",
        )
        insert_participant(db, participant_id=1, evaluation_id=1)

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                insert into live_answers (
                    evaluation_id,
                    participant_id,
                    item_key,
                    answer_value
                ) values (2, 1, 'item-1', 0)
                """
            )


def test_item_aggregates_store_export_ready_counts(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        columns = {
            row["name"]
            for row in db.execute("pragma table_info(item_aggregates)")
        }

    assert {
        "count_0",
        "count_1",
        "count_2",
        "count_3",
        "missing_count",
        "joined_count",
        "mean",
    }.issubset(columns)


def test_admin_log_retains_deleted_evaluation_target_id(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        columns = {row["name"] for row in db.execute("pragma table_info(admin_log)")}

    assert "target_evaluation_id" in columns


def test_initialize_database_migrates_existing_admin_log_target_id(
    tmp_path: Path,
):
    db_path = tmp_path / "eval.db"
    with connect(db_path) as db:
        db.execute(
            """
            create table admin_log (
                id integer primary key,
                actor text not null,
                action text not null,
                evaluation_id integer,
                details text,
                created_at text not null default current_timestamp
            )
            """
        )

    initialize_database(db_path)

    with connect(db_path) as db:
        columns = {row["name"] for row in db.execute("pragma table_info(admin_log)")}

    assert "target_evaluation_id" in columns


def test_evaluations_store_import_export_metadata(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        columns = {
            row["name"]
            for row in db.execute("pragma table_info(evaluations)")
        }

    assert {
        "school_year",
        "grade",
        "class_group",
        "subject",
        "teacher_id",
        "questionnaire_version",
        "expected_participants",
        "status",
        "student_token",
        "teacher_token",
    }.issubset(columns)


def test_evaluations_prevent_duplicate_import_rows(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        insert_teacher(db)
        insert_evaluation(db, evaluation_id=1, student_token="STUDENT1")

        with pytest.raises(sqlite3.IntegrityError):
            insert_evaluation(db, evaluation_id=2, student_token="STUDENT2")


def test_evaluation_grade_matches_questionnaire_domain(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        insert_teacher(db)
        insert_evaluation(db, evaluation_id=1, grade=10, student_token="STUDENT1")

        with pytest.raises(sqlite3.IntegrityError):
            insert_evaluation(
                db,
                evaluation_id=2,
                grade=11,
                class_group="11a",
                student_token="STUDENT2",
                teacher_token="TEACHER2",
            )


def test_teacher_pins_are_scoped_by_teacher_and_school_year(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        insert_teacher(db)
        db.execute(
            """
            insert into teacher_pins (teacher_id, school_year, pin_code, pin_hash)
            values (1, '2026/2027', '1234', 'hash-1')
            """
        )
        db.execute(
            """
            insert into teacher_pins (teacher_id, school_year, pin_code, pin_hash)
            values (1, '2027/2028', '5678', 'hash-2')
            """
        )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                """
                insert into teacher_pins (teacher_id, school_year, pin_code, pin_hash)
                values (1, '2026/2027', '9012', 'hash-3')
                """
            )


def insert_teacher(db):
    db.execute(
        "insert into teachers (id, name, email) values (1, 'Ada', 'ada@example.test')"
    )


def insert_evaluation(
    db,
    *,
    evaluation_id: int = 1,
    grade: int = 7,
    class_group: str = "7a",
    student_token: str = "STUDENT1",
    teacher_token: str = "TEACHER1",
) -> None:
    db.execute(
        """
        insert into evaluations (
            id,
            teacher_id,
            title,
            school_year,
            grade,
            class_group,
            subject,
            questionnaire_version,
            expected_participants,
            student_token,
            teacher_token
        ) values (?, 1, 'Eval', '2026/2027', ?, ?, 'Mathe', 'oberstufe-v1', 25, ?, ?)
        """,
        (evaluation_id, grade, class_group, student_token, teacher_token),
    )


def insert_participant(
    db,
    *,
    participant_id: int = 1,
    evaluation_id: int = 1,
) -> None:
    db.execute(
        """
        insert into participants (id, evaluation_id, animal_code)
        values (?, ?, 'fuchs')
        """,
        (participant_id, evaluation_id),
    )
