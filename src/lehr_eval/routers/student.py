from pathlib import Path
import sqlite3
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeSerializer

from lehr_eval.animal_codes import code_for_index
from lehr_eval.db import connect
from lehr_eval.events import EventHub
from lehr_eval.live import submit_answer
from lehr_eval.questionnaires import questionnaire_for_grade


PARTICIPANT_COOKIE = "lehr_eval_participant"
JOIN_STATUSES = {"active", "joining"}
ANSWER_LABELS = (
    "stimme nicht zu",
    "stimme eher nicht zu",
    "stimme eher zu",
    "stimme zu",
)

templates = Jinja2Templates(directory=Path(__file__).parents[1] / "templates")


def create_student_router(
    db_path: Path, cookie_secret: str, event_hub: EventHub
) -> APIRouter:
    router = APIRouter()
    signer = URLSafeSerializer(cookie_secret, salt=PARTICIPANT_COOKIE)

    @router.get("/e/{student_token}", response_class=HTMLResponse)
    def student_entry(request: Request, student_token: str) -> HTMLResponse:
        with connect(db_path) as db:
            evaluation = evaluation_for_token(db, student_token)
            participant = participant_from_cookie(db, request, signer, evaluation["id"])

            if participant is None:
                if evaluation["status"] not in JOIN_STATUSES:
                    return render_rejoin_page(request, student_token)
                participant = create_participant(db, evaluation["id"])
                publish_student_progress(event_hub, evaluation)

            touch_participant(db, participant["id"])
            submitted_value = current_submitted_value(db, evaluation, participant)

        if evaluation["status"] in {"reading", "answering"}:
            response = render_answer_page(
                request,
                student_token,
                evaluation,
                participant,
                submitted_value=submitted_value,
            )
        else:
            response = render_wait_page(
                request, student_token, evaluation, participant["animal_code"]
            )
        set_participant_cookie(response, signer, evaluation["id"], participant["id"])
        return response

    @router.post("/e/{student_token}/rejoin")
    def rejoin(
        student_token: str, animal_code: str = Form(...)
    ) -> RedirectResponse:
        with connect(db_path) as db:
            evaluation = evaluation_for_token(db, student_token)
            participant = db.execute(
                """
                select id, animal_code
                from participants
                where evaluation_id = ? and animal_code = ?
                """,
                (evaluation["id"], animal_code.strip()),
            ).fetchone()
            if participant is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND)

            touch_participant(db, participant["id"])
            publish_student_progress(event_hub, evaluation)

        response = RedirectResponse(
            f"/e/{student_token}", status_code=status.HTTP_303_SEE_OTHER
        )
        set_participant_cookie(response, signer, evaluation["id"], participant["id"])
        return response

    @router.post("/e/{student_token}/answer")
    def answer(
        request: Request, student_token: str, value: int = Form(...)
    ) -> RedirectResponse:
        with connect(db_path) as db:
            evaluation = evaluation_for_token(db, student_token)
            participant = participant_from_cookie(db, request, signer, evaluation["id"])
            if participant is None:
                raise HTTPException(status.HTTP_403_FORBIDDEN)
            item_index = evaluation["current_item_index"]
            if item_index is None:
                raise HTTPException(status.HTTP_409_CONFLICT, detail="no current item")

        try:
            submit_answer(
                db_path,
                evaluation["id"],
                participant["id"],
                item_index=int(item_index),
                value=value,
            )
        except ValueError:
            # Antwortphase ist vorbei oder Item hat gewechselt.
            # Statt Fehlerseite: Schueler-Seite neu laden (zeigt aktuellen Stand).
            return RedirectResponse(
                f"/e/{student_token}", status_code=status.HTTP_303_SEE_OTHER
            )

        publish_student_progress(event_hub, evaluation)
        return RedirectResponse(
            f"/e/{student_token}", status_code=status.HTTP_303_SEE_OTHER
        )

    return router


def evaluation_for_token(db, student_token: str):
    evaluation = db.execute(
        """
        select id, status, title, grade, current_item_index
        from evaluations
        where student_token = ?
        """,
        (student_token,),
    ).fetchone()
    if evaluation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return evaluation


def participant_from_cookie(
    db, request: Request, signer: URLSafeSerializer, evaluation_id: int
):
    cookie = request.cookies.get(PARTICIPANT_COOKIE)
    if cookie is None:
        return None

    try:
        payload = signer.loads(cookie)
    except BadSignature:
        return None

    if not isinstance(payload, dict) or payload.get("evaluation_id") != evaluation_id:
        return None

    participant_id = payload.get("participant_id")
    if not isinstance(participant_id, int):
        return None

    return db.execute(
        """
        select id, animal_code
        from participants
        where id = ? and evaluation_id = ?
        """,
        (participant_id, evaluation_id),
    ).fetchone()


def create_participant(db, evaluation_id: int):
    participant_count = db.execute(
        "select count(*) from participants where evaluation_id = ?", (evaluation_id,)
    ).fetchone()[0]
    index = int(participant_count)

    while True:
        animal_code = code_for_index(index)
        try:
            cursor = db.execute(
                """
                insert into participants (evaluation_id, animal_code, last_seen_at)
                values (?, ?, current_timestamp)
                """,
                (evaluation_id, animal_code),
            )
        except sqlite3.IntegrityError as error:
            if not is_animal_code_collision(error):
                raise
            index += 1
            continue

        return {"id": int(cursor.lastrowid), "animal_code": animal_code}


def touch_participant(db, participant_id: int) -> None:
    db.execute(
        "update participants set last_seen_at = current_timestamp where id = ?",
        (participant_id,),
    )


def is_animal_code_collision(error: sqlite3.IntegrityError) -> bool:
    return "participants.evaluation_id, participants.animal_code" in str(error)


def render_wait_page(
    request: Request, student_token: str, evaluation, animal_code: str
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "student_wait.html",
        {
            "animal_code": animal_code,
            "rejoin_path": f"/e/{student_token}/rejoin",
            "event_url": f"/events/{student_token}",
            "live_role": "student",
            "current_phase": evaluation["status"],
            "current_item": evaluation["current_item_index"],
        },
    )


def render_rejoin_page(request: Request, student_token: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "student_wait.html",
        {
            "animal_code": None,
            "rejoin_path": f"/e/{student_token}/rejoin",
            "rejoin_only": True,
        },
    )


def render_answer_page(
    request: Request,
    student_token: str,
    evaluation,
    participant,
    *,
    submitted_value: int | None = None,
) -> HTMLResponse:
    item_index = evaluation["current_item_index"]
    item_text = None
    item_number: int | None = None
    item_total: int | None = None
    if item_index is not None:
        questionnaire = questionnaire_for_grade(int(evaluation["grade"]))
        index = int(item_index)
        item = questionnaire.items[index]
        item_text = item.text
        item_number = index + 1
        item_total = len(questionnaire.items)
    return templates.TemplateResponse(
        request,
        "student_answer.html",
        {
            "animal_code": participant["animal_code"],
            "item_text": item_text,
            "item_number": item_number,
            "item_total": item_total,
            "show_options": evaluation["status"] == "answering",
            "answer_path": f"/e/{student_token}/answer",
            "event_url": f"/events/{student_token}",
            "live_role": "student",
            "current_phase": evaluation["status"],
            "current_item": evaluation["current_item_index"],
            "submitted_value": submitted_value,
            "answer_labels": ANSWER_LABELS,
        },
    )


def current_submitted_value(db, evaluation, participant) -> int | None:
    item_index = evaluation["current_item_index"]
    if item_index is None:
        return None
    questionnaire = questionnaire_for_grade(int(evaluation["grade"]))
    item = questionnaire.items[int(item_index)]
    row = db.execute(
        """
        select answer_value
        from live_answers
        where participant_id = ? and item_key = ?
        """,
        (participant["id"], item.key),
    ).fetchone()
    if row is None:
        return None
    return int(row["answer_value"])


def set_participant_cookie(
    response: Any, signer: URLSafeSerializer, evaluation_id: int, participant_id: int
) -> None:
    cookie_value = signer.dumps(
        {"evaluation_id": evaluation_id, "participant_id": participant_id}
    )
    response.set_cookie(
        PARTICIPANT_COOKIE,
        cookie_value,
        httponly=True,
        samesite="lax",
    )


def publish_student_progress(event_hub: EventHub, evaluation) -> None:
    event_hub.publish_nowait(
        evaluation["id"],
        {
            "phase": evaluation["status"],
            "item": evaluation["current_item_index"],
            "progress": True,
        },
    )
