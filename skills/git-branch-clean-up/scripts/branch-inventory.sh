#!/usr/bin/env bash
# branch-inventory — classify a repo's local branches for cleanup. Read-only, no network.
#
# Usage: branch-inventory.sh
#
# Prints one tab-separated row per local branch:
#   CLASS  BRANCH  TIP  AHEAD  UNMATCHED  UPSTREAM  NOTE
#
#   KEEP-default   the default branch
#   KEEP-current   the branch checked out in the main worktree
#   WORKTREE       checked out in another worktree (NOTE holds path + dirty-file count)
#   MERGED         nothing ahead of default, or every commit has a patch-id match in default
#   REVIEW         commits not matched in default — squash merge or unmerged work; verify
#
# AHEAD = commits not reachable from default. UNMATCHED = commits with no patch-id twin in default.
# Then one row per remote branch: REMOTE-MERGED | REMOTE-REVIEW  REF  TIP.
set -euo pipefail

git rev-parse --git-dir >/dev/null 2>&1 || {
  echo "error: not inside a git repository" >&2
  exit 1
}

default="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || true)"
if [[ -z "$default" ]]; then
  for candidate in main master; do
    if git show-ref --verify --quiet "refs/heads/$candidate"; then default="$candidate"; break; fi
  done
fi
[[ -n "$default" ]] || { echo "error: cannot determine the default branch" >&2; exit 1; }

main_wt="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -n1)"
current="$(git -C "$main_wt" branch --show-current)"

# "branch<TAB>path" for every worktree except the main one.
other_worktrees="$(git worktree list --porcelain | awk '
  /^worktree /{path=substr($0,10); n++}
  /^branch refs\/heads\//{ if (n>1) print substr($0,19) "\t" path }')"

echo "default branch: $default   main worktree: $main_wt"
printf 'CLASS\tBRANCH\tTIP\tAHEAD\tUNMATCHED\tUPSTREAM\tNOTE\n'

git for-each-ref refs/heads --format='%(refname:short)|%(upstream:short)|%(upstream:track)' |
while IFS='|' read -r branch upstream track; do
  tip="$(git rev-parse --short "$branch")"
  ahead="$(git rev-list --count "$default..$branch")"
  unmatched="$(git cherry "$default" "$branch" | awk '/^\+/{n++} END{print n+0}')"
  up="${upstream:-none}${track:+ $track}"
  note=""
  wt_path="$(printf '%s\n' "$other_worktrees" | awk -F'\t' -v b="$branch" '$1==b{print $2}')"

  if   [[ "$branch" == "$default" ]]; then class="KEEP-default"
  elif [[ "$branch" == "$current" ]]; then class="KEEP-current"
  elif [[ -n "$wt_path" ]]; then
    class="WORKTREE"
    dirty="$(git -C "$wt_path" status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
    note="$wt_path (dirty files: $dirty)"
  elif [[ "$ahead" == 0 || "$unmatched" == 0 ]]; then class="MERGED"
  else class="REVIEW"
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$class" "$branch" "$tip" "$ahead" "$unmatched" "$up" "$note"
done

if git show-ref --verify --quiet "refs/remotes/origin/$default"; then
  merged_remote="$(git branch -r --merged "origin/$default" --format='%(refname:short)')"
  git branch -r --format='%(refname:short)' | grep -vE "^origin(/HEAD)?$|^origin/$default$" |
  while IFS= read -r ref; do
    if printf '%s\n' "$merged_remote" | grep -qx "$ref"; then class="REMOTE-MERGED"; else class="REMOTE-REVIEW"; fi
    printf '%s\t%s\t%s\n' "$class" "$ref" "$(git rev-parse --short "$ref")"
  done
fi
