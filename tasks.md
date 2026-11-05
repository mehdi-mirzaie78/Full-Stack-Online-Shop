# Project Implementation Tasks

Live task tracking matrix for Full-Stack Online Shop. Status marks: `[ ]` Pending, `[/]` In Progress, `[x]` Completed.

Testing rule: every feature includes relevant unit, integration, and E2E coverage as it is built. All three layers are required across the project; Phase 7 closes gaps and enforces release gates, not the start of testing. Existing DB-backed BaseModel tests are integration coverage; manual browser checks are not an automated E2E suite.

Delivery rule: follow [layered instructions](./AGENTS.md) and [admin/settings contract](./docs/admin-and-shop-settings.md). Every new model ships its permitted Next.js staff operations, protected API, and tests in the same slice. Immutable audit/derived records use safe inspection/actions, not unrestricted CRUD. Phase 5 does not postpone model administration.

---

- [x] **TASK-INFRA-S3**: Replace unavailable MinIO image with pinned SeaweedFS; all Compose services healthy; authenticated S3 bucket listing and object upload/download/delete verified.

## Phase 0: Project Scaffolding & Infrastructure Foundations

- [x] **TASK-OBS-PULL-RETRY**: Pull missing digest-pinned images before telemetry startup; retry selected transient registry errors up to three attempts with 5s/10s delays. Permanent and exhausted failures remain fatal; startup uses `--pull never`. Nine script regressions and structural checks passed; full disposable telemetry smoke passed privacy, metrics, Grafana correlation and restart persistence, with cleanup. Hosted CI rerun remains unverified.

- [x] **TASK-LOCAL-SETUP**: Installed root/client lockfiles and 69 locked backend packages in Python 3.12 virtualenv; configured ignored root environment, using PostgreSQL host port 55433 to avoid an existing service. Four infrastructure services healthy, migrations applied, no migration drift, storefront/API running, and DB/Redis health plus RabbitMQ/S3 authentication verified. Passed 46 backend tests against disposable PostgreSQL/Redis, 21 frontend tests, typecheck/lint/build, and 3 Chrome browser smoke tests with live API health probe. Installed upstream Ponytail skill in the user Codex skills directory. Downloads used the local HTTP proxy; Node 26 was available locally while CI targets Node 22. No commit/push.

- [x] **TASK-OBS-CI**: Safe logging, correlation and five CI gates verified. Review fixes prevent Celery worker formatter bypass and trace-header leakage through redirects, with failing-then-passing regressions. Final local checks: 46 backend tests / 93.80% coverage; 21 client tests; 3 browser tests; lint/types/build; Django checks/migration drift; workflow contract and full disposable telemetry smoke including runtime Grafana correlation templates. Hosted Actions and branch protection remain owner follow-up after authorized push; no business checkout waterfall claimed.
- [x] **TASK-OBS-LOCAL**: Optional private Docker Grafana/Loki/Tempo/Prometheus/Alloy stack, digest-pinned images, provisioned dashboards, retention and restricted socket proxy. Disposable full smoke passed Docker collection, log/trace privacy, existing route retention, metrics, dashboard queries and restart persistence; production-style setup still needs user-owned Grafana password file. Multi-day expiration and browser trace-link clicking not claimed.

- [x] **TASK-010**: Review Fixes & Bilingual Typography Consistency
  - [x] Centralize English/Persian body/heading rhythm; fix slider labels, add explicit page-reload failed-import recovery and phase-aware root environment loading
  - [x] Audit clean; 10 client tests, 15 backend tests, typecheck/lint/build and browser spacing/labels/reload/mobile checks pass; clean Docker npm 10 install and client tests pass

- [x] **TASK-009**: Layered Engineering Rules & Custom Admin Contract
  - [x] Split root/client/server/infra/testing instructions; require readable, maintainable code, DRY and minimal abstractions for every change
  - [x] Specify per-model custom Next.js administration and ShopSettings singleton roadmap; preserve Django auth/permissions
  - [x] Remove Django admin app/routes; 15 backend tests, touched-file Ruff, Django system checks and documentation links pass

- [x] **TASK-001**: Git Repository Initialization & Structure Scaffolding
  - [x] Create `README.md`, `LICENSE` (MIT), `.gitignore`, `tasks.md`, and `AGENTS.md`
  - [x] Initialize git repo on `main` and create `develop` branch
  - [x] Configure root `package.json` runner (`npm run dev`, `dev:client`, `dev:server`)
  - [x] Establish repository folder structure (`/server`, `/client`, `/infra`)

- [x] **TASK-002**: Docker Compose & Local Services Orchestration
  - [x] Configure `docker-compose.yml` for PostgreSQL 16 (with `pgvector`), Redis 7, RabbitMQ 3.13 (management enabled), and MinIO
  - [x] Configure environment variable templates (`.env.example` in `/server` and `/client`)
  - [x] Verify healthchecks for all containerized dependencies

- [x] **TASK-003**: Server API Boilerplate (Django REST Framework)
  - [x] Initialize Django project in `/server` with dependency management
  - [x] Install and configure djangorestframework, drf-spectacular, CORS headers, and PostgreSQL connection
  - [x] Implement global healthcheck endpoints (`/api/health/`, `/api/health/db/`, `/api/health/redis/`)
  - [x] Configure Ruff linter and formatter settings

- [x] **TASK-004**: Client Boilerplate (Next.js 15)
  - [x] Scaffold Next.js 15 App Router in `/client` with TypeScript and Tailwind CSS
  - [x] Install and initialize shadcn/ui component library
  - [x] Configure Biome / ESLint & Prettier
  - [x] Setup initial RTL layout direction switch (`dir="rtl"` / `dir="ltr"`)

- [x] **TASK-008**: Polished Persian & English Typography
  - [x] Self-host Vazirmatn and Manrope variable fonts with licenses; apply language-aware font stacks
  - [x] Refine heading spacing and UI typography; verify both languages, mobile layout, and client checks

- [x] **TASK-005**: Automated Test Harness & Isolated Test Environment
  - [x] Establish distinct unit, integration, and E2E discovery/commands; register Pytest markers and keep Vitest from collecting Playwright tests
  - [x] Add Playwright dependency, configuration, browser installation instructions, and first repeatable storefront smoke test
  - [x] Provide deterministic fixtures and isolated PostgreSQL test DB, Redis namespace/database, and test storage; never use SQLite or production resources
  - [x] Prevent current tests from real delivery with in-memory email/Celery and outbound Python socket checks; payment/SMS fake adapters must ship with their first owning feature (those modules do not exist yet)
  - [x] Document service startup, seed/reset/cleanup, environment prerequisites, and failure artifacts
  - [x] Acceptance: each layer runs independently with meaningful assertions; unavailable dependencies fail clearly, not silently skip critical checks
  - Verification: managed full run passed 57 backend tests / 93.80% runtime coverage, 24 frontend tests, 6 runner/workflow checks, and 3 Chrome browser tests against its own API. Unit, integration (9 tests), and E2E commands also passed independently; missing PostgreSQL failed clearly. Lint/types/build passed and test containers/network were removed; hosted Actions awaits authorized push.

  - Review: fixed duplicate cleanup attempts when Docker is inaccessible and excluded generated `.next-test` output from ESLint, with failing-then-passing regressions. Full backend/browser checks and final client tests/lint/types pass.

- [x] **TASK-006**: DDD Architecture & Shared Business Language
  - [x] Document bounded contexts, business vocabulary, invariants, transaction boundaries, and Django implementation rules in `docs/domain-driven-design.md`
  - [x] Link conventions and requirements; map upcoming feature work to owning contexts without generating empty apps

- [ ] **TASK-007**: Resolve Domain Questions Before Catalog/Checkout Modeling
  - [ ] Confirm physical goods, digital assets, or both; define stock/reservations, shipping versus download entitlement, license/refund rules, and availability applicability
  - [ ] Specify currency unit/rounding, store timezone/calendar, availability boundary semantics, and coupon/discount precedence
  - [ ] Reconcile payment and fulfillment states, stock reservation/commit/release timing, and authoritative transition rules across requirements and ERD
  - [ ] Acceptance: worked business examples and agreed invariants recorded in DDD guide and reflected in requirements/ERD; no silent change to existing scored constraints

---

## Three.js Learning Track: Material Storefront

Work alongside business phases; this track does not replace catalog, auth, or checkout work. Learning checkpoints and source links: [docs/threejs-learning.md](./docs/threejs-learning.md).

- [x] **TASK-3D-001**: Native Three.js Foundation & First Material Lab
  - [x] Add `three` and TypeScript types; keep WebGL code behind a client-only dynamic import
  - [x] Build an opt-in material sphere with orbit controls, color, roughness, metalness, and reset
  - [x] Preserve Persian/English controls, keyboard access, static fallback, and on-demand rendering
  - [x] Verify scene tests, client typecheck, lint, production build, and browser behavior
  - [x] Document scene, camera, mesh, lights, renderer, and cleanup; leave exercises for learner
  - Verification: production browser smoke checks and development Strict Mode load pass; real-device touch gesture validation remains in TASK-3D-006.

- [ ] **TASK-3D-002**: PBR Texture Inspector (after TASK-3D-001)
  - [ ] Learn UVs and texture color space; load a licensed local base-color, normal, roughness, and metalness map set
  - [ ] Mark base-color maps as sRGB; keep normal/roughness/metalness maps as non-color data
  - [ ] Add UV tiling and map toggles with DOM controls; dispose replaced textures
  - [ ] Compare same material under two lighting setups; explain why this is not an exact UE/V-Ray/Corona preview
  - [ ] Acceptance: texture load failure preserves poster and controls; no remote asset dependency in starter

- [ ] **TASK-3D-003**: Catalog Product Preview (after TASK-201, TASK-205, TASK-206, TASK-3D-002)
  - [ ] Define validated, optional preview metadata: poster, approved asset URLs, material maps, and attribution
  - [ ] Extend presigned upload policy for preview assets with type, byte-size, origin, and resource limits
  - [ ] Reuse one active viewer on product detail; keep product grids as static posters
  - [ ] Keep price, availability, license, and cart actions in HTML, independent of WebGL
  - [ ] Acceptance: no WebGL or asset failure blocks browsing or purchase; previews never expose paid source downloads

- [ ] **TASK-3D-004**: Model Turntable (after TASK-3D-003)
  - [ ] Learn scene graphs/transforms with a licensed GLB and `GLTFLoader`; frame model bounds
  - [ ] Validate asset and external-resource URLs; prefer self-contained GLB previews
  - [ ] Add keyboard-accessible view presets, zoom limits, and reset; clean up every geometry, material, and texture
  - [ ] Add explicit animation toggle only if useful; default off and respect reduced motion, hidden tabs, and offscreen state
  - [ ] Acceptance: model load errors/timeouts retain poster and usable purchase controls

- [ ] **TASK-3D-005**: Material Comparison & Shader Experiments (after TASK-3D-002)
  - [ ] Compare two materials on one shared canvas under identical light/camera settings
  - [ ] Learn uniforms, vertex/fragment stages, and GLSL with one optional shader exercise
  - [ ] Treat browser shaders as demos, not executable previews of HLSL or proprietary engine shaders
  - [ ] Acceptance: standard PBR viewer remains default; experiments never enter cart/admin critical paths

- [ ] **TASK-3D-006**: Production Preview Quality Gate (before storefront release)
  - [ ] Automate browser checks for RTL/LTR, keyboard controls, blocked WebGL, lost context, retry, resize, and route cleanup
  - [ ] Profile a representative mobile device: initial JS, asset bytes, frame time, GPU memory, and idle work
  - [ ] Set measured budgets; cap pixel ratio, render on demand, lazy-load assets, and retain static posters
  - [ ] Acceptance: no idle animation loop, no repeated-mount resource growth, and no 3D dependency required for checkout

---

## Phase 1: Core Domain, Identity & Customer Module

- [x] **TASK-IDENTITY-PASSWORD**: Shared rate-limited password/OTP login with CSRF and JWT cookies; private development-admin credentials created outside git; explicit Zod phone-length checks; shadcn Base UI navigation/button/input components with fixed navbar anchors and RTL direction provider; removed server status. Verified 88 backend tests, 31 frontend tests, 9 browser journeys including password sign-in and fixed navbar geometry, plus lint/types/build. Production dependency audit reports zero vulnerabilities. No commit/push.

- [x] **TASK-IDENTITY-UX**: Development-only Redis OTP inspection (`dev_sms` command), automatic session recovery/redirects with no manual session button, shared navbar language toggle, Zod forms with native browser validation disabled, and identity page polish. Verified 86 backend tests / 92.46% runtime coverage, 30 client tests, 7 browser journeys, lint/types/build; visually inspected login screenshot. Also fixed the initial CSRF request race and test API port preflight for rapid reruns.

Build TASK-501 after TASK-102/103 authentication and before delivering additional managed models. TASK-102 includes initial protected identity management APIs and staff screens; TASK-501 provides their shared shell. No unauthenticated temporary CRUD panel.

- [ ] **TASK-108**: ShopSettings Singleton & Protected API (after TASK-102/103, TASK-501, TASK-005)
  - [ ] Implement shop-owned BaseModel singleton, DB CHECK + UNIQUE key, bootstrap migration, no deletion/archive/deactivation, revision-based stale-write protection
  - [ ] Add validated localized branding, landing, contact, link lists and metadata; explicit safe public serializer and SUPERADMIN editor/AUDITOR read-only API
  - [ ] Ship minimal usable `/admin/shop` editor in this slice, with API authorization, validation and conflict states
  - [ ] Verify constraints/concurrency, bootstrap, denied methods/roles, public allowlist and staff-save browser journey; follow admin/settings contract

- [ ] **TASK-109**: Settings-Driven Storefront (with TASK-108; media picker after TASK-205)
  - [ ] Replace hardcoded shop identity/landing/navigation/contact/footer/metadata with shared server-side settings loader; keep UI translations and catalog data separate
  - [ ] Start uncached; verify fresh public content/metadata after save without redeploy, explicit fallback and Persian/English behavior
  - [ ] Extend editor with approved media picker when presigned upload slice exists; no arbitrary URL fetching or executable content

- [ ] **TASK-110**: Configurable About Page (later, after TASK-108/109)
  - [ ] Add localized About content/publication fields, safe rendering and `/about` page with matching staff editor/API/tests; no generic CMS scaffolding now

- [x] **TASK-101**: Abstract Base Models & Soft Delete Pattern
  - [x] Create `BaseModel` (`id: UUID`, `created_at`, `updated_at`, `deleted_at`, `is_active`, `is_deleted`)
  - [x] Implement `SoftDeleteManager` (`objects.all()` excludes soft-deleted records; `objects.all_with_deleted()` includes them)
  - [x] DB-backed integration tests for soft-delete, restore, and cascade behavior

- [/] **TASK-102**: Custom User & RBAC Model
  - [x] First vertical slice: User/roles, protected staff operations, OTP/JWT sessions and minimal staff shell; customer profiles/addresses follow separately.
  - [x] Create custom `User` model using phone number as unique identifier
  - [x] Add `Role` enum (`SUPERADMIN`, `PRODUCT_MANAGER`, `OPERATOR`, `AUDITOR`, `CUSTOMER`)
  - [ ] Create `CustomerProfile` (avatar, national code, age, gender) and `Address` (province, city, 10-digit postal code, body)
  - [x] User/LoginSession model tests, migration guard and migrations; profile/address models remain in the next slice

- [x] **TASK-103**: Redis-Backed OTP Engine & Sliding Rate Limiter
  - [x] Create `POST /api/v1/auth/otp/request` endpoint (generates 6-digit cryptographic code, 120s Redis TTL)
  - [x] Implement sliding window rate limit (max 3 requests per 10 minutes per IP/phone)
  - [x] Create `POST /api/v1/auth/otp/verify` endpoint (atomic verification, single-use invalidation)
  - [x] Issue JWT access + rotating refresh tokens

  - Delivery: fake SMS is enabled only by isolated test settings; normal OTP delivery returns 503 until a provider is selected. Verified 85 backend tests / 94.49% runtime coverage, 29 client tests, 9 runner/workflow regressions and 7 browser journeys (staff create/edit/archive/restore/logout, auditor read-only, customer denial, refresh recovery, mobile/keyboard and existing storefront smoke). Lint/types/test build, migration drift checks and local migrations passed; test resources cleaned up. No commit/push or hosted CI run for this slice.

- [ ] **TASK-104**: Customer Profile & Address Management APIs
  - [ ] `GET / PUT /api/v1/customer/profile`
  - [ ] `GET / POST / PUT / DELETE /api/v1/customer/addresses`
  - [ ] Enforce address validation (regex on postal code and phone)

- [ ] **TASK-105**: Storefront Auth & Address UI (Next.js)
  - [ ] Build mobile-responsive OTP login dialog with countdown timer
  - [ ] Build customer address book management UI (add, edit, select default)
  - [ ] Implement auth state management (JWT cookies + user context)

- [ ] **TASK-106**: Wishlist & Saved Products System
  - [ ] Create `SavedProduct` model with unique constraint (`customer_id`, `product_id`)
  - [ ] Implement toggle bookmark API `POST /api/v1/customer/wishlist/{product_id}`
  - [ ] Build client wishlist page with 1-click move-to-cart

- [ ] **TASK-107**: Support Ticket & Order Inquiry System
  - [ ] Create `Ticket` and `TicketMessage` models (supporting optional order reference)
  - [ ] Implement ticket creation and messaging endpoints `POST /api/v1/tickets`
  - [ ] Build client ticket management and chat thread view

---

## Phase 2: Product Catalog & Advanced Business Rules Engine

- [ ] **TASK-201**: Hierarchical Category & Product Data Models
  - [ ] Create self-referencing `Category` model (`parent_id`, `slug`, `name`, `icon_url`)
  - [ ] Create `Product` model with `base_price`, `stock`, `JSONB` specifications, and `pgvector` column
  - [ ] Category tree queries (ancestors, subcategories)

- [ ] **TASK-202**: Discount Engine (Percentage with Cap & Fixed Amount)
  - [ ] Create `Discount` model (product-level and category-level scopes)
  - [ ] Implement discount calculation logic with percentage cap ceiling
  - [ ] Unit tests covering discount priorities and edge cases

- [ ] **TASK-203**: Scored Constraint: Time-Window Availability Engine
  - [ ] Create `ProductAvailabilityWindow` (e.g. even-days 16:00 to 20:00)
  - [ ] Build `AvailabilityEngine` service verifying current timestamp against product windows

- [ ] **TASK-204**: Scored Constraint: Advance Lead-Time Ordering & Summary Table
  - [ ] Create `StoreSchedule` (store opening/closing times per day)
  - [ ] Create `ProductLeadTimeRule` (e.g. min 3h before store close, min 10h before store open)
  - [ ] Implement `ProductAvailabilitySummary` table and precomputation task
  - [ ] Tests covering edge-case ordering time validations

- [ ] **TASK-205**: S3 Presigned URL Direct Upload Integration
  - [ ] Endpoint `POST /api/v1/media/presign-upload`
  - [ ] Secure upload policy with MIME-type restriction and file size limits

- [ ] **TASK-206**: Storefront Catalog UI (Next.js)
  - [ ] Product listing page with category filters, price range, and search
  - [ ] Product detail page with dynamic specification table and availability badge

- [ ] **TASK-207**: Product Ratings & Reviews Engine
  - [ ] Create `ProductReview` model (1 to 5 rating, title, body, `is_verified_purchase` badge, `PENDING` approval status)
  - [ ] Implement submission endpoint `POST /api/v1/products/{id}/reviews` (auto-checks order history for verified badge)
  - [ ] Build client review submission form and star rating display breakdown

- [ ] **TASK-208**: Back-in-Stock & Price-Drop Subscriptions
  - [ ] Create `ProductSubscription` model (`BACK_IN_STOCK | PRICE_DROP`)
  - [ ] Implement subscribe/unsubscribe toggle endpoint `POST /api/v1/products/{id}/subscribe`
  - [ ] Build client notification alert bell toggle on product detail page

---

## Phase 3: Cart, Coupon & Atomic Checkout Engine

- [ ] **TASK-301**: Reactive Shopping Cart (Guest Local + Authenticated Redis Sync)
  - [ ] Client-side Zustand / LocalStorage cart for guest users
  - [ ] Redis hash storage for authenticated user carts
  - [ ] Auto-merge guest items into Redis cart upon login

- [ ] **TASK-302**: Coupon Code System
  - [ ] Create `Coupon` model (code, type, value, max discount, min order, usage limits)
  - [ ] Coupon validation endpoint with user usage counters

- [ ] **TASK-303**: Atomic Checkout & Concurrency Row Locking
  - [ ] Endpoint `POST /api/v1/orders/checkout`
  - [ ] Atomic transaction with `SELECT ... FOR UPDATE` on inventory
  - [ ] Concurrency test simulating 10 simultaneous orders on 1 remaining stock item

- [ ] **TASK-304**: Order State Machine & Operator Phone Verification
  - [ ] Create `Order`, `OrderItem`, and `OrderVerificationCall` models
  - [ ] Implement lifecycle transitions: `UNPAID -> PAYMENT_PENDING -> PAID -> CHECKING -> PROCESSING -> SHIPPED -> DELIVERED`
  - [ ] Operator verification step before order fulfillment

- [ ] **TASK-305**: Payment Gateway Integration & Idempotent Webhook
  - [ ] Gateway initiation endpoint
  - [ ] Idempotent callback webhook using Redis `SETNX` lock to prevent replay attacks

- [ ] **TASK-306**: Order Fulfillment Queue & Out-of-Stock Reconciliation
  - [ ] Create `OrderAdjustment` and `OrderHistory` audit trail models
  - [ ] Implement inventory reconciliation logic: auto-decrement missing items, recalculate totals, trigger partial refund
  - [ ] Enqueue notification event for customer with delta breakdown

- [ ] **TASK-307**: Dynamic Email Template Engine with TinyMCE
  - [ ] Create `EmailTemplate` model with placeholders JSON schema
  - [ ] Implement variable replacement engine (`{{customer_name}}`, `{{order_id}}`, etc.)
  - [ ] Seed base templates (`order_confirmed`, `order_item_unavailable`, `ticket_replied`)

---

## Phase 4: Async Task Worker, Scheduling & Resilience

- [ ] **TASK-401**: RabbitMQ & Celery Architecture Setup
  - [ ] Celery app initialization with RabbitMQ broker and Redis result backend
  - [ ] Task retry policy: exponential backoff with jitter (max 5 retries)
  - [ ] Dead Letter Queue (DLQ) configuration for unrecoverable failures

- [ ] **TASK-402**: Background Notification & SMS Worker
  - [ ] `send_otp_sms_task` with automatic retries on provider failure
  - [ ] Order confirmation notification task

- [ ] **TASK-403**: Celery Beat Scheduled Crons
  - [ ] Periodic task (every 5 min): auto-cancel orders stuck in `PAYMENT_PENDING` > 15 min and release reserved stock
  - [ ] Daily cleanup task: prune expired OTP keys, temp uploads, stale carts
  - [ ] Scheduled precomputation task for `ProductAvailabilitySummary`

- [ ] **TASK-404**: Fulfillment Queue, Email & Subscription Workers
  - [ ] `process_fulfillment_queue_task` (runs in `order_fulfillment` queue)
  - [ ] `dispatch_transactional_email_task` (renders TinyMCE templates and sends via SMTP)
  - [ ] `notify_stock_subscribers_task` (alerts users when back-in-stock or price drop triggers)

---

## Phase 5: Custom Next.js Admin Panel (RBAC)

- [x] **TASK-501**: Admin Portal Shell & Authentication Guards
  - [x] Build alongside identity/auth in Phase 1, before additional model slices; Phase 5 completes specialist workflows, not initial CRUD
  - [x] Dedicated `/admin` route layout with sidebar navigation
  - [x] Server-side Next.js route checks and backend role/object permissions; middleware is supplemental, never sole authorization
  - [x] Controlled staff-account bootstrap, identity management screens, loading/error/empty states and keyboard/mobile navigation; no Django admin fallback

- [ ] **TASK-502**: Product Manager Dashboard
  - [ ] Product and category CRUD data table
  - [ ] Availability window and discount configuration forms
  - [ ] Bulk stock and price adjustment interface

- [ ] **TASK-503**: Operator Order Fulfillment & Verification Console
  - [ ] Live order table filtered by status
  - [ ] Phone verification dialog (`CHECKING` queue) to log customer calls and confirm addresses
  - [ ] Status transition controls (`PROCESSING -> SHIPPED -> DELIVERED`)

- [ ] **TASK-504**: Auditor Read-Only Reporting Dashboard
  - [ ] Comprehensive analytics and read-only views across catalog, customers, and orders
  - [ ] Mutation buttons disabled/hidden for Auditor role
  - [ ] API rejects Auditor mutations even through direct requests; UI visibility alone is not authorization

- [ ] **TASK-505**: Support Ticket Operations Desk
  - [ ] Support tickets datatable filtered by priority, status, and linked order
  - [ ] Real-time conversation thread with internal notes and canned replies

- [ ] **TASK-506**: Review Moderation & Store Policy Manager
  - [ ] Product review approval / rejection queue
  - [ ] Store policy markdown editor (`StorePolicy`) generating vector embeddings for AI RAG

- [ ] **TASK-507**: TinyMCE Visual Email Template Designer
  - [ ] Rich-text TinyMCE editor integrated into admin panel
  - [ ] Placeholder chip inserter and live preview renderer with sample data

---

## Phase 6: Practical AI Enhancements

- [ ] **TASK-601**: Semantic Product Search with pgvector
  - [ ] Generate product text embeddings on create/update
  - [ ] Hybrid search endpoint combining PostgreSQL Full-Text Search with cosine similarity vector search

- [ ] **TASK-602**: Admin 1-Click Catalog Auto-Enricher
  - [ ] Admin panel action: Send product title + bullet attributes to LLM
  - [ ] Receive SEO meta title, Persian description, English description, and recommended category tags

- [ ] **TASK-603**: Grounded AI Support Assistant with Policy RAG
  - [ ] Storefront floating chat widget interface
  - [ ] Backend RAG endpoint: embeds user query, retrieves top-k `StorePolicy` chunks from pgvector
  - [ ] Generates friendly, grounded responses with strict policy guardrails
  - [ ] Automatic fallback: 1-click conversion of chat session into human support `Ticket`

---

## Phase 7: Quality Assurance, Hardening & Deployment

- [ ] **TASK-701**: Unit Test Coverage & TDD Quality Gate
  - [ ] Pytest unit tests for isolated availability rules, discounts/coupons, order transitions, and template substitution; include boundary and failure cases
  - [ ] Vitest unit tests for client validation/state logic and Three.js scene/material/disposal behavior
  - [ ] Preserve existing DB-backed model tests as integration coverage under TASK-705, not isolated unit coverage
  - [ ] Enforce existing minimum 85% backend coverage target across unit/integration tests; add client coverage reporting and set an explicit threshold
  - [ ] Add CI gates for unit/integration tests, coverage, lint, and typecheck; coverage alone does not prove correctness

- [ ] **TASK-705**: Integration Test Coverage (after TASK-005; extend with each feature)
  - [ ] DRF API tests for validation, authentication, RBAC, ownership boundaries, and persisted responses
  - [ ] PostgreSQL model constraints, soft-delete/cascade behavior, JSONB/pgvector paths, rollback, and concurrent checkout with real transactions (exactly one winner for last stock item)
  - [ ] Real Redis tests for OTP TTL/single-use/rate limits, cart merge, payment locks, and callback idempotency
  - [ ] Availability summary invalidation and worker retry/idempotency tests; exercise real broker/worker for delivery behavior rather than relying only on Celery eager mode
  - [ ] Presigned upload policy and test storage integration; payment/refund/SMS/email provider boundaries use controlled test adapters
  - [ ] Acceptance: isolated fixtures and cleanup, reproducible success/failure cases, no production side effects

- [ ] **TASK-702**: Playwright End-to-End Browser Testing (after TASK-005; extend with each journey)
  - [ ] Run real browser against running Next.js and Django with seeded isolated services, not a mocked catalog/checkout API
  - [ ] E2E purchase flow: Browse -> Add to Cart -> OTP Login -> Address Select -> Coupon -> Checkout -> Test Gateway Callback; assert persisted order outcome
  - [ ] E2E scored constraint: Verify purchase rejection outside time window
  - [ ] E2E RBAC boundary tests: Verify access denial across staff roles, including direct navigation and API denial
  - [ ] Persian/English RTL/LTR, localized values/dates, mobile layout, and keyboard-accessible critical controls
  - [ ] Three.js load/controls/reset, unsupported WebGL, lost context/retry, and close/reopen (coordinate with TASK-3D-006)
  - [ ] CI browser gate with traces/screenshots on failure; document seeds, startup, and cleanup; manual smoke checks do not complete this task

- [x] **TASK-704**: Resolve Client Dependency Audit Findings
  - [x] Review `npm --prefix client audit` findings affecting existing Next.js/PostCSS and Vitest dependencies
  - [x] Upgrade Vitest and PostCSS with scoped compatibility overrides; retain Next.js 15, verify clean Docker install and lockfile
  - [x] Re-run tests, typecheck, lint, build and browser smoke checks; audit reports 0 vulnerabilities

- [ ] **TASK-703**: Production Dockerization & Hardening
  - [ ] Multi-stage Dockerfiles for frontend, backend API, and Celery worker
  - [ ] NGINX reverse proxy with TLS, security headers, and compression
  - [ ] Locust load test verifying 500 RPM checkout performance

- [x] **TASK-INFRA-ENV**: Centralize local configuration in root `.env` for Compose, Django, and public frontend settings.

- [x] **TASK-CLIENT-CHUNKS**: Isolate development output from production to prevent missing JavaScript chunks.

- [x] **TASK-DEV-WORKFLOW**: Run Next.js with hot reload on port 3000 alongside Docker infrastructure; verify static assets and live changes.

- [x] **TASK-DEV-RUNNER**: Install backend environment and run frontend/backend together with verified health endpoints. Runner uses server/.venv; dependencies installed, migrations applied, frontend and backend started together.

- [x] **TASK-DOCKER-APPS**: Containerize frontend/backend development with source watch, isolated dependencies, health checks, and documented startup.
