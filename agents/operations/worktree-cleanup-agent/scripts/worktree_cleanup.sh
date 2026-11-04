#!/usr/bin/env bash
# Classify this repository's git worktrees and remove only the provably merged, idle ones.
# Usage: worktree_cleanup.sh [--apply] [--ref <branch>]     (default: dry-run)
# Never removes the main worktree, a dirty/locked/stashed worktree, or one with a live session in it.
set -uo pipefail

apply=0 ref=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) apply=1 ;;
    --ref) ref=$2; shift ;;
    -h|--help) sed -n '2,4p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

if ! wts=$(git worktree list --porcelain 2>/dev/null) || [ -z "$wts" ]; then
  echo "not a git repository" >&2; exit 2
fi

w_path=() w_head=() w_branch=() w_locked=()
while IFS= read -r line; do
  case "$line" in
    "worktree "*) w_path+=("${line#worktree }"); w_head+=(""); w_branch+=(""); w_locked+=("") ;;
    "HEAD "*)     w_head[${#w_head[@]}-1]=${line#HEAD } ;;
    "branch refs/heads/"*) w_branch[${#w_branch[@]}-1]=${line#branch refs/heads/} ;;
    "locked"*)    w_locked[${#w_locked[@]}-1]=1 ;;
  esac
done <<< "$wts"

[ -n "$ref" ] || ref=${w_branch[0]:-}
[ -n "$ref" ] || ref=main
# Fail closed: an unresolved reference must stop the run, never read as "0 ahead".
if ! git rev-parse --verify --quiet "refs/heads/$ref" >/dev/null; then
  echo "reference branch not found: $ref (pass --ref <branch>)" >&2
  exit 2
fi

live_cwds=$(lsof -w -d cwd -Fpn 2>/dev/null | sed -n 's/^n//p')
is_live() {
  [ -n "$live_cwds" ] || return 1
  printf '%s\n' "$live_cwds" | grep -qxF -- "$1" && return 0
  printf '%s\n' "$live_cwds" | grep -qF -- "$1/"
}
has_stash() {
  git stash list 2>/dev/null | awk -v a="On $1:" -v w="WIP on $1:" \
    'index($0,a) || index($0,w) {f=1} END{exit !f}'
}
dirty() { [ -n "$(git -C "$1" status --porcelain 2>/dev/null | head -n1)" ]; }
in_progress() {
  local gd f
  gd=$(git -C "$1" rev-parse --absolute-git-dir 2>/dev/null) || return 1
  for f in BISECT_LOG rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD; do
    [ -e "$gd/$f" ] && { echo "$f"; return 0; }
  done
  return 1
}

r_path=() r_branch=() r_tip=() r_class=() r_ev=() r_guards=() r_action=() r_delwt=() r_delflag=()
row() {  # path branch tip behind/ahead class evidence guards action delwt delflag
  r_path+=("$1"); r_branch+=("$2"); r_tip+=("$3"); r_class+=("$5")
  r_ev+=("$6"); r_guards+=("$7"); r_action+=("$8"); r_delwt+=("$9"); r_delflag+=("${10}")
  printf '%-46s | %-30s | %-10s | %-7s | %-10s | %-40s | %-12s | %s\n' \
    "$1" "${2:--}" "${3:0:10}" "$4" "$5" "$6" "${7:--}" "$8"
}
printf '%-46s | %-30s | %-10s | %-7s | %-10s | %-40s | %-12s | %s\n' \
  PATH BRANCH TIP BEH/AHD CLASS EVIDENCE GUARDS ACTION

for i in "${!w_path[@]}"; do
  p=${w_path[$i]} b=${w_branch[$i]} h=${w_head[$i]}
  if [ "$i" -eq 0 ]; then row "$p" "$b" "$h" "-" never "main worktree" "" keep 0 ""; continue; fi

  prunable=0
  [ -d "$p" ] || prunable=1

  guards=()
  [ -n "${w_locked[$i]}" ] && guards+=("locked")
  [ -n "$b" ] && has_stash "$b" && guards+=("stash")
  if [ "$prunable" = 0 ]; then
    dirty "$p" && guards+=("dirty")
    is_live "$p" && guards+=("live-session")
    f=$(in_progress "$p") && guards+=("in-progress:$f")
  fi
  guardstr=$(IFS=,; echo "${guards[*]:-}")

  behind="" ahead=""
  obj=${b:-$h}
  if [ -n "$obj" ]; then
    behind=$(git rev-list --count "$obj..$ref" 2>/dev/null) || behind=""
    ahead=$(git rev-list --count "$ref..$obj" 2>/dev/null) || ahead=""
  fi
  ba="?/?"; [ -n "$ahead" ] && ba="${behind}/${ahead}"

  if [ -z "$b" ]; then
    if [ -z "$ahead" ]; then
      class=ask-owner ev="detached HEAD ${h:0:7}, cannot resolve" act="list, ask owner" dflag=""
    elif [ "$ahead" = 0 ]; then
      class=auto-remove ev="detached HEAD, ancestor of $ref" act="remove worktree" dflag=""
    else
      holds=$(git for-each-ref --contains "$h" --format='%(refname:short)' refs/heads refs/remotes 2>/dev/null \
                | grep -v '/HEAD$' | sort -u | head -n3 | paste -sd, - | sed 's/,/, /g')
      if [ -n "$holds" ]; then
        class=auto-remove ev="detached HEAD in ${holds}" act="remove worktree" dflag=""
      else
        class=ask-owner ev="detached HEAD, ${ahead} ahead, no branch holds it" \
          act="list, ask owner" dflag=""
      fi
    fi
  elif [ "$b" = "$ref" ]; then
    class=never ev="same as reference $ref" act="keep" dflag=""
  elif [ -z "$ahead" ]; then
    class=ask-owner ev="cannot resolve $b against $ref" act="list, ask owner" dflag=""
  elif [ "$ahead" = 0 ]; then
    class=auto-remove ev="ancestor of $ref" act="remove worktree, branch -d" dflag=-d
  else
    pr=$(gh pr view "$b" --json number,state,headRefOid \
           --template '{{.number}} {{.state}} {{.headRefOid}}' 2>/dev/null || true)
    if [ -n "$pr" ]; then
      read -r prn prstate prhead <<< "$pr"
      if [ "$prstate" = MERGED ] && [ "$prhead" = "$h" ]; then
        class=auto-remove ev="PR #${prn} MERGED, tip == headRefOid" \
          act="remove worktree, branch -D" dflag=-D
      elif [ "$prstate" = MERGED ]; then
        class=ask-owner ev="PR #${prn} MERGED but tip ${h:0:7} != headRefOid ${prhead:0:7}" \
          act="list, ask owner" dflag=""
      else
        class=ask-owner ev="PR #${prn} ${prstate}" act="list, ask owner" dflag=""
      fi
    else
      class=ask-owner ev="unmerged, ${ahead} ahead of ${ref}" act="list, ask owner" dflag=""
    fi
  fi

  if [ -n "$guardstr" ]; then class=keep ev="guarded" act="keep" dflag=""; fi
  if [ "$prunable" = 1 ]; then
    case "$act" in
      "remove worktree") act="prune entry" ;;
      "remove worktree, branch -d") act="prune entry, branch -d" ;;
      "remove worktree, branch -D") act="prune entry, branch -D" ;;
      keep) ;;
      *) act="prune entry; $act" ;;
    esac
  fi
  delwt=0
  [ "$class" = auto-remove ] && [ "$prunable" = 0 ] && case "$act" in *"remove worktree"*) delwt=1 ;; esac

  row "$p" "$b" "$h" "$ba" "$class" "$ev" "$guardstr" "$act" "$delwt" "$dflag"
done

for i in "${!r_path[@]}"; do
  [ "${r_class[$i]}" = auto-remove ] && [ -n "${r_branch[$i]}" ] && [ -n "${r_delflag[$i]}" ] &&
    echo "restore: git branch ${r_branch[$i]} ${r_tip[$i]}"
done

if [ "$apply" -eq 0 ]; then
  echo "dry run: nothing removed (run with --apply)"
  exit 0
fi
# Prune first: a missing-directory entry still counts as a checked-out branch, so `branch -d`
# would refuse until its admin files are gone, and the branch would be orphaned.
git worktree prune && echo "pruned stale worktree entries"
for i in "${!r_path[@]}"; do
  [ "${r_class[$i]}" = auto-remove ] || continue
  p=${r_path[$i]} b=${r_branch[$i]}
  if [ "${r_delwt[$i]}" = 1 ]; then
    git worktree remove "$p" || { echo "kept worktree (remove failed): $p"; continue; }
    echo "removed worktree: $p"
  fi
  [ -n "$b" ] && [ "$b" != "$ref" ] && [ -n "${r_delflag[$i]}" ] || continue
  git branch "${r_delflag[$i]}" "$b" && echo "deleted branch: $b" || echo "kept branch (delete failed): $b"
done
