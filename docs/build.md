[English](build.md) | [简体中文](build.zh-CN.md)

# Phone build guide

## Supported environment

Verified: an ARM64 Android phone, a Termux terminal, Debian chroot, and a GNU/glibc toolchain. The pinned target is `aarch64-unknown-linux-gnu`. Compile and run inside Debian, with input/output connected directly to Termux's PTY.

This repository does not install or manage chroot. Prepare a working Debian environment first. Device-specific launchers, a root command bridge, and the Android SDK are not required. Native Termux's Bionic compiler cannot directly replace the glibc compiler used here. Other Linux userspaces may work, but proot and other CPU architectures are unverified.

Keep the clone, upstream sources, Cargo caches, and executable packages on the Debian Linux filesystem, such as `$HOME`. Do not put build output on `/sdcard` or Android shared storage. If the project repository itself is on shared storage, invoke scripts through `bash`.

## Dependencies

Python 3.11+ is required for standard-library `tomllib`; Debian 12 or newer is recommended. Install these packages with Debian package-management privileges. The following are administrator commands; use a configured `sudo` or an administrator shell if needed:

```sh
apt-get update
apt-get install -y build-essential cmake pkg-config libssl-dev libcap-dev lld git python3 curl ca-certificates
```

Install rustup for the ordinary build user using the [official instructions](https://rustup.rs/). If rustup is already available, install the pinned toolchain:

```sh
rustup toolchain install 1.95.0 --profile minimal --component rustfmt --component clippy --component rust-src
rustup run 1.95.0 rustc --version
cc -dumpmachine
```

`cc -dumpmachine` should print `aarch64-linux-gnu`. The build scripts select Rust 1.95.0 themselves; changing the global default toolchain is unnecessary.

## First build

Clone the repository from the URL in the README, enter its directory, and run:

```sh
bash scripts/check.sh
bash scripts/build-touch.sh
bash scripts/run-touch.sh
```

`build-touch.sh` obtains the Codex revision in `upstream.json`, checks the known lockfile normalization, applies the cumulative patch, and uses upstream packaging. Unknown source edits stop the build. Existing output packages are never overwritten. You do not need to run `build-baseline.sh` first; it exists for comparison with the unmodified client.

Default directories:

```text
~/codex-touch-build/
  upstream/                     Pinned upstream source with the patch
  target/                       Rust incremental cache
  downloads/                    Upstream packaging dependencies
  logs/                         Build logs
  packages/touch-pickers-0.169.0/ Complete adapted package
```

Builds use one Cargo job, the `dev-small` profile, LLD, and `--locked`. Codex's own helpers compile locally; third-party V8 and ripgrep artifacts are downloaded and verified according to upstream packaging. The build does not start a Codex session or read your regular API configuration.

Initial downloads and compilation take time. On the development phone, the first baseline attempt through successful packaging took about 42.5 minutes, including download, debugging, and cooling. Incremental builds are much faster. See the [baseline measurements](baseline-build.md) and [current feature record](shortcut-touch.md); these observations are not minimum requirements.

Keep Termux running and watch temperature, memory, and free space. If needed, run `termux-wake-lock` in host Termux, then `termux-wake-unlock` when finished. Repository scripts provide one-job and low-priority controls only. The automatic thermal monitor mentioned in development records is a device-local tool and is not distributed with this project.

## Launch and isolation

`run-touch.sh` sets `CODEX_TOUCH=1` and runs the package's Codex, forwarding arguments:

```sh
bash scripts/run-touch.sh --version
bash scripts/run-touch.sh
```

Normal launches use the current user's Codex configuration and sessions. To configure and test separately, explicitly select another directory and complete normal setup there:

```sh
CODEX_HOME="$HOME/.codex-touch-test" bash scripts/run-touch.sh
```

Automated package tests use temporary HOME/CODEX_HOME and local fake services. They need no real API key. Open the keyboard manually using Termux's keyboard control.

## Rebuild, choose a package, and roll back

Existing output is preserved. Build into a new directory, then select that directory when launching:

```sh
CODEX_TOUCH_PACKAGE="$HOME/codex-touch-build/packages/touch-local" bash scripts/build-touch.sh
CODEX_TOUCH_PACKAGE="$HOME/codex-touch-build/packages/touch-local" bash scripts/run-touch.sh
```

To return to a retained older package, point `CODEX_TOUCH_PACKAGE` to it. `CODEX_TOUCH_BUILD_DIR` changes the entire Linux build root. `CODEX_TOUCH_JOBS` changes compilation concurrency; retain the default of 1 on a phone unless you have measured the impact.

## Validation

```sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-pickers-0.169.0"
```

Both are longer-running checks. The first Rust test build adds compilation caches; package checks start temporary local services and pseudoterminals. Android touch, keyboard behavior, and other Termux versions still need device testing.

## Development-device example

`crsh`, `crcodex`, and `termux-run` in historical records belong to the development device's existing environment. Other users do not need them. On that device, enter `crsh` from Termux, then run:

```sh
bash /storage/emulated/0/Agent/codex-touch/scripts/run-touch.sh
```

Elsewhere, enter your own Debian shell and run the script from the cloned repository.
