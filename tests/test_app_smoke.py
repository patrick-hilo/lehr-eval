from fastapi.testclient import TestClient

from lehr_eval.app import create_app
from lehr_eval.db import connect
from lehr_eval.settings import load_settings


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_static_css_is_served():
    client = TestClient(create_app())

    response = client.get("/static/app.css")

    assert response.status_code == 200
    assert "font-family" in response.text


def test_create_app_initializes_configured_database(tmp_path):
    db_path = tmp_path / "eval.db"

    create_app(db_path=db_path)

    with connect(db_path) as db:
        row = db.execute(
            "select name from sqlite_master where type = 'table' and name = 'evaluations'"
        ).fetchone()
    assert row is not None


def test_load_settings_uses_plain_admin_password_env(monkeypatch):
    monkeypatch.setenv("LEHR_EVAL_ADMIN_PASSWORD", "secret")
    monkeypatch.delenv("LEHR_EVAL_ADMIN_PASSWORD_HASH", raising=False)

    settings = load_settings()

    assert settings.admin_password == "secret"
