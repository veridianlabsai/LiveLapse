#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(
  CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1
  pwd
)"

# shellcheck source=bin/common.sh
source "$SCRIPT_DIR/../bin/common.sh"

usage() {
  cat <<'EOF' >&2
Usage: install/install.sh
EOF
}

run_as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
    return
  fi

  log "This action requires root privileges: $*"
  return 1
}

create_default_env_if_missing() {
  local env_path="$LIVELAPSE_ROOT/.env"

  if [[ -f "$env_path" ]]; then
    return 0
  fi

  cp "$LIVELAPSE_ROOT/.env.example" "$env_path"

  if is_darwin; then
    python3 - "$env_path" "$LIVELAPSE_ROOT/data" <<'PY'
import pathlib
import sys

env_path = pathlib.Path(sys.argv[1])
data_dir = sys.argv[2]
content = env_path.read_text()
content = content.replace("LIVELAPSE_DATA_DIR=/mnt/livelapse", f"LIVELAPSE_DATA_DIR={data_dir}", 1)
env_path.write_text(content)
PY
  fi
}

install_darwin_dependencies() {
  local -a packages=()

  if ! command -v brew >/dev/null 2>&1; then
    log "Homebrew is required on macOS. Install it first, then rerun install.sh."
    exit 1
  fi

  command -v yt-dlp >/dev/null 2>&1 || packages+=(yt-dlp)
  command -v ffmpeg >/dev/null 2>&1 || packages+=(ffmpeg)
  command -v jq >/dev/null 2>&1 || packages+=(jq)

  if [[ ${#packages[@]} -eq 0 ]]; then
    log "macOS dependencies already present: yt-dlp, ffmpeg, jq"
    return 0
  fi

  brew install "${packages[@]}"
}

install_linux_dependencies() {
  run_as_root apt-get update
  run_as_root apt-get install -y yt-dlp ffmpeg jq curl bc
}

deploy_systemd_template() {
  local target_unit="/etc/systemd/system/livelapse@.service"
  local temp_unit
  temp_unit="$(mktemp)"

  python3 - "$LIVELAPSE_ROOT/templates/livelapse@.service" "$temp_unit" "$LIVELAPSE_ROOT" <<'PY'
import pathlib
import sys

template = pathlib.Path(sys.argv[1]).read_text()
target = pathlib.Path(sys.argv[2])
root = sys.argv[3]
target.write_text(template.replace("__LIVELAPSE_ROOT__", root))
PY

  run_as_root cp "$temp_unit" "$target_unit"
  rm -f "$temp_unit"

  run_as_root systemctl daemon-reload
}

start_linux_services() {
  local feed_name=""

  while IFS= read -r feed_name; do
    [[ -n "$feed_name" ]] || continue
    run_as_root systemctl enable --now "livelapse@${feed_name}.service"
  done < <(list_feed_names)
}

main() {
  if [[ $# -gt 0 ]]; then
    usage
    exit 1
  fi

  ensure_feeds_exist
  create_default_env_if_missing
  load_env

  case "$(os_name)" in
    Darwin)
      mkdir -p "$LIVELAPSE_DATA_DIR"
      install_darwin_dependencies
      log "Local macOS setup complete. Run bin/capture.sh <feed-name> to verify capture."
      ;;
    Linux)
      run_as_root mkdir -p "$LIVELAPSE_DATA_DIR"
      install_linux_dependencies
      deploy_systemd_template
      start_linux_services
      log "Linux install complete. Systemd services are enabled for configured feeds."
      ;;
    *)
      log "Unsupported platform: $(os_name)"
      exit 1
      ;;
  esac
}

main "$@"
