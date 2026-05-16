from base64 import b64encode
import json
from pathlib import Path

from fastapi.testclient import TestClient
import itsdangerous

from lehr_eval.app import create_app
from lehr_eval.db import connect
from lehr_eval.migrations import initialize_database


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def test_admin_page_requires_login(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    response = client.get("/admin/evaluations", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_can_login(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    response = client.post(
        "/admin/login", data={"password": "secret"}, follow_redirects=False
    )

    assert response.status_code == 303
    assert "lehr_eval_admin" in response.headers["set-cookie"]


def test_wrong_admin_password_returns_401(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    response = client.post("/admin/login", data={"password": "wrong"})

    assert response.status_code == 401
    assert "Anmeldung" in response.text


def test_default_app_health_works_but_admin_login_is_not_usable(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    client = TestClient(create_app(db_path=db_path))

    assert client.get("/health").json() == {"status": "ok"}

    login_response = client.post("/admin/login", data={"password": "anything"})
    assert login_response.status_code == 401

    client.cookies.set("lehr_eval_admin", forged_admin_cookie())
    admin_response = client.get("/admin/evaluations", follow_redirects=False)
    assert admin_response.status_code == 303
    assert admin_response.headers["location"] == "/admin/login"


def test_admin_evaluations_page_after_login(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.get("/admin/evaluations")

    assert response.status_code == 200
    assert "Evaluationen" in response.text
    assert "Stammdaten importieren" in response.text


def test_admin_import_requires_login(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    response = client.post(
        "/admin/import",
        files={"csv_file": ("stammdaten.csv", CSV, "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_can_import_master_data_from_csv(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    monkeypatch.setenv("LEHR_EVAL_BASE_URL", "https://eval.schule.test")
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(
        "/admin/import",
        files={"csv_file": ("stammdaten.csv", CSV, "text/csv")},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/evaluations"
    with connect(db_path) as db:
        evaluation = db.execute(
            """
            select evaluations.status, evaluations.base_url, teachers.email
            from evaluations
            join teachers on teachers.id = evaluations.teacher_id
            """
        ).fetchone()
        pin = db.execute("select pin_code from teacher_pins").fetchone()
    assert dict(evaluation) == {
        "status": "prepared",
        "base_url": "https://eval.schule.test",
        "email": "mueller@example.edu",
    }
    assert pin["pin_code"].isdigit()


def test_admin_import_rejects_invalid_csv(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(
        "/admin/import",
        files={"csv_file": ("stammdaten.csv", "not,the,right,columns\n", "text/csv")},
    )

    assert response.status_code == 400
    assert "CSV-Spalten ungueltig" in response.text


def test_admin_can_activate_prepared_evaluation(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    evaluation_id = insert_evaluation(db_path, status="prepared")
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(
        f"/admin/evaluations/{evaluation_id}/activate", follow_redirects=False
    )

    assert response.status_code == 303
    assert evaluation_status(db_path, evaluation_id) == "active"
    assert admin_log_actions(db_path) == ["activate"]


def test_admin_can_deactivate_unused_active_evaluation(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    evaluation_id = insert_evaluation(db_path, status="active")
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(
        f"/admin/evaluations/{evaluation_id}/deactivate", follow_redirects=False
    )

    assert response.status_code == 303
    assert evaluation_status(db_path, evaluation_id) == "deactivated"
    assert admin_log_actions(db_path) == ["deactivate"]


def test_admin_cannot_deactivate_evaluation_with_participant(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    evaluation_id = insert_evaluation(db_path, status="active")
    insert_participant(db_path, evaluation_id)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(f"/admin/evaluations/{evaluation_id}/deactivate")

    assert response.status_code == 409
    assert evaluation_status(db_path, evaluation_id) == "active"
    assert admin_log_actions(db_path) == []


def test_admin_cannot_deactivate_evaluation_with_item_aggregate(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    evaluation_id = insert_evaluation(db_path, status="active")
    insert_item_aggregate(db_path, evaluation_id)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(f"/admin/evaluations/{evaluation_id}/deactivate")

    assert response.status_code == 409
    assert evaluation_status(db_path, evaluation_id) == "active"
    assert admin_log_actions(db_path) == []


def test_admin_can_delete_unused_evaluation(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    evaluation_id = insert_evaluation(db_path, status="prepared")
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(
        f"/admin/evaluations/{evaluation_id}/delete", follow_redirects=False
    )

    assert response.status_code == 303
    with connect(db_path) as db:
        count = db.execute(
            "select count(*) from evaluations where id = ?", (evaluation_id,)
        ).fetchone()[0]
    assert count == 0
    assert admin_log_actions(db_path) == ["delete"]
    assert admin_log_target_ids(db_path) == [evaluation_id]


def test_admin_cannot_delete_used_evaluation(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    evaluation_id = insert_evaluation(db_path, status="prepared")
    insert_item_aggregate(db_path, evaluation_id)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    login(client)

    response = client.post(f"/admin/evaluations/{evaluation_id}/delete")

    assert response.status_code == 409
    assert evaluation_status(db_path, evaluation_id) == "prepared"
    assert admin_log_actions(db_path) == []


def login(client: TestClient) -> None:
    response = client.post(
        "/admin/login", data={"password": "secret"}, follow_redirects=False
    )
    assert response.status_code == 303


def forged_admin_cookie() -> str:
    session = b64encode(json.dumps({"admin_authenticated": True}).encode("utf-8"))
    return itsdangerous.TimestampSigner("lehr-eval-local-admin").sign(session).decode(
        "utf-8"
    )


def insert_evaluation(db_path: Path, *, status: str) -> int:
    with connect(db_path) as db:
        db.execute(
            "insert into teachers (id, name, email) values (1, 'Ada', 'ada@test.local')"
        )
        cursor = db.execute(
            """
            insert into evaluations (
                teacher_id,
                title,
                school_year,
                grade,
                class_group,
                subject,
                questionnaire_version,
                expected_participants,
                status,
                student_token,
                teacher_token
            ) values (
                1,
                'Mathematik 8b',
                '2025/26',
                8,
                '8b',
                'Mathematik',
                'sekundarstufe-v1',
                24,
                ?,
                'student-token',
                'teacher-token'
            )
            """,
            (status,),
        )
        return int(cursor.lastrowid)


def insert_participant(db_path: Path, evaluation_id: int) -> None:
    with connect(db_path) as db:
        db.execute(
            """
            insert into participants (evaluation_id, animal_code)
            values (?, 'fuchs')
            """,
            (evaluation_id,),
        )


def insert_item_aggregate(db_path: Path, evaluation_id: int) -> None:
    with connect(db_path) as db:
        db.execute(
            """
            insert into item_aggregates (evaluation_id, item_key, joined_count)
            values (?, 'item-1', 1)
            """,
            (evaluation_id,),
        )


def evaluation_status(db_path: Path, evaluation_id: int) -> str:
    with connect(db_path) as db:
        return db.execute(
            "select status from evaluations where id = ?", (evaluation_id,)
        ).fetchone()["status"]


def admin_log_actions(db_path: Path) -> list[str]:
    with connect(db_path) as db:
        return [
            row["action"]
            for row in db.execute("select action from admin_log order by id")
        ]


def admin_log_target_ids(db_path: Path) -> list[int]:
    with connect(db_path) as db:
        return [
            row["target_evaluation_id"]
            for row in db.execute(
                "select target_evaluation_id from admin_log order by id"
            )
        ]
