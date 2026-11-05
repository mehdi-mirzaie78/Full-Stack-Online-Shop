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

## Local commands and isolated resources

Install the root/client lockfiles and `server/requirements-dev.lock` first (Python 3.12,
Node.js 22 in CI). Docker Compose and Docker socket access are needed for integration
and E2E; unit tests need no services. The root runners use `server/.venv/bin/python`
when present, otherwise the invoking Python (CI installs dependencies there).

```sh
npm run test:unit         # Script regressions, Vitest, and backend unit tests
npm run test:integration  # Real PostgreSQL, Redis, and S3 tests
npm run test:e2e          # Build test client, migrate/start test API, run Playwright
npm run test:all          # All layers, including 85% backend runtime coverage gate
```

Install Chromium once using `npm --prefix client exec -- playwright install --with-deps chromium`.
If Chrome is already installed, use `E2E_BROWSER_CHANNEL=chrome npm run test:all`
(or the same prefix on `test:e2e`). Browser downloads can use `HTTPS_PROXY` during
installation; the test runner discards inherited proxies so local requests stay local.
The harness does not install missing dependencies or silently skip missing services.

| Resource | Test address / identifier |
| --- | --- |
| Compose project | `shop-tests`, standalone `infra/compose.test.yml` |
| PostgreSQL | `127.0.0.1:55432`, `shop_test`; Pytest creates/drops `test_shop_test` |
| Redis | `127.0.0.1:56379`, database 15, key prefix `shop-tests` |
| SeaweedFS S3 | `http://127.0.0.1:59000`, test-only credentials, `shop-test-media` |
| Django API | `http://127.0.0.1:8100`, `config.test_settings` |
| Next.js | `http://127.0.0.1:3100`, `.next-test` build output |

The root runner starts fresh test containers, waits for health, and removes the
`shop-tests` containers/network/anonymous volumes in `finally`, including failed
startup/tests. PostgreSQL and S3 use tmpfs; Redis persistence is disabled. Development
containers, volumes, ports, and `.env` are not used. Fixed ports and an exclusive
local lock reject concurrent runs instead of sharing mutable fixtures. Avoid manually
binding these test ports to unrelated services. Do not merge the test Compose file
with development files or put real data in the test stack.

For focused debugging, `npm run test:infra:up` leaves services running. Activate
`server/.venv`, then from `server` use `pytest -m integration` or a single test.
`npm run test:infra:down` removes only test resources; this is also the recovery
command after forced termination or machine shutdown. A managed integration/E2E run
resets any retained test stack before starting. The existing root `npm run test`
still chains Vitest and Pytest without managing services or running E2E; prefer
`test:all` for the complete managed workflow. Root `npm run lint` needs Python tools
on PATH; client-only checks remain `npm --prefix client run lint` / `typecheck`.

## Fixtures, delivery safety, and artifacts

Backend tests default to `config.test_settings`, which skips root `.env`, fixes DB,
cache, and S3 addresses, and overrides inherited service URLs. Pytest rejects development
settings. Database fixtures use Django's isolated test DB; BaseModel rows use explicit
example data and rollback between tests. S3 tests get a unique bucket with fixed object
contents and remove its objects/bucket on teardown. The browser API uses only freshly
migrated test data. The runner seeds synthetic identity users for the staff/OTP browser journeys.
Future model slices must add deterministic factories and browser fixtures alongside
the feature rather than seed real customer data.

Email uses Django's in-memory outbox; Celery uses eager execution and in-memory
broker/results. Eager mode does not prove real broker delivery. Autouse Pytest socket
checks block external hosts and service access from unit tests; integration tests
allow only the three local test ports. A telemetry unit test explicitly allows its
own ephemeral receiver port. These Python socket checks do not sandbox subprocesses
or native libraries. Keep provider credentials out of tests and stub those boundaries.
Payments do not exist yet: add their fake adapters and outcome fixtures with their owning feature. Identity now has a test-only SMS mailbox; normal delivery fails clearly unless DEBUG-only Redis delivery is explicitly enabled for manual testing; real SMS awaits provider selection. No placeholder
payment/SMS framework is introduced by this harness.

Test browser build/start discards cached client environment files and does not load
root `.env`. The runner fixes public API/media URLs to the isolated services. Managed E2E
always starts its own API and production Next server, refuses existing server reuse,
and checks real API health. It proves password/OTP identity journeys, named user creation/editing, password and role/direct permission controls, tab/switch keyboard and RTL behavior, late-search response handling and draft preservation during session revocation, alongside storefront language switching, browser error privacy and unsupported WebGL fallback. Purchase journeys remain planned.

Artifacts survive service cleanup: `server/server.junit.xml`, `server/coverage.xml`
(full backend run), `test-results/api.log`, `client/playwright-report/`, and
`client/test-results/` (failure screenshots/traces). Open browser reports with
`npm --prefix client exec -- playwright show-report`. CI uses the same backend/E2E
runner and uploads these artifacts; hosted Actions verification requires a push.

## Gates

- Private collector validation: `python3 scripts/check_observability.py --static` or full disposable `npm run test:observability`; see [observability runbook](./observability.md). CI runs five independent gates; no real workstation logs or telemetry volumes are uploaded.
- Minimum backend coverage target 85% across unit/integration; client reporting/threshold under TASK-701. Add CI gates for tests, coverage, lint, typecheck, and browser failure traces/screenshots. Coverage does not replace critical behavioral assertions.
- Never production data, charges, SMS, or email sends. Use PostgreSQL test DBs (never SQLite), isolated Redis keys/database and test storage, deterministic time/fixtures, cleanup, and controlled external adapters.
- Record real command results, missing tools/services, and unrun checks. Missing critical dependencies must fail clearly, not silently skip tests. Do not mark feature complete while its required admin/API/test slice is missing.
