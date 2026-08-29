# Data Fetching & Mutations

Read on the server, update on the client, validate at every boundary. One typed client, one schema per resource.

## The API client (`src/lib/api-client.ts`)

- One `apiFetch<T>(path, { schema, ...init })` wrapper around `fetch`. It attaches auth, sets JSON headers, maps non-2xx to an `ApiError` (with the RFC 7807 body parsed), and **validates the response with the provided Zod schema**. Nothing calls `fetch` against our API directly.
- Two entry points: `serverApi` (adds the session cookie/token from `cookies()`, imports `server-only`) and `clientApi` (relies on the browser cookie). Same signature.
- Errors are thrown as `ApiError { status, code, detail, fieldErrors? }`. Never swallow; let the caller decide.
- Base URL from `env.API_URL` (server) / `env.NEXT_PUBLIC_API_URL` (client). Never hard-coded.

## Schemas (`features/<name>/schemas.ts`)

- Every resource has a Zod schema for what the API returns; types are inferred (`type Order = z.infer<typeof orderSchema>`). No hand-written interfaces that mirror API responses.
- Input schemas for mutations (`createOrderSchema`) are separate from resource schemas. Reuse via `.pick()`/`.omit()`/`.extend()`.
- Dates come in as ISO strings; transform to `Date` only at the display layer if needed. Money as `{ amount, currency }` — never a float.

## Reads on the server (`features/<name>/queries.ts`)

```ts
import 'server-only';
import { cache } from 'react';
import { serverApi } from '@/lib/api-client';
import { orderSchema, orderListSchema } from './schemas';

export const getOrder = cache((orderId: string) =>
  serverApi(`/v1/orders/${orderId}`, { schema: orderSchema, next: { tags: [`order:${orderId}`] } }),
);

export const listOrders = (params: OrderListParams) =>
  serverApi(`/v1/orders?${toSearchParams(params)}`, { schema: orderListSchema, next: { tags: ['orders'], revalidate: 60 } });
```

- Wrap single-entity reads in `React.cache` so `generateMetadata` and the page share one request.
- Tag every cached read. The tag vocabulary is: `<resource>` for collections, `<resource>:<id>` for one item.
- Pages call these directly and `await`. Parallelize independent reads with `Promise.all`. Throw `notFound()` on 404.
- Never call `queries.ts` from a client component — it won't compile (`server-only`), by design.

## Reads on the client — TanStack Query (`features/<name>/hooks/`)

Use only when data must change after first render: polling, dependent on client-only input, refetch after mutation without a full router refresh, infinite scroll.

```ts
// features/orders/hooks/use-orders.ts
'use client';
export const orderKeys = {
  all: ['orders'] as const,
  list: (params: OrderListParams) => [...orderKeys.all, 'list', params] as const,
  detail: (id: string) => [...orderKeys.all, 'detail', id] as const,
};

export function useOrders(params: OrderListParams, initialData?: OrderList) {
  return useQuery({
    queryKey: orderKeys.list(params),
    queryFn: () => clientApi(`/v1/orders?${toSearchParams(params)}`, { schema: orderListSchema }),
    initialData,
    staleTime: 30_000,
  });
}
```

- **Query key factory** per feature, exported. Keys are arrays; params objects are part of the key. Never build keys inline in components.
- **Seed from the server** so there is no loading flash: pass the server-fetched data as `initialData`, or prefetch in the page and wrap in `<HydrationBoundary state={dehydrate(queryClient)}>`. Bare `useQuery` with a spinner on first render is a smell.
- `staleTime` is set deliberately per query (default in `QueryClient`: 30s). `refetchOnWindowFocus` stays on unless there's a reason.
- Components read `data`, `isPending`, `isError`; branch on status, never on `data === undefined`.
- Select to what you need: `select: (d) => d.items.length` to avoid re-renders.
- `useSuspenseQuery` only inside a `<Suspense>` boundary with a matching skeleton, and only when data is guaranteed prefetched on the server.
- Infinite lists: `useInfiniteQuery` with the API's cursor (`getNextPageParam: (last) => last.nextCursor`). Never `skip`-based paging.

## Mutations

Two allowed paths. Pick one per feature and stay consistent.

**A. Server Action (default for forms, progressive enhancement):** see [nextjs.md §Server Actions](nextjs.md#server-actions). After success, `revalidateTag` in the action; the client calls `queryClient.invalidateQueries({ queryKey: orderKeys.all })` if the same data is also held in TanStack Query.

**B. TanStack `useMutation` (for interactive, non-form mutations: toggles, drag-reorder, inline edit):**

```ts
export function useCancelOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (orderId: string) => clientApi(`/v1/orders/${orderId}/cancel`, { method: 'POST', schema: orderSchema }),
    onSuccess: (order) => {
      qc.setQueryData(orderKeys.detail(order.id), order);
      void qc.invalidateQueries({ queryKey: orderKeys.list });
    },
  });
}
```

- Validate input with the Zod input schema **before** sending, and rely on the server validating again. Client validation is UX; server validation is security.
- Optimistic updates: `onMutate` snapshots + `setQueryData`, `onError` restores the snapshot and toasts, `onSettled` invalidates. Only for near-certain successes.
- Always surface `isPending` in the UI (disabled button, spinner in place). Never fire-and-forget.
- Error handling: `ApiError` with `fieldErrors` → map onto the form; other `ApiError` → toast with `detail`; unknown → rethrow to the boundary.

## Loading, empty, error states

Every data-driven component renders all four: loading (skeleton), empty (explicit message + primary action), error (message + retry), success. A test covers each. See [testing.md](testing.md).

## Rules (reject in review)

- `useEffect(() => { fetch(...) })` — always. Server Component or TanStack Query.
- `fetch` to our API without `apiFetch`/schema.
- `as Order` casts on API responses — parse, don't assert.
- Query keys built inline in a component.
- A Zustand store holding API data.
- Mutation without invalidation/revalidation.
- Sequential `await`s for independent server reads.
- Client component receiving a whole server object and re-fetching it anyway.

For infinite queries, prefetching strategies, or offline/persisted cache, invoke the `tanstack-query` skill.
