# Backend service template — CLAUDE.md + standards

A sample `CLAUDE.md` and `docs/standards/` set for a backend service, written so that Claude Code **and the subagents it dispatches** (e.g. via `superpowers:subagent-driven-development`) follow the same conventions without loading large persona skills into every agent.

## How it works

- `CLAUDE.md` is loaded automatically by every Claude Code session and subagent working in the repo. It is deliberately short: commands, eight numbered non-negotiable rules, one-line convention summaries, and a docs index. Reviewers are told to cite rule numbers.
- `docs/standards/*.md` hold the detail. `CLAUDE.md` tells agents *when* to read each one ("Read when: adding an endpoint"), so an implementer only loads the 1–2 docs relevant to its task.
- Skills referenced in `CLAUDE.md` (`clean-code`, `nestjs-best-practices`, `superpowers:*`) are **not** committed to the service repo. They are installed once per machine and referenced by name. Install from this repo with:
  ```bash
  ln -s "$(pwd)/skills/clean-code" ~/.claude/skills/clean-code
  ln -s "$(pwd)/skills/nestjs-best-practices" ~/.claude/skills/nestjs-best-practices
  claude plugin install superpowers@claude-plugins-official
  ```
  Run `/skills` in a session to confirm they load. A referenced skill that isn't installed is silently unavailable, so `CLAUDE.md` tells agents to report that and fall back to the inline summary.
- The hard rules are meant to be backed by tooling (eslint, prettier, commitlint, gitleaks, coverage gate). Prose that a linter can enforce should be moved into the linter and deleted from the prose.

## Using it

1. Copy `CLAUDE.md` and `docs/standards/` into your service repo root.
2. Replace the stack specifics (this sample assumes NestJS / TypeScript / Prisma / PostgreSQL / pnpm / GitLab). Keep the *shape*: short root file, numbered rules, detail docs with "read when" triggers.
3. Delete any standard you won't actually enforce. An unenforced rule teaches agents to ignore the rest.
4. Add the hooks/linters referenced in `git-workflow.md` so violations fail before review.

## Files

| File | Covers |
|------|--------|
| `CLAUDE.md` | Entry point — rules, commands, docs index |
| `docs/standards/architecture.md` | Module layout, layers, DI, config |
| `docs/standards/naming-and-style.md` | Files, symbols, types, imports, comments |
| `docs/standards/api-design.md` | URLs, status codes, pagination, RFC 7807 errors, Swagger |
| `docs/standards/error-handling.md` | `AppException` hierarchy, filter, async rules |
| `docs/standards/testing.md` | Pyramid, TDD loop, fakes vs mocks, e2e minimums |
| `docs/standards/database.md` | Schema conventions, safe migrations, query rules, indexes |
| `docs/standards/security.md` | Auth, input bounds, PII & logging, secrets, deps |
| `docs/standards/observability.md` | Structured logs, metrics cardinality, tracing, health, alerts |
| `docs/standards/git-workflow.md` | Branches, Conventional Commits, hooks, MRs, agent rules |
