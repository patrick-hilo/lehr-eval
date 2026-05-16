from io import BytesIO
from pathlib import Path
import sqlite3
from zipfile import ZipFile

from fastapi.testclient import TestClient

from lehr_eval.app import create_app
from lehr_eval.db import connect
from lehr_eval.exports import ExportNotAvailable, build_qr_material_zip
from lehr_eval.migrations import initialize_database


def test_qr_material_zip_contains_printable_html_and_pngs(tmp_path: Path):
    db_path, evaluation_id = prepared_evaluation(tmp_path)

    content = build_qr_material_zip(db_path, [evaluation_id])

    with ZipFile(BytesIO(content)) as archive:
        names = set(archive.namelist())
        html = archive.read("qr-material.html").decode("utf-8")
        student_png = archive.read(f"evaluation-{evaluation_id}-schueler.png")
        teacher_png = archive.read(f"evaluation-{evaluation_id}-lehrkraft.png")

    assert "qr-material.html" in names
    assert f"evaluation-{evaluation_id}-schueler.png" in names
    assert f"evaluation-{evaluation_id}-lehrkraft.png" in names
    assert student_png.startswith(b"\x89PNG\r\n\x1a\n")
    assert teacher_png.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(student_png) > 100
    assert len(teacher_png) > 100
    assert "https://eval.schule.test/e/student-token-1" in html
    assert "https://eval.schule.test/t/teacher-token-1" in html


def test_qr_material_html_includes_print_metadata_and_omits_teacher_email(
    tmp_path: Path,
):
    db_path, evaluation_id = prepared_evaluation(tmp_path)

    content = build_qr_material_zip(db_path, [evaluation_id])

    with ZipFile(BytesIO(content)) as archive:
        html = archive.read("qr-material.html").decode("utf-8")
        all_content = b"\n".join(archive.read(name) for name in archive.namelist())

    assert "2025/26" in html
    assert "8b" in html
    assert "Mathematik" in html
    assert "Frau Mueller" in html
    assert "4321" in html
    assert "mueller@example.test" not in html
    assert b"mueller@example.test" not in all_content


def test_admin_qr_material_endpoint_requires_login_and_returns_zip(tmp_path: Path):
    db_path, evaluation_id = prepared_evaluation(tmp_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    unauthenticated = client.get(
        f"/admin/evaluations/qr-material.zip?evaluation_id={evaluation_id}",
        follow_redirects=False,
    )
    assert unauthenticated.status_code == 303
    assert unauthenticated.headers["location"] == "/admin/login"

    login(client)
    response = client.get(
        f"/admin/evaluations/qr-material.zip?evaluation_id={evaluation_id}"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["content-disposition"] == (
        'attachment; filename="qr-material.zip"'
    )
    with ZipFile(BytesIO(response.content)) as archive:
        assert "qr-material.html" in archive.namelist()


def test_qr_material_rejects_existing_hash_only_pin(tmp_path: Path):
    db_path, evaluation_id = legacy_hash_only_pin_evaluation(tmp_path)

    try:
        build_qr_material_zip(db_path, [evaluation_id])
    except ExportNotAvailable:
        pass
    else:
        raise AssertionError("expected QR export to require printable teacher PIN")


def test_admin_qr_material_endpoint_returns_409_for_hash_only_pin(tmp_path: Path):
    db_path, evaluation_id = legacy_hash_only_pin_evaluation(tmp_path)
    client = TestClient(create_app(db_path=db_path, admin_password="secret"))

    login(client)
    response = client.get(
        f"/admin/evaluations/qr-material.zip?evaluation_id={evaluation_id}"
    )

    assert response.status_code == 409


def legacy_hash_only_pin_evaluation(tmp_path: Path) -> tuple[Path, int]:
    db_path = tmp_path / "legacy-eval.db"
    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            create table teachers (
                id integer primary key,
                name text not null,
                email text,
                created_at text not null default current_timestamp,
                unique (email)
            );
            create table teacher_pins (
                id integer primary key,
                teacher_id integer not null references teachers(id) on delete cascade,
                school_year text not null,
                pin_hash text not null,
                created_at text not null default current_timestamp,
                unique (teacher_id, school_year)
            );
            create table evaluations (
                id integer primary key,
                teacher_id integer not null references teachers(id) on delete restrict,
                title text not null,
                school_year text not null,
                grade integer not null check (grade between 1 and 10),
                class_group text not null,
                subject text not null,
                questionnaire_version text not null,
                expected_participants integer not null check (expected_participants >= 0),
                status text not null default 'prepared',
                current_item_index integer,
                previous_status text,
                student_token text not null,
                teacher_token text not null,
                created_at text not null default current_timestamp,
                updated_at text not null default current_timestamp,
                unique (student_token),
                unique (teacher_token),
                unique (school_year, class_group, subject, teacher_id)
            );
            insert into teachers (id, name, email)
            values (1, 'Frau Mueller', 'mueller@example.test');
            insert into teacher_pins (teacher_id, school_year, pin_hash)
            values (1, '2025/26', 'hash-only-in-this-test');
            insert into evaluations (
                id,
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
                1,
                '8b Mathematik',
                '2025/26',
                8,
                '8b',
                'Mathematik',
                'oberstufe-v1',
                24,
                'prepared',
                'student-token-1',
                'teacher-token-1'
            );
            """
        )

    initialize_database(db_path)
    with connect(db_path) as db:
        db.execute(
            "update evaluations set base_url = 'https://eval.schule.test' where id = 1"
        )
    return db_path, 1


def prepared_evaluation(tmp_path: Path) -> tuple[Path, int]:
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    with connect(db_path) as db:
        db.execute(
            """
            insert into teachers (id, name, email)
            values (1, 'Frau Mueller', 'mueller@example.test')
            """
        )
        db.execute(
            """
            insert into teacher_pins (teacher_id, school_year, pin_code, pin_hash)
            values (1, '2025/26', '4321', 'hash-only-in-this-test')
            """
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
                teacher_token,
                base_url
            ) values (
                1,
                '8b Mathematik',
                '2025/26',
                8,
                '8b',
                'Mathematik',
                'oberstufe-v1',
                24,
                'prepared',
                'student-token-1',
                'teacher-token-1',
                'https://eval.schule.test'
            )
            """
        )
        return db_path, int(cursor.lastrowid)


def login(client: TestClient) -> None:
    response = client.post(
        "/admin/login", data={"password": "secret"}, follow_redirects=False
    )
    assert response.status_code == 303
