#!/usr/bin/env bash

set -euo pipefail

LIVELAPSE_ROOT="$(
  CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"

log() {
  printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
}

os_name() {
  uname -s
}

is_darwin() {
  [[ "$(os_name)" == "Darwin" ]]
}

is_linux() {
  [[ "$(os_name)" == "Linux" ]]
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

realpath_portable() {
  python3 - "$1" <<'PY'
import os
import sys

print(os.path.realpath(sys.argv[1]))
PY
}

load_env() {
  local env_file=""

  if [[ -f "$LIVELAPSE_ROOT/.env" ]]; then
    env_file="$LIVELAPSE_ROOT/.env"
  elif [[ -f "$LIVELAPSE_ROOT/.env.example" ]]; then
    env_file="$LIVELAPSE_ROOT/.env.example"
  else
    log "No .env or .env.example file found in $LIVELAPSE_ROOT"
    return 1
  fi

  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a

  : "${LIVELAPSE_DATA_DIR:=/mnt/livelapse}"
  : "${LIVELAPSE_FORMAT:=webp}"
  : "${LIVELAPSE_LOSSLESS:=1}"
  : "${LIVELAPSE_JPEG_QUALITY:=2}"
  : "${LIVELAPSE_MAX_HEIGHT:=720}"
  : "${LIVELAPSE_RETRY_DELAY:=10}"
}

list_feed_records() {
  awk -F'|' '
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", $1)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", $3)
      if ($1 == "" || $2 == "") {
        next
      }
      if ($3 == "") {
        $3 = "1"
      }
      print $1 "|" $2 "|" $3
    }
  ' "$LIVELAPSE_ROOT/feeds.conf"
}

feed_record_by_name() {
  local target="$1"

  list_feed_records | awk -F'|' -v target="$target" '
    $1 == target {
      print
      found = 1
      exit
    }
    END {
      if (!found) {
        exit 1
      }
    }
  '
}

list_feed_names() {
  list_feed_records | cut -d'|' -f1
}

validate_feed_name() {
  local feed_name="$1"

  if [[ ! "$feed_name" =~ ^[A-Za-z0-9-]+$ ]]; then
    log "Invalid feed name: $feed_name"
    return 1
  fi
}

ensure_feeds_exist() {
  if [[ ! -f "$LIVELAPSE_ROOT/feeds.conf" ]]; then
    log "Missing feeds.conf in $LIVELAPSE_ROOT"
    return 1
  fi

  if ! list_feed_records | grep -q '.'; then
    log "feeds.conf must contain at least one feed"
    return 1
  fi
}

ensure_command() {
  local cmd="$1"

  if ! command -v "$cmd" >/dev/null 2>&1; then
    log "Missing required command: $cmd"
    return 1
  fi
}

pids_dir() {
  printf '%s/.pids\n' "$LIVELAPSE_ROOT"
}

ensure_pids_dir() {
  mkdir -p "$(pids_dir)"
}

read_pid_file() {
  local pid_file="$1"

  [[ -f "$pid_file" ]] || return 1
  tr -d '[:space:]' <"$pid_file"
}

pid_is_running() {
  local pid="${1:-}"

  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

cleanup_stale_pid_file() {
  local pid_file="$1"
  local pid=""

  if ! pid="$(read_pid_file "$pid_file" 2>/dev/null)"; then
    return 0
  fi

  if ! pid_is_running "$pid"; then
    rm -f "$pid_file"
  fi
}

feed_pid_file() {
  local feed_name="$1"

  printf '%s/%s.pid\n' "$(pids_dir)" "$feed_name"
}

feed_log_file() {
  local feed_name="$1"

  printf '%s/%s.log\n' "$(pids_dir)" "$feed_name"
}

caffeinate_pid_file() {
  printf '%s/caffeinate.pid\n' "$(pids_dir)"
}

caffeinate_log_file() {
  printf '%s/caffeinate.log\n' "$(pids_dir)"
}
