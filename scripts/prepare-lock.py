#!/usr/bin/env python3
"""Normalize release-tag local package versions without resolving dependencies."""

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path


def normalize_local_versions(original: bytes, version: str) -> bytes:
    sections = re.split(r"(?=^\[\[package\]\]$)", original.decode(), flags=re.MULTILINE)
    for index, section in enumerate(sections):
        if not section.startswith("[[package]]"):
            continue
        package = tomllib.loads(section)["package"][0]
        if "source" not in package and package["version"] == "0.0.0":
            sections[index] = re.sub(
                r'^version = "0\.0\.0"$',
                f'version = "{version}"',
                section,
                count=1,
                flags=re.MULTILINE,
            )
    return "".join(sections).encode()


def prepare(path: Path, pin: dict, version: str, *, check_only: bool = False) -> bool:
    original = path.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if digest == pin["lockfile_build_sha256"]:
        return False
    if digest != pin["lockfile_upstream_sha256"]:
        raise ValueError("Cargo.lock differs from both pinned hashes; refusing to replace it")
    if check_only:
        raise ValueError("Cargo.lock still needs the pinned local-version normalization")
    normalized = normalize_local_versions(original, version)
    if hashlib.sha256(normalized).hexdigest() != pin["lockfile_build_sha256"]:
        raise ValueError("Normalized Cargo.lock does not match the pinned build hash")
    path.write_bytes(normalized)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--pin", type=Path, default=Path(__file__).resolve().parents[1] / "upstream.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    pin = json.loads(args.pin.read_text())
    version = tomllib.loads((args.source / "codex-rs/Cargo.toml").read_text())["workspace"]["package"]["version"]
    if version != pin["tag"].removeprefix("rust-v"):
        raise SystemExit("Workspace version does not match the pinned tag")
    try:
        changed = prepare(args.source / "codex-rs/Cargo.lock", pin, version, check_only=args.check)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print("Normalized local package versions." if changed else "Verified pinned build lockfile.")


if __name__ == "__main__":
    main()
