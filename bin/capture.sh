#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(
  CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1
  pwd
)"

# shellcheck source=bin/common.sh
source "$SCRIPT_DIR/common.sh"

usage() {
  cat <<'EOF' >&2
Usage: bin/capture.sh <feed-name>
EOF
}

is_direct_ffmpeg_input() {
  case "$1" in
    rtsp://*|rtsps://*|rtmp://*|rtmps://*|srt://*|udp://*|tcp://*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

resolve_stream_url() {
  local url="$1"
  local selector="bestvideo[height<=${LIVELAPSE_MAX_HEIGHT}]/best[height<=${LIVELAPSE_MAX_HEIGHT}]/bestvideo/best"

  yt-dlp -g -f "$selector" "$url" | awk 'NR == 1 { print; exit }'
}

build_ffmpeg_output_args() {
  local format="$1"

  FF_OUTPUT_EXT="$format"
  FF_OUTPUT_ARGS=()

  case "$format" in
    webp)
      FF_OUTPUT_ARGS=(-c:v libwebp -quality 100 -compression_level 4 -lossless "$LIVELAPSE_LOSSLESS")
      ;;
    png)
      FF_OUTPUT_ARGS=(-c:v png)
      ;;
    jpg|jpeg)
      FF_OUTPUT_EXT="jpg"
      FF_OUTPUT_ARGS=(-q:v "$LIVELAPSE_JPEG_QUALITY")
      ;;
    *)
      log "Unsupported LIVELAPSE_FORMAT: $format"
      return 1
      ;;
  esac
}

warn_if_high_fps() {
  local fps="$1"

  if awk "BEGIN { exit !($fps > 1) }"; then
    log "Warning: fps values above 1 may reuse the same second-level filename in Phase 0"
  fi
}

run_ffmpeg_capture() {
  local input_url="$1"
  local source_url="$2"
  local fps="$3"
  local output_pattern="$4"

  local -a ffmpeg_input_args
  ffmpeg_input_args=(-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10 -i "$input_url")

  if is_direct_ffmpeg_input "$source_url"; then
    ffmpeg_input_args=(-i "$source_url")
    if [[ "$source_url" == rtsp://* || "$source_url" == rtsps://* ]]; then
      ffmpeg_input_args=(-rtsp_transport tcp -i "$source_url")
    fi
  fi

  TZ=UTC ffmpeg \
    -hide_banner \
    -loglevel warning \
    -nostdin \
    "${ffmpeg_input_args[@]}" \
    -map 0:v:0 \
    -an \
    -vf "fps=${fps}" \
    -f image2 \
    -strftime 1 \
    "${FF_OUTPUT_ARGS[@]}" \
    "$output_pattern"
}

main() {
  local feed_name="${1:-}"

  if [[ -z "$feed_name" ]]; then
    usage
    exit 1
  fi

  ensure_command yt-dlp
  ensure_command ffmpeg
  ensure_feeds_exist
  load_env

  local record
  if ! record="$(feed_record_by_name "$feed_name")"; then
    log "Feed not found in feeds.conf: $feed_name"
    exit 1
  fi

  local name url fps
  IFS='|' read -r name url fps <<<"$record"

  validate_feed_name "$name"
  warn_if_high_fps "$fps"

  local data_dir
  data_dir="$(realpath_portable "$LIVELAPSE_DATA_DIR")"
  local output_dir="$data_dir/$name"
  mkdir -p "$output_dir"

  build_ffmpeg_output_args "$LIVELAPSE_FORMAT"

  local output_pattern="$output_dir/%Y-%m-%dT%H_%M_%SZ.$FF_OUTPUT_EXT"

  while true; do
    local input_url="$url"
    if ! is_direct_ffmpeg_input "$url"; then
      log "Resolving stream URL for $name"
      if ! input_url="$(resolve_stream_url "$url")"; then
        log "yt-dlp failed to resolve stream URL for $name"
        sleep "$LIVELAPSE_RETRY_DELAY"
        continue
      fi
    fi

    log "Starting capture for $name -> $output_dir"

    local exit_code=0
    if ! run_ffmpeg_capture "$input_url" "$url" "$fps" "$output_pattern"; then
      exit_code=$?
    fi

    log "Capture loop exited for $name with code $exit_code; retrying in ${LIVELAPSE_RETRY_DELAY}s"
    sleep "$LIVELAPSE_RETRY_DELAY"
  done
}

main "$@"
