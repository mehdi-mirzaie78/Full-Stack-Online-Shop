# Project Implementation Tasks

Live task tracking matrix for Full-Stack Online Shop. Status marks: `[ ]` Pending, `[/]` In Progress, `[x]` Completed.

---

## Phase 0: Project Scaffolding & Infrastructure Foundations

- [ ] **TASK-001**: Git Repository Initialization & Structure Scaffolding
  - [x] Create `README.md`, `LICENSE` (MIT), `.gitignore`, `tasks.md`, and `AGENTS.md`
  - [x] Initialize git repo on `main` and create `develop` branch
  - [ ] Configure root `package.json` runner (`npm run dev`, `dev:client`, `dev:server`)
  - [ ] Establish repository folder structure (`/server`, `/client`, `/infra`)

- [ ] **TASK-002**: Docker Compose & Local Services Orchestration
  - [ ] Configure `docker-compose.yml` for PostgreSQL 16 (with `pgvector`), Redis 7, RabbitMQ 3.13 (management enabled), and MinIO
  - [ ] Configure environment variable templates (`.env.example` in `/server` and `/client`)
  - [ ] Verify healthchecks for all containerized dependencies

- [ ] **TASK-003**: Server API Boilerplate (Django REST Framework)
  - [ ] Initialize Django project in `/server` with dependency management
  - [ ] Install and configure djangorestframework, drf-spectacular, CORS headers, and PostgreSQL connection
  - [ ] Implement global healthcheck endpoints (`/api/health/`, `/api/health/db/`, `/api/health/redis/`)
  - [ ] Configure Ruff linter and formatter settings

- [ ] **TASK-004**: Client Boilerplate (Next.js 15)
  - [ ] Scaffold Next.js 15 App Router in `/client` with TypeScript and Tailwind CSS
  - [ ] Install and initialize shadcn/ui component library
  - [ ] Configure Biome / ESLint & Prettier
  - [ ] Setup initial RTL layout direction switch (`dir="rtl"` / `dir="ltr"`)

---

## Phase 1: Core Domain, Identity & Customer Module

- [ ] **TASK-101**: Abstract Base Models & Soft Delete Pattern
  - [ ] Create `BaseModel` (`id: UUID`, `created_at`, `updated_at`, `deleted_at`, `is_active`, `is_deleted`)
  - [ ] Implement `SoftDeleteManager` (`objects.all()` excludes soft-deleted records; `objects.all_with_deleted()` includes them)
  - [ ] Unit tests for soft-delete, restore, and cascade behavior

- [ ] **TASK-102**: Custom User & RBAC Model
  - [ ] Create custom `User` model using phone number as unique identifier
  - [ ] Add `Role` enum (`SUPERADMIN`, `PRODUCT_MANAGER`, `OPERATOR`, `AUDITOR`, `CUSTOMER`)
  - [ ] Create `CustomerProfile` (avatar, national code, age, gender) and `Address` (province, city, 10-digit postal code, body)
  - [ ] Model tests and migrations

- [ ] **TASK-103**: Redis-Backed OTP Engine & Sliding Rate Limiter
  - [ ] Create `POST /api/v1/auth/otp/request` endpoint (generates 6-digit cryptographic code, 120s Redis TTL)
  - [ ] Implement sliding window rate limit (max 3 requests per 10 minutes per IP/phone)
  - [ ] Create `POST /api/v1/auth/otp/verify` endpoint (atomic verification, single-use invalidation)
  - [ ] Issue JWT access + rotating refresh tokens

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

- [ ] **TASK-501**: Admin Portal Shell & Authentication Guards
  - [ ] Dedicated `/admin` route layout with sidebar navigation
  - [ ] Next.js middleware and backend permission classes enforcing role-based route access

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

- [ ] **TASK-701**: Test-Driven Development (TDD) Model & Service Suite
  - [ ] Complete Pytest unit and integration test suite with >85% code coverage
  - [ ] Test reporting and coverage enforcement

- [ ] **TASK-702**: Playwright End-to-End Browser Testing
  - [ ] E2E purchase flow: Browse -> Add to Cart -> OTP Login -> Address Select -> Checkout
  - [ ] E2E scored constraint: Verify purchase rejection outside time window
  - [ ] E2E RBAC boundary tests: Verify access denial across staff roles

- [ ] **TASK-703**: Production Dockerization & Hardening
  - [ ] Multi-stage Dockerfiles for frontend, backend API, and Celery worker
  - [ ] NGINX reverse proxy with TLS, security headers, and compression
  - [ ] Locust load test verifying 500 RPM checkout performance
