# LiveLapse Next Steps

This file tracks the immediate follow-on work after the Phase 0 local macOS soak.

## Current Position

- `bin/capture.sh` works for local frame capture
- `bin/livelapse` currently supports `caffeinate start|stop|status` on macOS
- macOS local capture is still being managed manually with background `bin/capture.sh` processes
- Linux deployment has install and systemd scaffolding, but has not been validated end-to-end on Ubuntu yet
- DigitalOcean block storage automation is still planned work, not current implementation

## Priority Order

1. Backfill the real local CLI surface on macOS
2. Validate Ubuntu end-to-end manually
3. Only then automate infrastructure steps such as `doctl`

## Immediate CLI Backfill

### 1. Feed lifecycle commands

Implement these commands in `bin/livelapse`:

- `start [feed-name]`
- `stop [feed-name]`
- `status`
- `logs <feed-name>`

Expected behavior:

- On macOS, `start` should launch `bin/capture.sh` in the background for one feed or all feeds from `feeds.conf`
- Store feed PIDs in `.pids/<feed>.pid`
- Store feed logs in `.pids/<feed>.log`
- `stop` should gracefully stop one feed or all tracked feeds
- `status` should report whether each configured feed is running and show the latest frame timestamp if available
- `logs` should tail the local log file on macOS and map cleanly to `journalctl` on Linux later

Acceptance criteria:

- Starting all feeds from the CLI recreates the same behavior as the current manual `nohup` workflow
- Re-running `start` does not duplicate already-running feeds
- `status` is reliable after stale PID cleanup

### 2. Snapshot preview command

Add a CLI command for a point-in-time preview video:

- `preview <feed-name>`

Expected behavior:

- Snapshot the current frame list without stopping capture
- Build a temporary sequential input set for `ffmpeg`
- Write the preview MP4 under `data/output/intermediate/`
- Print the output path, frame count, and duration

Acceptance criteria:

- Capture continues while preview rendering runs
- Preview output is playable in QuickTime and VLC

### 3. Stitch wrapper

Back the documented `stitch` command into a real script and wire it into the CLI.

Expected behavior:

- Support a feed name plus optional start, end, playback fps, codec, quality, output, and dry-run flags
- Work from timestamped frame files without requiring a database

## Documentation Cleanup

### 4. Reconcile docs with reality

Bring the documentation in line with the current repo state:

- Keep README accurate about what exists today versus planned commands
- Maintain a concrete macOS runbook for local operations
- Decide whether `feeds.conf` should remain tracked or be split into `feeds.conf.example` plus instance-local `feeds.conf`

## Deployment Validation

### 5. Manual Ubuntu end-to-end run

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

### 6. `doctl` provisioning

Only after the manual Ubuntu path is stable:

- add `install/do-provision.sh`
- support inspect, attach, detach, and status first
- add destructive actions only with explicit confirmation and guardrails

## Not Needed Yet

- Full block-storage automation before the first manual Ubuntu validation
- Premature refactors of the capture loop while the overnight soak is still gathering evidence
