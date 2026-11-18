[English](README.md) | 简体中文

# codex-touch

为 Termux 中的 Codex 增加触摸操作，让手机上缺少 Shift 等组合键时，也能点击提示文字执行操作。

本项目维护针对 **Codex 0.169.0** 的 Rust TUI 源码补丁和手机构建工具，生成独立的适配版客户端。使用已有的鼠标协议和运行时快捷键处理，不需要修改 Termux APK。项目独立维护，与 OpenAI 无隶属关系。

当前版本 **0.3.0**。详见[版本记录](CHANGELOG.zh-CN.md)、[发布说明](docs/releases/v0.3.0.zh-CN.md)和 [v0.3.0 Release](https://github.com/Zircon10086/codex-touch/releases/tag/v0.3.0)。本次发布源码与校验文件，程序需要按下方步骤构建；没有预编译二进制附件。

0.3.0 新增恢复/分叉选择器、弹窗、补全及导航触摸，已于 2026-11-18 确认手机测试通过，见[覆盖与验收](docs/picker-touch.zh-CN.md)。

## 功能与范围

| 位置 | 触摸操作 |
| --- | --- |
| 异步问答 | 点摘要展开、点选答案、Other/自由编辑、提交、跳过与前后题提示 |
| 主输入区 | 点击帮助、换行、模式等提示；有草稿时仍可打开帮助与插入换行 |
| 快捷键帮助 | 点击完整显示的独立动作，支持运行时单键和两段快捷键 |
| Agent command center | 点击任务行选中、再点已选中行打开；筛选、分组、底部提示与帮助动作 |
| 工作状态 | 点击完整显示的 `esc to interrupt` 中断任务，拖动不会激活 |
| 恢复/分叉 | 选中/打开会话、筛选、排序、密度、预览、展开、取消 |
| 菜单与弹窗 | 通用列表、设置、审批、同步问答、MCP 表单、提供商字段、启动选项 |
| 补全与导航 | 命令/文件/技能/提及补全、浮动快捷键指引、记录/分页控制、警告与统计 |

适用于默认全屏 TUI，通过 `CODEX_TOUCH=1` 显式启用。补丁提供上述触摸范围；`--no-alt-screen` 仍未适配。需要在其他界面执行的快捷键参考行保留说明用途。Android 软键盘仍需手动打开；异步答案编辑器的便捷换行入口和曾报告的多题卡住问题仍待后续处理。具体覆盖见[快捷键与中心操作](docs/shortcut-touch.zh-CN.md)。

## 在手机上构建与运行

已验证环境为 ARM64 手机上的 Debian chroot，终端由 Termux 提供。当前目标是 `aarch64-unknown-linux-gnu`（glibc），产物需要在兼容的 Linux 用户环境中运行。其他 Termux 发行渠道、proot 和其他架构尚未完成同等验收。

先准备 Debian 环境，再按[手机构建指南](docs/build.zh-CN.md)安装依赖及固定的 Rust 1.95.0。进入该环境，在 Linux 文件系统中执行：

```sh
git clone https://github.com/Zircon10086/codex-touch.git
cd codex-touch
bash scripts/check.sh
bash scripts/build-touch.sh
bash scripts/run-touch.sh
```

默认构建目录为 `~/codex-touch-build`，生成包为 `packages/touch-pickers-0.169.0`。构建脚本拒绝覆盖现有包；后续构建可以用 `CODEX_TOUCH_PACKAGE` 指定新目录。无需先构建原版基线。

启动器只设置 `CODEX_TOUCH=1`，不改变 HOME/CODEX_HOME。与日用 Codex 在相同用户环境下运行时，会共用配置和会话；需要隔离时另设 `CODEX_HOME`。它不替换日用 `codex` 命令。

完整构建需要下载依赖并占用较多空间：首轮基线实测约 18.1 GiB，加入测试缓存和四个保留包后约 32.57 GiB；这些是特定手机的记录，见[基线构建](docs/baseline-build.zh-CN.md)。脚本默认单任务并降低优先级。构建与测试缓存应放在 Linux 文件系统，避免 Android 共享存储的权限限制。

## 验证与贡献

0.3.0 于 2026-11-18 通过 1,297 项去重 Rust 回归，随后已确认手机测试通过；程序包和验收详情见[验证记录](docs/picker-touch.zh-CN.md)。

2026-11-17：409 项去重 Rust 回归、隔离模型工具回合、SGR 鼠标 PTY 与终端恢复检查通过。用户已确认第一阶段主要点答路径可用，并在后续补齐后确认 Agent command center 与工作中断触摸测试通过。详细证据和待验收边界见[第一阶段记录](docs/phase1.zh-CN.md)及[快捷键记录](docs/shortcut-touch.zh-CN.md)；自动化测试不能替代 Android 输入法验收。

```sh
bash scripts/check.sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-pickers-0.169.0"
```

基础检查只需要 Bash、Python 3.11+ 标准库、Git 和常见 Unix 工具。GitHub Actions 运行基础检查；Rust 编译和真实程序验收为显式的耗时步骤。贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.zh-CN.md)。

## 文档与源码

- [手机构建指南](docs/build.zh-CN.md)：依赖、首次构建、启动、重建与环境边界。
- [设计说明](docs/design.zh-CN.md)与[开发指南](docs/development.zh-CN.md)：实现约定、检查和版本管理。
- [首次调查](docs/termux-touch.zh-CN.md)：Termux 输入链路和软键盘实验。
- [src/](src/README.zh-CN.md)：固定上游补丁、许可证和来源。
- [tests/](tests/README.zh-CN.md)：合成输入、程序包和 PTY 验收。

项目默认语言为英文；每份文档顶部均可切换到简体中文版本。

## 许可证

当前源码采用 [Apache License 2.0](LICENSE)，与固定版本的上游 Codex 相同。版权、修改说明和上游声明见 [NOTICE](NOTICE) 与[源码来源](src/README.zh-CN.md)。第三方代码保留各自许可证；历史 `v0.1.0` 的 MIT 许可记录不变。
