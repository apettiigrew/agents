# Next.js

App Router, React Server Components, Server Actions. Render on the server, ship the minimum JavaScript, cache deliberately.

## Server vs client components

- **Default is server.** No directive means Server Component. It can be `async`, read secrets, hit the DB/API, and ships zero JS.
- Add `'use client'` only when the component needs: `useState`/`useReducer`/`useEffect`, event handlers, browser APIs, or a client-only library. Put the directive on the **smallest leaf** that needs it.
- **Never** `'use client'` on `page.tsx`, `layout.tsx`, or `template.tsx`.
- Server Components can render Client Components and pass them props. Client Components cannot import Server Components — pass them as `children` instead:
  ```tsx
  // good: server data rendered inside a client shell
  <Collapsible>            {/* 'use client' */}
    <OrderDetails order={order} />   {/* server */}
  </Collapsible>
  ```
- Props crossing to a client component must be serializable: no functions (except Server Actions), no `Date` (send ISO strings), no class instances, no `Map`/`Set`.
- Async Client Components are invalid. If you wrote `async function` with `'use client'`, the fetch belongs in a parent Server Component or a TanStack Query hook.
- Import `'server-only'` at the top of any module that must never reach the browser (`queries.ts`, anything touching secrets). Import `'client-only'` for modules using `window` at import time.

## File conventions per route segment

| File | Purpose | Rule |
|------|---------|------|
| `page.tsx` | Route UI | Server Component; fetches and composes. ≤ ~40 lines |
| `layout.tsx` | Shared shell; does not re-render on navigation | Never fetch per-page data here |
| `loading.tsx` | Suspense fallback for the segment | Required wherever `page.tsx` awaits data. Use skeletons matching the final layout, not spinners |
| `error.tsx` | Error boundary (`'use client'`) | Required wherever `page.tsx` can throw. Show a retry (`reset()`) and a generic message; log the digest |
| `not-found.tsx` | 404 UI | Call `notFound()` from the page when the entity doesn't exist |
| `route.ts` | Route handler | Only for webhooks, non-browser clients, or streaming. UI mutations use Server Actions |

Route groups `(name)` for layout sharing without URL segments. Dynamic segments `[id]`; catch-all `[...slug]` only for CMS-style paths. `params` and `searchParams` are **Promises** in Next 15 — `await` them.

## Data fetching

- Fetch in Server Components, as close to where the data is used as possible. Parallel fetches with `Promise.all`, not sequential awaits.
- Request deduplication: same `fetch(url)` in one render is deduped automatically. For non-fetch sources (DB, SDK) wrap in `React.cache()`.
- Stream slow parts: wrap the slow subtree in `<Suspense fallback={<Skeleton/>}>` inside the page so the rest paints immediately.
- Never fetch in `useEffect`. Client-side reads that must update after load go through TanStack Query — see [data-fetching.md](data-fetching.md).

## Caching & revalidation (Next 15 defaults)

- `fetch` is **uncached by default**. Opt in explicitly: `fetch(url, { next: { revalidate: 300, tags: ['orders'] } })` or `cache: 'force-cache'`.
- Prefer **tag-based** revalidation: tag reads, call `revalidateTag('orders')` from the action that mutates. `revalidatePath` only when a tag is impractical.
- Routes are dynamic when they use `cookies()`, `headers()`, `searchParams`, or uncached fetch. Don't fight it with `export const dynamic = 'force-static'` unless you understand every fetch in the tree.
- `unstable_cache`/`'use cache'` is opt-in per project — if the repo uses it, follow the existing pattern; don't introduce it in a feature MR.
- Router cache: after a mutation, call `router.refresh()` from the client **or** `revalidatePath/Tag` in the Server Action — the action is preferred; it's one source of truth.

## Server Actions

`features/<name>/actions.ts` with `'use server'` at the top of the file (not per-function).

```ts
'use server';
import 'server-only';
import { z } from 'zod';
import { revalidateTag } from 'next/cache';
import { requireUser } from '@/lib/auth';
import { createOrderSchema } from './schemas';

export type ActionState = { ok: true } | { ok: false; fieldErrors?: Record<string, string[]>; message?: string };

export async function createOrder(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const user = await requireUser();                                  // 1. authz first — actions are public endpoints
  const parsed = createOrderSchema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) return { ok: false, fieldErrors: parsed.error.flatten().fieldErrors }; // 2. validate
  await ordersApi.create(user.tenantId, parsed.data);                // 3. do the work
  revalidateTag('orders');                                           // 4. invalidate
  return { ok: true };                                               // 5. return data, never throw for expected failures
}
```

- Every action: authenticate, authorize, validate with Zod, then act. Actions are HTTP endpoints — treat input as hostile.
- Return a discriminated `ActionState`; throw only for unexpected failures (the `error.tsx` boundary catches those).
- Consume with `useActionState` for forms (progressive enhancement works without JS) or call directly from an event handler inside `useTransition` for buttons.
- `redirect()` must be called **outside** `try/catch` — it throws internally.
- Don't pass Server Actions through more than one component layer. If you need to, the boundary is in the wrong place.

## Route handlers (`app/api/**/route.ts`)

- Only for: webhooks, mobile/third-party clients, file streaming, OAuth callbacks. UI never calls our own route handlers for mutations — use Server Actions.
- Validate with Zod; return `NextResponse.json(body, { status })`. Same error shape as the backend API (RFC 7807).
- Export only the HTTP methods you handle. Set `runtime = 'nodejs'` unless you've confirmed every import is edge-compatible.

## Navigation

- `<Link>` for all internal navigation; `useRouter().push` only after a mutation. Never `<a href>` for internal routes (loses prefetch and client transitions).
- Read URL state with `useSearchParams` (client) or `searchParams` (page). Update with `router.replace` + `useTransition` to keep the UI responsive.
- `redirect()` in Server Components/Actions; `permanentRedirect` for moved resources.

## Metadata & SEO

- Static: `export const metadata: Metadata = { title: ..., description: ... }` in `layout.tsx`/`page.tsx`.
- Dynamic: `export async function generateMetadata({ params })` — reuse the page's data function (deduped by `React.cache`), don't fetch twice.
- Root layout sets `title.template = '%s | AppName'`. Pages set `title` only.
- `opengraph-image.tsx` / `sitemap.ts` / `robots.ts` as file conventions, not hand-rolled routes.

## Images, fonts, scripts

- `next/image` always. Provide `width`/`height` or `fill` + sized parent; `sizes` for responsive; `priority` only on the LCP image (one per page). Remote hosts must be allow-listed in `next.config.ts`.
- `next/font` in the root layout, one or two families, `display: 'swap'`, exposed as CSS variables. Never `<link>` to Google Fonts.
- `next/script` with `strategy="afterInteractive"` (default) or `lazyOnload` for third-party scripts. Never a raw `<script>` tag.

## Middleware (`src/middleware.ts` / `proxy.ts` in Next 16)

- Edge runtime: no Node APIs, no DB calls, no heavy imports. Auth redirect checks against a cookie/JWT signature only.
- Scope with `config.matcher`; exclude `_next/static`, `_next/image`, `favicon.ico`, and public assets.

## Hydration errors

A hydration mismatch is a bug, not a warning to suppress. Causes in order of likelihood: rendering `Date.now()`/`Math.random()`/`window` during render; browser-extension DOM edits (verify in incognito); invalid HTML nesting (`<div>` inside `<p>`); locale-dependent formatting differing between server and client. Fix the cause; `suppressHydrationWarning` is allowed only on the `<html>` tag for theme classes.

## Reference

For anything not covered here — parallel/intercepting routes, `generateStaticParams`, runtime selection, bundling flags — invoke the `next-best-practices` skill and follow it. Record any decision it drove in this doc.
