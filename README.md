# LiveLapse

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Ubuntu%2024%2B-blue)

> Capture any live stream as timestamped frames. Run it forever. Never miss a moment.

Self-hosted timelapse engine for YouTube Live, RTSP, HLS, and anything yt-dlp or ffmpeg can reach. Point it at a stream, walk away, and come back to a precisely timestamped archive ready to render into a video at any speed.

No database. No cloud dependency. No moving parts beyond a shell script and a cron job.

---

## The Origin Story

LiveLapse was built by [Veridian Labs](https://veridianlabs.co) to capture NASA's Artemis II lunar flyby — a once-in-a-generation event broadcasting live across multiple feeds simultaneously on April 6, 2026. We needed something that could run unattended for 24+ hours, survive stream drops, capture across multiple feeds in parallel, and produce clean timelapse footage afterward. Nothing off the shelf did all of that simply, so we built it.

The Artemis II use case shaped the design, but the tool itself is general-purpose. If you have a live stream and want a permanent, timestamped record of it — LiveLapse is for you.

---

## Why LiveLapse?

Most screen recorders and stream downloaders aren't designed to run unattended for hours or days, reconnect automatically when a stream drops, or produce frame archives that survive restarts without gaps or filename collisions. LiveLapse is.

- **Any source** — YouTube Live, RTSP cameras, HLS, RTMP, or any URL yt-dlp understands
- **Self-hosted** — your frames, your disk, your infrastructure
- **Runs forever** — systemd-managed with automatic reconnect on stream drop
- **No collisions** — ISO 8601 timestamped filenames; restarts never overwrite existing frames
- **No database** — the filesystem is the database; browse, inspect, and manage frames with standard tools
- **Point-in-time previews** — render a video from captured frames without stopping capture
- **Health monitoring** — stale frame and disk alerts via email (Resend), rate-limited and cron-driven

---

## Use Cases

**Space & astronomy**
Capture rocket launches, eclipses, ISS flybys, or any major live event frame-by-frame across multiple feeds simultaneously.

**Breaking news & live events**
Archive a news broadcast, election night, or weather emergency as it unfolds — searchable by timestamp after the fact.

**Construction & infrastructure**
Pull frames from IP cameras or public webcams to document site progress over days, weeks, or months.

**Environment & science**
Monitor wildfires (CAL FIRE streams), weather systems, tide gauges, or geological cameras — many public RTSP feeds are available at no cost.

**Security archiving**
Self-hosted DVR alternative. Archive RTSP camera feeds with timestamped frames, no cloud subscription required.

**Nature & agriculture**
Track seasonal change, plant or crop growth, or wildlife behavior from a remote camera over an extended period.

**Long-form events**
24-hour endurance races, marathon courses, concert live-streams — anything too long to watch live but worth having on record.

---

## Quick Start

**Requirements:** `yt-dlp`, `ffmpeg`, `jq`, `curl` (installed by `install.sh`)

```bash
# 1. Clone
git clone https://github.com/veridian-labs/livelapse /opt/livelapse
cd /opt/livelapse

# 2. Configure feeds
# Edit feeds.conf — add your streams (name|url|fps|max_hours)

# 3. Configure environment
cp .env.example .env
# Edit .env — set LIVELAPSE_DATA_DIR and optional alerting keys

# 4. Install dependencies
./install.sh

# 5. Start capture
# macOS: ./bin/livelapse start
# Linux: systemctl start livelapse@<feed-name>
```

Frames appear in `$LIVELAPSE_DATA_DIR/<feed-name>/` within seconds.

---

## AI Developer Experience

LiveLapse is structured as an AI-native repository. Any agent that opens this repo gets full operational context automatically — no manual briefing required.

**Using an AI agent?** Open the repo in Claude Code, Codex, or OpenCode and just say `bootstrap` or `init` — the `livelapse-init` skill walks through every step in Quick Start automatically.

### Automatic project context

`AGENTS.md` (read by Codex and OpenCode) and `CLAUDE.md` (read by Claude Code) point to the same source of truth. Open this repo in any major AI coding tool and the agent already knows:

- What the project does and its current implementation state
- Which files do what and how to navigate the codebase
- Dev conventions (UTC timestamps, no database, never read `.env` directly)
- What's implemented vs. still planned

### Skills

Two skills ship with the repo, available to all three agent tools without duplication:

| Skill | What it covers | Example triggers |
|---|---|---|
| `livelapse-init` | First-time setup — copies `.env`, configures feeds, runs `install.sh`, starts capture | "bootstrap", "init", "set up the project" |
| `livelapse-ops` | Ongoing operations — start/stop feeds, previews, logs, Linux/systemd deployment, DigitalOcean | "start the main feed", "render a preview", "deploy to Ubuntu" |

Each skill is stored once in `.agents/skills/` (the spec-standard location, read by Codex and OpenCode) and symlinked into `.claude/skills/` for Claude Code.

**You don't need to name them.** Each skill's description drives automatic loading — just ask naturally. To force-load one regardless of context:

```
/livelapse-init
/livelapse-ops what's the full systemd deployment sequence?
```

This pattern — `AGENTS.md` as the repo's standing brief, skills as operational playbooks — is a reusable template for any AI-native project. See [docs/cross-agent-skills-deployment-guide.md](docs/cross-agent-skills-deployment-guide.md) for the full compatibility matrix and deployment scenarios across Claude Code, Codex, and OpenCode.

---

## Configuration

### `feeds.conf`

Pipe-delimited, one feed per line. Comments start with `#`.

```
# name|url|fps|max_hours
artemis-main|https://www.youtube.com/live/5flTTJuoExo|1|48
construction-cam|rtsp://192.168.1.100/stream|0.2
```

- **name** — Alphanumeric + hyphens. Used as the folder name and systemd instance identifier.
- **url** — Any URL supported by yt-dlp, or a direct ffmpeg input (RTSP, HLS, RTMP, etc.).
- **fps** — Frames per second. `0.2` = one frame every 5 s, `0.5` = one every 2 s.
- **max_hours** — Optional. Stop capture automatically after this many hours. Omit or leave blank to run indefinitely. For yt-dlp sources, capture also stops automatically when the stream ends (detected via `is_live` check on reconnect).
- One feed name maps to one capture process. To run the same source twice, duplicate the entry with a new name.

### `.env`

```bash
# Data directory (mount your volume here)
LIVELAPSE_DATA_DIR=/mnt/livelapse

# Frame format: webp (default), png, jpg
LIVELAPSE_FORMAT=webp
LIVELAPSE_LOSSLESS=1           # WebP: 1=lossless. JPG: quality 1-31 (lower=better)

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

## How It Works

Each feed runs as a systemd service (`livelapse@<feed-name>.service`) wrapping a `yt-dlp | ffmpeg` pipeline:

- `yt-dlp` resolves the stream URL and pipes video to ffmpeg
- `ffmpeg` extracts frames at the configured rate, writing each as a timestamped file
- On stream drop, the service waits `RETRY_DELAY` seconds and reconnects automatically
- Filenames use `-strftime 1` so they reflect real wall-clock time — restarts produce no collisions and no gaps to reconcile

Health checks run every 60 seconds via cron, checking frame age per feed and disk usage. Alerts are rate-limited to one per 10 minutes per feed per alert type.

---

## CLI Reference

### Implemented today

```bash
./bin/livelapse status                                  # Feed table: state, PID, last frame, count
./bin/livelapse start                                  # Interactive picker of stopped feeds in a TTY
./bin/livelapse start artemis-main
./bin/livelapse start artemis-main --dry-run
./bin/livelapse stop                                   # Interactive picker of running feeds in a TTY
./bin/livelapse stop artemis-main
./bin/livelapse stop artemis-main --dry-run
./bin/livelapse stop artemis-main --yes                # Skip confirmation in non-interactive use
./bin/livelapse logs <feed-name>                        # Tail feed log (auto-follow in a TTY)
./bin/livelapse logs <feed-name> --follow               # Always follow
./bin/livelapse logs <feed-name> --lines 100            # Set line count
./bin/livelapse peek <feed-name> > ./out/latest.webp    # Write the latest captured frame
./bin/livelapse peek <feed-name> | imgcat               # Stream the latest frame into a viewer
./bin/livelapse watch <feed-name>                       # Live view: show latest frame, refresh every 1s
./bin/livelapse watch <feed-name> --interval 5          # Refresh every 5 seconds
./bin/livelapse watch <feed-name> --once                # Show one frame and exit
./bin/livelapse preview <feed-name>                     # Render a point-in-time MP4
./bin/livelapse preview <feed-name> --playback-fps 24
./bin/livelapse preview <feed-name> --output ./out/preview.mp4
./bin/livelapse preview <feed-name> --add-timestamp     # Burn capture time into each frame
./bin/livelapse preview <feed-name> --add-timestamp --timestamp-tz et
./bin/livelapse caffeinate start                        # Prevent idle sleep (macOS)
./bin/livelapse caffeinate stop
./bin/livelapse caffeinate status
```

**Timestamp overlay notes (`--add-timestamp`):**

- Burns each frame's capture time into the video using the filename as the source of truth
- `--timestamp-tz <zone>` sets the display timezone; common aliases (`utc`, `et`, `est`, `edt`, `pt`, `pst`, `pdt`) are accepted
- Default is Eastern time — resolves to `America/New_York`, so DST dates show `EDT` automatically

Lifecycle notes:

- `start` without a feed name offers a selector of currently stopped feeds in a TTY; non-interactive use targets all stopped feeds
- `stop` without a feed name offers a selector of currently running feeds in a TTY; non-interactive use targets all running feeds and requires `--yes`
- `stop` always asks for confirmation in an interactive terminal
- `start <feed-name>` checks whether that feed is already running and offers a stop-and-restart path instead of silently duplicating it
- During an active soak, prefer `--dry-run` first to confirm the target set before touching live captures

Peek notes:

- `peek` writes the newest captured frame's raw bytes to stdout, so pipe or redirect it instead of running it bare in an interactive terminal
- This is useful for quick inspection with tools such as `imgcat` or for copying out the latest frame without hunting through the feed directory

Watch notes:

- `watch` displays the latest captured frame inline in the terminal and refreshes automatically — a live monitor for what the feed is capturing right now
- For stopped feeds it shows the last valid frame before the stream dropped
- Renderer detection is automatic: iTerm2 and Kitty use native inline images; falls back to `chafa` or `viu` if installed
- `--interval <seconds>` controls the refresh rate (default 1s); `--once` shows a single frame and exits
- Read-only — never touches capture processes, PIDs, or log files

### Planned next

```
livelapse add <name> <url> [fps]  Add a new feed and start capture immediately
livelapse remove <name>           Stop and remove a feed (frames kept by default)
livelapse stitch <name> [opts]    Assemble captured frames into a timelapse video
livelapse disk                    Disk usage summary per feed and total
```

Behavior notes:
- `start` / `stop` without a feed name offer operation-aware selectors in a TTY
- Stopping and restarting a feed resumes capture in the same directory; gaps are expected and no backfill is attempted
- Duplicate the `feeds.conf` entry under a new feed name if you want a second concurrent capture from the same source
- `stitch` will share the `--add-timestamp` / `--timestamp-tz` overlay path with `preview`

### Stitching (planned)

```bash
livelapse stitch artemis-main \
  --start 2026-04-06T00:00:00Z \
  --end   2026-04-06T23:59:59Z \
  --playback-fps 30 \
  --output ./output/flyby.mp4
```

Options: `--start` / `--end` (ISO 8601), `--playback-fps` (default 30), `--output`, `--codec` (`libx264` / `libx265`), `--quality` (CRF, lower = better), `--dry-run`.

---

## Deployment

### Platform Compatibility

| Feature | macOS | Linux (Ubuntu 24+) |
|---|---|---|
| Install deps | `brew install yt-dlp ffmpeg jq` | `apt install yt-dlp ffmpeg jq curl bc` |
| Process management | Background process + PID file | systemd template units |
| Logs | `.pids/<feed>.log` | `journalctl -u livelapse@<feed>` |
| Health check | User crontab | `/etc/cron.d/livelapse` |
| Sleep prevention | `livelapse caffeinate start` | Not needed |

### Resource Usage (720p, WebP lossless, 1 fps)

| | Per feed |
|---|---|
| Frame size | ~500 KB – 1 MB |
| Per hour | ~1.8 – 3.6 GB |
| Per day | ~43 – 86 GB |
| CPU | ~5–10% of one vCPU |
| RAM | ~50–100 MB |

For a 3-feed, 3-day capture: 250 GB volume, 2 vCPU / 2 GB RAM droplet.

### DigitalOcean Provisioning (Planned)

`install/do-provision.sh` is planned work. The intended order:

1. Finish the local CLI backfill (`start`, `stop`)
2. Validate one manual Ubuntu deployment end-to-end
3. Add `install/do-provision.sh` once the infrastructure shape is proven

See [next_steps.md](next_steps.md) for the full implementation sequence.

---

## Directory Layout

```
livelapse/
├── AGENTS.md                       # Agent instructions — source of truth (Codex, OpenCode)
├── CLAUDE.md -> AGENTS.md          # Symlink for Claude Code
├── feeds.conf                      # Feed definitions
├── .env.example                    # Config template
├── next_steps.md                   # Implementation plan
├── bin/
│   ├── livelapse                   # CLI entrypoint
│   ├── capture.sh                  # Per-feed capture loop
│   └── common.sh                   # Shared shell helpers
├── docs/
│   ├── macos-runbook.md            # Current macOS operation guide
│   ├── cross-agent-skills-deployment-guide.md
│   └── livelapse-spec.md           # Original spec
├── install/
│   └── install.sh                  # Install deps + Linux systemd units
├── templates/
│   └── livelapse@.service          # Systemd template unit
├── .agents/
│   └── skills/
│       ├── livelapse-init/         # First-time setup skill (Codex, OpenCode)
│       │   └── SKILL.md
│       └── livelapse-ops/          # Operations skill (Codex, OpenCode)
│           └── SKILL.md
└── .claude/
    └── skills/
        ├── livelapse-init -> ...   # Symlink for Claude Code
        └── livelapse-ops -> ...    # Symlink for Claude Code
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

## License

MIT — see [LICENSE](LICENSE).
