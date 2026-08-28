# Naming & Style

Formatting is owned by Prettier and ESLint (`pnpm lint`). This doc covers what tools can't enforce.

## Files

- `kebab-case.ts`, suffixed by role: `orders.controller.ts`, `orders.service.ts`, `create-order.dto.ts`, `orders.repository.ts`, `orders.service.spec.ts`, `orders.e2e-spec.ts`.
- One exported class per file. Small helper types may live alongside the class that uses them.
- `index.ts` barrels only at module root, and only re-exporting the public surface (module class, exported service, public DTOs).
- Keep files under ~300 lines. If a service grows past that, split by sub-responsibility (`orders-pricing.service.ts`) — as its own task.

## Symbols

| Thing | Style | Example |
|-------|-------|---------|
| Classes, interfaces, types, enums | `PascalCase` | `OrderService`, `CreateOrderDto` |
| Variables, functions, methods | `camelCase` | `findByCustomerId` |
| Constants (true compile-time constants) | `SCREAMING_SNAKE` | `MAX_PAGE_SIZE` |
| Enum members | `PascalCase` | `OrderStatus.Shipped` |
| Injection tokens | `SCREAMING_SNAKE` string const | `PAYMENT_GATEWAY` |
| Booleans | prefix `is/has/can/should` | `isPoBox`, `hasShipped` |
| Async functions | no `Async` suffix; the return type says it | `create()`, not `createAsync()` |

Do not prefix interfaces with `I`. Do not suffix types with `Type`.

## Methods

- Verbs that say what happens: `create`, `findById`, `findMany`, `update`, `remove` (not `delete`, it's reserved-ish), `cancel`, `ship`.
- Repository methods return `T | null` for single lookups; services convert `null` into `NotFoundError`. Repositories never throw domain errors.
- Prefer many small methods over flags: `shipOrder()` and `cancelOrder()`, not `updateStatus(id, status)`.

## Types

- `strict: true`. No `any`. Use `unknown` and narrow.
- No non-null assertions (`!`) outside tests. Handle the null.
- Prefer `interface` for object shapes, `type` for unions/intersections/mapped types.
- Explicit return types on every exported function and public method.
- DTOs are classes (decorators need them). Entities/domain types are interfaces unless they have behavior.

## Imports

- Order: node built-ins → external packages → `@app/*` path aliases → relative. ESLint enforces.
- No relative imports crossing module boundaries (`../../users/...`). Import from the module's barrel via alias.
- No default exports.

## Comments

- Code says *what*; comments say *why*. If you need a comment to explain what, rename or extract.
- JSDoc on every exported symbol that is not self-explanatory from its signature. Skip it for `findById(id: string)`.
- `// TODO(ticket-id): ...` — a TODO without a ticket is a lint error.
- No commented-out code. Git remembers.

## Misc

- Early return over nested `if`.
- No magic numbers/strings — named constant or enum.
- Dates: store and pass `Date` (UTC) internally; serialise as ISO 8601 at the edge. Never `moment`.
- Money: integer minor units (`cents: number`) plus ISO currency code. Never floats.
