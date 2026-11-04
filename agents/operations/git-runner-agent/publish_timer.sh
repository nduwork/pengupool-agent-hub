#!/usr/bin/env bash
# publish_timer.sh — dispatch one repository's workflow every morning at 06:00
# host-local time (DST-aware via launchd StartCalendarInterval). The repository,
# workflow and inputs are the "publish" entry of runners.local.json (see
# runners.example.json). GitHub's own crons run hours late; they stay
# as a backup and the freshness gate skips a day already published.
#
#   ./publish_timer.sh            # dispatch now
#   ./publish_timer.sh install    # install the daily 06:00 LaunchAgent
#   ./publish_timer.sh uninstall  # remove it
#
# Each dispatch writes ~/actions-runners/publish-dispatch.json; machine_health
# flags a failed one (e.g. expired gh auth).

set -euo pipefail

RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runners}"
LABEL="com.github.actions.publish-timer"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/$(basename "${BASH_SOURCE[0]}")"
CONFIG="${RUNNERS_CONFIG:-$(dirname "$SCRIPT_PATH")/runners.local.json}"
publish() {  # publish() <repo|workflow|fields>: one value of the config's "publish" entry
  /usr/bin/python3 -c 'import json,sys
try:
    p = json.load(open(sys.argv[1])).get("publish", {})
except (OSError, ValueError):
    p = {}
print(" ".join("-f " + x for x in p.get("fields", [])) if sys.argv[2] == "fields" else p.get(sys.argv[2], ""))' "$CONFIG" "$1"
}
REPO="$(publish repo)"
WORKFLOW="$(publish workflow)"
FIELDS="$(publish fields)"
GH="${GH:-/opt/homebrew/bin/gh}"

install() {
  # launchd jobs are TCC-denied /Volumes/* (see README), so they must run
  # from the internal deploy copy.
  if [[ "$SCRIPT_PATH" == /Volumes/* ]]; then
    echo "Refusing: launchd cannot run scripts from $SCRIPT_PATH. Deploy to ~/actions-runners/runner-agent (README) and install from there." >&2
    exit 1
  fi
  cat > "$PLIST" <<EOF
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
  <dict><key>Hour</key><integer>6</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key>
  <string>$RUNNER_ROOT/publish-dispatch.log</string>
  <key>StandardErrorPath</key>
  <string>$RUNNER_ROOT/publish-dispatch.log</string>
</dict>
</plist>
EOF
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  echo "Installed $LABEL: daily 06:00 $(readlink /etc/localtime | sed 's#.*/zoneinfo/##') → $RUNNER_ROOT/publish-dispatch.json"
}

uninstall() {
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  rm -f "$PLIST"
  echo "Removed $LABEL"
}

dispatch() {
  local out rc=0
  if [[ -z "$REPO" || -z "$WORKFLOW" ]]; then  # recorded as a failed dispatch, so machine-health flags it
    out="no publish repo or workflow in $CONFIG (see runners.example.json)" rc=2
  else
    # shellcheck disable=SC2086  # FIELDS is a list of -f arguments
    out="$("$GH" workflow run "$WORKFLOW" -R "$REPO" $FIELDS 2>&1)" || rc=$?
  fi
  echo "$(date -u +%FT%TZ) rc=$rc $out"
  /usr/bin/python3 -c 'import json,sys; json.dump({"at":sys.argv[1],"ok":sys.argv[2]=="0","rc":int(sys.argv[2]),"output":sys.argv[3]}, open(sys.argv[4],"w"), indent=2)' \
    "$(date -u +%FT%TZ)" "$rc" "$out" "$RUNNER_ROOT/publish-dispatch.json"
  return "$rc"
}

case "${1:-dispatch}" in
  dispatch) dispatch ;;
  install) install ;;
  uninstall) uninstall ;;
  *) echo "Usage: $0 [dispatch|install|uninstall]"; exit 1 ;;
esac
