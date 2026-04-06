# LiveLapse macOS Runbook

This document describes the current Phase 0 macOS workflow.

Use this runbook until feed lifecycle and preview commands are fully backed into `bin/livelapse`.

## Current Implementation Status

- `./install.sh` installs local dependencies and creates a local `.env` if needed
- `./bin/capture.sh <feed-name>` runs a single capture loop
- `./bin/livelapse status`, `logs <feed-name>`, and `preview <feed-name>` are available for local inspection without disturbing capture
- `./bin/livelapse caffeinate start|stop|status` manages the macOS no-sleep hold
- Feed `start|stop` commands are still intentionally manual until the current soak finishes
- When CLI `stop` and `start` land later, restarting a stopped feed should resume future capture only; gaps while stopped are expected

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
mkdir -p .pids
nohup ./bin/capture.sh artemis2-main > .pids/artemis2-main.log 2>&1 < /dev/null &
echo $! > .pids/artemis2-main.pid
```

## Start All Feeds In `feeds.conf`

```bash
mkdir -p .pids

while IFS= read -r feed_name; do
  nohup ./bin/capture.sh "$feed_name" > ".pids/$feed_name.log" 2>&1 < /dev/null &
  echo $! > ".pids/$feed_name.pid"
done < <(
  awk -F'|' '
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", $1)
      if ($1 != "") {
        print $1
      }
    }
  ' feeds.conf
)
```

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
kill "$(tr -d '[:space:]' < .pids/artemis2-main.pid)"
rm -f .pids/artemis2-main.pid
```

## Stop All Feeds

```bash
for pid_file in .pids/*.pid; do
  kill "$(tr -d '[:space:]' < "$pid_file")"
done
rm -f .pids/*.pid
```

## Frame Output

Captured frames land under the data directory configured for the repo. In the current local Phase 0 workflow, that is the repository `data/` tree:

```bash
ls data/artemis2-main | tail
```

## Create A Preview Video For One Feed

This creates a point-in-time preview from the current frame set without stopping capture.

```bash
./bin/livelapse preview artemis2-main
```

Optional overrides:

```bash
./bin/livelapse preview artemis2-main --playback-fps 24
./bin/livelapse preview artemis2-main --output ./tmp/artemis2-main-preview.mp4
```

The command writes previews under `$LIVELAPSE_DATA_DIR/output/intermediate/` by default and prints the output path, frame count, and playback duration.

## Create Preview Videos For All Feeds

Repeat the one-feed preview command for each feed listed in `feeds.conf`, or script around it once the broader CLI lifecycle surface is added.
