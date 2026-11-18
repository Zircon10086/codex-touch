[English](picker-touch.md) | [简体中文](picker-touch.zh-CN.md)

# Picker and dialog touch development

This is unreleased work after v0.2.0, pinned to Codex 0.169.0. The separate package is `~/codex-touch-build/packages/touch-pickers-0.169.0`. Existing installed clients and the published release are not changed.

## Coverage inventory

| Surface | Adaptation |
| --- | --- |
| Resume and fork | Tap a session to select it; tap the selected row to open it. Backend/thread identity prevents stale row activation. Toolbar filters, active/archived status, sorting, density, preview, expansion, cancel, and visible list navigation use existing actions. |
| Shared list dialogs | Painted rows, wrapped entries, tabs and overflow navigation, footer hints, expanded descriptions, and scrolling. Disabled entries stay disabled. Selection then acceptance preserves each owner's behavior. This includes models, configuration, approvals, verification, keymap selection, and similar shared menus. |
| Settings and multi-select | Skills, experimental features, memory settings, status/title fields, app links, and hooks. Section headings are excluded from selectable rows. |
| Synchronous questions and MCP forms | Options, confirmation choices, notes/text areas, and action hints. Existing answer submission, validation, auto-resolution, queueing, and permissions remain authoritative. |
| Text/provider/keymap editing | Custom prompts and feedback text areas; provider fields and Save; key capture cancel and key debugger close. Captured keys continue to use the original recording logic. |
| Completion popups | Commands, files, skills, and mention tabs/rows. Touch invokes completion (Tab) and does not directly submit a command. |
| Floating guides | Pending chord completions, workspace actions, and preset hints. The pending chord prefix is preserved. |
| Transcript and static pager | Visible navigation, search, selection/copy, close and other owner-authored hints; original transcript mouse selection remains available. Search query text is not an action. |
| Warnings and analytics | Footer actions, with original warning policy and analytics controls. |
| Startup choices | Working directory, updates, model migration, unarchive, external configuration migration, hook review, recovery and draft entry. |
| Initial setup | Login-mode and directory-trust rows; a touch navigation bar for continue, back, up/down, next field, quit and available copy actions. Trust still requires explicit confirmation. Cloud/gateway forms use the navigation bar to move between fields. |
| Additional shortcut hints | `/keymap customize`, double-Escape edit, combined subagent shortcuts, and side-chat confirmation footer. Reference-only transcript entries in the main help require opening the transcript; its active footer provides the controls. |

A tap means left-button press and release without dragging. Gesture cancellation covers resizing, changed targets, keyboard input, focus loss, and view replacement where the owner handles those transitions. Target geometry comes from rendering; no terminal buffer or model output is parsed into actions. Full-screen mode and `CODEX_TOUCH=1` are required.

## Validation

2026-11-18: 1,297 distinct Rust regressions passed across 43 registered filters on the development phone. The test executable took 157.08 seconds after compilation. Package layout/helpers, app-server initialization, a loopback model/tool round trip, the default-daemon TUI, and the extended touch PTY all passed. The final touch PTY completed in 49.8 seconds, including direct startup resume and terminal restoration. Debian and host Termux basic checks passed. The unified entry point is:

```sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-pickers-0.169.0"
```

Rust regressions include existing keyboard/layout snapshots and touch checks for row identity, drag/resize cancellation, clipping, disabled entries, custom chords, forms and trust confirmation. The runner verifies that every registered filter selects tests and runs their union once, with the inherited touch opt-in removed.

The extended PTY uses a temporary HOME/CODEX_HOME and loopback fake model. It exercises actual command completion, `/resume`, filtering, preview/close, session opening, a shared model dialog, shortcut customization with draft retention, floating chord completion and CLI startup resume, in addition to the prior question, shortcut, command center and interruption checks. It checks mouse-mode and terminal restoration. No real sessions, credentials or remote models are used.

The final Rust-check-and-package run took 391.8 seconds with one build job and reduced priority; sampled process-tree RSS peaked at about 6.21 GiB and battery temperature at 33.5°C, with no cooling pause. The complete development package occupies about 598.5 MiB. These are observations from this phone, not performance guarantees.

## Phone acceptance

Run inside the same Debian environment as the regular client:

```sh
bash /storage/emulated/0/Agent/codex-touch/scripts/run-touch.sh resume
```

1. Select an unselected session, then tap it again to resume. Drag across a row and confirm it does not open. Repeat in `/fork`.
2. Tap visible filter/sort/status controls and footer hints, including transcript preview and cancel. Fold/unfold or resize, then tap again.
3. Try `/model`, a settings multi-select and a confirmation dialog. Confirm each step explicitly; check disabled rows do nothing.
4. Complete a slash command or file mention by touch, then submit separately. Open shortcut help and tap customization; verify a draft is retained.
5. Try floating chord hints, transcript navigation/search, synchronous questions and MCP forms when available. Verify typing still works and taps do not leak through a modal.

Automated checks cannot establish every phone interaction or external provider flow. Phone acceptance of this development package is pending. Android keyboard auto-display, `--no-alt-screen`, and the previously reported asynchronous multi-question stall/answer-editor newline follow-up are outside this change.

History search also adapts the visible accept/cancel suffix while excluding the editable query. Two update-dialog snapshots use the pinned 0.169.0 package version instead of upstream’s 0.0.0 placeholder. A cloud-resume test filters actual response rows so random startup tips mentioning “response” do not contaminate its assertion.
