# State Management

Most "state" is not yours to manage. Classify it first, then put it in the least powerful place that works.

## Decision ladder

Work down the list. Stop at the first rung that fits.

| # | Kind of state | Lives in | Examples |
|---|---------------|----------|----------|
| 1 | **Shareable / bookmarkable** | The **URL** (`searchParams`, path) | Filters, sort, pagination, active tab, selected ID, open modal |
| 2 | **Server data** (came from an API, other users can change it) | **Server Component props** on first render; **TanStack Query** if it must update on the client | Orders, user profile, feature flags |
| 3 | **Local UI** (one component cares) | `useState` / `useReducer` | Input draft, hover, disclosure open/closed |
| 4 | **Shared by a subtree** | Lift to the common parent; **Context** if it would drill >2 levels | Form wizard step, compound component state, theme |
| 5 | **Global client-only** (survives navigation, unrelated components read it) | **Zustand** store in `src/stores/` | Cart draft before checkout, sidebar collapsed, toasts, unsaved-changes flag |
| 6 | **Persistent client-only** | Zustand + `persist` middleware, or `localStorage` behind a hook | Dismissed banners, column preferences |

Rules that follow from the ladder:

- **Never copy server data into a store.** TanStack Query is the cache. A Zustand store holding `orders` is a bug — it goes stale and diverges.
- **Never put URL-worthy state in `useState`.** If the user would expect Back or Refresh to preserve it, it's URL state.
- **Never reach for Context or a store to avoid passing one prop one level.** Composition (`children`) fixes most drilling.
- **No Redux / MobX / Jotai / Recoil.** Zustand is the one global store library. New state libraries require an ADR, not an MR.

## URL state (rung 1)

- Read: `searchParams` prop in `page.tsx` (server), `useSearchParams()` in client components.
- Write: `router.replace(`?${params}`)` inside `startTransition` so the page stays interactive; `push` only when the change should be a Back-navigable step.
- Parse with Zod in one place per route (`features/<name>/search-params.ts`) — defaults, coercion, and bounds live there, not scattered through components. `nuqs` is acceptable if already in the repo.
- Keep keys short and stable (`?status=shipped&page=2`). Changing a key is a breaking change for bookmarks.

## Server state (rung 2)

See [data-fetching.md](data-fetching.md) for the full contract. Summary:

- First render: fetch in the Server Component, pass as props. Zero client JS.
- Needs to update after load (polling, mutation feedback, user refetch): a TanStack Query hook in `features/<name>/hooks/`, seeded from the server via `initialData` or `HydrationBoundary` so there's no loading flash.
- Mutations invalidate by query key / cache tag. No manual "set the list after create" unless it's an optimistic update that the query will replace.

## Local state (rung 3)

- `useState` for independent values. `useReducer` when several values change together or transitions have rules (a state machine: `idle → submitting → success | error`).
- Keep state minimal: store the selected `id`, not the selected object; store the raw input, not the raw input *and* the parsed number.
- Group related state in one object only if the pieces always change together; otherwise separate `useState`s.
- Initialize lazily for expensive defaults: `useState(() => compute())`.

## Lifted state & Context (rung 4)

- Lift to the lowest common ancestor. If that ancestor is a page, reconsider rung 1 (URL) first.
- Context is for **low-frequency** shared state: theme, current user, locale, a compound component's internals. Not for anything that updates on every keystroke — every consumer re-renders.
- One Context per concern. Split "value" and "dispatch" contexts if consumers update rarely but read often.
- Wrap with a `useX()` hook that throws if used outside the provider:
  ```ts
  export function useWizard() {
    const ctx = useContext(WizardContext);
    if (!ctx) throw new Error('useWizard must be used within <Wizard>');
    return ctx;
  }
  ```
- Memoize the provider `value` so consumers don't re-render on parent renders.

## Global client state — Zustand (rung 5)

`src/stores/<name>-store.ts`, one store per concern, small.

```ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface CartState {
  lines: CartLine[];
  addLine: (line: CartLine) => void;
  removeLine: (sku: string) => void;
  clear: () => void;
}

export const useCartStore = create<CartState>()(
  devtools((set) => ({
    lines: [],
    addLine: (line) => set((s) => ({ lines: upsertLine(s.lines, line) }), false, 'cart/addLine'),
    removeLine: (sku) => set((s) => ({ lines: s.lines.filter((l) => l.sku !== sku) }), false, 'cart/removeLine'),
    clear: () => set({ lines: [] }, false, 'cart/clear'),
  })),
);
```

- **Select slices**: `useCartStore((s) => s.lines.length)`, never `const store = useCartStore()` — that subscribes to everything.
- Actions live in the store; components never `set` directly. Derived values are selectors or plain functions, not stored.
- Stores are client-only. Never import a store in a Server Component. Per-request server data goes through props, not a store.
- Hydration with Next.js: don't read `persist`ed state during the first render (mismatch). Use a `useHydrated()` guard or `skipHydration` + manual `rehydrate()` in an effect.
- Testing: reset with `useCartStore.setState(initialState)` in `beforeEach`. Test store logic as plain functions.

## Forms

Form state is its own category — React Hook Form owns it. Don't mirror form fields into `useState`, Context, or a store. Multi-step wizards keep the accumulated draft in a single RHF form or a Zustand store (rung 5) if steps are separate routes. See [components.md §Forms](components.md#forms).

## Anti-patterns (reject in review)

- Server data in Zustand/Context → TanStack Query.
- `useEffect` syncing one state variable from another → derive it.
- Filters/pagination in `useState` → URL.
- A single `AppContext` with everything in it → split by concern, or Zustand.
- Store selector returning a new object every call without `useShallow` → re-render storm.
- Prop-drilling a `setX` five levels → lift, compose, or Context.
