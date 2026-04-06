@README.md

---

# Agent Instructions — LiveLapse

Read the full README above before taking action. It is the source of truth for the project's purpose, configuration, CLI surface, and current status.

## Key Files

| File | Purpose |
|---|---|
| `bin/livelapse` | CLI entrypoint — all agent-facing commands live here |
| `bin/capture.sh` | Per-feed capture loop spawned by the CLI or systemd |
| `bin/common.sh` | Shared shell helpers (env loading, feed parsing, PID utilities) |
| `feeds.conf` | Pipe-delimited feed definitions: `name\|url\|fps` |
| `.env` | Runtime config — sourced at startup, never tracked in git |
| `.env.example` | Config template — read this, never `.env` |
| `docs/macos-runbook.md` | Current macOS operations guide |
| `next_steps.md` | Implementation plan and priority order |
| `status.md` | Session-level status and current phase |

## Implementation State

The README "CLI Reference" section notes what is implemented vs. planned. As of Phase 0:

**Implemented in `bin/livelapse`:**
- `status` — feed table (state, PID, last frame UTC, frame count)
- `logs <feed-name>` — tails local log (macOS) or wraps journalctl (Linux)
- `preview <feed-name>` — renders a point-in-time MP4 without stopping capture
- `caffeinate start|stop|status` — macOS idle-sleep prevention via launchctl

**Not yet implemented (manual workflow required):**
- `start` / `stop` — see `docs/macos-runbook.md` for the manual `nohup` pattern
- `stitch`, `add`, `remove`, `peek`, `disk`

## Navigation Notes

- Feed lifecycle is in `bin/livelapse` functions `status_command`, `logs_command`, `preview_command`
- Feed parsing and PID helpers are in `bin/common.sh`
- The capture loop retry logic is in `bin/capture.sh` — the `while true` at the bottom
- Platform detection (`is_darwin`, `is_linux`) is in `bin/common.sh`
- `.pids/<feed>.pid` and `.pids/<feed>.log` are the macOS process tracking files

## Development Conventions

- Shell scripts use `set -euo pipefail`
- All timestamps are forced UTC (`TZ=UTC ffmpeg ...`)
- Frame filenames use ISO 8601 with colons replaced by underscores: `2026-04-06T14_23_07Z.webp`
- No database — the filesystem is the database
- `feeds.conf` is tracked in git as an example; instance-local overrides are expected
- Never read `.env` — use `.env.example` for reference
