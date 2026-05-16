from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from lehr_eval.db import connect
from lehr_eval.questionnaires import questionnaire_for_grade


LIVE_PHASES = {"joining", "reading", "answering"}


@dataclass(frozen=True)
class LiveState:
    evaluation_id: int
    phase: str
    current_item_index: int | None


@dataclass(frozen=True)
class ItemAggregate:
    evaluation_id: int
    item_key: str
    count_0: int
    count_1: int
    count_2: int
    count_3: int
    missing_count: int
    joined_count: int
    mean: float | None


def start_joining(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] not in {"active", "joining"}:
            raise ValueError("evaluation must be active to start joining")
        _set_state(db, evaluation_id, "joining", None)
        return _state(db, evaluation_id)


def show_first_item(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] not in {"joining", "reading"}:
            raise ValueError("evaluation must be joining before showing first item")
        index = row["current_item_index"]
        _set_state(db, evaluation_id, "reading", 0 if index is None else int(index))
        return _state(db, evaluation_id)


def open_answer_phase(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] != "reading":
            raise ValueError("evaluation must be reading before opening answers")
        if row["current_item_index"] is None:
            raise ValueError("evaluation must have a current item")
        _set_state(db, evaluation_id, "answering", int(row["current_item_index"]))
        return _state(db, evaluation_id)


def finish_current_item(db_path: str | Path, evaluation_id: int) -> LiveState:
    return finalize_current_item(db_path, evaluation_id)


def submit_answer(
    db_path: str | Path,
    evaluation_id: int,
    participant_id: int,
    item_index: int,
    value: int,
) -> None:
    if value not in {0, 1, 2, 3}:
        raise ValueError("answer value must be between 0 and 3")

    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] != "answering":
            raise ValueError(
                "evaluation must be answering before answers can be submitted"
            )
        if (
            row["current_item_index"] is None
            or int(row["current_item_index"]) != item_index
        ):
            raise ValueError("answer must be submitted for the current item")

        participant = db.execute(
            """
            select id
            from participants
            where id = ? and evaluation_id = ?
            """,
            (participant_id, evaluation_id),
        ).fetchone()
        if participant is None:
            raise ValueError("participant not found for evaluation")

        item_key = _item_key(row, item_index)
        db.execute(
            """
            insert into live_answers (
                evaluation_id,
                participant_id,
                item_key,
                answer_value,
                answered_at
            ) values (?, ?, ?, ?, current_timestamp)
            on conflict(participant_id, item_key) do update set
                answer_value = excluded.answer_value,
                answered_at = current_timestamp
            """,
            (evaluation_id, participant_id, item_key, value),
        )


def finalize_current_item(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] != "answering":
            raise ValueError("evaluation must be answering before finalizing an item")
        current_index = row["current_item_index"]
        if current_index is None:
            raise ValueError("evaluation must have a current item")

        _finalize_item(db, row, int(current_index))
        next_index = int(current_index) + 1
        if next_index >= _item_count(row):
            _close(db, evaluation_id, int(current_index))
        else:
            _set_state(db, evaluation_id, "reading", next_index)
        return _state(db, evaluation_id)


def pause_evaluation(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] not in LIVE_PHASES:
            raise ValueError("only live evaluations can be paused")
        db.execute(
            """
            update evaluations
            set status = 'paused',
                previous_status = ?,
                updated_at = current_timestamp
            where id = ?
            """,
            (row["status"], evaluation_id),
        )
        return _state(db, evaluation_id)


def resume_evaluation(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] != "paused":
            raise ValueError("evaluation must be paused before resuming")
        phase = row["previous_status"] or "joining"
        if phase not in LIVE_PHASES:
            phase = "joining"
        _set_state(db, evaluation_id, phase, row["current_item_index"])
        return _state(db, evaluation_id)


def close_evaluation(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        row = _evaluation(db, evaluation_id)
        if row["status"] not in LIVE_PHASES | {"paused"}:
            raise ValueError("evaluation must be live or paused before closing")
        should_finalize = row["status"] == "answering" or (
            row["status"] == "paused" and row["previous_status"] == "answering"
        )
        if should_finalize:
            current_index = row["current_item_index"]
            if current_index is None:
                raise ValueError("evaluation must have a current item")
            _finalize_item(db, row, int(current_index))
        _close(db, evaluation_id, row["current_item_index"])
        return _state(db, evaluation_id)


def get_state(db_path: str | Path, evaluation_id: int) -> LiveState:
    with connect(db_path) as db:
        return _state(db, evaluation_id)


def get_item_aggregate(
    db_path: str | Path, evaluation_id: int, item_index: int
) -> ItemAggregate | None:
    with connect(db_path) as db:
        evaluation = _evaluation(db, evaluation_id)
        item_key = _item_key(evaluation, item_index)
        row = db.execute(
            """
            select
                evaluation_id,
                item_key,
                count_0,
                count_1,
                count_2,
                count_3,
                missing_count,
                joined_count,
                mean
            from item_aggregates
            where evaluation_id = ? and item_key = ?
            """,
            (evaluation_id, item_key),
        ).fetchone()
    if row is None:
        return None
    return ItemAggregate(
        evaluation_id=int(row["evaluation_id"]),
        item_key=row["item_key"],
        count_0=int(row["count_0"]),
        count_1=int(row["count_1"]),
        count_2=int(row["count_2"]),
        count_3=int(row["count_3"]),
        missing_count=int(row["missing_count"]),
        joined_count=int(row["joined_count"]),
        mean=None if row["mean"] is None else float(row["mean"]),
    )


def count_live_answers(db_path: str | Path, evaluation_id: int) -> int:
    with connect(db_path) as db:
        return int(
            db.execute(
                "select count(*) from live_answers where evaluation_id = ?",
                (evaluation_id,),
            ).fetchone()[0]
        )


def count_participants(db_path: str | Path, evaluation_id: int) -> int:
    with connect(db_path) as db:
        return int(
            db.execute(
                "select count(*) from participants where evaluation_id = ?",
                (evaluation_id,),
            ).fetchone()[0]
        )


def _evaluation(db, evaluation_id: int):
    row = db.execute(
        """
        select id, status, current_item_index, previous_status, grade
        from evaluations
        where id = ?
        """,
        (evaluation_id,),
    ).fetchone()
    if row is None:
        raise ValueError("evaluation not found")
    return row


def _state(db, evaluation_id: int) -> LiveState:
    row = _evaluation(db, evaluation_id)
    index = row["current_item_index"]
    return LiveState(
        evaluation_id=int(row["id"]),
        phase=row["status"],
        current_item_index=None if index is None else int(index),
    )


def _set_state(db, evaluation_id: int, phase: str, item_index: int | None) -> None:
    db.execute(
        """
        update evaluations
        set status = ?,
            current_item_index = ?,
            previous_status = null,
            updated_at = current_timestamp
        where id = ?
        """,
        (phase, item_index, evaluation_id),
    )


def _close(db, evaluation_id: int, item_index: int | None) -> None:
    db.execute("delete from live_answers where evaluation_id = ?", (evaluation_id,))
    db.execute("delete from participants where evaluation_id = ?", (evaluation_id,))
    db.execute(
        """
        update evaluations
        set status = 'closed',
            current_item_index = ?,
            previous_status = null,
            updated_at = current_timestamp
        where id = ?
        """,
        (item_index, evaluation_id),
    )


def _finalize_item(db, evaluation, item_index: int) -> None:
    evaluation_id = int(evaluation["id"])
    item_key = _item_key(evaluation, item_index)
    joined_count = int(
        db.execute(
            "select count(*) from participants where evaluation_id = ?",
            (evaluation_id,),
        ).fetchone()[0]
    )
    answer_counts = {value: 0 for value in range(4)}
    for row in db.execute(
        """
        select answer_value, count(*) as answer_count
        from live_answers
        where evaluation_id = ? and item_key = ?
        group by answer_value
        """,
        (evaluation_id, item_key),
    ):
        answer_counts[int(row["answer_value"])] = int(row["answer_count"])

    answered_count = sum(answer_counts.values())
    missing_count = joined_count - answered_count
    weighted_sum = sum(value * count for value, count in answer_counts.items())
    mean = None if answered_count == 0 else weighted_sum / answered_count

    try:
        db.execute(
            """
            insert into item_aggregates (
                evaluation_id,
                item_key,
                count_0,
                count_1,
                count_2,
                count_3,
                missing_count,
                joined_count,
                mean
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                item_key,
                answer_counts[0],
                answer_counts[1],
                answer_counts[2],
                answer_counts[3],
                missing_count,
                joined_count,
                mean,
            ),
        )
    except sqlite3.IntegrityError as error:
        if "item_aggregates.evaluation_id, item_aggregates.item_key" not in str(error):
            raise

    db.execute(
        "delete from live_answers where evaluation_id = ? and item_key = ?",
        (evaluation_id, item_key),
    )


def _item_count(evaluation) -> int:
    return len(questionnaire_for_grade(int(evaluation["grade"])).items)


def _item_key(evaluation, item_index: int) -> str:
    items = questionnaire_for_grade(int(evaluation["grade"])).items
    if item_index < 0 or item_index >= len(items):
        raise ValueError("item index out of range")
    return items[item_index].key
