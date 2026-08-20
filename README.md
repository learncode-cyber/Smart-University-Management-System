# University Management System

Final project — ICT Bangladesh, AI-Powered Software Engineering Batch 26/3.

Backend: FastAPI + PostgreSQL + SQLAlchemy 2.0 + Alembic
Frontend: React 18 + TypeScript + TailwindCSS + React Query

---

## Quick start (Docker — recommended)

```bash
docker compose up --build
```

This starts Postgres, runs migrations, seeds the first admin account, and starts both
the API (`:8000`) and the web app (`:5173`). First run takes a minute or two.

- Web app: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs
- **Default admin login** (change immediately after first login):
  `admin@university.edu` / `ChangeMe123!`

To stop: `docker compose down`. To wipe the database and start fresh: `docker compose down -v`.

---

## Manual setup (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# create a Postgres database matching backend/.env.example, or update DATABASE_URL
cp .env.example .env

alembic upgrade head
python -m scripts.seed          # creates the first admin account — see below
uvicorn app.main:app --reload
```

API now runs at http://localhost:8000 (docs at `/docs`).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Web app runs at http://localhost:5173 and proxies `/api` to `http://localhost:8000`
(see `vite.config.ts`).

---

## Why a seed script? (bootstrap gap, flagged during the build)

Every account-creation endpoint (`POST /users/students`, `POST /users/teachers`)
requires an already-logged-in Admin. On a freshly migrated, empty database there is no
admin to log in as — the system would otherwise be unbootable. `backend/scripts/seed.py`
creates exactly one university, one department, and one admin account (see credentials
above). It's a no-op if a university already exists, so it's safe to run more than once.

After logging in as the seeded admin, use **Admin → User Management** to create real
department/course data and onboard actual students/teachers.

---

## Environment variables

See `backend/.env.example` for the full list. The only one that matters beyond local
dev is `JWT_SECRET_KEY` — generate a real one for anything other than a local demo:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Running backend tests

```bash
cd backend
pip install pytest
pytest tests/
```

Covers the pure business-logic functions called out in the brief: attendance
percentage, GPA calculation, fee/invoice status, marks aggregation, and schedule
conflict detection — all unit-tested independent of the database.

---

## Project structure

```
backend/
  app/
    api/v1/        # routers — thin, parse request → call service → shape response
    services/       # business logic (incl. pure, unit-tested functions)
    models/          # SQLAlchemy ORM models
    schemas/          # Pydantic request/response schemas
    core/              # config, security, error shapes, rate limiting
  alembic/             # migrations
  scripts/seed.py       # bootstrap script (see above)
  tests/                # pytest unit tests for pure functions

frontend/
  src/
    pages/          # one file per screen (Section 7 of the proposal)
    components/      # layout shell, dashboard widgets, shared Modal
    contexts/          # auth, toast
    lib/                # typed API client, React Query hooks
    types/                # shared TypeScript types mirroring backend schemas
```

---

## Flagged deviations from the original proposal

The proposal (Section 6, REST API spec) omitted a few things needed to actually run
the system end-to-end. Each is flagged in code comments at the point it was added;
summary here for the video walkthrough:

| Addition | Why |
|---|---|
| Academic Structure module (`/academic/*`) + its Admin UI screen | Exams/attendance/results/schedule all need a `course_section_id`, which needs departments/courses/sections to exist first — and an Admin needs an actual screen to create them, not just Swagger |
| Parent access to attendance/results/schedule `/me` endpoints | Section 5 promises this for Parent; Section 6 only listed Student |
| Student access to `/fees/payments/{id}` | Section 3 promises "view full payment history" for Student; Section 6 listed Admin/Parent only |
| `GET /results/pending` + "Submit for Approval" button in Teacher Grading | No way to list results awaiting approval, or to actually trigger submission after grading — the whole approval workflow was unusable without both |
| `GET/POST /fees/dashboard-summary`, `/fees/overdue/send-notices`, plus Create Fee Structure / Record Payment forms | "Real-time revenue view," "bulk notice sender," "define fee structures," and "track all payments" were all described for Admin but had no backing endpoints or UI |
| `GET /academic/course-sections/{id}/students` (class roster) | Needed for the Teacher Attendance Marker screen — no way to know who's enrolled otherwise |
| Entire Notifications module (`/notifications/*`) | Never defined in Section 6 at all, despite Section 3/7 requiring a working notification feed, and other modules already creating `Notification` rows |
| `GET /schedule` (list all) + Admin Timetable Control screen | Proposal names this screen explicitly ("Admin: Timetable Control — Create and publish class schedules") but no screen or list-all endpoint existed |
| `backend/scripts/seed.py` | Bootstrap gap — see above |
| `vite.config.ts` `resolve.alias` for `@` | **Caught during real Docker testing, not by static analysis**: `tsconfig.json`'s `paths` mapping only satisfies TypeScript's type-checker — Vite's actual dev-server module resolution needs its own, separate alias config, or every `@/...` import fails at runtime with "Failed to resolve import" |

**Minor, non-blocking gaps** (flagged, not fixed, to keep scope sane):
- No single-student detail view (`GET /users/students/{id}`) — Admin's list + edit-modal already carries the same data, so this is a nice-to-have, not a missing capability
- No "edit" action on Admin Timetable Control (only create/delete) — delete-and-recreate achieves the same result
- `GET /attendance/reports` has no dedicated Admin screen — attendance is visible via Teacher's marker and Student/Parent's own view; cross-department reporting UI was deprioritized

---

## Troubleshooting

**`npm error code ECONNRESET` / `npm error network` during `docker compose up --build`**
This is your network dropping mid-download inside the frontend container, not a code
problem — the backend build (much larger) already succeeded by this point. Just re-run:
```bash
docker compose up --build
```
Docker caches the backend layer, so only the frontend retries. If it keeps happening on
an unstable connection, add retry tolerance to `frontend/Dockerfile` before `RUN npm install`:
```dockerfile
RUN npm config set fetch-retries 5 && npm config set fetch-retry-mintimeout 20000
```

**`Failed to resolve import "@/..." from "src/App.tsx"`**
Already fixed in this version — `vite.config.ts` now has its own `resolve.alias` for `@`.
(Root cause: `tsconfig.json`'s `paths` mapping only affects TypeScript's type-checker; Vite's
dev server needs the alias configured separately, or it can't find any `@/...` import at
runtime even though `tsc` reports no errors.)

---



Mapped to the grading rubric in the proposal (Section 2).

**API completeness (30 marks)**
- [ ] Show `/docs` (Swagger) — walk through each module's endpoints
- [ ] Demonstrate JWT auth: login, an authenticated request, refresh, logout
- [ ] Demonstrate RBAC: same endpoint, two roles, different results (e.g. student vs teacher hitting `/exams`)
- [ ] Show a request that gets rejected by validation (Pydantic) and one rejected by a business rule (e.g. submitting an exam after its deadline)

**UI completeness + role-based access (30 marks)**
- [ ] Walk through all 4 roles logging in and landing on their own dashboard
- [ ] Student: sit an exam end-to-end (MCQ auto-grades instantly), check Results/Attendance/Fees
- [ ] Teacher: build an exam, mark attendance, grade a written answer
- [ ] Admin: approve a result, view the fee dashboard, send overdue notices
- [ ] Parent: show the same data scoped to their linked child
- [ ] Show a loading state, an error state, and an empty state (resize the browser to show responsive layout too)

**Database design (15 marks)**
- [ ] Show the ER structure — highlight `university_id` on every tenant table (multi-tenancy readiness) and the RESTRICT foreign keys that protect historical records from deletion
- [ ] Explain one non-obvious design decision out loud (e.g. why `exam_answers` holds grading data instead of a separate `exam_grades` table)

**Code quality, documentation, deployment (5 marks)**
- [ ] `docker compose up --build` running live, from a clean checkout
- [ ] Show the pure, unit-tested functions (`services/grading.py`, `gpa.py`, `attendance_calc.py`, `fee_calc.py`, `schedule_calc.py`) and run `pytest`
- [ ] Mention the flagged-deviations table above — shows you understood the spec well enough to know where it was incomplete, not just where it was explicit
