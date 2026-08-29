#!/usr/bin/env python3
"""Build a deterministic oh-my-niu release bundle zip and SHA-256 file."""

from __future__ import annotations

import argparse
import hashlib
import tempfile
import zipfile
from pathlib import Path

import validate_bundle


ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
RELEASE_DIRS = [
    "lib",
    "plugins",
    "packs",
    "aliases",
    "completions",
    "prompts",
    "keybindings",
    "themes",
    "wasm",
    "docs",
    "templates",
    "tools",
]
RELEASE_FILES = ["oh-my-niu.winux", "bundle.toml", "index.toml", "README.md", "CHANGELOG.md"]


def include_release_path(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if "__pycache__" in relative.parts:
        return False
    if path.suffix in {".pyc", ".pyo"}:
        return False
    return True


def load_version() -> str:
    return validate_bundle.load_toml(ROOT / "bundle.toml")["version"]


def release_paths() -> list[Path]:
    paths: list[Path] = []
    for name in RELEASE_FILES:
        paths.append(ROOT / name)
    for dirname in RELEASE_DIRS:
        paths.extend(path for path in (ROOT / dirname).rglob("*") if path.is_file() and include_release_path(path))
    return sorted(paths, key=lambda path: path.relative_to(ROOT).as_posix())


def write_zip(zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in release_paths():
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, FIXED_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checksum(zip_path: Path, digest: str) -> Path:
    checksum_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
    return checksum_path


def build(out_dir: Path, check: bool) -> tuple[Path, str, Path | None]:
    errors = validate_bundle.validate()
    if errors:
        raise SystemExit("\n".join(f"error: {error}" for error in errors))

    version = load_version()
    zip_path = out_dir / f"oh-my-niu-{version}.zip"
    write_zip(zip_path)
    digest = sha256_file(zip_path)
    checksum_path = None if check else write_checksum(zip_path, digest)
    return zip_path, digest, checksum_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT / "dist"), help="Output directory for release artifacts")
    parser.add_argument("--check", action="store_true", help="Build in a temporary directory without writing dist artifacts")
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="oh-my-niu-package-") as temp:
            zip_path, digest, _ = build(Path(temp), check=True)
            print(f"package check ok: {zip_path.name} sha256={digest}")
        return 0

    zip_path, digest, checksum_path = build(Path(args.out_dir), check=False)
    print(f"wrote {zip_path}")
    print(f"wrote {checksum_path}")
    print(f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
