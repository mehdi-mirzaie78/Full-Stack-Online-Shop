# Infrastructure instructions

Inherits [root rules](../AGENTS.md); read [testing guide](../docs/development/testing.md) for isolated test services.

- Root config: `.env` (ignored), template `.env.example`. Never print/read/commit secrets. Only `NEXT_PUBLIC_` values are safe for browser exposure.
- From root: `npm run infra:up` or `docker compose --env-file .env -f infra/docker-compose.yml up -d --wait`; `npm run infra:status` for service state.
- Services: PostgreSQL 16 + pgvector :5432, Redis 7 :6379, RabbitMQ 3.13 :5672 / management :15672, SeaweedFS S3 :9000. MinIO console :9001 is no longer provided.
- Use healthchecks and verify actual service operations after infrastructure changes. Keep local/prod/test configuration separated; no SQLite fallback.
- PostgreSQL/RabbitMQ credentials initialize new volumes; changing config does not update existing users. Never reset/delete volumes or migrate storage implicitly.
- Media clients upload directly using S3 presigned URLs. No media proxy/streaming through Django. Test buckets/Redis namespaces/DBs must not overlap production.
- Keep changes small and explicit; reuse root runners, no duplicate configuration sources or extra services without need. Preserve TLS, cookie/CSRF boundaries, and reverse-proxy route isolation: Next.js owns `/admin`; Django owns protected APIs, not a fallback admin UI.

- Full application development: `npm run docker:dev` merges `compose.dev.yml` and enables Compose Watch; `docker:up` is detached without watch. Do not use these development servers for production.
