[English](shortcut-touch.md) | [简体中文](shortcut-touch.zh-CN.md)

# Tappable shortcut hints

These controls use the same pinned Codex 0.169.0 revision, `CODEX_TOUCH=1`, and the default full-screen terminal. They ship in codex-touch 0.2.0.

## Usage

Follow the [phone build guide](build.md), then run inside the cloned project in Debian chroot:

```sh
bash scripts/run-touch.sh
```

The launcher selects `~/codex-touch-build/packages/touch-agents-0.169.0`. The development device retains earlier shortcut and phase-one packages. If you have the preceding shortcut package, select it temporarily with:

```sh
CODEX_TOUCH_PACKAGE="$HOME/codex-touch-build/packages/touch-shortcuts-0.169.0" bash scripts/run-touch.sh
```

The launcher leaves HOME/CODEX_HOME unchanged and normally shares regular configuration and sessions. Rebuild with `bash scripts/build-touch.sh`; use `CODEX_TOUCH_PACKAGE` for a new Linux output directory because existing packages are never overwritten.

## Coverage

| Surface | Supported behavior |
| --- | --- |
| Main composer footer | Tap the binding or description to open help, enter agents, or queue; tap the idle mode hint to change mode |
| Composer with a draft | Keep help and `new line` available; insert a newline at the cursor without submitting |
| `?` shortcut help | Commands, Mention files, Shell command, New line, Paste image, External editor, Search history, send/queue, Change mode, reasoning effort, Voice, Agents, Inspect activity, Interrupt/Quit, Open transcript, Find text |
| Help footer `close` | Close help and preserve the draft |
| Agent command center | Tap a task to select, then tap the selected task to open; tap status tabs, grouping, footer hints, and help actions; wheel events move selection |
| Working `esc to interrupt` | Tap the complete binding or `to interrupt` text to use the configured upstream interruption flow |
| Asynchronous question footer | Retain phase-one single-key submit, skip, main prompt, previous/next hints, including Shift combinations |

Command center targets use stable thread IDs. A background refresh cannot redirect an old tap to another task. Task-row and filter clicks are disabled during rename to avoid renaming the wrong task. Narrow tab-strip arrows reach hidden filters. In combined direction hints, each key is independently tappable and the description belongs to the last direction. Delete/archive keep upstream confirmation flows.

In full-screen mode, Open transcript expands current transcript details while retaining the composer; Find text opens transcript search.

Coverage applies only when hints are visible and their bindings are enabled. Upstream constraints for state, permissions, external editors, and clipboard availability still apply. The physical `?` key keeps its original meaning; tapping help can open it with a draft.

Double-Esc, combined Subagents/Scroll/Top-latest references, transcript-only selection hints, and `/keymap customize` remain reference text. Floating leader/preset menus, unrelated dialogs, and transcript-owned hints are not adapted. Synchronous question dialogs, a new newline affordance inside the asynchronous answer editor, and automatic Android keyboard display remain future work.

## Hit testing and dispatch

- Use semantics and actual painted regions. Help retains upstream one-/two-/three-column layouts and word wrapping, mapping source ranges to hit regions. Height-clipped entries are not registered.
- Press and release must hit the same entry with unchanged layout/action. Dragging, leaving the target, wheel input, modifiers, other input, resizing, and focus loss cancel activation. A cancelled gesture remains captured through release to avoid falling through.
- Hint taps run before static text selection. Dragging from a hint does not select text or execute the action. Other areas retain upstream behavior.
- The composer handles help open/close locally. Other actions return through application key routing, emitting press/release and supporting runtime two-key bindings. Shift+Tab generates terminal-style BackTab.
- Executing a help action dismisses help directly and uses the original action path. It neither inserts key-label text nor simulates Escape to close help, which could backtrack the session.

## Validation

```sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-agents-0.169.0"
```

Rust checks retain phase-one coverage and add gestures, help columns/wrapping/clipping, draft newline/help-close behavior, and hidden/unfocused owners. Integration checks use temporary HOME/CODEX_HOME, a local fake model, and a synthetic PTY to verify actual SGR mouse routing through the program and resulting model requests.

The preceding shortcut build on 2026-11-17 passed **376 distinct Rust tests**, including 10 new hint tests. Filter counts were questions 75, selection_popup_common 10, request_user_input 90, shortcut 117, footer 91, and live_center 12. Filters overlap; the full upstream suite was not run.

Actual-program PTY checks passed question answers and Shift previous/next navigation; mode-drag cancellation; newline at 42 columns; help open/close with a draft; mode changes in both directions; custom Shift+Up reasoning; help Shift+Enter newline; a custom two-key transcript search; exact three-line delivery with high reasoning effort; and terminal/mouse-reporting restoration on exit.

Application tests use upstream CI's `RUST_MIN_STACK=8388608`. One old snapshot still contained `v0.0.0`; its only two differences were version labels, updated to pinned `v0.169.0`. Initial isolated daemon installation took about 40–50 seconds, so startup waits allow 120 seconds while ordinary actions allow 30. Tests drain queued answers before idle interactions and wait for a hint's position to stabilize for 250 milliseconds, without retrying failed taps.

That shortcut package was about 599 MiB and initially took 145.6 seconds to build. Repackaging after the snapshot correction took 6.2 seconds with identical hashes for five binaries. The record is `~/codex-touch-build/shortcut-build-record.json`. Test compilation's sampled process-group RSS peaked around 7.07 GiB with one Cargo job and no thermal pause.

The user later reported that most touch tests passed, identifying the command center and interrupt hint as gaps. This was a general report, not acceptance of every individual shortcut. After those fixes, the user explicitly confirmed both areas passed on-device testing. This does not establish every sub-action or keyboard behavior; PTY evidence remains separate.

Suggested checks for other devices: tap mode; type two Chinese lines using `new line`; open help with a draft and use New line/Change mode/close; navigate multiple questions; then repeat after narrowing or folding the screen. Confirm that dragging a hint does not activate it.

## Command center and interrupt completion

On 2026-11-17, independent view routing was added so only the top component accepts taps. Opening another view cancels underlying gestures. The status component owns complete interrupt regions; hiding, clipping, binding changes, and layout changes invalidate old taps. Shared gesture/help layout code is reused without new dependencies.

Reproduction steps: open agents, select and reopen a task; tap Working/Ready tabs and narrow-screen arrows; open `? help`, execute Search/Rename/Group, and use back to leave help and then the center. During an interruptible task, drag `esc to interrupt` to confirm it continues, then tap the text to stop it.

The final regression run passed **409 distinct Rust tests**, including 7 new tests. Filter counts: questions 75, selection_popup_common 10, request_user_input 90, shortcut 121, footer 91, live_center 16, status_indicator 29. Counts overlap. Existing status-effect snapshots stayed unchanged; the full upstream suite was not run.

Unified checks also passed package/helpers, V8/shell/ripgrep tool execution, the default-daemon TUI, and extended touch PTY. New PTY steps verified center filtering, help, a runtime two-key Search binding, layered back behavior, open, and “drag continues; tap interrupts” while a fake model turn remained held. Exit restored terminal state. All data used temporary HOME/CODEX_HOME and loopback services.

The phone's incremental package build took 88.9 seconds, including 2.1 seconds waiting for initial cooling. Final Rust validation took 76.4 seconds; unified package checks took 86.8 seconds, including 18.7 seconds waiting for initial cooling. These are not fresh-build timings. The new package is about 598.8 MiB; source, dependencies, caches, and four packages total about 32.57 GiB. Peak sampled test-compilation process-group RSS was about 6.97 GiB. Records are in `~/codex-touch-build/agents-build-record.json`; older packages remain available. The user confirmed these two touch areas in real Termux after automated validation.
