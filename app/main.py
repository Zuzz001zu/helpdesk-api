from fastapi import FastAPI

from app.config import get_settings
from app.routers import tickets

DESCRIPTION = """
REST API for an IT support desk.

* Tickets with priority-based **SLA due dates** and an `overdue` flag
* Status workflow: `open` → `in_progress` → `resolved` → `closed` (resolved tickets can be reopened)
* Filtering, search and pagination

Write operations require the `X-API-Key` header when `API_KEY` is set.
"""

app = FastAPI(title=get_settings().app_name, version="1.0.0", description=DESCRIPTION)
app.include_router(tickets.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
