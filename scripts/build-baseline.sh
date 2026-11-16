#!/usr/bin/env bash
set -euo pipefail

project_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
build_root="${CODEX_TOUCH_BUILD_DIR:-$HOME/codex-touch-build}"

if [[ "${1:-}" == '--help' ]]; then
    printf '%s\n' \
        'Build the pinned Codex baseline in Debian ARM64.' \
        'Usage: bash scripts/build-baseline.sh' \
        'CODEX_TOUCH_BUILD_DIR: Linux build directory (default: ~/codex-touch-build)' \
        'CODEX_TOUCH_JOBS: concurrent build jobs (default: 1)' \
        'The pinned release lockfile normalization is the only allowed source change.' \
        'Other source changes and existing package output are never replaced.'
    exit 0
fi
[[ $# == 0 ]] || { printf 'Unexpected arguments. Use --help.\n' >&2; exit 2; }

for tool in python3 git cargo rustup cc cmake pkg-config ld.lld nice; do
    command -v "$tool" >/dev/null || { printf 'Missing tool: %s\n' "$tool" >&2; exit 1; }
done
[[ "$(cc -dumpmachine)" == 'aarch64-linux-gnu' ]] \
    || { printf 'Run this build with the Debian ARM64 compiler.\n' >&2; exit 1; }

mapfile -t pin < <(python3 - "$project_root/upstream.json" <<'PY'
import json
import sys
with open(sys.argv[1]) as source:
    pin = json.load(source)
for key in ("repository", "tag", "commit", "rust_toolchain", "target", "profile"):
    value = pin[key]
    if not isinstance(value, str) or not value or "\n" in value:
        raise SystemExit(f"Invalid upstream pin: {key}")
    print(value)
PY
)
[[ ${#pin[@]} == 6 && "${pin[2]}" =~ ^[0-9a-f]{40}$ ]] \
    || { printf 'Invalid upstream.json.\n' >&2; exit 1; }
rustup run "${pin[3]}" rustc --version

build_root="$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$build_root")"
case "$build_root/" in
    /storage/*|/sdcard/*|/mnt/media_rw/*)
        printf 'Use the Linux filesystem for source, executables and caches.\n' >&2
        exit 1 ;;
esac
package_dir="$build_root/packages/baseline-${pin[1]#rust-v}"
[[ ! -e "$package_dir" ]] \
    || { printf 'Package already exists: %s\n' "$package_dir" >&2; exit 1; }
mkdir -p "$build_root/logs" "$build_root/downloads" "$build_root/packages"

if [[ ! -e "$build_root/upstream" ]]; then
    git clone --depth 1 --single-branch --branch "${pin[1]}" "${pin[0]}" "$build_root/upstream"
fi
[[ "$(git -C "$build_root/upstream" rev-parse HEAD)" == "${pin[2]}" ]] \
    || { printf 'Source commit differs from upstream.json.\n' >&2; exit 1; }
[[ -z "$(git -C "$build_root/upstream" status --porcelain -- . ':!codex-rs/Cargo.lock')" ]] \
    || { printf 'Baseline source has local changes; stopping.\n' >&2; exit 1; }
python3 -B "$project_root/scripts/prepare-lock.py" "$build_root/upstream"

# The upstream builder accepts a Cargo executable, but has no --locked option.
# Keep this executable on the Linux filesystem, outside shared storage.
cat > "$build_root/cargo-locked" <<'SH'
#!/bin/sh
exec cargo "$@" --locked --timings
SH
chmod 755 "$build_root/cargo-locked"

export CODEX_REPO_ROOT="$build_root/upstream"
export CARGO_TARGET_DIR="$build_root/target"
export TMPDIR="$build_root/downloads"
export RUSTUP_TOOLCHAIN="${pin[3]}"
export CARGO_BUILD_JOBS="${CODEX_TOUCH_JOBS:-1}"
export CMAKE_BUILD_PARALLEL_LEVEL="$CARGO_BUILD_JOBS"
export CARGO_NET_GIT_FETCH_WITH_CLI=true
export GIT_TERMINAL_PROMPT=0
export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUSTFLAGS='-C link-arg=-fuse-ld=lld'
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

log_path="$build_root/logs/build-$(date -u +%Y%m%dT%H%M%SZ).log"
nice -n 5 python3 -B "$CODEX_REPO_ROOT/scripts/build_codex_package.py" \
    --target "${pin[4]}" --cargo-profile "${pin[5]}" \
    --cargo "$build_root/cargo-locked" --package-dir "$package_dir" 2>&1 | tee "$log_path"

git -C "$CODEX_REPO_ROOT" diff --exit-code HEAD -- . ':!codex-rs/Cargo.lock'
python3 -B "$project_root/scripts/prepare-lock.py" "$CODEX_REPO_ROOT" --check
printf 'Built baseline package: %s\nBuild log: %s\n' "$package_dir" "$log_path"
