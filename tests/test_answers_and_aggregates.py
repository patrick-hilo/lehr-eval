from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import lehr_eval.live as live
from lehr_eval.app import create_app
from lehr_eval.db import connect
from lehr_eval.imports import import_master_data
from lehr_eval.live import (
    close_evaluation,
    open_answer_phase,
    pause_evaluation,
    show_first_item,
    start_joining,
)
from lehr_eval.migrations import initialize_database
from lehr_eval.questionnaires import questionnaire_for_grade


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def test_only_latest_answer_counts_when_item_is_finalized(tmp_path: Path):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)

    live.submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=0)
    live.submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=3)
    live.finalize_current_item(db_path, evaluation_id)

    aggregate = live.get_item_aggregate(db_path, evaluation_id, item_index=0)

    assert aggregate.count_0 == 0
    assert aggregate.count_3 == 1
    assert aggregate.mean == 3.0


def test_finalized_item_counts_missing_joined_participants(tmp_path: Path):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)
    add_participant(db_path, evaluation_id, "zweiter")

    live.submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=2)
    live.finalize_current_item(db_path, evaluation_id)

    aggregate = live.get_item_aggregate(db_path, evaluation_id, item_index=0)

    assert aggregate.count_2 == 1
    assert aggregate.joined_count == 2
    assert aggregate.missing_count == 1
    assert aggregate.mean == 2.0


def test_item_with_no_answers_has_null_mean(tmp_path: Path):
    db_path, evaluation_id, _participant_id = prepared_answering_evaluation(tmp_path)

    live.finalize_current_item(db_path, evaluation_id)

    aggregate = live.get_item_aggregate(db_path, evaluation_id, item_index=0)

    assert aggregate.joined_count == 1
    assert aggregate.missing_count == 1
    assert aggregate.mean is None


def test_submit_answer_rejects_wrong_phase_item_and_value(tmp_path: Path):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)

    with pytest.raises(ValueError, match="between 0 and 3"):
        live.submit_answer(
            db_path, evaluation_id, participant_id, item_index=0, value=4
        )

    with pytest.raises(ValueError, match="current item"):
        live.submit_answer(
            db_path, evaluation_id, participant_id, item_index=1, value=2
        )

    live.finalize_current_item(db_path, evaluation_id)
    with pytest.raises(ValueError, match="answering"):
        live.submit_answer(
            db_path, evaluation_id, participant_id, item_index=1, value=2
        )


def test_closing_evaluation_deletes_live_answers_and_participants(tmp_path: Path):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)

    live.submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=2)
    live.finalize_current_item(db_path, evaluation_id)
    close_evaluation(db_path, evaluation_id)

    assert live.count_live_answers(db_path, evaluation_id) == 0
    assert live.count_participants(db_path, evaluation_id) == 0
    assert live.get_item_aggregate(db_path, evaluation_id, item_index=0).count_2 == 1


def test_closing_answering_evaluation_finalizes_current_item_before_cleanup(
    tmp_path: Path,
):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)

    live.submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=1)
    close_evaluation(db_path, evaluation_id)

    assert live.count_live_answers(db_path, evaluation_id) == 0
    assert live.count_participants(db_path, evaluation_id) == 0
    assert live.get_item_aggregate(db_path, evaluation_id, item_index=0).count_1 == 1


def test_closing_paused_answering_evaluation_finalizes_current_item_before_cleanup(
    tmp_path: Path,
):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)

    live.submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=2)
    pause_evaluation(db_path, evaluation_id)
    close_evaluation(db_path, evaluation_id)

    aggregate = live.get_item_aggregate(db_path, evaluation_id, item_index=0)
    assert aggregate is not None
    assert aggregate.count_2 == 1
    assert live.count_live_answers(db_path, evaluation_id) == 0
    assert live.count_participants(db_path, evaluation_id) == 0


def test_closing_reading_evaluation_does_not_create_unanswered_aggregate(
    tmp_path: Path,
):
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path)
    start_joining(db_path, evaluation_id)
    show_first_item(db_path, evaluation_id)
    add_participant(db_path, evaluation_id, "erstes")

    close_evaluation(db_path, evaluation_id)

    assert live.get_item_aggregate(db_path, evaluation_id, item_index=0) is None
    assert live.count_participants(db_path, evaluation_id) == 0


def test_student_answer_page_and_post_are_available_only_during_answering(
    tmp_path: Path,
):
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path)
    token = student_token(db_path, evaluation_id)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    join = client.get(f"/e/{token}")
    participant_id = only_participant_id(db_path, evaluation_id)

    start_joining(db_path, evaluation_id)
    show_first_item(db_path, evaluation_id)
    reading = client.get(f"/e/{token}")
    open_answer_phase(db_path, evaluation_id)
    answering = client.get(f"/e/{token}")
    posted = client.post(
        f"/e/{token}/answer", data={"value": "3"}, follow_redirects=False
    )

    assert join.status_code == 200
    assert "value=\"0\"" not in reading.text
    first_item_text = (
        questionnaire_for_grade(8).items[0].text
    )
    assert first_item_text in answering.text
    assert answering.text.count("type=\"radio\"") == 4
    assert posted.status_code == 303
    assert live.count_live_answers(db_path, evaluation_id) == 1
    live.finalize_current_item(db_path, evaluation_id)
    assert live.get_item_aggregate(db_path, evaluation_id, item_index=0).count_3 == 1
    assert participant_id == only_participant_id(db_path, evaluation_id)


def prepared_answering_evaluation(tmp_path: Path) -> tuple[Path, int, int]:
    db_path = tmp_path / "eval.db"
    evaluation_id = setup_evaluation(db_path)
    start_joining(db_path, evaluation_id)
    participant_id = add_participant(db_path, evaluation_id, "erstes")
    show_first_item(db_path, evaluation_id)
    open_answer_phase(db_path, evaluation_id)
    return db_path, evaluation_id, participant_id


def setup_evaluation(db_path: Path) -> int:
    initialize_database(db_path)
    result = import_master_data(
        db_path, StringIO(CSV), base_url="https://eval.schule.test"
    )
    evaluation_id = result.qr_rows[0].evaluation_id
    with connect(db_path) as db:
        db.execute(
            "update evaluations set status = 'active' where id = ?",
            (evaluation_id,),
        )
    return evaluation_id


def add_participant(db_path: Path, evaluation_id: int, animal_code: str) -> int:
    with connect(db_path) as db:
        cursor = db.execute(
            """
            insert into participants (evaluation_id, animal_code, last_seen_at)
            values (?, ?, current_timestamp)
            """,
            (evaluation_id, animal_code),
        )
        return int(cursor.lastrowid)


def student_token(db_path: Path, evaluation_id: int) -> str:
    with connect(db_path) as db:
        return db.execute(
            "select student_token from evaluations where id = ?",
            (evaluation_id,),
        ).fetchone()["student_token"]


def only_participant_id(db_path: Path, evaluation_id: int) -> int:
    with connect(db_path) as db:
        return int(
            db.execute(
                "select id from participants where evaluation_id = ?",
                (evaluation_id,),
            ).fetchone()["id"]
        )
