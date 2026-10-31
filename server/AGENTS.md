# Server instructions

Inherits [root rules](../AGENTS.md). Read [DDD guide](../docs/domain-driven-design.md), [testing guide](../docs/development/testing.md), and [admin/settings contract](../docs/admin-and-shop-settings.md) when relevant.

## Commands (inside server, activate .venv first)

- `python manage.py runserver 0.0.0.0:8000`
- `python manage.py makemigrations && python manage.py migrate` — inspect migrations before applying; no destructive schema/data change without explicit scope.
- `pytest -v --cov=.`; focused example once added: `pytest tests/test_availability.py -k test_time_window`.
- `ruff check . --fix && ruff format .` — only format/fix touched scope during feature work; no drive-by edits.
- `celery -A config worker -l INFO`; `celery -A config beat -l INFO`.

## Domain and persistence

- Modular Django monolith, acyclic context imports, direct ORM. Thin views/serializers dispatch owning use cases. Application services orchestrate I/O/permissions/transactions; policies are pure decisions with explicit inputs/time. Start with `services.py`; grow into package only when needed.
- Reuse owning business behavior from APIs, workers, and custom admin. Keep local invariants in model behavior/policies; no duplicate ORM/domain hierarchy, speculative repositories, event bus, or empty apps. Keep `apps.core` for shared technical primitives.
- Persisted domain entities inherit `apps.core.models.BaseModel`; value objects do not. Reconcile custom auth inheritance before creating User. BaseModel provides UUID/timestamps and filtered soft-delete manager. Define cross-context deletion behavior explicitly; preserve paid-order snapshots/audit records.
- Model fields/Meta use `gettext_lazy as _` for all verbose names, plurals and help text. Strict Python typing and explicit serializer fields; avoid accidental exposure/mass assignment.
- Stock writes require `transaction.atomic()` + `select_for_update()`; deterministic multi-product lock order. Use PostgreSQL constraints for enforceable invariants. No SQLite in dev or tests.
- OTP/rate limits live in Redis with 120s OTP TTL, never PostgreSQL. Payment callbacks acquire atomic Redis `SETNX lock:payment:{token}` before mutation; also need durable idempotency/transition guards.
- Schedule/window writes update or invalidate `ProductAvailabilitySummary`; checkout rechecks authoritative eligibility rather than stale display cache.
- External work outside long-held DB locks; dispatch after commit. Critical side effects require durable idempotency/recovery, not Redis locks or `on_commit()` alone.

## Custom administration and shop configuration

- No `django.contrib.admin`, Django admin routes, registrations, or ModelAdmin dependencies. Keep auth/contenttypes/permissions and required security middleware.
- New model completion requires protected DRF operations + usable Next.js staff UI + unit/integration/E2E tests. Enforce role/object authorization at reusable use-case boundaries; no unrestricted CRUD for audit history, derived summaries, payment records, or aggregate children.
- ShopSettings belongs to shop configuration context, not `core`. Keep inherited UUID; enforce constant singleton key with DB CHECK + UNIQUE constraints. Bootstrap one row in migration; deny normal deletion/soft-deletion/deactivation. Do not rely on `.first()` or model `save()` alone for singleton safety. Full contract in linked guide.
- Public settings serializer explicitly allowlists safe content; no environment secrets/provider credentials. Validate URL schemes and structured link fields, lengths, locales and rich content. Presigned uploads only; never stream media through Django.
