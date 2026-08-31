---
name: mr
description: Create a GitLab merge request from the current branch into the project's `main` branch using glab. Use when the user asks to open an MR, create a merge request, or ship the current branch.
---

# MR — Create a Merge Request

Creates a GitLab merge request from the current branch into the repo's `main` branch using the `glab` CLI. **The target branch is always `main`** — do not detect or substitute another default (e.g. `master`).

## Prerequisites (assume true, verify only if a step fails)

- `glab` is installed and authenticated (`glab auth status`).
- Remote `origin` points at a GitLab project.

## Steps

1. **Check state.** Run `git status` and `git branch --show-current`.
   - If on `main` itself, **proceed automatically without prompting**: derive a branch name per the **Branch naming** rules below, create the branch, and move the work onto it.
   - If there are uncommitted changes, **commit them automatically** (stage with `git add -A` if nothing is staged) using a message that matches the repo's commit-message convention. No confirmation needed.
   - Briefly state the branch name and commit message you chose as you go, so the user can intervene if needed — but don't wait for approval.

### Branch naming — always Conventional Commits

Branch names **always** follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/#summary). Do **not** detect or copy the repo's existing branch-naming style — this rule is global, like the `main` target branch.

Git refs cannot contain `:`, so render the spec's `<type>[optional scope]: <description>` as a path:

```
<type>[-<scope>]/<description-in-kebab-case>
```

- **`<type>`** — required, lowercase, from the spec: `feat`, `fix`, plus `build`, `chore`, `ci`, `docs`, `perf`, `refactor`, `style`, `test`. `feat` for a new capability, `fix` for a bug fix; pick the type from what the diff actually does.
- **`<scope>`** — optional; the affected area, appended to the type with a hyphen (`feat-auth/…`, `fix-dashboard/…`). Omit it when the change is repo-wide or the scope adds nothing.
- **`<description>`** — required; short, imperative, lowercase, kebab-case, no trailing period. Aim for 3–6 words.
- **Ticket IDs** — when the work has one, put it first in the description: `feat/tnt-123-add-carrier-filter`. Never let it replace the type.
- **Breaking changes** — do not put `!` in the branch name. Signal breakage with `!` in the MR title and a `BREAKING CHANGE:` footer in the description (step 4).

Examples: `feat/add-carrier-transit-filter`, `fix-dashboard/null-carrier-name-crash`, `chore/bump-prisma-6`, `docs/document-health-endpoint`.

Verify the name is a legal ref before creating it: `git check-ref-format --branch "<name>"`.

2. **Target branch is always `main`.** Do not detect or infer it — `origin/HEAD` may point at `master`, but MRs always target `main`. Use `main` unconditionally.

3. **Push the branch.** `git push -u origin <current-branch>`.

4. **Derive title and description.** Match the repo's conventions (inspect recent commit subjects):
   - **Title:** follow the dominant style — e.g. `TICKET-123: <summary>` if the repo prefixes tickets (pull the ID from the branch name when present), or a `feat:`/`fix:` conventional-commit style, otherwise a concise imperative summary.
   - **Description:** a short "## Summary" with bullets covering what changed and why; add "## Test plan" if tests were run.

5. **Create the MR.**
   ```bash
   glab mr create \
     --source-branch "<current-branch>" \
     --target-branch "main" \
     --title "<title>" \
     --description "<description>" \
     --remove-source-branch \
     --yes
   ```
   - Add `--draft` if the user asked for a draft.
   - Add `--reviewer <username>` / `--assignee <username>` only if the user named people.
   - Use `--squash-before-merge` only if the user asks to squash.

6. **Report.** Print the MR URL returned by `glab` so the user can click through.

## Notes

- Never force-push or rewrite shared history without explicit instruction.
- If `glab mr create` reports an MR already exists for the branch, surface its URL instead of erroring.
- Detect the **MR title and commit-message** format per-repo rather than hardcoding — this skill runs across multiple projects. Two things are global exceptions, never auto-detected:
  - the **target branch is always `main`** (decided 2026-06-29);
  - **branch names always follow Conventional Commits** (decided 2026-08-31), regardless of what the repo's existing branches look like.
- **Run end-to-end without stopping for approval** (decided 2026-06-10): branch off `main`, commit uncommitted work, push, and open the MR autonomously. The user prefers speed over a confirmation gate. The "never without explicit instruction" guards above (force-push, history rewrites) still apply.
