# Performance

Ship less JavaScript, render on the server, load what's visible. Budgets are enforced in CI; opinions aren't.

## Budgets (CI-enforced)

| Metric | Budget | Where measured |
|--------|--------|----------------|
| First Load JS per route | ≤ 150 kB gzipped | `pnpm build` output + `@next/bundle-analyzer` |
| Shared chunk | ≤ 90 kB gzipped | `pnpm build` |
| LCP | ≤ 2.5 s (p75, mobile) | Lighthouse CI on staging |
| INP | ≤ 200 ms | Lighthouse CI / RUM |
| CLS | ≤ 0.1 | Lighthouse CI |

A route that exceeds its budget fails the pipeline. Raising a budget is an MR to this file with a justification, reviewed by a tech lead.

## JavaScript

- **Server Components first** (CLAUDE.md rule 2). Every `'use client'` is bytes on the wire — justify it.
- Before adding a dependency: check size on bundlephobia, prefer ESM tree-shakeable packages, check for an existing equivalent in the repo. Say the size in the commit body (rule 9).
- Banned in client bundles: `moment`, `lodash` (whole), `date-fns` without per-function imports, full icon libraries (`import { X } from 'lucide-react'` is fine — it tree-shakes), charting libraries in the shared chunk.
- Heavy client components (editors, charts, maps) load with `next/dynamic` and `ssr: false` only if they truly can't SSR, with a skeleton `loading`.
- Route-level code splitting is automatic. Don't import feature A's components from feature B's route.
- Third-party scripts via `next/script` with `lazyOnload` unless they're needed for first interaction. Analytics never blocks.
- Run `ANALYZE=true pnpm build` when a route's First Load JS grows by > 10 kB and explain what's in it.

## Rendering

- Stream: `<Suspense>` around slow data so the shell paints first. `loading.tsx` per segment.
- Static where possible: routes without per-user data should build statically (`generateStaticParams` for known dynamic segments) or use ISR (`revalidate`).
- Avoid layout thrash: `loading.tsx` skeletons match final dimensions; images have explicit sizes; fonts use `next/font` with `display: swap` and `adjustFontFallback`.
- Don't block on non-critical data: a "recommended items" panel loads inside its own Suspense boundary, not in the page's top-level `await`.
- Avoid waterfalls: `Promise.all` for independent server reads; don't await inside a `.map`.

## Lists & tables

- > 100 rows or unbounded lists → virtualize (`@tanstack/react-virtual`). Never render 1,000 DOM rows.
- Server-side pagination (cursor) over loading everything and filtering on the client. Sorting/filtering of server data happens in the API query, driven by URL state.
- Stable keys; memoized row components when the row is non-trivial and the list re-renders often.

## Re-renders

- Measure first: React DevTools Profiler, "Highlight updates". Optimize what's slow, not what looks suspicious.
- Common fixes in order: move state down (colocate), pass `children` instead of re-creating the subtree, split Context, select slices from stores (`useShallow`), then `memo`/`useMemo`/`useCallback`.
- Don't create objects/arrays/functions in JSX props of memoized children (`style={{}}`, `onClick={() => …}`) without a reason.
- Debounce/throttle user input that triggers network or heavy computation (`use-debounce`, 300 ms for search).

## Images & media

- `next/image` always (nextjs.md). `priority` on exactly the LCP image. `sizes` on every responsive image so the browser doesn't download desktop sizes on mobile.
- Modern formats are automatic (AVIF/WebP). Source assets ≤ 2× the largest display size.
- Video: `preload="none"`, `poster`, lazy load below the fold; never autoplay with sound.
- SVG icons inline as components; illustrations as `<Image>`.

## Network

- Cache reads with tags and sensible `revalidate` (nextjs.md). Don't `cache: 'no-store'` by reflex.
- `staleTime` on TanStack queries so navigation back doesn't refetch instantly.
- Prefetch on intent: `<Link prefetch>` is on by default in viewport; for buttons that open heavy routes, `router.prefetch` on hover.
- Compress and paginate API responses; don't fetch 50 fields to display 3 — ask the backend for a projection or use `select` in the query.

## Monitoring

- Web Vitals reported from `app/layout.tsx` via `useReportWebVitals` to the analytics endpoint, tagged with route pattern (not concrete path).
- Lighthouse CI runs against the staging deploy for the top 5 routes on every MR; results posted as an MR comment.
- Any regression > 10 % on LCP/INP blocks merge until explained.

## Checklist for a new client component

- [ ] Does it need to be client? Could the interactive part be a smaller leaf?
- [ ] New dependency? Size stated, tree-shakeable, no lighter alternative in repo?
- [ ] Renders a list? Bounded or virtualized?
- [ ] Images sized, LCP marked?
- [ ] `pnpm build` First Load JS for its route still under budget?
