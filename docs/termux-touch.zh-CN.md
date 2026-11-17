[English](termux-touch.md) | 简体中文

# Termux 下的问答点选与软键盘：首次调查

调查日期：2026-11-16。结论适用于本次核对的两个版本。
**问答由 Codex 决定点了哪一项，软键盘由 Termux 的 Android 窗口显示。** 两者可以分开交付；问答点选不需要改 Termux。

## 输入实际走哪条路

本机 `codex --version` 为 `0.169.0`。不提权查询 Android 包管理器，`com.termux` 的版本码为 **142**；[Google Play 分支的构建定义][play-version]对应 `googleplay.2026.10.09`，工作区原应用清单中的六月版是 141。以下引用固定在对应提交，不假定 F-Droid 版或其他终端相同。

1. [Termux TerminalView][view] 在手指抬起时，如果开启了鼠标上报、没有滑动且不在选文，会连续发出一次左键按下和释放。它按字体度量把像素转成字符格；手指滑动则走滚轮路径。两次鼠标报告都来自同一次抬手，不能用它们之间的时间推断手指按了多久。
2. [TerminalEmulator.sendMouseEvent][emulator] 在 SGR 模式下把第 8 列第 30 行的这次点按写作 `ESC[<0;8;30M` 和 `ESC[<0;8;30m`。协议坐标从 1 开始，crossterm 交给 TUI 的坐标从 0 开始。**进入 TUI 后，普通手指点按和鼠标左键点击没有来源标识。**
3. Debian 中 Codex 的交互进程继承 Termux 的 PTY（测试设备使用自己的 `crcodex` 启动器）。Codex 的[终端模式设置][capture]打开鼠标上报时请求 SGR 编码；[事件流][event-stream]生成 `TuiEvent::Mouse`。宿主命令桥 `termux-run` 没有交互 PTY，不参与这条输入链路。
4. [Back to bottom][follow] 保存实际绘制的按钮区域，按下时记住命中，释放仍在区域内才跳到底部。[主输入框][textarea]也已有按字符格放光标、拖选和滚轮处理。问题出在具体视图，不需要重写触摸解码器。

## 同一二进制的对照实验

使用已安装的 Codex、独立 88×34 PTY、空临时 HOME 和项目、`--no-daemon`，仅由回环地址上的假 Responses 服务生成一题（选项 Lime / Teal）。实验读虚拟终端的**合成画面**定位选项；没有连接真实模型、操作日常会话或读取手机画面。以下是原版的行为，不是适配后的效果。

| 场景 | 发送的输入 | 观察到的结果 |
| --- | --- | --- |
| 普通问答 `request_user_input` | 对第二项文字发送 SGR 左键按下和释放 | 卡片保留，第一项仍高亮；按键盘 `2` 后卡片关闭，历史显示 `answer: Teal`。 |
| 异步问答 `request_user_input_async` | 点击底部的 `1 question`，再用画面提示的 `Shift+←` 作对照 | 点击后仍折叠；快捷键能展开。展开时 TUI 发出 `?1006l`、`?1003l`、`?1002l`、`?1000l`，关闭鼠标上报；按 `2` 后第二项进入消息队列，上报重新开启。此时不能假设 Termux 还会发送选项点按。 |
| 主聊天输入框 | 输入 `ABCDEF`，发同类左键点按到 C 所在的格子，再输入 `Z` | 结果是 `ABZCDEF`。光标定位已生效；PTY 无 Android 窗口，不能验证键盘是否显示。 |

普通弹层通过 [BottomPaneView][pane-view] 处理键盘、粘贴等事件，没有鼠标分派入口。[底部面板][pane]还会在有活动视图或展开问答时阻止主输入框接管鼠标。异步问答另有一层：[ChatWidget::mouse_capture][async-capture] 在 Codex 管理整个终端画面、没有其他模态框且问答已展开时，主动选择 `MouseCapture::Disabled`。这解释了为什么模拟一个点击回调，或者仅把上报一直打开，都不能独立修好问答。

也定点比对了调查时的[上游 main](https://github.com/openai/codex/tree/35145aba212e923f987ccefaf9086ceba31e3b7c)：上述视图接口、普通问答处理和异步问答输入处理三个文件与发布版相同，异步问答仍有关闭鼠标上报的分支。没有对 main 二进制作运行验证。

## 第一步：给 Codex 的问答增加点击

建议在本仓库维护可对指定 Codex 标签应用的 Rust 源码补丁，并以合成问答做上游测试。官方[插件接口][plugins]提供 skills、MCP 工具、生命周期 hooks 等能力，未发现可订阅本地鼠标事件或注册内置组件命中区域的接口。MCP 可以提供自己的内容，但无法给已经运行的原版 TUI 控件挂回调。发布这种适配需要构建匹配的客户端，不是把文件拷到插件目录即可生效。

- **先做异步问答的入口和选项。** 底部的折叠摘要本身就是入口；点它应和“展开问答”快捷键等效。只在启用触摸适配、使用全屏 TUI 的对应场景保留鼠标上报；保留桌面端原有选择／复制策略。事件先交给当前问答视图，命中后消费，不落到下面的聊天输入框。点击已完成的历史问答不应再次作答。
- **另一套弹层单独接线。** 同步弹层用 [RequestUserInputOverlay][sync-input]，异步编辑器用 [AsyncQuestions][async-input]。使用各自已有的选项选择、进入下一题、提交、排队、自由填写和暂停超时逻辑。比如异步选项会区分普通选项和 Other；触摸 Other 进入编辑，不能把预选值误作已提交。不要给所有选择器或审批框统一注入数字或 Enter。
- **命中区域跟着绘制。** [共享选择行渲染器][rows]知道每个选项实际占了哪些行；[问答渲染][aligned]还会将可见行底部对齐。只记录最终可见区域与选项索引的对应关系，包括换行、截断和滚动偏移。仿照 Back to bottom，仅在按下和释放命中同一有效目标时触发一次；题目变更、折叠、弹层替换或终端重排时使旧命中失效。

首轮验收：点折叠摘要能展开；点第二项和键盘选第二项得到同一答案且只提交一次；点 Other 可输入；滑动、空白和过期坐标不提交。再覆盖多题、窄屏中文换行、内外屏切换、输入法引发的尺寸变化，以及键盘、复制、滚动、Back to bottom 的回归。同步弹层还需验证它自己的“未回答／确认”流程。

## 第二步：点击可编辑区域时显示 Android 键盘

[TermuxTerminalViewClient.onSingleTapUp][termux-ime] 只在**没有鼠标上报**且事件不是实体鼠标时，才调用 `showSoftInput(terminalView, 0)`。Codex 主输入框在全屏模式启用了鼠标上报，所以移动光标和显示 Android 输入法是两个独立结果。Termux 抽屉／额外按键的 [KEYBOARD][extra-key] 是手动切换；已经显示时再次切换会隐藏，不适合作为输入框的自动动作。

**先试原版 Termux，不改 APK。** [手势识别代码][gesture]在抬手时上报坐标，另由 Android 的 `onSingleTapConfirmed` 处理普通单击。如果 Codex 在认出编辑区的一次点击后很短暂地关闭上报，Termux *有可能*在确认该次单击时看到关闭状态，进而调用原有的显示键盘逻辑。回调顺序受按压时长、Android 调度和终端往返时间影响；窗口期间滚动或下一次点按也可能丢失。这只是实验假设，不是可发布的保证。

仓库提供[独立诊断脚本](../scripts/probe-termux-ime.sh)。在一个**新开的普通 Termux shell** 中运行，不在 Codex、tmux 或 `termux-run` 里跑。脚本只启用自己测试用的 1000/1006 模式。启动每一轮后先用系统返回键收起输入法（若已隐藏则跳过），确认仍在探针画面，再单指轻点第 2 行的 `[ Test input ]`。

```sh
# 在宿主 Termux 可访问的项目克隆目录中运行
bash scripts/probe-termux-ime.sh
# 第一轮结束后，用相同条件再跑：
bash scripts/probe-termux-ime.sh --ime-window
```

两轮都应报告 `tap 1: field`；对照轮一直上报，实验轮仅在该格子点按后关闭上报 0.7 秒再恢复。点空白应为 `outside` 且不触发窗口。**由操作者观察**：原本隐藏的键盘是否因这第一次点按而显示，已显示时再次点会不会关闭；键盘收起后、连续速点和稍慢点按能否重复。脚本不检测 IME、不保存输入；按 `q`、Ctrl+C 或等待约 45 秒退出。合成 PTY 测过命中／未命中、上报序列和退出清理，**两轮 Android 显示结果均待真机验收**。0.7 秒只为放大实验信号；不能据一次成功就照搬进产品。

**如果时序不可靠，需要 Termux 宿主参与。** 建议在可控的 Termux 构建里做一个很小的会话级扩展：Codex 认出可编辑区的一次点击后发送双方约定的“显示 IME”请求。Termux 只对当前前台会话、当前有焦点的 TerminalView、刚发生的真实手指点按响应，在 UI 线程调用 [Android 的显示接口][android-ime]；消费该次手势后不再重复响应，永远不做 toggle。切换会话、超时、实体鼠标点击或其他程序单纯打印相同字符时不应弹键盘。私有控制序列只是候选传输，原版 Termux 的 [OSC 分派][osc]没有现成的这一动作。启用前需显式协商或配置，未支持的宿主照常处理输入，仍可手动打开键盘。

不推荐从 chroot 发送系统级模拟按键，或用中间 PTY 从 ANSI 文字猜选项：前者不知道当前窗口及键盘可见性，后者在换行、重绘、主题及异步问题切换时会失去语义。全程关闭鼠标上报虽然能恢复 Termux 的普通点按，却也会破坏用户已经在用的滚动和按钮。若硬性要求两端都保持原版，可用独立 app-server 客户端绘制自己的 Android 控件，但那是另一个客户端，不能补回原终端的控件交互。

本次没有构建／替换日用 Codex 或 Termux，也没有拷入上游源码。后续如分发修改后的程序，应分别保留 [Codex][codex-license] 和 [Termux Play][play-license] 的上游许可要求；本仓库当前的 Apache-2.0 声明不替代其他组件的许可证。

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
