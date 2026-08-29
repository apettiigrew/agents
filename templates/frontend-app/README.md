# Frontend app template — CLAUDE.md + standards

A sample `CLAUDE.md` and `docs/standards/` set for a React / Next.js / TypeScript application, written so that Claude Code **and the subagents it dispatches** (e.g. via `superpowers:subagent-driven-development`) follow the same conventions without loading large persona skills into every agent.

Sibling of [`templates/backend-service`](../backend-service) — same shape, frontend content.

## How it works

- `CLAUDE.md` is loaded automatically by every Claude Code session and subagent working in the repo. It is deliberately short: commands, eleven numbered non-negotiable rules, one-line convention summaries, a skills table, and a docs index. Reviewers are told to cite rule numbers.
- `docs/standards/*.md` hold the detail. `CLAUDE.md` tells agents *when* to read each one ("Read when: deciding where a piece of state lives"), so an implementer only loads the 1–3 docs relevant to its task.
- The frontend-specific concerns the user asked to enforce map to docs like this:

  | Concern | Where it's enforced |
  |---------|---------------------|
  | General frontend best practices | `components.md`, `styling-and-accessibility.md`, `performance.md`, `naming-and-style.md` |
  | Writing Next.js code | `nextjs.md` (RSC boundaries, file conventions, Server Actions, caching, metadata, images/fonts, hydration) |
  | Using Next.js with industrial practices | `architecture.md` (feature slices, thin routes), `security.md` (CSP, env, auth), `performance.md` (budgets in CI), `git-workflow.md` (pipeline) |
  | State management | `state-management.md` — a six-rung decision ladder (URL → server → local → lifted/Context → Zustand → persisted) |
  | React scenarios | `components.md` (composition, hooks, `useEffect` alternatives table, forms, Suspense, memoization) + `data-fetching.md` (TanStack Query patterns, mutations, optimistic UI) |

- Skills referenced in `CLAUDE.md` (`clean-code`, `next-best-practices`, `react-expert`, `tanstack-query`, `playwright-expert`, `frontend-design`, `superpowers:*`) are **not** committed to the app repo. They are installed once per machine and referenced by name. Install from this repo with:
  ```bash
  ln -s "$(pwd)/skills/clean-code" ~/.claude/skills/clean-code
  ln -s "$(pwd)/skills/next-best-practices" ~/.claude/skills/next-best-practices
  ln -s "$(pwd)/skills/react-expert" ~/.claude/skills/react-expert
  ln -s "$(pwd)/skills/playwright-expert" ~/.claude/skills/playwright-expert
  claude plugin install superpowers@claude-plugins-official
  claude plugin install tanstack-query@tanstack-skills
  claude plugin install frontend-design@claude-plugins-official
  ```
  Run `/skills` in a session to confirm they load. A referenced skill that isn't installed is silently unavailable, so `CLAUDE.md` tells agents to report that and fall back to the inline summary.
- The hard rules are meant to be backed by tooling (eslint incl. `jsx-a11y` + `react-hooks`, prettier, `tsc`, commitlint, gitleaks, coverage gate, bundle budgets, axe in Playwright, Lighthouse CI). Prose that a linter can enforce should be moved into the linter and deleted from the prose.

## Using it

1. Copy `CLAUDE.md` and `docs/standards/` into your app repo root.
2. Replace the stack specifics. This sample assumes **Next.js 15 App Router / React 19 / TypeScript 5 / pnpm / Tailwind / TanStack Query / Zustand / React Hook Form + Zod / Vitest + Testing Library / Playwright / GitLab**. If you use a different piece (e.g. Redux Toolkit, CSS Modules, Jest), edit the relevant doc and the rule that points at it — keep the *shape*: short root file, numbered rules, detail docs with "read when" triggers.
3. Delete any standard you won't actually enforce. An unenforced rule teaches agents to ignore the rest.
4. Add the hooks/linters/budgets referenced in `git-workflow.md` and `performance.md` so violations fail before review.

## Files

| File | Covers |
|------|--------|
| `CLAUDE.md` | Entry point — rules, commands, skills table, docs index |
| `docs/standards/architecture.md` | Feature-sliced layout, thin `app/`, data flow, providers, env |
| `docs/standards/nextjs.md` | Server vs client components, file conventions, fetching, caching/revalidation, Server Actions, route handlers, metadata, images/fonts, middleware, hydration |
| `docs/standards/components.md` | Component shape, composition, rendering rules, hooks, `useEffect` alternatives, forms, Suspense, memoization, anti-patterns |
| `docs/standards/state-management.md` | Decision ladder, URL state, server state, local/lifted/Context, Zustand rules, anti-patterns |
| `docs/standards/data-fetching.md` | Typed API client, Zod schemas, server queries, TanStack Query hooks, mutations (Server Action vs `useMutation`), optimistic updates |
| `docs/standards/styling-and-accessibility.md` | Tailwind + `cva`, design-system primitives, semantic HTML, forms, keyboard/focus, ARIA, color, tooling gates |
| `docs/standards/performance.md` | CI budgets, JS bundle rules, streaming, lists/virtualization, re-renders, images, network, monitoring |
| `docs/standards/testing.md` | Pyramid, TDD loop, Testing Library queries, MSW, hooks, stores, Playwright + axe, builders |
| `docs/standards/security.md` | Env/secrets, sessions, Server Action authz, input validation, XSS, CSP/headers, CSRF, PII, deps |
| `docs/standards/naming-and-style.md` | Files, symbols, TypeScript rules, imports, JSX, comments |
| `docs/standards/git-workflow.md` | Branches, Conventional Commits, hooks, CI pipeline, MRs, review, releases, agent rules |
