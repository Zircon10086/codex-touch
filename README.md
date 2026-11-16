# codex-touch

为 Termux 中的 Codex 提供触摸操作支持的组件。

当前版本：**0.1.0**（框架基线）。目前已核对 Codex 0.169.0 和 Google Play 版 Termux 的输入链路，复现了问答不响应点按、主输入框能用点按移动光标的区别，尚未发布触摸适配。

[首次调查：问答点选与 Android 软键盘](docs/termux-touch.md) 记录原版行为、源码位置、建议的 Codex 补丁，以及一个无需修改 APK 的键盘实验。

[手机本地基线构建](docs/baseline-build.md) 提供固定上游提交和 Debian ARM64 构建入口。Codex 0.169.0 基线已在手机构建并通过隔离的工具调用与 TUI 验收，可作为触摸适配前的对照版本。

## 开发入口

在工作区运行：

```sh
cd /storage/emulated/0/Agent/codex-touch
bash scripts/check.sh
```

检查依赖 Bash、Python 3（标准库）、Git 和常见 Unix 工具，不需要下载依赖。在 Debian guest 内没有 Git 时，检查脚本会通过现有的 `termux-run` 调用宿主 Git；直接在 Termux 中运行时使用本地 Git。

## 目录

```text
src/                 后续功能源码
tests/               后续自动化测试
scripts/check.sh     仓库与合成 PTY 检查入口
scripts/probe-termux-ime.sh  在独立交互终端中验证软键盘假设
docs/termux-touch.md 版本、原版对照实验、适配路线与真机验证步骤
docs/design.md       目标、待验证问题与首个功能的验收范围
docs/development.md  开发、验证与版本管理约定
VERSION              当前版本号
CHANGELOG.md         版本变更记录
```

从 [设计说明](docs/design.md) 和 [开发指南](docs/development.md) 开始开发。项目采用独立 Git 仓库，默认分支为 `main`，版本标签使用 `vX.Y.Z`。

## 许可证

[MIT](LICENSE)。
