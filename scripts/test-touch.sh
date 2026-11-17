#!/usr/bin/env bash
set -euo pipefail
project_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
build_root="${CODEX_TOUCH_BUILD_DIR:-$HOME/codex-touch-build}"
source_root="${1:-$build_root/upstream}"
python3 -B "$project_root/scripts/prepare-touch.py" "$source_root" --check
export CARGO_TARGET_DIR="$build_root/target"
export CARGO_BUILD_JOBS="${CODEX_TOUCH_JOBS:-1}"
export CARGO_NET_GIT_FETCH_WITH_CLI=true
export CARGO_TARGET_AARCH64_UNKNOWN_LINUX_GNU_RUSTFLAGS='-C link-arg=-fuse-ld=lld'
export RUSTUP_TOOLCHAIN=1.95.0
cd -- "$source_root/codex-rs"
# Reuse one compiled test executable for question and shared row-renderer coverage.
for filter in questions selection_popup_common request_user_input; do
    nice -n 5 cargo test --locked --profile dev-small --target aarch64-unknown-linux-gnu \
        -p codex-tui --lib "$filter" -- --test-threads=1
done
