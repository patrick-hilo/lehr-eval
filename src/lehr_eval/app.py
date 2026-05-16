import os
from pathlib import Path
import secrets

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from lehr_eval.events import EventHub, create_events_router
from lehr_eval.migrations import initialize_database
from lehr_eval.routers.admin import create_admin_router
from lehr_eval.routers.student import create_student_router
from lehr_eval.routers.teacher import create_teacher_router
from lehr_eval.settings import load_settings


def _resolve_secret_key(database_path: Path) -> str:
    env_value = os.environ.get("LEHR_EVAL_SECRET_KEY", "").strip()
    if env_value:
        return env_value
    secret_path = database_path.parent / "secret_key.txt"
    if secret_path.exists():
        existing = secret_path.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    generated = secrets.token_urlsafe(32)
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    secret_path.write_text(generated + "\n", encoding="utf-8")
    try:
        secret_path.chmod(0o600)
    except OSError:
        pass
    return generated


def create_app(
    *, db_path: str | Path | None = None, admin_password: str | None = None
) -> FastAPI:
    settings = load_settings()
    database_path = Path(db_path) if db_path is not None else settings.database_path
    initialize_database(database_path)
    password = admin_password if admin_password is not None else settings.admin_password
    secret_key = _resolve_secret_key(database_path)

    app = FastAPI(title="Lehr-Evaluation")
    event_hub = EventHub()
    app.state.event_hub = event_hub
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie="lehr_eval_admin",
        same_site="lax",
    )
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )
    app.include_router(create_admin_router(database_path, password))
    app.include_router(create_events_router(database_path, event_hub))
    app.include_router(create_teacher_router(database_path, event_hub))
    app.include_router(create_student_router(database_path, secret_key, event_hub))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
