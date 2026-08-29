# Testing

Tests describe what the user sees and does. Write the failing test first, make it pass, refactor. A task without tests is not done.

## Pyramid

| Level | Tool | Location | Covers | Speed |
|-------|------|----------|--------|-------|
| Unit | Vitest | `*.test.ts` next to source | `lib/`, schemas, store logic, hooks (via `renderHook`), Server Action logic, query key factories | ms |
| Component | Vitest + Testing Library + jsdom | `*.test.tsx` next to component | Every component with logic: renders, interactions, loading/empty/error/success states, a11y roles | 10s of ms |
| E2E | Playwright | `e2e/*.spec.ts` | One spec per user-facing flow: happy path + the most likely failure. Runs against a built app with the API mocked at the network edge or a seeded test backend | s |
| Visual/a11y | Playwright + `@axe-core/playwright` | inside E2E specs | Every page: zero critical/serious axe violations. Screenshots for design-system primitives only | s |

Coverage gate in CI: 80 % lines on `src/features/**` and `src/lib/**`. `components/ui/` is covered by its keyboard-contract tests. Don't chase coverage on `app/` — pages are thin by rule and E2E covers them.

## TDD loop

1. Write the test for the *behavior* the task describes, from the user's point of view. Run it. **It must fail.**
2. Write the minimum code to pass.
3. Run the focused file: `pnpm test -- order-list.test.tsx`.
4. Refactor. Re-run.
5. Before committing: `pnpm typecheck && pnpm lint && pnpm test`. Before opening the MR: `pnpm build && pnpm test:e2e`.

## Component tests

```tsx
import { render, screen } from '@/test/render';   // wraps providers: QueryClient, theme, router mock
import userEvent from '@testing-library/user-event';

it('cancels the order when the user confirms', async () => {
  const user = userEvent.setup();
  const cancel = vi.fn().mockResolvedValue(undefined);
  render(<OrderActions order={anOrder({ status: 'pending' })} onCancel={cancel} />);

  await user.click(screen.getByRole('button', { name: /cancel order/i }));
  await user.click(screen.getByRole('button', { name: /confirm/i }));

  expect(cancel).toHaveBeenCalledWith('ord_123');
});
```

- **Query by role, then label, then text.** `getByRole('button', { name })`, `getByLabelText`, `getByText`. `getByTestId` is a last resort and needs a comment saying why no accessible query worked. If you can't find it by role, the markup probably has an a11y bug — fix that first.
- `userEvent` over `fireEvent`. Real users type, tab, and click; test the same way.
- Use the shared `render` from `src/test/render.tsx` that installs providers. Never construct `QueryClientProvider` in a test file.
- Assert on what the user sees: text, roles, `toBeDisabled()`, `toHaveAccessibleDescription()`. Never on state, class names, or that a hook was called.
- Async: `await screen.findByRole(...)` / `waitFor`. No arbitrary `setTimeout`.
- One behavior per `it`. Name as a sentence. Arrange / Act / Assert with blank lines. No `if`/loops in tests.
- Every data-driven component has four tests: loading, empty, error, success.
- Server Components that are `async`: test the extracted pieces — the `queries.ts` function (unit, with `apiFetch` mocked at `fetch` level via MSW) and the presentational component it renders (component test). Don't try to render async RSCs in jsdom.

## Hooks

- `renderHook` from Testing Library with the providers wrapper. Assert on returned values after `act`.
- TanStack Query hooks: MSW handles the network; assert on `result.current.data` after `await waitFor(() => expect(result.current.isSuccess).toBe(true))`.
- Don't test React itself (`useState` sets state). Test your hook's decisions.

## Network mocking — MSW

- `src/test/msw/handlers.ts` holds default happy-path handlers per resource; tests override per case with `server.use(...)`.
- Mock at the network (MSW), never `vi.mock('@/lib/api-client')`. The client's parsing and error mapping are part of what you're testing.
- Handlers return data from **builders** (`anOrder()`), not hand-typed JSON — keeps them valid against the schema.

## Server Actions & `lib/`

- Plain Vitest. Actions: mock `requireUser` and the API (MSW); assert the returned `ActionState`, that `revalidateTag` was called with the right tag (`vi.mock('next/cache')`), and that invalid input never reaches the API.
- `lib/` functions are pure; test them with tables (`it.each`).
- Zod schemas: one test per non-obvious rule (bounds, transforms, refinements). Not one per field.

## Stores (Zustand)

- Reset in `beforeEach`: `useCartStore.setState(useCartStore.getInitialState())`.
- Test actions by calling them on the store and asserting `getState()`. Components that use the store are tested with the real store, pre-seeded.

## E2E — Playwright

- One spec per flow: `e2e/orders/create-order.spec.ts`. Happy path + the most likely failure (validation error, 404). Not every permutation — that's component tests.
- Page Object Model for anything used by more than one spec (`e2e/pages/orders.page.ts`). Locators by role/label, same as component tests.
- Auth via a stored `storageState` created once in `global-setup.ts`. Never log in through the UI in every test.
- Backend: either MSW-in-browser / Playwright `route()` mocks with builder data, or a seeded test environment — whichever the repo has configured. Don't mix.
- `await expect(locator).toBeVisible()` auto-waits. No `waitForTimeout`.
- Axe on every page visited: `expect((await new AxeBuilder({ page }).analyze()).violations.filter(critical|serious)).toEqual([])`.
- Runs in CI against `pnpm build && pnpm start`, Chromium only on MRs; full matrix nightly.

## Builders (`src/test/builders/`)

- `anOrder(overrides?)`: valid by default, typed from the Zod schema, obviously-fake PII (`test+<uuid>@example.com`, "123 Test St"). Never copy production data.
- Builders are the single source of test data for MSW handlers, component tests, and E2E mocks.

## What not to test

- Tailwind classes, snapshot of markup (brittle; a11y assertions cover structure).
- Third-party components' internals (Radix already tests its Dialog).
- Next.js file-convention wiring (that `loading.tsx` shows) — E2E sees it incidentally.
- Type-level behavior — `tsc` does that.

## Flaky tests

A flaky test is a bug. Quarantine with `it.skip` + `// TODO(TICKET):` in the same MR that finds it; fix within the sprint. Never add `retries` in Playwright config to hide it; never wrap in `try/catch`.
