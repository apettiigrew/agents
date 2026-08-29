# CLAUDE.md

Guidance for Claude Code (and every subagent it dispatches) working in this repository.
Keep this file short and imperative. Detail lives in `docs/standards/` — read the linked
doc before touching the area it covers.

## Project

Next.js 15 (App Router) / React 19 / TypeScript 5 web application. pnpm. Tailwind CSS.
TanStack Query for server state, Zustand for the little global client state that exists,
React Hook Form + Zod for forms. Vitest + Testing Library for unit/component tests, Playwright for E2E.
Entry: `src/app/`. Features live under `src/features/<name>/`; shared UI under `src/components/`.

## Commands

- Install: `pnpm install`
- Dev server: `pnpm dev`
- Type check: `pnpm typecheck` (`tsc --noEmit`)
- Lint + format check: `pnpm lint` (eslint + prettier; **must pass before every commit**)
- Unit/component tests: `pnpm test` — single file: `pnpm test -- src/features/orders/order-list.test.tsx`
- E2E tests: `pnpm test:e2e` (Playwright; builds and starts the app)
- Production build: `pnpm build` — must succeed; a build warning about client/server boundaries is a task failure

## Non-negotiable rules

1. `pnpm typecheck && pnpm lint && pnpm test` green before every commit. A lint or type failure is a task failure.
2. **Server Components by default.** Add `'use client'` only at the leaf that needs state, effects, or browser APIs — never on a page or layout. → [nextjs.md](docs/standards/nextjs.md)
3. **Fetch on the server.** Pages and Server Components fetch their own data; the client uses TanStack Query for data that must update after load. No `useEffect` + `fetch`. → [data-fetching.md](docs/standards/data-fetching.md)
4. **State lives in the least powerful place that works:** URL → server (TanStack Query) → local `useState` → lifted/Context → Zustand store. Never duplicate server data into a store. → [state-management.md](docs/standards/state-management.md)
5. Every mutation goes through a Server Action or a typed API client function, validated with Zod **on the server**. Client-side validation is UX, not security. → [data-fetching.md](docs/standards/data-fetching.md)
6. Every component with logic has a test that renders it and asserts on what the user sees (role/label queries, not test IDs or implementation details). Every user-facing flow has one Playwright test. TDD: failing test first. → [testing.md](docs/standards/testing.md)
7. Accessible by construction: semantic elements, labelled controls, keyboard operable, visible focus, `next/image` with `alt`. `eslint-plugin-jsx-a11y` errors block the commit. → [styling-and-accessibility.md](docs/standards/styling-and-accessibility.md)
8. Never expose secrets to the browser. Only `NEXT_PUBLIC_*` reaches the client; server-only modules import `server-only`. Never log or render PII you weren't asked to display. → [security.md](docs/standards/security.md)
9. No new runtime dependency without stating why in the commit body / task report. Check bundle impact first. → [performance.md](docs/standards/performance.md)
10. Follow existing patterns in the feature you're touching. Don't restructure outside your task; report concerns instead.
11. All code follows the `clean-code` skill: intention-revealing names, small single-purpose components and hooks,
    props objects over long parameter lists, no side effects in render, no commented-out code.
    Invoke the skill **before** writing, refactoring, or reviewing any source file. See [Skills](#skills).

## Conventions (summary — details in docs/standards/)

- Files: `kebab-case.tsx`; one component per file, named export matching the file (`order-list.tsx` → `OrderList`). Hooks `use-*.ts`. → [naming-and-style.md](docs/standards/naming-and-style.md)
- Components: function components + hooks only. Props typed as `interface XProps`. Compose; don't configure with boolean flags. → [components.md](docs/standards/components.md)
- Routing: App Router only. Route groups for layouts; `loading.tsx`/`error.tsx` in every segment that fetches. → [nextjs.md](docs/standards/nextjs.md)
- Styling: Tailwind utilities + `cva` variants. No CSS-in-JS; inline `style` only for runtime-computed values. → [styling-and-accessibility.md](docs/standards/styling-and-accessibility.md)
- Commits: Conventional Commits (`feat(orders): ...`). One logical change per commit. → [git-workflow.md](docs/standards/git-workflow.md)

## Skills

Skills are installed globally on each developer's machine (`~/.claude/skills/`), **not** committed
to this repo. Invoke them with the Skill tool at the moment stated. If a skill is not available in
your session, say so in your report and apply the summary in the rule instead — do not skip silently.
Where a skill disagrees with `docs/standards/`, the standards win.

| Skill | When to invoke |
|-------|----------------|
| `clean-code` | **Always** — before writing, refactoring, or reviewing any `.ts`/`.tsx` file (rule 11) |
| `superpowers:test-driven-development` | Before implementing any feature or fix (rule 6) |
| `next-best-practices` | When adding a route segment, changing a server/client boundary, touching caching/revalidation, `generateMetadata`, route handlers, or when you hit a hydration error. This repo's `nextjs.md` is the summary; the skill is the reference |
| `react-expert` | Only when solving a React problem `components.md` is silent on (concurrent features, `useTransition`/`useOptimistic`, custom Suspense orchestration, ref edge cases). Otherwise this repo's patterns are the standard |
| `tanstack-query` | When adding a query/mutation shape not already present (infinite queries, optimistic updates, prefetch + hydration). For copying an existing query pattern, `data-fetching.md` is sufficient |
| `playwright-expert` | When adding E2E infrastructure (fixtures, page objects, auth setup) or debugging a flaky E2E test. Not for writing one more test in an existing spec |
| `frontend-design` | Only when the task is to design **new** UI with no existing design to follow. Never for adding a field to an existing screen |

## For subagents (implementers and reviewers)

- Read this file and the standards doc for your area **before** writing code.
- Implementers: invoke `clean-code` before your first edit; run `pnpm build` once before reporting done — it catches server/client boundary mistakes that tests don't.
- Reviewers: check the diff against the numbered rules above **and** the `clean-code` skill; cite the
  rule number or doc section (e.g. "rule 2", "state-management.md §Decision ladder") in each finding.

## Docs index

| Doc | Read when |
|-----|-----------|
| [architecture.md](docs/standards/architecture.md) | Adding a feature, page, or shared module |
| [nextjs.md](docs/standards/nextjs.md) | Adding a route, layout, server action, route handler, or touching caching |
| [components.md](docs/standards/components.md) | Writing or changing any React component or hook |
| [state-management.md](docs/standards/state-management.md) | Deciding where a piece of state lives |
| [data-fetching.md](docs/standards/data-fetching.md) | Reading or writing data from any component |
| [styling-and-accessibility.md](docs/standards/styling-and-accessibility.md) | Any markup or styling change |
| [performance.md](docs/standards/performance.md) | Adding a dependency, a large list, an image, or a client component |
| [testing.md](docs/standards/testing.md) | Always |
| [security.md](docs/standards/security.md) | Auth, env vars, user input, rendering external content, PII |
| [naming-and-style.md](docs/standards/naming-and-style.md) | Any new file or symbol |
| [git-workflow.md](docs/standards/git-workflow.md) | Committing or opening an MR |
