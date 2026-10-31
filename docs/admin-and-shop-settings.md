# Custom administration and shop configuration

## Delivery policy

Next.js `/admin` backed by protected DRF APIs is the only staff panel. Do not use Django admin UI, registrations, or ModelAdmin as a shortcut. Django auth, groups/permissions, authentication middleware, and management commands remain available. Removing admin URLs/app does not delete existing DB tables or migration history.

Every new persisted business model is a vertical slice: model/migration, owning use cases, explicit serializers/permissions, usable staff screen, and relevant unit/integration/E2E tests. Build the minimum authenticated shell after identity/auth and before the next managed model. Phase 5 groups specialist workflows and polish; it is not permission to postpone all staff UI.

## Model management checklist

- Define allowed operations per role/model. Mutable records need list/search/pagination, detail, create/edit and delete/archive/restore where safe. Include relationship selectors and meaningful validation, loading, empty, error and permission-denied states.
- API enforces field/object authorization and business rules even for direct requests. UI mirrors permissions but is not the security boundary. Cookie-authenticated writes retain CSRF/origin protections; never send credentials through public settings.
- Call existing application services; no duplicated admin business logic, generic raw SQL editor, automatic serializer-all-fields, or UI component coupled to Django admin.
- Aggregate children are managed through their owning aggregate. Audit history/payment records are inspectable but immutable except named business operations. Derived summaries are read-only with controlled recomputation. Stock/order transitions are explicit actions, never arbitrary field edits bypassing locks/state rules. Abstract BaseModel needs no screen.
- Destructive actions require confirmation and defined soft-delete/restore/retention rules. Never delete paid-order/audit history through cascading account/product removal. Singleton settings is edit-only, with no normal delete/archive.
- Reuse small proven form/table pieces when duplication appears; keep model-specific sections composable. No metadata-driven universal admin framework required.

## ShopSettings singleton (planned, TASK-108)

One shop per deployment initially. Own it in proposed `shop` context, separate from technical `core`. No multi-tenancy system or page builder now. Model, APIs and staff screen below are a specification, not implemented functionality.

### Persistence and fields

Inherit UUID/timestamps from BaseModel. Add non-null `singleton_key` with default `1`, DB CHECK `singleton_key = 1`, and UNIQUE on that key, so even concurrent/bulk inserts cannot create another row. Seed one neutral editable record through data migration. Constraints guarantee at most one row; bootstrap plus denial of deletion maintains one during supported application operations, not against manual DBA deletion.

Require `is_deleted=False`, `deleted_at IS NULL`, and `is_active=True` with DB checks; reject ordinary deletion/hard deletion and archive APIs. No list/create/delete endpoints. Do not use `.first()`, `save()` override, or cache alone as singleton enforcement. Do not replace UUID primary key with integer just for singleton convenience. Use a row lock plus an expected revision value for edits; reject stale updates rather than silently overwriting another editor.

Initial typed fields, finalized with migration/API implementation:

| Content | Planned fields |
| --- | --- |
| Identity | `name_fa`, `name_en`, `tagline_fa`, `tagline_en`, `logo_url`, `favicon_url` |
| Landing | `hero_title_fa/en`, `hero_description_fa/en`, optional `hero_image_url`, `hero_cta_label_fa/en`, `hero_cta_url` |
| Contact | `contact_email`, `contact_phone`, `address_fa/en` |
| Navigation / social / footer | `navigation_links`, `social_links`, `footer_links`: bounded validated arrays of `{label_fa, label_en, url}`; `footer_text_fa/en` |
| Search metadata | `meta_title_fa/en`, `meta_description_fa/en`, optional `social_image_url` |
| Editing | monotonic `revision`, audit actor/change metadata managed server-side |

Use explicit fields for fixed content; JSONB only for bounded link lists, not arbitrary unvalidated settings. Names like `_fa/en` in this table mean separate locale fields, not literal slash-containing identifiers. Keep Persian/English fallback explicit: requested non-empty translation, other available translation, then neutral setup copy. Static interface translations stay in UI i18n, not this table. Feature/cart/inventory/pricing/provider configuration does not belong here. Keep structured fields bounded and typed, allow only safe relative routes or approved URL schemes, validate contacts, and reject scripts/unsafe markup. Images use approved media assets/presigned uploads; no server-side fetching of arbitrary URLs.

### API contract (proposed)

- `GET /api/v1/shop/settings/`: anonymous-safe allowlisted storefront projection; never internal actors, private settings, credentials, or provider keys.
- `GET /api/v1/admin/shop/settings/`: authorized staff detail with revision; initially SUPERADMIN writes and reads, AUDITOR read-only, other roles denied until explicit permission added.
- `PATCH /api/v1/admin/shop/settings/`: SUPERADMIN-only validated partial update with expected revision; conflict response on stale edit, transaction/row lock, audit record and revised representation. Unsupported methods return 405; read routes never create DB rows.
- Bootstrap must not require publicly writable setup endpoints. Staff account bootstrap uses a controlled management command/workflow after custom auth setup.

### Next.js configuration flow (TASK-109)

Staff editor at `/admin/shop` groups identity, landing, links/contact and metadata. Read safe API data server-side through a shared loader for layout/landing/metadata; avoid per-component duplicate fetches. Start uncached (`no-store`) for settings until a tested revalidation scheme is needed; ensure route/metadata caches cannot retain old branding. Save success appears only after API acceptance; refresh public view to verify persisted changes without redeploy. Explicit neutral setup/unavailable state on missing record/API failure, never a silent hardcoded brand.

Replace shop-specific `CYBER//STORE`, header badges, marketing copy, landing links/contact/footer and metadata with settings-driven content as that slice lands. Keep component design, fonts, UI translations, and catalog product data separate. Settings change must not rewrite product availability or claim backend health; health indicators need actual health data or should be removed.

About page is a later feature (TASK-110). Add localized title/body and publication semantics when building `/about`, with safe plain text/Markdown rendering and staff editor in same slice. Do not build arbitrary executable HTML or a generic CMS now.

## Acceptance

- Django admin route stays absent; new model cannot be marked complete while its allowed staff operations are missing.
- Singleton constraints hold for concurrent/bulk creation, immutable singleton fields, and deletion/deactivation attempts. Test bootstrap and missing-row recovery procedure separately.
- Authorization, field validation, stale-edit rejection and public allowlist verified with unit/integration checks.
- E2E: authorized staff saves branding/landing/link changes; reload public page and verify text, links, images and metadata; unauthorized roles cannot write. Verify Persian/English, keyboard/mobile, API failure, and no secrets in public response.
- Current state: Django admin disablement is small immediate cleanup; custom panel, ShopSettings table/migrations/API/editor and About remain pending tasks. No claim that dynamic branding works before TASK-108/109 pass.
