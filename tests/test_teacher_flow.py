from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient

from lehr_eval.app import create_app
from lehr_eval.db import connect
from lehr_eval.imports import import_master_data
from lehr_eval.migrations import initialize_database


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def test_teacher_qr_requires_pin(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)

    response = client.get(qr.teacher_path)

    assert response.status_code == 200
    assert "PIN" in response.text
    assert "Starten" not in response.text


def test_teacher_wrong_pin_returns_401(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)

    response = client.post(qr.teacher_path, data={"pin": "not-pin"})

    assert response.status_code == 401
    assert "PIN" in response.text


def test_teacher_correct_pin_shows_live_page_and_sets_evaluation_session(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)

    response = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})

    assert response.status_code == 200
    assert "Live-Steuerung" in response.text
    assert "Status" in response.text
    assert "lehr_eval_admin" in response.headers["set-cookie"]


def test_teacher_can_reopen_live_page_after_auth(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)
    login = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})
    assert login.status_code == 200

    response = client.get(qr.teacher_path)

    assert response.status_code == 200
    assert "Live-Steuerung" in response.text
    assert "PIN" not in response.text


def test_teacher_session_is_specific_to_evaluation(tmp_path: Path):
    client, first_qr, second_qr, _db_path = setup_client_with_two_evaluations(tmp_path)
    login = client.post(first_qr.teacher_path, data={"pin": first_qr.teacher_pin})
    assert login.status_code == 200

    response = client.get(second_qr.teacher_path)

    assert response.status_code == 200
    assert "PIN" in response.text
    assert "Live-Steuerung" not in response.text


def test_teacher_session_does_not_authorize_changed_teacher_token(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    login = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})
    assert login.status_code == 200
    replace_teacher_token(db_path, qr.evaluation_id, "replacement-teacher-token")

    response = client.post(
        f"/teacher/{qr.evaluation_id}/start", follow_redirects=False
    )

    assert response.status_code == 403
    assert evaluation_status(db_path, qr.evaluation_id) == "active"


def test_teacher_live_actions_advance_state_and_close(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    login = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})
    assert login.status_code == 200

    start = client.post(f"/teacher/{qr.evaluation_id}/start", follow_redirects=False)
    first_item = client.post(f"/teacher/{qr.evaluation_id}/item", follow_redirects=False)
    answers = client.post(f"/teacher/{qr.evaluation_id}/answers", follow_redirects=False)
    close = client.post(f"/teacher/{qr.evaluation_id}/close", follow_redirects=False)

    assert start.status_code == 303
    assert first_item.status_code == 303
    assert answers.status_code == 303
    assert close.status_code == 303
    assert evaluation_status(db_path, qr.evaluation_id) == "closed"


def test_teacher_invalid_live_action_redirects_without_state_change(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    login = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})
    assert login.status_code == 200
    start = client.post(f"/teacher/{qr.evaluation_id}/start", follow_redirects=False)
    assert start.status_code == 303

    response = client.post(
        f"/teacher/{qr.evaluation_id}/answers", follow_redirects=False
    )

    # Invalide Aktion fuehrt nicht mehr zu einer JSON-Fehlerseite,
    # sondern zu einem Redirect auf die Live-Seite (kein State-Wechsel).
    assert response.status_code == 303
    assert evaluation_status(db_path, qr.evaluation_id) == "joining"


def test_teacher_can_pause_and_resume_prior_phase(tmp_path: Path):
    client, qr, db_path = setup_client(tmp_path)
    login = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})
    assert login.status_code == 200
    assert client.post(f"/teacher/{qr.evaluation_id}/start").status_code == 200
    assert client.post(f"/teacher/{qr.evaluation_id}/item").status_code == 200

    pause = client.post(f"/teacher/{qr.evaluation_id}/pause", follow_redirects=False)
    resume = client.post(f"/teacher/{qr.evaluation_id}/resume", follow_redirects=False)
    live_page = client.get(qr.teacher_path)

    assert pause.status_code == 303
    assert resume.status_code == 303
    assert evaluation_status(db_path, qr.evaluation_id) == "reading"
    assert "Pausieren" in live_page.text
    assert "Fortsetzen" in live_page.text


def setup_client(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    result = import_master_data(
        db_path, StringIO(CSV), base_url="https://eval.schule.test"
    )
    activate_evaluation(db_path, result.qr_rows[0].evaluation_id)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    return client, result.qr_rows[0], db_path


def setup_client_with_two_evaluations(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    csv = CSV + "2025/26,8,8c,Deutsch,Frau Mueller,mueller@example.edu,22\n"
    result = import_master_data(
        db_path, StringIO(csv), base_url="https://eval.schule.test"
    )
    for qr in result.qr_rows:
        activate_evaluation(db_path, qr.evaluation_id)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    return client, result.qr_rows[0], result.qr_rows[1], db_path


def activate_evaluation(db_path: Path, evaluation_id: int) -> None:
    with connect(db_path) as db:
        db.execute(
            "update evaluations set status = 'active' where id = ?", (evaluation_id,)
        )


def replace_teacher_token(db_path: Path, evaluation_id: int, teacher_token: str) -> None:
    with connect(db_path) as db:
        db.execute(
            "update evaluations set teacher_token = ? where id = ?",
            (teacher_token, evaluation_id),
        )


def evaluation_status(db_path: Path, evaluation_id: int) -> str:
    with connect(db_path) as db:
        return db.execute(
            "select status from evaluations where id = ?", (evaluation_id,)
        ).fetchone()["status"]
