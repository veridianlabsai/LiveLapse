# LiveLapse Status

## Current Session

- Date: 2026-04-05
- Phase: Phase 0 - Launch Window
- Objective: turn the spec-only repo into a working local-first baseline on macOS, then soak it locally overnight before moving to the Ubuntu instance
- Status: local Phase 0 verification passed; a 3-feed overnight macOS soak is running now with caffeinate control in the CLI

## Scope For This Session

- Create the Phase 0 tracker and repository skeleton
- Implement the minimal capture path and install flow
- Verify a few sample seconds of local capture on macOS
- Extend the local run to three feeds and leave it running overnight
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
- Added a minimal CLI entrypoint at [bin/livelapse](/Users/liam/Documents/dev/veridian-labs/livelapse/bin/livelapse) for `caffeinate start|stop|status` on macOS, backed by `launchctl`
- Expanded the local soak run to three active feeds from [feeds.conf](/Users/liam/Documents/dev/veridian-labs/livelapse/feeds.conf):
  - `artemis2-main`
  - `artemis2-2nd`
  - `artemis2-3rd`
- Started the overnight local capture run on macOS and confirmed all three feeds were still increasing after the preview renders:
  - `artemis2-main`: 571 frames, then 574 frames three seconds later
  - `artemis2-2nd`: 562 frames, then 566 frames three seconds later
  - `artemis2-3rd`: 502 frames, then 506 frames three seconds later
- Created snapshot preview videos from the current frame sets without stopping capture:
  - [artemis2-main_2026-04-06T02_15_12Z.mp4](/Users/liam/Documents/dev/veridian-labs/livelapse/data/output/intermediate/artemis2-main_2026-04-06T02_15_12Z.mp4) from 554 frames, duration `18.47s`
  - [artemis2-2nd_2026-04-06T02_15_12Z.mp4](/Users/liam/Documents/dev/veridian-labs/livelapse/data/output/intermediate/artemis2-2nd_2026-04-06T02_15_12Z.mp4) from 549 frames, duration `18.30s`
  - [artemis2-3rd_2026-04-06T02_15_12Z.mp4](/Users/liam/Documents/dev/veridian-labs/livelapse/data/output/intermediate/artemis2-3rd_2026-04-06T02_15_12Z.mp4) from 490 frames, duration `16.33s`

## In Progress

- Overnight macOS soak is still running with three feeds
- Linux/systemd deployment remains untested until the next session on the instance

## Verification Target

- `bin/capture.sh artemis2-main` creates UTC timestamped frames locally under the configured data directory
- `install/install.sh` handles macOS dependency/setup and Linux systemd deployment foundations
- `bin/livelapse caffeinate start|stop|status` controls the macOS sleep-prevention hold for local captures
- The repository is ready for an instance-focused Phase 0 continuation next

## Issues

- None logged yet. If a blocker appears, create `issues.md` in the repo root and track it there.

## Next Session Start Point

- Check the overnight macOS run first:
  - confirm the three capture processes are still running
  - inspect the newest frames under [data/artemis2-main](/Users/liam/Documents/dev/veridian-labs/livelapse/data/artemis2-main), [data/artemis2-2nd](/Users/liam/Documents/dev/veridian-labs/livelapse/data/artemis2-2nd), and [data/artemis2-3rd](/Users/liam/Documents/dev/veridian-labs/livelapse/data/artemis2-3rd)
  - review the preview MP4s under [data/output/intermediate](/Users/liam/Documents/dev/veridian-labs/livelapse/data/output/intermediate)
- Then begin the Ubuntu/droplet session, mount storage, copy the repo to `/opt/livelapse`, run `install.sh`, and validate the `livelapse@artemis2-main` service.
- On the instance, verify:
  - `systemctl status livelapse@artemis2-main`
  - new frames appear under the mounted data directory
  - the unit restarts cleanly if the stream drops
- If local verification fails: continue Phase 0 only, fix the blocker, and keep `status.md` as the source of truth before opening a new session.
