[English](build.md) | 简体中文

# 手机构建指南

## 支持环境

已验证：ARM64 Android 手机，Termux 终端，Debian chroot，GNU/glibc 工具链。目标固定为 `aarch64-unknown-linux-gnu`。构建和程序运行都在 Debian 环境内完成，终端输入输出直接连接 Termux 的 PTY。

本仓库不安装或管理 chroot。先准备可工作的 Debian 环境；当前发布流程不要求本机专用的启动器、root 命令桥或 Android SDK。原生 Termux 的 Bionic 编译器不能直接替代这里的 glibc 编译器。其他 Linux 用户环境可能可行，但尚未验证 proot 或其他 CPU 架构。

将克隆、源码、Cargo 缓存和可执行包放在 Debian 的 Linux 文件系统，例如 `$HOME`。不要将构建输出放到 `/sdcard` 或 Android 共享存储。仓库本身若放在共享存储，脚本须用 `bash` 调用。

## 安装依赖

需要 Python 3.11+（使用标准库 `tomllib`），建议使用 Debian 12 或更新版本。在 Debian 中以有包管理权限的用户安装依赖。下面两条是管理员命令；普通用户可使用已配置的 `sudo` 或进入管理员 shell 后执行：

```sh
apt-get update
apt-get install -y build-essential cmake pkg-config libssl-dev libcap-dev lld git python3 curl ca-certificates
```

在用于构建的普通用户下，按照 [rustup 官方说明](https://rustup.rs/)安装 rustup。已有 rustup 时直接安装固定工具链：

```sh
rustup toolchain install 1.95.0 --profile minimal --component rustfmt --component clippy --component rust-src
rustup run 1.95.0 rustc --version
cc -dumpmachine
```

`cc -dumpmachine` 应为 `aarch64-linux-gnu`。项目构建脚本自行选择 Rust 1.95.0，无需修改全局默认版本。

## 首次构建

从 README 的地址克隆项目并进入仓库后：

```sh
bash scripts/check.sh
bash scripts/build-touch.sh
bash scripts/run-touch.sh
```

`build-touch.sh` 自动获取 `upstream.json` 固定的 Codex 提交，核对已知锁文件修正，应用累计补丁，并复用上游打包流程。未知源码改动会使它停止，已有输出不会被覆盖。第一次使用无需先运行 `build-baseline.sh`；基线构建仅用于与原版对照。

默认目录：

```text
~/codex-touch-build/
  upstream/                     固定上游源码及补丁
  target/                       Rust 增量缓存
  downloads/                    上游打包依赖
  logs/                         构建日志
  packages/touch-agents-0.169.0/ 完整适配包
```

构建采用单个 Cargo 任务、`dev-small` 配置和 LLD，使用 `--locked`。Codex 自有辅助程序本地编译；V8、ripgrep 等第三方产物按上游构建流程下载并校验。构建脚本不会启动 Codex 会话或读取日用 API 配置。

首次下载和编译耗时较长。既有手机的基线首次尝试至成功约 42.5 分钟，包含下载、排障和降温；增量开发包通常快得多。空间与时间实测见[基线记录](baseline-build.zh-CN.md)和[当前功能记录](shortcut-touch.zh-CN.md)，不要把实测值当作最低资源要求。

保持 Termux 可运行并留意温度、内存和剩余空间。需要唤醒锁时，在宿主 Termux 中执行 `termux-wake-lock`，结束后执行 `termux-wake-unlock`。仓库构建脚本只有单任务和低优先级控制；开发记录中的自动温控监视器是测试设备本地工具，没有随本项目提供。

## 启动与隔离

`run-touch.sh` 启用 `CODEX_TOUCH=1` 后执行包内 Codex，沿用原有参数：

```sh
bash scripts/run-touch.sh --version
bash scripts/run-touch.sh
```

正常启动会使用当前用户的 Codex 配置与会话。希望单独配置和测试时可以显式指定新目录，再完成该环境的正常配置：

```sh
CODEX_HOME="$HOME/.codex-touch-test" bash scripts/run-touch.sh
```

所有自动化程序包测试都会使用临时 HOME/CODEX_HOME 和本机假服务，不需要真实 API Key。输入法仍需通过 Termux 的键盘按钮手动打开。

## 重建、选包与回退

已有包不覆盖。用新的输出目录构建，并用相同变量启动：

```sh
CODEX_TOUCH_PACKAGE="$HOME/codex-touch-build/packages/touch-local" bash scripts/build-touch.sh
CODEX_TOUCH_PACKAGE="$HOME/codex-touch-build/packages/touch-local" bash scripts/run-touch.sh
```

旧包若保留，可把 `CODEX_TOUCH_PACKAGE` 指向旧目录切回。`CODEX_TOUCH_BUILD_DIR` 用于变更整个 Linux 构建根目录；`CODEX_TOUCH_JOBS` 调整编译并发，手机上建议保留默认值 1。

## 验收

```sh
bash scripts/check.sh --upstream-source "$HOME/codex-touch-build/upstream" --rust-tests
bash scripts/check.sh --touch-package "$HOME/codex-touch-build/packages/touch-agents-0.169.0"
```

两项均属于耗时检查。Rust 测试首次会增加编译缓存；程序包检查启动临时本机服务和伪终端。真实 Android 点按、软键盘以及不同 Termux 版本仍需实际设备验收。

## 开发设备的启动示例

开发记录中的 `crsh`、`crcodex` 和 `termux-run` 是测试设备已有环境的命令，其他用户无需安装它们。在该设备上，可从 Termux 进入 `crsh`，再执行：

```sh
bash /storage/emulated/0/Agent/codex-touch/scripts/run-touch.sh
```

其他环境直接进入自己的 Debian shell，在克隆的仓库目录运行同一脚本即可。
