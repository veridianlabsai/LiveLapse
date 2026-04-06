# LiveLapse

> **Status:** Under active development for the Artemis II lunar flyby (April 6, 2026). First release coming soon.

Self-hosted timelapse capture from live streams. Pull timestamped frames from YouTube, RTSP, or any yt-dlp/ffmpeg-compatible source and stitch them into videos. Runs headless on Linux via systemd, with email alerting and a simple CLI.

Built to capture NASA's Artemis II lunar flyby across multiple feeds simultaneously.

---

## Features

- Capture frames from any yt-dlp/ffmpeg-compatible stream (YouTube Live, RTSP, HLS, etc.)
- Configurable frame rate per feed (e.g. `1` fps, `0.2` for one frame every 5 seconds)
- ISO 8601 timestamped filenames — no sequential counters, no collision on restart
- Systemd-managed per-feed capture processes with automatic restart on stream drop
- Health monitoring via cron — per-feed stale alerts and disk usage warnings via email (Resend)
- Simple CLI for start/stop/status/logs/add/remove/stitch
- Frame-to-timelapse stitching with time-range filtering
- Works on macOS (local testing) and Ubuntu 24+ (production)
- No database — the filesystem is the database

---

## Quick Start

**Requirements:** `yt-dlp`, `ffmpeg`, `jq`, `curl` (installed by `install.sh`)

```bash
# 1. Clone
git clone https://github.com/veridian-labs/livelapse /opt/livelapse
cd /opt/livelapse

# 2. Configure feeds
cp feeds.conf.example feeds.conf
# Edit feeds.conf — add your streams (name|url|fps)

# 3. Configure environment
cp .env.example .env
# Edit .env — set LIVELAPSE_DATA_DIR and optional alerting keys

# 4. Install dependencies and start
./install/install.sh

# 5. Verify capture is running
livelapse status
```

Frames will appear in `$LIVELAPSE_DATA_DIR/<feed-name>/` within seconds.

---

## Configuration

### `feeds.conf`

Pipe-delimited, one feed per line. Comments start with `#`.

```
# name|url|fps
artemis-main|https://www.youtube.com/live/5flTTJuoExo|1
spacecraft-cam|rtsp://example.com/stream|0.5
```

- **name** — Alphanumeric + hyphens. Used as folder name and systemd instance identifier.
- **url** — Any URL supported by yt-dlp or a direct ffmpeg input (RTSP, HLS, etc).
- **fps** — Frames per second. Use `0.2` for one frame every 5 seconds, `0.5` for every 2 seconds.

### `.env`

```bash
# Data directory (mount your volume here)
LIVELAPSE_DATA_DIR=/mnt/livelapse

# Frame format: webp (default), png, jpg
LIVELAPSE_FORMAT=webp
LIVELAPSE_LOSSLESS=1          # WebP: 1=lossless. JPG: quality 1-31 (lower=better)

# Stream settings
LIVELAPSE_MAX_HEIGHT=720       # Max resolution height to request
LIVELAPSE_RETRY_DELAY=10       # Seconds to wait before retrying after stream drop

# Alerting (optional — leave blank to disable)
RESEND_API_KEY=
ALERT_FROM=alerts@yourdomain.com
ALERT_TO=you@example.com

# Health check thresholds
HEALTHCHECK_STALE_SECONDS=120  # Seconds with no new frames before alerting
HEALTHCHECK_DISK_THRESHOLD=80  # Disk usage % threshold
```

---

## CLI Reference

```
livelapse start [feed-name]     Start all feeds, or a specific feed
livelapse stop [feed-name]      Stop all feeds, or a specific feed
livelapse status                Table of all feeds: status, last frame, count, disk usage
livelapse caffeinate start      Prevent idle sleep on macOS during local capture
livelapse caffeinate stop       Release the macOS caffeinate hold
livelapse caffeinate status     Show whether the macOS caffeinate hold is active
livelapse logs <feed-name>      Tail logs for a feed (journalctl wrapper)
livelapse add <name> <url> [fps]  Add a new feed and start capture immediately
livelapse remove <name>         Stop and remove a feed (frames kept by default)
livelapse stitch <name> [opts]  Assemble captured frames into a timelapse video
livelapse peek <feed-name>      Output the most recent frame to stdout
livelapse disk                  Disk usage summary per feed and total
```

### Stitching

```bash
livelapse stitch artemis-main \
  --start 2026-04-06T00:00:00Z \
  --end   2026-04-06T23:59:59Z \
  --playback-fps 30 \
  --output ./output/flyby.mp4
```

Options:
- `--start` / `--end` — ISO 8601 timestamps for time-range filtering
- `--playback-fps` — Output video frame rate (default: 30)
- `--output` — Output path (default: `$LIVELAPSE_DATA_DIR/output/<feed>_<start>_<end>.mp4`)
- `--codec` — `libx264` (default) or `libx265`
- `--quality` — CRF value, lower = better (default: 18)
- `--dry-run` — Print frame count and estimated duration without encoding

---

## Directory Layout

```
livelapse/
├── feeds.conf                  # Feed definitions
├── .env.example                # Config template
├── bin/
│   ├── livelapse               # CLI entrypoint
│   ├── capture.sh              # Per-feed capture loop (spawned by systemd)
│   ├── healthcheck.sh          # Cron-driven health monitor
│   └── stitch.sh               # Frame-to-video assembler
├── install/
│   ├── install.sh              # Install deps, systemd units, cron
│   ├── do-provision.sh         # DigitalOcean droplet + volume lifecycle (optional)
│   └── uninstall.sh            # Clean removal
└── templates/
    └── livelapse@.service      # Systemd template unit
```

### Captured data

```
/mnt/livelapse/
├── artemis-main/
│   ├── 2026-04-06T14_23_07Z.webp
│   ├── 2026-04-06T14_23_08Z.webp
│   └── ...
└── output/
    └── artemis-main_2026-04-06_2026-04-06.mp4
```

---

## How It Works

Each feed runs as a systemd service (`livelapse@<feed-name>.service`) that keeps a `yt-dlp | ffmpeg` pipeline alive:

- `yt-dlp` resolves the stream URL and pipes the video to ffmpeg
- `ffmpeg` extracts frames at the configured rate, writing each as a timestamped file
- On stream drop, the service waits `RETRY_DELAY` seconds and reconnects automatically
- Filenames use `-strftime 1` so they reflect real wall-clock time — restarts produce no filename collisions and no gaps to reconcile

Health checks run every 60 seconds via cron, checking frame age per feed and overall disk usage. Alerts are rate-limited to one per 10 minutes per feed per alert type.

---

## Platform Compatibility

| Feature | macOS | Linux (Ubuntu 24+) |
|---|---|---|
| Install deps | `brew install yt-dlp ffmpeg jq` | `apt install yt-dlp ffmpeg jq curl bc` |
| Process management | Background process + PID file | systemd template units |
| Logs | `$LIVELAPSE_DATA_DIR/<feed>/capture.log` | `journalctl -u livelapse@<feed>` |
| Health check | User crontab | `/etc/cron.d/livelapse` |

Run on macOS for local testing with a local data directory, deploy to Linux for production capture.

On macOS, keep the machine awake during long local captures with `bin/livelapse caffeinate start`.

---

## Resource Usage (720p, WebP lossless, 1 fps)

| | Per feed |
|---|---|
| Frame size | ~500 KB – 1 MB |
| Per hour | ~1.8 – 3.6 GB |
| Per day | ~43 – 86 GB |
| CPU | ~5–10% of one vCPU |
| RAM | ~50–100 MB |

For a 3-feed, 3-day capture: 250 GB volume, 2 vCPU / 2 GB RAM droplet.

---

## DigitalOcean Provisioning (Optional)

`install/do-provision.sh` manages the full infrastructure lifecycle from your local machine using `doctl`:

```bash
do-provision.sh inspect  --droplet-name my-droplet   # Read-only recon
do-provision.sh attach   --droplet-name my-droplet   # Create + attach block volume
do-provision.sh detach   --droplet-name my-droplet   # Unmount + detach (data preserved)
do-provision.sh destroy  --volume-name livelapse-data # Permanent deletion (requires confirmation)
do-provision.sh status   --droplet-name my-droplet   # Current state summary
```

All destructive actions require explicit confirmation. The script inspects existing state before making any changes and never touches resources outside its scope.

---

## License

MIT — see [LICENSE](LICENSE).

---

*Built by [Veridian Labs](https://veridianlabs.co) to capture the Artemis II lunar flyby.*
