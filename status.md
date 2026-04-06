# LiveLapse Status

## Current Session

- Date: 2026-04-05
- Phase: Phase 0 - Launch Window
- Objective: turn the spec-only repo into a working local-first baseline on macOS, then verify a short sample capture before moving to the Ubuntu instance in the next session
- Status: in progress

## Scope For This Session

- Create the Phase 0 tracker and repository skeleton
- Implement the minimal capture path and install flow
- Verify a few sample seconds of local capture on macOS
- Record handoff notes for the next session

## Completed

- Reviewed [docs/livelapse-spec.md](/Users/liam/Documents/dev/veridian-labs/livelapse/docs/livelapse-spec.md) and extracted the Phase 0 deliverables plus the macOS development path
- Created the initial repo structure for `bin/`, `install/`, and `templates/`

## In Progress

- Implementing the capture loop, install flow, and Linux systemd template
- Preparing a short local verification run against the Artemis main feed

## Verification Target

- `bin/capture.sh artemis-main` can create timestamped frames locally under the configured data directory
- `install/install.sh` handles macOS dependency/setup and Linux systemd deployment foundations
- The repository is ready for an instance-focused Phase 0 session next

## Issues

- None logged yet. If a blocker appears, create `issues.md` in the repo root and track it there.

## Next Session Start Point

- If local verification passes: begin the Ubuntu/droplet session, mount storage, copy the repo to `/opt/livelapse`, run `install.sh`, and validate the `livelapse@artemis-main` service.
- If local verification fails: continue Phase 0 only, fix the blocker, and keep `status.md` as the source of truth before opening a new session.
