[English](termux-touch.md) | [简体中文](termux-touch.zh-CN.md)

# Initial investigation: question taps and the Android keyboard

Investigation date: 2026-11-16. Findings apply to the versions inspected here. **Codex decides which answer a tap selects; Termux's Android window displays the keyboard.** These can be delivered separately, and question selection does not require a Termux modification.

## Actual input path

The installed `codex --version` was `0.169.0`. A non-root Android package-manager query reported `com.termux` version code **142**. The [Google Play build definition][play-version] corresponds to `googleplay.2026.10.09`; the older June inventory listed 141. References below pin relevant commits and do not assume identical F-Droid or other-terminal behavior.

1. On finger release, [Termux TerminalView][view] emits a left-button press followed by release if mouse reporting is enabled and the interaction is neither a scroll nor text selection. Font metrics convert pixels to cells; finger scrolling uses wheel events. Both mouse reports come from the same finger release, so their timing does not reveal how long the finger was held down.
2. In SGR mode, [TerminalEmulator.sendMouseEvent][emulator] writes a tap at column 8, row 30 as `ESC[<0;8;30M` followed by `ESC[<0;8;30m`. Protocol coordinates are one-based; crossterm supplies zero-based TUI coordinates. **The TUI cannot distinguish a finger tap from a left mouse click by these events.**
3. Codex running inside Debian inherits Termux's PTY; the development device uses its own `crcodex` launcher. Codex [terminal setup][capture] requests SGR mouse reporting, and the [event stream][event-stream] produces `TuiEvent::Mouse`. The noninteractive `termux-run` bridge has no PTY and is not in this input path.
4. [Back to bottom][follow] stores its rendered rectangle, remembers a press, and activates only if release remains inside. The [main text area][textarea] already supports cell-positioned cursors, dragging, and scrolling. Missing behavior belongs to individual views rather than the mouse decoder.

## Baseline experiment with the same binary

The installed client ran with `--no-daemon` in an isolated 88×34 PTY, empty temporary HOME/workspace, and a loopback fake Responses service asking one Lime/Teal question. Test coordinates came from the virtual terminal's synthetic output. No real model, regular session, or phone screen was accessed. The observations below describe the unmodified client.

| Surface | Input | Observed result |
| --- | --- | --- |
| Synchronous `request_user_input` | SGR left press/release over the second answer | Dialog remained with the first choice highlighted. Keyboard `2` closed it and history showed `answer: Teal`. |
| Asynchronous `request_user_input_async` | Tap `1 question`, then use the displayed Shift+Left binding as a control | Tap did not expand it; the binding did. Expansion emitted `?1006l`, `?1003l`, `?1002l`, and `?1000l`, disabling reporting. Keyboard `2` queued the second answer and restored reporting. Termux could not be assumed to send taps while reporting was off. |
| Main composer | Enter `ABCDEF`, click cell C, then type `Z` | Text became `ABZCDEF`, proving cursor placement. The PTY has no Android window and cannot establish keyboard display. |

The synchronous dialog's [BottomPaneView][pane-view] accepted keys and paste but had no mouse-dispatch interface. The [bottom pane][pane] also prevented the main composer from owning mouse input when a view or expanded question was active. For asynchronous questions, [ChatWidget::mouse_capture][async-capture] explicitly selected `MouseCapture::Disabled` when Codex owned the screen, no other modal was active, and questions were expanded. Adding a click callback alone, or keeping reporting on alone, would not fix the entire path.

A focused comparison with [upstream main at investigation time](https://github.com/openai/codex/tree/35145aba212e923f987ccefaf9086ceba31e3b7c) found the same view interface, synchronous question handler, and asynchronous input handler as the release. The asynchronous mouse-disable branch remained. No binary from that main revision was executed.

## Step one: add question taps inside Codex

Maintain a Rust patch for a specific Codex tag, with synthetic upstream tests. At investigation time, the documented [plugin interface][plugins] exposed skills, MCP tools, and lifecycle hooks, but no interface was found for subscribing to local mouse events or registering built-in TUI hit regions. MCP can provide content but cannot attach callbacks to an already-running original TUI. This adaptation therefore requires building a matching client rather than copying files into a plugin directory.

- **Start with asynchronous entry and choices.** The collapsed summary should behave like the expand binding when tapped. Keep reporting only for applicable opt-in full-screen scenarios and retain desktop selection/copy behavior. Dispatch to the active question view first, consuming hits rather than passing them to the composer. Historical completed questions must not submit again.
- **Wire the other dialog separately.** Synchronous dialogs use [RequestUserInputOverlay][sync-input]; asynchronous editing uses [AsyncQuestions][async-input]. Reuse their own choice, next-question, submit, queue, freeform, and timeout-pause logic. Other must enter editing without submitting the preselected option. Do not inject generic numbers or Enter into every selector or approval dialog.
- **Follow actual rendering.** The [shared row renderer][rows] knows every row occupied by an option; [question rendering][aligned] may bottom-align visible content. Register final visible areas and option identities, including wrapping, clipping, and scrolling. Like Back to bottom, activate once only if press/release hit the same valid target. Invalidate targets when the question changes, collapses, is covered/replaced, or the terminal layout changes.

Initial acceptance should verify summary expansion, equivalence of tapping the second choice and keyboard selection, a single submission, Other editing, and no submission from drags, blank areas, or stale coordinates. Then cover multiple questions, narrow Chinese wrapping, fold/unfold, keyboard-induced resizing, and keyboard/copy/scroll/Back to bottom regressions. Synchronous dialogs need their own unanswered/confirmation-flow validation.

## Step two: display the Android keyboard when editing is tapped

[TermuxTerminalViewClient.onSingleTapUp][termux-ime] calls `showSoftInput(terminalView, 0)` only when mouse reporting is disabled and the event is not from a physical mouse. Codex's full-screen composer enables reporting, making cursor placement and keyboard display separate outcomes. Termux's drawer/extra-key [KEYBOARD control][extra-key] toggles visibility; it can hide an already visible keyboard, so it is unsuitable as an unconditional automatic action.

**First experiment with stock Termux.** [Gesture handling][gesture] reports coordinates at finger release; Android's `onSingleTapConfirmed` separately handles a confirmed tap. If Codex briefly disables reporting after recognizing an edit-area tap, Termux might observe that disabled state when confirming the same tap and invoke its existing keyboard path. Ordering depends on press duration, Android scheduling, and terminal latency. During that window, scroll or subsequent taps may be lost. This is an experiment, not a reliable feature guarantee.

The repository includes an [independent probe](../scripts/probe-termux-ime.sh). Run it in a fresh ordinary Termux shell, outside Codex, tmux, and `termux-run`. It enables only its own 1000/1006 test modes. At the start of each run, hide the keyboard using Android Back if needed, keep the probe visible, and tap `[ Test input ]` on row 2.

```sh
# Run from a clone accessible to host Termux.
bash scripts/probe-termux-ime.sh
# After the first run, repeat under the same conditions:
bash scripts/probe-termux-ime.sh --ime-window
```

Both runs should report `tap 1: field`. The control leaves reporting enabled; the experiment disables it for 0.7 seconds after a field tap, then restores it. Blank taps report `outside` without opening that window. The operator must observe whether a first tap shows a hidden keyboard, whether another tap hides an already visible one, and whether the effect repeats after hiding or with rapid/slow taps. The probe neither detects the IME nor saves input. Quit with `q`, Ctrl+C, or its approximately 45-second timeout. Synthetic PTY checks cover hit/miss, reporting sequences, and cleanup; **both Android display experiments still need real-device validation**. The long 0.7-second window makes the experimental signal observable, not a production design.

**If timing is unreliable, Termux participation is needed.** A small session-level extension in a controlled Termux build could accept a negotiated “show IME” request after Codex recognizes an editing tap. Termux should act on the UI thread using [Android's display interface][android-ime] only for the foreground session, focused TerminalView, and a recent real finger tap. Consume that gesture once and show rather than toggle. Session switching, expiry, physical mouse events, and unrelated printed sequences must not show the keyboard. A private control sequence is only a transport candidate: the original [OSC dispatcher][osc] has no such action. Negotiate or configure support explicitly; unsupported hosts continue normally with manual keyboard controls.

Avoid system-wide simulated keys from chroot or an intermediate PTY guessing choices from ANSI text. The former does not know the active window/keyboard state; the latter loses semantics across wrapping, redraws, themes, and asynchronous question changes. Disabling reporting globally would restore Termux's ordinary tap behavior while breaking scrolling/buttons already in use. If both original clients must remain untouched, a separate app-server client could draw Android controls, but it would be another client rather than an adaptation of the original terminal UI.

This initial investigation did not build or replace regular Codex/Termux or copy upstream source into the project. Future distributions must preserve the respective [Codex][codex-license] and [Termux Play][play-license] obligations. This repository's current Apache-2.0 license does not replace component licenses.

[play-version]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/termux-app/build.gradle.kts#L20-L21
[view]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/terminal-view/src/main/java/com/termux/view/TerminalView.java#L119-L164
[gesture]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/terminal-view/src/main/java/com/termux/view/GestureAndScaleRecognizer.java#L64-L109
[emulator]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/terminal-emulator/src/main/java/com/termux/terminal/TerminalEmulator.java#L445-L467
[termux-ime]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/termux-app/src/main/java/com/termux/app/TermuxTerminalViewClient.java#L68-L76
[extra-key]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/termux-app/src/main/java/com/termux/app/extrakeys/TermuxTerminalExtraKeys.java#L113-L118
[osc]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/terminal-emulator/src/main/java/com/termux/terminal/TerminalEmulator.java#L2083-L2224
[capture]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/tui/alternate_screen.rs#L94-L133
[event-stream]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/tui/event_stream.rs#L315
[follow]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/transcript_view/follow_control.rs#L83-L106
[textarea]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/bottom_pane/textarea/mouse.rs#L100-L181
[pane]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/bottom_pane/mod.rs#L2024-L2037
[pane-view]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/bottom_pane/bottom_pane_view.rs
[async-capture]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/chatwidget/questions.rs#L10-L23
[async-input]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/bottom_pane/async_questions/input.rs#L155-L266
[sync-input]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/bottom_pane/request_user_input/mod.rs#L1315-L1380
[rows]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/bottom_pane/selection_popup_common.rs#L408-L479
[aligned]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/codex-rs/tui/src/bottom_pane/request_user_input/render.rs#L411-L456
[plugins]: https://learn.chatgpt.com/docs/plugins
[android-ime]: https://developer.android.com/develop/ui/views/touch-and-input/keyboard-input/visibility
[codex-license]: https://github.com/openai/codex/blob/d32063f96c2dff1dc96af839b3952abb6acfeda4/LICENSE
[play-license]: https://github.com/termux-play-store/termux-apps/blob/cf69df7a8d2a4c496f5b2464d0365a63a58716c5/LICENSE.md
