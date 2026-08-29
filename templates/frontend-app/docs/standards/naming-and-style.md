# Naming & Style

Formatting is owned by Prettier and ESLint (`pnpm lint`). This doc covers what tools can't enforce.

## Files & folders

- `kebab-case` for every file and folder: `order-list.tsx`, `use-orders.ts`, `api-client.ts`. Next.js special files keep their required names (`page.tsx`, `layout.tsx`, `route.ts`).
- Suffix by role where it aids scanning: `.test.tsx`, `.spec.ts` (Playwright), `.stories.tsx`, `-store.ts`, `.client.tsx` when a server/client pair shares a name.
- One component per file; file name = component name in kebab-case (`order-status-badge.tsx` → `OrderStatusBadge`).
- `index.ts` barrels only at `features/<name>/index.ts` and `components/ui/index.ts`, re-exporting the public surface. No barrels inside `app/`.
- Colocate tests, stories, and styles-adjacent files with the component. No top-level `__tests__/` for unit/component tests.
- Keep files under ~200 lines (components ~150). Split by responsibility, as its own task.

## Symbols

| Thing | Style | Example |
|-------|-------|---------|
| Components | `PascalCase` function, named export | `export function OrderList()` |
| Props interface | `<Component>Props` | `interface OrderListProps` |
| Hooks | `useCamelCase` | `useOrders`, `useDebouncedValue` |
| Server Actions | verb-first `camelCase` | `createOrder`, `cancelOrder` |
| Query functions (server) | `get`/`list` prefix | `getOrder`, `listOrders` |
| Query key factories | `<resource>Keys` | `orderKeys.detail(id)` |
| Zustand stores | `use<Name>Store` | `useCartStore` |
| Zod schemas | `camelCase` + `Schema` | `createOrderSchema` |
| Types inferred from schemas | `PascalCase` noun | `type Order = z.infer<typeof orderSchema>` |
| Event handler props | `on<Event>` | `onSelect`, `onSubmit` |
| Event handlers (internal) | `handle<Event>` | `handleSelect` |
| Booleans | `is/has/can/should` | `isPending`, `hasItems` |
| Constants | `SCREAMING_SNAKE` for true constants | `MAX_PAGE_SIZE`; config objects stay `camelCase` |
| Enums | Avoid; use `z.enum([...])` / string literal unions | `type OrderStatus = 'pending' \| 'shipped'` |
| CSS variant helpers | `camelCase` `cva` result named after the element | `const button = cva(...)` |

- No `I` prefix on interfaces, no `Type`/`Interface` suffix. No `Component` suffix on components.
- Don't abbreviate: `order`, not `ord`; `button`, not `btn`. Accepted: `id`, `url`, `api`, `props`, `ref`, `e` only for event params in one-liners.
- Generic type params are descriptive past one: `TItem`, `TData`, not `T, U, V`.

## TypeScript

- `strict: true`, `noUncheckedIndexedAccess: true`. No `any`; use `unknown` and narrow. `@ts-expect-error` (with a reason) over `@ts-ignore`; both are rare.
- No non-null assertions (`!`) outside tests. Handle the `undefined`.
- Types from Zod schemas for anything that crosses a boundary (API, forms, URL). Hand-written types only for internal UI state.
- `interface` for object shapes and props; `type` for unions, intersections, mapped and inferred types.
- Explicit return types on exported functions in `lib/`, `queries.ts`, `actions.ts`. Components may infer `JSX.Element`.
- Props: `React.ComponentProps<'button'>` / `ComponentPropsWithoutRef<typeof Primitive>` to extend native or Radix elements. Don't redeclare `className`, `children`.
- Discriminated unions for state machines and action results (`{ ok: true } | { ok: false; message }`). Never `success: boolean` + optional fields.
- `satisfies` for config objects that need both inference and a constraint (`export const metadata = { … } satisfies Metadata`).
- Never `as` to silence a type error on data from outside — parse it.

## Imports

- Absolute imports via `@/` alias for anything outside the current feature; relative within a feature.
- Order (enforced by `eslint-plugin-import`): react/next → third-party → `@/lib`, `@/components` → `@/features` → relative → types (`import type`). Blank line between groups.
- `import type { … }` for type-only imports. `import 'server-only'` / `'client-only'` is the first line after the directive.
- No default exports except Next.js conventions and `next.config.ts`. Named exports refactor and grep better.
- No importing another feature's internals (`@/features/orders/components/...`); go through `@/features/orders`.

## JSX

- Self-close empty elements. Boolean props bare (`disabled`, not `disabled={true}`).
- Multi-line JSX in parentheses. Extract a variable or component when a conditional needs more than one ternary level.
- Strings that users see are not inline literals when the repo has i18n; otherwise plain strings are fine but never concatenate translatable fragments.
- Attribute order: `key`/`ref`, then identity (`id`, `type`, `name`), then data/state, then event handlers, then `className` last. Prettier-tailwind sorts inside `className`.

## Comments

- Code explains *what*; comments explain *why*, or a non-obvious constraint (`// Radix needs a stable id across SSR — see #1234`).
- No commented-out code. No `// TODO` without a ticket: `// TODO(SHIP-1234): …`.
- JSDoc on `lib/` exports and design-system primitives (props with non-obvious behavior). Not on every component.
- Don't restate the type in the comment.

## Formatting (owned by tools; listed for completeness)

Prettier: single quotes, semicolons, trailing commas `all`, print width 100, `prettier-plugin-tailwindcss`. ESLint: `next/core-web-vitals`, `@typescript-eslint/strict-type-checked`, `jsx-a11y/strict`, `import/order`, `no-console`, `react-hooks/*` as errors. Fix the code, not the config.
