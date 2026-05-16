# Minimal On-Prem Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working on-premises Lehr-Evaluation web app for anonymous student participation, teacher-led live evaluation flow, SQLite persistence, and administrative imports/exports.

**Architecture:** One Python web application serves admin, teacher, and student browser interfaces. SQLite in WAL mode stores evaluation metadata, live state, transient participation data, item aggregates, and admin logs; Server-Sent Events notify connected browsers when the teacher advances the live flow. The app is designed to sit behind Caddy on a school-network DNS name.

**Tech Stack:** Python 3.12, FastAPI, Jinja2, SQLite, Server-Sent Events, openpyxl for XLSX, qrcode/Pillow for QR material, pytest/httpx for tests, uv for all Python execution.

---

## File Structure

- Create `pyproject.toml`: project metadata, runtime dependencies, test dependencies, app entrypoint.
- Create `src/lehr_eval/app.py`: FastAPI app factory, router registration, static/template setup.
- Create `src/lehr_eval/settings.py`: environment-based settings including database path, base URL, admin password hash.
- Create `src/lehr_eval/db.py`: SQLite connection helper, WAL setup, transaction helper.
- Create `src/lehr_eval/schema.sql`: database schema.
- Create `src/lehr_eval/migrations.py`: idempotent schema initialization.
- Create `src/lehr_eval/questionnaires.py`: fixed lower/upper questionnaire definitions and version identifiers.
- Create `src/lehr_eval/animal_codes.py`: deterministic unique animal-code assignment.
- Create `src/lehr_eval/imports.py`: CSV import validation and evaluation creation.
- Create `src/lehr_eval/live.py`: evaluation state machine and aggregate finalization.
- Create `src/lehr_eval/auth.py`: admin session handling and teacher PIN checks.
- Create `src/lehr_eval/events.py`: in-process Server-Sent Events broadcaster.
- Create `src/lehr_eval/exports.py`: XLSX exports and printable QR material generation.
- Create `src/lehr_eval/routers/admin.py`: admin pages and actions.
- Create `src/lehr_eval/routers/student.py`: student join, rejoin, answer routes.
- Create `src/lehr_eval/routers/teacher.py`: teacher PIN and live-control routes.
- Create `src/lehr_eval/templates/*.html`: minimal German HTML pages.
- Create `src/lehr_eval/static/app.css`: restrained responsive layout.
- Create `src/lehr_eval/static/live.js`: EventSource client updates.
- Create `tests/`: focused tests for schema, import validation, animal codes, live state, cleanup, exports, and HTTP flows.
- Create `ops/Caddyfile.example`, `ops/lehr-eval.service`, `ops/backup-sqlite.sh`, `README.md`.

## Task 1: Project Skeleton And Test Harness

**Files:**
- Create: `pyproject.toml`
- Create: `src/lehr_eval/__init__.py`
- Create: `src/lehr_eval/app.py`
- Create: `tests/test_app_smoke.py`

- [x] **Step 1: Write the failing smoke test**

```python
# tests/test_app_smoke.py
from fastapi.testclient import TestClient

from lehr_eval.app import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app_smoke.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'lehr_eval'` or missing `create_app`.

- [x] **Step 3: Add minimal project files**

```toml
# pyproject.toml
[project]
name = "lehr-eval"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
  "jinja2>=3.1",
  "python-multipart>=0.0.9",
  "openpyxl>=3.1",
  "qrcode[pil]>=7.4",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "httpx>=0.27",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

```python
# src/lehr_eval/app.py
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Lehr-Evaluation")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app_smoke.py -v`

Expected: PASS.

## Task 2: SQLite Schema And WAL Initialization

**Files:**
- Create: `src/lehr_eval/settings.py`
- Create: `src/lehr_eval/db.py`
- Create: `src/lehr_eval/schema.sql`
- Create: `src/lehr_eval/migrations.py`
- Create: `tests/test_db.py`

- [x] **Step 1: Write failing database tests**

```python
# tests/test_db.py
from pathlib import Path

from lehr_eval.db import connect
from lehr_eval.migrations import initialize_database


def test_initialize_database_creates_core_tables(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        tables = {
            row["name"]
            for row in db.execute(
                "select name from sqlite_master where type = 'table'"
            )
        }

    assert {
        "teachers",
        "evaluations",
        "participants",
        "live_answers",
        "item_aggregates",
        "admin_log",
    }.issubset(tables)


def test_database_uses_wal_mode(tmp_path: Path):
    db_path = tmp_path / "eval.db"

    initialize_database(db_path)

    with connect(db_path) as db:
        mode = db.execute("pragma journal_mode").fetchone()[0]

    assert mode.lower() == "wal"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_db.py -v`

Expected: FAIL because `lehr_eval.db` and `initialize_database` do not exist.

- [x] **Step 3: Implement schema and initialization**

Create `schema.sql` with tables for teachers, evaluations, participants, live_answers, item_aggregates, and admin_log. Use explicit evaluation status values: `prepared`, `active`, `joining`, `reading`, `answering`, `paused`, `review_required`, `closed`, `deactivated`.

Implement `connect(db_path)` with `sqlite3.Row`, `pragma foreign_keys = on`, and short timeout. Implement `initialize_database(db_path)` to apply WAL mode and execute `schema.sql`.

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_db.py -v`

Expected: PASS.

## Task 3: Fixed Questionnaires And Animal Codes

**Files:**
- Create: `src/lehr_eval/questionnaires.py`
- Create: `src/lehr_eval/animal_codes.py`
- Create: `tests/test_questionnaires.py`
- Create: `tests/test_animal_codes.py`

- [x] **Step 1: Write failing tests for questionnaire selection**

```python
# tests/test_questionnaires.py
from lehr_eval.questionnaires import questionnaire_for_grade


def test_grades_one_to_six_use_lower_questionnaire():
    assert questionnaire_for_grade(1).kind == "unterstufe"
    assert questionnaire_for_grade(6).kind == "unterstufe"


def test_grades_seven_to_ten_use_upper_questionnaire():
    assert questionnaire_for_grade(7).kind == "oberstufe"
    assert questionnaire_for_grade(10).kind == "oberstufe"


def test_questionnaire_has_ten_items():
    assert len(questionnaire_for_grade(4).items) == 10
    assert len(questionnaire_for_grade(9).items) == 10
```

- [x] **Step 2: Write failing tests for animal codes**

```python
# tests/test_animal_codes.py
from lehr_eval.animal_codes import code_for_index


def test_first_forty_codes_are_plain_animals():
    codes = [code_for_index(i) for i in range(40)]

    assert len(set(codes)) == 40
    assert all(" " not in code for code in codes)


def test_codes_after_forty_use_positive_or_neutral_adjectives():
    code = code_for_index(40)

    assert " " in code
    assert not code.startswith("fauler ")
```

- [x] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_questionnaires.py tests/test_animal_codes.py -v`

Expected: FAIL because modules do not exist.

- [x] **Step 4: Implement fixed questionnaire and code lists**

Use placeholder-neutral item texts only if final school wording is not yet available, e.g. `Item 1` through `Item 10`, so behavior can be implemented without pretending final pedagogical wording exists. Use 40 German animal names and neutral/positive adjectives such as `blauer`, `grüner`, `kleiner`, `großer`, `schneller`, `leiser`, `bunter`.

- [x] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_questionnaires.py tests/test_animal_codes.py -v`

Expected: PASS.

## Task 4: Stammdatenimport Service

**Files:**
- Create: `src/lehr_eval/imports.py`
- Create: `tests/test_imports.py`

- [x] **Step 1: Write failing import validation tests**

```python
# tests/test_imports.py
from io import StringIO
from pathlib import Path

import pytest

from lehr_eval.imports import ImportErrorReport, import_master_data
from lehr_eval.migrations import initialize_database


VALID_CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def test_valid_import_creates_prepared_evaluation_and_teacher_pin(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)

    result = import_master_data(db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test")

    assert result.created_evaluations == 1
    assert len(result.qr_rows) == 1
    assert result.qr_rows[0].teacher_pin.isdigit()
    assert len(result.qr_rows[0].teacher_pin) == 4


def test_duplicate Unterrichtsgruppe_rejects_entire_import(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    import_master_data(db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test")

    with pytest.raises(ImportErrorReport) as error:
        import_master_data(db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test")

    assert "Doppelte Unterrichtsgruppe" in str(error.value)
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_imports.py -v`

Expected: FAIL because import service does not exist.

- [x] **Step 3: Implement atomic CSV import**

Implement required columns exactly: `schuljahr`, `klassenstufe`, `klasse_lerngruppe`, `fach`, `lehrkraft_name`, `lehrkraft_kennung`, `erwartete_teilnehmerzahl`. Validate all rows before inserting. Generate one yearly teacher PIN per `lehrkraft_kennung` and `schuljahr`. Create prepared evaluations with student and teacher tokens for QR URLs.

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_imports.py -v`

Expected: PASS.

## Task 5: Admin HTTP Flow

**Files:**
- Modify: `src/lehr_eval/app.py`
- Create: `src/lehr_eval/auth.py`
- Create: `src/lehr_eval/routers/admin.py`
- Create: `src/lehr_eval/templates/base.html`
- Create: `src/lehr_eval/templates/admin_login.html`
- Create: `src/lehr_eval/templates/admin_evaluations.html`
- Create: `tests/test_admin_http.py`

- [x] **Step 1: Write failing admin tests**

```python
# tests/test_admin_http.py
from pathlib import Path

from fastapi.testclient import TestClient

from lehr_eval.app import create_app
from lehr_eval.migrations import initialize_database


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

    response = client.post("/admin/login", data={"password": "secret"}, follow_redirects=False)

    assert response.status_code == 303
    assert "lehr_eval_admin" in response.headers["set-cookie"]
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_admin_http.py -v`

Expected: FAIL because admin routes do not exist.

- [x] **Step 3: Implement minimal admin session and pages**

Use signed cookie sessions via FastAPI `SessionMiddleware`. Store only admin session state in the cookie. Add `/admin/login`, `/admin/logout`, `/admin/evaluations`, and POST actions for activate, deactivate, delete unneeded unused evaluations.

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_admin_http.py -v`

Expected: PASS.

## Task 6: Student Join And Rejoin

**Files:**
- Create: `src/lehr_eval/routers/student.py`
- Create: `src/lehr_eval/templates/student_wait.html`
- Create: `src/lehr_eval/templates/student_answer.html`
- Create: `tests/test_student_flow.py`

- [x] **Step 1: Write failing student tests**

```python
# tests/test_student_flow.py
from io import StringIO
from pathlib import Path

from fastapi.testclient import TestClient

from lehr_eval.app import create_app
from lehr_eval.imports import import_master_data
from lehr_eval.migrations import initialize_database


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def setup_client(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    result = import_master_data(db_path, StringIO(CSV), base_url="https://eval.schule.test")
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))
    client.post(f"/admin/evaluations/{result.qr_rows[0].evaluation_id}/activate")
    return client, result.qr_rows[0]


def test_student_join_assigns_animal_code_cookie(tmp_path: Path):
    client, qr = setup_client(tmp_path)

    response = client.get(qr.student_path)

    assert response.status_code == 200
    assert "lehr_eval_participant" in response.headers["set-cookie"]
    assert "Dein Tiername" in response.text
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_student_flow.py -v`

Expected: FAIL because student routes do not exist.

- [x] **Step 3: Implement student join, cookie rejoin, and manual animal-code rejoin**

Allow new participants only while evaluation is active and in the join phase. Assign animal codes automatically. Store a participant cookie token for automatic rejoin. Add manual rejoin form by animal code for existing participants after device loss.

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_student_flow.py -v`

Expected: PASS.

## Task 7: Teacher PIN And Live State Machine

**Files:**
- Create: `src/lehr_eval/live.py`
- Create: `src/lehr_eval/routers/teacher.py`
- Create: `src/lehr_eval/templates/teacher_pin.html`
- Create: `src/lehr_eval/templates/teacher_live.html`
- Create: `tests/test_teacher_flow.py`
- Create: `tests/test_live_state.py`

- [x] **Step 1: Write failing live-state tests**

```python
# tests/test_live_state.py
from io import StringIO
from pathlib import Path

from lehr_eval.imports import import_master_data
from lehr_eval.live import open_answer_phase, show_first_item, start_joining
from lehr_eval.migrations import initialize_database


CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def test_teacher_advances_from_joining_to_reading_to_answering(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    result = import_master_data(db_path, StringIO(CSV), base_url="https://eval.schule.test")
    evaluation_id = result.qr_rows[0].evaluation_id

    start_joining(db_path, evaluation_id)
    state = show_first_item(db_path, evaluation_id)
    assert state.phase == "reading"
    assert state.current_item_index == 0

    state = open_answer_phase(db_path, evaluation_id)
    assert state.phase == "answering"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_live_state.py -v`

Expected: FAIL because `live.py` does not exist.

- [x] **Step 3: Implement live state machine**

Implement transitions: prepared -> active -> joining -> reading -> answering -> reading next item -> closed. Permit pause/resume. Permit teacher to proceed despite missing joins or missing answers. Reject new student joins after first item starts.

- [x] **Step 4: Add teacher HTTP tests for QR plus PIN**

```python
# tests/test_teacher_flow.py
def test_teacher_qr_requires_pin(tmp_path):
    client, qr = setup_client(tmp_path)

    response = client.get(qr.teacher_path)

    assert response.status_code == 200
    assert "PIN" in response.text
```

- [x] **Step 5: Implement teacher routes**

Add teacher PIN form, session cookie for the specific evaluation, live dashboard, and POST actions: start, show answers, next item, close evaluation, pause.

- [x] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_live_state.py tests/test_teacher_flow.py -v`

Expected: PASS.

## Task 8: Answer Changes, Aggregate Finalization, And Live Data Cleanup

**Files:**
- Modify: `src/lehr_eval/live.py`
- Modify: `src/lehr_eval/routers/student.py`
- Create: `tests/test_answers_and_aggregates.py`

- [x] **Step 1: Write failing aggregate tests**

```python
# tests/test_answers_and_aggregates.py
def test_only_latest_answer_counts_when_item_is_finalized(tmp_path):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)

    submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=0)
    submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=3)
    finalize_current_item(db_path, evaluation_id)

    aggregate = get_item_aggregate(db_path, evaluation_id, item_index=0)

    assert aggregate.count_0 == 0
    assert aggregate.count_3 == 1
    assert aggregate.mean == 3.0


def test_closing_evaluation_deletes_live_answers_and_participants(tmp_path):
    db_path, evaluation_id, participant_id = prepared_answering_evaluation(tmp_path)

    submit_answer(db_path, evaluation_id, participant_id, item_index=0, value=2)
    finalize_current_item(db_path, evaluation_id)
    close_evaluation(db_path, evaluation_id)

    assert count_live_answers(db_path, evaluation_id) == 0
    assert count_participants(db_path, evaluation_id) == 0
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_answers_and_aggregates.py -v`

Expected: FAIL because aggregate functions are not implemented.

- [x] **Step 3: Implement answer replacement and aggregate finalization**

Use one live answer row per participant/evaluation/item. On answer change, update the row. On item finalization, count values 0-3, count missing answers from joined participants without a current answer, store one immutable item_aggregate row, then remove live answers for that item.

- [x] **Step 4: Implement close cleanup**

On close, finalize any open answer item if needed, delete participants and remaining live answers, mark evaluation closed, and leave item aggregates plus metadata.

- [x] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_answers_and_aggregates.py -v`

Expected: PASS.

## Task 9: Server-Sent Events Live Updates

**Files:**
- Create: `src/lehr_eval/events.py`
- Modify: `src/lehr_eval/routers/student.py`
- Modify: `src/lehr_eval/routers/teacher.py`
- Create: `src/lehr_eval/static/live.js`
- Create: `tests/test_events.py`

- [x] **Step 1: Write failing event broadcaster test**

```python
# tests/test_events.py
import pytest

from lehr_eval.events import EventHub


@pytest.mark.anyio
async def test_event_hub_delivers_evaluation_event():
    hub = EventHub()
    subscription = hub.subscribe(evaluation_id=42)

    await hub.publish(evaluation_id=42, event={"phase": "answering", "item": 0})

    assert await subscription.__anext__() == {"phase": "answering", "item": 0}
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_events.py -v`

Expected: FAIL because `EventHub` does not exist.

- [x] **Step 3: Implement EventHub and SSE endpoint**

Implement in-process async queues keyed by evaluation ID. Add `/events/{evaluation_token}` route returning `text/event-stream`. Publish after every teacher transition and student answer/rejoin.

- [x] **Step 4: Add browser update script**

Use `EventSource` in `live.js` to reload or patch the current page when evaluation phase changes. Keep the first version simple: reload on phase/item change.

- [x] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_events.py -v`

Expected: PASS.

## Task 10: Excel Exports

**Files:**
- Create: `src/lehr_eval/exports.py`
- Modify: `src/lehr_eval/routers/admin.py`
- Create: `tests/test_exports.py`

- [x] **Step 1: Write failing XLSX export tests**

```python
# tests/test_exports.py
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from lehr_eval.exports import build_single_export


def test_single_export_contains_header_and_item_aggregates(tmp_path: Path):
    db_path, evaluation_id = closed_evaluation_with_aggregates(tmp_path)

    content = build_single_export(db_path, evaluation_id)
    workbook = load_workbook(BytesIO(content))
    sheet = workbook.active

    assert sheet["A1"].value == "Schuljahr"
    assert sheet["B1"].value == "2025/26"
    assert "Auswertung enthaelt nur aggregierte Daten" in sheet["A9"].value
    assert sheet["A12"].value == "Item"
    assert sheet["B12"].value == "0"
    assert sheet["F12"].value == "Fehlend"
    assert sheet["H12"].value == "Mittelwert"
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_exports.py -v`

Expected: FAIL because export service does not exist.

- [x] **Step 3: Implement single and teacher export**

Generate simple XLSX files without charts. Single export has one sheet. Teacher export has one sheet per evaluation using `klasse_lerngruppe + fach`, with numeric suffixes for collisions and Excel-compatible length.

- [x] **Step 4: Add admin download endpoints**

Add `/admin/evaluations/{id}/export.xlsx` and `/admin/teachers/{teacher_id}/{school_year}/export.xlsx`.

- [x] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_exports.py -v`

Expected: PASS.

## Task 11: QR Material Export

**Files:**
- Modify: `src/lehr_eval/exports.py`
- Modify: `src/lehr_eval/routers/admin.py`
- Create: `tests/test_qr_material.py`

- [x] **Step 1: Write failing QR material test**

```python
# tests/test_qr_material.py
from zipfile import ZipFile
from io import BytesIO

from lehr_eval.exports import build_qr_material_zip


def test_qr_material_zip_contains_printable_html_and_pngs(tmp_path):
    db_path, evaluation_id = prepared_evaluation(tmp_path)

    content = build_qr_material_zip(db_path, [evaluation_id])

    with ZipFile(BytesIO(content)) as archive:
        names = set(archive.namelist())

    assert "qr-material.html" in names
    assert any(name.endswith("-schueler.png") for name in names)
    assert any(name.endswith("-lehrkraft.png") for name in names)
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_qr_material.py -v`

Expected: FAIL because QR material export does not exist.

- [x] **Step 3: Implement printable QR material ZIP**

Generate QR PNGs for student and teacher URLs and a printable HTML index with school year, class/group, subject, teacher name, and teacher PIN. Do not include teacher email.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_qr_material.py -v`

Expected: PASS.

## Task 12: Operations Package

**Files:**
- Create: `README.md`
- Create: `ops/Caddyfile.example`
- Create: `ops/lehr-eval.service`
- Create: `ops/backup-sqlite.sh`
- Create: `tests/test_ops_files.py`

- [x] **Step 1: Write failing ops file tests**

```python
# tests/test_ops_files.py
from pathlib import Path


def test_ops_files_document_dns_https_and_backups():
    readme = Path("README.md").read_text()
    caddy = Path("ops/Caddyfile.example").read_text()
    backup = Path("ops/backup-sqlite.sh").read_text()

    assert "DNS" in readme
    assert "SQLite" in readme
    assert "reverse_proxy" in caddy
    assert "sqlite" in backup.lower()
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ops_files.py -v`

Expected: FAIL because ops files do not exist.

- [x] **Step 3: Add operations files**

Document:
- QR URLs should use DNS, not IP addresses.
- Caddy terminates HTTPS and proxies to `127.0.0.1:8000`.
- App runs as an unprivileged `lehr-eval` user.
- Database lives under `/var/lib/lehr-eval/eval.db`.
- Backups run daily and copy a consistent SQLite backup to separate school storage.
- Restore tests must be performed regularly.

- [x] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_ops_files.py -v`

Expected: PASS.

## Task 13: End-To-End Smoke Test And Local Run

**Files:**
- Create: `tests/test_e2e_scope.py`
- Modify: `README.md`

- [x] **Step 1: Write failing end-to-end scope test**

```python
# tests/test_e2e_scope.py
def test_import_activate_join_answer_close_export_flow(tmp_path):
    db_path = tmp_path / "eval.db"
    client, qr = create_imported_and_activated_client(db_path)

    student = client.get(qr.student_path)
    assert "Dein Tiername" in student.text

    teacher = client.post(qr.teacher_path, data={"pin": qr.teacher_pin})
    assert teacher.status_code == 200

    client.post(f"/teacher/{qr.evaluation_id}/start")
    client.post(f"/teacher/{qr.evaluation_id}/item/answers")
    client.post(f"/student/{qr.evaluation_id}/answer", data={"value": "3"})
    client.post(f"/teacher/{qr.evaluation_id}/item/finish")

    client.post(f"/teacher/{qr.evaluation_id}/close")
    export = client.get(f"/admin/evaluations/{qr.evaluation_id}/export.xlsx")

    assert export.status_code == 200
    assert export.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_e2e_scope.py -v`

Expected: FAIL until helper functions and all routes are complete.

- [x] **Step 3: Fill gaps only needed by the smoke flow**

Implement missing helper behavior exposed by the test. Do not add dashboards, charts, teacher result portals, student identity, or answer profiles.

- [x] **Step 4: Run full test suite**

Run: `uv run pytest -v`

Expected: PASS.

- [x] **Step 5: Start local development server**

Run: `uv run uvicorn lehr_eval.app:create_app --factory --reload --host 127.0.0.1 --port 8000`

Expected: app serves at `http://127.0.0.1:8000`.

## Scope Guardrails

- Do not add graphing, dashboards, PDF reports, or teacher result login.
- Do not store answer histories.
- Do not keep participant/tiername/live-answer data after closing an evaluation.
- Do not use DuckDB as the primary application database.
- Do not put teacher email addresses in QR material or exports.
- Do not make QR URLs IP-based in production docs; use DNS names.
- Do not implement final school questionnaire wording until provided; keep questionnaire data isolated.

## Self-Review

Spec coverage:
- Stammdatenimport, prepared/activated evaluation lifecycle, teacher PIN, student QR, animal-code rejoin, live phases, mutable answers during answer phase, item aggregates, close cleanup, Excel exports, QR material, and on-prem operations are covered.

Placeholder scan:
- No `TBD`, `TODO`, or "implement later" placeholders are used. Final questionnaire wording is explicitly isolated as data because the wording has not been supplied.

Type consistency:
- The plan consistently uses `evaluation_id`, `teacher_pin`, `student_path`, `teacher_path`, `item_index`, `Item-Aggregate`, and status strings defined in Task 2 and reused through later tasks.
