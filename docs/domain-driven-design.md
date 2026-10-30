# Domain-driven design for this shop

## Decision and scope

Use pragmatic domain-driven design (DDD) for new backend features. DDD starts with understanding business behavior and using its language in code; it is not a framework, directory template, or requirement for microservices.

Keep one modular Django backend and shared PostgreSQL database, plus existing infrastructure and Next.js client. Only core shared models and health endpoints currently exist in the backend. Context/app names and methods below are proposed targets, not implemented symbols. Introduce a module when its first use case needs it; do not generate empty layers or rewrite `BaseModel` to demonstrate DDD.

Existing requirements and ERD remain business specifications. This guide assigns ownership and implementation conventions; unresolved policy conflicts require TASK-007, not an invented rule.

## Concepts through this project's language

| Concept | Meaning | Shop example |
| --- | --- | --- |
| Domain | Business problem being modeled | Selling products under pricing, availability, payment, and fulfillment rules |
| Ubiquitous language | Shared precise vocabulary in discussion, tests, and code | Reservation, availability window, payment confirmation, order adjustment |
| Bounded context | Boundary within which a model and its terms have a specific meaning | Catalog describes a product; ordering preserves the purchased title/price snapshot |
| Entity | Object identified over time, despite changed attributes | Product or order identified by UUID |
| Value object | Value defined by its contents, without its own identity | Validated money amount/currency or availability interval; introduce only when behavior/validation warrants a type |
| Aggregate / root | Small consistency boundary; root controls changes to its dependent state | Order controls its order items, adjustments, totals, and allowed transitions |
| Invariant | Business rule that must remain true after an operation | Stock never becomes negative; a payment replay does not fulfill twice |
| Domain service | Business decision not naturally owned by one entity | Availability calculation across schedule, window, and lead-time inputs |
| Application service | Coordinates a complete use case and its I/O | Checkout loads data, locks stock, invokes policies, saves order, and schedules follow-up |
| Domain event | Fact about something that already happened | Payment confirmed; use explicit calls initially, not an event bus for every change |

DDD has two useful scales: **strategic design** chooses contexts, ownership, and language; **tactical design** chooses entities, value objects, aggregates, and services where needed. Start with strategic clarity. Simple CRUD can remain simple Django CRUD.

## Initial context map and task ownership

These are logical boundaries, not separate deployments, schemas, or necessarily one app per row.

| Context / proposed Django app | Owns | Existing task families |
| --- | --- | --- |
| Identity & customers / `identity` | User, role, customer profile, address, authentication policy | TASK-102–105 |
| Shop configuration / `shop` | Singleton ShopSettings: localized shop identity, landing/link/contact/footer content and metadata; later About content | TASK-108–110 |
| Catalog / `catalog` | Category/product descriptions, specifications, base pricing, product/category discounts, schedules and availability rules, inventory operations; reviews, saved products and subscriptions initially remain local modules | TASK-106, TASK-201–204, TASK-206–208, TASK-601–602 |
| Ordering / `orders` | Cart/checkout coordination, coupons, orders/items/snapshots, adjustments/history, operator verification and fulfillment transitions | TASK-301–304, TASK-306 |
| Payments / `payments` | Gateway translation, callback authenticity/idempotency and payment/refund coordination; ordering owns authoritative order state changes | TASK-305; payment/refund portions of TASK-306 |
| Support / `support` | Ticket/message ownership, store policies and grounded support conversation; obtains order/customer facts through explicit reads | TASK-107, TASK-505–506, TASK-603 |
| Media / `media` | Approved upload/preview asset contracts and presigning; no product price/availability logic | TASK-205, TASK-3D-003 |
| Notifications / `notifications` | Email templates, provider adapters and message delivery; callers decide when business events warrant notification | TASK-307, TASK-402, TASK-404 |

Admin tasks TASK-501–507 provide Next.js + DRF interfaces to these contexts, not a second domain model or Django admin. Deliver permitted staff operations alongside every model; build shell during identity/auth, not only Phase 5. Immutable audit/derived records use safe actions/read-only views. [Admin/settings contract](./admin-and-shop-settings.md) defines ShopSettings ownership and singleton rules. Celery tasks TASK-401–404 call owning use cases. Three.js is presentation: preview failure must never change purchase eligibility or payment state.

Checkout coordinates identity/address reads, catalog availability/pricing/inventory operations, and ordering-owned persistence. Payments calls an ordering use case for a verified payment result. Support reads order facts without mutating order internals. Notifications consumes explicit after-commit calls. Keep these call paths one-way; avoid circular imports and hidden signal choreography.

Use owning context's public use-case functions for cross-context writes. Controlled read queries and foreign keys are acceptable within this shared-DB monolith; they do not imply ownership of another context's lifecycle. Cross-context foreign keys need explicit deletion behavior—do not let `BaseModel` cascade delete paid orders or audit history when an account/product is removed. Order items retain title, unit price, and address snapshots even when live catalog/customer data changes.

## Minimal Django shape

For the first real feature in a context, keep normal `models.py` for persisted entities/constraints, `services.py` for application use cases, and `serializers.py` / `views.py` for API contracts and dispatch. Add `policies.py` only when a pure business calculation needs separation. Split `services.py` into a `services/` package only when size warrants it. These are conventions, not files to create now.

- Django model methods may protect local entity/aggregate state, such as a legal transition. Do not create a second ORM-independent entity class for every Django model.
- Persisted domain entities inherit existing `apps.core.models.BaseModel` and keep translated metadata. Simple value objects do not inherit it or require DB tables. Framework-owned/auth-specific inheritance must be reconciled before defining the custom user model, not forced into conflicting base classes.
- Domain policies accept explicit values and time, return a decision/result, and avoid requests, serializers, SQL, Redis, Celery, and provider calls. Extract only meaningful behavior; do not invent a value-object class for every field.
- Application services own loading, authorization at the reusable use-case boundary, transactions, locking, calling domain behavior, persistence, and external scheduling. They are not pure functions. Views retain transport/authentication and input validation; permission checks must also hold when workers or another API invoke the use case.
- Celery task wrappers call the same application services as APIs. No duplicated business rules in views, serializers, admin actions, tasks, or Three.js code.
- Use ORM/querysets directly for persistence; DB constraints reinforce invariants where possible. Avoid generic repositories, unit-of-work wrappers around `transaction.atomic()`, speculative interfaces, and domain-wide dependency injection frameworks.
- Keep `apps.core` limited to genuinely shared technical primitives. Do not turn it into a home for checkout, pricing, or unrelated domain utilities.

## Invariants and consistency boundaries

| Boundary | Required invariant / enforcement |
| --- | --- |
| Catalog inventory | Reservation/change runs under `transaction.atomic()` and row locks via `select_for_update()`; no negative stock; lock multiple products in deterministic order |
| Order aggregate | Child mutations and total/transition changes go through owning use case; persist consistent snapshots and audit records atomically |
| Availability | One authoritative policy; checkout rechecks relevant current rules rather than trusting stale display summaries; schedule/window mutation updates or invalidates `ProductAvailabilitySummary` |
| Pricing/coupons | Authoritative server calculation with defined currency/rounding/precedence; validate expiry and applicable usage limits atomically; never trust client totals |
| Payment result | Verify provider result and bind token, amount, and order; acquire existing Redis atomic callback lock before mutation; persist durable idempotency/transition protection because a Redis lock alone does not survive expiry, restart, or all retries |
| Customer/support data | Identity and ownership/role checks apply to every use-case entry point, not only hidden UI buttons |

A bounded context can contain several aggregates. A whole catalog is not one aggregate; products, categories, and rules must not load as one giant object graph. An order may include its line-item mutation boundary, but not every customer, product, and payment object it references.

DDD does not prohibit a cross-aggregate transaction. This monolith needs atomic checkout across inventory and ordering state in shared PostgreSQL. The checkout application service owns that transaction and invokes catalog-owned inventory behavior without creating circular dependencies. Do not replace this safety requirement with eventual consistency merely to follow a pattern.

Keep external gateway/network calls outside long-held stock/DB locks. Persist intent and recoverable state, then perform provider work with idempotent retries. The exact reservation/commit/release timing is unresolved and must be specified in TASK-007 before implementation.

## Events without unnecessary machinery

Start with explicit application-service calls. Dispatch non-critical notification work with `transaction.on_commit()` so rolled-back writes do not send successful-order messages. Its callback is not durable delivery: a process/broker failure after commit can still lose work. Payment, refund, entitlement, or fulfillment side effects needing guaranteed eventual delivery require a durable record/reconciliation or transactional outbox with idempotent consumers before production. Add that machinery only for a concrete delivery requirement; RabbitMQ alone does not make DB writes and messages atomic.

Do not introduce event sourcing, CQRS infrastructure, microservices, or a generic event bus to claim DDD. Existing availability summaries are useful read optimizations, not a reason to duplicate the entire write model.

## Domain questions to resolve (TASK-007)

Storefront describes digital PBR materials/shaders and instant downloads; original specification also requires physical stock, delivery addresses, shipping, store-hour constraints, and phone verification. These are not automatically the same business model. Keep existing scored requirements until explicitly revised.

Before TASK-201 / TASK-301–306:

- Are products physical, digital, or mixed? Does stock mean physical quantity, limited licenses, or something else? Which products use availability windows and lead times?
- For digital products, what payment state grants access, what license is purchased, and how do refunds affect download entitlements? No entitlement feature exists yet; do not expose paid source files as public preview assets.
- Which price unit is canonical (Toman, Rial, or cents), what rounding is required, and how do category/product discounts and coupons combine?
- What store timezone, day/calendar convention, and inclusive/exclusive availability boundaries apply?
- What is canonical payment versus fulfillment state machine? Existing combined lifecycle labels must be reconciled with separate fields. When exactly is stock reserved, committed, released, or restored, and which retries must be harmless?

Record decisions with worked examples and update requirements/ERD; leave unresolved answers explicit rather than guessing.

## Feature workflow and tests

1. Name the owning context, command/use case, business terms, and invariants before creating tables/endpoints.
2. Write examples with expected outcomes. For availability: an order just inside versus just outside an approved window. Agree precise boundaries before asserting timestamps.
3. Write failing unit tests for pure decisions, then minimal domain logic. Add PostgreSQL/Redis integration tests for persistence, locks, rollback, permissions, and retries.
4. Expose the application use case through a thin API and its permitted Next.js staff screen/actions in the same model slice; exercise customer/staff journeys with Playwright. No Django admin shortcut or unsafe generic CRUD for audit/derived records.
5. Update glossary/decisions and `tasks.md`; ship one vertical slice, not empty folders for future contexts.

Unit tests prove policies and transitions. Integration tests prove real constraints, transactions and infrastructure boundaries. E2E tests prove customer/staff journeys. None substitutes for the others; follow existing test requirements and TASK-005 / TASK-701 / TASK-705 / TASK-702.

Learning order: vocabulary and contexts now; identity use case next; availability/discount policies when catalog work begins; checkout aggregate/transaction boundaries before payment/fulfillment. Prefer a small working example over architecture boilerplate.
