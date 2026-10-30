# AGENTS.md — Project-wide rules

Next.js 15 / React 19 storefront and custom admin, Django REST Framework modular monolith, PostgreSQL 16 + pgvector, Redis, RabbitMQ, Celery, and S3-compatible storage.

## Read only relevant layers

These linked guides are instructions, not optional background. Root rules apply everywhere; scoped guides add detail. Read all relevant layers for cross-stack work. Keep rules in their owning guide, link rather than duplicate, and do not load every guide for unrelated changes.

| Work | Required guide |
| --- | --- |
| Client/UI, typography, Three.js | [client/AGENTS.md](client/AGENTS.md) |
| Models, API, business rules, workers | [server/AGENTS.md](server/AGENTS.md) |
| Containers, services, configuration | [infra/AGENTS.md](infra/AGENTS.md) |
| Feature tests / verification | [Testing](docs/development/testing.md) |
| Domain ownership / modeling | [DDD guide](docs/domain-driven-design.md) |
| Admin operations / shop configuration | [Admin and shop settings](docs/admin-and-shop-settings.md) |

## Clean code on every change

- Read definitions/usages first; match existing style. Use clear business names, explicit types, small cohesive functions/components, and one responsibility per module. Prefer functions under 30 lines where it improves clarity; do not fragment readable code just to meet a count.
- DRY: one owner for each business rule; reuse owning use cases across APIs, admin, and workers. Extract real repeated behavior, not unrelated code that only looks similar. Avoid copy-paste rules and premature generic abstractions.
- YAGNI: stdlib/native platform and installed dependencies first. Smallest correct diff; no empty scaffolding, speculative interfaces, generic repositories, or unrelated refactors. Extend through clear module boundaries, not a framework for hypothetical features.
- Validate at trust boundaries; handle failures without losing data, hiding errors, or leaking secrets. Keep permissions, accessibility, concurrency, and audit guarantees intact. Comments explain why, not obvious code.
- Develop one tested vertical slice at a time. New model delivery includes its permitted Next.js admin operations + protected API + tests; do not defer admin usability until final hardening. Read-only/derived/audit models use safe inspection/actions, not unrestricted CRUD.
- No Django admin UI or model registrations. Next.js `/admin` + DRF is the only staff panel. Keep Django auth/permissions; removing admin does not mean removing security.
- Use pragmatic DDD; preserve domain invariants and existing requirements. Resolve TASK-007 before catalog/checkout modeling; do not invent missing business policies.

## Workflow and verification

- Work on `feature/*` off `develop`; Conventional Commits. Do not commit/push without request. Preserve unrelated working-tree edits.
- Update `tasks.md` on every transition (`[ ]` pending, `[/]` active, `[x]` verified). Keep requirements/ERD consistent with domain changes.
- Require relevant unit, integration, and E2E coverage alongside features; follow [testing guide](docs/development/testing.md). Record missing tools/services and unrun checks honestly.
- Root runners: `npm run dev`, `npm run dev:client`, `npm run dev:server`, `npm run test`, `npm run lint`, `npm run infra:up`, `npm run infra:status`. Root test runs Vitest then Pytest, not Playwright. Backend root test/lint need activated Python environment; backend dev runner uses `server/.venv`.
- Never read/print/commit secrets. Shared local config is root `.env` (ignored); copy `.env.example` for setup. Only `NEXT_PUBLIC_` values may reach browsers. Use example templates in git, never real credentials.
