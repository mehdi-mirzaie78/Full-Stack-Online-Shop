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
- Browser: `npm --prefix client exec -- playwright install --with-deps chromium`, then build client and run `npm --prefix client run test:e2e`. Playwright starts production Next on 127.0.0.1:3100; no reuse of development servers. If browser download is unavailable and Chrome is installed, explicitly set `E2E_BROWSER_CHANNEL=chrome`. `E2E_API_URL=http://127.0.0.1:8100` adds fail-closed real health probing; omit it for frontend-only smoke.
- Unit/integration discovery: `npm --prefix client run test:unit`; inside server `pytest -m 'not integration'` and `pytest -m integration`. Backend service checks require dedicated PostgreSQL/Redis, e.g. DATABASE_URL on test port 55432 and REDIS_URL on 56379 DB 15; never point tests at development/production data. CI provides isolated services automatically.
- Existing coverage includes safe JSON/error/telemetry unit checks, PostgreSQL BaseModel tests, real PostgreSQL/Redis health checks, and three browser storefront/error/fallback smoke tests. Current storefront smoke is not a backend business journey. Broader purchase/auth/RBAC/worker/storage integration and E2E remain pending under TASK-005 / TASK-701 / TASK-705 / TASK-702 / TASK-3D-006.
- Private collector validation: `python3 scripts/check_observability.py --static` or full disposable `npm run test:observability`; see [observability runbook](./observability.md). CI runs five independent gates; no real workstation logs or telemetry volumes are uploaded.
- Minimum backend coverage target 85% across unit/integration; client reporting/threshold under TASK-701. Add CI gates for tests, coverage, lint, typecheck, and browser failure traces/screenshots. Coverage does not replace critical behavioral assertions.
- Never production data, charges, SMS, or email sends. Use PostgreSQL test DBs (never SQLite), isolated Redis keys/database and test storage, deterministic time/fixtures, cleanup, and controlled external adapters.
- Record real command results, missing tools/services, and unrun checks. Missing critical dependencies must fail clearly, not silently skip tests. Do not mark feature complete while its required admin/API/test slice is missing.
