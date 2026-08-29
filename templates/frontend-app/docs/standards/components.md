# React Components & Hooks

Small, composable, predictable. A component renders props to UI; a hook owns a piece of behavior. Nothing else.

## Component shape

```tsx
import type { Order } from '../schemas';

interface OrderRowProps {
  order: Order;
  onSelect?: (orderId: string) => void;
  isSelected?: boolean;
}

export function OrderRow({ order, onSelect, isSelected = false }: OrderRowProps) {
  return (
    <li aria-selected={isSelected} onClick={() => onSelect?.(order.id)}>
      <OrderStatusBadge status={order.status} />
      <span>{formatMoney(order.total)}</span>
    </li>
  );
}
```

- Function components, named export, `interface XProps` directly above. No `React.FC`, no default exports (except `page.tsx`/`layout.tsx` where Next requires them).
- Destructure props in the signature; defaults there too. Never mutate props.
- One component per file. A tiny private helper component may live in the same file if it's not exported.
- Keep components under ~150 lines. Past that, extract a child component or a hook — as its own step.
- JSX returns one root; use fragments, not wrapper `<div>`s.

## Composition over configuration

- **No boolean prop explosions.** `<Card variant="warning">` beats `<Card isWarning>`; `<Dialog><DialogTitle/><DialogBody/></Dialog>` beats `<Dialog title body footer/>`.
- Pass `children` and slots (`header`, `actions`) for layout components. Render props only when the child needs the parent's state.
- Compound components share state via a small Context declared in the same file (`Tabs` / `TabList` / `Tab` / `TabPanel`).
- Shared primitives in `components/ui/` accept `className` and spread remaining props onto the root element; use `cn()` to merge. They forward refs (React 19: `ref` is a normal prop).

## Rendering rules

- Render must be pure: same props + state → same output. No mutations, no I/O, no `Date.now()`/`Math.random()` in render (hydration mismatch — see nextjs.md).
- **Keys** are stable IDs from the data. Never the array index for lists that reorder, filter, or delete. Never `Math.random()`.
- Conditional rendering: early returns for whole-component branches; `&&`/ternary for small inline pieces. Guard `0`: `count > 0 && <Badge/>`, not `count && <Badge/>`.
- Don't derive state you can compute: `const total = items.reduce(...)` in render, not `useState` + `useEffect` to sync it.
- Lists longer than ~100 items that render off-screen use virtualization (see performance.md).

## Hooks

- Call hooks at the top level, unconditionally, in the same order. ESLint `rules-of-hooks` errors block the commit.
- Custom hooks `use-<thing>.ts`, one behavior each, returning an object (not a tuple) when there's more than two values.
- Extract a hook when: the same stateful logic appears twice, **or** a component's logic obscures its JSX. Don't extract a hook that's used once and only wraps `useState`.
- Hooks return data and callbacks; they don't return JSX.

### `useEffect` — last resort

You probably don't need it. Before writing one, check:

| You want to… | Use instead |
|--------------|-------------|
| Fetch data | Server Component or TanStack Query |
| Compute from props/state | Plain variable in render, `useMemo` if expensive |
| Respond to a user event | The event handler |
| Reset state when a prop changes | `key` on the component |
| Sync to a store/URL | The store's setter / `router.replace` in the handler |
| Notify a parent | Call the callback in the handler that caused the change |

Legitimate uses: subscribing to an external system (WebSocket, `ResizeObserver`, `matchMedia`), syncing with a non-React widget, `document.title`. Every effect that subscribes returns a cleanup. Dependencies are exact — never suppress `react-hooks/exhaustive-deps`; restructure instead.

### Refs

- `useRef` for DOM nodes and mutable values that don't drive rendering (timers, previous values). Never read `ref.current` during render.
- `useImperativeHandle` only for design-system primitives that must expose `focus()`/`scrollIntoView()`.

## Events & handlers

- Name handlers `handleX` inside the component, props `onX`. `onSelect`, not `selectHandler`.
- Handlers do one thing and delegate: call a mutation hook, update state, navigate. Business logic lives in the feature's `actions.ts`/`lib`, not inline in JSX.
- Async handlers wrap in `useTransition` (`startTransition(async () => …)`) so the UI shows `isPending` and stays interactive.

## Forms

React Hook Form + Zod, or Server Action + `useActionState` for simple progressive-enhancement forms.

```tsx
const form = useForm<CreateOrderInput>({ resolver: zodResolver(createOrderSchema), defaultValues });
```

- Schema in `features/<name>/schemas.ts`; the **same** schema validates on the server. Infer the type: `type CreateOrderInput = z.infer<typeof createOrderSchema>`.
- Controlled inputs through `form.register` / `<Controller>`; never hand-roll `useState` per field.
- Every input has a `<label htmlFor>`; errors rendered with `aria-describedby` and `aria-invalid`. Submit button shows pending state and is disabled while submitting.
- On success: reset or navigate, and invalidate the affected query/tag. On failure: map server `fieldErrors` back onto the form with `form.setError`.

## Suspense & error boundaries

- Wrap each independently-loading region in its own `<Suspense fallback>`; don't put one boundary around the whole page.
- Fallbacks are layout-matching skeletons (same dimensions), not spinners — prevents layout shift.
- `error.tsx` per segment handles render errors. Inside a page, wrap risky third-party widgets in a local `<ErrorBoundary>` (`react-error-boundary`) so one failure doesn't blank the screen.
- Use `useOptimistic` for mutations where the success case is near-certain (toggle, reorder). Roll back on failure with a toast.

## Memoization

- Don't reach for `memo`/`useMemo`/`useCallback` by default. React Compiler (if enabled) handles it; otherwise measure first with the Profiler.
- Justified when: a value is passed to a memoized child, a dependency of an effect, or genuinely expensive (>1ms) to compute.
- `useMemo` for referential stability of objects/arrays passed as props or deps; `useCallback` for handlers passed to memoized children or used in deps.

## Anti-patterns (reject in review)

- Prop drilling more than two levels → composition or Context (see state-management.md).
- `useEffect` that sets state from props → derive or `key`.
- Index keys on dynamic lists.
- `any` in props or event types. Use `React.ComponentProps<'button'>`, `React.ChangeEvent<HTMLInputElement>`.
- Giant "god components" mixing fetching, form state, and layout.
- `dangerouslySetInnerHTML` without sanitization (see security.md).
- `'use client'` on a component with no state/effects/handlers.
