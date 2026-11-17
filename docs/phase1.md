[English](phase1.md) | [简体中文](phase1.zh-CN.md)

# Phase one: asynchronous question touch controls

This document preserves phase-one behavior and validation history. See [shortcut controls](shortcut-touch.md) for the current default package and subsequent features. The old package below contains only phase-one functionality.

Development targets the Codex 0.169.0 revision in `upstream.json` and the default full-screen TUI. Inline `--no-alt-screen` mode is outside this phase. The patch is `src/async-question-touch.patch`, enabled by `CODEX_TOUCH=1`. During this phase the project version still identified the 0.1.0 scaffold; these features are now included in release 0.2.0.

## Behavior and boundaries

- Tap the collapsed question summary to expand it while keeping terminal mouse reporting enabled.
- Tap a fully visible named option to submit through upstream sending or queueing. Remove the question only after acceptance.
- Tap Other to enter the existing freeform editor. Tap existing text to place the cursor; keyboard input and paste continue to work.
- Tap fully visible submit, skip, and previous/next hints using the current single-key binding, including modifier combinations. Custom two-key bindings in asynchronous question hints still require keyboard input.
- Use wheel events to browse options without submitting. Dragging, resizing, focus loss, keyboard input, modal coverage, and question changes cancel an unfinished tap.
- Submit only fully visible answer targets, retaining upstream visibility and sending constraints.

Only asynchronous questions were adapted in this phase. Synchronous question dialogs and automatic Android keyboard display are outside the implementation. Open the keyboard manually. Codex handles mouse events in the expanded question region, which may change terminal link/selection behavior there.

## On-device build and launch

Inside Debian chroot, using its Linux compiler:

```sh
# Enter the cloned project directory in Debian.
bash scripts/build-touch.sh
bash scripts/run-touch.sh
```

The build verifies the upstream revision, normalizes the known lockfile metadata, then applies and checks the exact patch. Unknown edits stop it; the baseline package is preserved. It uses one job, dev-small, LLD, and the shared `~/codex-touch-build/target` cache. The historical phase-one output is `~/codex-touch-build/packages/touch-0.169.0`; current scripts build `touch-agents-0.169.0`, including later features, upstream helpers, and `touch-build.json`.

`CODEX_TOUCH_BUILD_DIR` selects another Linux build root; `CODEX_TOUCH_PACKAGE` selects a new output directory. Existing packages are not overwritten. `run-touch.sh` enables touch only for the launched process and does not change the regular launcher, configuration, or global environment. Run the same package's `bin/codex` without `CODEX_TOUCH=1` to compare upstream mouse behavior.

A separate package does not isolate sessions. The launcher leaves HOME/CODEX_HOME unchanged; the same Linux user normally shares `$HOME/.codex`. Automated tests explicitly use temporary HOME/CODEX_HOME.

Long builds need controlled concurrency/temperature and an active Termux session. Repository scripts use one Cargo job and reduced priority. For the recorded run, a device-local monitor sampled battery temperature every two seconds, paused the process group at 44°C, and resumed at 42.5°C. The earlier 41.5°C resume threshold caused long waits while charging. A `taskset` experiment was removed: Android reset CPU affinity, and CPU 0 was sometimes outside the permitted set, causing startup failure. A successful affinity assignment was not a lasting limit. Baseline timings do not describe test-build cost.

## Automated validation

These commands use the current cumulative patch. The expanded PTY now tests later features too, so an old phase-one package will not pass the entire current check:

```sh
bash scripts/check.sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-agents-0.169.0"
```

- Basic: patch syntax, Python/Shell, repository conventions, lockfile tests, and the IME probe.
- Rust: upstream question/shared-list/dialog regressions plus painted coordinates, Chinese wrapping, clipping, drag/stale/repeated release behavior, Other/freeform editing, narrow layouts, and mouse capture.
- Package: the full tool round trip plus isolated HOME/CODEX_HOME, a local HTTP fake model, and actual SGR mouse sequences in a PTY. Checks cover expansion, capture, resizing, choices, editing, submission, delivery, and restoration.

The PTY decoder serves synthetic tests only; it cannot prove Android touch or keyboard display. The unmodified package failed at “Summary did not expand”, confirming coverage of the original defect.

## On-device acceptance: 2026-11-17

The user tested in Termux, reported high usability, and authorized review of the test session. It contained 16 distinct structured question replies and feedback such as skipping. Some replies reported problems, so they are not 16 passing cases. Only conclusions are retained here, without original sessions, prompts, or identifiers.

| Area | Result and evidence |
| --- | --- |
| Opening questions and named answers | Worked on-device; answers were delivered |
| Wrapped long choices and an eighth option | Intended answers were delivered without reported wrong selection |
| Chinese freeform text, cursor editing, Other | Freeform and mid-text edits were delivered |
| Accidental submission while scrolling | The user clarified that the reported second answer was an intentional tap |
| Skip | Explicitly confirmed through the footer hint |
| Collapse/reopen and draft retention | The user confirmed retained drafts |
| Return from Other to a preset answer | The user confirmed returning and submitting the preset |
| Manual newline | Failed at this stage: no convenient modifier-key input; Enter submitted |
| Question navigation | Not completed: Shift hints were interpreted as requiring a physical modifier |
| Multiple simultaneous questions | A stall was reported without a confirmed cause; one-at-a-time testing succeeded |
| Synchronous questions | The interface was not reached because Default mode rejected the tool call |

The session also reported that unanswered questions became unusable when the turn finished. Source inspection showed that upstream recovers unsent text and clears pending questions at turn completion. This is the existing lifecycle, not evidence of a touch defect. Keep a turn running until interaction tests finish. Test questions individually, and investigate the multi-question report separately.

Navigation discoverability needs work. Fully visible `prev question` and `next question` single-key hints already had touch targets, including Shift combinations; tapping does not require physically pressing Shift. That does not prove on-device navigation acceptance in this phase. Distinguish clipping from an undiscovered control. Later work added composer newline/help controls; the answer editor's newline convenience and the multi-question report remain follow-up items.

This phase did not establish actual fold/unfold, focus recovery, or normal/abnormal terminal restoration on the phone. Automated resize/cleanup evidence is separate. Automatic keyboard display remains unimplemented.

## Build and regression record

Phase-one Rust filters passed: 75 question tests, 10 shared-list tests, and 90 dialog-related tests, with **168 distinct tests**, including 12 new touch tests. The full upstream suite was not run. Package and touch PTY checks passed version/helpers, app-server initialization, V8→shell/ripgrep→reply, the default-daemon TUI tool turn, summary expansion, capture, narrow resizing, drag cancellation, named options, Other/freeform input, footer submission, complete answer delivery, and normal terminal restoration. Tests locate actual painted text in screen cells and wait for all queued answers before declaring success.

Measurements from 2026-11-17:

| Item | Result |
| --- | --- |
| Phase-one package | `~/codex-touch-build/packages/touch-0.169.0`, about 599 MiB |
| Final incremental package build | About 71 seconds for Cargo; 74 seconds including packaging/checks |
| Final incremental Rust build and three filters | About 115 seconds |
| Peak sampled process-group RSS | About 5.41 GiB during TUI test compilation, with substantial swap use |
| Source, Cargo caches, target, downloads, two packages | About 30.86 GiB, 12.79 GiB above the baseline stage |

The first addition of TUI test dependencies, cooling, and debugging took about an hour; this does not predict ordinary incremental work. Local logs, samples, and hashes remain in `~/codex-touch-build/logs/` and `phase1-build-record.json`. All five baseline binary hashes stayed unchanged. The regular launcher was preserved, and the task's wake lock was released.
