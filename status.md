# LiveLapse Status

## Current Session

- Date: 2026-04-05
- Phase: Phase 0 - Launch Window
- Objective: turn the spec-only repo into a working local-first baseline on macOS, then verify a short sample capture before moving to the Ubuntu instance in the next session
- Status: local Phase 0 verification passed; Ubuntu instance deployment is next

## Scope For This Session

- Create the Phase 0 tracker and repository skeleton
- Implement the minimal capture path and install flow
- Verify a few sample seconds of local capture on macOS
- Record handoff notes for the next session

## Completed

- Reviewed [docs/livelapse-spec.md](/Users/liam/Documents/dev/veridian-labs/livelapse/docs/livelapse-spec.md) and extracted the Phase 0 deliverables plus the macOS development path
- Created the initial repo structure for `bin/`, `install/`, and `templates/`
- Added Phase 0 foundations:
  - [bin/common.sh](/Users/liam/Documents/dev/veridian-labs/livelapse/bin/common.sh) for shared config and platform helpers
  - [bin/capture.sh](/Users/liam/Documents/dev/veridian-labs/livelapse/bin/capture.sh) for the capture loop
  - [install/install.sh](/Users/liam/Documents/dev/veridian-labs/livelapse/install/install.sh) and [install.sh](/Users/liam/Documents/dev/veridian-labs/livelapse/install.sh) for local setup and Linux systemd deployment
  - [templates/livelapse@.service](/Users/liam/Documents/dev/veridian-labs/livelapse/templates/livelapse@.service), [feeds.conf](/Users/liam/Documents/dev/veridian-labs/livelapse/feeds.conf), and [.env.example](/Users/liam/Documents/dev/veridian-labs/livelapse/.env.example)
- Verified local macOS capture against the seeded Artemis feed:
  - 32 frames written to [data/artemis-main](/Users/liam/Documents/dev/veridian-labs/livelapse/data/artemis-main)
  - First frame: `2026-04-06T00_57_33Z.webp`
  - Last frame: `2026-04-06T00_58_04Z.webp`
  - Observed rate: 32 frames in 32 seconds (`60.00` frames/minute)
  - Sample size: `6,357,156` bytes total, about `198,661` bytes per frame, roughly `715 MB/hour` at the observed sample
- Fixed two Phase 0 issues during verification:
  - ffmpeg needed the `image2` muxer for timestamp expansion instead of writing the filename pattern literally
  - filenames now force UTC so the `Z` suffix is correct on macOS too

## In Progress

- Linux/systemd deployment remains untested until the next session on the instance

## Verification Target

- `bin/capture.sh artemis-main` creates UTC timestamped frames locally under the configured data directory
- `install/install.sh` handles macOS dependency/setup and Linux systemd deployment foundations
- The repository is ready for an instance-focused Phase 0 continuation next

## Issues

- None logged yet. If a blocker appears, create `issues.md` in the repo root and track it there.

## Next Session Start Point

- Begin the Ubuntu/droplet session, mount storage, copy the repo to `/opt/livelapse`, run `install.sh`, and validate the `livelapse@artemis-main` service.
- On the instance, verify:
  - `systemctl status livelapse@artemis-main`
  - new frames appear under the mounted data directory
  - the unit restarts cleanly if the stream drops
- If local verification fails: continue Phase 0 only, fix the blocker, and keep `status.md` as the source of truth before opening a new session.
