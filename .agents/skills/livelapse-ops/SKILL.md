---
name: livelapse-ops
description: Operational guide for running, deploying, and managing the LiveLapse timelapse capture system. Use when asked to start/stop feeds, render previews, configure captures, deploy to Ubuntu/Linux, or provision on DigitalOcean.
metadata:
  author: veridian-labs
  version: "0.1"
---

# LiveLapse Operations

LiveLapse captures timestamped frames from live streams (YouTube Live, RTSP, HLS) and stitches them into timelapse videos. Core pipeline: `yt-dlp` resolves the stream URL → `ffmpeg` extracts frames at the configured rate → ISO 8601-named files land in `$LIVELAPSE_DATA_DIR/<feed-name>/`.

## Project Layout

```
livelapse/
├── bin/livelapse         # CLI entrypoint (run from repo root)
├── bin/capture.sh        # Per-feed capture loop
├── bin/common.sh         # Shared helpers (env, feeds, PIDs)
├── feeds.conf            # Feed definitions (name|url|fps)
├── .env                  # Runtime config — not in git, never read directly
├── .env.example          # Config template — reference this
├── install/install.sh    # Installs deps + Linux systemd units
├── install.sh            # Repo-root shortcut → install/install.sh
├── templates/livelapse@.service  # Systemd unit template
├── docs/macos-runbook.md # macOS manual workflow
└── next_steps.md         # Implementation plan
```

## Configuration

### feeds.conf

Pipe-delimited, one feed per line, comments with `#`:

```
# name|url|fps
artemis2-main|https://www.youtube.com/live/XXXXX|1
spacecraft-cam|rtsp://example.com/stream|0.5
```

- **name** — alphanumeric + hyphens; becomes the folder name and systemd instance ID
- **url** — any yt-dlp-compatible URL, or a direct RTSP/HLS/RTMP address
- **fps** — frames per second (`1` = 1 fps, `0.2` = one frame every 5 s)

### .env

Copy from `.env.example`. Key variables:

```bash
LIVELAPSE_DATA_DIR=/path/to/data   # Where frames land; mount your volume here
LIVELAPSE_FORMAT=webp              # webp | png | jpg
LIVELAPSE_LOSSLESS=1               # WebP: 1=lossless; JPG: quality 1-31 (lower=better)
LIVELAPSE_MAX_HEIGHT=720           # Cap stream resolution
LIVELAPSE_RETRY_DELAY=10           # Seconds before reconnect after stream drop

# Alerting (optional — leave blank to disable)
RESEND_API_KEY=
ALERT_FROM=alerts@yourdomain.com
ALERT_TO=you@example.com

HEALTHCHECK_STALE_SECONDS=120      # Seconds with no new frame before alerting
HEALTHCHECK_DISK_THRESHOLD=80      # Disk % threshold
```

---

## CLI Reference (Implemented)

All commands run from the repo root: `./bin/livelapse <command>`

### status

```bash
./bin/livelapse status
```

Prints a table of all feeds defined in `feeds.conf`:

```
FEED             STATE    PID      LAST_FRAME_UTC         FRAMES
artemis2-main    running  34821    2026-04-06T02:15:08Z   571
artemis2-2nd     stopped  -        2026-04-06T01:44:12Z   562
```

### logs

```bash
./bin/livelapse logs <feed-name>
./bin/livelapse logs <feed-name> --lines 100
./bin/livelapse logs <feed-name> --follow
./bin/livelapse logs <feed-name> --no-follow
```

- macOS: tails `.pids/<feed>.log`
- Linux: wraps `journalctl -u livelapse@<feed>`

### preview

```bash
./bin/livelapse preview <feed-name>
./bin/livelapse preview <feed-name> --playback-fps 24
./bin/livelapse preview <feed-name> --output ./tmp/preview.mp4
```

Snapshots the current frame list, stages symlinks in a temp dir, renders an MP4 with ffmpeg. Capture continues uninterrupted. Output lands in `$LIVELAPSE_DATA_DIR/output/intermediate/` by default. Prints output path, frame count, and playback duration on completion.

### peek

```bash
./bin/livelapse peek <feed-name> > latest.webp    # Raw bytes to stdout — pipe or redirect
./bin/livelapse peek <feed-name> | imgcat          # Pipe to an image viewer
```

Outputs the newest valid frame's raw bytes. Refuses to write binary to an interactive terminal — use `watch --once` to view inline instead.

### watch

```bash
./bin/livelapse watch <feed-name>                  # Live refresh every 1s, Ctrl-C to stop
./bin/livelapse watch <feed-name> --interval 5     # Refresh every 5s
./bin/livelapse watch <feed-name> --once            # Show one frame and exit
```

Displays the latest captured frame inline in the terminal and refreshes automatically. For stopped feeds, shows the last valid frame before the stream dropped.

Renderer detection: prefers `chafa` (install via `brew install chafa`), then `viu`, then Kitty/iTerm2 native inline images. Read-only — never touches capture processes or PIDs.

### caffeinate (macOS only)

```bash
./bin/livelapse caffeinate start    # Prevent idle sleep via launchctl
./bin/livelapse caffeinate stop     # Release the hold
./bin/livelapse caffeinate status   # Show whether hold is active
```

Required for long local runs. Keep the lid open and machine on power.

---

## CLI — Not Yet Implemented

These commands are planned but not yet backed into `bin/livelapse`. Use the manual workflows below in the meantime.

```
stitch <name> [opts]      Assemble frames into a timelapse
add <name> <url> [fps]    Add a feed and start immediately
remove <name>             Stop and remove a feed
disk                      Disk usage per feed and total
```

---

## macOS Workflow (Manual)

### One-time setup

```bash
./install.sh
# installs yt-dlp, ffmpeg, jq via Homebrew and creates local .env if missing
```

### Start all feeds

```bash
mkdir -p .pids
while IFS= read -r feed_name; do
  nohup ./bin/capture.sh "$feed_name" > ".pids/$feed_name.log" 2>&1 < /dev/null &
  echo $! > ".pids/$feed_name.pid"
done < <(
  awk -F'|' '
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    { gsub(/^[[:space:]]+|[[:space:]]+$/, "", $1); if ($1 != "") print $1 }
  ' feeds.conf
)
```

### Start a single feed

```bash
mkdir -p .pids
nohup ./bin/capture.sh artemis2-main > .pids/artemis2-main.log 2>&1 < /dev/null &
echo $! > .pids/artemis2-main.pid
```

### Stop a single feed

```bash
kill "$(tr -d '[:space:]' < .pids/artemis2-main.pid)"
rm -f .pids/artemis2-main.pid
```

### Stop all feeds

```bash
for pid_file in .pids/*.pid; do
  kill "$(tr -d '[:space:]' < "$pid_file")"
done
rm -f .pids/*.pid
```

### Keep Mac awake during capture

```bash
./bin/livelapse caffeinate start
```

---

## Linux / Ubuntu Deployment

### First-time install

```bash
# On the Ubuntu instance:
git clone https://github.com/veridian-labs/livelapse /opt/livelapse
cd /opt/livelapse
cp .env.example .env
# Edit .env — set LIVELAPSE_DATA_DIR to the mounted volume path (e.g. /mnt/livelapse)
./install.sh
# installs apt deps (yt-dlp ffmpeg jq curl bc), copies systemd unit, installs cron
```

### Systemd feed management

Each feed runs as `livelapse@<feed-name>.service` from `templates/livelapse@.service`.

```bash
# Start a specific feed
systemctl start livelapse@artemis2-main

# Stop a feed
systemctl stop livelapse@artemis2-main

# Enable at boot
systemctl enable livelapse@artemis2-main

# Status
systemctl status livelapse@artemis2-main

# Logs (or use the CLI)
journalctl -u livelapse@artemis2-main -f
./bin/livelapse logs artemis2-main --follow
```

### Verify frames are landing

```bash
# Watch for new files
watch -n 2 "ls -lt $LIVELAPSE_DATA_DIR/artemis2-main | head -5"

# Or via CLI status
./bin/livelapse status
```

---

## DigitalOcean Provisioning (Planned)

`install/do-provision.sh` is not yet written. Manual steps until it exists:

1. **Create Droplet** — Ubuntu 24 LTS, 2 vCPU / 2 GB RAM minimum for 3 feeds at 1 fps
2. **Attach Block Storage** — 250 GB for a 3-feed, 3-day capture at 1 fps WebP lossless
3. **Mount volume**
   ```bash
   mkfs.ext4 /dev/sda
   mkdir -p /mnt/livelapse
   mount /dev/sda /mnt/livelapse
   echo '/dev/sda /mnt/livelapse ext4 defaults 0 2' >> /etc/fstab
   ```
4. **Deploy repo**
   ```bash
   git clone https://github.com/veridian-labs/livelapse /opt/livelapse
   cd /opt/livelapse
   cp .env.example .env
   # Set LIVELAPSE_DATA_DIR=/mnt/livelapse
   ./install.sh
   ```
5. **Start feeds**
   ```bash
   systemctl start livelapse@artemis2-main
   systemctl start livelapse@artemis2-2nd
   systemctl start livelapse@artemis2-3rd
   ```

Resource estimates (720p WebP lossless, 1 fps per feed):

| | Per feed / hour | Per feed / day |
|---|---|---|
| Storage | ~1.8–3.6 GB | ~43–86 GB |
| CPU | ~5–10% of 1 vCPU | — |
| RAM | ~50–100 MB | — |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No frames appearing | Stream offline or yt-dlp failed | `./bin/livelapse logs <feed>` — check for URL resolution errors |
| Frames stop mid-run | Stream dropped | capture.sh retries automatically after `RETRY_DELAY` seconds |
| Wrong timezone in filenames | TZ override in environment | capture.sh forces `TZ=UTC`; check parent shell env |
| `status` shows stopped but process exists | Stale PID file | Cleaned up automatically on next `status` call |
| ffmpeg exits immediately | Bad URL or format mismatch | Run `yt-dlp -g <url>` manually to test URL resolution |
| Preview MP4 won't play in QuickTime | Non-even resolution | `pad=ceil(iw/2)*2:ceil(ih/2)*2` filter is already applied; check ffmpeg logs |

---

## What's Next

See `next_steps.md` for the full implementation plan. Priority:

1. `start` / `stop` CLI commands (macOS PID-based, Linux systemd)
2. `stitch` command with time-range filtering
3. Manual Ubuntu end-to-end validation
4. `install/do-provision.sh` for DigitalOcean automation
