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
# Match upstream rust-ci-full-nextest-platform.yml for app-level async tests.
export RUST_MIN_STACK=8388608
cd -- "$source_root/codex-rs"
# Default-off regressions must not inherit the launcher's touch opt-in.
unset CODEX_TOUCH
artifacts="$(mktemp)"
trap 'rm -f -- "$artifacts"' EXIT
nice -n 5 cargo test --locked --profile dev-small --target aarch64-unknown-linux-gnu \
    -p codex-tui --lib --no-run --message-format=json-render-diagnostics >"$artifacts"
python3 - "$artifacts" <<'PYTHON'
import json
from pathlib import Path
import subprocess
import sys
artifacts = [json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.startswith("{")]
executables = {item["executable"] for item in artifacts
               if item.get("reason") == "compiler-artifact" and item.get("executable")
               and item.get("target", {}).get("name") == "codex_tui"}
if len(executables) != 1:
    raise SystemExit("Expected one codex-tui test executable")
binary = executables.pop()
filters = """touch history_search sidebar_close questions selection_popup_common request_user_input shortcut footer
live_center status_indicator resume_picker list_selection_view multi_select_picker
skills_toggle experimental_features memories_settings hooks_browser app_link
mcp_server_elicitation custom_prompt feedback_note keymap_setup provider::editor
onboarding cwd_prompt update_prompt model_migration unarchive_prompt
external_agent_config_migration pager_overlay command_popup file_search_popup
skill_popup mentions_v2 warnings_view analytics
approval_overlay user_verification status_line_setup title_setup config_panel
startup_hooks_review daemon_recovery""".split()
listing = subprocess.check_output([binary, "--list"], text=True)
names = [line.removesuffix(": test") for line in listing.splitlines() if line.endswith(": test")]
for pattern in filters:
    if not any(pattern in name for name in names):
        raise SystemExit(f"No tests match registered filter: {pattern}")
selected = {name for name in names if any(pattern in name for pattern in filters)}
print(f"Running {len(selected)} distinct Rust regressions across {len(filters)} registered filters.", flush=True)
subprocess.run(["nice", "-n", "5", binary, "--test-threads=1", *filters], check=True)
PYTHON
