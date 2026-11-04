#!/usr/bin/env bash
# runner_stats.sh — refresh a machine-readable JSON snapshot of all self-hosted
# runners (per repo: name, GitHub status, labels, launchd service health,
# installed runner version) plus aggregate count and latest runner release.
# Writes STATS_OUT (default ~/actions-runners/runner-stats.json) atomically.
#
#   ./runner_stats.sh            # refresh now
#   ./runner_stats.sh install    # install a daily 09:05 launchd auto-update

set -euo pipefail

REPO_ROOT="${RUNNER_ROOT:-$HOME/actions-runners}"
STATS_OUT="${STATS_OUT:-$REPO_ROOT/runner-stats.json}"
LABEL="com.github.actions.runner-stats"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"
OWNER="${GITHUB_OWNER:-}"  # empty: runners.local.json names the owner

install() {
  if [[ "$SCRIPT_PATH" == /Volumes/* ]]; then
    echo "Refusing: launchd cannot run scripts from $SCRIPT_PATH (TCC). Deploy to ~/actions-runners/runner-agent (README) and install from there." >&2
    exit 1
  fi
  cat > "$HOME/Library/LaunchAgents/$LABEL.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>$SCRIPT_PATH</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>5</integer></dict>
  <key>StandardOutPath</key>
  <string>$REPO_ROOT/runner-stats.log</string>
  <key>StandardErrorPath</key>
  <string>$REPO_ROOT/runner-stats.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$LABEL.plist"
  echo "Installed runner-stats auto-update ($LABEL) daily 09:05 → $STATS_OUT"
}

update() {
  local python3
  python3="$(command -v python3 || echo /usr/bin/python3)"

  # Repos in scope and, for each, the instance dir names (relative to
  # INSTANCES_DIR) or absolute paths. Keep in sync with README inventory.
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

  (export RUNNER_ROOT OWNER STATS_OUT; "$python3" "$script_dir/scripts/_runner_stats_build.py")
}

case "${1:-update}" in
  install) install ;;
  update|"") update ;;
  *) echo "Usage: $0 [update|install]"; exit 1 ;;
esac
