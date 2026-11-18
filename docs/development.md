[English](development.md) | [简体中文](development.zh-CN.md)

# Development guide

## Local checks

```sh
bash scripts/check.sh
```

Basic checks cover patch syntax, required files, version/changelog consistency, Shell and Python syntax, Git whitespace, document language pairs and links, and the IME probe's synthetic PTY hit/cleanup behavior. The probe does not start Codex or manipulate the Android foreground, and cannot prove keyboard display. See [device comparison steps](termux-touch.md).

The script locates the repository root itself and can run from another directory. It needs Bash, Python 3.11+ with the standard library, Git, and common Unix tools. Use the current Linux environment's Git. On the development device only, the existing `termux-run` bridge is a fallback when local Git is unavailable; it is not a project dependency. See the [environment example](build.md#development-device-example).

Invoke shared-storage scripts with `bash`; no filesystem permission or mount change is needed.

## Daily workflow

Follow the [phone build guide](build.md) to obtain the pinned source and a runnable package. Sources, compilation caches, and downloaded dependencies belong on the Linux filesystem. This repository holds the version pin, build entry points, and adaptation patch.

1. Create a focused `feat/<name>` or `fix/<name>` branch from `main`.
2. Inspect existing source and interfaces before implementing. Add dependency manifests only when an implementation needs them.
3. Keep source changes in `src/`, meaningful tests in `tests/`, and new checks in the unified entry point.
4. Record user-visible changes under `Unreleased` in `CHANGELOG.md`, update both documentation languages, run checks, review the diff, and commit.

Use focused English commit messages such as `feat: add ...` or `fix: ...`. On the development device, access host tools through `termux-run`; Debian's native Git can directly manage guest source.

If Git reports an ownership mismatch, scope the exception to one invocation and this repository:

```sh
git -c safe.directory="$(pwd -P)" status
```

When an identity is not configured, provide `user.name` and `user.email` with one-command `git -c` options. Do not change global configuration automatically. Public commits and annotated tags use the verified GitHub noreply identity.

## Versions and releases

- `VERSION` is the version source of truth: `X.Y.Z`, with tag `vX.Y.Z`.
- Version 0.2.0 is the first functional release; 0.1.0 is the historical scaffold. Put development changes under `Unreleased` without bumping the version for every commit.
- During 0.x development, increment the minor version for features or incompatible changes, and the patch version for compatible fixes. Use stable semantic-versioning expectations from 1.0.0 onward.
- Update VERSION, both READMEs, both changelogs, and release notes together. Create an annotated tag on the validated commit.
- Never move a published tag; publish a new version to correct it.

A user-confirmed version update includes a GitHub Release in the same delivery unless the user explicitly defers it. Ordinary development commits can remain under `Unreleased`; once the version update is confirmed, do not stop at a source push or ask for separate release authorization again.

Complete the release in this order:

1. Choose the version, move accepted changes into its dated changelog entry, and update VERSION, both READMEs, and `docs/releases/vX.Y.Z.md` plus its Chinese translation.
2. Run repository checks and verify the exact patch against the tested package. Reuse recorded Rust/package results when the tested code is unchanged; otherwise run the relevant validation.
3. Commit using the verified noreply identity. Create an annotated version tag on that exact commit. Push only `main` and that tag, with automatic tag following disabled.
4. Export the tagged repository source without Git metadata, local configuration, or caches. Compare archive contents to the commit, check the extracted source, and create SHA256SUMS. Retain licenses and notices.
5. Create a draft Release with English notes and translation links; upload the source archive and checksums. Verify the release commit's CI and download the draft assets to check their bytes.
6. Publish the Release as Latest, then verify its public metadata, tag, assets and anonymous downloads. Record the release URL and CI result. A source push or draft alone does not complete a confirmed version update; if publication is blocked, report the exact incomplete step.

Use Git in the current environment. On the development device, authenticated remote operations use Termux Git/gh through `termux-run`. Preserve existing published tags and releases. Never push local backup branches or unrelated historical tags using `--all`, `--mirror`, or `--tags`.

Actual-package validation is described in [phase one](phase1.md). `--rust-tests` and `--touch-package PATH` are explicit, longer-running checks; basic checks do not compile Codex.

## Updating the upstream patch

Keep the upstream checkout's HEAD at the commit pinned in `upstream.json`. Do not commit adaptations in that checkout and move HEAD away from the baseline. The patch in this repository is the versioned adaptation. After editing, mark each new file with `git add -N <specific-new-file>` in the upstream checkout, then export from the codex-touch repository:

```sh
git -C "$HOME/codex-touch-build/upstream" diff --binary HEAD -- codex-rs/tui > src/async-question-touch.patch
python3 -B scripts/prepare-touch.py "$HOME/codex-touch-build/upstream" --check
```

Export only the TUI directory. `prepare-lock.py` maintains the known Cargo.lock metadata correction separately. Do not include unrelated edits. Register additional Rust test filters in `scripts/test-touch.sh` rather than relying on an unrecorded local command.

## Continuous checks and documentation

`.github/workflows/check.yml` runs `bash scripts/check.sh` on `main` pushes and pull requests. Permissions are limited to `contents: read`; checkout is pinned to a verified commit and does not persist credentials. Basic CI does not download or compile upstream Codex. Developers run full Rust and package validation explicitly.

Default documentation is English. Chinese translations use sibling `*.zh-CN.md` files with reciprocal language links at the top. `scripts/check-docs.py`, called by the unified check script, verifies pairs, local links, and version consistency. Retain multilingual test inputs required to verify editing and character widths.
