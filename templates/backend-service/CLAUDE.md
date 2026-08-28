# CLAUDE.md

Guidance for Claude Code (and every subagent it dispatches) working in this repository.
Keep this file short and imperative. Detail lives in `docs/standards/` — read the linked
doc before touching the area it covers.

## Project

NestJS 10 / TypeScript 5 REST service. PostgreSQL via Prisma. Jest for tests. pnpm.
Entry point: `src/main.ts`. One module per bounded context under `src/modules/<name>/`.

## Commands

- Install: `pnpm install`
- Dev server: `pnpm start:dev`
- Lint + format check: `pnpm lint` (eslint + prettier; **must pass before every commit**)
- Unit tests: `pnpm test` — single file: `pnpm test -- path/to/file.spec.ts`
- E2E tests: `pnpm test:e2e` (needs `docker compose up -d db`)
- Migrations: `pnpm prisma migrate dev --name <snake_case_name>`

## Non-negotiable rules

1. `pnpm lint && pnpm test` green before every commit. A lint failure is a task failure.
2. Controllers are thin: validate in DTOs, put logic in services. → [architecture.md](docs/standards/architecture.md)
3. Never throw raw `Error` from request paths — use the `AppException` hierarchy. → [error-handling.md](docs/standards/error-handling.md)
4. Every public service method has a `*.spec.ts` test; every endpoint has an e2e test. TDD: failing test first. → [testing.md](docs/standards/testing.md)
5. No new runtime dependency without stating why in the commit body / task report.
6. Never log PII (names, emails, phone numbers, street addresses). Postal code, region, country are fine. → [security.md](docs/standards/security.md)
7. Schema changes go through Prisma migrations — never edit the DB or generated client by hand. → [database.md](docs/standards/database.md)
8. Follow existing patterns in the module you're touching. Don't restructure outside your task; report concerns instead.
9. All code follows the `clean-code` skill: intention-revealing names, small single-purpose functions,
   ≤2 arguments unless justified, no side effects, no commented-out or explanatory-comment-instead-of-refactor code.
   Invoke the skill **before** writing, refactoring, or reviewing any source file. See [Skills](#skills).

## Conventions (summary — details in docs/standards/)

- Files: `kebab-case.ts`; suffix by role: `.controller.ts`, `.service.ts`, `.dto.ts`, `.repository.ts`, `.spec.ts`. → [naming-and-style.md](docs/standards/naming-and-style.md)
- HTTP: plural nouns, `/v1/` prefix, cursor pagination, RFC 7807 error bodies. → [api-design.md](docs/standards/api-design.md)
- Commits: Conventional Commits (`feat(orders): ...`). One logical change per commit. → [git-workflow.md](docs/standards/git-workflow.md)
- Logging: structured JSON via `Logger`, always include `requestId`. → [observability.md](docs/standards/observability.md)

## Skills

Skills are installed globally on each developer's machine (`~/.claude/skills/`), **not** committed
to this repo. Invoke them with the Skill tool at the moment stated. If a skill is not available in
your session, say so in your report and apply the summary in the rule instead — do not skip silently.
Where a skill disagrees with `docs/standards/`, the standards win.

| Skill | When to invoke |
|-------|----------------|
| `clean-code` | **Always** — before writing, refactoring, or reviewing any `.ts` file (rule 9) |
| `superpowers:test-driven-development` | Before implementing any feature or fix (rule 4) |
| `api-designer` | Only when designing a **new** resource model or API surface, or when `docs/standards/api-design.md` is silent on a question. For adding endpoints to existing resources the standards doc is sufficient and authoritative |
| `nestjs-best-practices` | Only when adding a Nest construct (guard, interceptor, pipe, custom provider) not already present in the codebase. Otherwise this repo's patterns are the standard — don't import outside opinions |

## For subagents (implementers and reviewers)

- Read this file and the standards doc for your area **before** writing code.
- Implementers: invoke `clean-code` before your first edit, and self-review your diff against it before reporting done.
- Reviewers: check the diff against the numbered rules above **and** the `clean-code` skill; cite the
  rule number or the clean-code section (e.g. "clean-code §2 Functions") in each finding.

## Docs index

| Doc | Read when |
|-----|-----------|
| [architecture.md](docs/standards/architecture.md) | Adding a module, service, or repository |
| [naming-and-style.md](docs/standards/naming-and-style.md) | Any new file or symbol |
| [api-design.md](docs/standards/api-design.md) | Adding or changing an endpoint |
| [error-handling.md](docs/standards/error-handling.md) | Anything that can fail |
| [testing.md](docs/standards/testing.md) | Always |
| [database.md](docs/standards/database.md) | Touching Prisma schema or queries |
| [security.md](docs/standards/security.md) | Auth, input handling, logging, secrets |
| [observability.md](docs/standards/observability.md) | Logging, metrics, tracing |
| [git-workflow.md](docs/standards/git-workflow.md) | Committing or opening an MR |
