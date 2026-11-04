#!/usr/bin/env bash
# One check: two triage runs resolve different scratch paths, and an explicit
# path the caller passes is kept.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

a="$("$here/ci_triage.sh" --print-paths 1 | head -1)"
b="$("$here/ci_triage.sh" --print-paths 2 | head -1)"
[ "$a" != "$b" ] || { echo "two runs shared a scratch dir: $a"; exit 1; }
case "$a" in
  *ci-triage.*) ;;
  *) echo "unexpected scratch path: $a"; exit 1 ;;
esac

explicit="$("$here/ci_triage.sh" --print-paths 1 /tmp/caller.log /tmp/caller.report | head -1)"
[ "$explicit" = "/tmp/caller.log" ] || { echo "explicit path not kept: $explicit"; exit 1; }

echo "ok: two runs get different scratch dirs; explicit paths are kept"
