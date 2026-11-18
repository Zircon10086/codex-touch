[English](README.md) | [简体中文](README.zh-CN.md)

# Tests

Add tests for observable behavior and register them with `scripts/check.sh`. Prefer synthetic inputs for event conversion, boundaries, and cleanup; avoid private session data.

`probe_pty.py` runs the diagnostic script in an isolated pseudoterminal. It checks hit/miss behavior, temporary mouse-reporting disable/restore, normal exit, signal exit, and terminal restoration. It is part of basic checks. It is not a Codex integration test; [keyboard validation](../docs/termux-touch.md) still requires a real Termux session.

`test_prepare_lock.py` verifies that lockfile normalization changes only local package versions, rejects unknown inputs or unexpected output hashes, and supports read-only and repeated checks.

`baseline_smoke.py` checks the built package's version and helpers, app-server initialization, and a loopback model-driven code-execution round trip. It also exercises the default-daemon TUI in a synthetic PTY and stops the test daemon. It uses temporary HOME/CODEX_HOME and sends only synthetic data to a local service:

```sh
bash scripts/check.sh --baseline-package "$HOME/codex-touch-build/packages/baseline-0.169.0"
```

Without `--baseline-package`, basic checks do not launch a built Codex package.

`touch_pty.py` drives the adapted client's asynchronous questions using SGR mouse events, terminal resizing, a local model fixture, and isolated state. It verifies answer delivery and terminal restoration. Run it with `bash scripts/check.sh --touch-package PATH`, which also runs the package regressions. The original baseline fails at summary expansion.

Rust touch tests live in `src/async-question-touch.patch`; after application they appear in upstream modules such as `async_questions/mouse_tests.rs` and question integration tests. `bash scripts/check.sh --rust-tests` compiles and runs selected question, shared-list, and synchronous-dialog regressions. The first run compiles additional test dependencies. Use `--upstream-source PATH` to verify the exact source. See [phase one](../docs/phase1.md).

`test_prepare_touch.py` uses temporary synthetic Git repositories to check patch application, repeat execution, read-only verification, preservation of the real index, and rejection of wrong versions, local modifications, pre-existing new files, and unknown files.

Hint coverage in the cumulative patch is registered through `shortcut`, `footer`, and `live_center` in `scripts/test-touch.sh`. The extended PTY uses custom Shift+Enter, Shift+Up, and two-key transcript-search bindings. It covers question navigation, draft newline, help open/close, mode changes, reasoning effort, and exact multiline message delivery. The old phase-one package does not support these later tests.

Command center and interrupt coverage adds `status_indicator`. `live_center` includes actual App modal routing, selection/opening, filters, help actions, and refresh/drag/resize cancellation. The PTY also checks filters, help, a two-key Search binding, back/open behavior, and interrupting a held local-model turn. Current package validation requires `touch-agents` or a newer build.

`scripts/check-docs.py` validates English/Chinese document pairs, language-switch links, local Markdown links, and the current version in both READMEs and changelogs. It is included in the basic check entry point.

Development picker/dialog coverage is registered as one deduplicated Rust run. The runner unsets `CODEX_TOUCH` for default-off regressions and rejects filters that select no tests. Package checks now use `touch_pty.py --extended` for command completion, resume toolbar/preview/cancel/open, a generic model dialog, and direct CLI resume. Use a new `touch-pickers` build; to repeat only the historical v0.2.0 PTY, run the Python test directly without `--extended`. See [coverage](../docs/picker-touch.md).
