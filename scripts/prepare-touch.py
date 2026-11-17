#!/usr/bin/env python3
"""Apply/check the exact touch patch without overwriting unrelated source edits."""
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


def prepare(source, check=False):
    pin = json.loads((PROJECT / "upstream.json").read_text())
    patch = PROJECT / "src/async-question-touch.patch"

    def git(*args, env=None):
        return subprocess.check_output(["git", "-C", str(source), *args], env=env)

    if git("rev-parse", "HEAD").decode().strip() != pin["commit"]:
        raise ValueError("Source commit differs from upstream.json")
    subprocess.run(["python3", "-B", str(PROJECT / "scripts/prepare-lock.py"), str(source),
                    *(["--check"] if check else [])], check=True)
    with tempfile.TemporaryDirectory(prefix="codex-touch-index-") as directory:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(directory) / "index")}
        git("read-tree", "HEAD", env=env)
        git("apply", "--cached", "--whitespace=error", str(patch), env=env)
        paths = git("diff", "--cached", "--name-only", "-z", env=env).decode().split("\0")[:-1]
        changed = set(git("diff", "HEAD", "--name-only", "-z").decode().split("\0")[:-1])
        changed.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0")[:-1])
        unexpected = changed - set(paths) - {"codex-rs/Cargo.lock"}
        if unexpected:
            raise ValueError(f"Unrelated source edits: {sorted(unexpected)}")
        expected = {path: git("show", f":{path}", env=env) for path in paths}
        if all((source / path).is_file() and (source / path).read_bytes() == data
               for path, data in expected.items()):
            print("PASS: exact touch patch is present.")
            return
        if check:
            raise ValueError("Source does not match the touch patch")
        tracked = set(git("ls-tree", "-r", "--name-only", "-z", "HEAD").decode().split("\0")[:-1])
        for path in paths:
            current = source / path
            if path in tracked:
                if not current.is_file() or current.read_bytes() != git("show", f"HEAD:{path}"):
                    raise ValueError(f"Local edits in patch target: {path}")
            elif current.exists():
                raise ValueError(f"New patch path already exists: {path}")
        # git apply --check validates all hunks/new paths before any mutation.
        git("apply", "--check", "--whitespace=error", str(patch))
        git("apply", "--whitespace=error", str(patch))
        if not all((source / path).read_bytes() == data for path, data in expected.items()):
            raise ValueError("Applied source differs from expected patch; inspect local changes")
        print("PASS: applied the pinned touch patch.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        prepare(args.source.resolve(), args.check)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"FAIL: {error}\n")
