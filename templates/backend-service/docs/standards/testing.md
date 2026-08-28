# Testing

Tests are the spec. Write the failing test first, make it pass, then refactor. A task without tests is not done.

## Pyramid

| Level | Location | Runs against | Speed | Coverage target |
|-------|----------|--------------|-------|-----------------|
| Unit | `*.spec.ts` next to source | Service/class with injected fakes | ms | Every public service method, every branch |
| Integration | `*.int-spec.ts` next to repository | Real Postgres (docker) via Prisma | 100ms | Every repository method |
| E2E | `test/e2e/*.e2e-spec.ts` | Full Nest app + real DB, HTTP via supertest | s | Every endpoint × (success, validation, not-found, unauth) |

Coverage gate in CI: 85% lines on `src/modules/**`. Don't game it — uncovered branches in error paths are exactly where bugs live.

## TDD loop

1. Write the test for the *behavior* the task describes. Run it. **It must fail** — if it passes, the test is wrong or the feature already exists.
2. Write the minimum code to pass.
3. Run the focused file: `pnpm test -- orders.service.spec.ts`.
4. Refactor. Re-run.
5. Before committing, run the full suite once: `pnpm test && pnpm test:e2e`.

Don't run the full suite after every edit — it's slow and trains you to skip it.

## Unit tests

- Use Nest's `Test.createTestingModule` **only** when you need DI wiring. Otherwise instantiate the class directly with fakes — it's faster and clearer:
  ```ts
  const repo = createFakeOrdersRepository();
  const svc = new OrdersService(repo, fakeClock, fakeEvents);
  ```
- Fakes over mocks. A `FakeOrdersRepository` backed by a `Map` beats `jest.fn()` chains — it survives refactors and reads like the real thing. Put shared fakes in `test/fakes/`.
- `jest.mock()` of modules is a last resort (third-party SDKs). Never mock the class under test's own collaborators piecemeal.
- Never mock Prisma in unit tests. If a service talks to Prisma directly, that's an architecture violation — it should go through a repository.
- One behavior per `it`. Name it as a sentence: `it('rejects shipping an already-cancelled order')`.
- Structure: Arrange / Act / Assert, separated by blank lines. No logic in tests (no `if`, no loops building expectations).
- Time: inject a `Clock`; never `jest.useFakeTimers()` on service logic. Randomness: inject an `IdGenerator`.

## Integration tests (repositories)

- Real database, one schema per Jest worker (`DATABASE_URL` + `?schema=test_${JEST_WORKER_ID}`), migrated in `globalSetup`.
- Each test runs inside a transaction that's rolled back in `afterEach`. No `TRUNCATE` between tests.
- Test the query, not Prisma: filtering, ordering, pagination edge cases (empty page, last page, cursor at boundary), unique constraint behavior.

## E2E tests

- Boot the app once per file in `beforeAll`. Use `supertest` against `app.getHttpServer()`.
- Authenticate with a helper that mints a real JWT with the test signing key — don't bypass the guard.
- Assert on status **and** body shape. Use `toMatchObject` for the fields you care about; snapshot the OpenAPI document, not response bodies.
- Every endpoint gets at minimum:
  - happy path
  - `400` for an invalid body (one representative case)
  - `404` for a missing resource
  - `401` without a token
  - `403` for another tenant's resource (where applicable)

## Fixtures & builders

- Builders over fixtures files: `anOrder({ status: 'shipped' })` in `test/builders/`. Defaults are valid; tests override only what matters.
- No shared mutable state between tests. No `beforeAll` that creates data used by multiple `it`s.

## What not to test

- Framework behavior (that `@IsString()` rejects numbers).
- Private methods — test through the public surface.
- Getters, DTO classes, module wiring.

## Flaky tests

A flaky test is a bug. Quarantine with `it.skip` + a `// TODO(TICKET):` on the same PR that finds it, and fix within the sprint. Never add retries to hide it.
