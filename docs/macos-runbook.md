# LiveLapse macOS Runbook

This document describes the current Phase 0 macOS workflow.

## Current Implementation Status

- `./install.sh` installs local dependencies and creates a local `.env` if needed
- `./bin/capture.sh <feed-name>` remains the per-feed capture loop used under the CLI
- `./bin/livelapse status`, `start`, `stop`, `logs <feed-name>`, `peek <feed-name>`, and `preview <feed-name>` are available locally
- `./bin/livelapse caffeinate start|stop|status` manages the macOS no-sleep hold
- Restarting a stopped feed resumes future capture only; gaps while stopped are expected
- During a live soak, use `--dry-run` first before touching active feeds

## One-Time Setup

From the repo root:

```bash
cd /Users/liam/Documents/dev/veridian-labs/livelapse
./install.sh
```

Edit `feeds.conf` directly to define the feeds you want to run.

## Keep The Mac Awake

Start the no-sleep hold:

```bash
./bin/livelapse caffeinate start
```

Check it:

```bash
./bin/livelapse caffeinate status
```

Stop it:

```bash
./bin/livelapse caffeinate stop
```

Note:

- Leave the Mac open and on power for long runs
- `caffeinate` helps with idle sleep, but closing the lid can still interrupt capture

## Start A Single Feed

```bash
./bin/livelapse start artemis2-main
```

## Start Without Naming A Feed

```bash
./bin/livelapse start
```

In an interactive terminal this opens a picker of currently stopped feeds. In non-interactive use it targets all stopped feeds.

## Dry-Run A Start First

```bash
./bin/livelapse start artemis2-main --dry-run
./bin/livelapse start --dry-run
```

If a feed is already running, `start <feed-name>` offers a stop-and-restart path instead of silently launching a duplicate.
If you truly want two concurrent captures from the same source, duplicate the `feeds.conf` entry with a new feed name.

## Check Running Feeds

```bash
./bin/livelapse status
```

## Tail Feed Logs

```bash
./bin/livelapse logs artemis2-main
```

## Stop A Single Feed

```bash
./bin/livelapse stop artemis2-main
```

`stop` asks for confirmation in an interactive terminal. In non-interactive use, pass `--yes` if you really mean it.

## Stop Without Naming A Feed

```bash
./bin/livelapse stop
```

In an interactive terminal this opens a picker of currently running feeds. In non-interactive use it targets all running feeds.

## Dry-Run A Stop First

```bash
./bin/livelapse stop artemis2-main --dry-run
./bin/livelapse stop --dry-run
```

## Frame Output

Captured frames land under the data directory configured for the repo. In the current local Phase 0 workflow, that is the repository `data/` tree:

```bash
ls data/artemis2-main | tail
```

## Inspect The Latest Frame

This streams the newest frame to stdout, so use a pipe or redirect:

```bash
./bin/livelapse peek artemis2-main > /tmp/artemis2-main-latest.webp
./bin/livelapse peek artemis2-main | imgcat
```

## Watch A Feed Live

Display the latest captured frame inline in the terminal, refreshing automatically. This is the fastest way to see what a feed is capturing right now without leaving the terminal.

```bash
./bin/livelapse watch artemis2-main                # refresh every 1s, Ctrl-C to stop
./bin/livelapse watch artemis2-main --interval 5   # refresh every 5s
./bin/livelapse watch artemis2-main --once          # show one frame and exit
```

Works natively in iTerm2 and Kitty. For other terminals, install `chafa` (`brew install chafa`) or `viu` (`brew install viu`).

For stopped feeds, `watch` shows the last valid frame before the stream dropped — runt frames from stream drops are skipped automatically.

## Create A Preview Video For One Feed

This creates a point-in-time preview from the current frame set without stopping capture.

```bash
./bin/livelapse preview artemis2-main
./bin/livelapse preview artemis2-main --add-timestamp
```

Optional overrides:

```bash
./bin/livelapse preview artemis2-main --playback-fps 24
./bin/livelapse preview artemis2-main --add-timestamp --timestamp-tz America/Los_Angeles
./bin/livelapse preview artemis2-main --output ./tmp/artemis2-main-preview.mp4
```

The command writes previews under `$LIVELAPSE_DATA_DIR/output/intermediate/` by default and prints the output path, frame count, and playback duration.
When `--add-timestamp` is enabled, the overlay is derived from the UTC frame filenames and then converted to the requested display timezone. The default request is Eastern time, resolved through `America/New_York`, so daylight-saving dates render as `EDT` instead of a fixed `EST` label.

## Create Preview Videos For All Feeds

Repeat the one-feed preview command for each feed listed in `feeds.conf`, or script around it once the broader CLI surface is expanded further.
