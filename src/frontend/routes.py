"""Frontend routes.

Exposes:
    GET  /          — serves the UI if a valid session cookie is present;
                      serves the login page otherwise.
    POST /session   — validates the password; on success sets a session cookie
                      and redirects to /; on failure redirects back with an
                      error flag.
"""

import os
from pathlib import Path

from fastapi import APIRouter, Cookie, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from src.frontend.session import create_session, is_valid

router = APIRouter()

_templates_dir = Path(__file__).parent / "templates"


@router.get("/", response_class=HTMLResponse)
def index(
    session_id: str | None = Cookie(default=None),
    error: str | None = Query(default=None),
) -> HTMLResponse:
    if not is_valid(session_id):
        login_template = (_templates_dir / "login.html").read_text()
        error_html = (
            '<p class="text-xs text-red-500 mt-1">Incorrect password.</p>'
            if error else ""
        )
        return HTMLResponse(login_template.replace("__ERROR__", error_html))
    ui_template = (_templates_dir / "index.html").read_text()
    html = ui_template.replace("__API_KEY__", os.environ.get("API_KEY", ""))
    return HTMLResponse(html)


@router.post("/session")
def login(password: str = Form(...)) -> RedirectResponse:
    expected = os.environ.get("FRONTEND_SESSION_PASSWORD", "")
    if password != expected:
        return RedirectResponse("/?error=1", status_code=303)
    session_id = create_session()
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="strict",
    )
    return response
