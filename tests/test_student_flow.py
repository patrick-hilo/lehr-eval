from io import StringIO
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from lehr_eval.animal_codes import code_for_index
from lehr_eval.app import create_app
from lehr_eval.db import connect
from lehr_eval.imports import import_master_data
from lehr_eval.migrations import initialize_database
from lehr_eval.routers.student import create_participant


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def setup_client(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    result = import_master_data(
        db_path, StringIO(CSV), base_url="https://eval.schule.test"
    )
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login = client.post(
        "/admin/login", data={"password": "secret"}, follow_redirects=False
    )
    assert login.status_code == 303
    client.post(f"/admin/evaluations/{result.qr_rows[0].evaluation_id}/activate")
    return client, result.qr_rows[0], db_path


def test_student_join_assigns_animal_code_cookie(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)

    response = client.get(qr.student_path)

    assert response.status_code == 200
    assert "lehr_eval_participant" in response.headers["set-cookie"]
    assert "Dein Tiername" in response.text


def test_student_qr_path_uses_student_token(tmp_path: Path):
    _client, qr, db_path = setup_client(tmp_path)
    with connect(db_path) as db:
        token = db.execute(
            "select student_token from evaluations where id = ?", (qr.evaluation_id,)
        ).fetchone()["student_token"]

    assert qr.student_path == f"/e/{token}"


def test_student_join_reuses_cookie_without_duplicate_participant(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)

    first = client.get(qr.student_path)
    second = client.get(qr.student_path)

    assert first.status_code == 200
    assert second.status_code == 200
    assert participant_count(db_path, qr.evaluation_id) == 1
    assert code_for_index(0) in second.text


def test_new_students_join_active_and_joining_with_next_animal_code(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    first = client.get(qr.student_path)
    assert first.status_code == 200

    update_status(db_path, qr.evaluation_id, "joining")
    second_client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    second = second_client.get(qr.student_path)

    assert second.status_code == 200
    assert participant_codes(db_path, qr.evaluation_id) == [
        code_for_index(0),
        code_for_index(1),
    ]
    assert code_for_index(1) in second.text


def test_new_student_after_first_item_starts_sees_manual_rejoin_form(tmp_path: Path):
    _client, qr, db_path = setup_client(tmp_path)
    update_status(db_path, qr.evaluation_id, "reading")
    new_client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    response = new_client.get(qr.student_path)

    assert response.status_code == 200
    assert "Mit Tiername erneut beitreten" in response.text
    assert "Dein Tiername" not in response.text
    assert "lehr_eval_participant" not in response.headers.get("set-cookie", "")
    assert participant_count(db_path, qr.evaluation_id) == 0


def test_rejoin_only_page_does_not_load_live_updates(tmp_path: Path):
    _client, qr, db_path = setup_client(tmp_path)
    update_status(db_path, qr.evaluation_id, "reading")
    new_client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    response = new_client.get(qr.student_path)

    assert response.status_code == 200
    assert "Mit Tiername erneut beitreten" in response.text
    assert "/static/live.js" not in response.text
    assert "data-event-url" not in response.text


def test_existing_cookie_can_rejoin_after_first_item_starts(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    client.get(qr.student_path)
    update_status(db_path, qr.evaluation_id, "answering")

    response = client.get(qr.student_path)

    assert response.status_code == 200
    assert participant_count(db_path, qr.evaluation_id) == 1
    assert code_for_index(0) in response.text


def test_manual_animal_code_rejoin_sets_cookie_after_first_item_starts(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    client.get(qr.student_path)
    update_status(db_path, qr.evaluation_id, "reading")

    rejoin_client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    rejoin = rejoin_client.post(
        f"{qr.student_path}/rejoin",
        data={"animal_code": code_for_index(0)},
        follow_redirects=False,
    )
    response = rejoin_client.get(qr.student_path)

    assert rejoin.status_code == 303
    assert "lehr_eval_participant" in rejoin.headers["set-cookie"]
    assert response.status_code == 200
    assert code_for_index(0) in response.text
    assert participant_count(db_path, qr.evaluation_id) == 1


def test_manual_rejoin_recovers_after_app_restart_invalidates_cookie(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    join = client.get(qr.student_path)
    assert join.status_code == 200
    update_status(db_path, qr.evaluation_id, "reading")

    restarted_client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    rejoin_form = restarted_client.get(qr.student_path)
    rejoin = restarted_client.post(
        f"{qr.student_path}/rejoin",
        data={"animal_code": code_for_index(0)},
        follow_redirects=False,
    )
    restored = restarted_client.get(qr.student_path)

    assert rejoin_form.status_code == 200
    assert "Mit Tiername erneut beitreten" in rejoin_form.text
    assert "Dein Tiername" not in rejoin_form.text
    assert rejoin.status_code == 303
    assert "lehr_eval_participant" in rejoin.headers["set-cookie"]
    assert restored.status_code == 200
    assert "Dein Tiername" in restored.text
    assert code_for_index(0) in restored.text
    assert participant_count(db_path, qr.evaluation_id) == 1


def test_create_participant_retries_next_animal_code_after_unique_collision():
    db = CollisionDb()

    participant = create_participant(db, evaluation_id=1)

    assert participant == {"id": 42, "animal_code": code_for_index(1)}
    assert db.inserted_codes == [code_for_index(0), code_for_index(1)]


def update_status(db_path: Path, evaluation_id: int, status: str) -> None:
    with connect(db_path) as db:
        db.execute(
            "update evaluations set status = ? where id = ?", (status, evaluation_id)
        )


def participant_count(db_path: Path, evaluation_id: int) -> int:
    with connect(db_path) as db:
        return int(
            db.execute(
                "select count(*) from participants where evaluation_id = ?",
                (evaluation_id,),
            ).fetchone()[0]
        )


def participant_codes(db_path: Path, evaluation_id: int) -> list[str]:
    with connect(db_path) as db:
        return [
            row["animal_code"]
            for row in db.execute(
                """
                select animal_code
                from participants
                where evaluation_id = ?
                order by id
                """,
                (evaluation_id,),
            )
        ]


class CollisionDb:
    def __init__(self):
        self.inserted_codes: list[str] = []

    def execute(self, query: str, parameters=()):
        normalized_query = query.strip()
        if normalized_query.startswith("select count(*)"):
            return CountResult()

        if normalized_query.startswith("insert into participants"):
            animal_code = parameters[1]
            self.inserted_codes.append(animal_code)
            if animal_code == code_for_index(0):
                raise sqlite3.IntegrityError(
                    "UNIQUE constraint failed: participants.evaluation_id, "
                    "participants.animal_code"
                )
            return InsertResult()

        raise AssertionError(f"unexpected query: {query}")


class CountResult:
    def fetchone(self):
        return (0,)


class InsertResult:
    lastrowid = 42
