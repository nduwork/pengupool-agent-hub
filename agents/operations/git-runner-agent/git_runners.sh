#!/usr/bin/env bash
set -euo pipefail

RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runners}"
INSTANCES_DIR="$RUNNER_ROOT/instances"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
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

ACTION="${1:-start}"

runner_dir() {
  local runner_name="$1"
  printf '%s/%s' "$INSTANCES_DIR" "$runner_name"
}

launch_label() {
  local runner_name="$1"
  printf 'com.github.actions.%s' "$runner_name"
}

plist_path() {
  local runner_name="$1"
  printf '%s/%s.plist' "$LAUNCH_AGENTS_DIR" "$(launch_label "$runner_name")"
}

# Write a LaunchAgent plist with RunAtLoad + KeepAlive so the runner
# starts at login and relaunches automatically after a crash or a
# self-update exit. This is what keeps them always on across reboots.
write_plist() {
  local runner_name="$1"
  local dir
  dir="$(runner_dir "$runner_name")"
  # Background (the default) runs jobs on efficiency cores with throttled I/O. A runner whose jobs are
  # CPU-heavy (renders, builds) gets PROCESS_TYPE=Standard. It is saved in the instance dir, so a later
  # start keeps it, and setup_runners.sh carries it over when it re-creates the dir.
  local process_type="${PROCESS_TYPE:-$(cat "$dir/.process_type" 2>/dev/null || echo Background)}"
  case "$process_type" in
    Background|Standard|Adaptive|Interactive) ;;
    *) echo "Invalid ProcessType '$process_type' for $runner_name (Background, Standard, Adaptive or Interactive)" >&2; return 1 ;;
  esac
  printf '%s\n' "$process_type" > "$dir/.process_type"
  # Optional launcher program placed before bash in the plist (saved as .launcher, like .process_type).
  # macOS charges a launchd job's file access to its first non-Apple program, normally bin*/Runner.Listener,
  # whose path changes on every runner update; a fixed launcher keeps one privacy grant (e.g. external drives).
  local launcher="${LAUNCHER:-$(cat "$dir/.launcher" 2>/dev/null || true)}" launcher_arg=""
  if [[ -n "$launcher" ]]; then
    if [[ "$launcher" != /* || ! -f "$launcher" || ! -x "$launcher" || "$launcher" == *[\&\<\>]* ]]; then
      echo "Launcher '$launcher' for $runner_name must be an absolute path to an executable file, without & < >" \
        "(set LAUNCHER again, or delete $dir/.launcher to stop using one)" >&2
      return 1
    fi
    printf '%s\n' "$launcher" > "$dir/.launcher"
    launcher_arg="    <string>$launcher</string>
"
  fi

  mkdir -p "$LAUNCH_AGENTS_DIR"
  cat > "$(plist_path "$runner_name")" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$(launch_label "$runner_name")</string>
  <key>ProgramArguments</key>
  <array>
${launcher_arg}    <string>/bin/bash</string>
    <string>-lc</string>
    <string>exec ./run.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$dir</string>
  <key>StandardOutPath</key>
  <string>$dir/runner.log</string>
  <key>StandardErrorPath</key>
  <string>$dir/runner.log</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ProcessType</key>
  <string>$process_type</string>
</dict>
</plist>
EOF
}

is_running() {
  local runner_name="$1"
  launchctl print "gui/$(id -u)/$(launch_label "$runner_name")" >/dev/null 2>&1
}

start_runner() {
  local runner_name="$1"
  local dir

  dir="$(runner_dir "$runner_name")"

  if [[ ! -x "$dir/run.sh" ]]; then
    echo "Skipping $runner_name: $dir/run.sh is missing or not executable"
    return 0
  fi

  if is_running "$runner_name"; then
    echo "$runner_name is already running"
    return 0
  fi

  # A bad setting skips this runner only, so a restart still starts the others.
  write_plist "$runner_name" || { echo "Skipping $runner_name: fix the setting above" >&2; return 0; }
  launchctl bootstrap "gui/$(id -u)" "$(plist_path "$runner_name")"

  echo "Started $runner_name"
  echo "  log: $dir/runner.log"
}

stop_runner() {
  local runner_name="$1"

  launchctl bootout "gui/$(id -u)/$(launch_label "$runner_name")" >/dev/null 2>&1 || true
  rm -f "$(plist_path "$runner_name")"

  echo "Stopped $runner_name"
}

status_runner() {
  local runner_name="$1"

  if is_running "$runner_name"; then
    echo "$runner_name: running"
  else
    echo "$runner_name: stopped"
  fi
}

case "$ACTION" in
  start)
    for runner_name in "${RUNNERS[@]}"; do
      start_runner "$runner_name"
    done
    ;;
  stop)
    for runner_name in "${RUNNERS[@]}"; do
      stop_runner "$runner_name"
    done
    ;;
  restart)
    for runner_name in "${RUNNERS[@]}"; do
      stop_runner "$runner_name"
    done
    sleep 2
    for runner_name in "${RUNNERS[@]}"; do
      start_runner "$runner_name"
    done
    ;;
  status)
    for runner_name in "${RUNNERS[@]}"; do
      status_runner "$runner_name"
    done
    ;;
  *)
    echo "Usage: $0 [start|stop|restart|status]"
    exit 1
    ;;
esac
