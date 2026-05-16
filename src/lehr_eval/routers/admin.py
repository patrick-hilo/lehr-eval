from io import StringIO
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from lehr_eval.auth import (
    admin_is_authenticated,
    clear_admin_authentication,
    mark_admin_authenticated,
    password_matches,
)
from lehr_eval.db import connect
from lehr_eval.exports import (
    ExportNotAvailable,
    ExportNotFound,
    build_qr_material_zip,
    build_single_export,
    build_teacher_export,
    safe_download_filename,
)
from lehr_eval.imports import (
    ImportErrorReport,
    import_master_data,
    import_master_data_from_xlsx,
)
from lehr_eval.settings import load_settings


templates = Jinja2Templates(directory=Path(__file__).parents[1] / "templates")

STATUS_FILTERS = (
    "prepared",
    "active",
    "joining",
    "reading",
    "answering",
    "paused",
    "closed",
    "deactivated",
)


def create_admin_router(db_path: Path, admin_password: str) -> APIRouter:
    router = APIRouter(prefix="/admin")

    @router.get("/login", response_class=HTMLResponse)
    def login_form(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "admin_login.html", {"error": None}, status_code=200
        )

    @router.post("/login", response_class=HTMLResponse)
    def login(request: Request, password: str = Form(...)) -> HTMLResponse:
        if not password_matches(password, admin_password):
            return templates.TemplateResponse(
                request,
                "admin_login.html",
                {"error": "Falsches Passwort."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        mark_admin_authenticated(request)
        return RedirectResponse(
            "/admin/evaluations", status_code=status.HTTP_303_SEE_OTHER
        )

    @router.post("/logout")
    def logout(request: Request) -> RedirectResponse:
        clear_admin_authentication(request)
        return RedirectResponse("/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    @router.get("/evaluations", response_class=HTMLResponse)
    def evaluations(
        request: Request, status_filter: str | None = Query(None, alias="status")
    ) -> HTMLResponse:
        require_admin(request)
        active_filter = status_filter if status_filter in STATUS_FILTERS else None
        params: tuple = ()
        where = ""
        if active_filter:
            where = "where evaluations.status = ?"
            params = (active_filter,)
        with connect(db_path) as db:
            rows = db.execute(
                f"""
                select
                    evaluations.id,
                    evaluations.title,
                    evaluations.school_year,
                    evaluations.class_group,
                    evaluations.subject,
                    evaluations.status,
                    teachers.name as teacher_name
                from evaluations
                join teachers on teachers.id = evaluations.teacher_id
                {where}
                order by evaluations.school_year desc, evaluations.id desc
                """,
                params,
            ).fetchall()

            status_counts_rows = db.execute(
                """
                select status, count(*) as n
                from evaluations
                group by status
                """
            ).fetchall()
        status_counts = {row["status"]: int(row["n"]) for row in status_counts_rows}
        total = sum(status_counts.values())

        return templates.TemplateResponse(
            request,
            "admin_evaluations.html",
            {
                "evaluations": rows,
                "active_filter": active_filter,
                "status_counts": status_counts,
                "total_count": total,
                "filter_options": STATUS_FILTERS,
            },
        )

    @router.post("/evaluations/bulk")
    def bulk_action(
        request: Request,
        action: str = Form(...),
        evaluation_ids: list[int] = Form(default=[]),
        status_filter: str | None = Form(default=None, alias="status"),
    ) -> RedirectResponse:
        require_admin(request)
        if action not in {"activate", "deactivate", "delete"}:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="unknown action")
        if not evaluation_ids:
            return _redirect_to_evaluations(status_filter)

        with connect(db_path) as db:
            for evaluation_id in evaluation_ids:
                row = db.execute(
                    "select status from evaluations where id = ?", (evaluation_id,)
                ).fetchone()
                if row is None:
                    continue
                current = row["status"]
                if action == "activate" and current == "prepared":
                    db.execute(
                        "update evaluations set status='active', updated_at=current_timestamp where id=?",
                        (evaluation_id,),
                    )
                    insert_admin_log(db, "activate", evaluation_id)
                elif action == "deactivate" and current == "active" and not evaluation_is_used(db, evaluation_id):
                    db.execute(
                        "update evaluations set status='deactivated', updated_at=current_timestamp where id=?",
                        (evaluation_id,),
                    )
                    insert_admin_log(db, "deactivate", evaluation_id)
                elif action == "delete" and not evaluation_is_used(db, evaluation_id):
                    insert_admin_log(db, "delete", evaluation_id)
                    db.execute("delete from evaluations where id = ?", (evaluation_id,))

        return _redirect_to_evaluations(status_filter)

    def _redirect_to_evaluations(status_filter: str | None) -> RedirectResponse:
        target = "/admin/evaluations"
        if status_filter in STATUS_FILTERS:
            target += f"?status={status_filter}"
        return RedirectResponse(target, status_code=status.HTTP_303_SEE_OTHER)

    @router.post("/import")
    def import_csv(request: Request, csv_file: UploadFile = File(...)) -> Response:
        require_admin(request)
        content = csv_file.file.read()
        filename = (csv_file.filename or "").lower()
        is_xlsx = filename.endswith(".xlsx") or (
            csv_file.content_type or ""
        ).endswith("spreadsheetml.sheet")
        try:
            if is_xlsx:
                from io import BytesIO

                import_master_data_from_xlsx(
                    db_path,
                    BytesIO(content),
                    base_url=load_settings().base_url,
                )
            else:
                text = content.decode("utf-8-sig")
                import_master_data(
                    db_path,
                    StringIO(text),
                    base_url=load_settings().base_url,
                )
        except UnicodeDecodeError as error:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="CSV-Datei muss UTF-8 sein"
            ) from error
        except ImportErrorReport as error:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="\n".join(error.errors)
            ) from error

        return RedirectResponse(
            "/admin/evaluations", status_code=status.HTTP_303_SEE_OTHER
        )

    @router.get("/evaluations/{evaluation_id}/export.xlsx")
    def export_evaluation(request: Request, evaluation_id: int) -> Response:
        require_admin(request)
        try:
            content = build_single_export(db_path, evaluation_id)
        except ExportNotFound:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        except ExportNotAvailable:
            raise HTTPException(status.HTTP_409_CONFLICT)
        return xlsx_response(content, f"evaluation-{evaluation_id}.xlsx")

    @router.get("/teachers/{teacher_id}/{school_year:path}/export.xlsx")
    def export_teacher(
        request: Request, teacher_id: int, school_year: str
    ) -> Response:
        require_admin(request)
        try:
            content = build_teacher_export(db_path, teacher_id, school_year)
        except ExportNotFound:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        filename_year = safe_download_filename(school_year)
        return xlsx_response(
            content, f"teacher-{teacher_id}-{filename_year}.xlsx"
        )

    @router.get("/evaluations/qr-material.zip")
    def export_qr_material(
        request: Request, evaluation_id: list[int] = Query(...)
    ) -> Response:
        require_admin(request)
        try:
            content = build_qr_material_zip(db_path, evaluation_id)
        except ExportNotFound:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        except ExportNotAvailable:
            raise HTTPException(status.HTTP_409_CONFLICT)
        return zip_response(content, "qr-material.zip")

    @router.get("/evaluations/{evaluation_id}/qr-material.zip")
    def export_qr_material_single(
        request: Request, evaluation_id: int
    ) -> Response:
        require_admin(request)
        try:
            content = build_qr_material_zip(db_path, [evaluation_id])
        except ExportNotFound:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        except ExportNotAvailable:
            raise HTTPException(status.HTTP_409_CONFLICT)
        return zip_response(content, f"qr-material-{evaluation_id}.zip")

    @router.post("/evaluations/{evaluation_id}/activate")
    def activate_evaluation(request: Request, evaluation_id: int) -> RedirectResponse:
        require_admin(request)
        with connect(db_path) as db:
            row = db.execute(
                "select status from evaluations where id = ?", (evaluation_id,)
            ).fetchone()
            if row is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND)
            if row["status"] != "prepared":
                raise HTTPException(status.HTTP_409_CONFLICT)

            db.execute(
                """
                update evaluations
                set status = 'active', updated_at = current_timestamp
                where id = ?
                """,
                (evaluation_id,),
            )
            insert_admin_log(db, "activate", evaluation_id)

        return RedirectResponse(
            "/admin/evaluations", status_code=status.HTTP_303_SEE_OTHER
        )

    @router.post("/evaluations/{evaluation_id}/deactivate")
    def deactivate_evaluation(request: Request, evaluation_id: int) -> RedirectResponse:
        require_admin(request)
        with connect(db_path) as db:
            row = db.execute(
                "select status from evaluations where id = ?", (evaluation_id,)
            ).fetchone()
            if row is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND)
            if row["status"] != "active" or evaluation_is_used(db, evaluation_id):
                raise HTTPException(status.HTTP_409_CONFLICT)

            db.execute(
                """
                update evaluations
                set status = 'deactivated', updated_at = current_timestamp
                where id = ?
                """,
                (evaluation_id,),
            )
            insert_admin_log(db, "deactivate", evaluation_id)

        return RedirectResponse(
            "/admin/evaluations", status_code=status.HTTP_303_SEE_OTHER
        )

    @router.post("/evaluations/{evaluation_id}/delete")
    def delete_evaluation(request: Request, evaluation_id: int) -> RedirectResponse:
        require_admin(request)
        with connect(db_path) as db:
            row = db.execute(
                "select id from evaluations where id = ?", (evaluation_id,)
            ).fetchone()
            if row is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND)
            if evaluation_is_used(db, evaluation_id):
                raise HTTPException(status.HTTP_409_CONFLICT)

            insert_admin_log(db, "delete", evaluation_id)
            db.execute("delete from evaluations where id = ?", (evaluation_id,))

        return RedirectResponse(
            "/admin/evaluations", status_code=status.HTTP_303_SEE_OTHER
        )

    return router


def require_admin(request: Request) -> None:
    if not admin_is_authenticated(request):
        raise_redirect = RedirectResponse(
            "/admin/login", status_code=status.HTTP_303_SEE_OTHER
        )
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"location": raise_redirect.headers["location"]},
        )


def evaluation_is_used(db, evaluation_id: int) -> bool:
    for table in ("participants", "live_answers", "item_aggregates"):
        if db.execute(
            f"select 1 from {table} where evaluation_id = ? limit 1",
            (evaluation_id,),
        ).fetchone():
            return True
    return False


def insert_admin_log(db, action: str, evaluation_id: int) -> None:
    db.execute(
        """
        insert into admin_log (actor, action, evaluation_id, target_evaluation_id)
        values ('admin', ?, ?, ?)
        """,
        (action, evaluation_id, evaluation_id),
    )


def xlsx_response(content: bytes, filename: str) -> Response:
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )


def zip_response(content: bytes, filename: str) -> Response:
    return Response(
        content,
        media_type="application/zip",
        headers={"content-disposition": f'attachment; filename="{filename}"'},
    )
