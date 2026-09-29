#!/usr/bin/env bash
# remove-worktree — unlock a git worktree, force-remove it, and delete its branch.
#
# Usage: remove-worktree.sh <name | path | branch>
#
#   <name>   worktree directory name        e.g. deployment-runbook
#   <path>   full path to the worktree      e.g. .claude/worktrees/deployment-runbook
#   <branch> branch checked out in it       e.g. worktree-deployment-runbook
#
# Destructive: runs `git worktree remove --force` and `git branch -D`.
set -euo pipefail

name="${1:-}"
if [[ -z "$name" ]]; then
  echo "usage: remove-worktree.sh <name | path | branch>" >&2
  exit 2
fi

git rev-parse --git-dir >/dev/null 2>&1 || {
  echo "error: not inside a git repository" >&2
  exit 1
}

# You cannot remove a worktree from within it, so always work from the main worktree.
main_wt="$(git worktree list --porcelain | sed -n 's/^worktree //p' | head -n1)"
cd "$main_wt"

# Normalize the argument: bare name, relative path, or absolute path all resolve the same.
name_base="${name##*/}"
name_abs=""
if [[ "$name" == */* ]]; then
  name_abs="$(cd "$(dirname "$name")" 2>/dev/null && printf '%s/%s' "$(pwd)" "$name_base")" || name_abs=""
fi

# Resolve <name> against the real worktree list. Never assume the branch from the dir name.
matches=()
wt="" ; br=""
while IFS= read -r line || [[ -n "$line" ]]; do
  case "$line" in
    "worktree "*)          wt="${line#worktree }" ;;
    "branch refs/heads/"*) br="${line#branch refs/heads/}" ;;
    "")
      if [[ -n "$wt" ]] &&
         { [[ "$name" == "$wt" ]] ||
           [[ -n "$name_abs" && "$name_abs" == "$wt" ]] ||
           [[ "$name" == "$(basename "$wt")" ]] ||
           [[ "$name" == */* && "$name_base" == "$(basename "$wt")" ]] ||
           [[ -n "$br" && "$name" == "$br" ]]; }; then
        matches+=("${wt}"$'\t'"${br}")
      fi
      wt="" ; br=""
      ;;
  esac
done < <(git worktree list --porcelain; printf '\n')

if [[ ${#matches[@]} -eq 0 ]]; then
  echo "error: no worktree matches '$name'" >&2
  echo "known worktrees:" >&2
  git worktree list >&2
  exit 1
fi
if [[ ${#matches[@]} -gt 1 ]]; then
  echo "error: '$name' matches multiple worktrees:" >&2
  printf '  %s\n' "${matches[@]//$'\t'/  ->  }" >&2
  exit 1
fi

IFS=$'\t' read -r target branch <<<"${matches[0]}"

if [[ "$target" == "$main_wt" ]]; then
  echo "error: refusing to remove the main worktree ($main_wt)" >&2
  exit 1
fi

echo "worktree: $target"
echo "branch:   ${branch:-<detached, no branch>}"

if [[ -n "$(git -C "$target" status --porcelain 2>/dev/null || true)" ]]; then
  echo "warning: uncommitted changes in this worktree will be lost:" >&2
  git -C "$target" status --short >&2 || true
fi

echo "+ git worktree unlock $target"
git worktree unlock "$target" 2>/dev/null || true   # no-op if it was not locked

echo "+ git worktree remove $target --force"
git worktree remove "$target" --force

if [[ -n "$branch" ]]; then
  echo "+ git branch -D $branch"
  git branch -D "$branch"
fi

echo "done."
