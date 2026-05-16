from io import BytesIO, StringIO
from pathlib import Path

import pytest
from openpyxl import Workbook

from lehr_eval.db import connect
from lehr_eval import imports
from lehr_eval.imports import (
    ImportErrorReport,
    import_master_data,
    import_master_data_from_xlsx,
)
from lehr_eval.migrations import initialize_database


VALID_CSV = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
"""


def test_valid_import_creates_prepared_evaluation_and_teacher_pin(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)

    result = import_master_data(
        db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test"
    )

    assert result.created_evaluations == 1
    assert len(result.qr_rows) == 1
    assert result.qr_rows[0].teacher_pin.isdigit()
    assert len(result.qr_rows[0].teacher_pin) == 4

    with connect(db_path) as db:
        evaluation = db.execute(
            """
            select
                evaluations.status,
                evaluations.school_year,
                evaluations.grade,
                evaluations.class_group,
                evaluations.subject,
                evaluations.questionnaire_version,
                evaluations.expected_participants,
                evaluations.base_url,
                teachers.name,
                teachers.email
            from evaluations
            join teachers on teachers.id = evaluations.teacher_id
            """
        ).fetchone()

    assert dict(evaluation) == {
        "status": "prepared",
        "school_year": "2025/26",
        "grade": 8,
        "class_group": "8b",
        "subject": "Mathematik",
        "questionnaire_version": "oberstufe-v1",
        "expected_participants": 24,
        "base_url": "https://eval.schule.test",
        "name": "Frau Mueller",
        "email": "mueller@example.edu",
    }
    with connect(db_path) as db:
        pin = db.execute("select pin_code, pin_hash from teacher_pins").fetchone()
    assert pin["pin_code"] == result.qr_rows[0].teacher_pin
    assert pin["pin_hash"] != pin["pin_code"]


def test_duplicate_unterrichtsgruppe_rejects_entire_import(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    import_master_data(db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test")

    with pytest.raises(ImportErrorReport) as error:
        import_master_data(db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test")

    assert "Doppelte Unterrichtsgruppe" in str(error.value)


def test_invalid_row_rejects_entire_import_atomically(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    csv_data = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
2025/26,11,11a,Deutsch,Herr Schmidt,schmidt@example.edu,18
"""

    with pytest.raises(ImportErrorReport) as error:
        import_master_data(db_path, StringIO(csv_data), base_url="https://eval.schule.test")

    assert "Klassenstufe" in str(error.value)
    with connect(db_path) as db:
        assert db.execute("select count(*) from teachers").fetchone()[0] == 0
        assert db.execute("select count(*) from teacher_pins").fetchone()[0] == 0
        assert db.execute("select count(*) from evaluations").fetchone()[0] == 0


def test_missing_required_column_is_import_error(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    csv_data = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,24
"""

    with pytest.raises(ImportErrorReport) as error:
        import_master_data(db_path, StringIO(csv_data), base_url="https://eval.schule.test")

    assert "lehrkraft_kennung" in str(error.value)


def test_same_teacher_and_year_reuses_one_pin_for_multiple_rows(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    csv_data = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
2025/26,8,8b,Deutsch,Frau Mueller,mueller@example.edu,24
"""

    result = import_master_data(
        db_path, StringIO(csv_data), base_url="https://eval.schule.test/"
    )

    assert result.created_evaluations == 2
    assert {row.teacher_pin for row in result.qr_rows} == {result.qr_rows[0].teacher_pin}
    with connect(db_path) as db:
        assert db.execute("select count(*) from teacher_pins").fetchone()[0] == 1


def test_same_teacher_and_year_generates_one_random_pin_for_current_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    generated_numbers = iter([1234, 9876])
    calls = 0

    def fake_randbelow(limit: int) -> int:
        nonlocal calls
        calls += 1
        assert limit == 10000
        return next(generated_numbers)

    monkeypatch.setattr(imports.secrets, "randbelow", fake_randbelow)
    csv_data = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Mathematik,Frau Mueller,mueller@example.edu,24
2025/26,8,8b,Deutsch,Frau Mueller,mueller@example.edu,24
"""

    result = import_master_data(
        db_path, StringIO(csv_data), base_url="https://eval.schule.test"
    )

    assert calls == 1
    assert [row.teacher_pin for row in result.qr_rows] == ["1234", "1234"]


def test_existing_teacher_year_pin_is_not_regenerated_or_returned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    generated_numbers = iter([1234])
    calls = 0

    def fake_randbelow(limit: int) -> int:
        nonlocal calls
        calls += 1
        assert limit == 10000
        return next(generated_numbers)

    monkeypatch.setattr(imports.secrets, "randbelow", fake_randbelow)
    import_master_data(db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test")

    second_csv = """schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,8,8b,Deutsch,Frau Mueller,mueller@example.edu,24
"""
    result = import_master_data(
        db_path, StringIO(second_csv), base_url="https://eval.schule.test"
    )

    assert calls == 1
    assert result.qr_rows[0].teacher_pin is None
    with connect(db_path) as db:
        assert db.execute("select count(*) from teacher_pins").fetchone()[0] == 1


def test_hash_pin_uses_salted_pbkdf2_material():
    first = imports._hash_pin("1234")
    second = imports._hash_pin("1234")

    first_parts = first.split("$")
    second_parts = second.split("$")
    assert first_parts[0] == "pbkdf2_sha256"
    assert int(first_parts[1]) >= 200_000
    assert len(first_parts[2]) >= 32
    assert len(first_parts[3]) == 64
    assert first != second
    assert second_parts[0] == "pbkdf2_sha256"


def test_qr_rows_do_not_expose_teacher_identifier(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)

    result = import_master_data(
        db_path, StringIO(VALID_CSV), base_url="https://eval.schule.test"
    )

    qr_row = result.qr_rows[0]
    assert qr_row.teacher_name == "Frau Mueller"
    assert "mueller@example.edu" not in qr_row.student_path
    assert "mueller@example.edu" not in qr_row.teacher_path
    assert "mueller@example.edu" not in qr_row.student_url
    assert "mueller@example.edu" not in qr_row.teacher_url


@pytest.mark.parametrize(
    ("grade", "expected_participants", "message"),
    [
        ("0", "24", "Klassenstufe"),
        ("11", "24", "Klassenstufe"),
        ("8", "-1", "erwartete_teilnehmerzahl"),
    ],
)
def test_rejects_invalid_grade_and_expected_participants(
    tmp_path: Path, grade: str, expected_participants: str, message: str
):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)
    csv_data = f"""schuljahr,klassenstufe,klasse_lerngruppe,fach,lehrkraft_name,lehrkraft_kennung,erwartete_teilnehmerzahl
2025/26,{grade},8b,Mathematik,Frau Mueller,mueller@example.edu,{expected_participants}
"""

    with pytest.raises(ImportErrorReport) as error:
        import_master_data(db_path, StringIO(csv_data), base_url="https://eval.schule.test")

    assert message in str(error.value)


def _build_xlsx(rows: list[list[str]]) -> BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def test_xlsx_import_creates_prepared_evaluation(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)

    xlsx = _build_xlsx(
        [
            [
                "schuljahr",
                "klassenstufe",
                "klasse_lerngruppe",
                "fach",
                "lehrkraft_name",
                "lehrkraft_kennung",
                "erwartete_teilnehmerzahl",
            ],
            ["2025/26", 8, "8b", "Mathematik", "Frau Mueller", "mueller@example.edu", 24],
        ]
    )

    result = import_master_data_from_xlsx(
        db_path, xlsx, base_url="https://eval.schule.test"
    )

    assert result.created_evaluations == 1
    assert result.qr_rows[0].teacher_pin.isdigit()


def test_xlsx_import_skips_blank_rows(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)

    xlsx = _build_xlsx(
        [
            [
                "schuljahr",
                "klassenstufe",
                "klasse_lerngruppe",
                "fach",
                "lehrkraft_name",
                "lehrkraft_kennung",
                "erwartete_teilnehmerzahl",
            ],
            ["2025/26", 8, "8b", "Mathematik", "Frau Mueller", "mueller@example.edu", 24],
            [None, None, None, None, None, None, None],
        ]
    )

    result = import_master_data_from_xlsx(
        db_path, xlsx, base_url="https://eval.schule.test"
    )

    assert result.created_evaluations == 1


def test_xlsx_import_reports_missing_columns(tmp_path: Path):
    db_path = tmp_path / "eval.db"
    initialize_database(db_path)

    xlsx = _build_xlsx(
        [
            ["schuljahr", "klassenstufe", "fach"],
            ["2025/26", 8, "Mathematik"],
        ]
    )

    with pytest.raises(ImportErrorReport) as error:
        import_master_data_from_xlsx(
            db_path, xlsx, base_url="https://eval.schule.test"
        )

    assert "Spalten" in str(error.value)
