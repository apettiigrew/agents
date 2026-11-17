---
name: trello-review
description: Pull Andrew's Trello data from the Life Design board and report it. Use when the user asks for last week's wins or completed tasks, the month's completed and incomplete tasks (e.g. "full list for October"), or all incomplete backlog items. Read-only. Triggers on "last week's wins", "what did I complete", "incomplete tasks for <month>", "backlog items", "/trello-review".
---

# Trello Review

Read-only report of completed and incomplete tasks from the **Life Design <year>** Trello board.

## Modes

| Ask | Command |
|---|---|
| Last week's wins / completed tasks | `python3 scripts/trello_review.py week` |
| A specific week | `... week --end YYYY-MM-DD` (the Sunday the week ends on) |
| Month: completed + incomplete | `python3 scripts/trello_review.py month --month 10 [--year 2026]` |
| All incomplete backlog items | `python3 scripts/trello_review.py backlog` |

Run the script from this skill's directory. Credentials come from `TRELLO_API_KEY` / `TRELLO_TOKEN`, else `~/Documents/projects/life-os/Life-OS/.env` (override with `--env-file`). Never print the credentials.

**"Last week" default:** the Mon–Sun week ending on the most recent Sunday, today included. On a Sunday that is the week ending today. State the date range in the answer, and confirm if the user's phrasing could mean a different week.

## Data sources (what the script prints)

- **week:** the weekly card (`<Month> Week N`, newest created on or before the week's end), each day card (`October 21st, 2026`) in range, days with no card, and Done-list cards by last-activity date.
- **month:** the month card (`October 2026`), all `<Month> Week N` cards, all day cards in the month, Done-list cards by last activity.
- **backlog:** open cards (and their unchecked checklist items) in the Backlog, Follow Ups, Mind Dump, Now, and Next Week Sprint lists, plus open `| [ ] |` rows in `Life-OS/tasks/backlog.md`.

Lines prefixed `x` are complete. Checklist headers show `done/total`.

## Building the report

1. **Dedupe.** The same task often appears on the weekly card, several day cards, and the Done list. Report it once.
2. **Don't list items done later as incomplete.** If an unchecked item on one card is checked on a later card or is in the Done list, count it as done (e.g. "Setup USD Account with Sendana" unchecked Oct 20, done Oct 21).
3. **Flag conflicts. Don't resolve them silently.** For example, an item checked on the weekly card but unchecked on the month card, or a One Thing left unchecked even though related work is in the Done list.
4. **Caveat the Done list.** Trello stores the last-activity date, not the completion date. Done cards touched on the first day of the range may have been completed earlier.
5. **Summarize habits.** Don't list every unchecked daily habit. Give the miss pattern instead (e.g. "Night routine checked 2 of 5 day cards").
6. **Flag a stale `backlog.md`** if its "This Week" section is from a past week.

## Output format

- Lead with a 2–4 bullet headline: the One Thing status, the Top 3 hit rate, and the standout day.
- **week:** a table of Category | Task/Goal | Status | Notes. One task per row. Categories: One Thing, [Andrew] Top 3, [Work] Top 3, Habits, Daily, Errands & Life, Everything else.
- **month:** a "Completed" table grouped by area (project, work, learning, trading/finance, baby/family, life). Then an "Incomplete" section: month card outcomes first, then weekly and day card leftovers by source date, then conflicts and habit misses.
- **backlog:** group by source (Trello Backlog, Follow Ups with due dates and overdue marked, Mind Dump grouped by theme, local `backlog.md` by category). Call out duplicates across sources.
- No em dashes. No emojis unless the user asks.

## Writes

The skill is read-only. Writing results anywhere (Notion journal page, Trello, `backlog.md`) needs the user's explicit go-ahead in that session. Show the exact content first. For Notion, fetch the page, then use `notion-update-page` with `update_content` anchored on the question text.

## PII

Cards contain names and personal finance amounts. Remind the user once per session to handle this data carefully per Shipium guidelines.
