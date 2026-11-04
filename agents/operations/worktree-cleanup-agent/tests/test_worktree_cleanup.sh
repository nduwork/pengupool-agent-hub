#!/usr/bin/env bash
# Self-check for worktree_cleanup.sh. Builds a temp repo covering every class and guard, asserts
# the dry-run table, then asserts that --apply removes and keeps exactly the right worktrees.
# Exits non-zero if any classification breaks.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
script="$here/../scripts/worktree_cleanup.sh"
tmp=$(mktemp -d)
live_pid=""
trap 'kill "$live_pid" 2>/dev/null || true; rm -rf "$tmp"' EXIT

git init -q "$tmp"
cd "$tmp"
git config user.email t@example.org
git config user.name t
printf 'a\n' > f
git add f && git commit -qm init

# merged: no commits of its own
git worktree add -q -b merged "$tmp/wt-merged" HEAD

# unmerged and behind: one commit of its own, then the reference moves on
git worktree add -q -b behind "$tmp/wt-behind" HEAD
printf 'b\n' > "$tmp/wt-behind/g"
git -C "$tmp/wt-behind" add g && git -C "$tmp/wt-behind" commit -qm ahead

printf 'c\n' > h && git add h && git commit -qm advance

# unmerged and ahead only
git worktree add -q -b ahead "$tmp/wt-ahead" HEAD
printf 'd\n' > "$tmp/wt-ahead/i"
git -C "$tmp/wt-ahead" add i && git -C "$tmp/wt-ahead" commit -qm ahead2

# merged branch, dirty working tree
git worktree add -q -b dirty "$tmp/wt-dirty" HEAD
printf 'x\n' > "$tmp/wt-dirty/scratch"

# plain `git stash` writes "WIP on <branch>:", not "On <branch>:"
git worktree add -q -b stashed "$tmp/wt-stash" HEAD
printf 's\n' > "$tmp/wt-stash/j"
git -C "$tmp/wt-stash" add j && git -C "$tmp/wt-stash" stash -q

# locked
git worktree add -q -b locked "$tmp/wt-locked" HEAD
git worktree lock "$tmp/wt-locked"

# a live session whose working directory is inside the worktree
git worktree add -q -b live "$tmp/wt-live" HEAD
( cd "$tmp/wt-live" && exec sleep 60 ) &
live_pid=$!
disown "$live_pid" 2>/dev/null || true

# detached HEAD, clean and an ancestor of the reference
git worktree add -q --detach "$tmp/wt-det" HEAD

# detached HEAD with a commit no branch holds: real work, ask
git worktree add -q --detach "$tmp/wt-det-ahead" HEAD
printf 't\n' > "$tmp/wt-det-ahead/o"
git -C "$tmp/wt-det-ahead" add o && git -C "$tmp/wt-det-ahead" commit -qm detached-work

# detached HEAD whose commit another branch holds: safe to remove
git worktree add -q -b holder "$tmp/wt-holder" HEAD
printf 'u\n' > "$tmp/wt-holder/u"
git -C "$tmp/wt-holder" add u && git -C "$tmp/wt-holder" commit -qm held
held=$(git -C "$tmp/wt-holder" rev-parse HEAD)
git worktree add -q --detach "$tmp/wt-det-held" "$held"

# directory missing: the entry is prunable, the branch is still unmerged
git worktree add -q -b prunable "$tmp/wt-prunable" HEAD
printf 'p\n' > "$tmp/wt-prunable/k"
git -C "$tmp/wt-prunable" add k && git -C "$tmp/wt-prunable" commit -qm prunable
rm -rf "$tmp/wt-prunable"

# directory missing and the branch merged: the entry is pruned and the branch deleted
git worktree add -q -b prunable-merged "$tmp/wt-prunable-merged" HEAD
rm -rf "$tmp/wt-prunable-merged"

# an operation in progress: MERGE_HEAD in the worktree's git dir
git worktree add -q -b inprog "$tmp/wt-inprog" HEAD
: > "$(git -C "$tmp/wt-inprog" rev-parse --absolute-git-dir)/MERGE_HEAD"

# pull-request fixtures behind a gh shim
git worktree add -q -b pr-same "$tmp/wt-pr-same" HEAD
printf 'q\n' > "$tmp/wt-pr-same/l"
git -C "$tmp/wt-pr-same" add l && git -C "$tmp/wt-pr-same" commit -qm pr-same
same_tip=$(git -C "$tmp/wt-pr-same" rev-parse HEAD)

git worktree add -q -b pr-after "$tmp/wt-pr-after" HEAD
printf 'r\n' > "$tmp/wt-pr-after/m"
git -C "$tmp/wt-pr-after" add m && git -C "$tmp/wt-pr-after" commit -qm pr-head
after_head=$(git -C "$tmp/wt-pr-after" rev-parse HEAD)
printf 'z\n' > "$tmp/wt-pr-after/n"
git -C "$tmp/wt-pr-after" add n && git -C "$tmp/wt-pr-after" commit -qm post-merge

mkdir "$tmp/shim"
cat > "$tmp/shim/gh" <<EOF
#!/usr/bin/env bash
[ "\$1" = pr ] && [ "\$2" = view ] || exit 1
case "\$3" in
  pr-same) echo "11 MERGED $same_tip" ;;
  pr-after) echo "12 MERGED $after_head" ;;
  *) exit 1 ;;
esac
EOF
chmod +x "$tmp/shim/gh"
export PATH="$tmp/shim:$PATH"

out=$("$script" --ref main 2>&1) || { echo "$out"; exit 1; }
echo "$out"
fail() { echo "FAIL: $1"; exit 1; }
has() { printf '%s\n' "$out" | grep -q -- "$1"; }

has 'wt-merged.*auto-remove.*ancestor of main' || fail 'merged worktree not auto-removable'
has 'wt-behind.*ask-owner.*unmerged' || fail 'unmerged-behind worktree not ask-owner'
has 'wt-ahead.*ask-owner.*unmerged' || fail 'unmerged-ahead worktree not ask-owner'
has 'wt-dirty.*keep.*dirty' || fail 'dirty guard missing'
has 'wt-stash.*keep.*stash' || fail 'stash guard missing (WIP on ...)'
has 'wt-locked.*keep.*locked' || fail 'locked guard missing'
has 'wt-live.*keep.*live-session' || fail 'live-session guard missing'
has 'wt-det .*auto-remove.*detached HEAD, ancestor of main' || fail 'detached ancestor not auto-removable'
has 'wt-det-ahead.*ask-owner.*no branch holds it' || fail 'detached commit ahead of main not ask-owner'
has 'wt-det-ahead.*1 ahead' || fail 'detached ahead count is not computed against HEAD'
has 'wt-det-held.*auto-remove.*detached HEAD in holder' || fail 'detached commit held by a branch not auto-removable'
has 'wt-prunable.*ask-owner.*prune entry; list, ask owner' || fail 'prunable row mishandled'
has 'wt-prunable-merged.*auto-remove.*prune entry, branch -d' || fail 'merged prunable branch not auto-removable'
has 'wt-inprog.*keep.*in-progress:MERGE_HEAD' || fail 'in-progress guard missing'
has 'wt-pr-same.*auto-remove.*PR #11 MERGED, tip == headRefOid' || fail 'merged PR with exact tip not auto-removable'
has 'wt-pr-after.*ask-owner.*!= headRefOid' || fail 'merged PR with later commits not ask-owner'
has 'main worktree' || fail 'main worktree row missing'
has 'dry run: nothing removed' || fail 'default is not a dry run'

# An unresolved reference must fail closed, not read as "0 ahead".
if "$script" --ref no-such-branch >/dev/null 2>&1; then fail 'unresolved --ref did not fail'; fi

"$script" --apply --ref main >/dev/null 2>&1 || fail 'apply run failed'
[ ! -d "$tmp/wt-merged" ] || fail 'merged worktree not removed'
[ ! -d "$tmp/wt-det" ] || fail 'detached ancestor worktree not removed'
[ ! -d "$tmp/wt-det-held" ] || fail 'detached commit held by a branch not removed'
[ -d "$tmp/wt-det-ahead" ] || fail 'detached worktree with unique commits was removed'
[ ! -d "$tmp/wt-pr-same" ] || fail 'merged-PR worktree not removed'
for w in behind ahead dirty stash locked live inprog; do
  [ -d "$tmp/wt-$w" ] || fail "guarded worktree wt-$w was removed"
done
[ ! -e "$tmp/wt-prunable" ] || fail 'prunable directory unexpectedly exists'
git worktree list --porcelain | grep -q 'wt-prunable' && fail 'prunable entry not pruned'
git worktree list --porcelain | grep -q 'wt-prunable-merged' && fail 'merged prunable entry not pruned'
git rev-parse --verify -q prunable-merged >/dev/null && fail 'merged prunable branch not deleted'
git rev-parse --verify -q inprog >/dev/null || fail 'in-progress branch was deleted'
git rev-parse --verify -q merged >/dev/null && fail 'merged branch not deleted'
git rev-parse --verify -q pr-same >/dev/null && fail 'merged-PR branch not deleted'
for b in behind ahead prunable; do
  git rev-parse --verify -q "$b" >/dev/null || fail "unmerged branch $b was deleted"
done
echo "ok"
