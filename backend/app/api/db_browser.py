"""Browser UI routes for exploring and editing database tables."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.db_browser import (
    delete_row,
    get_row,
    get_table_rows,
    list_tables_with_counts,
    update_row,
)

router = APIRouter(tags=["db-browser"])

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/db", response_class=HTMLResponse)
def db_home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """List all browsable tables with row counts."""
    tables = list_tables_with_counts(db)
    return templates.TemplateResponse(
        request,
        "db/index.html",
        {"tables": tables},
    )


@router.get("/db/{table_name}", response_class=HTMLResponse)
def db_table(
    request: Request,
    table_name: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str = Query("", alias="q"),
) -> HTMLResponse:
    """Show paginated/searchable rows for one table."""
    try:
        table = get_table_rows(
            db,
            table_name,
            limit=limit,
            offset=offset,
            search=q or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return templates.TemplateResponse(
        request,
        "db/table.html",
        {
            "table": table,
            "flash_ok": request.query_params.get("ok"),
            "flash_error": request.query_params.get("error"),
        },
    )


@router.get("/db/{table_name}/{row_id}/edit", response_class=HTMLResponse)
def db_edit_form(
    request: Request,
    table_name: str,
    row_id: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Render edit form for one row."""
    try:
        row = get_row(db, table_name, row_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request,
        "db/edit.html",
        {
            "row": row,
            "flash_error": request.query_params.get("error"),
        },
    )


@router.post("/db/{table_name}/{row_id}/edit")
async def db_edit_save(
    request: Request,
    table_name: str,
    row_id: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Save edited row values."""
    form = await request.form()
    values = {key: form.get(key) for key in form.keys()}
    try:
        update_row(db, table_name, row_id, values)
    except ValueError as exc:
        return RedirectResponse(
            url=(
                f"/db/{table_name}/{row_id}/edit"
                f"?error={quote(str(exc))}"
            ),
            status_code=303,
        )
    except IntegrityError as exc:
        db.rollback()
        return RedirectResponse(
            url=(
                f"/db/{table_name}/{row_id}/edit"
                f"?error={quote('Update blocked by database constraint: ' + str(exc.orig))}"
            ),
            status_code=303,
        )

    return RedirectResponse(
        url=f"/db/{table_name}?ok={quote('Row updated successfully')}",
        status_code=303,
    )


@router.post("/db/{table_name}/{row_id}/delete")
def db_delete(
    table_name: str,
    row_id: str,
    db: Session = Depends(get_db),
    q: str = Form(""),
    limit: int = Form(50),
    offset: int = Form(0),
) -> RedirectResponse:
    """Delete one row, then return to the table list."""
    try:
        delete_row(db, table_name, row_id)
    except ValueError as exc:
        return RedirectResponse(
            url=_table_url(table_name, q=q, limit=limit, offset=offset, error=str(exc)),
            status_code=303,
        )
    except IntegrityError as exc:
        db.rollback()
        return RedirectResponse(
            url=_table_url(
                table_name,
                q=q,
                limit=limit,
                offset=offset,
                error=(
                    "Delete blocked: this row is still referenced by other records "
                    f"({exc.orig})"
                ),
            ),
            status_code=303,
        )

    return RedirectResponse(
        url=_table_url(
            table_name,
            q=q,
            limit=limit,
            offset=offset,
            ok="Row deleted successfully",
        ),
        status_code=303,
    )


def _table_url(
    table_name: str,
    *,
    q: str = "",
    limit: int = 50,
    offset: int = 0,
    ok: str | None = None,
    error: str | None = None,
) -> str:
    parts = [f"/db/{table_name}?limit={limit}&offset={offset}"]
    if q:
        parts.append(f"&q={quote(q)}")
    if ok:
        parts.append(f"&ok={quote(ok)}")
    if error:
        parts.append(f"&error={quote(error)}")
    return "".join(parts)
