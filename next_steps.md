# LiveLapse Next Steps

This file tracks the immediate follow-on work after the Phase 0 local macOS soak.

## Current Position

- `bin/capture.sh` works for local frame capture
- `bin/livelapse` now supports `status`, `start`, `stop`, `logs <feed-name>`, and `preview <feed-name>` plus `caffeinate start|stop|status` on macOS
- macOS local capture can now be managed through the CLI with interactive selectors, confirmations, and `--dry-run` guardrails
- Linux deployment has install and systemd scaffolding, but has not been validated end-to-end on Ubuntu yet
- DigitalOcean block storage automation is still planned work, not current implementation

## Priority Order

1. Live-validate the new lifecycle commands after the macOS soak finishes
2. Validate Ubuntu end-to-end manually
3. Only then automate infrastructure steps such as `doctl`

## Immediate Local CLI Hardening

### 1. Safe local inspection and preview commands

Implement and verify these commands in `bin/livelapse` first:

- `status`
- `logs <feed-name>`
- `preview <feed-name>`

Expected behavior:

- `status` reports whether each configured feed is running and shows the latest frame timestamp if available
- `logs` tails the local log file on macOS and maps cleanly to `journalctl` on Linux later
- `preview` snapshots the current frame list without stopping capture and writes an MP4 under `$LIVELAPSE_DATA_DIR/output/intermediate/`
- None of these commands should disturb already-running capture jobs during the overnight soak

### 2. Snapshot preview command details

Add a CLI command for a point-in-time preview video:

- `preview <feed-name>`

Expected behavior:

- Snapshot the current frame list without stopping capture
- Build a temporary sequential input set for `ffmpeg`
- Write the preview MP4 under `$LIVELAPSE_DATA_DIR/output/intermediate/`
- Print the output path, frame count, and duration

Acceptance criteria:

- Capture continues while preview rendering runs
- Preview output is playable in QuickTime and VLC

### 3. Feed lifecycle validation after the soak

Exercise the new lifecycle commands in `bin/livelapse` once the active local soak is finished:

- `start [feed-name] [--dry-run]`
- `stop [feed-name] [--dry-run] [--yes]`

Expected behavior:

- On macOS, `start` should launch `bin/capture.sh` in the background for one feed or all feeds from `feeds.conf`
- Store feed PIDs in `.pids/<feed>.pid`
- Store feed logs in `.pids/<feed>.log`
- `stop` should gracefully stop one feed or all tracked feeds
- In an interactive terminal, omitting the feed name should offer an operation-aware selector instead of forcing manual re-entry
- `stop` should confirm before touching live feeds, and `start` should refuse to silently duplicate an already-running feed
- Stopping and later starting the same feed should resume future capture in the same directory; the stopped interval is an expected gap and no backfill is attempted

Acceptance criteria:

- Starting stopped feeds from the CLI recreates the same behavior as the current manual `nohup` workflow
- Re-running `start` does not duplicate already-running feeds
- `stop` terminates the entire capture process group cleanly
- Restarting a stopped feed resumes new frames without touching existing ones

### 4. Stitch wrapper

Back the documented `stitch` command into a real script and wire it into the CLI.

Expected behavior:

- Support a feed name plus optional start, end, playback fps, codec, quality, output, and dry-run flags
- Reuse the preview timestamp-overlay path for `--add-timestamp` and `--timestamp-tz`
- Work from timestamped frame files without requiring a database

## Documentation Cleanup

### 5. Reconcile docs with reality

Bring the documentation in line with the current repo state:

- Keep README accurate about what exists today versus planned commands
- Maintain a concrete macOS runbook for local operations
- Decide whether `feeds.conf` should remain tracked or be split into `feeds.conf.example` plus instance-local `feeds.conf`

## Deployment Validation

### 6. Manual Ubuntu end-to-end run

Before writing `doctl` automation:

- mount the target volume manually
- clone or pull the repo on the Ubuntu box
- create instance-local `.env`
- run `./install.sh`
- verify `livelapse@<feed>.service`
- confirm frames land on the mounted volume
- confirm restart behavior after an interrupted stream

Acceptance criteria:

- One successful manual Ubuntu run from clean checkout to active capture
- Known-good mount path, ownership model, and service behavior documented

## Infrastructure Automation After Validation

### 7. `doctl` provisioning

Only after the manual Ubuntu path is stable:

- add `install/do-provision.sh`
- support inspect, attach, detach, and status first
- add destructive actions only with explicit confirmation and guardrails

## Not Needed Yet

- Full block-storage automation before the first manual Ubuntu validation
- Premature refactors of the capture loop while the overnight soak is still gathering evidence
