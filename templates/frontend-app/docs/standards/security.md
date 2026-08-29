# Security

The browser is hostile territory. Anything that runs there can be read and modified; anything it sends can be forged. Enforce on the server, render safely on the client.

## Secrets & environment

- Only variables prefixed `NEXT_PUBLIC_` are bundled to the client. Everything else is server-only **and must stay that way**: never re-export a server env value from a client module.
- `src/lib/env.ts` validates env with Zod into two objects: `serverEnv` (imports `server-only`) and `clientEnv` (`NEXT_PUBLIC_*` only). Nothing reads `process.env` directly. Build fails on missing vars.
- No secrets in the repo, `.env.example` contains keys with placeholder values only. `gitleaks` in pre-commit and CI.
- Modules that touch tokens, API keys, or the session import `'server-only'` at the top so a client import is a build error.

## Authentication & sessions

- Session token in an `HttpOnly; Secure; SameSite=Lax` cookie set by the auth server. Never in `localStorage`, never readable by JS.
- `src/lib/auth.ts`: `getSession()` (nullable) and `requireUser()` (redirects/throws). Both server-only.
- **Every Server Action and route handler calls `requireUser()` first** and checks authorization for the specific resource. Actions are public HTTP endpoints regardless of which button renders them.
- Middleware does a cheap "is there a valid session cookie" check to redirect unauthenticated users; it is **not** authorization. Pages and actions verify again.
- Never gate security on client state: hiding a button is UX; the action behind it must still refuse.
- Logout invalidates the session server-side and clears the cookie; then `router.refresh()`.

## Input handling

- Every Server Action and route handler parses input with Zod (`safeParse`). Unknown keys stripped (`.strict()` when the shape is closed). Bounds on strings (`max`), arrays (`max`), numbers (`min`/`max`).
- IDs validated as the expected format (UUID/prefixed) before use in a URL or query.
- Never build URLs by string concatenation with user input — `new URL()` + `searchParams.set`. Never build shell commands or file paths from input (route handlers included).
- `FormData` values are strings; coerce with `z.coerce`. Don't trust `hidden` inputs (price, userId) — recompute on the server.
- File uploads: validate MIME **and** magic bytes on the server, cap size, generate the stored filename server-side, upload to object storage via a signed URL — never write to the app filesystem.

## Output & XSS

- React escapes by default. The exceptions are yours to defend:
  - `dangerouslySetInnerHTML` only with content sanitized by `DOMPurify` (or `isomorphic-dompurify` on the server), with an allow-list config, and a comment saying where the HTML comes from. Reviewers reject unsanitized uses on sight.
  - `href`/`src` from user data: allow `https:` (and `mailto:` where intended) only. Reject `javascript:` and `data:` — validate with `new URL()` and check `protocol`.
  - Markdown from users renders through a sanitizing renderer (`rehype-sanitize`), never `marked` → raw HTML.
- Don't render secrets, tokens, or internal error details. `error.tsx` shows a generic message and the `digest`; the full error goes to the server log.
- JSON embedded in HTML (rare — prefer props): escape `<` as `<`.

## Content Security Policy & headers

Set in `next.config.ts` `headers()` (or middleware for nonce-based CSP):

- `Content-Security-Policy`: `default-src 'self'; script-src 'self' 'nonce-…' 'strict-dynamic'; img-src 'self' data: <cdn>; connect-src 'self' <api>; frame-ancestors 'none'; object-src 'none'; base-uri 'self'`. Every third-party script/host is an explicit, reviewed addition to the policy.
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
- `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` denying camera/mic/geolocation unless used.
- `next/script` with `nonce` when CSP uses nonces. No inline event handlers or `javascript:` URLs (CSP will block them anyway).

## CSRF, CORS, clickjacking

- Server Actions carry Next's origin check; keep `serverActions.allowedOrigins` tight. Route handlers that mutate check `Origin` against `serverEnv.APP_ORIGIN` and require `SameSite` cookies.
- No `Access-Control-Allow-Origin: *` on any route handler that reads cookies.
- `frame-ancestors 'none'` (above) unless the app is meant to be embedded — then list the embedders.

## PII

PII = anything that identifies a person: name, email, phone, street address, IP, government IDs, precise geolocation, free-text that may contain any of these. **Not** PII for our purposes: postal code, region/state/province, country, `isPoBox`.

- Render PII only where the screen's purpose is to show it. Don't put it in page titles, URLs, query strings, `localStorage`, analytics events, or error reports.
- Never log PII — client or server. `console.*` is lint-banned in app code; the server logger's redaction denylist is a backstop, not a strategy. Error-reporting SDK (Sentry etc.) has `beforeSend` scrubbing and `sendDefaultPii: false`.
- Forms with PII: `autoComplete` set correctly, no persistence of drafts to `localStorage` unless the product explicitly requires it (then encrypted and expiring).
- Screenshots in E2E tests never contain real PII — builders generate fake data.
- Third-party scripts (analytics, chat widgets, session replay) are a data-sharing decision, not a dev decision: require sign-off and mask inputs (`data-sensitive`, replay `maskAllInputs`).

## Dependencies

- `pnpm audit --prod` in CI; high/critical fail. Renovate keeps deps current; review changelogs for majors.
- No dependency that requires `eval`/`new Function` or `unsafe-eval` in CSP.
- Pin exact versions in `package.json` for anything that ships client-side code from a small maintainer.
- Verify a package's provenance/npm signatures for anything touching auth or payments.

## Rate limiting & abuse

- Server Actions and route handlers that send email/SMS, create records, or are expensive get rate-limited per user/IP at the edge or via the backend API. Don't rely on the button being disabled.
- Bot protection on public forms (signup, contact) via the platform's challenge, not a homegrown honeypot alone.

## Checklist (before marking an auth/input/rendering task done)

- [ ] `requireUser()` + resource authorization at the top of every new action/handler
- [ ] Zod parse on every input, bounds set
- [ ] No new `NEXT_PUBLIC_` var carrying anything sensitive
- [ ] No `dangerouslySetInnerHTML` / raw `href` from user data without sanitization/validation
- [ ] New third-party host added to CSP explicitly
- [ ] No PII in logs, URLs, analytics, storage
