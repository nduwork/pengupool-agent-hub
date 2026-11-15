#!/usr/bin/env bash
set -euo pipefail

GITHUB_OWNER="${GITHUB_OWNER:-}"
GITHUB_REPO="${GITHUB_REPO:-}"
RUNNER_VERSION="${RUNNER_VERSION:-2.337.0}"
RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runners}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,macOS,ARM64}"
RUNNER_GROUP="${RUNNER_GROUP:-}"
RUNNER_WORKDIR_PREFIX="${RUNNER_WORKDIR_PREFIX:-_work}"
REPLACE_EXISTING="${REPLACE_EXISTING:-true}"
RUNNER_COUNT="${RUNNER_COUNT:-9}"
ARCHIVE_DIR="$RUNNER_ROOT/downloads"
TEMPLATE_DIR="$RUNNER_ROOT/template"
INSTANCES_DIR="$RUNNER_ROOT/instances"
PLATFORM="osx-arm64"
SAVED_SETTINGS=( .process_type .launcher )  # files git_runners.sh saves in an instance dir

if [[ -z "$GITHUB_OWNER" || -z "$GITHUB_REPO" ]]; then
  echo "Set GITHUB_OWNER and GITHUB_REPO before running this script."
  exit 1
fi

if [[ -n "${RUNNER_NAMES:-}" ]]; then
  # shellcheck disable=SC2206
  RUNNERS=( $RUNNER_NAMES )
else
  RUNNERS=()
  for ((i = 1; i <= RUNNER_COUNT; i++)); do
    RUNNERS+=( "${RUNNER_PREFIX:-$(hostname -s)}-$i" )
  done
fi

RUNNER_ARCHIVE_URL="${RUNNER_ARCHIVE_URL:-https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-${PLATFORM}-${RUNNER_VERSION}.tar.gz}"
RUNNER_ARCHIVE="$ARCHIVE_DIR/actions-runner-${PLATFORM}-${RUNNER_VERSION}.tar.gz"

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd"
    exit 1
  fi
}

require_gh_auth() {
  if ! gh auth status -h github.com >/dev/null 2>&1; then
    cat <<'EOF'
GitHub CLI is not authenticated or the stored token is invalid.
Run: gh auth login -h github.com
Then verify: gh auth status -h github.com
EOF
    exit 1
  fi
}

repo_api() {
  printf 'repos/%s/%s' "$GITHUB_OWNER" "$GITHUB_REPO"
}

fetch_registration_token() {
  if ! gh api \
    --method POST \
    -H "Accept: application/vnd.github+json" \
    "$(repo_api)/actions/runners/registration-token" \
    --jq '.token'; then
    cat <<EOF
Failed to fetch a GitHub Actions runner registration token for $GITHUB_OWNER/$GITHUB_REPO.
Check that gh is authenticated, the token has access to the repository, and the repo has Actions enabled.
EOF
    exit 1
  fi
}

download_runner() {
  mkdir -p "$ARCHIVE_DIR"

  if [[ ! -f "$RUNNER_ARCHIVE" ]]; then
    echo "Downloading runner $RUNNER_VERSION"
    curl -L "$RUNNER_ARCHIVE_URL" -o "$RUNNER_ARCHIVE"
  else
    echo "Using cached runner archive $RUNNER_ARCHIVE"
  fi
}

prepare_template() {
  echo "Refreshing template at $TEMPLATE_DIR"
  rm -rf "$TEMPLATE_DIR"
  mkdir -p "$TEMPLATE_DIR"
  tar -xzf "$RUNNER_ARCHIVE" -C "$TEMPLATE_DIR"
}

clone_instance() {
  local runner_name="$1"
  local dir="$INSTANCES_DIR/$runner_name"

  # Keep the settings git_runners.sh saved for this runner across the re-create.
  local keep f
  keep="$(mktemp -d)"
  for f in "${SAVED_SETTINGS[@]}"; do
    if [[ -f "$dir/$f" ]]; then mv "$dir/$f" "$keep/"; fi
  done
  rm -rf "$dir"
  cp -cR "$TEMPLATE_DIR" "$dir"
  for f in "${SAVED_SETTINGS[@]}"; do
    if [[ -f "$keep/$f" ]]; then mv "$keep/$f" "$dir/"; fi
  done
  rmdir "$keep"
}

configure_instance() {
  local runner_name="$1"
  local token="$2"
  local dir="$INSTANCES_DIR/$runner_name"
  local args=(
    "--url" "https://github.com/$GITHUB_OWNER/$GITHUB_REPO"
    "--token" "$token"
    "--name" "$runner_name"
    "--labels" "$RUNNER_LABELS"
    "--work" "${RUNNER_WORKDIR_PREFIX}-${runner_name}"
    "--unattended"
  )

  if [[ "$REPLACE_EXISTING" == "true" ]]; then
    args+=( "--replace" )
  fi

  if [[ -n "$RUNNER_GROUP" ]]; then
    args+=( "--runnergroup" "$RUNNER_GROUP" )
  fi

  (
    cd "$dir"
    ./config.sh "${args[@]}"
  )
}

main() {
  require_cmd gh
  require_cmd curl
  require_cmd tar
  require_cmd cp
  require_gh_auth

  mkdir -p "$INSTANCES_DIR"
  download_runner
  prepare_template

  for runner_name in "${RUNNERS[@]}"; do
    echo "Creating instance $runner_name"
    clone_instance "$runner_name"
    token="$(fetch_registration_token)"
    configure_instance "$runner_name" "$token"
  done

  echo
  echo "Runner setup complete."
  echo "Start them with: ./git_runners.sh start"
}

main "$@"
