# 快捷键提示点击

本轮基于同一 Codex 0.169.0 固定提交，沿用 `CODEX_TOUCH=1`，适用于默认全屏终端。功能在 `Unreleased`，版本号仍为框架基线 0.1.0。

## 使用方法

在与 `crcodex` 相同的 Debian chroot 中运行：

```sh
cd /storage/emulated/0/Agent/codex-touch
bash scripts/run-touch.sh
```

当前入口选择 `~/codex-touch-build/packages/touch-shortcuts-0.169.0`。第一阶段已验收包仍保留，可临时切回：

```sh
CODEX_TOUCH_PACKAGE="$HOME/codex-touch-build/packages/touch-0.169.0" bash scripts/run-touch.sh
```

启动器不修改 HOME/CODEX_HOME，默认仍共用日用 Codex 的配置和会话。重新构建用 `bash scripts/build-touch.sh`；已有输出不覆盖，需要通过 `CODEX_TOUCH_PACKAGE` 指定新的 Linux 目录。

## 点击覆盖

| 位置 | 支持行为 |
| --- | --- |
| 主输入区底部 | 点击快捷键或后面的说明文字打开帮助、进入 agents、排队；空闲时点击模式提示切换模式 |
| 有草稿的主输入区 | 保留帮助和 `new line` 入口；换行插入到当前光标处，不提交草稿 |
| `?` 快捷键帮助 | Commands、Mention files、Shell command、New line、Paste image、External editor、Search history、发送/排队、Change mode、推理强度、Voice、Agents、Inspect activity、Interrupt/Quit、Open transcript、Find text |
| 帮助底部 `close` | 关闭帮助并保留草稿 |
| 异步问答底部 | 沿用第一阶段的 submit、skip、main prompt、prev question、next question 等单键提示点按，包含 Shift 组合键 |

默认全屏模式下，Open transcript 展开当前记录详情，输入框仍然保留；Find text 则进入记录搜索。

以上是提示可见且对应绑定未禁用时的覆盖，原版对运行状态、权限、外部编辑器和剪贴板可用性的约束继续生效。`?` 键原有语义不变；只有点击帮助入口能在已有草稿时直接打开帮助。

帮助中的双 Esc、合并的 Subagents/Scroll/Top-latest、只能在记录页内使用的选择提示，以及 `/keymap customize` 仍是参考文字。浮动 leader/preset 菜单、其他弹窗和记录页自身的提示未在本轮适配。普通问答弹层、异步回答编辑器内的新增换行入口、Android 自动弹键盘仍待后续开发。

## 命中与事件处理

- 使用绘制时保留的语义和真实区域。帮助复用原版的一至三列布局及自动换行，并按源文字范围映射命中区域；整条被高度裁剪时不注册点击。
- 按下和松开必须属于同一条提示，期间布局与动作不变。拖动、离开目标、滚轮、修饰键、其他输入、缩放和失焦取消激活；取消后的松手仍被捕获，避免穿透。
- 提示点击优先于底部静态文字选择；从提示开始拖动不会选择文字或触发操作。非提示区域保留原版处理。
- 帮助打开和关闭由输入框处理；其他点击回到应用原按键链路，包含按下与松开，以及运行时两段快捷键。Shift+Tab 按终端约定生成 BackTab。
- 帮助执行动作后关闭，发送、换行等走原版路径；不向输入框插入快捷键名称，也不通过模拟 Escape 关闭帮助，以免触发会话回退。

## 验证

统一入口：

```sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-shortcuts-0.169.0"
```

Rust 检查包含第一阶段范围，并增加提示手势、帮助列布局/换行/裁剪、草稿换行/帮助关闭、弹层背景与非焦点区域测试。集成测试使用隔离 HOME/CODEX_HOME、本机假模型和合成 PTY，验证实际 SGR 鼠标经过完整程序后产生的动作与模型请求。

2026-11-17：376 项去重后的 Rust 测试通过，包含 10 项新增提示点击测试。六个筛选范围分别为 questions 75、selection_popup_common 10、request_user_input 90、shortcut 117、footer 91、live_center 12；范围有交集，未运行整个上游套件。

实际程序 PTY 已通过：原有问答点答与 Shift 前后题导航；拖动模式提示不激活；42 列下换行；带草稿打开帮助和关闭；模式双向切换；自定义 Shift+Up 推理强度；帮助内 Shift+Enter 换行；自定义两段快捷键打开记录搜索；点击发送后实际模型请求包含精确的三行文本及 high 推理强度；退出后终端属性与鼠标上报恢复。

应用级 Rust 测试采用上游 CI 的 `RUST_MIN_STACK=8388608`。一个原有界面快照仍写 `v0.0.0`；验证差异只有两处版本标签后，已更新为固定发布版本 `v0.169.0`。PTY 首次安装隔离后台服务包实测约 40–50 秒，因此启动等待改为 120 秒；界面操作的等待仍为 30 秒，开始空闲操作前排空问答回复，点击提示前等待其位置稳定 250 毫秒，不自动重试点击。

手机本地程序包约 599 MiB，首次本轮出包耗时 145.6 秒；只修正快照后重打包 6.2 秒，五个二进制校验值相同。构建记录在 `~/codex-touch-build/shortcut-build-record.json`。本轮 TUI 测试编译采样进程组 RSS 峰值约 7.07 GiB；单 Cargo 任务，未触发温控暂停。

新功能尚未通过用户真机验收；PTY 不代表 Android 手指操作或输入法已验证。

建议真机按顺序确认：点击底部模式提示；输入两行中文（第二行用 `new line` 插入）；有草稿时点击帮助、再点 New line/Change mode/close；在多题问答中点 next question 与 prev question。缩窄窗口或折叠屏幕后再次操作，确认拖动提示不触发。
