[English](README.md) | [简体中文](README.zh-CN.md)

# codex-touch

Touch controls for Codex in Termux. Tap shortcut hints to perform actions that would otherwise require Shift or other keyboard combinations on a phone.

This project maintains a Rust TUI patch and on-device build tools for **Codex 0.169.0**. It builds a separate adapted client using the existing mouse protocol and runtime key bindings. No Termux APK modification is required. The project is independently maintained and is not affiliated with OpenAI.

Current version: **0.2.0**, the first functional release. See the [changelog](CHANGELOG.md) and [v0.2.0 Release](https://github.com/Zircon10086/codex-touch/releases/tag/v0.2.0). This release provides source and checksums; build the client using the instructions below. No prebuilt binary is included.

The `main` branch adds picker and dialog controls beyond v0.2.0. On-device testing was confirmed on 2026-11-18; see [coverage and acceptance](docs/picker-touch.md). These changes are not part of the v0.2.0 Release.

## Features and scope

| Surface | Touch controls |
| --- | --- |
| Asynchronous questions | Expand the summary, choose an answer, use Other or freeform editing, submit, skip, and navigate between questions |
| Main composer | Tap help, newline, and mode hints; help and newline remain available with a draft |
| Shortcut help | Tap fully visible individual actions, including runtime single-key and two-key bindings |
| Agent command center | Tap a task to select it, then tap the selected task to open it; use filters, grouping, footer hints, and help actions |
| Working status | Tap the fully visible `esc to interrupt` hint; dragging does not activate it |
| Resume / fork (development) | Select/open sessions, filters, sorting, density, preview, expansion, and cancellation |
| Menus and dialogs (development) | Shared lists, settings, approvals, synchronous questions, MCP forms, provider fields, and startup choices |
| Completion and navigation (development) | Command/file/skill/mention completion, floating shortcut guides, transcript/pager controls, warnings, and analytics |

Touch support is opt-in through `CODEX_TOUCH=1` and targets the default full-screen TUI. The development patch adds the controls listed above; `--no-alt-screen` remains unsupported. Shortcut reference entries that require a different active view remain explanatory. Open the Android keyboard manually. A convenient newline action inside the asynchronous answer editor and a reported multi-question stall remain follow-up work. See [shortcut and command center coverage](docs/shortcut-touch.md) for details.

## Build and run on a phone

The verified environment is Debian chroot on an ARM64 Android phone, with Termux providing the terminal. The target is `aarch64-unknown-linux-gnu` (glibc); the resulting package runs inside a compatible Linux userspace. Other Termux distribution channels, proot, and other architectures have not received equivalent validation.

Prepare Debian and install the dependencies and pinned Rust 1.95.0 toolchain using the [phone build guide](docs/build.md). Inside that environment, use a Linux filesystem:

```sh
git clone https://github.com/Zircon10086/codex-touch.git
cd codex-touch
bash scripts/check.sh
bash scripts/build-touch.sh
bash scripts/run-touch.sh
```

The default build directory is `~/codex-touch-build`; the output is `packages/touch-pickers-0.169.0`. Existing packages are never overwritten. Set `CODEX_TOUCH_PACKAGE` to a new directory for later builds. Building the unmodified baseline first is optional.

The launcher sets `CODEX_TOUCH=1` without changing HOME or CODEX_HOME. Running it as the same Linux user as your regular Codex shares configuration and sessions. Set a separate `CODEX_HOME` if you want isolation. It does not replace your regular `codex` command.

A full build downloads dependencies and uses substantial disk space. The initial baseline used about 18.1 GiB; adding test caches and retaining four packages brought the measured total to about 32.57 GiB. These are observations from one phone, not minimum requirements; see the [baseline build record](docs/baseline-build.md). Builds use one job and reduced scheduling priority by default. Keep sources, caches, and executables on a Linux filesystem rather than Android shared storage.

## Verification and contributions

The unreleased picker/dialog development passed 1,297 distinct Rust regressions on 2026-11-18. On-device testing was subsequently confirmed. See the [development validation record](docs/picker-touch.md) for package tests and acceptance details.

As of 2026-11-17, 409 distinct Rust regression tests, isolated model/tool round trips, SGR mouse PTY checks, and terminal restoration checks passed. On-device testing confirmed the main asynchronous answer paths, followed by the agent command center and interrupt hint fixes. Detailed evidence and remaining gaps are recorded in [phase one](docs/phase1.md) and [shortcut testing](docs/shortcut-touch.md). Automated tests do not establish Android keyboard behavior.

```sh
bash scripts/check.sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-pickers-0.169.0"
```

Basic checks require Bash, Python 3.11+ with its standard library, Git, and common Unix tools. GitHub Actions runs those checks. Rust compilation and actual-package validation are explicit, longer-running steps. See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute.

## Documentation and source

- [Phone build guide](docs/build.md): dependencies, first build, launch, rebuilding, and environment boundaries.
- [Design](docs/design.md) and [development guide](docs/development.md): implementation conventions, checks, and versioning.
- [Initial investigation](docs/termux-touch.md): Termux input routing and keyboard experiments.
- [src/](src/README.md): the pinned upstream patch, licenses, and provenance.
- [tests/](tests/README.md): synthetic input, package, and PTY validation.

English is the default project language. Each document links to its Simplified Chinese translation at the top.

## License

Current source is licensed under the [Apache License 2.0](LICENSE), matching the pinned upstream Codex version. See [NOTICE](NOTICE) and [source provenance](src/README.md) for copyright, modifications, and upstream notices. Third-party code retains its own licenses. The historical `v0.1.0` MIT license record remains unchanged.
