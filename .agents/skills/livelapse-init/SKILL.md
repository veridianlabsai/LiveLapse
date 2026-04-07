---
name: livelapse-init
description: First-time setup and project initialization for LiveLapse. Use when the user says "bootstrap", "init", "initialize", "set up the project", "prepare", or "get started" after cloning the repo.
metadata:
  author: veridian-labs
  version: "0.1"
---

# LiveLapse — Project Initialization

Walk the user through first-time setup interactively. Do each step in order. Check current state before acting — never overwrite work that already exists without asking.

---

## Step 1 — Check Current State

Before doing anything, inspect:

```bash
ls .env 2>/dev/null && echo "EXISTS" || echo "MISSING"
cat feeds.conf
```

- If `.env` already exists: ask the user whether to skip env setup or re-initialize it.
- If `feeds.conf` already has real feeds (not just the example artemis2 entries): confirm with the user before modifying it.

---

## Step 2 — Set Up `.env`

Copy from `.env.example` and set `LIVELAPSE_DATA_DIR` to `<repo-root>/data`:

```bash
cp .env.example .env
```

Then edit `.env` to set:

```
LIVELAPSE_DATA_DIR=<absolute-path-to-repo>/data
```

Use the actual absolute path of the repo (i.e. the directory where `bin/livelapse` lives). Do not use a relative path — the capture process may be invoked from different working directories.

Tell the user:
> "Frames will be stored in `<path>/data/<feed-name>/`. You can change this anytime by editing `.env`."

---

## Step 3 — Configure Feeds

Show the user what is currently in `feeds.conf`, then ask:

> "What streams do you want to capture? For each feed, I need:
> - A short name (letters, numbers, hyphens — e.g. `main-cam`)
> - The stream URL (YouTube Live, RTSP, HLS, or anything yt-dlp supports)
> - Frames per second (e.g. `1` for 1 fps, `0.2` for one frame every 5 seconds)
>
> You can add as many as you like, or press Enter to keep the existing feeds."

If the user provides feeds, rewrite `feeds.conf` with their entries. Format:

```
# name|url|fps
<name>|<url>|<fps>
```

If they want to keep the existing feeds unchanged, skip this step.

**Helpful fps guidance to offer if asked:**
- `1` — one frame per second (good for fast-moving events, higher storage)
- `0.5` — one frame every 2 seconds
- `0.2` — one frame every 5 seconds (good for slow-changing scenes, lower storage)
- `0.033` — one frame every 30 seconds (construction sites, weather cams)

---

## Step 4 — Install Dependencies

Run the installer:

```bash
./install.sh
```

This installs `yt-dlp`, `ffmpeg`, `jq`, `curl`, and `chafa` via Homebrew (macOS) or apt (Linux), and on Linux also installs the systemd unit template and cron health check.

If the installer fails, show the user the error and suggest running it manually.

---

## Step 5 — Verify and Offer to Start

Show the current status:

```bash
./bin/livelapse status
```

Then offer next steps based on platform:

**macOS:**
> "Your project is ready. To start capturing:
> - Start sleep prevention: `./bin/livelapse caffeinate start`
> - Start a feed manually: `nohup ./bin/capture.sh <feed-name> > .pids/<feed-name>.log 2>&1 < /dev/null & echo $! > .pids/<feed-name>.pid`
>
> Would you like me to start capture for any of your feeds now?"

If the user says yes, start the requested feeds using the nohup pattern above.

**Linux:**
> "Your project is ready. To start capturing:
> - `systemctl start livelapse@<feed-name>`
>
> Would you like me to start any feeds?"

---

## What to Do If Something Goes Wrong

- **`.env.example` missing** — the repo is incomplete; ask the user to re-clone.
- **`install.sh` missing** — check `install/install.sh` as a fallback; it's the same file.
- **`yt-dlp` or `ffmpeg` not found after install** — on macOS, check that Homebrew is installed and that `/usr/local/bin` or `/opt/homebrew/bin` is in PATH.
- **Permissions error on `.pids/`** — create it manually: `mkdir -p .pids`.
- **User unsure of stream URL** — for YouTube Live, the URL is the live stream page URL (e.g. `https://www.youtube.com/live/XXXXX`). For RTSP cameras, check the camera's admin panel.

---

## When You're Done

Confirm what was set up:
- Path where frames will land
- Feeds configured
- Whether dependencies are installed
- Whether any feeds are running

Keep it brief — one paragraph or a short bulleted summary.
