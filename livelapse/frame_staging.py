from __future__ import annotations

from pathlib import Path


def index_frame_paths(source_dir: Path, frame_ext: str) -> list[str]:
    pattern = f"*.{frame_ext}"
    return sorted(str(path) for path in source_dir.glob(pattern) if path.is_file())


def write_frame_manifest(source_dir: Path, frame_ext: str, manifest_path: Path) -> int:
    frame_paths = index_frame_paths(source_dir, frame_ext)
    if frame_paths:
        manifest_path.write_text("\n".join(frame_paths) + "\n", encoding="utf-8")
    else:
        manifest_path.write_text("", encoding="utf-8")
    return len(frame_paths)


def load_manifest_frame_paths(manifest_path: Path) -> list[str]:
    return [line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stage_frame_links(frame_paths: list[str], stage_dir: Path, frame_ext: str) -> int:
    stage_dir.mkdir(parents=True, exist_ok=True)

    for index, frame_path in enumerate(frame_paths, start=1):
        target_path = stage_dir / f"{index:06d}.{frame_ext}"
        if target_path.exists() or target_path.is_symlink():
            target_path.unlink()
        target_path.symlink_to(frame_path)

    return len(frame_paths)
