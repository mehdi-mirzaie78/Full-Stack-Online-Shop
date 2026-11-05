# Identity and first staff operations

Implemented: named phone-based users, role/direct identity capabilities, password and
Redis OTP sign-in, JWT cookie sessions and revocation, `/login`, the protected
`/admin/users` workspace, and `/admin/permissions`. CustomerProfile and
Address are still planned under TASK-102/104/105; no catalog/checkout policies are
introduced here.

## Running and delivery

Run `server/.venv/bin/python server/manage.py migrate` after updating. Migrations add
identity tables and constraints without dropping the old auth tables or migration
history. The initial migration refuses to continue if `auth_user` has any rows:
such installations need an explicit account/data migration before switching users.
The inspected local development database had zero legacy users.

Bootstrap a real staff identity with the existing Django command, not a public API:

```sh
server/.venv/bin/python server/manage.py createsuperuser --phone +989121234567
```

This creates a SUPERADMIN. The password is hashed by Django; the browser login supports both password and OTP. No account can register its own staff role.
The protected staff editor can create users and change their permitted access.

**Real SMS delivery is deliberately unconfigured.** Normal OTP requests return 503 unless explicit DEBUG-only Redis delivery is enabled for manual testing. Real SMS still needs a provider. No production code logs,
returns, or exposes verification codes. Isolated test settings enable the test fake
sender; it writes a short-lived synthetic message to the dedicated test Redis.
`test_identity seed/code/reset` is a CLI browser fixture and refuses normal settings.
Do not enable test settings for a live deployment. A provider adapter and its failure
handling will be implemented once the provider is selected.

## Contracts and boundaries

Phones use canonical international form: `+` then 8–15 digits, with a nonzero country
prefix. Local numbers are rejected rather than silently interpreted as one country.
Product type and stock policy are independent of account identity.

- `GET /api/v1/auth/csrf` establishes the CSRF cookie and returns a masked CSRF token.
- `POST /api/v1/auth/otp/request`: `{phone}`, six cryptographic digits, 120s TTL.
- `POST /api/v1/auth/otp/verify`: `{phone, code}`, atomic consume and CUSTOMER signup.
- `POST /api/v1/auth/refresh`: rotates the HTTP-only refresh cookie.
- `POST /api/v1/auth/logout`: revokes the session and clears auth cookies.
- `GET /api/v1/auth/me`: explicit safe account projection.
- `GET/POST /api/v1/staff/users`, `GET/PATCH /api/v1/staff/users/{uuid}`:
  SUPERADMIN management; AUDITOR read-only. Other roles are denied. List search
  filters phone numbers and paginates 25 records. Archiving/restoring is an explicit
  `is_deleted` edit; hard deletion has no endpoint. An administrator cannot alter their
  own role/activation/archive state through this editor; another administrator must
  perform that change. Staff mutations lock administrators in deterministic order.
- `POST /api/v1/staff/sessions/{uuid}/revoke`: SUPERADMIN only. Sessions are inspected
  through user detail, without token digests or raw JWTs, and have no general CRUD API.

OTP request limiting is one Redis Lua operation across phone and IP: at most three
requests per sliding ten-minute window. Verification is single-use under concurrency;
five wrong attempts consume a challenge. Expired, invalid and replayed codes fail.
Redis keys and OTP digests use a keyed hash; verification codes are never PostgreSQL
records. The current IP input is the direct peer (`REMOTE_ADDR`), never an untrusted
forwarding header. A production reverse proxy must establish a trusted client-IP
policy before public rollout; otherwise proxied clients share a request budget.

Access JWTs expire after 15 minutes; sessions/refresh tokens have an absolute seven-day
expiry. `JWT_SECRET_KEY` signs HS256 tokens with explicit issuer/audience/type claims.
Only a current refresh digest is stored in PostgreSQL. Reusing a rotated refresh token
revokes the session durably. Access checks load current session/user state so revocation,
archiving and deactivation take effect without waiting for JWT expiry. Browser Web Locks
serialize refresh across tabs when supported; same-tab refresh requests share a promise.
Browsers without Web Locks retain replay protection but simultaneous cross-tab refresh
can require signing in again.

JWT cookies are HTTP-only, SameSite=Lax, and Secure outside Django DEBUG mode. Write
requests require CSRF checks, including unauthenticated OTP verification and refresh;
the browser client establishes a CSRF token before writes. API/browser origins must be
same-site for these cookies, and explicitly allowed via CORS and CSRF trusted origins.
Set browser API URL and trusted origins together. Tokens are never put in browser storage. Identity responses are private/no-store and vary by Cookie.
The login page can continue an existing session (including refresh) or request a code.
The Next.js staff layout/pages check identity server-side, with repeated authorization
at backend use-case boundaries. Hiding staff navigation is not authorization.

## Verification

Use the [isolated test commands](./testing.md). The managed browser runner seeds only
synthetic superadmin/auditor/customer identities into its fresh test DB. Each identity
browser test clears its dedicated Redis before requesting a synthetic code. Codes are
read by the test-only CLI, not an HTTP backdoor. Browser coverage includes staff create,
edit/archive/restore/logout, auditor mutation denial, customer route denial, mobile and
keyboard interaction, Persian/English controls, and session recovery through refresh.

Normal client type checks generate current Next route types before TSC. Browser builds
use `tsconfig.test.json` and `.next-test` types so stale development/production route
validators cannot collide with test build types.

## Manual development sign-in

Enable `DEV_SMS_REDIS=True` in the ignored root `.env` with `DEBUG=True`, then restart
Django. Request a code from `/login` and read its short-lived Redis mailbox locally:

```sh
server/.venv/bin/python server/manage.py dev_sms +989121234567
```

The code expires after 120 seconds. Production (`DEBUG=False`) cannot enable this
sender. No codes are logged or returned by HTTP. Real delivery still needs a provider.
Authenticated visitors to `/login` automatically recover/refresh their session and
redirect to the storefront or staff workspace; there is no manual session button.
Forms use Zod with `noValidate`, and the navbar toggle owns the shared page language.

## Password sign-in and navbar

`POST /api/v1/auth/password` accepts `{phone, password}` and uses Django's password
hasher/authentication backend. Invalid, inactive and archived accounts get the same
failure response. Password and OTP requests share the phone/IP attempt budget; CSRF,
HTTP-only JWT cookies, rotation and revocation are identical for both methods.
Passwords are never returned by the API. Staff accounts can be bootstrapped with
`createsuperuser`; OTP-created accounts have unusable passwords until explicitly set by a superadmin in the protected staff editor or through Django’s management commands. There is no public password setter.

The login form offers both methods and uses Zod character limits (9–16 total characters
including `+`) plus international phone syntax. Native validation remains disabled.
Navigation uses shadcn Base UI components and a direction provider for RTL interaction;
the header's outer grid stays LTR so brand/language-control anchors do not swap sides.
The previous server-status decoration has been removed.


## Staff passwords and permission management

`POST /api/v1/staff/users` and `PATCH /api/v1/staff/users/{id}` accept an optional,
write-only `password` from an active SUPERADMIN whose Django `is_superuser` flag is
also true. Omission preserves an existing password (or creates an unusable password);
empty values are rejected. Passwords retain whitespace, have a 128-character maximum,
and pass the configured Django password validators before hashing. No password/hash
is serialized. Setting a password revokes all existing access/refresh sessions for the
target, including the current session when editing oneself. The Next.js dialog/detail
editor supplies confirmation locally; confirmation is never stored or sent to the API.

Identity owns four assignable capability codenames: `view_user`, `add_user`,
`change_user`, and `revoke_loginsession`. They are stored as Django auth Permission
records on the identity User content type. Role grants use framework-owned Group
records named `identity-role:{ROLE}`; individual additions use User.user_permissions.
The business `User.role` selects the role group directly; arbitrary `User.groups`
membership does not grant application access. `identity.access.effective_permissions`
is the application authorization owner, evaluates current database grants without
per-user permission caches, and supplies the read-only `permissions` user projection.
This is distinct from Django ModelBackend's generic `has_perm` group lookup.

- SUPERADMIN has fixed full identity access; only SUPERADMIN can assign staff roles,
  change permissions, set passwords, or mutate staff accounts.
- OPERATOR and PRODUCT_MANAGER start with no identity grants. A superadmin can grant
  view plus create/edit/revoke capabilities directly or through their role.
  Delegated mutations are restricted to CUSTOMER accounts and cannot assign staff roles.
- AUDITOR starts with `view_user`. Its effective grants are always read-only, even
  if an out-of-band auth record incorrectly grants a write capability.
- CUSTOMER has no staff capabilities, regardless of direct auth records. Customer and
  superadmin access is fixed. Individual grants are additive; clearing a direct grant
  does not remove access inherited from a role. Every delegated write also needs view.

The migration initializes role groups and the initial auditor view grant. It does not
change any existing account passwords. Framework permission/group tables are reused;
there is no new generic Role model or Django admin registration.

Superadmin-only endpoints:

| Method/path | Contract |
| --- | --- |
| `GET staff/access` | Supported capability catalog and all role grants |
| `PATCH staff/roles/{ROLE}/permissions` | Replace an editable role's identity grants |
| `GET staff/users/{id}/permissions` | Direct, inherited and effective grants plus role |
| `PATCH staff/users/{id}/permissions` | Replace additional grants for an editable staff account |

Permission PATCH bodies require `permissions` and `expected_permissions` arrays of
supported, distinct codenames. Expected grants must match current stored grants;
a stale edit returns 409 and changes nothing. Unknown capabilities, duplicates,
unsupported roles and auditor writes are rejected. Unrelated Django permissions are
preserved. All mutations retain cookie/CSRF enforcement, lock authorization changes
with existing staff account mutations, and recheck the actor from the database inside
the transaction. Role/direct changes affect the next authenticated request; the
admin UI refreshes its permissions on navigation/reload.

Next.js `/admin/permissions` manages role grants; each `/admin/users/{id}` offers
additional individual grants and shows inherited/effective access. Password and
permission controls are never available to delegated staff or auditors. These UI
checks supplement API authorization and are not its security boundary.


## User names and editing sections

User owns `first_name` and `last_name` (up to 150 characters each). Staff account
creation requires both fields; supplied values are trimmed and must not be blank.
Staff PATCH supports partial updates: omitted names remain unchanged, while explicitly
blank/overlong names are rejected. The application service repeats these requirements
for non-HTTP callers. Next.js creation and account editing require both names and show
the saved name in the users table. Django `createsuperuser` prompts for both names.

Migration 0005 adds non-null name columns with empty defaults for existing rows. No
names are invented or existing accounts disabled. Existing accounts with unknown names
show “Name needed” in the list, and staff can complete their details. As explicitly
selected for this slice, phone-only OTP registration/login remains unchanged, so OTP
accounts may also need names completed later. Database fields permit these legacy/OTP
empty values; staff creation validation supplies the stronger admin contract.

User filtering ignores superseded responses so a slow earlier search cannot replace
the current results. Session revocation refreshes session data without replacing
unsaved account fields in another tab. An explicit account reload refreshes those
fields from the API.

The user detail editor has Account, Permissions (superadmin only), and Login sessions
tabs. Hidden panels remain mounted so switching tabs preserves account and permission
drafts. Tab controls use Base UI keyboard behavior and direction-aware navigation for
Persian/English. Auditors can inspect Account/Login sessions with disabled account
controls; API role/object authorization remains authoritative for every mutation.
