# Helpdesk API

[![CI](https://github.com/Zuzz001zu/helpdesk-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Zuzz001zu/helpdesk-api/actions/workflows/ci.yml)

A REST API for an IT support desk, built with FastAPI and PostgreSQL.

Tickets get a due date from their priority (SLA), follow a simple status workflow and can be
searched, filtered and commented. A stats endpoint gives the numbers a support team usually
reports on: open tickets, overdue tickets and average resolution time.

> **FR** - API REST de gestion de tickets de support (FastAPI, PostgreSQL, SQLAlchemy, Alembic) :
> SLA par priorité, workflow de statuts, recherche et pagination, commentaires, statistiques,
> documentation OpenAPI, tests automatisés et CI.

## Features

- CRUD for tickets with validation (Pydantic)
- SLA due date per priority: critical 4 h, high 8 h, medium 24 h, low 72 h
- `overdue` flag and filter for active tickets past their due date
- Status workflow with checks: `open → in_progress → resolved → closed`; resolved tickets can be
  reopened, closed tickets are final. Invalid moves return `409 Conflict`
- Search (`q`), filters (status, priority, assignee, overdue) and pagination
- Comments and internal notes that can be hidden from the requester
- `/stats` for reporting
- API key for write operations (`X-API-Key`)
- OpenAPI documentation generated from the code (`/docs`, `/redoc`, `/openapi.json`)

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · Alembic · Pydantic v2 · pytest ·
Ruff · Docker · GitHub Actions

## Getting started

### With Docker

```bash
cp .env.example .env
docker compose up --build
```

The API runs on http://localhost:8000 and the interactive docs on http://localhost:8000/docs.
Migrations are applied when the container starts.

### Without Docker

You need Python 3.11+ and a PostgreSQL database.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # then edit DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload
```

## Examples

```bash
# Open a ticket
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" -H "X-API-Key: change-me" \
  -d '{"title": "Teams crashes on start", "requester_email": "marc@example.com",
       "priority": "critical", "category": "software"}'

# Take it and start working on it
curl -X PATCH http://localhost:8000/tickets/1 \
  -H "Content-Type: application/json" -H "X-API-Key: change-me" \
  -d '{"status": "in_progress", "assignee": "zara"}'

# Overdue high-priority tickets
curl "http://localhost:8000/tickets?priority=high&overdue=true"

# Numbers for the weekly report
curl http://localhost:8000/stats
```

```json
{
  "total": 42,
  "by_status": {"open": 12, "in_progress": 5, "resolved": 20, "closed": 5},
  "by_priority": {"critical": 2, "high": 9, "medium": 21, "low": 10},
  "overdue": 3,
  "avg_resolution_hours": 6.4
}
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/tickets` | Open a ticket |
| `GET` | `/tickets` | List, filter, search, paginate |
| `GET` | `/tickets/{id}` | Get a ticket |
| `PATCH` | `/tickets/{id}` | Update, assign, change status or priority |
| `DELETE` | `/tickets/{id}` | Delete a ticket and its comments |
| `GET` | `/tickets/{id}/comments` | List comments (`include_internal=false` hides notes) |
| `POST` | `/tickets/{id}/comments` | Add a comment or an internal note |
| `GET` | `/stats` | Counts, overdue tickets, average resolution time |
| `GET` | `/health` | Health check |

## Project structure

```
app/
  main.py          FastAPI app and routers
  config.py        settings from environment variables
  database.py      engine, session, Base
  models.py        SQLAlchemy models
  schemas.py       Pydantic request/response models
  sla.py           SLA rules and status workflow (pure functions)
  services.py      business logic and queries
  deps.py          API key dependency
  routers/         tickets, comments, stats
alembic/           database migrations
tests/             pytest suite
```

Routers stay thin: they handle HTTP concerns and call `services.py`. The SLA rules live in
`sla.py` without any database code, so they are easy to test and to change.

## Design notes

- **Dates are stored in UTC.** A small `UTCDateTime` column type makes sure values always come
  back timezone-aware, including on SQLite where the timezone would otherwise be lost.
- **Priority change keeps the SLA start.** If a ticket goes from low to critical, the due date is
  recalculated from the creation time, not from the moment of the change.
- **Statuses are stored as strings**, validated by Python enums. Adding a status does not need a
  PostgreSQL `ALTER TYPE`.
- **Migrations are checked in CI.** `alembic check` fails the build if the models and the
  migrations drift apart.

## Tests

```bash
pytest --cov=app
```

Locally the tests use SQLite in memory, so nothing has to be installed. In CI they run against a
real PostgreSQL 16 service (`TEST_DATABASE_URL`). The suite covers the SLA rules, the status
workflow, filters and pagination, API key checks, comments and stats.

## Possible next steps

- Users and roles instead of a single API key
- Email notification when a ticket becomes overdue
- Export of the stats to CSV

## License

MIT
