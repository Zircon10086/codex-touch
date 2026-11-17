[English](README.md) | 简体中文

# 测试目录

按实际行为添加测试，并接入 `scripts/check.sh`。优先使用合成输入验证事件转换、边界处理和退出清理，避免依赖私人会话数据。

`probe_pty.py` 在独立伪终端内运行诊断脚本，检查点击命中、短时关闭与恢复鼠标上报、正常退出和信号退出后的终端状态。已接入 `bash scripts/check.sh`。这不是 Codex 集成测试；[键盘真机验收](../docs/termux-touch.zh-CN.md)需在普通 Termux 会话中另做。

`test_prepare_lock.py` 检查发布锁文件修正只影响本地包版本，拒绝未知输入或错误输出校验值，并覆盖只读检查与重复执行。

`baseline_smoke.py` 验证实际构建包的版本和辅助程序、app-server 初始化，以及回环假模型驱动的代码执行和回复；另在合成 PTY 中验证默认后台模式的 TUI，并停止测试后台服务。使用独立临时 HOME/CODEX_HOME，只向本机假服务发送合成数据。它需要先完成基线构建，通过统一入口显式运行：

```sh
bash scripts/check.sh --baseline-package "$HOME/codex-touch-build/packages/baseline-0.169.0"
```

不传 `--baseline-package` 时不会执行已构建 Codex 的集成验收。


`touch_pty.py` 驱动真实适配包的异步问答界面，使用合成 SGR 点击、终端缩放、本机假模型和隔离状态，检查答案投递及终端恢复。通过 `bash scripts/check.sh --touch-package PATH` 运行，并自动运行已有程序包回归。原版基线会在摘要点击展开处失败。

Rust 触摸行为测试保存在 `src/async-question-touch.patch`，应用后位于上游 `async_questions/mouse_tests.rs` 和问答集成测试模块。`bash scripts/check.sh --rust-tests` 编译并运行问答、共享行渲染器和普通问答弹层回归；首次会编译额外的上游测试依赖。精确源码核对可用 `--upstream-source PATH`。详见[阶段一说明](../docs/phase1.zh-CN.md)。

`test_prepare_touch.py` 用临时合成 Git 仓库检查补丁应用、重复执行、只读检查、真实索引保持，以及拒绝错误版本、本地改动、预先存在的新文件和未知文件。

提示点击测试同样保存在累计补丁中：`shortcut`、`footer`、`live_center` 已登记到 `scripts/test-touch.sh`。扩展的 `touch_pty.py` 使用自定义 Shift+Enter、Shift+Up 和两段记录搜索快捷键，覆盖问答前后导航、草稿换行、帮助开关、模式切换、推理强度和多行消息发送，并核对实际发往本机模型的内容。旧第一阶段包不具备这些新增行为。

command center 与中断提示回归增加 `status_indicator` 筛选；`live_center` 包含真实 App 弹层路由、任务选择/打开、筛选、帮助动作以及刷新/拖动/缩放取消。`touch_pty.py` 另外验证中心筛选、帮助、两段搜索绑定、返回与打开，并在本机假模型保持运行时点击中断提示。当前程序包验收需要 `touch-agents` 或更新构建。

`scripts/check-docs.py` 验证英中文档配对、顶部语言链接、本地 Markdown 链接，以及两种语言 README 和 CHANGELOG 的当前版本号；已接入基础检查。
