"""Frontend routes.

Exposes:
    GET  /
        — If a valid session cookie is present: serves index.html.
        — Otherwise: serves the login page (also index.html, login state).
    POST /session
        — Accepts the session password from the login form.
        — If correct: creates a session, sets a cookie, redirects to /.
        — If wrong: redirects back to / with an error flag.
    POST /session/logout
        — Clears the session cookie and redirects to /.
"""

# TODO: implement
