# AGENTS.md — Full-Stack Online Shop Instructions

Modern distributed e-commerce platform: Next.js 15 storefront & custom admin (`/client`), Django Ninja REST API (`/server`), PostgreSQL 16 (`pgvector`), Redis 7, RabbitMQ 3.13, and Celery (`/infra`).

## Project Layout & Root Runner

- Root runner: Root `package.json` orchestrates client and server workspaces.
  - `npm run dev` -> Runs client and server concurrently.
  - `npm run dev:client` -> Boots Next.js 15 app on `:3000`.
  - `npm run dev:server` -> Boots Django Ninja API on `:8000`.
  - `npm run test` / `npm run lint` -> Runs tests and linters across workspaces.
- Infrastructure: `docker compose -f infra/docker-compose.yml up -d`
- Core ports: PostgreSQL (`5432`), Redis (`6379`), RabbitMQ (`5672`, UI `15672`), MinIO (`9000`, UI `9001`).

## Environment & Secrets Policy

- Secret isolation: Dedicated `.env` files live in `/server` and `/client` (git-ignored).
- Version control rule: Commit ONLY `.env.example` templates. Never commit `.env` or plain credentials.
- Local setup: Copy `.env.example` -> `.env` in target workspace before running.

## Exact Commands

### Server (`/server`)
- Run server: `python manage.py runserver 0.0.0.0:8000`
- Migrations: `python manage.py makemigrations && python manage.py migrate`
- Run test suite: `pytest -v --cov=.`
- Run single test: `pytest tests/test_availability.py -k test_time_window`
- Linter & Formatter: `ruff check . --fix && ruff format .`
- Celery worker: `celery -A core worker -l INFO`
- Celery beat: `celery -A core beat -l INFO`

### Client (`/client`)
- Dev server: `npm run dev`
- Typecheck: `npx tsc --noEmit`
- Linter: `npm run lint`
- Unit tests: `npm run test`
- E2E tests: `npx playwright test`

## Architecture & Code Standards

- **Modularity & Boundaries**: Monorepo split into `/client`, `/server`, and `/infra`. Zero circular dependencies.
- **DRY & Single Responsibility**: Extract shared domain calculations to pure services; do not duplicate logic across API endpoints or UI views.
- **Thin APIs, Pure Services**: Endpoints only validate Pydantic v2 schemas; business logic lives in `services/` (e.g. `AvailabilityEngine`, `CheckoutService`).
- **Base Model**: Entities inherit `BaseModel` (UUID pk, timestamps, soft-delete manager filtering `is_deleted=False`).
- **Stock Concurrency**: Inventory updates MUST execute inside `transaction.atomic()` with `select_for_update()`.
- **Ephemeral Data**: OTP codes and sliding rate-limits belong strictly in Redis with TTLs (120s); never store OTP in PostgreSQL.
- **Clean Code & Maintainability**: Strict typing across Python (`mypy`/Pydantic) and TypeScript; small functions (<30 lines); self-documenting code over excessive comments.
- **Git & Task Tracking**:
  - Branches: Work on `feature/*` branched off `develop`. Merge to `develop`, then `main`.
  - Commits: Conventional Commits (`feat(order): ...`, `fix(auth): ...`).
  - Progress: Update `tasks.md` marks (`[ ]` -> `[/]` -> `[x]`) on every task transition.

## Pitfalls & Prohibitions

- **No SQLite in dev or test**: PostgreSQL native `JSONB` specs and `pgvector` columns break under SQLite. Tests require PostgreSQL test DB.
- **Presigned Uploads Only**: Never stream media files through Django. Issue S3 presigned URLs (`POST /api/v1/media/presign-upload`) for direct upload to MinIO/S3.
- **Webhook Idempotency**: Payment callbacks must set Redis atomic locks (`SETNX lock:payment:{token}`) before mutating order state.
- **Summary Table Invalidation**: Update or invalidate `ProductAvailabilitySummary` on any schedule or window mutation.
