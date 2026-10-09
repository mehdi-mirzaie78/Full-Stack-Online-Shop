# AGENTS.md — Full-Stack Online Shop Instructions

Modern distributed e-commerce platform: Next.js 15 storefront & custom admin, Django Ninja REST API, PostgreSQL 16 (`pgvector`), Redis 7, RabbitMQ 3.13, and Celery.

## Development Environment & Services

- Docker stack: `docker compose -f infra/docker-compose.yml up -d`
- Core ports: PostgreSQL (`5432`), Redis (`6379`), RabbitMQ (`5672`, UI `15672`), MinIO (`9000`, UI `9001`)
- API base: `http://localhost:8000` (docs at `/api/docs`), Frontend: `http://localhost:3000`

## Exact Commands

### Backend (`/backend`)
- Run server: `python manage.py runserver 0.0.0.0:8000`
- Migrations: `python manage.py makemigrations && python manage.py migrate`
- Run test suite: `pytest -v --cov=.`
- Run single test: `pytest tests/test_availability.py -k test_time_window`
- Linter & Formatter: `ruff check . --fix && ruff format .`
- Celery worker: `celery -A core worker -l INFO`
- Celery beat: `celery -A core beat -l INFO`

### Frontend (`/frontend`)
- Install deps: `npm install`
- Dev server: `npm run dev`
- Typecheck: `npx tsc --noEmit`
- Linter: `npm run lint`
- Unit tests: `npm run test`
- E2E tests: `npx playwright test`

## Architecture & Code Conventions

- **Directory layout**: Monorepo split into `/backend` (Django Ninja), `/frontend` (Next.js 15), and `/infra` (Docker).
- **Thin APIs, Pure Services**: API endpoints validate schemas; all business logic lives in `services/` (e.g. `AvailabilityEngine`, `CheckoutService`).
- **Base Model**: Entities inherit `BaseModel` (UUID pk, timestamps, soft-delete filtering `is_deleted=False`).
- **Stock Concurrency**: Inventory updates MUST execute inside `transaction.atomic()` with `select_for_update()`.
- **OTP & Ephemeral Data**: OTP codes and sliding rate-limits belong in Redis with TTLs (120s); never persist OTPs to PostgreSQL.
- **Git & Task Tracking**:
  - Branches: Work on `feature/*` branched off `develop`. Merge to `develop`, then `main`.
  - Commits: Conventional Commits (`feat(catalog): ...`, `fix(checkout): ...`).
  - Progress: Update `tasks.md` marks (`[ ]` -> `[/]` -> `[x]`) upon starting and finishing tasks.

## Pitfalls & Prohibitions

- **No SQLite in dev or test**: PostgreSQL native `JSONB` specs and `pgvector` columns break under SQLite. Run tests against PostgreSQL test DB.
- **No Direct Media Uploads**: Never stream file uploads through Django. Issue S3 presigned URLs (`POST /api/v1/media/presign-upload`) for direct client uploads to MinIO/S3.
- **Payment Webhook Idempotency**: Payment callbacks must set Redis atomic locks (`SETNX lock:payment:{token}`) before updating order status.
- **Summary Table Invalidation**: When modifying store hours or product availability windows, immediately invalidate or recompute `ProductAvailabilitySummary`.
