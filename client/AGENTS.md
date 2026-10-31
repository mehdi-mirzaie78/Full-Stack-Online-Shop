# Client instructions

Inherits [root rules](../AGENTS.md). Read [testing guide](../docs/development/testing.md) for feature verification and [admin/settings contract](../docs/admin-and-shop-settings.md) for staff/configuration work.

## Commands (inside client)

- `npm run dev` — Next.js Fast Refresh on :3000; `.next-dev` output.
- `npm run build` / `npm run start` — production `.next`; separate port if dev also runs.
- `npm run typecheck`, `npm run lint`, `npm run test`.
- `npx playwright test` is planned after TASK-005 installation/configuration; not a working E2E suite yet.

## UI and API boundaries

- Strict TypeScript, descriptive names, small cohesive components. Separate API I/O, domain decisions, and rendering; reuse established patterns without generating a universal form/table framework.
- Use Server Components for read-only data where appropriate; client components only for interaction/browser APIs. Validate API responses at trust boundaries. Backend remains authoritative for price, availability, permissions, and transitions.
- Staff panel lives at `/admin`, implemented with Next.js and protected DRF endpoints, never Django admin. Each new model ships permitted list/detail/forms/actions alongside backend work. Compose specific components so new custom panels remain easy to add; no raw-table editor bypassing business rules.
- Include loading, empty, validation, failure, and permission-denied states. Protect routes server-side and enforce permissions again in API; hiding buttons is not authorization. Preserve cookie/CSRF protections for authenticated writes.
- Use ShopSettings API for shop-specific branding, navigation, landing copy, contact/social/footer content, and metadata. Avoid hardcoded shop identity scattered in components. Product/stock data remains catalog-owned; credentials stay outside public settings. Missing configuration gets an explicit neutral setup state, not another shop's branding.

## Design, language, accessibility

- Preserve responsive layouts, keyboard navigation, focus visibility, contrast, and reduced-motion behavior.
- Persian `fa-IR` RTL and English `en-US` LTR; semantic `lang`/`dir` for mixed text. Self-hosted Vazirmatn for Persian and Manrope for English through `next/font/local`; preserve font licenses. Natural Persian letter spacing, readable line height, monospace only for technical values.
- Keep layout/design tokens separate from editable shop content; no arbitrary admin-supplied JavaScript/CSS or unsanitized HTML.

## Three.js learning components

- Follow [learning guide](../docs/threejs-learning.md) and TASK-3D-*; teach one concept per small change with experiment/check, not all future lessons at once.
- Native `three`, browser-only dynamic import, one opt-in viewer, static posters in grids. Text/prices/license/purchase controls remain HTML and work without WebGL.
- Render on demand, cap pixel ratio, dispose owned GPU resources/listeners/observers, verify Strict Mode. Do not force context loss on a canvas Strict Mode will reuse. No automatic motion by default; retain usable mobile scroll.
- Keyboard-accessible bilingual controls; unsupported WebGL/load/context loss must retain fallback and retry state. Preview assets are public, never paid source archives. Validate future asset URLs/types/sizes/external resources.
- No exact UE/HLSL/V-Ray/Corona compatibility claim. No React Three Fiber, Drei, physics, postprocessing, or shader framework without a concrete task.
