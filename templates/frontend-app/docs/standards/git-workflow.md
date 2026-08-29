# Git Workflow

Small, reviewable, revertable. Every commit builds, type-checks, and passes tests on its own.

## Branches

- `main` is protected and always deployable. No direct pushes.
- Feature branches from `main`: `<type>/<ticket>-<short-desc>` — `feat/SHIP-1234-order-filters`, `fix/SHIP-1301-hydration-mismatch`.
- Rebase on `main` before opening the MR and before merge. No merge commits from `main` into the branch.
- Delete the branch on merge.

## Commits

Conventional Commits, enforced by `commitlint` in the pre-commit hook:

```
<type>(<scope>): <imperative summary ≤ 72 chars>

<body: what and why, not how. Wrap at 100.>

Refs: SHIP-1234
```

- `type` ∈ `feat | fix | refactor | test | docs | style | chore | perf | build | ci | a11y`.
- `scope` = feature name (`orders`, `checkout`), or area (`ui`, `auth`, `deps`, `a11y`, `perf`).
- One logical change per commit. "Add primitive" and "use primitive in orders" are two commits.
- New runtime dependency → body states which, why, and gzipped size (CLAUDE.md rule 9).
- A commit that adds `'use client'` to an existing component says why in the body.
- Never commit: secrets, `.env*` (except `.env.example`), `.next/`, `node_modules`, Playwright reports/traces, IDE files. `.gitignore` covers these; `gitleaks` catches the rest.
- Don't `--amend` or force-push after review has started. Add fixup commits; squash on merge.

## Pre-commit (husky + lint-staged)

Runs automatically; don't `--no-verify`:

1. `prettier --write` + `eslint --fix` on staged files (includes `jsx-a11y`, `react-hooks`, `no-console`)
2. `tsc --noEmit`
3. `commitlint`
4. `gitleaks protect --staged`

Tests and the production build are not in pre-commit (too slow) — they're your responsibility before pushing (`pnpm test && pnpm build`), and CI's before merging.

## CI pipeline (every MR)

1. `pnpm install --frozen-lockfile`
2. `pnpm lint && pnpm typecheck`
3. `pnpm test --coverage` (gate: 80 % on `features/**`, `lib/**`)
4. `pnpm build` — fails on bundle budget breach (performance.md)
5. `pnpm test:e2e` (Chromium) incl. axe checks
6. Deploy preview → Lighthouse CI on top routes → results as MR comment
7. `pnpm audit --prod`

## Merge requests

- One MR = one deliverable. ≤ ~400 lines changed excluding tests, stories, and generated files; split if bigger. UI + API-contract changes ship in separate MRs when the backend is a different repo.
- Title = the commit summary if single-commit, otherwise a summary of the whole.
- Description template (`.gitlab/merge_request_templates/default.md`):
  ```
  ## What
  ## Why
  ## Screenshots / recording        (before & after for any visual change; mobile + desktop)
  ## How to verify
  ## Checklist
  - [ ] Tests added/updated (component + E2E for new flows)
  - [ ] Keyboard-only pass done; axe clean
  - [ ] No new `'use client'` without justification
  - [ ] Bundle budget unchanged or explained
  - [ ] No PII in logs/URLs/analytics
  - [ ] Docs/standards updated if conventions changed
  ```
- Draft until CI is green and the preview deploy is up. Request review from the feature's CODEOWNERS; a design review for new UI.
- Squash-merge with the MR title as the commit message.

## Review

- Reviewers cite the standard being violated (e.g. "CLAUDE.md rule 2", "state-management.md §Decision ladder", "clean-code §2 Functions"). Findings without a cited rule are suggestions, not blockers.
- Reviewers open the preview deploy and click through the flow — reading the diff isn't a UI review.
- Authors reply to every thread; resolve only after the reviewer agrees or the change is made.
- Two approvals for anything touching auth, payments, CSP, or `components/ui/` primitives (blast radius).

## Releases

- Every merge to `main` deploys to staging automatically; production deploys are promoted from a staging build (same artifact), tagged `vYYYY.MM.DD.N`.
- Feature flags for anything user-visible that ships incrementally. Remove the flag within two releases of full rollout.
- Rollback = redeploy the previous tag. Frontend must tolerate the previous **and** next API version during a rolling deploy — additive API changes only, coordinated in the backend repo.

## For AI agents specifically

- Commit after each completed task from the plan, not at the end of the session.
- Never push to `main`, never force-push, never rewrite history that's been pushed.
- If a hook fails, fix the cause. Don't bypass it.
- Run `pnpm build` once before declaring a task done — it catches server/client boundary errors that unit tests can't.
- Include the ticket reference from the plan in every commit.
