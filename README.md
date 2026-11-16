# codex-touch

为 Termux 中的 Codex 提供触摸操作支持的组件。

当前版本：**0.1.0**。本版本建立开发框架，尚未实现触摸输入、手势映射或 Codex 集成。实现语言与接入方式将在验证实际输入链路后确定。

## 开发入口

在工作区运行：

```sh
cd /storage/emulated/0/Agent/codex-touch
bash scripts/check.sh
```

基础检查依赖 Bash、Git 和常见 Unix 工具，不需要下载依赖。在 Debian guest 内没有 Git 时，检查脚本会通过现有的 `termux-run` 调用宿主 Git；直接在 Termux 中运行时使用本地 Git。

## 目录

```text
src/                 后续功能源码
tests/               后续自动化测试
scripts/check.sh     统一基础检查入口
docs/design.md       目标、待验证问题与首个功能的验收范围
docs/development.md  开发、验证与版本管理约定
VERSION              当前版本号
CHANGELOG.md         版本变更记录
```

从 [设计说明](docs/design.md) 和 [开发指南](docs/development.md) 开始开发。项目采用独立 Git 仓库，默认分支为 `main`，版本标签使用 `vX.Y.Z`。

## 许可证

[MIT](LICENSE)。
