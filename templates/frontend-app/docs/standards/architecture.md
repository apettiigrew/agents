# Architecture

Feature-sliced. Routes are thin; features own their UI, data access, and types. Dependencies point one way: `app → features → components/lib`. Features never import from other features' internals.

## Layout

```
src/
├── app/                          # Next.js App Router — routing ONLY
│   ├── layout.tsx                # root layout: html/body, providers, fonts
│   ├── (marketing)/              # route group: public pages, own layout
│   ├── (app)/                    # route group: authenticated shell
│   │   ├── layout.tsx
│   │   └── orders/
│   │       ├── page.tsx          # Server Component: fetch + compose feature components
│   │       ├── loading.tsx
│   │       ├── error.tsx
│   │       └── [orderId]/page.tsx
│   └── api/                      # route handlers (webhooks, non-React clients only)
├── features/
│   └── orders/
│       ├── components/           # feature-specific UI (OrderList, OrderStatusBadge)
│       ├── actions.ts            # 'use server' — mutations for this feature
│       ├── queries.ts            # server-side data access (called from pages/RSCs)
│       ├── hooks/                # client hooks incl. TanStack Query hooks (use-orders.ts)
│       ├── schemas.ts            # Zod schemas + inferred types
│       ├── types.ts              # domain types not derived from schemas
│       └── index.ts              # public surface of the feature
├── components/
│   ├── ui/                       # design-system primitives (Button, Dialog, Input) — no domain knowledge
│   └── layout/                   # shells, nav, page headers
├── lib/                          # framework-agnostic utilities: api-client, env, formatters, cn()
├── hooks/                        # generic hooks (use-media-query, use-debounce)
├── stores/                       # Zustand stores (rare — see state-management.md)
└── styles/globals.css
```

## Rules

- **`app/` contains no business logic.** A `page.tsx` calls a feature's `queries.ts`, passes the result to a feature component, and returns. If a page grows past ~40 lines, the logic belongs in the feature.
- **Features are the unit of ownership.** Everything about "orders" lives in `features/orders/`. Cross-feature use goes through `index.ts`; if two features need the same thing, it moves to `components/` or `lib/`, not into one feature importing the other.
- **`components/ui/` knows nothing about the domain.** A `Button` doesn't know what an order is. If a primitive needs domain knowledge, it's a feature component.
- **`lib/` is pure TypeScript.** No React imports. Testable with plain Vitest.
- **Server/client split is a file property, not a folder.** Colocate; mark client files with `'use client'` at the top. Prefer naming that reveals it when the pair exists: `order-list.tsx` (server) and `order-filters.client.tsx`. See [nextjs.md](nextjs.md).

## Data flow

```
Server Component (page)        Client Component
  └─ queries.ts ──► API/DB       └─ hooks/use-orders.ts ──► TanStack Query ──► lib/api-client ──► API
  └─ passes data as props ─────► └─ or receives initialData from the server for hydration
Mutations: form/button ──► actions.ts ('use server', Zod-validated) ──► revalidatePath/Tag
```

- Read on the server whenever the data is needed on first render. Push to the client only what must change after load (polling, user-driven refetch, optimistic UI).
- Types cross the boundary as plain serializable objects. No class instances, Dates as ISO strings, no functions as props into client components except Server Actions.

## Providers

One `src/app/providers.tsx` (`'use client'`) wraps `QueryClientProvider`, theme, and toast providers. Nothing else is global. Feature-level Context is declared inside the feature.

## Configuration

- `src/lib/env.ts` parses `process.env` with Zod at import time and exports typed `env`. Nothing reads `process.env` directly.
- Two schemas: `server` (all vars) and `client` (`NEXT_PUBLIC_*` only). The client schema is the only thing imported by client code.

## Adding a feature (checklist)

1. `features/<name>/` with `schemas.ts` first — types come from Zod.
2. `queries.ts` (server read) and `actions.ts` (server write), each with tests.
3. Components, server-first; extract `'use client'` leaves only when needed.
4. `app/(app)/<name>/page.tsx` + `loading.tsx` + `error.tsx`.
5. Playwright test for the primary flow.
6. Export the public surface from `index.ts`.
