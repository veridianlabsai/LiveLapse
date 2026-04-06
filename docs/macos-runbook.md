# LiveLapse macOS Runbook

This document describes the current Phase 0 macOS workflow.

Use this runbook until feed lifecycle and preview commands are fully backed into `bin/livelapse`.

## Current Implementation Status

- `./install.sh` installs local dependencies and creates a local `.env` if needed
- `./bin/capture.sh <feed-name>` runs a single capture loop
- `./bin/livelapse caffeinate start|stop|status` manages the macOS no-sleep hold
- Feed `start|stop|status|logs` commands are not yet wired into `bin/livelapse`

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
for pid_file in .pids/*.pid; do
  feed_name="$(basename "$pid_file" .pid)"
  pid="$(tr -d '[:space:]' < "$pid_file")"

  if kill -0 "$pid" 2>/dev/null; then
    echo "$feed_name running pid=$pid"
  else
    echo "$feed_name stopped stale_pid=$pid"
  fi
done
```

## Tail Feed Logs

```bash
tail -f .pids/artemis2-main.log
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
feed="artemis2-main"
src="data/$feed"
out_dir="data/output/intermediate"
mkdir -p "$out_dir"
ts="$(date -u +%Y-%m-%dT%H_%M_%SZ)"
out="$out_dir/${feed}_${ts}.mp4"
stage="$(mktemp -d "/tmp/${feed}.XXXXXX")"

cleanup() {
  rm -rf "$stage"
}

trap cleanup EXIT

count=0
while IFS= read -r frame; do
  count=$((count + 1))
  printf -v target '%s/%06d.webp' "$stage" "$count"
  ln -s "$PWD/$frame" "$target"
done < <(find "$src" -maxdepth 1 -type f -name '*.webp' | sort)

ffmpeg -y \
  -hide_banner \
  -loglevel error \
  -framerate 30 \
  -i "$stage/%06d.webp" \
  -vf 'pad=ceil(iw/2)*2:ceil(ih/2)*2' \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$out"

echo "preview written to $out from $count frames"
```

## Create Preview Videos For All Feeds

Repeat the one-feed preview command for each feed listed in `feeds.conf`, or script around it once the CLI `preview` command is added.
