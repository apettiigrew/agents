---
name: remove-worktree
description: Use when you need to fully delete a git worktree and the branch checked out in it — cleaning up after a merged or abandoned worktree, clearing a stale `git worktree list` entry, or removing a `.claude/worktrees/<name>` directory you no longer need. Handles locked worktrees and unmerged branches. Triggers on "remove worktree", "/remove-worktree <name>", "delete that worktree and branch".
---

# remove-worktree

Tears down a git worktree completely in one step: unlock it (Claude Code locks its own worktrees), force-remove the working tree, then delete the branch that was checked out there. The target is identified by a single argument — worktree directory name, full path, or branch name — resolved against `git worktree list` so the branch is never guessed from the directory name.

## When to use

- A worktree's work is merged or abandoned and you want it and its branch gone
- `git worktree list` shows a stale / leftover entry
- A `.claude/worktrees/<name>` directory is no longer needed

**Do NOT use** to remove the main checkout, or a worktree whose changes you still want kept: this runs `git worktree remove --force` and `git branch -D`, which discard uncommitted changes and unmerged commits. There is no undo — commit or copy anything worth keeping first.

## Usage

Run the bundled script from anywhere inside the repository (the skill-load message shows this skill's directory — substitute it for `<skill-dir>`):

```bash
bash "<skill-dir>/scripts/remove-worktree.sh" <name|path|branch>
```

`<name|path|branch>` accepts any of:

| Form | Example |
|------|---------|
| worktree directory name | `deployment-runbook` |
| full path | `.claude/worktrees/deployment-runbook` |
| branch checked out in it | `worktree-deployment-runbook` |

## What it does

1. `cd` to the repo's **main** worktree — you cannot remove a worktree from inside it
2. Resolve `<name>` to exactly one worktree path + its branch; abort if zero or multiple match, or if it resolves to the main worktree
3. Print any uncommitted changes in that worktree that are about to be lost
4. `git worktree unlock <path>` — no-op if it wasn't locked
5. `git worktree remove <path> --force`
6. `git branch -D <branch>` — skipped if the worktree was detached (no branch)

Equivalent to running, for a worktree at `.claude/worktrees/deployment-runbook` on branch `worktree-deployment-runbook`:

```bash
git worktree unlock .claude/worktrees/deployment-runbook
git worktree remove .claude/worktrees/deployment-runbook --force
git branch -D worktree-deployment-runbook
```

## Common mistakes

- **Assuming the branch name matches the directory name** — it usually differs (`deployment-runbook` dir → `worktree-deployment-runbook` branch). The script reads the real branch from git; don't hardcode it.
- **Running `git worktree remove` from inside the target** — fails with "cannot remove the current working tree". The script avoids this by operating from the main worktree.
- **Expecting recovery** — `--force` + `-D` are destructive. If the branch had unpushed commits, `git reflog` on the main repo may still reach them briefly, but treat the removal as permanent.
