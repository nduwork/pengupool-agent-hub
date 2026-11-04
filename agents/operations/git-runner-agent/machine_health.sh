#!/usr/bin/env bash
# machine_health.sh — boot-time + periodic machine health for the runner box.
#
# Detects kernel panics (notably the panic that caused the current boot, so a
# RunAtLoad check fires right after a panic reboot) and GitHub Actions runs left
# in_progress across a reboot (orphaned — a self-hosted job whose host died can
# never resume). Writes ~/actions-runners/machine-health.json and notifies via
# macOS when there is a new problem.
#
#   ./machine_health.sh            # run the check now
#   ./machine_health.sh install    # RunAtLoad (+ hourly) launchd watcher
#
# Redispatch of orphaned runs is OFF by default (REDISPATCH=0). A blind re-run
# could double-upload a TestFlight build, so it stays behind the flag until the
# user approves; with REDISPATCH=1 the check only LOGS what it would re-run.

set -euo pipefail

RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runners}"
LABEL="com.github.actions.machine-health"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python_bin() {
  command -v python3 || echo /usr/bin/python3
}

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
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>StandardOutPath</key>
  <string>$RUNNER_ROOT/machine-health.log</string>
  <key>StandardErrorPath</key>
  <string>$RUNNER_ROOT/machine-health.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$LABEL.plist"
  echo "Installed machine-health watch ($LABEL): RunAtLoad + hourly → $RUNNER_ROOT/machine-health.json"
}

check() {
  ( export RUNNER_ROOT; "$(python_bin)" "$SCRIPT_DIR/scripts/_machine_health.py" )
}

# Repair is explicit and opt-in: it takes the signing action's (keychain_lock)
# non-blocking lock, so it can never race a live signing job.
repair() {
  ( export RUNNER_ROOT KEYCHAIN_REPAIR=1; "$(python_bin)" "$SCRIPT_DIR/scripts/_machine_health.py" )
}

case "${1:-check}" in
  install) install ;;
  check|"") check ;;
  repair) repair ;;
  *) echo "Usage: $0 [check|install|repair]"; exit 1 ;;
esac
