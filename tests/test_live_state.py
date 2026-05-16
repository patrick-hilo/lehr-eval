from io import StringIO
from pathlib import Path
import sqlite3

import pytest

from lehr_eval.db import connect
from lehr_eval.imports import import_master_data
from lehr_eval.live import (
    close_evaluation,
    finish_current_item,
    open_answer_phase,
    pause_evaluation,
    resume_evaluation,
    show_first_item,
    start_joining,
)
from lehr_eval.migrations import initialize_database


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def test_teacher_advances_from_joining_to_reading_to_answering(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    result = import_master_data(db_path, StringIO(CSV), base_url="https://eval.schule.test")
    evaluation_id = result.qr_rows[0].evaluation_id
    activate_evaluation(db_path, evaluation_id)

    start_joining(db_path, evaluation_id)
    state = show_first_item(db_path, evaluation_id)
    assert state.phase == "reading"
    assert state.current_item_index == 0

    state = open_answer_phase(db_path, evaluation_id)
    assert state.phase == "answering"


def test_teacher_advances_through_items_and_closes_after_item_9(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path)

    start_joining(db_path, evaluation_id)
    show_first_item(db_path, evaluation_id)

    for expected_next_index in range(1, 10):
        open_answer_phase(db_path, evaluation_id)
        state = finish_current_item(db_path, evaluation_id)
        assert state.phase == "reading"
        assert state.current_item_index == expected_next_index

    open_answer_phase(db_path, evaluation_id)
    state = finish_current_item(db_path, evaluation_id)

    assert state.phase == "closed"
    assert state.current_item_index == 9
    assert evaluation_status(db_path, evaluation_id) == "closed"


def test_live_state_rejects_opening_answers_before_item_is_shown(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path)
    start_joining(db_path, evaluation_id)

    with pytest.raises(ValueError, match="reading"):
        open_answer_phase(db_path, evaluation_id)


def test_start_joining_rejects_prepared_evaluation(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path, activate=False)

    with pytest.raises(ValueError, match="active"):
        start_joining(db_path, evaluation_id)

    assert evaluation_status(db_path, evaluation_id) == "prepared"


@pytest.mark.parametrize(
    "status",
    ["prepared", "active", "deactivated", "review_required", "closed"],
)
def test_close_evaluation_rejects_non_live_statuses(tmp_path: Path, status: str):
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path, activate=False)
    update_status(db_path, evaluation_id, status)

    with pytest.raises(ValueError, match="live"):
        close_evaluation(db_path, evaluation_id)

    assert evaluation_status(db_path, evaluation_id) == status


def test_paused_evaluation_resumes_to_previous_live_phase(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path)

    start_joining(db_path, evaluation_id)
    show_first_item(db_path, evaluation_id)
    paused = pause_evaluation(db_path, evaluation_id)
    resumed = resume_evaluation(db_path, evaluation_id)

    assert paused.phase == "paused"
    assert resumed.phase == "reading"
    assert resumed.current_item_index == 0


def test_initialize_database_migrates_live_state_columns(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    with sqlite3.connect(db_path) as db:
        db.execute("create table evaluations (id integer primary key)")

    initialize_database(db_path)

    with connect(db_path) as db:
        columns = {row["name"] for row in db.execute("pragma table_info(evaluations)")}
    assert {"current_item_index", "previous_status"} <= columns


def setup_evaluation(db_path: Path, *, activate: bool = True) -> int:
    initialize_database(db_path)
    result = import_master_data(db_path, StringIO(CSV), base_url="https://eval.schule.test")
    evaluation_id = result.qr_rows[0].evaluation_id
    if activate:
        activate_evaluation(db_path, evaluation_id)
    return evaluation_id


def activate_evaluation(db_path: Path, evaluation_id: int) -> None:
    update_status(db_path, evaluation_id, "active")


def update_status(db_path: Path, evaluation_id: int, status: str) -> None:
    with connect(db_path) as db:
        db.execute(
            "update evaluations set status = ? where id = ?", (status, evaluation_id)
        )


def evaluation_status(db_path: Path, evaluation_id: int) -> str:
    with connect(db_path) as db:
        return db.execute(
            "select status from evaluations where id = ?", (evaluation_id,)
        ).fetchone()["status"]
