#!/usr/bin/env bash
set -euo pipefail

RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runners}"
INSTANCES_DIR="$RUNNER_ROOT/instances"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LABEL="com.github.actions.check-runners"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"
RUNNER_COUNT="${RUNNER_COUNT:-9}"

if [[ -n "${RUNNER_NAMES:-}" ]]; then
  # shellcheck disable=SC2206
  RUNNERS=( $RUNNER_NAMES )
else
  RUNNERS=()
  for ((i = 1; i <= RUNNER_COUNT; i++)); do
    RUNNERS+=( "${RUNNER_PREFIX:-$(hostname -s)}-$i" )
  done
fi

# Install a daily LaunchAgent that runs this script at 09:00. launchd is the
# macOS-native cron: it catches up a missed run after sleep, which cron does not.
install() {
  if [[ "$SCRIPT_PATH" == /Volumes/* ]]; then
    echo "Refusing: launchd cannot run scripts from $SCRIPT_PATH (TCC). Deploy to ~/actions-runners/runner-agent (README) and install from there." >&2
    exit 1
  fi
  mkdir -p "$LAUNCH_AGENTS_DIR"
  cat > "$LAUNCH_AGENTS_DIR/$LABEL.plist" <<EOF
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
  <dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$RUNNER_ROOT/check.log</string>
  <key>StandardErrorPath</key>
  <string>$RUNNER_ROOT/check.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$LAUNCH_AGENTS_DIR/$LABEL.plist"
  echo "Installed daily check ($LABEL) at 09:00"
}

check() {
  local latest installed problems=()

  latest="$(gh api repos/actions/runner/releases/latest --jq '.tag_name' 2>/dev/null | tr -d 'v' || true)"
  if [[ -z "$latest" ]]; then
    problems+=("could not fetch latest runner version (gh auth?)")
  fi

  for name in "${RUNNERS[@]}"; do
    if ! launchctl print "gui/$(id -u)/com.github.actions.$name" >/dev/null 2>&1; then
      problems+=("$name is DOWN")
    fi
    installed="$("$INSTANCES_DIR/$name/bin/Runner.Listener" --version 2>/dev/null || echo unknown)"
    if [[ -n "$latest" && "$installed" != "$latest" ]]; then
      problems+=("$name is on $installed, latest is $latest")
    fi
  done

  if [[ ${#problems[@]} -gt 0 ]]; then
    printf '%s\n' "${problems[@]}"
    osascript -e "display notification \"${problems[0]}\" with title \"GitHub Runners: ${#problems[@]} problem(s)\"" 2>/dev/null || true
    exit 1
  fi
  echo "All runners alive and up to date ($latest)"
}

case "${1:-check}" in
  install) install ;;
  check) check ;;
  *) echo "Usage: $0 [check|install]"; exit 1 ;;
esac
