# Testing instructions

Applies with [root instructions](../../AGENTS.md) and relevant client/server guide. Require **unit, integration, and E2E** coverage across project; add relevant tests alongside each feature. Integration and E2E are complementary. Phase 7 closes coverage/release gaps, not the first tests.

## Layers

- **Unit**: Pytest for isolated business decisions; Vitest for client logic and Three.js scenes. Normal, boundary, invalid-input, and failure cases without external services. Use red-green-refactor for new behavior and bug fixes.
- **Integration**: Pytest/DRF APIClient with real isolated PostgreSQL for constraints/transactions, Redis for TTL/atomic locks, and workers/storage where those boundaries are under test. DB-backed model tests are integration coverage. Mock unrelated providers, not the boundary being proved; eager Celery alone does not prove broker delivery.
- **E2E**: Playwright real browser through running Next.js and Django with deterministic isolated data. Purchase/availability rejection, roles/ownership, Persian/English, mobile/keyboard accessibility, and Three.js unsupported WebGL/context loss/retry. Mocked API browser tests do not prove full-stack journeys. Manual browser checks are not an automated E2E suite.

## Admin / settings completion

- Every model slice includes allowed staff operations via Next.js + API. Test role/object denial, field validation, list/detail, create/edit/delete/restore where permitted, and safe aggregate actions/read-only exceptions.
- ShopSettings tests must prove DB singleton enforcement under concurrency, bootstrap, deletion/deactivation denial, unauthorized writes, safe public projection, URL/content validation, and stale-update conflict handling. E2E: staff edits shop content; fresh public request shows new content/metadata without redeploy and without stale cached branding.
- Django `/admin/` must remain absent; preserve Django auth/permissions and other health/API routes.

## Commands and gates

- Client: `npm --prefix client run test`, `npm --prefix client run typecheck`, `npm --prefix client run lint`, `npm --prefix client run build`.
- Server: activate `server/.venv`, then inside server run `pytest -v --cov=.` and `ruff check .`. Root `npm run test` / `npm run lint` chain client + server; Python tools must be on PATH.
- Playwright dependency/configuration and layer-specific discovery/commands remain TASK-005; do not claim `npx playwright test` is a working suite before setup.
- Existing coverage: client unit checks, BaseModel DB tests, mocked health API checks. Broader business integration and E2E remain pending. Track TASK-701 / TASK-705 / TASK-702 / TASK-3D-006.
- Minimum backend coverage target 85% across unit/integration; client reporting/threshold under TASK-701. Add CI gates for tests, coverage, lint, typecheck, and browser failure traces/screenshots. Coverage does not replace critical behavioral assertions.
- Never production data, charges, SMS, or email sends. Use PostgreSQL test DBs (never SQLite), isolated Redis keys/database and test storage, deterministic time/fixtures, cleanup, and controlled external adapters.
- Record real command results, missing tools/services, and unrun checks. Missing critical dependencies must fail clearly, not silently skip tests. Do not mark feature complete while its required admin/API/test slice is missing.
