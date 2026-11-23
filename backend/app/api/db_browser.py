"""Browser UI routes for exploring database tables."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.db_browser import get_table_rows, list_tables_with_counts

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
) -> HTMLResponse:
    """Show paginated rows for one table."""
    try:
        table = get_table_rows(db, table_name, limit=limit, offset=offset)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # DB connectivity / query errors
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return templates.TemplateResponse(
        request,
        "db/table.html",
        {"table": table},
    )
