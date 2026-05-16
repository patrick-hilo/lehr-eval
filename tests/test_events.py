from io import StringIO
from pathlib import Path

import anyio
import pytest
from fastapi.testclient import TestClient

from lehr_eval.app import create_app
from lehr_eval.db import connect
from lehr_eval.events import EventHub, create_events_router
from lehr_eval.imports import import_master_data
from lehr_eval.migrations import initialize_database


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


@pytest.mark.anyio
async def test_event_hub_delivers_evaluation_event():
    hub = EventHub()
    subscription = hub.subscribe(evaluation_id=42)

    await hub.publish(evaluation_id=42, event={"phase": "answering", "item": 0})

    assert await subscription.__anext__() == {"phase": "answering", "item": 0}


@pytest.mark.anyio
async def test_event_hub_isolates_events_by_evaluation_id():
    hub = EventHub()
    subscription = hub.subscribe(evaluation_id=42)
    other_subscription = hub.subscribe(evaluation_id=99)

    await hub.publish(evaluation_id=42, event={"phase": "reading", "item": 0})

    assert await subscription.__anext__() == {"phase": "reading", "item": 0}
    with pytest.raises(TimeoutError):
        with anyio.fail_after(0.01):
            await other_subscription.__anext__()


@pytest.mark.anyio
async def test_sse_endpoint_resolves_token_and_emits_json_data_lines(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)
    hub = client.app.state.event_hub
    endpoint = next(
        route.endpoint
        for route in client.app.routes
        if getattr(route, "path", None) == "/events/{evaluation_token}"
    )
    response = await endpoint(_ConnectedRequest(), qr.student_path.removeprefix("/e/"))

    await hub.publish(
        evaluation_id=qr.evaluation_id, event={"phase": "answering", "item": 0}
    )
    snapshot = await response.body_iterator.__anext__()
    line = await response.body_iterator.__anext__()

    assert response.media_type == "text/event-stream"
    assert snapshot == 'data: {"phase":"active","item":null,"snapshot":true}\n\n'
    assert line == 'data: {"phase":"answering","item":0}\n\n'


@pytest.mark.anyio
async def test_sse_endpoint_emits_current_snapshot_before_waiting_for_events(
    tmp_path: Path,
):
    client, qr, db_path = setup_client(tmp_path)
    endpoint = event_endpoint(client)
    with connect(db_path) as db:
        db.execute(
            """
            update evaluations
            set status = 'reading', current_item_index = 2
            where id = ?
            """,
            (qr.evaluation_id,),
        )

    response = await endpoint(_ConnectedRequest(), qr.student_path.removeprefix("/e/"))
    with anyio.fail_after(0.01):
        line = await response.body_iterator.__anext__()

    assert line == 'data: {"phase":"reading","item":2,"snapshot":true}\n\n'


@pytest.mark.anyio
async def test_sse_snapshot_is_read_after_subscription(tmp_path: Path):
    _client, qr, db_path = setup_client(tmp_path)
    hub = MutatingSubscribeHub(db_path, qr.evaluation_id)
    router = create_events_router(db_path, hub)
    endpoint = next(
        route.endpoint
        for route in router.routes
        if getattr(route, "path", None) == "/events/{evaluation_token}"
    )

    response = await endpoint(_ConnectedRequest(), qr.student_path.removeprefix("/e/"))
    line = await response.body_iterator.__anext__()

    assert hub.subscribed
    assert line == 'data: {"phase":"reading","item":4,"snapshot":true}\n\n'


@pytest.mark.anyio
async def test_unknown_event_token_returns_404(tmp_path: Path):
    client, _qr, _db_path = setup_client(tmp_path)

    response = client.get("/events/not-a-real-token")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_teacher_transition_publishes_phase_and_item_event(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)
    hub = client.app.state.event_hub
    subscription = hub.subscribe(evaluation_id=qr.evaluation_id)
    login = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})
    assert login.status_code == 200

    response = client.post(f"/teacher/{qr.evaluation_id}/start", follow_redirects=False)

    assert response.status_code == 303
    assert await subscription.__anext__() == {"phase": "joining", "item": None}


@pytest.mark.anyio
async def test_student_join_publishes_progress_event(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)
    hub = client.app.state.event_hub
    subscription = hub.subscribe(evaluation_id=qr.evaluation_id)

    response = client.get(qr.student_path)

    assert response.status_code == 200
    assert await subscription.__anext__() == {
        "phase": "active",
        "item": None,
        "progress": True,
    }


def test_live_js_reloads_for_progress_events_only_for_teacher_role():
    live_js = Path("src/lehr_eval/static/live.js").read_text()

    assert "dataset.liveRole" in live_js
    assert "liveRole === \"teacher\"" in live_js
    assert "event.progress === true" in live_js


def test_live_templates_assign_roles(tmp_path: Path):
    client, qr, _db_path = setup_client(tmp_path)
    student = client.get(qr.student_path)
    teacher = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})

    assert 'data-live-role="student"' in student.text
    assert 'data-live-role="teacher"' in teacher.text


def setup_client(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    result = import_master_data(
        db_path, StringIO(CSV), base_url="https://eval.schule.test"
    )
    qr = result.qr_rows[0]
    with connect(db_path) as db:
        db.execute(
            "update evaluations set status = 'active' where id = ?",
            (qr.evaluation_id,),
        )
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    return client, qr, db_path


def event_endpoint(client: TestClient):
    return next(
        route.endpoint
        for route in client.app.routes
        if getattr(route, "path", None) == "/events/{evaluation_token}"
    )


class _ConnectedRequest:
    async def is_disconnected(self) -> bool:
        return False


class MutatingSubscribeHub(EventHub):
    def __init__(self, db_path: Path, evaluation_id: int):
        super().__init__()
        self.db_path = db_path
        self.evaluation_id = evaluation_id
        self.subscribed = False

    def subscribe(self, evaluation_id: int):
        subscription = super().subscribe(evaluation_id)
        assert evaluation_id == self.evaluation_id
        with connect(self.db_path) as db:
            db.execute(
                """
                update evaluations
                set status = 'reading', current_item_index = 4
                where id = ?
                """,
                (evaluation_id,),
            )
        self.subscribed = True
        return subscription
