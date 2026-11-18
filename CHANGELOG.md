[English](CHANGELOG.md) | [简体中文](CHANGELOG.zh-CN.md)

# Changelog

## [Unreleased]

- Add resume/fork picker touch: stable session selection, opening, toolbar filters/sorting, footer actions, and wheel navigation.
- Extend touch to shared lists, settings, approvals, synchronous questions, MCP forms, provider editing, startup prompts, and initial setup controls while preserving validation and confirmation.
- Add history-search accept/cancel hints and completion-row taps, floating chord/preset guide actions, transcript/pager hints, warning/analytics hints, shortcut customization, and combined subagent navigation.
- Keep drag, clipping, resize, stale-state, focus, and disabled-touch checks. Use an independent `touch-pickers-0.169.0` package; do not replace installed v0.2.0 clients.
- Pass 1,297 distinct Rust regressions and isolated actual-package checks, including extended resume/completion/dialog PTY coverage. See [development coverage](docs/picker-touch.md).

## [0.2.0] - 2026-11-17

- Publish the first functional release as source with SHA-256 checksums. Build the client against the pinned upstream version; no prebuilt binary is included.
- Make English the default for documentation, README, project conventions, and release notes. Retain Chinese translations and add reciprocal language links to every document.
- License current project code, scripts, and documentation under Apache-2.0, matching pinned upstream Codex. Add root NOTICE while retaining upstream, third-party, and historical MIT notices.
- Provide a public README, a general Debian ARM64 phone build guide, contribution instructions, and GitHub Actions for basic repository checks.
- Add agent command center touch controls for task selection/opening, status filters, grouping, footer hints, and help actions. Use stable task IDs across refreshes and route gestures to the active view.
- Make the fully visible `esc to interrupt` hint tappable through the configured interrupt binding and original application flow. Dragging, clipping, hiding, and layout changes cancel activation.
- Default to the `touch-agents-0.169.0` build package while retaining earlier packages. Pass 409 distinct Rust regressions and actual-program PTY validation, including command center controls and interruption of a held model turn.
- Record on-device confirmation of the command center and interrupt fixes after the earlier report that most touch tests passed.
- Make main-composer hints and individual `?` help actions tappable, including mode, newline, reasoning effort, sending/queueing, and transcript actions. Respect runtime single-key and two-key bindings.
- Keep help and newline available with a draft. Use actual columns and wrapping to register fully visible entries; cancel taps on drag, layout/focus changes, or other input. The preceding shortcut package passed 376 distinct Rust regressions and multiline-delivery PTY checks.
- Add opt-in asynchronous question touch controls: expand the summary, choose named answers, edit Other/freeform text, tap footer actions, and scroll choices.
- Require fully visible answer targets. Cancel old gestures on drag, question changes, resizing, focus changes, or modal coverage, while retaining upstream sending and queueing behavior.
- Add independent build/launch tools and exact patch verification. Phase one passed 168 distinct Rust regressions and SGR mouse integration checks; synchronous questions and automatic Android keyboard display remain future work.
- Record on-device answer, editing, skip, and draft acceptance. Track newline/navigation follow-up and a reported multi-question stall. Explain that the adapted client shares regular sessions by default.
- Pin Codex 0.169.0 and provide Debian ARM64 baseline builds using upstream packaging and locked Cargo dependencies.
- Normalize the release tag's local-package lockfile versions deterministically without changing third-party dependency versions or checksums.
- Validate the baseline on a phone, record resource measurements, and add optional package, loopback tool-call, and default-daemon TUI checks.
- Document the original Codex question/composer behavior, Google Play Termux keyboard routing, and adaptation options. Add an independent keyboard probe and synthetic PTY checks.

## [0.1.0] - 2026-11-16

- Initialize the independent Git repository and development scaffold.
- Add the MIT license, editor configuration, and Git ignore rules.
- Add basic checks, design notes, and a development guide.
- Establish `VERSION`, the changelog, and the `vX.Y.Z` tag convention.

This historical version contains only the scaffold, with no functional touch adaptation.
