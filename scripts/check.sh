#!/usr/bin/env bash
set -euo pipefail

project_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd -- "$project_root"

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

for path in README.md LICENSE VERSION CHANGELOG.md AGENTS.md \
    .gitignore .gitattributes .editorconfig docs/design.md \
    docs/development.md src/README.md tests/README.md scripts/check.sh; do
    [[ -s "$path" ]] || fail "Missing or empty file: $path"
done

version="$(cat VERSION)"
[[ "$version" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] \
    || fail 'VERSION must contain X.Y.Z without leading zeros.'
grep -Fq "## [$version] - " CHANGELOG.md \
    || fail 'CHANGELOG.md has no entry for VERSION.'
grep -Fq "**$version**" README.md \
    || fail 'README.md does not show the current VERSION.'

bash -n scripts/check.sh
[[ -d .git || -f .git ]] || fail 'Initialize this directory as a Git repository first.'
git_cmd rev-parse --is-inside-work-tree >/dev/null
git_cmd diff --check
git_cmd diff --cached --check

printf 'PASS: scaffold checks (version %s). No functional tests exist yet.\n' "$version"
