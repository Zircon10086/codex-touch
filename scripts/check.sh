#!/usr/bin/env bash
set -euo pipefail

project_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd -- "$project_root"

baseline_package=''
touch_package=''
upstream_source=''
rust_tests=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --rust-tests) rust_tests=true; shift ;;
        --baseline-package|--touch-package|--upstream-source)
            [[ $# -ge 2 ]] || { printf 'Missing path for %s\n' "$1" >&2; exit 2; }
            case "$1" in
                --baseline-package) baseline_package="$2" ;;
                --touch-package) touch_package="$2" ;;
                --upstream-source) upstream_source="$2" ;;
            esac
            shift 2 ;;
        *) printf 'Usage: bash scripts/check.sh [--baseline-package PATH] [--touch-package PATH] [--upstream-source PATH] [--rust-tests]\n' >&2; exit 2 ;;
    esac
done

fail() {
    printf 'FAIL: %s\n' "$*" >&2
    exit 1
}

if command -v git >/dev/null 2>&1; then
    git_cmd() { git -c safe.directory="$project_root" -C "$project_root" "$@"; }
elif command -v termux-run >/dev/null 2>&1; then
    git_cmd() { termux-run --cwd "$project_root" git -c safe.directory="$project_root" "$@"; }
else
    fail 'Git is required (directly or through termux-run).'
fi

for path in README.md LICENSE NOTICE VERSION CHANGELOG.md AGENTS.md CONTRIBUTING.md \
    .gitignore .gitattributes .editorconfig docs/design.md \
    docs/development.md docs/build.md docs/termux-touch.md src/README.md tests/README.md scripts/check.sh \
    scripts/probe-termux-ime.sh tests/probe_pty.py upstream.json \
    scripts/build-baseline.sh scripts/prepare-lock.py tests/test_prepare_lock.py \
    tests/baseline_smoke.py docs/baseline-build.md scripts/build-touch.sh \
    scripts/prepare-touch.py scripts/run-touch.sh scripts/test-touch.sh tests/touch_pty.py \
    src/async-question-touch.patch src/LICENSE.upstream src/NOTICE.upstream docs/phase1.md docs/shortcut-touch.md tests/test_prepare_touch.py \
    .github/workflows/check.yml; do
    [[ -s "$path" ]] || fail "Missing or empty file: $path"
done

cmp -s LICENSE src/LICENSE.upstream || fail 'Project license must match the pinned Apache-2.0 text.'
python3 - <<'PYTHON'
from pathlib import Path
assert Path("src/NOTICE.upstream").read_bytes() in Path("NOTICE").read_bytes(), "Root NOTICE must retain upstream notices"
PYTHON

version="$(cat VERSION)"
[[ "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] \
    || fail 'VERSION must contain X.Y.Z without leading zeros.'
grep -Fq "## [$version] - " CHANGELOG.md \
    || fail 'CHANGELOG.md has no entry for VERSION.'
grep -Fq "**$version**" README.md \
    || fail 'README.md does not show the current VERSION.'

bash -n scripts/check.sh
bash -n scripts/probe-termux-ime.sh
bash -n scripts/build-baseline.sh
bash -n scripts/build-touch.sh
bash -n scripts/run-touch.sh
bash -n scripts/test-touch.sh
bash scripts/build-touch.sh --help >/dev/null
python3 -c 'import ast; from pathlib import Path; [ast.parse(Path(p).read_text()) for p in ("scripts/prepare-touch.py", "tests/touch_pty.py")]'
git_cmd apply --numstat src/async-question-touch.patch >/dev/null
bash scripts/build-baseline.sh --help >/dev/null
python3 -m json.tool upstream.json >/dev/null
python3 -B tests/test_prepare_lock.py
# Keep temporary fixture repositories in the same environment as their Git.
if command -v git >/dev/null 2>&1; then
    python3 -B tests/test_prepare_touch.py
else
    termux-run --cwd "$project_root" python3 -B tests/test_prepare_touch.py
fi
python3 -c 'import ast; from pathlib import Path; ast.parse(Path("tests/baseline_smoke.py").read_text())'
python3 tests/probe_pty.py
if [[ -n "$baseline_package" ]]; then
    python3 -B tests/baseline_smoke.py "$baseline_package"
fi
if [[ -n "$upstream_source" ]]; then
    python3 -B scripts/prepare-touch.py "$upstream_source" --check
fi
if "$rust_tests"; then
    bash scripts/test-touch.sh "${upstream_source:-${CODEX_TOUCH_BUILD_DIR:-$HOME/codex-touch-build}/upstream}"
fi
if [[ -n "$touch_package" ]]; then
    python3 -B tests/baseline_smoke.py "$touch_package"
    python3 -B tests/touch_pty.py "$touch_package"
fi
[[ -d .git || -f .git ]] || fail 'Initialize this directory as a Git repository first.'
git_cmd rev-parse --is-inside-work-tree >/dev/null
git_cmd diff --check
git_cmd diff --cached --check

printf 'PASS: repository checks (version %s). Android touch and IME require a real terminal.\n' "$version"
