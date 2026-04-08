# LiveLapse V1 Architecture

## Goal

Keep LiveLapse operator-first and filesystem-native, while moving the product logic out of a single Bash application file and into testable modules.

## Recommended Shape

- Keep `ffmpeg`, `yt-dlp`, and systemd as the media and supervision primitives.
- Keep the filesystem as the source of truth for captured frames and rendered outputs.
- Keep a thin shell layer for install, launch wrappers, and Linux/macOS integration.
- Move CLI behavior, manifest parsing, timestamp handling, preview orchestration, and extract planning into Python modules.

## Target Layers

### 1. Platform layer

- `install.sh`, `install/install.sh`
- systemd units
- macOS-specific process helpers

### 2. Thin command layer

- `bin/livelapse`
- validates environment and shells out to Python modules

### 3. Python application layer

- feed/config parsing
- timezone normalization
- frame timestamp parsing
- preview staging and subtitle generation
- manifest parsing and fragment planning

### 4. External tool adapters

- `ffmpeg`
- `yt-dlp`
- `journalctl` or local log files

## Migration Stages

1. Extract inline Python heredocs into package modules and add tests.
2. Move shared parsing and validation out of Bash into Python.
3. Replace the large Bash command dispatcher with a Python CLI that preserves the current command surface.
4. Decide whether the long-running capture worker should remain shell-based or move into Python.

## What Should Stay In Shell

- bootstrap scripts
- packaging/install steps
- systemd integration
- simple operator wrappers where shell is the natural OS boundary

## What Should Move To Python

- all timestamp and timezone logic
- manifest parsing and fragment selection
- preview/extract orchestration
- any code that needs tests, reuse, or structured error handling

## Non-Goals For V1

- adding a database before it is necessary
- replacing `ffmpeg` or `yt-dlp`
- introducing distributed services for a local-first workflow
