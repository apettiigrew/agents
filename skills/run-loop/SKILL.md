---
name: run-loop
description: Use when the user wants to run an autonomous coding loop on a specific goal until the project's quality gate passes. Triggers on "run the loop", "loop on X", "/run-loop <goal>", or "keep going until tests pass".
---

# run-loop

Autonomous coding loop: iterates DISCOVER → PLAN → EXECUTE → VERIFY → ITERATE until the quality gate is green or max iterations is reached. Self-contained — works in any project.

## Invocation

```
/run-loop <goal>
/run-loop <goal> max <N>
```

**Extract from user message:**
- `GOAL` — the task to complete (required)
- `MAX` — iteration limit (default: 10)

---

## The Loop Process

Run this cycle up to MAX times. Stop early when the quality gate passes AND the goal is met.

### Stage 1 — DISCOVER

Read project context:
1. Read `CLAUDE.md` (or `README.md`) — understand architecture, rules, and the "Done" bar.
2. Read `loop-memory.md` if it exists — skip anything already tried, don't repeat dead ends.
3. Run the quality gate (see below) to establish the current state.
4. Identify the single most-broken or most-relevant thing blocking `GOAL`.

### Stage 2 — PLAN

State in ~3 sentences:
- The single most important change to make this iteration.
- The exact files to touch.
- Confirmation it doesn't violate any architecture rule.

No code yet. If the plan is unclear, re-read DISCOVER output.

### Stage 3 — EXECUTE

Implement the smallest change that advances the plan:
- Stay within the project's architecture (services, validation, query hooks — whatever the project uses).
- Never edit generated files, add undeclared dependencies, or weaken existing tests.
- Surgical: touch only files relevant to `GOAL`.

### Stage 4 — VERIFY

Run the **quality gate** and **self-review**:

**Quality gate** — run in order, stop on first failure:
1. Detect the project's test/lint/type commands:
   - If `CLAUDE.md` defines a "Done" bar, use those exact commands.
   - Otherwise try: `npm test`, `npm run lint`, `npm run typecheck` (skip any that don't exist).
   - Fallback: `npx jest`, `npx eslint src`, `npx tsc --noEmit`.
2. All commands must exit 0.

**Self-review** — read the diff (`git diff`) and ask:
- Does the change actually satisfy `GOAL`?
- Does it respect the project's architecture?
- Does it break or skip any existing test?
- Any unhandled edge cases, auth gaps, or input validation issues?

Output `PASS` or `FAIL - <specific reason>`. Only proceed to ITERATE on PASS.

### Stage 5 — ITERATE

Before stopping each run, update (or create) `loop-memory.md` at the project root:

```markdown
# Loop Memory
**Last run:** <date>
**Current goal:** <GOAL>
**Status:** <In progress | Blocked | Complete>

## Completed
- [x] <what was done>

## Failing
- <what's still broken>

## Blocked
- <what can't proceed and why>

## Notes
- <durable gotchas: tooling quirks, known warnings, etc.>
```

**Pruning rule:** Keep only the current goal, Failing, Blocked, and durable gotchas. Move merged/complete entries to `loop-history.md` (append-only). Don't use memory as a changelog — git history is the changelog.

**Loop decision:**
- Gate green + goal met → **STOP**. Summarize what changed.
- Gate green + goal not met → continue to next iteration.
- Gate red or self-review FAIL → go back to Stage 1.
- MAX iterations reached → **STOP**. Report exactly what's stuck in `loop-memory.md`.

---

## Stop Summary (when loop ends)

Output:
```
✅ Loop complete in <N> iteration(s).
Gate: <green | hit max at N>
Changed: <bullet list of files touched>
Result: <one sentence on what the goal achieved>
```

If stopped at max: list what's still failing and what was tried in `loop-memory.md`.

---

## Notes

- **Max 5 stages per iteration** — if a plan isn't working after 5 attempts at it, record it as Blocked and stop.
- **Be surgical** — read only files you're changing plus their tests, not the whole tree.
- **No new deps** without explicit user approval — ask before installing anything.
- **Never commit to main** — all work stays on the current branch or a new feature branch.
