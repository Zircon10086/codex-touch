# 手机本地基线构建

先构建未经触摸修改的上游版本，用于验证构建环境和后续对照。
[upstream.json](../upstream.json) 固定源码仓库、标签、提交、工具链、目标和构建配置。

- Codex：`rust-v0.169.0`，提交 `d32063f96c2dff1dc96af839b3952abb6acfeda4`。
- Rust：`1.95.0`，含 rustfmt、Clippy 和 rust-src。
- 目标：`aarch64-unknown-linux-gnu`，运行于手机上的 Debian chroot。
- 配置：上游的 `dev-small`，默认 1 个编译任务，使用 LLD，Cargo 依赖采用 `--locked`。

## 构建依赖

Debian 包：`build-essential cmake pkg-config libssl-dev libcap-dev lld git`。
Python 3.11+ 和 HTTPS 根证书同样需要可用。Rust 通过 rustup 安装上述固定版本。
这里需要直接访问 guest 源码目录的 Git，以及针对 glibc 的 C/C++ 编译器。

无需预先安装 just 或 Android SDK。其他依赖以固定源码实际构建结果为准。
原版 Termux 的 Android/Bionic 编译器不直接用于这个 Linux 构建。

## 使用

在 Debian chroot 的项目目录执行：

```sh
bash scripts/build-baseline.sh
```

默认工作目录为 `~/codex-touch-build`，包含：

```text
upstream/                       固定源码，仅规范化发布锁文件的本地版本
target/                         Cargo 编译与增量缓存
downloads/                      上游打包工具下载的 V8、ripgrep 等依赖
logs/                           构建日志
packages/baseline-0.169.0/       完整的基线程序包
```

Cargo 自身的下载缓存位于 `~/.cargo`。即便 V8 使用上游预编译库，Cargo 初次获取其 Git 依赖时仍会下载子模块，可能占用数 GiB。

可用 `CODEX_TOUCH_BUILD_DIR` 指定其他 Linux 目录，用 `CODEX_TOUCH_JOBS` 调整编译并发。首次实机尝试在充电期间以 2 任务构建，电池温度升到 46.8°C，因此项目默认改为 1；这个设置独立于用户全局 Cargo 的并发配置。
源码与产物不要放在 Android 共享存储。首次构建会持续占用资源，应保持 Termux 活跃，按需持有唤醒锁，并留意温度及可用内存。

脚本拒绝不同提交、约定锁文件修正以外的本地修改以及已存在的输出包。依赖下载或编译失败时保留缓存，可以在排除故障后重新执行。成功后不会替换日用 Codex，也不会启动会话或读取日用配置。

## 发布标签的锁文件修正

该标签的工作区版本为 `0.169.0`，但 `Cargo.lock` 中 173 个本地包仍标记为 `0.0.0`，直接使用 `--locked` 会失败。
`scripts/prepare-lock.py` 只同步这些本地包版本，并核对修正前、后的完整 SHA-256；第三方依赖的版本、来源、校验值及依赖关系保持原样。
实际编译仍使用 `--locked`。这项构建元数据修正不包含 Rust 功能代码改动。

## 构建边界

复用上游 `scripts/build_codex_package.py`，构建主程序、`codex-code-mode-host`、`codex-exec-server` 和 Linux `bwrap`，并按上游清单下载、校验 V8 与 ripgrep。包内包括 `codex-package.json`、`bin/`、`codex-path/` 和 `codex-resources/`。

这里的“手机本地构建”指 Codex 及其自有辅助程序在手机上编译；第三方 V8 和 ripgrep 使用上游构建流程指定的预编译依赖。语音发行包和 Android APK 不属于本轮构建范围。

源码和依赖的上游许可证继续适用。本仓库当前同样采用 Apache-2.0，第三方组件仍保留各自许可证。

## 验收状态

2026-11-16：基线构建和统一集成验收完成。程序包位于：

```text
${HOME}/codex-touch-build/packages/baseline-0.169.0
```

无需加载日用配置的版本检查：

```sh
"$HOME/codex-touch-build/packages/baseline-0.169.0/bin/codex" --version
```

集成验收命令：

```sh
bash scripts/check.sh --baseline-package "$HOME/codex-touch-build/packages/baseline-0.169.0"
```

通过范围：程序包布局与版本、辅助程序启动、app-server 初始化、回环假模型驱动的 V8 代码执行及 shell/ripgrep 调用，以及默认后台服务模式下 TUI 在合成 PTY 中显示最终回复并正常退出。测试使用临时 HOME/CODEX_HOME，退出后停止测试后台服务并清理临时文件。自动生成会话标题会多发一次模型请求，验收依据具体工具结果与聊天回复，不依赖总请求数。

本轮没有修改触摸行为，也未进行真实 Android 键盘、手机点按、完整上游测试套件或 Linux 沙箱能力验收。

### 本机实测资源

从首次构建尝试到成功出包约 **42.5 分钟**，包含依赖下载、发布锁文件排查、一次中断以及降温；不是纯编译时间。最后一轮约 **25.8 分钟**，其中温度暂停约 **5.4 分钟**。最终一轮以 10 秒间隔采样的构建进程组 RSS 总和峰值约 **3.19 GiB**，包含共享内存重复计数，不等同于精确独占峰值。

| 内容 | 分配空间 |
| --- | ---: |
| 上游源码及浅克隆 | 151.5 MiB |
| Cargo 编译、增量缓存 | 12,611.3 MiB |
| Cargo Git 依赖缓存 | 3,862.0 MiB |
| Cargo registry 缓存 | 1,241.8 MiB |
| 上游 V8/ripgrep 下载缓存 | 34.6 MiB |
| 完整基线程序包 | 598.6 MiB |
| 合计 | 约 18.1 GiB |

以上不含此前安装的约 1.1 GiB 工具链和本轮新增的约 52 MiB Git 依赖。当前保留编译与下载缓存用于后续触摸开发。

上游 bubblewrap C 代码有两处 `sockaddr_nl` 字段未显式初始化警告，未导致构建失败；基线保留原代码。
本机构建命令、日志、采样、各二进制校验值记录在 `~/codex-touch-build/baseline-build-record.json` 与 `logs/`。
