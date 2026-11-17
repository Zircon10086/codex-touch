#!/usr/bin/env bash
set -euo pipefail
build_root="${CODEX_TOUCH_BUILD_DIR:-$HOME/codex-touch-build}"
package="${CODEX_TOUCH_PACKAGE:-$build_root/packages/touch-0.169.0}"
[[ -f "$package/touch-build.json" && -x "$package/bin/codex" ]] || {
    printf 'No touch build at %s. Run scripts/build-touch.sh in Debian first.\n' "$package" >&2
    exit 1
}
export CODEX_TOUCH=1
exec "$package/bin/codex" "$@"
