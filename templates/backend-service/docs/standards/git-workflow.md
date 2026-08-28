# Git Workflow

Small, reviewable, revertable. Every commit builds and passes tests on its own.

## Branches

- `main` is protected and always deployable. No direct pushes.
- Feature branches from `main`: `<type>/<ticket>-<short-desc>` — `feat/SHIP-1234-cursor-pagination`, `fix/SHIP-1301-null-carrier`.
- Rebase on `main` before opening the MR and before merge. No merge commits from `main` into the branch.
- Delete the branch on merge.

## Commits

Conventional Commits, enforced by `commitlint` in the pre-commit hook:

```
<type>(<scope>): <imperative summary ≤ 72 chars>

<body: what and why, not how. Wrap at 100.>

Refs: SHIP-1234
```

- `type` ∈ `feat | fix | refactor | test | docs | chore | perf | build | ci`.
- `scope` = module name (`orders`, `shipping`) or area (`db`, `auth`, `deps`).
- One logical change per commit. "Add migration" and "use new column" are two commits (and often two MRs — see database.md).
- New runtime dependency → the body says which and why (CLAUDE.md rule 5).
- Never commit: secrets, `.env`, generated Prisma client, `node_modules`, IDE files. `.gitignore` covers these; `gitleaks` catches the rest.
- Don't `--amend` or force-push after review has started. Add fixup commits; squash on merge.

## Pre-commit (husky + lint-staged)

Runs automatically; don't `--no-verify`:

1. `prettier --write` + `eslint --fix` on staged files
2. `tsc --noEmit`
3. `commitlint`
4. `gitleaks protect --staged`

Tests are not in pre-commit (too slow) — they're your responsibility before pushing (`pnpm test`), and CI's before merging.

## Merge requests

- One MR = one deliverable. ≤ ~400 lines changed excluding tests and generated files; split if bigger.
- Title = the commit summary if single-commit, otherwise a summary of the whole.
- Description template (`.gitlab/merge_request_templates/default.md`):
  ```
  ## What
  ## Why
  ## How to verify
  ## Rollout / rollback notes   (migrations, flags, config)
  ## Checklist
  - [ ] Tests added/updated
  - [ ] Docs/standards updated if conventions changed
  - [ ] No PII in logs/errors
  - [ ] Backward-compatible migration (or N/A)
  ```
- Draft until CI is green. Request review from the module's CODEOWNERS.
- Squash-merge with the MR title as the commit message. Rebase-merge only when each commit is independently valuable.

## Review

- Reviewers cite the standard being violated (e.g. "CLAUDE.md rule 3", "error-handling.md §Rules 4"). Findings without a cited rule are suggestions, not blockers.
- Authors reply to every thread; resolve only after the reviewer agrees or the change is made.
- Approve means "I'd be comfortable being paged for this." Two approvals for anything touching auth, migrations, or payments.

## Releases

- Every merge to `main` deploys to staging automatically.
- Production deploys are tagged `vYYYY.MM.DD.N` from `main`. Changelog is generated from Conventional Commits.
- Rollback = redeploy the previous tag. That's why migrations are backward-compatible.

## For AI agents specifically

- Commit after each completed task from the plan, not at the end of the session.
- Never push to `main`, never force-push, never rewrite history that's been pushed.
- If a hook fails, fix the cause. Don't bypass it.
- Include the ticket reference from the plan in every commit.
