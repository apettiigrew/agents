---
name: git-branch-clean-up
description: Use when cleaning up git branches or worktrees in any repository — deleting merged, squash-merged, or stale local branches, removing leftover worktrees, or getting a repo down to just its default branch. Triggers on "clean up branches", "delete old branches", "prune branches", "/git-branch-clean-up".
---

# git-branch-clean-up

Gets a repo down to its default branch (plus whatever the user keeps) without losing work. Deletion is irreversible in practice, so every branch is *proven* merged before it goes, and the user confirms the list.

## Scope

Default: keep the default branch, the current branch, and branches checked out in worktrees. When the user also wants worktrees gone ("remove all worktrees and their branches"), worktree branches join the candidates. Remote branches stay untouched unless the user asks for them by name or by "remote".

## Steps

### 1. Inventory

```bash
bash "<skill-dir>/scripts/branch-inventory.sh"
```

Read-only, no network. It prints the default branch, then one row per local branch with a class, then the remote branches. Done when every local branch has a class.

| Class | Meaning | Action |
|-------|---------|--------|
| `KEEP-default`, `KEEP-current` | default / checked-out branch | keep |
| `WORKTREE` | checked out in another worktree; note shows dirty-file count | keep, or remove with its worktree when in scope |
| `MERGED` | nothing ahead of default, or every commit has a patch-id twin in default | delete candidate |
| `REVIEW` | commits with no twin in default | prove merged (step 2), else keep |

### 2. Prove each REVIEW branch merged

A squash merge rewrites commits, so `git cherry` cannot see it. For each `REVIEW` branch, and for each `WORKTREE` branch in scope, gather evidence from the default branch's history:

- **Squash commit exists:** find it with `git log <default> --oneline --grep=<subject or MR title>`; then `git diff --stat <branch-tip> <squash-commit>` prints nothing when the content is identical.
- **Merge commit exists:** `git log <default> --oneline --grep="Merge branch '<name>'"`; then `git merge-base --is-ancestor <merged-tip> <branch>` shows whether the branch moved on afterwards.
- **Files landed:** for files the branch added (`git diff --name-status --diff-filter=A <default>...<branch>`), each exists in default at the same path or a clear new home (`git ls-tree -r <default> --name-only`).

An `[gone]` upstream means the remote branch was deleted, typically after an MR merged; treat it as a hint and confirm with one of the checks above.

Done when every `REVIEW` branch is either **verified merged** (name the commit that carries its work) or **kept with a stated reason**. Branches with unaccounted commits stay.

### 3. Confirm

Show the user one table: branch, tip SHA, and the evidence for each deletion; list dirty worktree files that removal would discard; list what stays. Wait for a go-ahead.

### 4. Delete

- Worktrees in scope: invoke the `remove-worktree` skill per worktree (unlocks, force-removes, deletes the branch).
- Remaining branches: `git branch -D <branch>`, printing each `was <sha>`. `-D` is required because git does not count squash merges as merged.

If the permission classifier blocks a batch `git branch -D`, stop, report what was blocked, and hand the user the exact command to run or the settings rule to add.

### 5. Report

Run `git branch -vv` and `git worktree list` and show the result. Include every deleted branch with its SHA (restore with `git branch <name> <sha>`) and the remote branches that remain with their `REMOTE-MERGED` / `REMOTE-REVIEW` class. Deleting remote branches (`git push origin --delete <name>`) needs network and the user's explicit go-ahead; offer it once.
