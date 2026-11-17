[English](baseline-build.md) | [简体中文](baseline-build.zh-CN.md)

# On-device baseline build

Build the unmodified upstream client to verify the environment and provide a comparison. [upstream.json](../upstream.json) pins the repository, tag, commit, toolchain, target, and profile.

- Codex: `rust-v0.169.0`, commit `d32063f96c2dff1dc96af839b3952abb6acfeda4`.
- Rust: `1.95.0`, with rustfmt, Clippy, and rust-src.
- Target: `aarch64-unknown-linux-gnu`, running in Debian chroot on the phone.
- Profile: upstream `dev-small`, one build job by default, LLD, and `--locked` Cargo dependencies.

## Dependencies

Debian packages: `build-essential cmake pkg-config libssl-dev libcap-dev lld git`. Python 3.11+ and HTTPS root certificates must also be available. Install the pinned Rust toolchain through rustup. Git must access the guest source directly, and the C/C++ compiler must target glibc.

Neither just nor the Android SDK is required beforehand. Other dependencies follow the pinned source's build requirements. Native Termux's Android/Bionic compiler is not used for this Linux build.

## Usage

Inside the project directory in Debian chroot:

```sh
bash scripts/build-baseline.sh
```

The default workspace is `~/codex-touch-build`:

```text
upstream/                 Pinned source with local lockfile versions normalized
target/                   Cargo build and incremental cache
downloads/                V8, ripgrep, and other upstream packaging downloads
logs/                     Build logs
packages/baseline-0.169.0/ Complete baseline package
```

Cargo downloads also use `~/.cargo`. Even though V8 uses a prebuilt library, Cargo initially downloads Git submodules for its dependency, using several GiB.

Use `CODEX_TOUCH_BUILD_DIR` for another Linux directory and `CODEX_TOUCH_JOBS` to change concurrency. The first charging-phone attempt with two jobs reached a battery temperature of 46.8°C, so the project default became one job, independently of global Cargo settings. Keep sources and output off Android shared storage. Long initial builds require Termux to remain active, a wake lock if appropriate, and monitoring of temperature and memory.

The script rejects a different source commit, changes beyond the known lockfile correction, and an existing output package. Download or compilation failures retain caches for retry after resolving the problem. A successful build does not replace regular Codex, start a session, or read regular configuration.

## Release-tag lockfile correction

This upstream tag declares workspace version `0.169.0`, but 173 local packages in Cargo.lock still say `0.0.0`, making an unchanged `--locked` build fail. `scripts/prepare-lock.py` synchronizes only those local versions and verifies the full SHA-256 before and after. Third-party versions, sources, checksums, and dependency relationships remain unchanged. Compilation still uses `--locked`; this correction changes build metadata, not Rust behavior.

## Build boundaries

The build reuses upstream `scripts/build_codex_package.py` for the main client, `codex-code-mode-host`, `codex-exec-server`, and Linux `bwrap`, and downloads/verifies V8 and ripgrep against upstream manifests. The package includes `codex-package.json`, `bin/`, `codex-path/`, and `codex-resources/`.

“On-device build” means Codex and its own helpers compile on the phone. Third-party V8 and ripgrep use the prebuilt dependencies selected by upstream. Voice distribution packages and Android APKs are outside this build.

Upstream and dependency licenses still apply. This repository also uses Apache-2.0; third-party components retain their own licenses.

## Validation record

2026-11-16: baseline compilation and integrated checks passed. The package is at `~/codex-touch-build/packages/baseline-0.169.0` on the development device.

Check its version without loading regular configuration:

```sh
"$HOME/codex-touch-build/packages/baseline-0.169.0/bin/codex" --version
```

Run integrated checks:

```sh
bash scripts/check.sh --baseline-package "$HOME/codex-touch-build/packages/baseline-0.169.0"
```

Passed: package layout/version, helper startup, app-server initialization, a local fake model driving V8 code execution and shell/ripgrep tools, and the default-daemon TUI rendering a complete tool turn in an isolated PTY before normal exit. Tests use temporary HOME/CODEX_HOME, stop their daemon, and clean temporary files. Automatic title generation adds a model request, so assertions use actual tool results and replies rather than request count alone.

This baseline run did not modify touch behavior or validate Android keyboard/taps, the entire upstream test suite, or Linux sandbox capabilities.

### Measured resources

The initial attempt through successful packaging took about **42.5 minutes**, including downloads, lockfile debugging, an interruption, and cooling. The final build took about **25.8 minutes**, including **5.4 minutes** paused for cooling. The final sampled sum of process-group RSS peaked around **3.19 GiB**, sampled every 10 seconds. Shared pages may be counted more than once; this is not exact private memory usage.

| Component | Allocated space |
| --- | ---: |
| Upstream source and shallow clone | 151.5 MiB |
| Cargo build and incremental cache | 12,611.3 MiB |
| Cargo Git dependencies | 3,862.0 MiB |
| Cargo registry | 1,241.8 MiB |
| Upstream V8/ripgrep downloads | 34.6 MiB |
| Complete baseline package | 598.6 MiB |
| Total | About 18.1 GiB |

This excludes the previously installed toolchain (about 1.1 GiB) and approximately 52 MiB of newly installed Git dependencies. Caches were retained for touch development.

Two upstream bubblewrap C warnings concerned uninitialized `sockaddr_nl` fields and did not fail the build; baseline source was preserved. Commands, resource samples, and binary hashes are recorded locally in `~/codex-touch-build/baseline-build-record.json` and `logs/`.
