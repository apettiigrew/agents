# Security

Defaults are secure; opting out is explicit and reviewed.

## Authentication & authorization

- Every route is protected by `JwtAuthGuard` registered globally. Public routes opt out with `@Public()` — the decorator name makes it greppable in review.
- JWTs: RS256, verified against the IdP's JWKS with caching. Never `HS256` with a shared secret in prod. Never disable `exp` checking.
- Authorization is enforced in the **service**, not the controller: `assertCanAccess(actor, resource)` before any read or mutation. Guards handle *who you are*; services handle *what you may do*.
- Tenant isolation: `tenantId` comes from the token, never from the request. Every repository query is tenant-scoped (see database.md). An E2E test per resource proves cross-tenant access returns `404` (not `403` — don't confirm existence).
- Service-to-service calls use short-lived machine tokens (client credentials), not shared API keys.

## Input handling

- Global `ValidationPipe` with `whitelist: true, forbidNonWhitelisted: true, transform: true`. Every body/query/param goes through a DTO.
- Bound everything: string `@MaxLength`, arrays `@ArrayMaxSize`, numbers `@Max`, page size ≤ 100, request body ≤ 1 MB (set at the HTTP server).
- IDs are validated as UUIDs before they reach a query.
- Never build SQL, shell commands, or file paths from user input by concatenation. `$queryRaw` tagged templates only; no `child_process` in request paths; file names are generated server-side.
- Deserialising untrusted JSON into class instances: `class-transformer` with `excludeExtraneousValues` — never `Object.assign(new Entity(), body)`.

## Output & data exposure

- Response DTOs only. Never return entities or Prisma models — they leak columns you'll add later.
- Error responses never include stack traces, SQL, or internal paths. The exception filter enforces this; don't bypass it.
- `404` for resources the caller can't see, not `403`.

## PII and logging

PII = anything that identifies a person: name, email, phone, street address, IP, government IDs, precise geolocation, free-text fields that may contain any of these. **Not** PII for our purposes: postal code, region/state/province, country, `isPoBox`.

- Never log PII. Log IDs and non-PII attributes. `logger.info({ orderId, destinationPostalCode })` — not the address.
- Never put PII in `AppException.context`, URL paths, query strings, or metrics labels.
- Redact at the logger: the `Logger` wrapper has a denylist of key names (`email`, `phone`, `address*`, `name`, `line1`, …). Adding a PII field to a DTO means adding its key to the denylist in the same MR.
- Retention: PII columns are enumerated in `docs/data-inventory.md` with a retention period and the job that enforces it. New PII column = update the inventory in the same MR.
- Test data: builders generate obviously fake PII (`test+<uuid>@example.com`). Never copy production rows into fixtures.

## Secrets

- No secrets in code, config files, Dockerfiles, or test fixtures. `gitleaks` runs in pre-commit and CI.
- Secrets arrive via environment from the secret manager. `config/schema.ts` marks them `secret: true` so they're redacted from the boot-time config dump.
- Rotate on any suspected exposure; don't debate whether it was "really" exposed.

## Dependencies

- `pnpm audit --audit-level=high` in CI; fails the build.
- Lockfile committed; `--frozen-lockfile` in CI.
- New runtime dependency: justify in the MR (why not the standard lib / existing dep), check maintenance status and license. Prefer zero-dependency libs for small needs.
- Renovate keeps deps current; security patches are merged within 48h.

## Transport & headers

- TLS terminated at the edge; the app still refuses `http://` callbacks in webhooks config.
- `helmet()` on. CORS allowlist from config — never `*` with credentials.
- Rate limiting via `@nestjs/throttler`, per tenant for authenticated routes, per IP for public ones.

## Webhooks & outbound calls

- Inbound webhooks: verify the HMAC signature before parsing the body; reject > 5 min clock skew; dedupe on event ID.
- Outbound HTTP: explicit timeouts (connect 2s, total 10s), bounded retries with jitter, circuit breaker for each upstream. No retries on non-idempotent calls without an idempotency key.

## Review checklist

- [ ] New route: is it intentionally `@Public()`? Is the service method authorising?
- [ ] New DTO field: bounded? Is it PII → denylist + inventory updated?
- [ ] New query: tenant-scoped?
- [ ] New log line: any PII?
- [ ] New dependency: justified?
