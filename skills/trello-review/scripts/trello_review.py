#!/usr/bin/env python3
"""Read-only Trello dump for the Life Design board: week, month, or backlog.

Usage:
  trello_review.py week    [--end YYYY-MM-DD]
  trello_review.py month   [--month 10] [--year 2026]
  trello_review.py backlog [--backlog-md PATH]

Credentials: TRELLO_API_KEY / TRELLO_TOKEN from the environment, else from --env-file.
"""
import argparse
import calendar
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

API = "https://api.trello.com/1"
DEFAULT_ENV = os.path.expanduser("~/Documents/projects/life-os/Life-OS/.env")
DEFAULT_BACKLOG_MD = os.path.expanduser("~/Documents/projects/life-os/Life-OS/tasks/backlog.md")
DAY_CARD = re.compile(r"^([A-Z][a-z]+) (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})$")
WEEK_CARD = re.compile(r"^([A-Z][a-z]+) Week (\d+)")
BACKLOG_LISTS = ("Backlog", "Follow Ups", "Mind Dump", "Now", "Next Week Sprint")


def load_creds(env_file):
    key, token = os.environ.get("TRELLO_API_KEY"), os.environ.get("TRELLO_TOKEN")
    if key and token:
        return key, token
    vals = {}
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals["TRELLO_API_KEY"], vals["TRELLO_TOKEN"]


def get(path, creds, **params):
    params.update(key=creds[0], token=creds[1])
    with urllib.request.urlopen(f"{API}{path}?{urllib.parse.urlencode(params)}") as r:
        return json.load(r)


def created(card):
    # Trello ids start with an 8-hex-digit unix timestamp
    return datetime.fromtimestamp(int(card["id"][:8], 16), timezone.utc).date()


def day_card_date(name):
    m = DAY_CARD.match(name.strip())
    if not m:
        return None
    try:
        return datetime.strptime(f"{m[1]} {m[2]} {m[3]}", "%B %d %Y").date()
    except ValueError:
        return None


def activity(card):
    # Trello stores UTC; compare in local time so evening activity lands on the right day
    return datetime.fromisoformat(card["dateLastActivity"].replace("Z", "+00:00")).astimezone().date().isoformat()


def print_card(card):
    print(f"\n## {card['name']}" + (" (archived)" if card["closed"] else ""))
    if card.get("due"):
        print(f"due: {card['due'][:10]}  dueComplete: {card['dueComplete']}")
    for cl in sorted(card["checklists"], key=lambda c: c["pos"]):
        items = sorted(cl["checkItems"], key=lambda x: x["pos"])
        done = sum(x["state"] == "complete" for x in items)
        print(f" [{cl['name']}] {done}/{len(items)}")
        for x in items:
            print(f"   {'x' if x['state'] == 'complete' else ' '} {x['name']}")


def load_board(creds, year):
    boards = get("/members/me/boards", creds, fields="name,closed")
    board = next(b for b in boards if b["name"] == f"Life Design {year}" and not b["closed"])
    lists = {l["id"]: l["name"] for l in get(f"/boards/{board['id']}/lists", creds, fields="name")}
    cards = get(f"/boards/{board['id']}/cards/all", creds,
                fields="name,idList,closed,dateLastActivity,due,dueComplete", checklists="all")
    for c in cards:
        c["list"] = lists.get(c["idList"], "?")
    return cards


def in_list(card, prefix):
    return card["list"].startswith(prefix)


def done_list(cards, start, end):
    print(f"\n## Done list (last activity {start}..{end}; activity date != completion date)")
    for c in sorted((c for c in cards if in_list(c, "Done") and str(start) <= activity(c) <= str(end)),
                    key=activity):
        print(f"   {activity(c)} {c['name']}")


def cmd_week(args, creds):
    today = date.today()
    end = date.fromisoformat(args.end) if args.end else today - timedelta(days=(today.weekday() + 1) % 7)
    start = end - timedelta(days=6)
    print(f"# Week {start} (Mon) .. {end} (Sun)")
    cards = load_board(creds, start.year)
    weekly = [c for c in cards if in_list(c, "Weekly") and WEEK_CARD.match(c["name"]) and created(c) <= end]
    if weekly:
        # the week card is the newest one created on or before the week ends
        print_card(max(weekly, key=created))
    else:
        print("\n(no weekly card found)")
    days = sorted((c for c in cards
                   if in_list(c, "Daily") and day_card_date(c["name"])
                   and start <= day_card_date(c["name"]) <= end),
                  key=lambda c: day_card_date(c["name"]))
    have = {day_card_date(c["name"]) for c in days}
    for c in days:
        print_card(c)
    missing = [str(start + timedelta(days=i)) for i in range(7) if start + timedelta(days=i) not in have]
    print(f"\n(no day card for: {', '.join(missing) or 'none'})")
    done_list(cards, start, end)


def cmd_month(args, creds):
    today = date.today()
    year, month = args.year or today.year, args.month or today.month
    name = calendar.month_name[month]
    start, end = date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    print(f"# {name} {year}")
    cards = load_board(creds, year)
    for c in cards:
        if in_list(c, "Monthly") and c["name"].strip() == f"{name} {year}":
            print_card(c)
    weeks = [c for c in cards if in_list(c, "Weekly") and (m := WEEK_CARD.match(c["name"])) and m[1] == name
             and created(c).year == year]
    for c in sorted(weeks, key=lambda c: int(WEEK_CARD.match(c["name"])[2])):
        print_card(c)
    for c in sorted((c for c in cards
                     if day_card_date(c["name"]) and start <= day_card_date(c["name"]) <= end),
                    key=lambda c: day_card_date(c["name"])):
        print_card(c)
    done_list(cards, start, end)


def cmd_backlog(args, creds):
    cards = load_board(creds, date.today().year)
    for prefix in BACKLOG_LISTS:
        open_cards = [c for c in cards if in_list(c, prefix) and not c["closed"]]
        print(f"\n# Trello list: {prefix} ({len(open_cards)} open)")
        for c in sorted(open_cards, key=lambda c: c.get("due") or "9999"):
            print(f"   {(c.get('due') or '')[:10]:10} {c['name']}")
            for cl in c["checklists"]:
                for x in cl["checkItems"]:
                    if x["state"] != "complete":
                        print(f"              - {x['name']}")
    if os.path.exists(args.backlog_md):
        print(f"\n# Local {args.backlog_md} (open rows, by section)")
        section = ""
        with open(args.backlog_md) as f:
            for line in f:
                if line.startswith("## "):
                    section = line[3:].strip()
                elif line.startswith("| [ ] |"):
                    print(f"   [{section}] {line.strip()}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["week", "month", "backlog"])
    p.add_argument("--end", help="week: last day (Sunday) of the week, default = most recent Sunday incl. today")
    p.add_argument("--month", type=int)
    p.add_argument("--year", type=int)
    p.add_argument("--backlog-md", default=DEFAULT_BACKLOG_MD)
    p.add_argument("--env-file", default=DEFAULT_ENV)
    args = p.parse_args()
    creds = load_creds(args.env_file)
    {"week": cmd_week, "month": cmd_month, "backlog": cmd_backlog}[args.mode](args, creds)


if __name__ == "__main__":
    sys.exit(main())
