#!/usr/bin/env bash
# Triage a failed run by hand, the same way the reusable workflow does.
#
#   cd <checkout of the failing repository at the failing commit>
#   gh run view <run-id> --log-failed | tail -n 400 | ci_triage.sh <run-id>
# Two copies of this helper never share a scratch directory: with no paths given
# it writes failed.log and report.md under a fresh `mktemp -d` and prints them.
#   ci_triage.sh <run-id> <log-file> [<report-file>]   # explicit paths win
#
# The local model runner (pi + Ollama today; see run_model below) may edit the
# working tree; review `git diff` and the report. It runs with no GitHub token
# and no API keys. Keep the prompt in step with
# .github/workflows/triage.yml.
set -euo pipefail

print_paths=0
if [ "${1:-}" = "--print-paths" ]; then print_paths=1; shift; fi
run_id="${1:?usage: ci_triage.sh <run-id> [log-file [report-file]]}"
shift
if [ "$#" -ge 2 ]; then
  log_file="$1"
  report_file="$2"
elif [ "$#" -eq 1 ]; then
  log_file="$1"
  report_file="$(mktemp -d "${TMPDIR:-/tmp}/ci-triage.XXXXXX")/report.md"
else
  workdir="$(mktemp -d "${TMPDIR:-/tmp}/ci-triage.XXXXXX")"
  log_file="$workdir/failed.log"
  report_file="$workdir/report.md"
fi
if [ "$print_paths" = 1 ]; then printf '%s\n%s\n' "$log_file" "$report_file"; exit 0; fi
if [ "$#" -eq 0 ]; then cat > "$log_file"; fi
model="${CI_DEBUG_MODEL:-qwen3.8:27b}"
checks="${CI_DEBUG_CHECKS:-the checks AGENTS.md or README.md documents}"

# read -d rather than $(cat <<EOF): macOS bash 3.2 misparses a heredoc in $().
read -r -d '' prompt <<EOF || true
A GitHub Actions run failed in this repository (run ${run_id}).
The failed steps' log is in ${log_file}. Read AGENTS.md first if it exists.

Find the root cause and fix it with the smallest change that addresses it:
- Read the log, then the code the failing step runs. Trace the cause; do not
  patch the symptom.
- If a code change fixes it, make it and run ${checks}.
- If the cause is outside the code (an outage, an expired credential, a runner
  problem), change nothing and say so.

Never: commit, push, merge, run gh, touch .github/workflows, print or read
secrets, keys or tokens, or delete files you did not create.

Finish with a short report in plain prose: what failed, the cause, what you
changed (file and why) or why nothing was changed, and the check result.
EOF

# The engine: a local model runner. Swap the pi line to use another one; keep the
# environment scrubbed and the model on this machine.
run_model() {
  env -u GH_TOKEN -u GITHUB_TOKEN -u OPENAI_API_KEY -u ANTHROPIC_API_KEY -u BRAVE_API_KEY \
    pi -p --provider ollama --model "$model" --no-session --tools read,bash,edit,write "$1"
}

run_model "$prompt" > "$report_file" 2>&1 \
  || echo "The model runner exited with an error; see the report above." >> "$report_file"
echo "report: $report_file"
