[English](design.md) | [简体中文](design.zh-CN.md)

# Design

## Goal and current scope

Make Codex usable by touch in Termux: open questions, choose answers, and eventually show the Android keyboard when an editable area is tapped, while preserving keyboard and scroll behavior.

Version 0.1.0 established the scaffold. The [initial investigation](termux-touch.md) describes the input path. Phase one added opt-in asynchronous question controls against a pinned upstream version; see its [implementation and acceptance record](phase1.md). Version 0.2.0 includes those controls and the later shortcut, command center, and interrupt work. Automatic keyboard display remains unimplemented.

## Implementation decisions

1. Implement controls in the Codex Rust TUI, dispatching against rendered areas. Start with asynchronous questions; adapt synchronous question dialogs separately. Reuse the mouse protocol.
2. Investigate the keyboard independently. Compare stock Termux tap behavior before deciding whether Termux needs a session-level display request.
3. Validate actual touch, window changes, and terminal restoration separately. A synthetic PTY proves only the portion it exercises.

The development device's `termux-run` bridge executes noninteractive commands and has no PTY. Running a command through it is not an interactive-terminal test.

## Acceptance requirements

- Describe gestures and expected results as reproducible steps.
- Record keyboard, terminal-resize, normal-exit, and interruption checks.
- Restore terminal modes after normal or abnormal exit if a component changes them.
- Cover normal, boundary, and invalid inputs with synthetic events when converting input.
- Keep automated checks separate from phone interaction acceptance, and identify unperformed checks.

Question and keyboard comparison procedures are maintained in the [investigation](termux-touch.md).

## Shortcut hints and view ownership

- Preserve runtime bindings and semantics when constructing hints. Column layout, wrapping, and rendering produce hit regions together; do not parse displayed labels back into keys.
- The main composer and `?` help capture short taps independently. Only fully visible entries activate. Clipping, layout changes, dragging, keyboard input, and focus loss cancel the gesture. Modals, background panes, and interactive transcripts do not receive underlying hint taps; the command center owns its own targets as the active view.
- Opening and closing help are local composer actions that preserve the draft. Other actions return through the full application key route, including runtime single-key and two-key bindings and existing permission/state constraints.
- With touch enabled, retain help and newline hints with a draft, and expose a mode hint while idle. Use existing narrow-screen layout priorities without adding a UI framework or dependency.
- The command center collects targets from painted task rows, status tabs, and semantic help layout. Task ID and selection state participate in gesture validation. A refresh with the same layout preserves a tap; reordering or coverage cancels it. The bottom-pane interface adds default no-op touch methods, so unrelated modals cannot receive underlying clicks.
- The working-status component registers the fully rendered interrupt hint. Coordinate changes caused by the timer cancel old gestures. Interruption, opening tasks, and help actions use the original runtime key route and retain confirmation/state rules.

See [shortcut controls](shortcut-touch.md) for coverage and verification.
