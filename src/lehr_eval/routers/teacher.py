from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from lehr_eval.db import connect
from lehr_eval.events import EventHub
from lehr_eval.live import (
    LiveState,
    close_evaluation,
    finish_current_item,
    get_state,
    open_answer_phase,
    pause_evaluation,
    resume_evaluation,
    show_first_item,
    start_joining,
)


templates = Jinja2Templates(directory=Path(__file__).parents[1] / "templates")
TEACHER_SESSION_KEY = "teacher_evaluations"


def create_teacher_router(db_path: Path, event_hub: EventHub) -> APIRouter:
    router = APIRouter()

    @router.get("/t/{teacher_token}", response_class=HTMLResponse)
    def teacher_entry(request: Request, teacher_token: str) -> HTMLResponse:
        evaluation = evaluation_for_teacher_token(db_path, teacher_token)
        if teacher_is_authenticated(request, evaluation["id"], evaluation["teacher_token"]):
            return render_live_page(request, db_path, evaluation["id"])
        return templates.TemplateResponse(
            request,
            "teacher_pin.html",
            {"teacher_token": teacher_token, "error": None},
        )

    @router.post("/t/{teacher_token}", response_class=HTMLResponse)
    def teacher_login(
        request: Request, teacher_token: str, pin: str = Form(...)
    ) -> HTMLResponse:
        evaluation = evaluation_for_teacher_token(db_path, teacher_token)
        if not verify_teacher_pin(db_path, evaluation, pin):
            return templates.TemplateResponse(
                request,
                "teacher_pin.html",
                {"teacher_token": teacher_token, "error": "Falsche PIN."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        mark_teacher_authenticated(request, evaluation["id"], evaluation["teacher_token"])
        return render_live_page(request, db_path, evaluation["id"])

    @router.post("/teacher/{evaluation_id}/start")
    def start(request: Request, evaluation_id: int) -> RedirectResponse:
        require_teacher(request, db_path, evaluation_id)
        publish_live_state(
            event_hub, run_live_action(start_joining, db_path, evaluation_id)
        )
        return redirect_to_teacher(db_path, evaluation_id)

    @router.post("/teacher/{evaluation_id}/item")
    def show_item(request: Request, evaluation_id: int) -> RedirectResponse:
        require_teacher(request, db_path, evaluation_id)
        publish_live_state(
            event_hub, run_live_action(show_first_item, db_path, evaluation_id)
        )
        return redirect_to_teacher(db_path, evaluation_id)

    @router.post("/teacher/{evaluation_id}/answers")
    def show_answers(request: Request, evaluation_id: int) -> RedirectResponse:
        require_teacher(request, db_path, evaluation_id)
        publish_live_state(
            event_hub, run_live_action(open_answer_phase, db_path, evaluation_id)
        )
        return redirect_to_teacher(db_path, evaluation_id)

    @router.post("/teacher/{evaluation_id}/finish")
    def finish_item(request: Request, evaluation_id: int) -> RedirectResponse:
        require_teacher(request, db_path, evaluation_id)
        publish_live_state(
            event_hub, run_live_action(finish_current_item, db_path, evaluation_id)
        )
        return redirect_to_teacher(db_path, evaluation_id)

    @router.post("/teacher/{evaluation_id}/pause")
    def pause(request: Request, evaluation_id: int) -> RedirectResponse:
        require_teacher(request, db_path, evaluation_id)
        publish_live_state(
            event_hub, run_live_action(pause_evaluation, db_path, evaluation_id)
        )
        return redirect_to_teacher(db_path, evaluation_id)

    @router.post("/teacher/{evaluation_id}/resume")
    def resume(request: Request, evaluation_id: int) -> RedirectResponse:
        require_teacher(request, db_path, evaluation_id)
        publish_live_state(
            event_hub, run_live_action(resume_evaluation, db_path, evaluation_id)
        )
        return redirect_to_teacher(db_path, evaluation_id)

    @router.post("/teacher/{evaluation_id}/close")
    def close(request: Request, evaluation_id: int) -> RedirectResponse:
        require_teacher(request, db_path, evaluation_id)
        publish_live_state(
            event_hub, run_live_action(close_evaluation, db_path, evaluation_id)
        )
        return redirect_to_teacher(db_path, evaluation_id)

    return router


def evaluation_for_teacher_token(db_path: Path, teacher_token: str):
    with connect(db_path) as db:
        row = db.execute(
            """
            select
                evaluations.id,
                evaluations.teacher_id,
                evaluations.title,
                evaluations.school_year,
                evaluations.class_group,
                evaluations.subject,
                evaluations.status,
                evaluations.teacher_token,
                teachers.name as teacher_name
            from evaluations
            join teachers on teachers.id = evaluations.teacher_id
            where evaluations.teacher_token = ?
            """,
            (teacher_token,),
        ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return row


def render_live_page(request: Request, db_path: Path, evaluation_id: int) -> HTMLResponse:
    with connect(db_path) as db:
        evaluation = db.execute(
            """
            select
                evaluations.id,
                evaluations.title,
                evaluations.class_group,
                evaluations.subject,
                evaluations.teacher_token,
                teachers.name as teacher_name,
                count(participants.id) as participant_count
            from evaluations
            join teachers on teachers.id = evaluations.teacher_id
            left join participants on participants.evaluation_id = evaluations.id
            where evaluations.id = ?
            group by evaluations.id
            """,
            (evaluation_id,),
        ).fetchone()
    if evaluation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    state = get_state(db_path, evaluation_id)
    return templates.TemplateResponse(
        request,
        "teacher_live.html",
        {
            "evaluation": evaluation,
            "state": state,
            "event_url": f"/events/{evaluation['teacher_token']}",
            "live_role": "teacher",
            "current_phase": state.phase,
            "current_item": state.current_item_index,
        },
    )


def verify_teacher_pin(db_path: Path, evaluation, pin: str) -> bool:
    with connect(db_path) as db:
        row = db.execute(
            """
            select pin_hash
            from teacher_pins
            where teacher_id = ? and school_year = ?
            """,
            (evaluation["teacher_id"], evaluation["school_year"]),
        ).fetchone()
    if row is None:
        return False
    return pin_matches(pin, row["pin_hash"])


def pin_matches(pin: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, hash_hex = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        calculated = hashlib.pbkdf2_hmac(
            "sha256",
            pin.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()
    except (TypeError, ValueError):
        return False
    return hmac.compare_digest(calculated, hash_hex)


def mark_teacher_authenticated(
    request: Request, evaluation_id: int, teacher_token: str
) -> None:
    credentials = teacher_credentials_from_session(request)
    credentials[evaluation_id] = teacher_token
    request.session[TEACHER_SESSION_KEY] = [
        {"evaluation_id": key, "teacher_token": value}
        for key, value in sorted(credentials.items())
    ]


def teacher_is_authenticated(
    request: Request, evaluation_id: int, teacher_token: str
) -> bool:
    return teacher_credentials_from_session(request).get(evaluation_id) == teacher_token


def require_teacher(request: Request, db_path: Path, evaluation_id: int) -> None:
    teacher_token = teacher_token_for_evaluation(db_path, evaluation_id)
    if not teacher_is_authenticated(request, evaluation_id, teacher_token):
        raise HTTPException(status.HTTP_403_FORBIDDEN)


def teacher_credentials_from_session(request: Request) -> dict[int, str]:
    credentials: dict[int, str] = {}
    for item in request.session.get(TEACHER_SESSION_KEY, []):
        if not isinstance(item, dict):
            continue
        evaluation_id = item.get("evaluation_id")
        teacher_token = item.get("teacher_token")
        if isinstance(evaluation_id, int) and isinstance(teacher_token, str):
            credentials[evaluation_id] = teacher_token
    return credentials


def teacher_token_for_evaluation(db_path: Path, evaluation_id: int) -> str:
    with connect(db_path) as db:
        row = db.execute(
            "select teacher_token from evaluations where id = ?", (evaluation_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return row["teacher_token"]


def run_live_action(action, db_path: Path, evaluation_id: int) -> LiveState:
    try:
        return action(db_path, evaluation_id)
    except ValueError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(error)) from error


def publish_live_state(event_hub: EventHub, state: LiveState) -> None:
    event_hub.publish_nowait(
        state.evaluation_id,
        {"phase": state.phase, "item": state.current_item_index},
    )


def redirect_to_teacher(db_path: Path, evaluation_id: int) -> RedirectResponse:
    with connect(db_path) as db:
        row = db.execute(
            "select teacher_token from evaluations where id = ?", (evaluation_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return RedirectResponse(
        f"/t/{row['teacher_token']}", status_code=status.HTTP_303_SEE_OTHER
    )
